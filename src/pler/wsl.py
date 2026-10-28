"""Explicit WSL log roots, scoped to one scan. All other UNC locations stay refused.

Only the Windows WSL status command runs. It neither selects nor starts a distro. A fresh running-state
snapshot gates discovery and each reader phase; an external stop between that check and a UNC operation
is an unavoidable race. No positive state is retained across scans.
"""
import ntpath
import os
from pathlib import Path, PureWindowsPath
import stat
import subprocess

from .paths import local_path

WINDOWS = os.name == 'nt'
HOSTS = {'wsl.localhost', 'wsl$'}
MAX_STATUS_BYTES = 65536


def _component(value):
    return (bool(value) and value not in ('.', '..') and value == value.strip()
            and value[-1] not in '. ' and not any(ord(c) < 32 or c in '<>:"/\\|?*' for c in value))


def split(value):
    """Parse the two ordinary WSL UNC hosts lexically, before any filesystem operation.

    Extended/device spellings, mixed initial slashes, host aliases, dot components and drive/stream
    spellings are deliberately unsupported. Distro names must subsequently match the running list.
    """
    text = str(value)
    if not text.startswith('\\\\') or text.startswith('\\\\\\'):
        return None
    parts = text[2:].replace('/', '\\').split('\\')
    if len(parts) < 2 or parts[0].lower() not in HOSTS or not _component(parts[1]):
        return None
    tail = parts[2:]
    if tail and tail[-1] == '':
        tail.pop()
    if any(not _component(part) for part in tail):
        return None
    return parts[1], tuple(tail)


def _executable():
    """Use the local OS directory, never PATH or the working directory."""
    base = os.environ.get('SystemRoot', '')
    drive, rest = ntpath.splitdrive(base)
    if (len(drive) != 2 or not drive[0].isascii() or not drive[0].isalpha() or drive[1] != ':'
            or not rest.startswith(('\\', '/'))):
        return None
    try:
        return local_path(ntpath.join(base, 'System32', 'wsl.exe'))
    except (OSError, ValueError, RuntimeError):
        return None


def _names(raw):
    """Redirected wsl.exe output is often UTF-16LE; malformed or unexpected output fails closed."""
    if not isinstance(raw, bytes) or len(raw) > MAX_STATUS_BYTES:
        return None
    try:
        if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
            value = raw.decode('utf-16')
        elif b'\x00' in raw:
            # WSL's unmarked UTF-16 stream has ASCII name/newline characters in the low byte.
            # Do not reinterpret a NUL embedded in otherwise plain UTF-8 as a different name.
            if len(raw) % 2 or not any(raw[index] == 0 and raw[index - 1] != 0 for index in range(1,len(raw),2)):
                return None
            value = raw.decode('utf-16-le')
        else:
            value = raw.decode('utf-8-sig')
    except UnicodeError:
        return None
    names = {}
    for name in value.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
        if not name:
            continue
        key = name.casefold()
        if not _component(name) or key in names:
            return None
        names[key] = name
    return names


def running():
    """None means status is unavailable; an empty mapping means no distro is running."""
    if not WINDOWS:
        return None
    executable = _executable()
    if executable is None:
        return None
    try:
        result = subprocess.run([str(executable), '--list', '--running', '--quiet'],
                                shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, timeout=3, creationflags=0x08000000)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return _names(result.stdout) if result.returncode == 0 else None


class WslRoots:
    """A capability for roots explicitly selected by this scan, never log/project metadata."""
    def __init__(self):
        self.roots = []
        self._status = None
        self._queried = False

    def read_phase(self):
        # Readers call this even when a cache could supply the records. A previous discovery result
        # must never authorize access to a distro which has since stopped.
        self._status, self._queried = None, False

    def _canonical(self, value):
        parsed = split(value)
        if not WINDOWS or parsed is None:
            return None, 'UnsafePath'
        if not self._queried:
            self._status, self._queried = running(), True
        if self._status is None:
            return None, 'WSLUnavailable'
        distro, tail = parsed
        actual = self._status.get(distro.casefold())
        if actual is None:
            return None, 'WSLNotRunning'
        return PureWindowsPath('\\\\wsl.localhost\\' + actual + '\\', *tail), None

    @staticmethod
    def _checked(path):
        # Do not inspect a UNC host root. The first probe is inside the already-running distro.
        current = PureWindowsPath(path.anchor)
        for part in (None, *path.parts[1:]):
            if part is not None:
                current = current / part
            try:
                info = Path(str(current)).lstat()
            except FileNotFoundError:
                break
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                return None
        return Path(str(path))

    def chosen(self, value):
        path, reason = self._canonical(value)
        if path is None:
            return None, reason
        safe = self._checked(path)
        if safe is None:
            return None, 'UnsafePath'
        if not any(root.parts == path.parts for root in self.roots):
            self.roots.append(path)
        return safe, None

    def source(self, value):
        # Check lexical membership before querying status, so arbitrary UNC input cannot run a program.
        parsed = split(value)
        if not WINDOWS or parsed is None:
            return None, 'UnsafePath'
        distro, tail = parsed
        candidate = PureWindowsPath('\\\\wsl.localhost\\' + distro + '\\', *tail)
        if not any(candidate.drive.casefold() == root.drive.casefold()
                   and candidate.parts[1:len(root.parts)] == root.parts[1:]
                   and len(candidate.parts) >= len(root.parts) for root in self.roots):
            return None, 'UnsafePath'
        path, reason = self._canonical(value)
        if path is None:
            return None, reason
        safe = self._checked(path)
        return (safe, None) if safe is not None else (None, 'UnsafePath')
