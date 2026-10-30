"""Are the lines a session's commits added still in place? A bounded, read-only look at Git trees and files.

For a commit made during a session that is still in the current HEAD's history, its added lines are the
lines whose count in a file grew compared with its first parent. Each is looked for, by content, in the
same file at HEAD. Blank lines and lines without a letter or digit (a lone `}`) are not counted.

File names and contents are read only in memory, through git_objects.py; only counts leave this module.
No Git program runs and nothing is written. Merge commits, renamed or moved files, binary or very large
files and anything unreadable are left out and counted as such, never guessed. Matching by content is an
approximation: a line moved within its file still counts as kept, a line rewritten in place does not.
"""
from collections import Counter
from pathlib import Path

from .git_objects import MAX_OBJECT, Objects, _common, _hex, _read, on_branch

MAX_COMMITS = 200        # commits measured per repository and scan
MAX_FILES = 400          # changed files measured per commit
MAX_BYTES = 256 << 20    # file contents inflated per repository and scan
MAX_MEMO = 20000
_TEXT_PROBE = 8000
# Counts only, for (repository, HEAD, commit): objects named by their ids never change, so a later read of
# the same HEAD in this process reuses the counts instead of reading the files again.
_MEMO = {}


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

    def close(self):
        self.store.close()

    def commit(self, hexed):
        """(tree id, [parent ids]) from a commit header; identities and the message are never read."""
        found = self.store._object(bytes.fromhex(hexed))
        if not found or found[0] != 1:
            return None
        tree, parents = None, []
        for line in found[1].split(b'\n'):
            if not line:
                break
            if line.startswith(b'tree '):
                tree = _hex(line[5:].decode('ascii', 'replace'), self.size)
            elif line.startswith(b'parent '):
                parents.append(_hex(line[7:].decode('ascii', 'replace'), self.size))
        return (tree, parents) if tree and None not in parents else None

    def tree(self, hexed):
        """{name: (is_tree, id)} for regular files and folders; links and submodules are skipped."""
        if hexed not in self.trees:
            found = self.store._object(bytes.fromhex(hexed))
            entries = None
            if found and found[0] == 2:
                entries, data, at = {}, found[1], 0
                while at < len(data):
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
        if hexed not in self.files:
            value = None
            if self.spent < MAX_BYTES:
                found = self.store._object(bytes.fromhex(hexed))
                if found and found[0] == 3 and len(found[1]) < MAX_OBJECT and b'\0' not in found[1][:_TEXT_PROBE]:
                    self.spent += len(found[1])
                    value = Counter(line for line in (raw.strip() for raw in found[1].decode('utf-8', 'replace').splitlines())
                                    if any(char.isalnum() for char in line))
            self.files[hexed] = value
        return self.files[hexed]

    def changed(self, old, new, prefix=()):
        """(path parts, old file id or None, new file id) for files added or changed between two trees."""
        before, after = (self.tree(old) if old else {}), self.tree(new)
        if before is None or after is None:
            raise ValueError('unreadable tree')
        for name, (folder, key) in after.items():
            previous = before.get(name)
            if previous and previous[1] == key:
                continue
            if folder:
                yield from self.changed(previous[1] if previous and previous[0] else None, key, prefix + (name,))
            else:
                yield prefix + (name,), previous[1] if previous and not previous[0] else None, key

    def find(self, tree, parts):
        for index, name in enumerate(parts):
            entries = self.tree(tree)
            if entries is None or name not in entries:
                return None
            folder, tree = entries[name]
            if folder != (index < len(parts) - 1):
                return None
        return tree


def survival(directory, commits, since=None):
    """{commit id: dict(added, kept, files, skipped) or None (not measurable)} against the current HEAD.

    A commit outside HEAD's history, a merge, a root commit or an unreadable one gives None."""
    commits = [value for value in dict.fromkeys(commits) if value][:MAX_COMMITS]
    result = dict.fromkeys(commits)
    if not commits:
        return result
    size = len(commits[0]) // 2
    tip = head(directory, size)
    if tip is None:
        return result
    known = {commit: _MEMO[(str(directory), tip, commit)] for commit in commits if (str(directory), tip, commit) in _MEMO}
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
            if reachable.get(commit) is not True:
                continue
            found = reader.commit(commit)
            if found is None or len(found[1]) != 1:
                continue  # merges and root commits are not one session's own change
            parent = reader.commit(found[1][0])
            if parent is None:
                continue
            try:
                files = list(reader.changed(parent[0], found[0]))
            except (ValueError, IndexError):
                continue
            added = kept = measured = skipped = 0
            for parts, old, new in files[:MAX_FILES]:
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
            skipped += max(0, len(files) - MAX_FILES)
            result[commit] = dict(added=added, kept=kept, files=measured, skipped=skipped)
            if reader.spent < MAX_BYTES:  # a count cut short by the byte budget is not remembered
                if len(_MEMO) >= MAX_MEMO:
                    _MEMO.clear()
                _MEMO[(str(directory), tip, commit)] = result[commit]
        return result
    except (OSError, ValueError, MemoryError):
        return result
    finally:
        reader.close()
