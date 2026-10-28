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


def key(path):
    """A lexical scope key; WSL tails keep Linux case and no filesystem is consulted."""
    from ..wsl import split
    parsed=split(path) if network(path) else None
    if parsed is not None:
        return ('wsl',parsed[0].casefold(),*parsed[1])
    if network(path): return None
    return ('local',*Path(os.path.abspath(os.path.expanduser(str(path)))).parts)


def contains(root,path):
    a,b=key(root),key(path)
    if a is None or b is None: return False
    if a[0]=='local' and os.name=='nt':
        a,b=tuple(v.casefold() for v in a),tuple(v.casefold() for v in b)
    return len(a)<=len(b) and b[:len(a)]==a


class Manifest:
    """Selected roots and successful whole-root enumeration, never an inference from an empty list."""
    def __init__(self):
        self.roots={}
        self.complete=set()
        self.found=set()

    def select(self,path):
        value=key(path)
        if value is not None: self.roots[value]=str(path)

    def selected(self,path):
        return any(contains(root,path) for root in self.roots.values())

    def scope(self,path):
        roots=[root for root in self.roots.values() if contains(root,path)]
        return max(roots,key=lambda value:len(key(value)),default=None)

    def missing(self,path):
        return (key(path) not in self.found
                and any(contains(self.roots[root],path) for root in self.complete))


def folders(bases, names, issues=None, access=None, explicit=False, manifest=None):
    result=[]
    for base in bases:
        if manifest is not None:
            for name in names: manifest.select(Path(base)/name)
        safe=chosen(base,issues,access,explicit)
        if safe is None: continue
        for name in names:
            path=chosen(safe/name,issues,access)
            if path is None: continue
            if manifest is not None: manifest.select(path)
            try:
                if stat.S_ISDIR(path.stat().st_mode): result.append(path)
            except FileNotFoundError: pass
            except OSError as error: note_file_issue(issues,path,type(error).__name__)
    return result


def files(roots, matches, issues=None, access=None, explicit=True, manifest=None):
    found=[]
    pending=[]
    for root in roots:
        if manifest is not None: manifest.select(root)
        safe=chosen(root,issues,access,explicit)
        if safe is not None:
            if manifest is not None: manifest.select(safe)
            pending.append((safe,key(safe)))
    complete={scope:True for _,scope in pending}
    while pending:
        directory,scope=pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        info=entry.stat(follow_symlinks=False)
                        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
                            note_file_issue(issues,entry.path,'UnsafePath')
                            complete[scope]=False
                        elif stat.S_ISDIR(info.st_mode): pending.append((Path(entry.path),scope))
                        elif stat.S_ISREG(info.st_mode) and matches(entry.name):
                            found.append(Path(entry.path))
                            if manifest is not None: manifest.found.add(key(entry.path))
                    except OSError as error:
                        complete[scope]=False
                        note_file_issue(issues,entry.path,type(error).__name__)
        except OSError as error:
            complete[scope]=False
            note_file_issue(issues,directory,type(error).__name__)
    if manifest is not None:
        manifest.complete.update(scope for scope,done in complete.items() if done)
    return unique(found)
