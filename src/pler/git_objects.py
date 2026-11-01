"""Is a commit still on a branch? A read-only, bounded walk over local Git commit objects.

Here only commit objects are opened, and only their parent ids and committer time are used. Author and
committer identities and messages are never kept. git_survival.py reuses the object reader for trees and
files, in memory only. Branch names are read only to find
branch tips and are discarded. No Git program runs and nothing is written. Loose objects and version-2
pack indexes (with delta entries) are supported. Anything else gives 'unknown', never a guess: alternates,
missing or shallow history, a very long walk or an unreadable object.
"""
import bisect
import heapq
import os
from pathlib import Path
import stat
import threading
import zlib

from .paths import local_path

MAX_COMMITS = 20000      # objects read per repository walk
MAX_OBJECT = 1 << 20     # a commit header is small; never inflate more than this
MAX_INDEX = 64 << 20     # largest pack index read
MAX_REFS = 10000
MAX_DEPTH = 64           # delta chain
SLACK = 86400            # committer clocks and rebases can disagree with reflog times
_CHUNK = 1 << 16
# Walk answers by (repository, tips, targets, since). Commit objects are immutable, so the same tips always give
# the same answer once every target is known; answers with an unknown target are never kept (an object or a
# longer history may appear later).
_WALKS = {}
_WALKS_LOCK = threading.Lock()
MAX_WALKS = 256


def _safe(path):
    """A local, link-free path or None."""
    return local_path(path)


def _read(path, limit):
    path = _safe(path)
    if path is None:
        return None
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            return None
        with path.open('rb') as stream:
            return stream.read(limit + 1)[:limit]
    except OSError:
        return None


def _regular(folder, name, limit):
    """A regular file (never a link) inside an already checked folder."""
    if folder is None:
        return None
    path = folder / name
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            return None
        with path.open('rb') as stream:
            return stream.read(limit + 1)[:limit]
    except OSError:
        return None


def _common(directory):
    """Objects and refs live in the common directory of a linked worktree."""
    pointer = _read(directory / 'commondir', 4096)
    if pointer:
        text = pointer.decode('utf-8', 'replace').strip()
        if not text or text[:2] in ('//', '\\\\', '/\\', '\\/'):
            return None
        return _safe(os.path.normpath(os.path.join(str(directory), text)))
    return directory


def _hex(value, size):
    value = value.strip().lower()
    return value if len(value) == size * 2 and all(c in '0123456789abcdef' for c in value) else None


def tips(directory, size):
    """Commit ids at HEAD and at every local and remote-tracking branch."""
    common = _common(directory)
    if common is None:
        return None
    found = set()
    head = _read(directory / 'HEAD', 4096)
    if head:
        text = head.decode('utf-8', 'replace').strip()
        if not text.startswith('ref:') and _hex(text, size):
            found.add(_hex(text, size))
    for folder in ('heads', 'remotes'):
        base = _safe(common / 'refs' / folder)
        pending = [base] if base is not None else []
        while pending and len(found) < MAX_REFS:
            current = pending.pop()
            try:
                entries = list(os.scandir(current))
            except OSError:
                continue
            for entry in entries:
                try:
                    info = entry.stat(follow_symlinks=False)
                except OSError:
                    continue
                if stat.S_ISDIR(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400:
                    pending.append(Path(entry.path))
                elif stat.S_ISREG(info.st_mode):
                    raw = _read(Path(entry.path), 4096)
                    value = _hex(raw.decode('ascii', 'replace'), size) if raw else None
                    if value:
                        found.add(value)
    packed = _read(common / 'packed-refs', 32 << 20)
    for line in (packed or b'').splitlines():
        parts = line.decode('ascii', 'replace').split(' ', 1)
        if len(parts) == 2 and parts[1].startswith(('refs/heads/', 'refs/remotes/')) and _hex(parts[0], size):
            found.add(_hex(parts[0], size))
    return found


class Objects:
    """Commit objects of one repository: loose files and version-2 pack indexes."""

    def __init__(self, directory, size):
        self.size = size
        common = _common(directory)
        self.base = _safe(common / 'objects') if common is not None else None
        self.indexes = None
        self.streams = {}
        self.fanout = {}

    def close(self):
        for stream in self.streams.values():
            stream.close()
        self.streams.clear()

    def _load_indexes(self):
        self.indexes = []
        folder = _safe(self.base / 'pack') if self.base is not None else None
        try:
            names = sorted(os.listdir(folder)) if folder is not None else []
        except OSError:
            names = []
        for name in names:
            if not name.endswith('.idx'):
                continue
            raw = _read(folder / name, MAX_INDEX)
            pack = _safe(folder / (name[:-4] + '.pack'))
            if not raw or pack is None or raw[:8] != b'\xfftOc\x00\x00\x00\x02':
                continue
            count = int.from_bytes(raw[8 + 255 * 4:8 + 256 * 4], 'big')
            names_at = 8 + 256 * 4
            offsets_at = names_at + count * self.size + count * 4
            if len(raw) < offsets_at + count * 4:
                continue
            self.indexes.append((raw, count, names_at, offsets_at, pack))

    def _locate(self, key):
        if self.indexes is None:
            self._load_indexes()
        for raw, count, names_at, offsets_at, pack in self.indexes:
            first = key[0]
            low = int.from_bytes(raw[8 + (first - 1) * 4:8 + first * 4], 'big') if first else 0
            high = int.from_bytes(raw[8 + first * 4:8 + (first + 1) * 4], 'big')
            entries = _Names(raw, names_at, self.size)
            position = bisect.bisect_left(entries, key, low, high)
            if position < high and entries[position] == key:
                offset = int.from_bytes(raw[offsets_at + position * 4:offsets_at + position * 4 + 4], 'big')
                if offset & 0x80000000:
                    large = offsets_at + count * 4 + (offset & 0x7fffffff) * 8
                    offset = int.from_bytes(raw[large:large + 8], 'big')
                return pack, offset
        return None

    def _stream(self, pack):
        if pack not in self.streams:
            self.streams[pack] = pack.open('rb')
        return self.streams[pack]

    def _inflate(self, stream, limit):
        engine, parts, total = zlib.decompressobj(), [], 0
        while not engine.eof:
            chunk = engine.unconsumed_tail or stream.read(_CHUNK)
            if not chunk:
                return None
            piece = engine.decompress(chunk, limit + 1 - total)
            parts.append(piece)
            total += len(piece)
            if total > limit:
                return None
        return b''.join(parts)

    def _packed(self, pack, offset, depth=0):
        if depth > MAX_DEPTH:
            return None
        stream = self._stream(pack)
        stream.seek(offset)
        header = stream.read(64)
        if not header:
            return None
        byte, used = header[0], 1
        kind, length, shift = (byte >> 4) & 7, byte & 15, 4
        while byte & 0x80 and used < len(header):
            byte = header[used]; used += 1
            length |= (byte & 0x7f) << shift; shift += 7
        base = None
        if kind == 6:  # offset delta
            byte = header[used]; used += 1
            distance = byte & 0x7f
            while byte & 0x80 and used < len(header):
                byte = header[used]; used += 1
                distance = ((distance + 1) << 7) | (byte & 0x7f)
            base = self._packed(pack, offset - distance, depth + 1)
        elif kind == 7:  # reference delta
            key = header[used:used + self.size]; used += self.size
            base = self._object(key, depth + 1)
        elif kind not in (1, 2, 3, 4):
            return None
        if length > MAX_OBJECT:
            return None
        stream.seek(offset + used)
        data = self._inflate(stream, MAX_OBJECT)
        if data is None:
            return None
        if kind in (6, 7):
            if base is None:
                return None
            data = _apply(base[1], data)
            return (base[0], data) if data is not None else None
        return kind, data

    def _folder(self, prefix):
        """A fan-out folder of the checked objects folder and its file names; checked and listed once.

        Its parents were checked with the objects folder, so one look at the folder itself refuses a link,
        and a packed object then costs no file-system call here."""
        if prefix not in self.fanout:
            folder, names = self.base / prefix, set()
            try:
                info = folder.lstat()
                if (stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode)
                        and not getattr(info, 'st_file_attributes', 0) & 0x400):
                    with os.scandir(str(folder)) as entries:
                        names = {entry.name for entry in entries if entry.is_file(follow_symlinks=False)}
                else:
                    folder = None
            except OSError:
                folder = None
            self.fanout[prefix] = (folder, names)
        return self.fanout[prefix]

    def _object(self, key, depth=0):
        """(type, bytes) for a binary object id, or None."""
        hexed = key.hex()
        if self.base is None:
            return None
        folder, names = self._folder(hexed[:2])
        loose = _regular(folder, hexed[2:], MAX_OBJECT) if hexed[2:] in names else None
        if loose is not None:
            try:
                data = zlib.decompressobj().decompress(loose, MAX_OBJECT + 64)
            except zlib.error:
                return None
            head, _, body = data.partition(b'\0')
            kind = {b'commit': 1, b'tree': 2, b'blob': 3, b'tag': 4}.get(head.split(b' ', 1)[0])
            return (kind, body) if kind else None
        found = self._locate(key)
        if found is None:
            return None
        try:
            return self._packed(*found, depth=depth)
        except (OSError, zlib.error, IndexError, ValueError):
            return None

    def commit(self, hexed):
        """(committer time, [parent ids]) of a commit, or None. Everything else in the object is skipped."""
        try:
            found = self._object(bytes.fromhex(hexed))
        except ValueError:
            return None
        if not found or found[0] != 1:
            return None
        parents, moment = [], None
        for line in found[1].split(b'\n'):
            if not line:
                break  # the message follows; it is never read
            if line.startswith(b'parent '):
                value = _hex(line[7:].decode('ascii', 'replace'), self.size)
                if value is None:
                    return None
                parents.append(value)
            elif line.startswith(b'committer '):
                parts = line.rsplit(b' ', 2)
                moment = int(parts[1]) if len(parts) == 3 and parts[1].isdigit() else None
        return moment, parents


class _Names:
    """Sorted object ids of a pack index, as a sequence for bisect."""

    def __init__(self, raw, start, size):
        self.raw, self.start, self.size = raw, start, size

    def __getitem__(self, position):
        at = self.start + position * self.size
        return self.raw[at:at + self.size]

    def __len__(self):
        return (len(self.raw) - self.start) // self.size


def _varint(data, at):
    value = shift = 0
    while True:
        byte = data[at]; at += 1
        value |= (byte & 0x7f) << shift; shift += 7
        if not byte & 0x80:
            return value, at


def _apply(base, delta):
    """Git's delta format: copy ranges of the base and insert new bytes."""
    try:
        source, at = _varint(delta, 0)
        target, at = _varint(delta, at)
        if source != len(base) or target > MAX_OBJECT:
            return None
        out = bytearray()
        while at < len(delta):
            op = delta[at]; at += 1
            if op & 0x80:
                offset = size = 0
                for bit in range(4):
                    if op & (1 << bit):
                        offset |= delta[at] << (8 * bit); at += 1
                for bit in range(3):
                    if op & (1 << (4 + bit)):
                        size |= delta[at] << (8 * bit); at += 1
                size = size or 0x10000
                if offset + size > len(base):
                    return None
                out += base[offset:offset + size]
            elif op:
                out += delta[at:at + op]; at += op
            else:
                return None
        return bytes(out) if len(out) == target else None
    except IndexError:
        return None


def on_branch(directory, targets, since=None, starts=None):
    """{commit id: True (on a branch), False (not on any), None (unknown)} for hexadecimal commit ids.

    `starts` replaces the branch tips (git_survival.py asks about HEAD's history only).

    Walks from every branch tip, newest committer time first. A target not met before the walk passes
    `since` (minus a day of slack) is not on a branch. A missing object, an incomplete history or the
    MAX_COMMITS bound leaves the remaining targets unknown."""
    targets = set(targets)
    if not targets:
        return {}
    size = len(next(iter(targets))) // 2
    result = dict.fromkeys(targets)
    starts = tips(Path(directory), size) if starts is None else set(starts)
    if not starts:
        return result
    key = (str(directory), size, frozenset(starts), frozenset(targets), since)
    with _WALKS_LOCK:
        known = _WALKS.get(key)
    if known is not None:
        return dict(known)
    store = Objects(Path(directory), size)
    try:
        if store.base is None or os.path.lexists(store.base / 'info' / 'alternates'):
            return result  # objects borrowed from another repository are out of scope
        # Every id pushed is reachable from a tip, whether or not its own object can be read.
        heap, seen, complete = [], set(), True
        def push(commit):
            nonlocal complete
            if commit in seen:
                return
            seen.add(commit)
            found = store.commit(commit)
            if found is None:
                complete = False
            else:
                heapq.heappush(heap, (-(found[0] or 0), commit, found[1]))
        for commit in starts:
            push(commit)
        cutoff = since - SLACK if since is not None else None
        while heap and not targets <= seen and len(seen) < MAX_COMMITS:
            if cutoff is not None and -heap[0][0] < cutoff:
                break
            for parent in heapq.heappop(heap)[2]:
                push(parent)
        # An unmet target is off every branch only when nothing that could still reach it is left unread.
        exhausted = not heap or cutoff is not None and -heap[0][0] < cutoff
        for commit in targets:
            result[commit] = True if commit in seen else (False if exhausted and complete else None)
        if None not in result.values():
            with _WALKS_LOCK:
                while len(_WALKS) >= MAX_WALKS:
                    _WALKS.pop(next(iter(_WALKS)))
                _WALKS[key] = dict(result)
        return result
    except (OSError, ValueError):
        return result
    finally:
        store.close()
