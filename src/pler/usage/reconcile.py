"""Reconcile Codex file copies, response snapshots and cumulative checkpoints before assigning totals."""
from collections import defaultdict
import os
from pathlib import Path

from . import accounting as rules
from . import discovery,input_limits,pricing
from .records import TOKEN_FIELDS,Session,add_tokens,empty_tokens,note_file_issue,percentage,timestamp,total
from .projects import ProjectRoots
from .edit_paths import canonical_target
from .period_usage import event_time, record_response


def _lockstep(rows):
    """Whether one file's own response records explain its cumulative meter (ACCOUNTING.md, "Compacted and
    forked Codex threads"): (state, client versions), state None when they do not.

    Between two checkpoints with no compaction between them, records and meter grow by exactly the same
    amounts. Across a compaction the records may only gain: the meter omits the compaction request. Every
    compaction follows a checkpoint, except a compaction marker that a thread naming a parent thread carries
    before its own first record and checkpoint: that is the parent's history copied into the thread. The first
    checkpoint equals the records so far ('records', or 'quiet' without records); only a thread naming a parent
    thread, with no records yet, may start from a different counter. With records later in the file that
    counter is inherited ('records'). Without any, the state is 'inherited': the caller accepts it only when
    its client versions wrote response records elsewhere in the session (that format records every call,
    so the thread made none; an older cumulative-only thread is not explained). Records after the last
    checkpoint have no meter evidence either way, as in any other session."""
    seen,own,gap,compacted,inherited,offset,versions={},empty_tokens(),None,False,False,False,set()
    for row in rows:
        payload=row.get('payload') if isinstance(row.get('payload'),dict) else {}
        kind=row.get('type')
        if kind=='session_meta':
            inherited=inherited or isinstance(payload.get('parent_thread_id'),str) and bool(payload['parent_thread_id'])
            if isinstance(payload.get('cli_version'),str) and payload['cli_version']: versions.add(payload['cli_version'])
        elif kind=='compacted':
            if gap is None:
                if inherited and not seen: continue
                return None,versions
            compacted=True
        elif kind=='token_usage_record' and isinstance(payload.get('usage'),dict):
            key=payload.get('response_id')
            if not (isinstance(key,str) and key): return None,versions
            try: tokens=rules.tokens(payload['usage'],'codex')
            except ValueError: return None,versions
            if key in seen:
                if seen[key]!=tokens: return None,versions
                continue
            seen[key]=tokens
            add_tokens(own,tokens)
        elif kind=='event_msg' and payload.get('type')=='token_count':
            info=payload.get('info') if isinstance(payload.get('info'),dict) else {}
            if not isinstance(info.get('total_token_usage'),dict): continue
            try: meter=rules.tokens(info['total_token_usage'],'codex')
            except ValueError: return None,versions
            now=tuple(own[key]-meter[key] for key in TOKEN_FIELDS)
            if gap is None:
                offset=any(now)
                if offset and (seen or not inherited): return None,versions
            elif compacted:
                if any(after<before for before,after in zip(gap,now)): return None,versions
            elif now!=gap: return None,versions
            gap,compacted=now,False
    return ('records' if seen else 'inherited' if offset else 'quiet'),versions


def codex_sessions(paths,cache,reader,decode,access=None,archive=None):
    sessions,streams,issues,projects = {},[],[],defaultdict(set)
    parents,threads,compactions,activity = defaultdict(list),defaultdict(set),set(),set()
    responses,events,checkpoints,locations = defaultdict(list),defaultdict(list),defaultdict(list),defaultdict(list)
    related = {}
    project_roots,project_keys = ProjectRoots(),{}
    def project_key(value):
        if value not in project_keys:
            found=project_roots._git_root(value)
            # Group only a safely observed repository or equivalent path spelling. The UI's
            # temporary-folder bucket is not evidence that two working projects are identical.
            canonical=os.path.normpath(found or value)
            project_keys[value]=(os.path.normcase(canonical),canonical)
        return project_keys[value]
    def root(key):
        related.setdefault(key,key)
        while related[key]!=key:
            key=related[key]
        return key
    def join(a,b):
        a,b=root(a),root(b)
        related[max(a,b)]=min(a,b)
    def incomplete_history(session,ownership=False):
        session.tokens_complete=False
        session.issues.add('unreconciled_totals')
        if ownership:
            session._history_uncertain=True
            session.attribution_complete=False
            session.issues.add('shared_attribution')
    if access is not None: access.read_phase()
    live=discovery.unique(paths)
    replay=archive.replay('codex') if archive is not None else []
    for original in live+discovery.unique(replay):
        input_limits.checkpoint()
        try:input_limits.available()
        except input_limits.ReadLimitExceeded:
            note_file_issue(issues,original,'ReadLimitExceeded');continue
        admitted=False
        path=original
        archived=str(original) not in {str(value) for value in live}
        rows=archive.rows('codex',path) if archived else None
        if not archived:
            path=discovery.local(path,issues,access)
            if path is None:
                rows=archive.rows('codex',original,unreadable=True) if archive is not None else None
                if rows is None: continue
                path=original;archived=True
        try:
            if archive is not None and not archived: archive.begin('codex',path)
            if not archived: rows=cache.get(path) if cache else None
            if rows is None and not archived:
                point={}
                rows=reader(path,decode,cache.grown(path) if cache else None,point)
                input_limits.admit(rows);admitted=True
                if cache: cache.put(path,rows,point)
            if rows is not None and not admitted:
                input_limits.admit(rows);admitted=True
            if archive is not None and not archived: archive.observe('codex',path,rows,cache.checksum(path) if cache else None)
        except input_limits.ReadLimitExceeded:
            note_file_issue(issues,path,'ReadLimitExceeded');continue
        except (OSError,ValueError,RuntimeError) as error:
            note_file_issue(issues,path,type(error).__name__)
            rows=archive.rows('codex',path,unreadable=True) if archive is not None else None
            if rows is None: continue
        if rows is None: continue
        try:
            if not admitted:input_limits.admit(rows)
        except input_limits.ReadLimitExceeded:
            note_file_issue(issues,path,'ReadLimitExceeded');continue
        metas=[r.get('payload',{}) for r in rows if r.get('type')=='session_meta']
        ids=[m.get('session_id') or m.get('id') for m in metas]
        identity=next((v for v in reversed(ids) if isinstance(v,str) and v),str(path))
        session=sessions.setdefault(identity,Session('codex',identity,str(path)))
        if not any(isinstance(value,str) and value for value in ids):
            session._history_uncertain=True
        if archive is not None: archive.mark(session,'codex',path)
        session.source=min(session.source,str(path))
        root(identity)
        for meta in metas:
            if isinstance(meta.get('cwd'),str) and meta['cwd']: projects[identity].add(meta['cwd'])
            if isinstance(meta.get('cli_version'),str): session.client_version=meta['cli_version']
            own=[meta[name] for name in ('id','session_id') if isinstance(meta.get(name),str) and meta[name]]
            threads[identity].update(own)
            if isinstance(meta.get('parent_thread_id'),str) and meta['parent_thread_id']:
                parents[identity].append((own[0] if own else None,meta['parent_thread_id']))
            session.seen(timestamp(meta.get('timestamp')))
        streams.append((path,session,rows))
    for identity,session in sessions.items():
        # Subagent threads of one Codex session share its session_id and name the root or a sibling
        # thread as parent. That lineage stays inside the merged session; only outside parents count.
        candidates={parent for _,parent in parents[identity] if parent not in threads[identity]}
        if any(thread==parent for thread,parent in parents[identity]) or len(candidates)>1:
            # Self-parent or contradictory metadata is not a file-order tie-breaker.
            incomplete_history(session,ownership=True)
        elif candidates:
            session.parent_id=next(iter(candidates))
    checked,cyclic=set(),set()
    for identity in sessions:
        trail={}
        current=identity
        while current in sessions and current not in checked:
            if current in trail:
                cyclic.update(list(trail)[trail[current]:])
                break
            trail[current]=len(trail)
            current=sessions[current].parent_id
        checked.update(trail)
    for identity in cyclic:
        sessions[identity].parent_id=None
        incomplete_history(sessions[identity],ownership=True)
    for identity,session in sessions.items():
        if session.parent_id in sessions: join(identity,session.parent_id)
    # A session whose every file passes _lockstep is counted completely by its response records: it needs
    # neither the compaction warning nor a cumulative residual.
    found=defaultdict(list)
    for path,session,rows in streams: found[session.session_id].append(_lockstep(rows))
    explained=set()
    for identity,states in found.items():
        recorded=set().union(*(versions for state,versions in states if state=='records'))
        if all(state in ('records','quiet') or state=='inherited' and versions and versions<=recorded
               for state,versions in states):
            explained.add(identity)
    # First collect all response owners. Copied anonymous events are compared only within related histories.
    for path,session,rows in streams:
        model=None
        for index,row in enumerate(rows):
            moment=timestamp(row.get('timestamp'))
            session.seen(moment)
            payload=row.get('payload') if isinstance(row.get('payload'),dict) else {}
            kind,sub=row.get('type'),payload.get('type')
            if kind=='pler_archive_ambiguous':
                session.tokens_complete=False;session.calls_complete=False;session.counts_complete=False
                session.issues.update(('archive_unverified','unidentified_records'))
            elif kind=='pler_incomplete_log':
                note_file_issue(issues,path,'ReadLimitExceeded' if row.get('reason')=='ReadLimitExceeded' else 'MalformedRows')
                session.tokens_complete=False
                session.issues.add('invalid_records')
            elif kind=='compacted':
                compactions.add(session.session_id)
                if session.session_id not in explained: incomplete_history(session)
            elif kind=='turn_context':
                if isinstance(payload.get('model'),str): model=payload['model']
                if isinstance(payload.get('cwd'),str) and payload['cwd']:
                    projects[session.session_id].add(payload['cwd'])
                session.count(session.efforts,payload.get('effort') if isinstance(payload.get('effort'),str) else None)
            elif kind=='token_usage_record' and isinstance(payload.get('usage'),dict):
                try: tokens=rules.tokens(payload['usage'],'codex')
                except ValueError:
                    note_file_issue(issues,path,'MalformedRows')
                    session.tokens_complete=False;session.issues.add('invalid_records');continue
                identity=payload.get('response_id')
                key=('response',identity) if isinstance(identity,str) and identity else ('anonymous',str(path),index)
                responses[key].append(dict(session=session,tokens=tokens,model=model,path=str(path),index=index,at=moment,
                                          usage_at=event_time(row.get('timestamp'))))
                locations[(session.session_id,key)].append((str(path),index,moment))
                if key[0]=='anonymous':
                    session.calls_complete=False;session.tokens_complete=False;session.issues.add('unidentified_records')
            elif kind=='event_msg' and sub=='token_count':
                info=payload.get('info') or {}
                if isinstance(info.get('total_token_usage'),dict):
                    checkpoints[session.session_id].append(dict(tokens=rules.tokens(info['total_token_usage'],'codex'),
                                                                 path=str(path),index=index,at=moment))
                limits=payload.get('rate_limits') or {}
                plan=limits['plan_type'] if isinstance(limits.get('plan_type'),str) and limits['plan_type'] else None
                if plan: session.quota_plan=plan
                for name in ('primary','secondary'):
                    window=limits.get(name) if isinstance(limits.get(name),dict) else {}
                    used,minutes=percentage(window.get('used_percent')),window.get('window_minutes')
                    if moment and used is not None and type(minutes) is int and minutes>0:
                        # The logged plan travels with each sample: a change bounds which samples describe one limit.
                        sample=(moment,minutes,used,timestamp(window.get('resets_at')),plan)
                        if sample not in session.quota: session.quota.append(sample)
    for candidates in responses.values():
        ids=sorted({c['session'].session_id for c in candidates})
        for identity in ids[1:]: join(ids[0],identity)
    groups=defaultdict(set)
    for identity in sessions:
        groups[root(identity)].add(identity)
    for identity in checkpoints:
        session=sessions[identity]
        if session.parent_id and session.parent_id not in sessions:
            incomplete_history(session)
        group=groups[root(identity)]
        if len(group)>1:
            # Different retained session counters do not prove disjoint history. Keep their
            # existing numbers, but never present an unproven parent/child sum as complete.
            for member in group:
                incomplete_history(sessions[member])
    for identity,session in sessions.items():
        evidence={}
        for value in sorted(projects[identity]):
            key,canonical=project_key(value)
            evidence.setdefault(key,canonical)
        rules.metadata(session,evidence)
        if len(evidence)==1:
            # Retain the reader's original spelling for a single logged path, while ownership
            # comparisons use canonical evidence even across different native session IDs.
            session.project=next(iter(projects[identity])) if len(projects[identity])==1 else next(iter(evidence.values()))
    for path,session,rows in streams:
        occurrences=defaultdict(int)
        cwd=None
        for row in rows:
            payload=row.get('payload') if isinstance(row.get('payload'),dict) else {}
            kind,sub=row.get('type'),payload.get('type')
            if kind in ('session_meta','turn_context') and isinstance(payload.get('cwd'),str) and payload['cwd']:
                cwd=payload['cwd']
            if isinstance(payload.get('edited_files'),list):
                # Patch targets may be relative to the working folder of that moment.
                payload=dict(payload,edited_files=[value for value in
                    (canonical_target(p,cwd) for p in payload['edited_files']) if value is not None])
            if not (kind=='event_msg' and sub in ('task_started','task_complete','turn_aborted','item_completed')
                    or kind=='response_item' and sub in ('function_call','custom_tool_call')): continue
            if sub=='item_completed':
                payload=dict(payload,at=timestamp(row.get('timestamp')))
            identity=(payload.get('call_id') if kind=='response_item' else
                      payload.get('item_id') if sub=='item_completed' else payload.get('turn_id'))
            if isinstance(identity,str) and identity:
                key=(sub,identity)
            else:
                signature=rules.fingerprint(row)
                nth=occurrences[signature];occurrences[signature]+=1
                key=(sub,root(session.session_id),signature,nth)
                session.counts_complete=False;session.issues.add('unidentified_records')
            events[key].append((session,payload))
    chosen={}
    for key,candidates in responses.items():
        target=rules.owner([c['session'] for c in candidates])
        value=rules.largest([c['tokens'] for c in candidates])
        chosen[key]=value
        target.calls+=1
        if value is None:
            target.tokens_complete=False;target.issues.add('conflicting_usage');continue
        add_tokens(target.tokens,value)
        model=rules.model_for([c['model'] for c in candidates])
        target.count(target.models,model)
        target.count(target.model_tokens,model,total(value))
        usd=pricing.charge(target,'codex',model,value)  # Codex logs no service tier; the standard tier is assumed
        if key[0]=='response' and key[1].strip(): record_response(target,value,candidates,usd)
        if model=='unknown': target.models_complete=False;target.issues.add('unknown_model')
    residuals=defaultdict(list)
    for identity,values in checkpoints.items():
        session=sessions[identity]
        if identity in explained: continue
        # Decreasing checkpoints can be a reset or a changed accounting boundary. Do not present
        # a maximum from the retained records as a proven complete lifetime total.
        for path in {v['path'] for v in values}:
            ordered=sorted((v for v in values if v['path']==path),key=lambda v:v['index'])
            if any(not rules.dominates(b['tokens'],a['tokens']) for a,b in zip(ordered,ordered[1:])):
                session.tokens_complete=False;session.issues.add('unreconciled_totals')
        value=rules.largest([v['tokens'] for v in values])
        if value is None:
            session.tokens_complete=False;session.issues.add('unreconciled_totals');continue
        equivalent=[v for v in values if v['tokens']==value]
        selected=sorted(equivalent,key=lambda v:(v['at'].isoformat() if v['at'] else '',v['index'],v['path']))[-1]
        covered,uncertain=set(),False
        for (sid,key),occurrences in locations.items():
            if sid!=identity: continue
            for path,index,moment in occurrences:
                if any(path==v['path'] and index<=v['index'] for v in equivalent):
                    covered.add(key);break
                if moment and selected['at'] and moment<selected['at']:
                    covered.add(key);break
                if path!=selected['path'] and (moment is None or selected['at'] is None or moment==selected['at']): uncertain=True
        before=empty_tokens()
        for key in covered:
            if chosen[key] is None: uncertain=True
            else:
                included=[c['tokens'] for c in responses[key] if c['session'].session_id==identity and
                          (any(c['path']==v['path'] and c['index']<=v['index'] for v in equivalent)
                           or c['at'] and selected['at'] and c['at']<selected['at'])]
                if not included or rules.largest(included)!=chosen[key]: uncertain=True
                add_tokens(before,chosen[key])
        if uncertain or not rules.dominates(value,before):
            session.tokens_complete=False;session.issues.add('unreconciled_totals');continue
        residual=rules.subtract(value,before)
        if total(residual):
            # Identical cumulative history can be replayed by related threads. Count that evidence once,
            # mark uncertain ownership, and never invent a model for the residual.
            signature=(root(identity),selected['at'],tuple(residual.values()))
            residuals[signature].append((session,residual))
            session.calls_complete=False;session.models_complete=False
            session.issues.add('cumulative_usage')
            session.note('Older Codex log: session total includes cumulative usage; per-call split unknown.')
    for entries in residuals.values():
        target=rules.owner([entry[0] for entry in entries])
        value=entries[0][1]
        add_tokens(target.tokens,value)
        target.count(target.model_tokens,'unknown',total(value))
        if len(entries)>1:
            target.tokens_complete=False;target.issues.add('unreconciled_totals')
    for candidates in events.values():
        target=rules.owner([s for s,_ in candidates])
        activity.add(target.session_id)
        payloads=[p for _,p in candidates]
        sub=payloads[0]['type']
        if sub=='task_started': target.prompts+=1
        elif sub=='turn_aborted': target.aborted+=1
        elif sub=='task_complete':
            target.errors+=any(p.get('error') for p in payloads)
            durations=[p['duration_ms'] for p in payloads if type(p.get('duration_ms')) is int]
            if durations: target.active_ms=(target.active_ms or 0)+max(durations)
        elif sub=='item_completed':
            # Copies of one finished command agree on the outcome unless a log was altered.
            kinds,outcomes={p['check'] for p in payloads},{p['outcome'] for p in payloads}
            target.record_check(next(iter(kinds)) if len(kinds)==1 else payloads[0]['check'],
                                next(iter(outcomes)) if len(outcomes)==1 else 'unknown',
                                min((p['at'] for p in payloads if p['at']),default=None))
        else:
            names={p.get('name') for p in payloads if isinstance(p.get('name'),str)}
            target.count(target.tools,next(iter(names)) if len(names)==1 else 'unknown')
            for p in payloads: target.files_edited.update(p.get('edited_files') or ())
    for session in sessions.values():
        session.quota.sort(key=lambda sample:sample[0])
        if 'codex-auto-review' in session.model_tokens:
            session.note('codex-auto-review is a routing alias; the effective model is not logged.')
        if session.quota: session.note('Quota samples are account-wide; concurrent sessions move the same meter.')
    rules.history_groups(sessions,root,(identity for identity,s in sessions.items()
                                      if s.parent_id and s.parent_id not in sessions))
    return [s for s in sessions.values() if total(s.tokens) or s.calls or s.prompts or s.errors
            or s.quota or s.session_id in activity or s.session_id in compactions
            or 'invalid_records' in s.issues],issues
