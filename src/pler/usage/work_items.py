"""Your own named work and its opaque session links, stored only on this computer.

Titles are explicit user input, never inferred from a transcript. The file contains no source path,
provider identity or conversation text. A link names the same source-sensitive page session code as
verdicts.py: a moved/unavailable session remains an unresolved link, never an automatic reassignment.
"""
import json
import math
import os
import re
import secrets
import stat
import threading
import time
import unicodedata

from ..paths import cache_file
from . import archive
from .records import _too_deep

FILENAME = 'work-items.json'
FORMAT = 1
MAX_ITEMS = 200
MAX_SESSIONS = 2000
MAX_MEMBERSHIPS = 20000
MAX_BYTES = 2 * 1024 * 1024
MAX_TITLE = 120
MAX_TIME = (1 << 53) - 1
CODE = re.compile('[a-f0-9]{24}')
_FLAGS = ('tokens_complete', 'calls_complete', 'attribution_complete', 'models_complete')


class WorkError(ValueError):
    """Fixed public error reason; never carry a private title, path or native identity."""
    def __init__(self, code='invalid'):
        self.code = code
        super().__init__(code)


def _code(value):
    return isinstance(value, str) and CODE.fullmatch(value) is not None


def _title(value):
    if not isinstance(value, str):
        raise WorkError()
    value = value.strip()
    if (not value or len(value) > MAX_TITLE
            or any(unicodedata.category(char) in ('Cc', 'Cs', 'Zl', 'Zp') for char in value)):
        raise WorkError()
    return value


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise WorkError()
        value[key] = item
    return value


def validate_document(value):
    """Validate the exact format envelope; return a detached items mapping for backup/readers."""
    if not isinstance(value, dict) or set(value) != {'format', 'items'}:
        raise WorkError()
    if type(value['format']) is not int or value['format'] != FORMAT:
        raise WorkError('unsupported')
    items = value['items']
    if not isinstance(items, dict):
        raise WorkError()
    if len(items) > MAX_ITEMS:
        raise WorkError('limit')
    clean, memberships = {}, 0
    for identity, item in items.items():
        if (not _code(identity) or not isinstance(item, dict)
                or set(item) != {'title', 'created_at', 'updated_at', 'sessions'}):
            raise WorkError()
        title = _title(item['title'])
        if title != item['title']:
            raise WorkError()
        created, updated, sessions = item['created_at'], item['updated_at'], item['sessions']
        if (type(created) is not int or type(updated) is not int
                or not 0 <= created <= updated <= MAX_TIME or not isinstance(sessions, list)
                or any(not _code(code) for code in sessions) or len(set(sessions)) != len(sessions)):
            raise WorkError()
        if len(sessions) > MAX_SESSIONS:
            raise WorkError('limit')
        memberships += len(sessions)
        if memberships > MAX_MEMBERSHIPS:
            raise WorkError('limit')
        clean[identity] = dict(title=title, created_at=created, updated_at=updated, sessions=list(sessions))
    return clean


def document(items):
    """The validated fixed document shape, useful to backup without reading any source."""
    return dict(format=FORMAT, items=validate_document(dict(format=FORMAT, items=items)))


def validate(data):
    """Validate bounded UTF-8 JSON bytes without filesystem access."""
    if type(data) is not bytes:
        raise WorkError()
    if len(data) > MAX_BYTES:
        raise WorkError('limit')
    try:
        text = data.decode('utf-8')
        if _too_deep(text):
            raise WorkError('limit')
        value = json.loads(text, object_pairs_hook=_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(WorkError()))
        return validate_document(value)
    except WorkError:
        raise
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError) as error:
        raise WorkError() from error


def _encoded(items):
    try:
        data = json.dumps(document(items), ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (UnicodeError, OverflowError) as error:
        raise WorkError() from error
    if len(data) > MAX_BYTES:
        raise WorkError('limit')
    return data


def _signature(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def _read(path):
    if path is None or cache_file(path.name, path.parent) != path:
        raise OSError('unsafe work items')
    try:
        observed = path.stat()
    except FileNotFoundError:
        return {}
    try:
        if not stat.S_ISREG(observed.st_mode):
            raise OSError('unsafe work items')
        if observed.st_size > MAX_BYTES:
            raise WorkError('limit')
        with path.open('rb') as stream:
            if _signature(os.fstat(stream.fileno())) != _signature(observed):
                raise OSError('work items changed')
            data = stream.read(observed.st_size + 1)
            after = os.fstat(stream.fileno())
        if (len(data) != observed.st_size or _signature(after) != _signature(observed)
                or cache_file(path.name, path.parent) != path
                or _signature(path.stat()) != _signature(observed)):
            raise OSError('work items changed')
    except FileNotFoundError as error:
        raise OSError('work items changed') from error
    return validate(data)


def _arguments(action, identity, title, session):
    if not isinstance(action, str) or action not in ('create', 'rename', 'link', 'unlink', 'delete'):
        raise WorkError()
    if action == 'create':
        if identity is not None or session is not None and not _code(session):
            raise WorkError()
        return _title(title)
    if not _code(identity):
        raise WorkError()
    if action == 'rename':
        if session is not None:
            raise WorkError()
        return _title(title)
    if title is not None or (action == 'delete' and session is not None):
        raise WorkError()
    if action in ('link', 'unlink') and not _code(session):
        raise WorkError()
    return None


def _mutate(items, action, identity, title, session):
    result = validate_document(dict(format=FORMAT, items=items))
    try:
        now = int(time.time())
    except (ValueError, OverflowError) as error:
        raise WorkError() from error
    if not 0 <= now <= MAX_TIME:
        raise WorkError()
    if action == 'create':
        if len(result) >= MAX_ITEMS:
            raise WorkError('limit')
        for _ in range(10):
            identity = secrets.token_hex(12)
            if _code(identity) and identity not in result:
                break
        else:
            raise WorkError('limit')
        result[identity] = dict(title=title, created_at=now, updated_at=now,
                                sessions=[session] if session is not None else [])
    else:
        if identity not in result:
            raise WorkError('missing')
        if action == 'delete':
            del result[identity]
        else:
            item = result[identity]
            before = dict(item, sessions=list(item['sessions']))
            if action == 'rename':
                item['title'] = title
            elif action == 'link' and session not in item['sessions']:
                item['sessions'] = sorted([*item['sessions'], session])
            elif action == 'unlink' and session in item['sessions']:
                item['sessions'].remove(session)
            if item != before:
                item['updated_at'] = max(item['updated_at'], now)
    _encoded(result)  # Validate semantic and serialized limits before an atomic write.
    return dict(id=identity, items=result)


class Folder:
    """Named work in a fixed safe local file; every update re-reads under the archive writer lock."""
    def __init__(self, base=None):
        self.base = base

    def read(self):
        return _read(cache_file(FILENAME, self.base))

    def mutate(self, action, identity=None, title=None, session=None):
        title = _arguments(action, identity, title, session)
        path = cache_file(FILENAME, self.base)
        if path is None:
            raise OSError('unsafe work items')
        with archive._locked(path.parent):
            before = _read(path)
            result = _mutate(before, action, identity, title, session)
            if result['items'] != before:
                archive._write(path, document(result['items']))
            return result


class Memory:
    """The demo's named work never reads or writes a user's metadata folder."""
    def __init__(self, items=None):
        self.items = validate_document(dict(format=FORMAT, items={} if items is None else items))
        self.lock = threading.RLock()

    def read(self):
        with self.lock:
            return validate_document(dict(format=FORMAT, items=self.items))

    def mutate(self, action, identity=None, title=None, session=None):
        title = _arguments(action, identity, title, session)
        with self.lock:
            result = _mutate(self.items, action, identity, title, session)
            self.items = validate_document(dict(format=FORMAT, items=result['items']))
            return result


def _totals(rows, missing=False):
    values = list(rows)
    result = dict(total_tokens=sum(row['total_tokens'] for row in values),
                  calls=sum(row['calls'] for row in values),
                  api_usd=round(sum(row['api_usd'] for row in values), 2))
    priced = sum(row['api_priced_tokens'] if 'api_priced_tokens' in row
                 else (row.get('api_priced_share') or 0) * row['total_tokens'] for row in values)
    result['api_priced_share'] = min(1.0, priced / result['total_tokens']) if result['total_tokens'] else None
    for flag in _FLAGS:
        result[flag] = all(row.get('quality', {}).get(flag, False) is True for row in values)
        if not values and missing:
            result[flag] = False
    return result


def project(items, rows, all_session_ids=None):
    """Selected subtotals per work; union totals count each selected session once across all work.

    All four ID arrays contain only opaque page session codes. `outside` is present in this snapshot
    but excluded by the selection; `missing` cannot be found in the snapshot and is never rebound.
    Counts/prices are whole-session observations, not a partition of the cost of individual work.
    """
    items = validate_document(dict(format=FORMAT, items=items))
    selected = {}
    for row in rows:
        if not isinstance(row, dict) or not _code(row.get('id')):
            raise WorkError()
        if (type(row.get('total_tokens')) is not int or row['total_tokens'] < 0
                or type(row.get('calls')) is not int or row['calls'] < 0
                or type(row.get('api_usd')) not in (int, float)
                or not math.isfinite(row['api_usd']) or row['api_usd'] < 0):
            raise WorkError()
        if 'api_priced_tokens' in row:
            if type(row['api_priced_tokens']) is not int or not 0 <= row['api_priced_tokens'] <= row['total_tokens']:
                raise WorkError()
        elif row.get('api_priced_share') is not None:
            share = row['api_priced_share']
            if type(share) not in (int, float) or not math.isfinite(share) or not 0 <= share <= 1:
                raise WorkError()
        if row['id'] in selected and selected[row['id']] != row:
            raise WorkError()
        selected[row['id']] = row
    selected_ids = set(selected)
    known = selected_ids | (set(all_session_ids) if all_session_ids is not None else set())
    if any(not _code(identity) for identity in known):
        raise WorkError()
    linked, frequencies = set(), {}
    for item in items.values():
        linked.update(item['sessions'])
        for identity in selected_ids.intersection(item['sessions']):
            frequencies[identity] = frequencies.get(identity, 0) + 1
    overlapping = {identity for identity, frequency in frequencies.items() if frequency > 1}
    projected = []
    for identity, item in sorted(items.items(), key=lambda pair: (-pair[1]['updated_at'], pair[0])):
        members = set(item['sessions'])
        chosen, outside, missing = members & selected_ids, (members & known) - selected_ids, members - known
        projected.append(dict(id=identity, title=item['title'], created_at=item['created_at'], updated_at=item['updated_at'],
            session_ids=sorted(members), selected_session_ids=sorted(chosen), outside_session_ids=sorted(outside),
            missing_session_ids=sorted(missing), linked_sessions=len(members), selected_sessions=len(chosen),
            outside_selection=len(outside), missing_sessions=len(missing), overlapping_sessions=len(chosen & overlapping),
            **_totals((selected[code] for code in sorted(chosen)), bool(missing))))
    chosen = linked & selected_ids
    summary = dict(items=len(items), linked_sessions=len(linked), selected_sessions=len(chosen),
                   unassigned_sessions=len(selected_ids - chosen), outside_selection=len((linked & known) - selected_ids),
                   missing_sessions=len(linked - known), overlapping_sessions=len(overlapping),
                   **_totals((selected[code] for code in sorted(chosen)), bool(linked - known)))
    return dict(items=projected, summary=summary)
