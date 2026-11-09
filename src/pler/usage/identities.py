"""Keep annotation codes across verified moves of the same physical local log.

No provider-ID-only matching and no annotation-file migrations. The registry holds
hashes of file identity, provider ID, start time and previous row codes; never paths,
transcript bytes or titles. Copies/new file objects cannot inherit old annotations.
An absent birth time/file ID, a changed source during a read, or ambiguous evidence
does not prove a move. Cross-volume copy/delete and cross-machine recovery require
a separate explicit reconnection workflow; this module never guesses.
"""
import hashlib
import json
import os
import re
import stat

from ..paths import cache_file, network
from . import discovery
from .records import _too_deep
from .verdicts import source_code
from .input_limits import checkpoint

FILENAME = 'session-identities.json'
MAX_ENTRIES = 20000
MAX_BYTES = 8 * 1024 * 1024
MAX_ROWS = 32
HEX = re.compile('[a-f0-9]{64}')
CODE = re.compile('[a-f0-9]{24}')


class IdentityError(ValueError):
    def __init__(self):
        super().__init__('Session identity preferences could not be read or saved.')


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), ensure_ascii=True).encode('ascii')).hexdigest()


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise IdentityError()
        result[key] = value
    return result


def validate(data):
    try:
        if type(data) is not bytes or len(data) > MAX_BYTES:
            raise IdentityError()
        text = data.decode('utf-8')
        if _too_deep(text):
            raise IdentityError()
        value = json.loads(text, object_pairs_hook=_pairs)
        if (not isinstance(value, dict) or set(value) != {'format', 'files'}
                or type(value['format']) is not int or value['format'] != 1
                or not isinstance(value['files'], dict) or len(value['files']) > MAX_ENTRIES):
            raise IdentityError()
        for token, row in value['files'].items():
            if (not isinstance(token, str) or not HEX.fullmatch(token) or not isinstance(row, dict)
                    or set(row) != {'code', 'provider', 'anchor', 'rows'}
                    or not isinstance(row['code'], str) or not CODE.fullmatch(row['code'])
                    or not all(isinstance(row[k], str) and HEX.fullmatch(row[k]) for k in ('provider', 'anchor'))
                    or not isinstance(row['rows'], list) or not 1 <= len(row['rows']) <= MAX_ROWS
                    or any(not isinstance(c, str) or not CODE.fullmatch(c) for c in row['rows'])
                    or len(set(row['rows'])) != len(row['rows'])):
                raise IdentityError()
        return value['files']
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError, KeyError) as error:
        raise IdentityError() from error


def _read(path):
    observed = None
    try:
        observed = path.stat()
        if not stat.S_ISREG(observed.st_mode) or observed.st_size > MAX_BYTES:
            raise IdentityError()
        def signature(info): return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns
        with path.open('rb') as stream:
            if signature(os.fstat(stream.fileno())) != signature(observed):
                raise IdentityError()
            data = stream.read(observed.st_size + 1)
            if signature(os.fstat(stream.fileno())) != signature(observed):
                raise IdentityError()
        if len(data) != observed.st_size or signature(path.stat()) != signature(observed):
            raise IdentityError()
    except FileNotFoundError:
        if observed is not None:
            raise IdentityError()
        return {}
    return validate(data)


def _volume(path, known):
    if os.name != 'nt':
        return None
    # Python 3.9 and 3.14 expose different-width st_dev values on Windows.
    # A volume GUID is stable across those runtimes and distinguishes mounted/cloned volumes.
    import ctypes
    from ctypes import wintypes
    kernel = known.get(None)
    if kernel is None:
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        known[None] = kernel
    root = ctypes.create_unicode_buffer(32768)
    locate = kernel.GetVolumePathNameW
    locate.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    locate.restype = wintypes.BOOL
    if not locate(str(path), root, len(root)):
        return None
    if root.value not in known:
        name = ctypes.create_unicode_buffer(1024)
        lookup = kernel.GetVolumeNameForVolumeMountPointW
        lookup.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        lookup.restype = wintypes.BOOL
        known[root.value] = name.value.casefold() if lookup(root.value, name, len(name)) else None
    return known[root.value]


def sample(paths):
    """Two-sided source signatures. Never probe network/WSL paths for local file IDs."""
    result, volumes = {}, {}
    for name in paths:
        checkpoint()
        if network(name):
            continue
        try:
            path = discovery.local(name)
            if path is None:
                continue
            info = path.stat()
            birth = getattr(info, 'st_birthtime_ns', info.st_ctime_ns if os.name == 'nt' else None)
            if not stat.S_ISREG(info.st_mode) or not info.st_ino or birth is None or birth <= 0:
                continue
            volume = _volume(path, volumes) if os.name == 'nt' else info.st_dev
            if volume is not None:
                result[str(name)] = (volume, info.st_ino, birth, info.st_size, info.st_mtime_ns)
        except (OSError, ValueError, RuntimeError):
            pass
    return result


def _describe(session, before, after):
    provider = digest([session.agent, session.session_id])
    anchor = digest(session.started.isoformat() if session.started else None)
    evidence = getattr(session, '_sources', None) or {session.source: dict(state=session.source_state)}
    live, archived, stable = {}, [], set()
    for path, state in evidence.items():
        row = source_code(session, source=path)
        if state['state'] == 'live':
            signature = before.get(path)
            following = after.get(path)
            if (signature is not None and following is not None and signature[:3] == following[:3]
                    and session.started is not None):
                token = digest([provider, anchor, *signature[:3]])
                live[token] = (row, path)
                if signature == following:
                    stable.add(token)
        else:
            archived.append(row)
    return dict(session=session, raw=source_code(session), provider=provider, anchor=anchor,
                live=live, stable=stable, archived=archived, state='original')


def _resolve(sessions, files, before, after):
    rows = [_describe(s, before, after) for s in sessions]
    occupied = {entry['code'] for entry in files.values()}
    by_row, by_native = {}, set()
    for entry in files.values():
        by_native.add((entry['provider'], entry['anchor']))
        for row in entry['rows']:
            by_row.setdefault((entry['provider'], entry['anchor'], row), set()).add(entry['code'])
    # One physical proof must never assign a shared code to two projected rows.
    token_owners = {}
    for row in rows:
        for token in row['live']:
            token_owners[token] = token_owners.get(token, 0) + 1
    for row in rows:
        checkpoint()
        candidates = {files[token]['code'] for token in row['live'] if token in files}
        row['known_files'] = {token for token in row['live'] if token in files}
        if not row['live'] and row['session'].source_state == 'archive':
            candidates = set(by_row.get((row['provider'], row['anchor'], row['raw']), ()))
        if len(candidates) == 1 and not any(token_owners[t] > 1 for t in row['live']):
            row['code'] = next(iter(candidates))
            moved = any(token in row['known_files'] and raw != row['code']
                        for token, (raw, _) in row['live'].items())
            row['state'] = 'preserved' if row['code'] != row['raw'] or moved else 'original'
        else:
            row['code'] = row['raw']
            if candidates or (row['provider'], row['anchor']) in by_native:
                row['state'] = 'conflict' if candidates else 'unverified'
            if row['raw'] in occupied and row['session'].source_state != 'archive':
                # The path/native ID was reused by an unproven new file object.
                row['code'] = digest(['unverified', row['raw'], sorted(row['live']), row['anchor']])[:24]
    counts = {}
    for row in rows:
        counts[row['code']] = counts.get(row['code'], 0) + 1
    for row in rows:
        if counts[row['code']] > 1:
            row['code'] = digest(['conflict', row['raw'], sorted(row['live'])])[:24]
            row['state'] = 'conflict'
    # Even identical synthetic/ambiguous rows must remain unresolved, never silently share annotations.
    if len({row['code'] for row in rows}) != len(rows):
        raise IdentityError()
    limited = False
    updated = dict(files)
    for row in rows:
        if row['state'] == 'conflict':
            continue
        for token, (raw, _) in row['live'].items():
            old = updated.get(token)
            if old is None and (row['known_files'] or raw != row['raw']):
                # A newly appearing copy alongside a known file is not a rename.
                # Initially enroll only the physical file that owns the legacy row code.
                continue
            if old is None and token not in row['stable']:
                continue  # do not enroll an unproven new file while it is changing
            if old is not None and old['code'] != row['code']:
                continue
            if old is None and len(updated) >= MAX_ENTRIES:
                limited = True
                continue
            previous = list(old['rows']) if old else []
            if raw not in previous:
                previous.append(raw)
            # Keep the original observation and recent paths, bounding repeated renames.
            previous = previous[:1] + previous[-(MAX_ROWS-1):] if len(previous) > MAX_ROWS else previous
            updated[token] = dict(code=row['code'], provider=row['provider'], anchor=row['anchor'], rows=previous)
    for row in rows:
        session = row['session']
        session._pler_identity = row['code']
        session._pler_identity_state = row['state']
        session._pler_file_objects = {path:before[path][:3] for _, path in row['live'].values()}
        session.__dict__.pop('_pler_live_sources', None)
        # A retained old name can be covered by the very same moved live file.
        covered = set()
        for token in row['live']:
            entry = updated.get(token)
            if entry and entry['code'] == row['code']:
                covered.update(entry['rows'])
        covered.update(source_code(session, source=path) for path in getattr(session, '_live_covered_archives', ()))
        if (row['archived'] and row['known_files'] and set(row['archived']) <= covered
                and row['state'] in ('original', 'preserved')):
            session._pler_live_sources = tuple(sorted(path for _, path in row['live'].values()))
    status = dict(state='ready', preserved=sum(r['state'] == 'preserved' for r in rows),
                  unverified=sum(r['state'] == 'unverified' for r in rows),
                  conflicts=sum(r['state'] == 'conflict' for r in rows), limit_reached=limited,
                  untracked=sum(not r['live'] and r['session'].source_state != 'archive' for r in rows))
    return updated, status


def bind(sessions, before, after, base=None):
    from .archive import _locked, _write
    path = cache_file(FILENAME, base)
    if path is None:
        if not before and not after:
            # WSL-only/cache-free reads have no local physical identity to persist.
            # Keep them readable without touching an unsafe cache location or
            # claiming that portable/moved-file identity was verified.
            _, status = _resolve(sessions, {}, before, after)
            return dict(status, state='unavailable')
        raise IdentityError()
    try:
        with _locked(path.parent):
            files = _read(path)
            updated, status = _resolve(sessions, files, before, after)
            if updated != files:
                value = dict(format=1, files=updated)
                encoded = json.dumps(value, separators=(',', ':'), allow_nan=False).encode('utf-8')
                validate(encoded)  # never publish an unbounded or incompatible registry
                try:
                    _write(path, value)
                except OSError:
                    # A cache that cannot be written must not hide verified usage. Nothing was
                    # replaced, so saved codes stay intact; this run simply cannot keep new ones.
                    return dict(status, state='unavailable')
            return status
    except (OSError, ValueError, TypeError, UnicodeError) as error:
        raise IdentityError() from error
