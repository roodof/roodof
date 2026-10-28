"""Discover local regular log files without following symlinks, junctions or network paths."""
import os
from pathlib import Path
import stat

from ..git_activity import _local_path
from ..paths import network
from .records import note_file_issue


def local(path, issues=None):
    # Reject network syntax before any filesystem access, including on Windows.
    value=str(path)
    if network(value):
        note_file_issue(issues,path,'UnsafePath')
        return None
    try:
        result=_local_path(os.path.abspath(os.path.expanduser(value)))
        if result is None: note_file_issue(issues,path,'UnsafePath')
        return result
    except (OSError,ValueError,RuntimeError) as error:
        note_file_issue(issues,path,type(error).__name__)
        return None


def folders(bases, names, issues=None):
    result=[]
    for base in bases:
        safe=local(base,issues)
        if safe is None: continue
        for name in names:
            path=local(safe/name,issues)
            if path is None: continue
            try:
                if path.is_dir(): result.append(path)
            except OSError as error: note_file_issue(issues,path,type(error).__name__)
    return result


def files(roots, matches, issues=None):
    found=[]
    pending=[]
    for root in roots:
        safe=local(root,issues)
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
    return sorted(set(found),key=str)
