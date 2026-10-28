"""Which project a session belongs to: its git repository root, else its working folder.

Agents log the folder they were started in. The same project then appears under several names: a
subfolder (app/panel), or the same path with another letter case (Windows paths are case-insensitive,
and Claude Code and Codex do not spell them alike). Sessions are grouped by the nearest folder holding
`.git`, never at or above the home folder (a dotfiles repository there would swallow everything).
Sessions started anywhere in the temporary folder (scripts, tools, throwaway checkouts) form one group.
Only the file system is looked at; no git command runs.
"""
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
        for candidate in [current] + list(current.parents):
            key = _key(str(candidate))
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

    def root(self, path):
        if not path:
            return path
        key = _key(path)
        if key == self.temp or key.startswith(self.temp.rstrip(os.sep) + os.sep):
            return self.temp_path
        if key not in self.cache:
            found = self._git_root(path)
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
