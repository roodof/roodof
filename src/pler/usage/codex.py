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
from . import accounting, discovery

_PATCH = re.compile(r'\*\*\* Begin Patch.*?(?:\*\*\* End Patch|$)', re.S)
_TARGET = re.compile(r'^\*\*\* (?:(?:Add|Update|Delete) File|Move to): (.+?)[ \t]*$', re.M)
_ESCAPE = re.compile(r'\\(.)', re.S)
MAX_EDITED = 200


def roots(skipped=None):
    base = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex').expanduser()
    return discovery.folders([base],('sessions','archived_sessions'),skipped)


def files(folders=None, skipped=None):
    return discovery.files(roots(skipped) if folders is None else folders,
                           lambda name:name.startswith('rollout-') and name.endswith(('.jsonl','.jsonl.zst')),skipped)


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
    elif kind == 'response_item' and sub in ('function_call', 'custom_tool_call'):
        _identities(payload, 'call_id')
        kept = dict(type=sub,name=payload.get('name'),call_id=payload.get('call_id'))
        edited = _edited_files(payload)
        if edited:
            kept['edited_files'] = edited
    else:
        return None
    return dict(type=kind, timestamp=row.get('timestamp'), payload=kept)


def _rows(path, decode):
    """Slim rows in log order; rows that only move the session's first/last time become two timestamps."""
    raw = decode(path.read_bytes()) if path.name.endswith('.zst') else path.read_bytes()
    rows, times, incomplete = [], [], False
    for line in raw.decode('utf-8', 'replace').splitlines():
        if not line.strip():
            continue
        try:
            row = json_row(line)
            slim = _slim(row)
        except ValueError:
            incomplete = True
            continue
        if slim:
            rows.append(slim)
        elif timestamp(row.get('timestamp')):
            times.append((timestamp(row['timestamp']), row['timestamp']))
    if times:
        rows.extend(dict(timestamp=pick(times, key=lambda moment: moment[0])[1]) for pick in (min, max))
    if incomplete:
        rows.append(dict(type='pler_incomplete_log'))  # metadata only; persists the warning on cache hits
    return rows


def read(paths, cache=None):
    """Reconcile logical sessions and response copies before publishing counts."""
    from .reconcile import codex_sessions
    return codex_sessions(paths,cache,_rows,decoder()[0])
