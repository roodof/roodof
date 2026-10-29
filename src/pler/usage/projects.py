"""Which project a session belongs to: its git repository root, else its working folder.

Agents log the folder they were started in. The same project then appears under several names: a
subfolder (app/panel), or the same path with another letter case (Windows paths are case-insensitive,
and Claude Code and Codex do not spell them alike). Sessions are grouped by the nearest folder holding
`.git`, never at or above the home folder (a dotfiles repository there would swallow everything).
Separate repositories inside the temporary folder stay separate; other temporary work forms one group.
Only the file system is looked at; no git command runs.
"""
import hashlib
import os
from pathlib import Path
import stat
import tempfile

from ..i18n import say
from ..git_activity import _local_path


def _key(path):
    return os.path.normcase(os.path.normpath(path))


def label(path, home=None, temp=None, lang='en'):
    """Display name: the last two folders are enough to recognise a project; temp and home say what they are."""
    if not path:
        return None
    key = _key(path)
    if key == _key(str(temp or tempfile.gettempdir())):
        return say(lang, 'temp_folders')
    if key == _key(str(home or Path.home())):
        return say(lang, 'home_folder')
    parts = [part for part in path.replace('\\', '/').split('/') if part]
    return '/'.join(parts[-2:]) if len(parts) > 1 else path


def labels(paths, lang='en', home=None, temp=None):
    """Safe display names for a complete project selection, with opaque collision suffixes.

    Equivalent spellings under the viewing host's project rules share a label.
    Distinct projects with the same short name never expose extra ancestors to
    distinguish them. Callers keep this full-timeline mapping when filtering.
    """
    grouped = {}
    for path in paths:
        identity = ('project', _key(path)) if path else ('unknown', '')
        grouped.setdefault(identity, set()).add(path)
    names, codes = {}, {}
    for identity, spellings in grouped.items():
        shown = min((value for value in spellings if value), key=lambda value:(value.casefold(), value), default=None)
        names[identity] = label(shown, home, temp, lang) or say(lang, 'unknown_project').capitalize()
        codes[identity] = hashlib.sha256((identity[0] + ':' + identity[1]).encode('utf-8')).hexdigest()
    collisions = {}
    for identity, name in names.items():
        collisions.setdefault(name.casefold(), []).append(identity)
    suffixes = {identity:8 for group in collisions.values() if len(group)>1 for identity in group}
    # Prefixes expand together if a short code or a literal name collides. The
    # hash is private identity evidence, not a user-provided path excerpt.
    while True:
        displayed = {identity:name + (' #' + codes[identity][:suffixes[identity]] if identity in suffixes else '')
                     for identity,name in names.items()}
        by_name = {}
        for identity,name in displayed.items(): by_name.setdefault(name.casefold(), []).append(identity)
        duplicates = [group for group in by_name.values() if len(group)>1]
        if not duplicates: break
        for group in duplicates:
            for identity in group: suffixes[identity] = suffixes.get(identity,7)+1
        if any(length>64 for length in suffixes.values()):
            # A complete digest collision is extraordinarily unlikely, but
            # deterministic ordering still prevents an ambiguous UI label.
            for group in duplicates:
                for index,identity in enumerate(sorted(group)):
                    displayed[identity] += '-' + str(index+1)
            break
    return {path:displayed[identity] for identity,spellings in grouped.items() for path in spellings}


class ProjectRoots:
    def __init__(self, home=None, temp=None):
        self.home = _key(str(home or Path.home()))
        self.temp_path = os.path.normpath(str(temp or tempfile.gettempdir()))
        self.temp = _key(self.temp_path)
        self.cache = {}
        self.spelling = {}  # canonical key -> first spelling seen, so one project has one name

    def _git_root(self, folder):
        try:
            current = _local_path(folder)
        except (OSError, ValueError, RuntimeError):
            return None
        if current is None:
            return None
        inside_temp = self._temporary(_key(str(current)))
        for candidate in [current] + list(current.parents):
            key = _key(str(candidate))
            if inside_temp and key == self.temp:
                return None  # a shared temporary root, or its ancestors, is not this project
            if key == self.home or len(key) <= len(self.home) and self.home.startswith(key):
                return None  # at or above home
            try:
                info = (candidate / '.git').lstat()
                if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
                    return None
                return str(candidate)
            except FileNotFoundError:
                continue
            except (OSError, ValueError):
                return None
        return None

    def _temporary(self, key):
        return key == self.temp or key.startswith(self.temp.rstrip(os.sep) + os.sep)

    def root(self, path):
        if not path:
            return path
        key = _key(path)
        if key not in self.cache:
            found = self._git_root(path)
            if found is None and self._temporary(key):
                self.cache[key] = self.temp_path
                return self.temp_path
            canonical = _key(found) if found else key
            self.spelling.setdefault(canonical, os.path.normpath(found or path))
            self.cache[key] = self.spelling[canonical]
        return self.cache[key]


def assign(sessions, home=None, temp=None):
    """Replace each session's project by its repository root (or normalised folder); returns the sessions."""
    roots = ProjectRoots(home, temp)
    for session in sessions:
        session.project = roots.root(session.project)
    return sessions
