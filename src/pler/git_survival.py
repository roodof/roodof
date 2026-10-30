"""Are the lines a session's commits added still in place? A bounded, read-only look at Git trees and files.

For a commit made during a session that is still in the current HEAD's history, its added lines are the
lines whose count in a file grew compared with its first parent. Each is looked for, by content, in the
same file at HEAD. Blank lines and lines without a letter or digit (a lone `}`) are not counted.

File names and contents are read only in memory, through git_objects.py; only counts leave this module.
No Git program runs and nothing is written to the repository; with a Saved store, the counts alone are kept
in PLER's cache folder. Merge/root commits and traversal-limited histories are not measurable; binary,
very large or unreadable files are skipped. Renames are not followed: additions are per-path count
increases, not proof of newly written code. A line moved within its file counts as kept; a rewritten
line or a file moved to another path does not.
"""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from . import git_objects
from .git_objects import MAX_OBJECT, Objects, _common, _hex, _read, on_branch
from .paths import cache_file
from .runtime import checkpoint

MAX_COMMITS = 200        # commits measured per repository and scan
MAX_FILES = 400          # changed files measured per commit
MAX_BYTES = 256 << 20    # file contents inflated per repository and scan
MAX_MEMO = 20000
MAX_TREES = 4096         # distinct trees retained per repository and scan
MAX_ENTRIES = 100000     # parsed tree entries and traversal visits, independently bounded
MAX_TREE_DEPTH = 128
_TEXT_PROBE = 8000
_FIELDS = ('added', 'kept', 'files', 'skipped')
_DIGEST = re.compile('[0-9a-f]{64}')
# Counts only, under a digest of (repository, HEAD, commit): objects named by their ids never change, so a
# later read of the same HEAD reuses the counts instead of reading the files again.
_MEMO = {}
_VERSION = None


class _LimitExceeded(ValueError):
    pass


def _counts(numbers):
    return (isinstance(numbers, list) and len(numbers) == len(_FIELDS)
            and all(type(number) is int and 0 <= number < 1 << 53 for number in numbers)
            and numbers[1] <= numbers[0])


def _key(directory, tip, commit):
    return hashlib.sha256('\0'.join((str(directory), tip, commit)).encode('utf-8', 'surrogatepass')).hexdigest()


def _version():
    """Changes with the counting code, so counts from another version are never reused."""
    global _VERSION
    if _VERSION is None:
        digest = hashlib.sha256()
        for module in (__file__, git_objects.__file__):
            digest.update(Path(module).read_bytes())
        _VERSION = digest.hexdigest()[:16]
    return _VERSION


class Saved:
    """Counts kept in PLER's cache folder (git-survival.json), so that a restart does not read the same files
    again. Each key is a one-way digest of repository folder, HEAD and commit; each value is the four counts.
    No path, commit id, name or text is written. The file is rebuildable: cache reset removes it, and a
    damaged file or one written by other counting code is ignored."""
    FILENAME = 'git-survival.json'
    MAX_SIZE = 4 << 20

    def __init__(self, base=None):
        self.base, self.loaded, self.saved = base, False, None

    def _path(self):
        return cache_file(self.FILENAME) if self.base is None else cache_file(self.FILENAME, self.base)

    def load(self):
        """The saved counts, the first time only; {} when there are none or they cannot be used."""
        if self.loaded:
            return {}
        self.loaded = True
        path = self._path()
        try:
            if path is None:
                return {}
            size = path.stat().st_size
            if size > self.MAX_SIZE:
                return {}
            with path.open('rb') as stream:
                data = stream.read(size + 1)
            if len(data) != size:
                return {}
            value = json.loads(data.decode('utf-8'))
            if (not isinstance(value, dict) or type(value.get('format')) is not int or value['format'] != 1
                    or value.get('version') != _version() or not isinstance(value.get('counts'), dict)):
                return {}
            counts = {key: dict(zip(_FIELDS, numbers)) for key, numbers in value['counts'].items()
                      if isinstance(key, str) and _DIGEST.fullmatch(key) and _counts(numbers)}
        except (OSError, ValueError, AttributeError, RecursionError):
            return {}
        self.saved = frozenset(counts)
        return dict(list(counts.items())[:MAX_MEMO])

    def save(self, memo):
        """Replace the file with `memo` when its keys differ from what was last read or written; a file that
        cannot be written is skipped, never an error."""
        clean = {}
        for key, value in memo.items():
            if len(clean) >= MAX_MEMO:
                break
            if not isinstance(key, str) or not _DIGEST.fullmatch(key) or not isinstance(value, dict):
                continue
            numbers = [value.get(name) for name in _FIELDS]
            if _counts(numbers):
                clean[key] = numbers
        keys = frozenset(clean)
        path = self._path()
        if keys == self.saved or path is None:
            return
        temporary = None
        try:
            body = json.dumps(dict(format=1, version=_version(),
                                   counts=clean),
                              separators=(',', ':'))
            if len(body) > self.MAX_SIZE:
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            if cache_file(path.name, path.parent) != path:
                return
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=str(path.parent), prefix=path.name + '.',
                                             suffix='.tmp', delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(body)
            if cache_file(path.name, path.parent) != path:
                return
            os.replace(str(temporary), str(path))
            temporary, self.saved = None, keys
        except (OSError, MemoryError):
            pass
        finally:
            if temporary is not None:
                try:
                    if cache_file(temporary.name, temporary.parent) == temporary:
                        temporary.unlink()
                except OSError:
                    pass


def head(directory, size):
    """The commit id at HEAD (following one symbolic reference), or None."""
    directory = Path(directory)
    raw = _read(directory / 'HEAD', 4096)
    if not raw:
        return None
    text = raw.decode('utf-8', 'replace').strip()
    if not text.startswith('ref:'):
        return _hex(text, size)
    name = text[4:].strip()
    if not name.startswith('refs/heads/') or '..' in name.split('/'):
        return None
    common = _common(directory)
    if common is None:
        return None
    for folder in (directory, common):
        value = _read(folder / name, 4096)
        if value and _hex(value.decode('ascii', 'replace'), size):
            return _hex(value.decode('ascii', 'replace'), size)
    packed = _read(common / 'packed-refs', 32 << 20)
    for line in (packed or b'').splitlines():
        parts = line.decode('ascii', 'replace').split(' ', 1)
        if len(parts) == 2 and parts[1].strip() == name and _hex(parts[0], size):
            return _hex(parts[0], size)
    return None


class _Reader:
    def __init__(self, directory, size):
        self.store, self.size, self.trees, self.files, self.spent = Objects(Path(directory), size), size, {}, {}, 0
        self.entries = self.visits = 0
        self.limited = False

    def limit(self):
        self.limited = True
        raise _LimitExceeded('Git traversal limit reached')

    def close(self):
        self.store.close()

    def commit(self, hexed):
        """(tree id, [parent ids]) from a commit header; identities and the message are never read."""
        checkpoint()
        found = self.store._object(bytes.fromhex(hexed))
        checkpoint()
        if not found or found[0] != 1:
            return None
        tree, parents = None, []
        for line in found[1].split(b'\n'):
            checkpoint()
            if not line:
                break
            if line.startswith(b'tree '):
                tree = _hex(line[5:].decode('ascii', 'replace'), self.size)
            elif line.startswith(b'parent '):
                parents.append(_hex(line[7:].decode('ascii', 'replace'), self.size))
        return (tree, parents) if tree and None not in parents else None

    def tree(self, hexed):
        """{name: (is_tree, id)} for regular files and folders; links and submodules are skipped."""
        checkpoint()
        if hexed not in self.trees:
            if len(self.trees) >= MAX_TREES:
                self.limit()
            found = self.store._object(bytes.fromhex(hexed))
            entries = None
            if found and found[0] == 2:
                entries, data, at = {}, found[1], 0
                while at < len(data):
                    checkpoint()
                    if self.entries >= MAX_ENTRIES:
                        self.limit()
                    self.entries += 1
                    space = data.index(b' ', at)
                    end = data.index(b'\0', space)
                    mode, name = data[at:space], data[space + 1:end]
                    key = data[end + 1:end + 1 + self.size].hex()
                    at = end + 1 + self.size
                    if mode == b'40000':
                        entries[name] = (True, key)
                    elif mode in (b'100644', b'100755'):
                        entries[name] = (False, key)
            self.trees[hexed] = entries
        return self.trees[hexed]

    def lines(self, hexed):
        """Counter of counted lines of a text file, or None (binary, too large, unreadable, over budget)."""
        checkpoint()
        if hexed not in self.files:
            value = None
            if self.spent < MAX_BYTES:
                found = self.store._object(bytes.fromhex(hexed))
                checkpoint()
                if found and found[0] == 3 and len(found[1]) < MAX_OBJECT and b'\0' not in found[1][:_TEXT_PROBE]:
                    if self.spent + len(found[1]) > MAX_BYTES:
                        self.limited = True
                        self.files[hexed] = None
                        return None
                    self.spent += len(found[1])
                    value = Counter()
                    for raw in found[1].decode('utf-8', 'replace').splitlines():
                        checkpoint()
                        line = raw.strip()
                        if any(char.isalnum() for char in line):
                            value[line] += 1
            else:
                self.limited = True
            self.files[hexed] = value
        return self.files[hexed]

    def changed(self, old, new, prefix=()):
        """(path parts, old file id or None, new file id) for files added or changed between two trees."""
        pending = [(old, new, prefix)]
        while pending:
            checkpoint()
            old, new, path = pending.pop()
            if len(path) > MAX_TREE_DEPTH:
                self.limit()
            before, after = (self.tree(old) if old else {}), self.tree(new)
            if before is None or after is None:
                raise ValueError('unreadable tree')
            for name, (folder, key) in after.items():
                checkpoint()
                if self.visits >= MAX_ENTRIES:
                    self.limit()
                self.visits += 1
                previous = before.get(name)
                if previous and previous[1] == key:
                    continue
                if folder:
                    if len(pending) >= MAX_TREES:
                        self.limit()
                    pending.append((previous[1] if previous and previous[0] else None, key, path + (name,)))
                else:
                    yield path + (name,), previous[1] if previous and not previous[0] else None, key

    def find(self, tree, parts):
        for index, name in enumerate(parts):
            checkpoint()
            entries = self.tree(tree)
            if entries is None or name not in entries:
                return None
            folder, tree = entries[name]
            if folder != (index < len(parts) - 1):
                return None
        return tree


def survival(directory, commits, since=None, store=None):
    """{commit id: dict(added, kept, files, skipped) or None (not measurable)} against the current HEAD.

    A commit outside HEAD's history, a merge, a root commit or an unreadable one gives None. `store` (a Saved)
    keeps the counts across restarts."""
    checkpoint()
    commits = [value for value in dict.fromkeys(commits) if value][:MAX_COMMITS]
    result = dict.fromkeys(commits)
    if not commits:
        return result
    size = len(commits[0]) // 2
    tip = head(directory, size)
    if tip is None:
        return result
    if store is not None:
        saved = store.load()
        if len(_MEMO) + len(saved) > MAX_MEMO:
            _MEMO.clear()
        _MEMO.update(saved)
    keys = {commit: _key(directory, tip, commit) for commit in commits}
    known = {commit: dict(_MEMO[keys[commit]]) for commit in commits if keys[commit] in _MEMO}
    result.update(known)
    commits = [commit for commit in commits if commit not in known]
    if not commits:
        return result
    reader = _Reader(directory, size)
    try:
        if reader.store.base is None:
            return result
        reachable = on_branch(directory, commits, since=since, starts={tip})
        top = reader.commit(tip)
        if top is None:
            return result
        for commit in commits:
            checkpoint()
            if reader.limited:
                break
            if reachable.get(commit) is not True:
                continue
            found = reader.commit(commit)
            if found is None or len(found[1]) != 1:
                continue  # merges and root commits are not one session's own change
            parent = reader.commit(found[1][0])
            if parent is None:
                continue
            added = kept = measured = skipped = 0
            try:
                for index, (parts, old, new) in enumerate(reader.changed(parent[0], found[0])):
                    checkpoint()
                    if index >= MAX_FILES:
                        reader.limit()  # do not invent an exact skipped count from an unvisited tail
                    before = reader.lines(old) if old else Counter()
                    after = reader.lines(new)
                    if before is None or after is None:
                        skipped += 1
                        continue
                    grown = after - before
                    if not grown:
                        continue
                    now_id = reader.find(top[0], parts)
                    now = reader.lines(now_id) if now_id else Counter()
                    if now is None:
                        skipped += 1
                        continue
                    measured += 1
                    added += sum(grown.values())
                    kept += sum(min(count, max(0, now[line] - before[line])) for line, count in grown.items())
            except (ValueError, IndexError):
                continue
            result[commit] = dict(added=added, kept=kept, files=measured, skipped=skipped)
            if not reader.limited and reader.spent < MAX_BYTES:  # partial counts are never remembered
                if len(_MEMO) >= MAX_MEMO:
                    _MEMO.clear()
                _MEMO[keys[commit]] = dict(result[commit])
        if store is not None:
            store.save(_MEMO)
        return result
    except (OSError, ValueError, MemoryError):
        return result
    finally:
        reader.close()
