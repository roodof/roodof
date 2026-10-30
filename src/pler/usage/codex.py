"""Codex rollouts: <CODEX_HOME>/sessions/YYYY/MM/DD/rollout-*.jsonl[.zst] and archived_sessions/.

Per-call usage comes from `token_usage_record` (counted once per response id). Older CLI versions (0.152,
0.155) only write cumulative `token_count` totals; then the session total is the last total and the
per-call split is unknown. Codex input includes cached input and output includes reasoning, so cached and
reasoning tokens are subtracted to make the fields disjoint. `token_count` also carries the subscription
meter (used percent per rate-limit window), which is kept as samples.
"""
import os
from pathlib import Path
import re

from .records import Session, add_tokens, json_row, note_file_issue, percentage, timestamp, total
from .zstd import decoder
from . import accounting, checks, discovery, input_limits

_PATCH = re.compile(r'\*\*\* Begin Patch.*?(?:\*\*\* End Patch|$)', re.S)
_TARGET = re.compile(r'^\*\*\* (?:(?:Add|Update|Delete) File|Move to): (.+?)[ \t]*$', re.M)
_ESCAPE = re.compile(r'\\(.)', re.S)
MAX_EDITED = 200


def roots(skipped=None, access=None, manifest=None):
    base = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex').expanduser()
    return discovery.folders([base],('sessions','archived_sessions'),skipped,access,
                             explicit=bool(os.environ.get('CODEX_HOME')),manifest=manifest)


def files(folders=None, skipped=None, access=None, manifest=None):
    access=access if access is not None else discovery.WslRoots()
    return discovery.files(roots(skipped,access,manifest) if folders is None else folders,
                           lambda name:name.startswith('rollout-') and name.endswith(('.jsonl','.jsonl.zst')),
                           skipped,access,explicit=folders is not None,manifest=manifest)


def _int(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else 0


def _tokens(usage):
    return accounting.tokens(usage,'codex')


def _numbers(value):
    _tokens(value)
    return {name:value[name] for name in ('input_tokens','cached_input_tokens','cache_write_input_tokens',
                                        'output_tokens','reasoning_output_tokens') if name in value}


def _identities(payload, *names):
    """Validate only identities consumed by this record's metadata projection."""
    for name in names:
        if payload.get(name) is not None and not isinstance(payload[name], str):
            raise ValueError('invalid record identity')


def _edited_files(payload):
    """Files named by apply_patch headers in a tool call. Only the target paths are kept, never the patch."""
    found = []
    for text in (payload.get('input'), payload.get('arguments')):
        if not isinstance(text, str) or '*** Begin Patch' not in text:
            continue
        for block in _PATCH.findall(text):
            if not _TARGET.search(block):
                # The patch sits in a quoted string (code or JSON): undo its escapes first.
                block = _ESCAPE.sub(lambda m: {'n': '\n', 'r': '\r', 't': '\t'}.get(m[1], m[1]), block)
            found.extend(_TARGET.findall(block))
    return sorted({path for path in found if 0 < len(path) <= 1024})[:MAX_EDITED]


def _slim(row):
    """The part of a log row that read() uses; text fields are dropped here, before anything is cached."""
    payload = row.get('payload') if isinstance(row.get('payload'), dict) else {}
    kind, sub = row.get('type'), payload.get('type')
    if kind == 'session_meta':
        _identities(payload, 'session_id', 'id', 'parent_thread_id')
        kept = {name: payload[name] for name in ('session_id', 'id', 'cwd', 'cli_version', 'parent_thread_id', 'timestamp')
                if name in payload}
    elif kind == 'turn_context':
        kept = {name: payload[name] for name in ('model', 'effort', 'cwd') if name in payload}
    elif kind == 'token_usage_record':
        _identities(payload, 'response_id')
        kept = dict(response_id=payload.get('response_id'), usage=_numbers(payload.get('usage')))
    elif kind == 'compacted':
        _identities(payload, 'compaction_response_id')
        kept = dict(compaction_response_id=payload.get('compaction_response_id'))
    elif kind == 'event_msg' and sub == 'token_count':
        info = payload.get('info') if isinstance(payload.get('info'), dict) else {}
        limits = payload.get('rate_limits') if isinstance(payload.get('rate_limits'), dict) else {}
        windows = {name: {key: limits[name].get(key) for key in ('used_percent', 'window_minutes', 'resets_at')}
                   for name in ('primary', 'secondary') if isinstance(limits.get(name), dict)}
        kept = dict(type=sub, info=dict(total_token_usage=_numbers(info['total_token_usage']) if info.get('total_token_usage') is not None else None),
                    rate_limits=dict(windows, plan_type=limits.get('plan_type')))
    elif kind == 'event_msg' and sub in ('task_started', 'turn_aborted'):
        _identities(payload, 'turn_id')
        kept = dict(type=sub,turn_id=payload.get('turn_id'))
    elif kind == 'event_msg' and sub == 'task_complete':
        _identities(payload, 'turn_id')
        duration = payload.get('duration_ms')
        if duration is not None:
            accounting.count(duration)
        kept = dict(type=sub,turn_id=payload.get('turn_id'),duration_ms=duration,error=bool(payload.get('error')))
    elif kind == 'event_msg' and sub == 'item_completed':
        item = payload.get('item') if isinstance(payload.get('item'), dict) else {}
        # A finished shell command: its text is classified here and dropped; kind and outcome remain.
        check = checks.classify(item.get('command')) if item.get('type') == 'CommandExecution' else None
        if not check:
            return None
        _identities(item, 'id')
        code = item.get('exit_code')
        kept = dict(type=sub, item_id=item.get('id'), check=check['kind'],
                    outcome=checks.outcome(check, code != 0 if type(code) is int else None))
    elif kind == 'response_item' and sub in ('function_call', 'custom_tool_call'):
        _identities(payload, 'call_id')
        kept = dict(type=sub,name=payload.get('name'),call_id=payload.get('call_id'))
        edited = _edited_files(payload)
        if edited:
            kept['edited_files'] = edited
    else:
        return None
    from .archive import sanitize
    return sanitize('codex',[dict(type=kind,timestamp=row.get('timestamp'),payload=kept)])[0]


def _rows(path, decode):
    """Slim rows in log order; rows that only move the session's first/last time become two timestamps."""
    projection=input_limits.Projection()
    with path.open('rb') as stream:
        stream=input_limits.Source(stream)
        if path.name.endswith('.zst'):
            iterator=getattr(decode,'iter_chunks',None)
            if iterator is None:
                # Compatibility for explicitly injected decoders, still with input/output bounds.
                raw=decode(b''.join(input_limits.chunks(stream,input_limits.MAX_SOURCE_BYTES)))
                if len(raw)>input_limits.MAX_EXPANDED_BYTES:raise input_limits.ReadLimitExceeded()
                parts=(raw[index:index+input_limits.CHUNK_BYTES] for index in range(0,len(raw),input_limits.CHUNK_BYTES))
            else:
                parts=iterator(stream,max_output=input_limits.MAX_EXPANDED_BYTES,max_input=input_limits.MAX_SOURCE_BYTES)
        else:parts=input_limits.chunks(stream,input_limits.MAX_SOURCE_BYTES)
        return _project_lines(input_limits.lines(input_limits.expanded(parts)),projection)


def _project_lines(lines,projection):
    rows,times,incomplete,limited=projection.rows,[],False,False
    for line in lines:
        if line is None:
            incomplete=True;limited=True;continue
        if not line.strip():
            continue
        try:
            row = json_row(line.decode('utf-8','replace'))
            slim = _slim(row)
        except ValueError:
            incomplete = True
            continue
        if slim:
            try:projection.append(slim)
            except input_limits.ReadLimitExceeded:
                incomplete=True;limited=True
                # Finish the bounded source so a compressed tail/CRC cannot escape verification.
                for _ in lines:input_limits.checkpoint()
                break
        elif (moment:=timestamp(row.get('timestamp'))) is not None:
            if not times:
                value=(moment,moment.isoformat());times=[value,value]
            else:
                if moment<times[0][0]:times[0]=(moment,moment.isoformat())
                if moment>times[1][0]:times[1]=(moment,moment.isoformat())
    if times:
        for moment,text in times:
            try:projection.append(dict(timestamp=text))
            except input_limits.ReadLimitExceeded:incomplete=True;limited=True;break
    if incomplete:
        rows.append(dict(type='pler_incomplete_log',**({'reason':'ReadLimitExceeded'} if limited else {})))
    return rows


def read(paths, cache=None, access=None, archive=None):
    """Reconcile logical sessions and response copies before publishing counts."""
    from .reconcile import codex_sessions
    return codex_sessions(paths,cache,_rows,decoder()[0],access,archive)
