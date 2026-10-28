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
