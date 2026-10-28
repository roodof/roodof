"""Local-only locations for PLER's small files. Kept lightweight for every Claude status refresh."""
import os
from pathlib import Path
import stat
import sys


def network(value):
    """Two leading slashes in any mix (//, \\\\, /\\, \\/) name a network location on Windows; never probe them."""
    text = str(value)
    return len(text) >= 2 and text[0] in '\\/' and text[1] in '\\/'


def _system_link(info):
    # macOS /var and /tmp, and /home on some Linux systems, are root-owned links made by the OS.
    # Only root can create or change them. Windows reports uid 0 for everything, so it never qualifies.
    return os.name != 'nt' and stat.S_ISLNK(info.st_mode) and getattr(info, 'st_uid', None) == 0


def local_path(value):
    """An absolute local path, without following user symlink/reparse ancestors. No network probe."""
    if not value or network(value):
        return None
    path = Path(value)
    if not path.is_absolute() or network(path.anchor):
        return None
    path = Path(os.path.abspath(path))
    for part in [*reversed(path.parents), path]:
        try:
            info = part.lstat()
        except FileNotFoundError:
            break
        if _system_link(info):
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            return None
    return path


MAX_LINKS = 32


def _target(text):
    """A link target in plain local spelling, or None. Windows reads junctions and symlinks as \\\\?\\C:\\...;
    \\\\?\\UNC\\..., volume and device targets are refused like any network path."""
    for prefix in ('\\\\?\\', '\\??\\'):
        if text.startswith(prefix):
            rest = text[len(prefix):]
            drive = len(rest) >= 3 and rest[0].isalpha() and rest[1] == ':' and rest[2] in '\\/'
            return rest if drive else None
    return None if network(text) else text


def user_folder(value):
    """A folder the user chose (a home default, an environment variable or a command option), with the user's
    own links and junctions followed to the final local folder. Each link is read without being followed, so a
    target with network syntax is refused before anything there is touched; loops stop after MAX_LINKS. Other
    reparse points stay refused. Paths read from logs never come here: they use local_path."""
    if not value or network(value) or str(value).replace('/', '\\').startswith('\\??\\'):
        return None
    # abspath would erase link/.. before the link is resolved, selecting a different folder on POSIX.
    path = Path(value)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.is_absolute() or network(path.anchor):
        return None
    current, pending, links = Path(path.anchor), list(path.parts[1:]), 0
    while pending:
        name = pending.pop(0)
        if name == '..':
            current = current.parent
            continue
        candidate = current / name
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            if '..' in pending:
                return None  # a missing component cannot be traversed to its parent
            return local_path(candidate.joinpath(*pending))
        # Root-owned OS links (macOS /var -> /private/var) keep the spelling the user and the tests see,
        # unless a later '..' needs the real parent.
        if (not (stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400)
                or (_system_link(info) and '..' not in pending)):
            current = candidate
            continue
        links += 1
        try:
            target = _target(os.readlink(candidate)) if links <= MAX_LINKS else None
        except (OSError, ValueError, NotImplementedError):
            target = None  # not a symlink or junction: another kind of reparse point
        if target is None:
            return None
        target = current / target
        if not target.is_absolute() or network(target.anchor):
            return None
        current, pending = Path(target.anchor), [*target.parts[1:], *pending]
    return local_path(current)


def _cache_path(value):
    if not value or network(value):
        return None
    try:
        expanded = Path(value).expanduser()
        if network(expanded):
            return None
        return local_path(os.path.abspath(expanded))
    except (OSError, ValueError, RuntimeError, TypeError):
        return None


def cache_folder():
    """Configured/default cache directory, or None when it cannot safely be used. Never reroute it."""
    if os.environ.get('PLER_CACHE_DIR'):
        return _cache_path(os.environ['PLER_CACHE_DIR'])
    if os.name == 'nt':
        base = os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData' / 'Local'
    elif sys.platform == 'darwin':
        base = Path.home() / 'Library' / 'Caches'
    else:
        base = os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache'
    # Validate the base before joining it; UNC syntax must never reach a filesystem probe.
    base = _cache_path(base)
    return _cache_path(base / 'pler') if base is not None else None


def cache_file(name, directory=None):
    """Validate the directory and final file; explicit quota folders use the same boundary."""
    base = cache_folder() if directory is None else _cache_path(directory)
    return _cache_path(base / name) if base is not None else None
