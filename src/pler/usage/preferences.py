"""Tiny local retention preference; no agent settings or account identities.

Archive writes and preference changes share archive.py's lock. This reader is
also safe on its own: a missing preference keeps the existing default, while an
invalid/unreadable preference must be handled as retention disabled by callers.
"""
import json

from ..paths import cache_file

FILENAME='retention-preferences.json'
FORMAT=1
MAX_BYTES=4096


def read(base):
    """Return the saved boolean, defaulting to True only for an absent file."""
    path=cache_file(FILENAME,base)
    if path is None:
        raise OSError('unsafe retention preference')
    try:
        size=path.stat().st_size
        if size>MAX_BYTES:
            raise ValueError('oversized retention preference')
        with path.open('rb') as stream:
            data=stream.read(size+1)
        if len(data)!=size:
            raise ValueError('retention preference changed while reading')
        value=json.loads(data.decode('utf-8'))
    except RecursionError as error:
        raise ValueError('over-nested retention preference') from error
    except FileNotFoundError:
        return True
    if (not isinstance(value,dict) or set(value)!={'format','retention_enabled'}
            or type(value.get('format')) is not int or value['format']!=FORMAT
            or type(value.get('retention_enabled')) is not bool):
        raise ValueError('invalid retention preference')
    return value['retention_enabled']


def value(enabled):
    if type(enabled) is not bool:
        raise ValueError('retention preference requires a boolean')
    return dict(format=FORMAT,retention_enabled=enabled)
