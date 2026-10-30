"""Your own one-click verdict on a session: "useful" or "wasted". Kept only on this computer.

The file holds the page's session code (a 24-character hash; never a path, project name, prompt or
command), one of the two words and the second it was set. Clearing the archive or the reader cache keeps
it. A file PLER cannot understand (damaged, or written by a newer version) is never overwritten.
"""
import hashlib
import json
import re
import time

from ..paths import cache_file

FILENAME = 'session-verdicts.json'
FORMAT = 1
VERDICTS = ('useful', 'wasted')
MAX_VERDICTS = 20000
MAX_BYTES = 2 * 1024 * 1024
CODE = re.compile('[a-f0-9]{24}')


def session_code(session):
    """The page's identity for one session row (agent, source and provider ID); also the verdict key."""
    value = session.source + '\0' + session.session_id
    return hashlib.sha256((session.agent + ':' + (value or 'unknown')).encode('utf-8')).hexdigest()[:24]


def _valid(entries):
    return (isinstance(entries, dict) and len(entries) <= MAX_VERDICTS and all(
        isinstance(code, str) and CODE.fullmatch(code) and isinstance(item, dict) and set(item) == {'verdict', 'at'}
        and item['verdict'] in VERDICTS and type(item['at']) is int and item['at'] >= 0 for code, item in entries.items()))


def _entries(path):
    """Read and validate one bounded snapshot, keeping timestamps for a later update."""
    try:
        size = path.stat().st_size
        if size > MAX_BYTES:
            raise ValueError('oversized verdict file')
        with path.open('rb') as stream:
            data = stream.read(size + 1)
    except FileNotFoundError:
        return {}
    if len(data) != size:
        raise ValueError('verdict file changed while reading')
    try:
        value = json.loads(data.decode('utf-8'))
    except RecursionError as error:
        raise ValueError('over-nested verdict file') from error
    if not isinstance(value, dict) or set(value) != {'format', 'verdicts'} or value['format'] != FORMAT \
            or type(value['format']) is not int or not _valid(value['verdicts']):
        raise ValueError('invalid verdict file')
    return value['verdicts']


def read(base=None):
    """{code: verdict}; empty when no verdict was ever saved. Raises ValueError/OSError for an unusable file."""
    path = cache_file(FILENAME, base)
    if path is None:
        raise OSError('unsafe verdict file')
    return {code: item['verdict'] for code, item in _entries(path).items()}


def save(code, verdict, base=None):
    """Set (or with None remove) one verdict under the cache lock; return the full {code: verdict} map."""
    from .archive import _locked, _write
    if not isinstance(code, str) or not CODE.fullmatch(code) or verdict not in (*VERDICTS, None):
        raise ValueError('invalid verdict')
    path = cache_file(FILENAME, base)
    if path is None:
        raise OSError('unsafe verdict file')
    with _locked(path.parent):
        # Use the same validated snapshot throughout the update, never reopen unbounded.
        stored = _entries(path)
        if verdict is None:
            stored.pop(code, None)
        else:
            if code not in stored and len(stored) >= MAX_VERDICTS:
                raise ValueError('too many verdicts')
            stored[code] = dict(verdict=verdict, at=int(time.time()))
        _write(path, dict(format=FORMAT, verdicts=stored))
        return {key: item['verdict'] for key, item in stored.items()}


class Memory:
    """Verdicts that live only as long as the page (the demo must not write into the real cache)."""

    def __init__(self):
        self.values = {}

    def read(self):
        return dict(self.values)

    def save(self, code, verdict):
        if not isinstance(code, str) or not CODE.fullmatch(code) or verdict not in (*VERDICTS, None):
            raise ValueError('invalid verdict')
        if verdict is None:
            self.values.pop(code, None)
        else:
            self.values[code] = verdict
        return dict(self.values)


class Folder:
    """Verdicts in PLER's cache folder (or `base`)."""

    def __init__(self, base=None):
        self.base = base

    def read(self):
        return read(self.base)

    def save(self, code, verdict):
        return save(code, verdict, self.base)


def summary(rows, verdicts):
    """Counts, tokens and list-price dollars per verdict for public session rows (session_view output)."""
    result = {}
    for name in (*VERDICTS, 'none'):
        chosen = [row for row in rows if (verdicts.get(row['id']) or 'none') == name]
        result[name] = dict(sessions=len(chosen), total_tokens=sum(row['total_tokens'] for row in chosen),
                            api_usd=round(sum(row['api_usd'] for row in chosen), 2))
    return result
