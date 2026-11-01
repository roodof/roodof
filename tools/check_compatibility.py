"""Offline release gate for reviewed readers, fixtures and dated provider prices.

Reads only this checkout and the imported package. Never discovers agent logs,
fetches a URL, updates a table, reads credentials or dispatches a workflow.
An intentional change requires a reviewed registry update, not an auto-snapshot.
"""
import argparse
import ast
from datetime import date,datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/'docs/compatibility.json'
CORE=('usage/accounting.py','usage/records.py','usage/codex.py','usage/claude_code.py','usage/reconcile.py',
      'usage/period_usage.py','usage/archive.py','usage/cache.py','usage/input_limits.py','usage/edit_paths.py',
      'usage/checks.py','usage/projects.py','usage/zstd.py','usage/unzstd.py','usage/xxh64.py',
      'usage/pricing.py','usage/plans.py')
HOSTS={'developers.openai.com','platform.openai.com','learn.chatgpt.com','platform.claude.com','claude.com','support.claude.com'}
MAX_PRICE_AGE_DAYS=30


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()


def code_digest(package):
    def normalized(value):
        if isinstance(value,ast.AST):
            fields={}
            for key,item in ast.iter_fields(value):
                if key=='type_params':continue
                if key=='body' and isinstance(value,(ast.Module,ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
                    item=list(item)
                    if item and isinstance(item[0],ast.Expr) and isinstance(item[0].value,ast.Constant) and isinstance(item[0].value.value,str):item=item[1:]
                fields[key]=normalized(item)
            return dict(node=type(value).__name__,fields=fields)
        if isinstance(value,list):return [normalized(item) for item in value]
        if isinstance(value,bytes):return dict(bytes_hex=value.hex())
        if isinstance(value,complex):return dict(complex=[value.real,value.imag])
        if value is Ellipsis:return dict(ellipsis=True)
        return value
    return digest({name:normalized(ast.parse((package/name).read_text(encoding='utf-8'))) for name in CORE})


def read_registry(path=REGISTRY):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('duplicate registry field')
            result[key]=value
        return result
    raw=Path(path).read_bytes()
    if len(raw)>2*1024*1024:raise ValueError('registry limit')
    return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite registry number')))


def check(registry=None,as_of=None,package=None,root=ROOT):
    import pler
    from pler import reporting
    from pler.usage import pricing,plans
    data=read_registry() if registry is None else registry
    package=Path(package) if package else Path(pler.__file__).resolve().parent
    today=as_of or datetime.now(timezone.utc).date();errors=[]
    def require(condition,code):
        if not condition:errors.append(code)
    def fresh(value,maximum,code):
        try:
            at=date.fromisoformat(value)
            require(0<maximum<=90 and 0<=(today-at).days<=maximum,code)
        except (ValueError,TypeError):errors.append(code)
    try:
        require(type(data['format']) is int and data['format']==1,'unsupported_registry')
        parser=data['reader_review'];price=data['price_review']
        require(parser['parser_version']==reporting.PARSER_VERSION and parser['schema_version']==reporting.SCHEMA_VERSION,'parser_version_review_required')
        require(parser['modules']==list(CORE),'reader_scope_review_required')
        require(parser['code_sha256']==code_digest(package),'reader_code_review_required')
        require(isinstance(parser['note'],str) and bool(parser['note'].strip()),'reader_review_note_missing')
        fresh(parser['reviewed_at'],90,'reader_review_expired')
        require(type(price['maximum_age_days']) is int and price['maximum_age_days']==MAX_PRICE_AGE_DAYS,'price_review_policy_changed')
        fresh(price['reviewed_at'],MAX_PRICE_AGE_DAYS,'price_review_expired')
        require(price['api_as_of']==pricing.PRICES_AS_OF and price['plan_as_of']==plans.PRICES_AS_OF,'price_date_review_required')
        require(date.fromisoformat(price['api_as_of'])<=date.fromisoformat(price['reviewed_at']) and date.fromisoformat(price['plan_as_of'])<=date.fromisoformat(price['reviewed_at']),'price_date_unreviewed')
        require(set(pricing.SOURCES)<=set(price['sources']),'price_source_review_required')
        require(len(price['sources'])>=3 and all(urlsplit(url).scheme=='https' and urlsplit(url).hostname in HOSTS and urlsplit(url).port in (None,443) and not urlsplit(url).username and not urlsplit(url).fragment for url in price['sources']),'untrusted_price_source')
        reviewed={}
        for group in price['api_groups']:
            for model in group['models']:
                key=(group['agent'],model)
                require(key not in reviewed,'duplicate_reviewed_model');reviewed[key]=group['tiers']
        actual={(agent,model):[[limit,rates] for limit,rates in tiers] for agent,models in pricing.PRICES.items() for model,tiers in models.items()}
        require(set(actual)==set(reviewed),'model_coverage_review_required')
        def money_table(table):
            result={}
            for (agent,model),tiers in table.items():
                clean=[]
                for limit,rates in tiers:
                    if any(value is not None and (type(value) not in (int,float) or not math.isfinite(value) or value<0) for value in rates.values()):raise ValueError('invalid reviewed rate')
                    clean.append([limit,{key:float(value) if value is not None else None for key,value in rates.items()}])
                result.setdefault(agent,{})[model]=clean
            return result
        require(digest(money_table(reviewed))==digest(money_table(actual)),'api_rate_review_required')
        for (agent,model),tiers in actual.items():
            previous=0
            for index,(limit,rates) in enumerate(tiers):
                require(limit is None and index==len(tiers)-1 or type(limit) is int and limit>previous,'invalid_price_tier')
                previous=limit or previous
                require(set(rates)=={'input','output','cache_read','write_5m','write_1h'},'invalid_price_fields')
                for name,value in rates.items():
                    require(value is None and agent=='codex' and name in ('write_5m','write_1h') or type(value) in (int,float) and math.isfinite(value) and value>=0,'invalid_price_rate')
        plan_table={a:{name:dict(usd=value['usd'],limits={str(k):v for k,v in value['limits'].items()} if value['limits'] is not None else None) for name,value in table.items()} for a,table in plans.PLANS.items()}
        require(digest(plan_table)==digest(price['plans']),'plan_rate_review_required')
        cases_path=root/'tests/fixtures/compatibility/cases.json'
        require(hashlib.sha256(cases_path.read_bytes()).hexdigest()==data['record_cases_sha256'],'record_fixture_review_required')
        cases=json.loads(cases_path.read_text(encoding='utf-8'))
        require(cases['format']==1 and len(cases['cases'])>=10,'record_cases_missing')
        require(len({case['id'] for case in cases['cases']})==len(cases['cases']),'duplicate_record_case')
        for control in data['regressions']:
            module,klass,method=control.split('.')
            tree=ast.parse((root/'tests'/(module+'.py')).read_text(encoding='utf-8'))
            require(any(isinstance(c,ast.ClassDef) and c.name==klass and any(isinstance(f,ast.FunctionDef) and f.name==method for f in c.body) for c in tree.body),'missing_named_regression')
        require(len(data['regressions'])>=6,'regression_coverage_missing')
    except (KeyError,ValueError,TypeError,AttributeError,OSError,OverflowError,RecursionError,SyntaxError):errors.append('invalid_review_registry')
    return dict(ok=not errors,errors=sorted(set(errors)),parser_version=reporting.PARSER_VERSION,schema_version=reporting.SCHEMA_VERSION,
                api_prices_as_of=pricing.PRICES_AS_OF,plan_prices_as_of=plans.PRICES_AS_OF,
                model_count=sum(len(table) for table in pricing.PRICES.values()),as_of=today.isoformat(),network_requests=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--as-of',type=date.fromisoformat,help='UTC review date; defaults to today (release policy, not runtime pricing expiry)');args=parser.parse_args()
    result=check(as_of=args.as_of);print(json.dumps(result,sort_keys=True));return 0 if result['ok'] else 1


if __name__=='__main__':
    sys.path.insert(0,str(ROOT/'src'))
    raise SystemExit(main())
