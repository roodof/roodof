"""Discover local regular log files without following network paths. The user's own links or junctions to a
log folder itself are followed; links inside a log folder never are."""
import os
from pathlib import Path
import stat

from ..git_activity import _local_path
from ..paths import network, user_folder
from ..wsl import WslRoots
from .records import note_file_issue


def _checked(path, issues, check):
    # Reject network syntax before any filesystem access, including on Windows.
    value=str(path)
    if network(value):
        note_file_issue(issues,path,'UnsafePath')
        return None
    try:
        # The selected root resolver must see '..' after a link, before lexical normalization.
        expanded=os.path.expanduser(value)
        result=check(expanded if check is user_folder else os.path.abspath(expanded))
        if result is None: note_file_issue(issues,path,'UnsafePath')
        return result
    except (OSError,ValueError,RuntimeError) as error:
        note_file_issue(issues,path,type(error).__name__)
        return None


def _wsl(path, issues, access, explicit=False):
    try:
        result,reason=(access.chosen(path) if explicit else access.source(path)) if access else (None,'UnsafePath')
        if result is None: note_file_issue(issues,path,reason)
        return result
    except (OSError,ValueError,RuntimeError) as error:
        note_file_issue(issues,path,type(error).__name__)
        return None


def local(path, issues=None, access=None):
    if network(path):
        return _wsl(path,issues,access)
    return _checked(path,issues,_local_path)


def chosen(path, issues=None, access=None, explicit=False):
    """A log folder the user chose (home default, environment variable or option), through their own links."""
    if network(path):
        return _wsl(path,issues,access,explicit)
    return _checked(path,issues,user_folder)


def unique(paths):
    """WSL names retain Linux case sensitivity even when represented by WindowsPath."""
    found={}
    for path in map(Path,paths):
        key=str(path) if network(path) else path
        found.setdefault(key,path)
    return sorted(found.values(),key=str)


def folders(bases, names, issues=None, access=None, explicit=False):
    result=[]
    for base in bases:
        safe=chosen(base,issues,access,explicit)
        if safe is None: continue
        for name in names:
            path=chosen(safe/name,issues,access)
            if path is None: continue
            try:
                if path.is_dir(): result.append(path)
            except OSError as error: note_file_issue(issues,path,type(error).__name__)
    return result


def files(roots, matches, issues=None, access=None, explicit=True):
    found=[]
    pending=[]
    for root in roots:
        safe=chosen(root,issues,access,explicit)
        if safe is not None: pending.append(safe)
    while pending:
        directory=pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        info=entry.stat(follow_symlinks=False)
                        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
                            note_file_issue(issues,entry.path,'UnsafePath')
                        elif stat.S_ISDIR(info.st_mode): pending.append(Path(entry.path))
                        elif stat.S_ISREG(info.st_mode) and matches(entry.name): found.append(Path(entry.path))
                    except OSError as error: note_file_issue(issues,entry.path,type(error).__name__)
        except OSError as error: note_file_issue(issues,directory,type(error).__name__)
    return unique(found)
