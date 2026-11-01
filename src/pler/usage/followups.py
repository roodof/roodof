"""Frozen, local before/after observations; never an experiment proving savings or quality.

Only already reconciled response metadata is used. Windows are half-open UTC
intervals, seven days each. Source paths and transcripts are never persisted.
"""
from datetime import timedelta
import hashlib
import json
import math
import re
import statistics
import unicodedata

from .records import TOKEN_FIELDS,total,empty_tokens,add_tokens
from .period_usage import event_time,_reason
from .verdicts import session_code

METHOD=1
WINDOW=timedelta(days=7)
MAX_AGE=timedelta(minutes=5)
MAX_PER_WORK=10
MAX_TOTAL=100
MAX_COHORTS=64
MAX_EVENTS=100000
MIN_SESSIONS=3
MAX_NUMBER=(1<<53)-1
CODE=re.compile('[a-f0-9]{24}')
TRIGGERS=('quota','concentration','session_pattern','other')
CONTEXTS=('unknown','similar','different')
LIMITS={'missing_sessions','source_incomplete','incomplete_usage','unknown_scope','boundary_response',
        'measurement_limit','baseline_changed','parser_changed','context_unknown','context_different',
        'cohort_changed','small_sample','zero_baseline','duplicate_sessions'}


def code(value): return isinstance(value,str) and CODE.fullmatch(value) is not None


def text(value,required=False):
    if not isinstance(value,str): raise ValueError('invalid')
    value=value.replace('\r\n','\n').replace('\r','\n').strip()
    if (required and not value or len(value)>1000
            or any(unicodedata.category(c) in ('Cc','Cs','Zl','Zp') and c!='\n' for c in value)):
        raise ValueError('invalid')
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),
                                    allow_nan=False).encode('utf-8')).hexdigest()[:24]


def date(value):
    parsed=event_time(value)
    if not isinstance(value,str) or parsed is None or parsed.isoformat()!=value:
        raise ValueError('invalid')
    return parsed


def _integer(value): return type(value) is int and 0<=value<=MAX_NUMBER


def validate_snapshot(value):
    fields={'since','until','observed_at','tokens','responses','sessions','excluded_sessions','missing_sessions',
            'boundary_sessions','cohorts','limitations','fingerprint','session_ids'}
    if not isinstance(value,dict) or set(value)!=fields: raise ValueError('invalid')
    since,until,observed=(date(value[k]) for k in ('since','until','observed_at'))
    if until-since!=WINDOW or observed<until: raise ValueError('invalid')
    for key in ('tokens','responses','sessions','excluded_sessions','missing_sessions','boundary_sessions'):
        if not _integer(value[key]): raise ValueError('invalid')
    ids=value['session_ids']
    if (not isinstance(ids,list) or len(ids)>2000 or any(not code(x) for x in ids) or ids!=sorted(set(ids))
            or value['sessions']!=len(ids) or not code(value['fingerprint'])): raise ValueError('invalid')
    if (not isinstance(value['limitations'],list) or any(not isinstance(x,str) or x not in LIMITS for x in value['limitations'])
            or value['limitations']!=sorted(set(value['limitations']))): raise ValueError('invalid')
    cohorts=value['cohorts']
    if not isinstance(cohorts,list) or len(cohorts)>MAX_COHORTS: raise ValueError('invalid')
    keys=[]
    for c in cohorts:
        if (not isinstance(c,dict) or set(c)!={'agent','project_id','model','sessions','responses','tokens','median_tokens_per_response'}
                or c['agent'] not in ('codex','claude-code') or not code(c['project_id'])
                or not isinstance(c['model'],str) or not c['model'] or len(c['model'])>256
                or any(unicodedata.category(ch) in ('Cc','Cs') for ch in c['model'])): raise ValueError('invalid')
        if any(not _integer(c[k]) for k in ('sessions','responses','tokens')) or not 0<c['sessions']<=c['responses']:
            raise ValueError('invalid')
        median=c['median_tokens_per_response']
        if type(median) not in (int,float) or not math.isfinite(median) or not 0<=median<=c['tokens']:
            raise ValueError('invalid')
        keys.append((c['agent'],c['project_id'],c['model']))
    if keys!=sorted(set(keys)) or any(sum(c[k] for c in cohorts)!=value[k] for k in ('tokens','responses','sessions')):
        raise ValueError('invalid')
    return json.loads(json.dumps(value,ensure_ascii=False,allow_nan=False))


def validate(records):
    if not isinstance(records,list) or len(records)>MAX_PER_WORK: raise ValueError('limit')
    clean=[];ids=set();open_count=0
    for r in records:
        if (not isinstance(r,dict) or set(r)!={'id','method','parser_version','created_at','trigger','observation','change',
                                              'baseline','status','review','cancelled_at','cancel_note'}
                or not code(r['id']) or r['id'] in ids or type(r['method']) is not int or r['method']!=METHOD
                or not isinstance(r['parser_version'],str) or not re.fullmatch('[a-zA-Z0-9._-]{1,128}',r['parser_version'])
                or not _integer(r['created_at']) or r['trigger'] not in TRIGGERS
                or r['status'] not in ('open','reviewed','cancelled')): raise ValueError('invalid')
        for key in ('observation','change','cancel_note'):
            if text(r[key],required=key=='change')!=r[key]: raise ValueError('invalid')
        baseline=validate_snapshot(r['baseline']);anchor=date(baseline['until'])
        if date(baseline['observed_at'])!=anchor or r['created_at']+1<anchor.timestamp(): raise ValueError('invalid')
        if r['status']=='reviewed':
            review=r['review']
            if (not isinstance(review,dict) or set(review)!={'after','baseline_match','parser_match','context','note'}
                    or type(review['baseline_match']) is not bool or type(review['parser_match']) is not bool
                    or review['context'] not in CONTEXTS or text(review['note'])!=review['note']): raise ValueError('invalid')
            after=validate_snapshot(review['after'])
            if date(after['since'])!=anchor or date(after['until'])!=anchor+WINDOW: raise ValueError('invalid')
        elif r['review'] is not None: raise ValueError('invalid')
        if r['status']=='cancelled':
            if not _integer(r['cancelled_at']) or r['cancelled_at']<r['created_at']: raise ValueError('invalid')
        elif r['cancelled_at'] is not None or r['cancel_note']: raise ValueError('invalid')
        open_count+=r['status']=='open';ids.add(r['id']);clean.append(json.loads(json.dumps(r,ensure_ascii=False,allow_nan=False)))
    if open_count>1: raise ValueError('active')
    return clean


def measure(sessions,members,since,until,observed_at,sources=None):
    """Each session contributes only dated responses wholly inside [since, until).

    Median is computed over per-session response averages, within exact
    agent/project/model cohorts. No whole active-session total becomes a week.
    """
    sources=sources or {};limits=set();found={};cohorts={};ledger=[];included=[]
    for s in sessions:
        identity=session_code(s)
        if identity in members and identity in found and found[identity] is not s: limits.add('duplicate_sessions')
        found.setdefault(identity,s)
    missing=sum(identity not in found for identity in members)
    if missing: limits.add('missing_sessions')
    archive=sources.get('archive') or {}
    if sources.get('skipped') or archive.get('errors') or archive.get('evicted_files'): limits.add('source_incomplete')
    excluded=boundary=events_seen=0
    for identity in sorted(set(members)):
        s=found.get(identity)
        if s is None: continue
        events=getattr(s,'_usage_events',None)
        start,end=event_time(s.started),event_time(s.ended)
        relevant=start is None or end is None or start<until and end>=since
        # A reliable out-of-period session needs no period allocation.
        if not relevant and not any((event_time(e.get('at')) is not None and since<=event_time(e.get('at'))<until)
                                    for e in events or () if isinstance(e,dict)):
            continue
        if (_reason(s) is not None or not s.calls_complete or not s.models_complete or not s.counts_complete
                or not isinstance(events,list)):
            excluded+=1;limits.add('incomplete_usage');continue
        models=set(s.models)|set(s.model_tokens)
        if (s.agent not in ('codex','claude-code') or not isinstance(s.project,str) or not s.project.strip()
                or s.project=='unknown' or len(models)!=1):
            excluded+=1;limits.add('unknown_scope');continue
        model=next(iter(models))
        if (not isinstance(model,str) or not model.strip() or model in ('unknown','<synthetic>') or len(model)>256
                or any(unicodedata.category(c) in ('Cc','Cs') for c in model)):
            excluded+=1;limits.add('unknown_scope');continue
        allocated=empty_tokens();chosen=[];bad=False;crosses=False
        for event in events:
            events_seen+=1
            if events_seen>MAX_EVENTS: limits.add('measurement_limit');bad=True;break
            if not isinstance(event,dict): bad=True;continue
            first,at=event_time(event.get('first')),event_time(event.get('at'))
            if first is None or at is None or first>at:
                bad=True;continue
            tokens=event.get('tokens',{})
            if not isinstance(tokens,dict) or set(tokens)!=set(TOKEN_FIELDS) or any(not _integer(tokens[k]) for k in TOKEN_FIELDS):
                bad=True;continue
            add_tokens(allocated,tokens)
            if first<since<=at or first<until<=at: crosses=True
            elif since<=first<=at<until: chosen.append((first.isoformat(),at.isoformat(),dict(tokens)))
        if bad or len(events)!=s.calls or allocated!=s.tokens:
            excluded+=1;limits.add('incomplete_usage');continue
        if crosses:
            boundary+=1;limits.add('boundary_response');continue
        if not chosen: continue
        key=(s.agent,hashlib.sha256(('project:'+s.project).encode()).hexdigest()[:24],model)
        if key not in cohorts and len(cohorts)>=MAX_COHORTS:
            limits.add('measurement_limit');continue
        n=sum(total(t) for _,_,t in chosen)
        if n+sum(v['tokens'] for v in cohorts.values())>MAX_NUMBER or len(included)>=2000:
            limits.add('measurement_limit');excluded+=1;continue
        value=cohorts.setdefault(key,dict(tokens=0,responses=0,rates=[]))
        value['tokens']+=n;value['responses']+=len(chosen);value['rates'].append(n/len(chosen))
        included.append(identity)
        ledger.extend(digest([identity,*key,*event]) for event in chosen)
    rows=[dict(agent=a,project_id=p,model=m,tokens=v['tokens'],responses=v['responses'],sessions=len(v['rates']),
               median_tokens_per_response=statistics.median(v['rates'])) for (a,p,m),v in sorted(cohorts.items())]
    result=dict(since=since.isoformat(),until=until.isoformat(),observed_at=observed_at.isoformat(),
                tokens=sum(c['tokens'] for c in rows),responses=sum(c['responses'] for c in rows),sessions=len(included),
                excluded_sessions=excluded,missing_sessions=missing,boundary_sessions=boundary,cohorts=rows,
                limitations=sorted(limits),session_ids=sorted(included))
    result['fingerprint']=digest(dict(ledger=sorted(ledger),since=result['since'],until=result['until'],limitations=result['limitations'],
                                      excluded=excluded,missing=missing,boundary=boundary))
    return validate_snapshot(result)


def comparison(record):
    """Only a descriptive within-cohort numeric difference; unknown context stays open."""
    if record['status']!='reviewed': return dict(limitations=[],cohorts=[])
    review=record['review'];before=record['baseline'];after=review['after']
    limits=set(before['limitations'])|set(after['limitations'])
    if not review['baseline_match']: limits.add('baseline_changed')
    if not review['parser_match']: limits.add('parser_changed')
    if review['context']!='similar': limits.add('context_'+review['context'])
    key=lambda c:(c['agent'],c['project_id'],c['model'])
    left={key(c):c for c in before['cohorts']};right={key(c):c for c in after['cohorts']}
    if set(left)!=set(right): limits.add('cohort_changed')
    if not left or any(c['sessions']<MIN_SESSIONS for c in list(left.values())+list(right.values())): limits.add('small_sample')
    if any(c['median_tokens_per_response']==0 for c in left.values()): limits.add('zero_baseline')
    rows=[]
    if not limits:
        for k in sorted(left):
            a,b=left[k],right[k]
            rows.append(dict(agent=k[0],project_id=k[1],model=k[2],before=a['median_tokens_per_response'],after=b['median_tokens_per_response'],
                             change_percent=round((b['median_tokens_per_response']/a['median_tokens_per_response']-1)*100,2)))
    return dict(limitations=sorted(limits),cohorts=rows)
