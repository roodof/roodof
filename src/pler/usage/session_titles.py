"""Live display titles only; never added to accounting caches, archives or exports.

Read provider-authored title fields, not user messages. Missing/oversized metadata
simply leaves the UI's project/date fallback. Each refresh rechecks rename files.
"""
from dataclasses import dataclass
import os
from pathlib import Path
import stat
import unicodedata

from . import discovery
from .input_limits import checkpoint
from .records import json_row
from .verdicts import session_code

MAX_FILE = 4 * 1024 * 1024
TAIL = 64 * 1024
MAX_TOTAL = 64 * 1024 * 1024

# Closed reason vocabulary, containing no paths, provider IDs or exception text.
REASONS = ('provided', 'not_recorded', 'archive_only', 'location_unknown', 'metadata_missing',
           'metadata_large', 'read_budget', 'access_denied', 'source_restricted',
           'wsl_not_running', 'wsl_unavailable', 'metadata_invalid', 'metadata_unreadable',
           'window_limited', 'read_changed', 'not_checked')


@dataclass(frozen=True)
class Read:
    text: str = ''
    reason: str = ''
    limited: bool = False


def _reason(reasons):
    # Report an observed failure before a merely bounded/absent lookup. Do not
    # infer that a title was never saved when part of its metadata was not read.
    priority = ('source_restricted', 'wsl_not_running', 'wsl_unavailable', 'access_denied',
                'read_changed', 'read_budget', 'metadata_large', 'metadata_unreadable',
                'metadata_invalid', 'window_limited', 'metadata_missing')
    return next((code for code in priority if code in reasons), 'not_recorded')


def clean(value):
    if not isinstance(value, str) or len(value) > 4096:
        return None
    value = ' '.join(''.join(c for c in value if not unicodedata.category(c).startswith('C') or c in '\n\t\r').split())
    return (value[:159] + '…' if len(value) > 160 else value) or None


class Reader:
    def __init__(self, access):
        self.access, self.used = access, 0

    def read(self, path, tail=False, head=False):
        checkpoint()
        issues = []
        path = discovery.local(path, issues=issues, access=self.access)
        if path is None:
            reason = issues[0][1] if issues else 'UnsafePath'
            return Read(reason={'WSLNotRunning':'wsl_not_running', 'WSLUnavailable':'wsl_unavailable',
                                'PermissionError':'access_denied'}.get(reason, 'source_restricted'))
        observed = False
        try:
            with open(path, 'rb') as stream:
                observed = True
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode):
                    return Read(reason='source_restricted')
                if not (tail or head) and info.st_size > MAX_FILE:
                    return Read(reason='metadata_large')
                size = min(info.st_size, TAIL) if tail or head else info.st_size
                if self.used + size > MAX_TOTAL:
                    return Read(reason='read_budget')
                self.used += size
                offset = max(0, info.st_size - size) if tail else 0
                stream.seek(offset)
                data = stream.read(size)
                after = os.fstat(stream.fileno())
                signature = lambda value: (value.st_size, value.st_mtime_ns, value.st_ino, value.st_dev)
                if len(data) != size or signature(info) != signature(after) or signature(after) != signature(path.stat()):
                    return Read(reason='read_changed')
                # A partial JSON row must never be interpreted as a whole record.
                if offset:
                    data = data.partition(b'\n')[2]
                if head and info.st_size > size:
                    data = data.rpartition(b'\n')[0]
                limited = bool((tail or head) and info.st_size > size)
                return Read(data.decode('utf-8'), 'window_limited' if limited else '', limited)
        except FileNotFoundError:
            return Read(reason='read_changed' if observed else 'metadata_missing')
        except PermissionError:
            return Read(reason='access_denied')
        except UnicodeError:
            return Read(reason='metadata_invalid')
        except (OSError, ValueError):
            return Read(reason='metadata_unreadable')


def _rows(data, reasons=None):
    for line in (data or '').splitlines():
        checkpoint()
        if len(line) > 16384:
            if reasons is not None: reasons.add('metadata_invalid')
            continue
        if not line.strip():
            continue
        try:
            yield json_row(line)
        except (ValueError, TypeError):
            if reasons is not None: reasons.add('metadata_invalid')
            continue


def inspect(sessions, access=None):
    reader = Reader(access or discovery.WslRoots())
    result, indexes, statuses = {}, {}, {}
    # Recent sessions get first use of the bounded metadata budget.
    rows = sorted(sessions, key=lambda s: s.ended.isoformat() if s.ended else '', reverse=True)
    for session in rows:
        checkpoint()
        code = session_code(session)
        if getattr(session, 'source_state', 'live') == 'archive':
            statuses[code] = dict(state='fallback', reason='archive_only')
            continue
        source = Path(session.source)
        if not source.is_absolute():
            statuses[code] = dict(state='fallback', reason='location_unknown')
            continue
        title, reasons, missing_transcript = None, set(), False
        if session.agent == 'codex':
            root = next((p.parent for p in source.parents if p.name in ('sessions', 'archived_sessions')), None)
            if root is None:
                statuses[code] = dict(state='fallback', reason='location_unknown')
                continue
            index = root / 'session_index.jsonl'
            if index not in indexes:
                names, problems = {}, set()
                read = reader.read(index)
                if read.reason: problems.add(read.reason)
                for row in _rows(read.text, problems):
                    identity, name = row.get('id'), clean(row.get('thread_name'))
                    if isinstance(identity, str) and name:
                        names[identity] = name  # append-only index: last rename wins
                indexes[index] = names, problems
            names, problems = indexes[index]
            title = names.get(session.session_id)
            reasons.update(problems)
        elif session.agent == 'claude-code':
            index = source.parent / 'sessions-index.json'
            if index not in indexes:
                names, problems = {}, set()
                read = reader.read(index)
                if read.reason: problems.add(read.reason)
                data = read.text
                try:
                    entries = json_row(data).get('entries', []) if data else []
                    if not isinstance(entries, list): problems.add('metadata_invalid')
                    for row in entries if isinstance(entries, list) else []:
                        checkpoint()
                        if not isinstance(row, dict):
                            problems.add('metadata_invalid')
                            continue
                        identity = row.get('sessionId')
                        name = clean(row.get('customTitle')) or clean(row.get('summary'))
                        if isinstance(identity, str) and name:
                            names[identity] = name
                except (ValueError, TypeError):
                    problems.add('metadata_invalid')
                indexes[index] = names, problems
            names, problems = indexes[index]
            title = names.get(session.session_id)
            reasons.update(problems)
            # /rename is appended to the transcript, including when the index is stale.
            head = reader.read(source, head=True)
            tail = reader.read(source, tail=True)
            missing_transcript = any(r.reason == 'metadata_missing' for r in (head, tail))
            reasons.update(r.reason for r in (head, tail) if r.reason)
            for row in _rows(head.text + '\n' + tail.text, reasons):
                if row.get('type') == 'custom-title' and row.get('sessionId') == session.session_id:
                    title = clean(row.get('customTitle')) or title
        if title:
            result[code] = title
            # A missing optional index does not make a complete transcript rename
            # uncertain. Read/format/window limits still make freshness unverified.
            if not missing_transcript:
                reasons.discard('metadata_missing')
        reason = _reason(reasons) if reasons else ('provided' if title else 'not_recorded')
        statuses[code] = dict(state=('available' if reason == 'provided' else 'limited') if title else 'fallback', reason=reason)
    return result, statuses


def load(sessions, access=None):
    """Compatibility API: titles only. All status information stays in the live UI layer."""
    return inspect(sessions, access)[0]
