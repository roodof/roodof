"""Claude Code transcripts: <config>/projects/<project>/<session>.jsonl (subagents in subfolders).

One model reply is written as several lines (one per content block) that repeat the same usage, and a
resumed session copies earlier lines into its new file. A reply is therefore counted once, by its message
id and request id, across all files; when copies differ, the largest usage is kept.
"""
import os
import math
import re
from pathlib import Path

from .records import Session, add_tokens, json_row, note_file_issue, timestamp, total
from . import accounting, checks, discovery, input_limits, pricing
from .edit_paths import canonical_target
from .cache import ResumeChanged,resume_matches
from .period_usage import event_time, record_response

EDIT_TOOLS = {'Edit': 'file_path', 'MultiEdit': 'file_path', 'Write': 'file_path', 'NotebookEdit': 'notebook_path'}
SHELL_TOOLS = ('Bash', 'PowerShell')
MAX_RESULTS = 1000


def roots(skipped=None, access=None, manifest=None):
    """Claude Code config folders: CLAUDE_CONFIG_DIR (comma-separated allowed), else ~/.config/claude and ~/.claude."""
    configured = os.environ.get('CLAUDE_CONFIG_DIR')
    bases = ([Path(part.strip()).expanduser() for part in configured.split(',') if part.strip()] if configured
             else [Path.home() / '.config' / 'claude', Path.home() / '.claude'])
    return discovery.folders(bases,('projects',),skipped,access,explicit=bool(configured),manifest=manifest)


def files(folders=None, skipped=None, access=None, manifest=None):
    access=access if access is not None else discovery.WslRoots()
    return discovery.files(roots(skipped,access,manifest) if folders is None else folders,
                           lambda name:name.endswith('.jsonl'),skipped,access,explicit=folders is not None,manifest=manifest)


def _tokens(usage):
    return accounting.tokens(usage,'claude-code')


def _int(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else 0


def _zeroed_copy(message, request):
    """Retain only a narrow, unverified repeated-snapshot shape, never a usage estimate.

    Some retained copies zero all primary counts but leave the thinking breakdown unchanged.
    read() must find an exact witness in a valid snapshot before treating this copy as reconciled.
    """
    usage = message.get('usage')
    fields = ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens', 'output_tokens')
    if (not isinstance(usage, dict) or not all(type(usage.get(k)) is int and usage[k] == 0 for k in fields)
            or not isinstance(message.get('id'), str) or not message['id'].strip()
            or not isinstance(request, str) or not request.strip()
            or not isinstance(message.get('model'), str) or not message['model'].strip()
            or message['model'].strip() in ('<synthetic>', 'unknown')):
        return None
    details = usage.get('output_tokens_details')
    thinking = details.get('thinking_tokens') if isinstance(details, dict) else None
    return thinking if type(thinking) is int and 0 < thinking <= accounting.MAX_COUNT else None


def _prompt(message):
    content = message.get('content') if isinstance(message, dict) else None
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, list):
        kinds = [item.get('type') for item in content if isinstance(item, dict)]
        return 'text' in kinds and 'tool_result' not in kinds
    return False


def _lines(path, issues, offset=0, ending=None, resume=None):
    try:
        with open(str(path),'rb') as stream:
            if offset:
                if not resume_matches(stream,resume or {}):raise ResumeChanged()
                stream.seek(offset)
            parts=input_limits.chunks(input_limits.Source(stream),input_limits.MAX_SOURCE_BYTES-offset)
            if ending is not None: parts=ending.watch(parts)
            for line in input_limits.lines(input_limits.expanded(parts)):
                if line is None:
                    note_file_issue(issues,path,'ReadLimitExceeded')
                else:yield line.decode('utf-8','replace')
    except input_limits.ReadLimitExceeded:
        note_file_issue(issues,path,'ReadLimitExceeded')
    except OSError as error:
        note_file_issue(issues, path, type(error).__name__)


def _slim(row, asked=None):
    """Whitelist metadata before caching; retain no prompt, reply, command or tool result.

    `asked` collects the ids of test/build commands seen so far in the file; a tool answer is kept (as
    failed or not) only for those, since an answer always follows its call in the transcript."""
    kind, identity = row.get('type'), row.get('sessionId')
    if not isinstance(identity, str):
        if kind in ('assistant', 'user'):
            raise ValueError('invalid session identity')
        return None
    kept = dict(type=kind if isinstance(kind, str) else None, sessionId=identity,
                timestamp=row.get('timestamp') if timestamp(row.get('timestamp')) else None)
    for name in ('cwd', 'gitBranch', 'version'):
        if isinstance(row.get(name), str):
            kept[name] = row[name]
    if kind == 'user':
        kept.update(prompt=_prompt(row.get('message')), isMeta=bool(row.get('isMeta')),
                    uuid=row.get('uuid') if isinstance(row.get('uuid'), str) else None)
        content = row['message'].get('content') if isinstance(row.get('message'), dict) else None
        if asked and isinstance(content, list):
            results = [dict(id=item['tool_use_id'], error=item.get('is_error') is True) for item in content
                       if isinstance(item, dict) and item.get('type') == 'tool_result' and item.get('tool_use_id') in asked]
            if results:
                kept['results'] = results[:MAX_RESULTS]
    elif kind == 'cost-state' and type(row.get('totalCostUSD')) in (int, float):
        try:
            if not math.isfinite(row['totalCostUSD']):
                raise ValueError('invalid running figure')
            kept['totalCostUSD'] = float(row['totalCostUSD'])
        except OverflowError as error:
            raise ValueError('invalid running figure') from error
    elif kind == 'assistant' and isinstance(row.get('message'), dict):
        message = row['message']
        for value in (message.get('id'), row.get('requestId')):
            if value is not None and not isinstance(value, str):
                raise ValueError('invalid response identity')
        kept.update(requestId=row.get('requestId'), isApiErrorMessage=bool(row.get('isApiErrorMessage')),
                    effort=row.get('effort') if isinstance(row.get('effort'), str) else None)
        quota = row.get('quotaLimits')
        kept['quotaLimits'] = dict(status=quota.get('status') if isinstance(quota, dict) and isinstance(quota.get('status'), str) else None)
        usage = message.get('usage')
        slim_usage = None
        zeroed = _zeroed_copy(message, row.get('requestId'))
        if isinstance(usage, dict) and usage and zeroed is None:
            _tokens(usage)
            slim_usage = {name: _int(usage.get(name)) for name in
                          ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens', 'output_tokens')}
            details = usage.get('output_tokens_details')
            slim_usage['output_tokens_details'] = dict(thinking_tokens=_int(details.get('thinking_tokens')) if isinstance(details, dict) else 0)
            # Price inputs only: 1-hour cache writes cost more than 5-minute ones; speed/region change the rate.
            written = usage.get('cache_creation')
            if isinstance(written, dict):
                try:
                    hour=accounting.count(written.get('ephemeral_1h_input_tokens',0))
                    five=accounting.count(written.get('ephemeral_5m_input_tokens',slim_usage['cache_creation_input_tokens']-hour))
                    if hour+five!=slim_usage['cache_creation_input_tokens']:raise ValueError('inconsistent write split')
                    slim_usage['ephemeral_1h_input_tokens']=hour
                except ValueError:slim_usage['price_inputs_complete']=False
            elif written is not None:slim_usage['price_inputs_complete']=False
            for name in ('speed', 'inference_geo'):
                value=usage.get(name)
                if isinstance(value,str) and re.fullmatch('[A-Za-z0-9_-]{1,32}',value):slim_usage[name]=value
                elif value is not None:slim_usage['price_inputs_complete']=False
            if usage.get('service_tier') not in (None,'standard'):slim_usage['price_inputs_complete']=False
        blocks = []
        for item in message.get('content') if isinstance(message.get('content'), list) else []:
            if not isinstance(item, dict) or item.get('type') != 'tool_use' or not isinstance(item.get('name'), str):
                continue
            field = EDIT_TOOLS.get(item['name'])
            value = item.get('input', {}).get(field) if field and isinstance(item.get('input'), dict) else None
            block = dict(type='tool_use', name=item['name'], id=item.get('id') if isinstance(item.get('id'), str) else None,
                         input={field: value} if isinstance(value, str) and value else {})
            if item['name'] in SHELL_TOOLS and isinstance(item.get('input'), dict):
                # The command is classified here and dropped; only the kind and a trust flag remain.
                check = checks.classify(item['input'].get('command'))
                if check:
                    block.update(check=check['kind'], known=check['known'] and item['input'].get('run_in_background') is not True)
                    if asked is not None and isinstance(block['id'], str):
                        asked.add(block['id'])
            blocks.append(block)
        kept['message'] = dict(id=message.get('id'), model=message.get('model') if isinstance(message.get('model'), str) else None,
                               usage=slim_usage, content=blocks)
        if zeroed is not None:
            kept['message']['zeroed_usage_thinking'] = zeroed
    from .archive import sanitize
    return sanitize('claude-code',[kept])[0]


def _resumed(rows, resume):
    """The rows, projected size, malformed flag and asked ids a grown transcript's earlier read ended with,
    before its closing row; None when the stored point does not fit those rows."""
    state, size = resume.get('state'), resume.get('size')
    if not isinstance(state, dict) or type(size) is not int:
        return None
    malformed, asked = state.get('malformed'), state.get('asked')
    if type(malformed) is not bool or not isinstance(asked, list) or not all(isinstance(value, str) for value in asked):
        return None
    closing = [dict(type='pler_file_issue', reason='MalformedRows')] if malformed else []
    body = len(rows) - len(closing)
    if body < 0 or rows[body:] != closing:
        return None
    return rows[:body], size, malformed, set(asked)


def _rows(path, resume=None, point=None):
    try:return _read_rows(path,resume,point)
    except ResumeChanged:
        if point is not None:point.clear()
        return _read_rows(path,None,point)


def _read_rows(path, resume=None, point=None):
    """`resume` (rows, point) from the cache continues a transcript that has only grown since that read;
    `point`, when given, receives where a later read may continue: a read to a line end without an issue."""
    projection=input_limits.Projection()
    rows, issues, malformed, asked = projection.rows, [], False, set()
    restored = _resumed(*resume) if resume is not None else None
    offset, ending = 0, input_limits.Ending()
    if restored is not None:
        body, projection.bytes, malformed, asked = restored
        rows.extend(body); offset = resume[1]['offset']
    for line in _lines(path,issues,offset,ending,resume[1] if restored is not None else None):
        if not line.strip():
            continue
        try:
            row = _slim(json_row(line), asked)
            if row is not None:
                projection.append(row)
        except input_limits.ReadLimitExceeded:
            note_file_issue(issues,path,'ReadLimitExceeded');break
        except ValueError:
            malformed = True
    if point is not None and not issues and ending.newline:
        point.update(offset=offset+ending.size, size=projection.bytes, state=dict(malformed=malformed, asked=sorted(asked)))
    if malformed and not issues:
        issues.append((str(path), 'MalformedRows'))
    rows.extend(dict(type='pler_file_issue', reason=reason) for _, reason in issues)
    return rows


def read(paths, skipped=None, cache=None, access=None, archive=None):
    """Merge copies before attribution; source order never determines a project's usage."""
    from collections import defaultdict
    sessions, replies, prompts, answers = {}, defaultdict(list), defaultdict(list), {}
    projects, branches, source_paths = defaultdict(set), defaultdict(set), defaultdict(set)
    if access is not None: access.read_phase()
    live=discovery.unique(paths)
    replay=archive.replay('claude-code') if archive is not None else []
    for original in live+discovery.unique(replay):
        input_limits.checkpoint()
        try:input_limits.available()
        except input_limits.ReadLimitExceeded:
            note_file_issue(skipped,original,'ReadLimitExceeded');continue
        admitted=False
        path=original
        archived=str(original) not in {str(value) for value in live}
        rows=archive.rows('claude-code',path) if archived else None
        if not archived:
            path=discovery.local(path,skipped,access)
            if path is None:
                rows=archive.rows('claude-code',original,unreadable=True) if archive is not None else None
                if rows is None: continue
                path=original;archived=True
        try:
            if archive is not None and not archived: archive.begin('claude-code',path)
            if not archived:
                rows=cache.get(path) if cache else None
            if rows is None and not archived:
                point={}
                rows=_rows(path,cache.grown(path) if cache else None,point)
                input_limits.admit(rows);admitted=True
                if cache and not any(row.get('type')=='pler_file_issue' and row['reason']!='MalformedRows' for row in rows):
                    cache.put(path,rows,point)
            if rows is not None and not admitted:
                input_limits.admit(rows);admitted=True
            if archive is not None and not archived:
                partial=any(row.get('type')=='pler_file_issue' and row['reason']!='MalformedRows' for row in rows)
                if partial:
                    for row in rows:
                        if row.get('type')=='pler_file_issue': note_file_issue(skipped,path,row['reason'])
                    prior=archive.rows('claude-code',path,unreadable=True)
                    if prior is not None:
                        input_limits.admit(prior)
                        rows=prior
                else: archive.observe('claude-code',path,rows,cache.checksum(path) if cache else None)
        except input_limits.ReadLimitExceeded:
            note_file_issue(skipped,path,'ReadLimitExceeded');continue
        except OSError as error:
            note_file_issue(skipped,path,type(error).__name__)
            rows=archive.rows('claude-code',path,unreadable=True) if archive is not None else None
            if rows is None: continue
        if rows is None: continue
        try:
            if not admitted:input_limits.admit(rows)
        except input_limits.ReadLimitExceeded:
            note_file_issue(skipped,path,'ReadLimitExceeded');continue
        affected,name,current=[],str(path),None
        for index,row in enumerate(rows):
            if row.get('type')=='pler_file_issue':
                note_file_issue(skipped,path,row['reason'])
                for session in affected:
                    session.tokens_complete=False;session.issues.add('invalid_records')
                continue
            identity=row.get('sessionId')
            if not isinstance(identity,str): continue
            if identity!=current:
                # A file's rows almost always share one session; its source facts are recorded once per run.
                current=identity
                session=sessions.get(identity)
                if session is None: session=sessions[identity]=Session('claude-code',identity,name)
                source_paths[identity].add(name)
                if archive is not None: archive.mark(session,'claude-code',path)
                session.source=min(session.source,name)
                if session not in affected: affected.append(session)
            moment=timestamp(row.get('timestamp'));session.seen(moment)
            if isinstance(row.get('cwd'),str) and row['cwd']: projects[identity].add(row['cwd'])
            if isinstance(row.get('gitBranch'),str) and row['gitBranch']: branches[identity].add(row['gitBranch'])
            if isinstance(row.get('version'),str): session.client_version=row['version']
            kind=row.get('type')
            if kind=='user' and isinstance(row.get('results'),list):
                for result in row['results']: answers.setdefault(result['id'],result['error'])
            if kind=='pler_archive_ambiguous':
                session.tokens_complete=False;session.calls_complete=False;session.counts_complete=False
                session.issues.update(('archive_unverified','unidentified_records'))
            elif kind=='cost-state' and type(row.get('totalCostUSD')) in (int,float):
                session.reported_cost_usd=max(session.reported_cost_usd or 0.0,float(row['totalCostUSD']))
            elif kind=='user' and not row.get('isMeta') and row.get('prompt'):
                uid=row.get('uuid')
                key=('prompt',uid) if isinstance(uid,str) and uid else ('anonymous',str(path),index)
                prompts[key].append(session)
                if key[0]=='anonymous': session.counts_complete=False;session.issues.add('unidentified_records')
            elif kind=='assistant' and isinstance(row.get('message'),dict):
                message=row['message']
                key=(message.get('id'),row.get('requestId'))
                if any(v is not None and not isinstance(v,str) for v in key):
                    note_file_issue(skipped,path,'MalformedRows');session.tokens_complete=False;continue
                if key==(None,None):
                    key=('anonymous',str(path),index)
                    session.calls_complete=False;session.tokens_complete=False;session.issues.add('unidentified_records')
                usage=message.get('usage')
                tokens=_tokens(usage) if usage and message.get('model')!='<synthetic>' else None
                replies[key].append(dict(session=session,message=message,row=row,at=moment,tokens=tokens,path=str(path),index=index,
                                         usage_at=event_time(row.get('timestamp'))))
    for identity,session in sessions.items():
        accounting.metadata(session,projects[identity],branches[identity])
    related={identity:identity for identity in sessions}
    def root(identity):
        while related[identity]!=identity:
            related[identity]=related[related[identity]]
            identity=related[identity]
        return identity
    def join(values):
        ids=sorted({session.session_id for session in values})
        if not ids: return
        for identity in ids[1:]:
            a,b=root(ids[0]),root(identity)
            related[max(a,b)]=min(a,b)
    for values in prompts.values():
        join(values)
        accounting.owner(values).prompts+=1
    for copies in replies.values():
        join([copy['session'] for copy in copies])
        target=accounting.owner([c['session'] for c in copies])
        target.errors+=any(c['row'].get('isApiErrorMessage') for c in copies)
        statuses={c['row'].get('quotaLimits',{}).get('status') for c in copies}
        statuses={value for value in statuses if isinstance(value,str) and value}
        status='rejected' if 'rejected' in statuses else sorted(statuses)[0] if statuses else None
        target.count(target.quota_events,status)
        times=[c['at'] for c in copies if c['at']]
        if status=='rejected' and times: target.limit_hits.append(min(times))
        values=[c['tokens'] for c in copies if c['tokens'] is not None]
        selected=accounting.largest(values) if values else None
        for copy in copies:
            thinking=copy['message'].get('zeroed_usage_thinking')
            if thinking is None: continue
            witnesses=[c for c in copies if c['tokens'] is not None and c['tokens']==selected
                       and c['message'].get('model')==copy['message']['model']
                       and c['tokens']['reasoning']==thinking]
            if witnesses:
                target.issues.add('reconciled_copies')
            else:
                note_file_issue(skipped,copy['path'],'InconsistentReasoning')
                copy['session'].tokens_complete=False;copy['session'].issues.add('invalid_records')
                target.tokens_complete=False;target.issues.add('invalid_records')
        if values:
            target.calls+=1
            tokens=selected
            if tokens is None:
                target.tokens_complete=False;target.issues.add('conflicting_usage')
            else:
                add_tokens(target.tokens,tokens)
                model=accounting.model_for([c['message'].get('model') for c in copies])
                target.count(target.models,model);target.count(target.model_tokens,model,total(tokens))
                witnesses=[c['message'].get('usage') or {} for c in copies if c['tokens']==tokens]
                # Only US-only inference ('us') costs more. Claude Code logged 'not_available' for every response
                # before the region was reported (seen until 2026-10-08), the same evidence as an absent field.
                args=[(_int(w.get('ephemeral_1h_input_tokens')),w.get('price_inputs_complete',True) and
                       w.get('speed') in (None,'standard') and w.get('inference_geo') in (None,'global','not_available'))
                      for w in witnesses]
                quotes={pricing.response_cost('claude-code',model,tokens,*a) for a in args}
                # Content-block copies must agree on pricing evidence, regardless of file/row order.
                usd=pricing.charge(target,'claude-code',model,tokens,*args[0]) if len(quotes)==1 and None not in quotes else None
                if any(isinstance(value,str) and value.strip() for copy in copies
                       for value in (copy['message'].get('id'),copy['row'].get('requestId'))):
                    record_response(target,tokens,copies,usd)
                if model=='unknown': target.models_complete=False;target.issues.add('unknown_model')
                efforts={c['row'].get('effort') for c in copies if isinstance(c['row'].get('effort'),str)}
                if len(efforts)==1: target.count(target.efforts,next(iter(efforts)))
        tools={}
        for copy in copies:
            for index,item in enumerate(copy['message'].get('content') or []):
                if item.get('type')!='tool_use' or not isinstance(item.get('name'),str): continue
                uid=item.get('id')
                key=('tool',uid) if isinstance(uid,str) and uid else ('anonymous',copy['path'],copy['index'],index)
                if key[0]=='anonymous': target.counts_complete=False;target.issues.add('unidentified_records')
                tools.setdefault(key,[]).append((item,copy['row'].get('cwd')))
        for key,items in tools.items():
            names={item['name'] for item,_ in items}
            name=next(iter(names)) if len(names)==1 else 'unknown'
            target.count(target.tools,name)
            kinds={item.get('check') for item,_ in items}
            if len(kinds)==1 and next(iter(kinds)) in (checks.TEST,checks.BUILD):
                known=all(item.get('known') is True for item,_ in items)
                failed=answers.get(key[1]) if key[0]=='tool' else None
                target.record_check(next(iter(kinds)),checks.outcome(dict(known=known),failed),
                                    min((c['at'] for c in copies if c['at']),default=None))
            for item,cwd in items:
                field=EDIT_TOOLS.get(item['name'])
                value=item.get('input',{}).get(field) if field else None
                value=canonical_target(value,cwd)
                if value is not None: target.files_edited.add(value)
    for session in sessions.values():
        session.note('Usage per reply as logged by Claude Code; repeated lines of one reply counted once.')
    def subagent_only(session):
        sources=source_paths[session.session_id]
        def child(value):
            parts=str(value).replace('\\','/').split('/')
            return len(parts)>1 and parts[-2]=='subagents' and parts[-1].startswith('agent-')
        return all(child(value) for value in sources)
    main_groups={root(identity) for identity,session in sessions.items() if not subagent_only(session)}
    accounting.history_groups(sessions,root,(identity for identity in sessions if root(identity) not in main_groups))
    return [s for s in sessions.values() if s.calls or s.prompts or s.errors]
