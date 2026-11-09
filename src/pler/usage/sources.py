"""Explicit extra log roots on this computer. Never learns roots from agent records.

Selection preferences stay outside reports/backups. Retained history can contain source paths.
Default discovery is additive. WSL access uses the existing running-distro capability.
"""
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import stat

from ..paths import cache_file, network
from ..wsl import split, WslRoots
from . import discovery

FILENAME = 'log-sources.json'
MAX_BYTES = 65536
MAX_ENTRIES = 12
AGENTS = ('claude-code', 'codex')


class SourceError(ValueError):
    def __init__(self, reason='unreadable'):
        self.reason = reason
        super().__init__(reason)


def path_value(value):
    """Validate lexical spelling before any filesystem or WSL status query."""
    if (not isinstance(value, str) or not 1 <= len(value) <= 1024
            or value != value.strip() or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise SourceError('unsafe_path')
    if network(value):
        parsed = split(value)
        if parsed is None or not parsed[1]:
            raise SourceError('unsafe_path')
        return str(PureWindowsPath('\\\\wsl.localhost\\' + parsed[0] + '\\', *parsed[1]))
    path = Path(os.path.expanduser(value))
    if (not path.is_absolute() or path.parent == path
            or str(path).replace('/', '\\').startswith('\\??\\')):
        raise SourceError('unsafe_path')
    # Preserve link/.. order: discovery.chosen resolves it safely at use time.
    return str(path)


def code(agent, path):
    key = discovery.key(path)
    if os.name == 'nt' and key and key[0] == 'local':
        key = tuple(part.casefold() for part in key)
    return hashlib.sha256((agent + ':' + repr(key)).encode('utf-8')).hexdigest()[:24]


def _encoded(entries):
    return json.dumps(dict(format=1, entries=entries), ensure_ascii=False,
                      sort_keys=True, separators=(',', ':')).encode('utf-8')


def revision(entries):
    return hashlib.sha256(_encoded(entries)).hexdigest()[:24]


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SourceError()
        result[key] = value
    return result


def validate(data):
    try:
        if len(data) > MAX_BYTES:
            raise SourceError()
        value = json.loads(data.decode('utf-8'), object_pairs_hook=_pairs)
        if (not isinstance(value, dict) or set(value) != {'format', 'entries'}
                or type(value['format']) is not int or value['format'] != 1
                or not isinstance(value['entries'], list) or len(value['entries']) > MAX_ENTRIES):
            raise SourceError()
        seen = set()
        for row in value['entries']:
            if (not isinstance(row, dict) or set(row) != {'agent', 'path'}
                    or row['agent'] not in AGENTS or path_value(row['path']) != row['path']):
                raise SourceError()
            identity = code(row['agent'], row['path'])
            if identity in seen:
                raise SourceError()
            seen.add(identity)
        return value['entries']
    except (ValueError, TypeError, UnicodeError, RecursionError, KeyError) as error:
        raise SourceError() from error


class Store:
    def __init__(self, base=None):
        self.base = base

    def read(self):
        path = cache_file(FILENAME, self.base)
        if path is None:
            raise SourceError()
        observed = False
        try:
            with path.open('rb') as stream:
                observed = True
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode):
                    raise SourceError()
                data = stream.read(MAX_BYTES + 1)
                after = os.fstat(stream.fileno())
            signature = lambda info: (info.st_size, info.st_mtime_ns, info.st_ino, info.st_dev)
            if len(data) != before.st_size or signature(before) != signature(after) or signature(after) != signature(path.stat()):
                raise SourceError()
        except FileNotFoundError:
            if observed:
                raise SourceError()
            return []
        except OSError as error:
            raise SourceError() from error
        return validate(data)

    def change(self, expected, agent=None, paths=None, remove=None):
        from .archive import _locked, _write
        path = cache_file(FILENAME, self.base)
        if path is None:
            raise SourceError('unsaved')
        try:
            with _locked(path.parent):
                entries = self.read()
                if expected != revision(entries):
                    raise SourceError('conflict')
                if remove is not None:
                    entries = [row for row in entries if code(row['agent'], row['path']) != remove]
                else:
                    if agent not in AGENTS:
                        raise SourceError('invalid')
                    for value in paths:
                        value = path_value(value)
                        if not any(code(row['agent'], row['path']) == code(agent, value) for row in entries):
                            entries.append(dict(agent=agent, path=value))
                    if len(entries) > MAX_ENTRIES:
                        raise SourceError('limit')
                validate(_encoded(entries))
                _write(path, dict(format=1, entries=entries))
        except OSError as error:
            raise SourceError('unsaved') from error


def defaults():
    """Display-only paths; the readers remain the authority for automatic discovery."""
    claude = os.environ.get('CLAUDE_CONFIG_DIR')
    bases = [Path(p.strip()).expanduser() for p in claude.split(',') if p.strip()] if claude else [Path.home()/'.config/claude', Path.home()/'.claude']
    codex = Path(os.environ.get('CODEX_HOME') or Path.home()/'.codex').expanduser()
    return [dict(agent='claude-code', path=str(base/'projects')) for base in bases] + [
        dict(agent='codex', path=str(codex/name)) for name in ('sessions', 'archived_sessions')]


def check(agent, value):
    """Check directories only. No transcript content, recursive scan or distro startup."""
    if agent not in AGENTS:
        raise SourceError('invalid')
    value = path_value(value)
    access, issues = WslRoots(), []
    safe = discovery.chosen(value, issues, access, explicit=True)
    if safe is None:
        reason = issues[0][1] if issues else 'UnsafePath'
        raise SourceError({'WSLNotRunning':'wsl_not_running', 'WSLUnavailable':'wsl_unavailable',
                           'UnsafePath':'unsafe_path'}.get(reason, 'unreadable'))
    try:
        if not stat.S_ISDIR(safe.stat().st_mode):
            raise SourceError('not_folder')
        # Selecting an agent config home is convenient; persist only its log subfolders.
        names = ('projects',) if agent == 'claude-code' else ('sessions', 'archived_sessions')
        roots = []
        for name in names:
            child = discovery.chosen(safe/name, issues, access)
            if child is not None and child.is_dir():
                roots.append(str(child))
        if not roots:
            roots = [str(safe)]
        # Verify each chosen directory is enumerable, without following any child entry.
        for root in roots:
            with os.scandir(root) as stream:
                next(stream, None)
        return dict(ok=True, roots=roots, kind='wsl' if network(safe) else 'local')
    except FileNotFoundError as error:
        raise SourceError('missing') from error
    except (OSError, ValueError) as error:
        if isinstance(error, SourceError):
            raise
        raise SourceError('unreadable') from error


def view(demo=False):
    if demo:
        return dict(readable=True, demo=True, entries=[], automatic=[], revision=revision([]), maximum=MAX_ENTRIES)
    try:
        entries = Store().read()
        return dict(readable=True, demo=False, revision=revision(entries), maximum=MAX_ENTRIES,
                    automatic=defaults(), entries=[dict(row, id=code(row['agent'], row['path'])) for row in entries])
    except (SourceError, OSError):
        return dict(readable=False, demo=False, entries=[], automatic=defaults(), revision=None, maximum=MAX_ENTRIES)
