"""Live display titles only; never added to accounting caches, archives or exports.

Read provider-authored title fields, not user messages. Missing/oversized metadata
simply leaves the UI's project/date fallback. Each refresh rechecks rename files.
"""
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
        path = discovery.local(path, access=self.access)
        if path is None:
            return None
        try:
            with open(path, 'rb') as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or (not (tail or head) and info.st_size > MAX_FILE):
                    return None
                size = min(info.st_size, TAIL) if tail or head else info.st_size
                if self.used + size > MAX_TOTAL:
                    return None
                self.used += size
                offset = max(0, info.st_size - size) if tail else 0
                stream.seek(offset)
                data = stream.read(size)
                # A partial JSON row must never be interpreted as a whole record.
                if offset:
                    data = data.partition(b'\n')[2]
                if head and info.st_size > size:
                    data = data.rpartition(b'\n')[0]
                return data.decode('utf-8', 'replace')
        except (OSError, ValueError):
            return None


def _rows(data):
    for line in (data or '').splitlines():
        checkpoint()
        if len(line) > 16384:
            continue
        try:
            yield json_row(line)
        except (ValueError, TypeError):
            continue


def load(sessions, access=None):
    reader = Reader(access or discovery.WslRoots())
    result, indexes = {}, {}
    # Recent sessions get first use of the bounded metadata budget.
    rows = sorted(sessions, key=lambda s: s.ended.isoformat() if s.ended else '', reverse=True)
    for session in rows:
        checkpoint()
        if getattr(session, 'source_state', 'live') == 'archive':
            continue
        source = Path(session.source)
        if not source.is_absolute():
            continue
        title = None
        if session.agent == 'codex':
            root = next((p.parent for p in source.parents if p.name in ('sessions', 'archived_sessions')), None)
            if root is None:
                continue
            index = root / 'session_index.jsonl'
            if index not in indexes:
                names = {}
                for row in _rows(reader.read(index)):
                    identity, name = row.get('id'), clean(row.get('thread_name'))
                    if isinstance(identity, str) and name:
                        names[identity] = name  # append-only index: last rename wins
                indexes[index] = names
            title = indexes[index].get(session.session_id)
        elif session.agent == 'claude-code':
            index = source.parent / 'sessions-index.json'
            if index not in indexes:
                names = {}
                data = reader.read(index)
                try:
                    entries = json_row(data).get('entries', []) if data else []
                    for row in entries if isinstance(entries, list) else []:
                        checkpoint()
                        if not isinstance(row, dict):
                            continue
                        identity = row.get('sessionId')
                        name = clean(row.get('customTitle')) or clean(row.get('summary'))
                        if isinstance(identity, str) and name:
                            names[identity] = name
                except (ValueError, TypeError):
                    pass
                indexes[index] = names
            title = indexes[index].get(session.session_id)
            # /rename is appended to the transcript, including when the index is stale.
            head = reader.read(source, head=True)
            tail = reader.read(source, tail=True)
            for row in _rows((head or '') + '\n' + (tail or '')):
                if row.get('type') == 'custom-title' and row.get('sessionId') == session.session_id:
                    title = clean(row.get('customTitle')) or title
        if title:
            result[session_code(session)] = title
    return result
