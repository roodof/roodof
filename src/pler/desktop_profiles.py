"""Explicit desktop history selection; terminal/--data-dir launches keep their own scope."""
import os
from pathlib import Path
import tempfile

from .paths import cache_file, local_path
from .usage import backup

FILENAME = 'desktop-history.json'
MAX_BYTES = 8192


def folder(value):
    if not isinstance(value, (str, Path)) or len(str(value)) > 2048:
        raise backup.BackupError('unsafe_path')
    path = local_path(value)
    if path is None or not path.is_dir():
        raise backup.BackupError('unsafe_path')
    return path


def read(anchor):
    """No chains, fallback, directory creation, source probing or environment changes."""
    path = cache_file(FILENAME, anchor)
    if path is None:
        raise backup.BackupError('unsafe_path')
    raw = backup._read_bytes(path, MAX_BYTES, absent=True)
    if raw is None:
        return None
    value = backup._json(raw)
    if set(value) != {'format', 'selected', 'previous'} or type(value['format']) is not int or value['format'] != 1:
        raise backup.BackupError('invalid')
    selected = value['selected']
    if not isinstance(selected, str) or len(selected) > 2048 or local_path(selected) is None:
        raise backup.BackupError('unsafe_path')
    previous = value['previous']
    if not isinstance(previous, str) or local_path(previous) is None or len(previous) > 2048:
        raise backup.BackupError('unsafe_path')
    return dict(selected=Path(selected), previous=Path(previous))


def save(anchor, selected, previous):
    """Atomic small selector. Only normal desktop launches opt into this record."""
    selected = folder(selected)
    if local_path(anchor) != anchor or local_path(previous) != previous:
        raise backup.BackupError('unsafe_path')
    anchor.mkdir(mode=0o700, parents=True, exist_ok=True)
    anchor = folder(anchor)
    path = cache_file(FILENAME, anchor)
    if path is None:
        raise backup.BackupError('unsafe_path')
    # Preserve a malformed existing choice for manual inspection instead of overwriting it.
    if path.exists():
        read(anchor)
    data = backup._encoded(dict(format=1, selected=str(selected), previous=str(previous)))
    temporary = None
    try:
        descriptor, name = tempfile.mkstemp(prefix='.pler-history-', dir=str(anchor))
        temporary = Path(name)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        if cache_file(FILENAME, anchor) != path:
            raise backup.BackupError('unsafe_path')
        os.replace(temporary, path)
        backup._sync_directory(anchor)
    except OSError as error:
        raise backup.BackupError('io') from error
    finally:
        if temporary is not None and local_path(temporary) == temporary:
            temporary.unlink(missing_ok=True)
