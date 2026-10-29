"""Lexical identities for logged edit targets; never inspect files or repositories.

The spelling of the logged path chooses its rules, not the viewing operating system.
Aliases such as a Windows drive and its WSL mount remain different identities.
"""
import ntpath
import posixpath
import re


_DRIVE_ABSOLUTE = re.compile(r'^[A-Za-z]:[\\/]')
_DRIVE = re.compile(r'^[A-Za-z]:')
MAX_TARGET_LENGTH = 1024


def _text(value):
    return isinstance(value, str) and 0 < len(value) <= MAX_TARGET_LENGTH and '\0' not in value


def _network(value):
    return len(value) > 1 and value[0] in '/\\' and value[1] in '/\\'


def _absolute(value):
    if not _text(value) or _network(value):
        return None
    if _DRIVE_ABSOLUTE.match(value):
        return ntpath.normcase(ntpath.normpath(value)).casefold()
    if _DRIVE.match(value) or value.startswith('\\'):
        return None
    if value.startswith('/'):
        # Backslashes in this spelling could be Windows separators or literal
        # POSIX filename characters. Neither interpretation is established.
        return posixpath.normpath(value) if '\\' not in value else None
    return None


def canonical_target(value, cwd=None):
    """Return a normalized absolute target, or None when its identity is ambiguous.

    Relative targets require the working directory at the edit record. This does
    not expand a home folder, resolve links, consult the current process cwd, or
    query file existence. Drive-relative, network and device paths are refused.
    """
    if not _text(value) or _network(value):
        return None
    if _DRIVE_ABSOLUTE.match(value):
        return _absolute(value)
    if _DRIVE.match(value) or value.startswith('\\'):
        return None
    if value.startswith('/'):
        # With a Windows cwd, /name could be rooted on its drive. Do not guess
        # whether it instead names a POSIX absolute target.
        if _text(cwd) and _DRIVE_ABSOLUTE.match(cwd):
            return None
        return _absolute(value)
    base = _absolute(cwd)
    if base is None:
        return None
    if _DRIVE_ABSOLUTE.match(base):
        return _absolute(ntpath.join(base, value))
    if '\\' in value:
        return None
    return _absolute(posixpath.join(base, value))
