"""Is a session's commit still on a branch? Real Git object formats, invented history, no git process.

Loose objects and version-2 packs (with offset and reference deltas) are written here byte by byte.
Author, committer and message carry a secret that must never reach any output.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib

from pler import git_objects
from pler.dashboard import UsageDashboard
from pler.git_activity import check_branches, read_repository, session_activity
from pler.git_survival import Saved
from pler.git_objects import Objects, on_branch
from pler.usage.records import Session

SECRET = 'PRIVATE-AUTHOR-AND-MESSAGE'
NOW = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
TREE = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'


class Store:
    """Writes commits into a synthetic .git directory."""

    def __init__(self, git, algorithm='sha1'):
        self.git, self.algorithm = git, algorithm
        (git / 'objects').mkdir(parents=True)
        (git / 'refs' / 'heads').mkdir(parents=True)
        (git / 'HEAD').write_text('ref: refs/heads/main\n', 'ascii')
        self.raw = {}

    def commit(self, parents=(), seconds=0):
        tree = TREE if self.algorithm == 'sha1' else TREE + '0' * 24
        when = int(NOW.timestamp()) + seconds
        body = ('tree %s\n' % tree + ''.join('parent %s\n' % p for p in parents)
                + 'author %s <secret@example.invalid> %d +0000\n' % (SECRET, when)
                + 'committer %s <secret@example.invalid> %d +0000\n\n%s %d\n' % (SECRET, when, SECRET, seconds)).encode()
        raw = b'commit %d\0' % len(body) + body
        key = hashlib.new(self.algorithm, raw).hexdigest()
        self.raw[key] = body
        return key

    def loose(self, *keys):
        for key in keys:
            body = self.raw[key]
            folder = self.git / 'objects' / key[:2]
            folder.mkdir(exist_ok=True)
            (folder / key[2:]).write_bytes(zlib.compress(b'commit %d\0' % len(body) + body))

    def ref(self, name, key):
        path = self.git / 'refs' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(key + '\n', 'ascii')

    def pack(self, keys, deltas=()):
        """A version-2 pack and index; keys in `deltas` are stored as (offset or reference) deltas."""
        out, offsets, previous = bytearray(b'PACK' + struct.pack('>II', 2, len(keys))), {}, None
        for index, key in enumerate(keys):
            body, offsets[key] = self.raw[key], len(out)
            if key in deltas and previous is not None:
                data = _delta(self.raw[previous], body)
                if index % 2:  # offset delta
                    out += _header(6, len(data)) + _distance(offsets[key] - offsets[previous])
                else:          # reference delta
                    out += _header(7, len(data)) + bytes.fromhex(previous)
                out += zlib.compress(data)
            else:
                out += _header(1, len(body)) + zlib.compress(body)
            previous = key
        out += hashlib.new(self.algorithm, bytes(out)).digest()
        (self.git / 'objects' / 'pack').mkdir(exist_ok=True)
        (self.git / 'objects' / 'pack' / 'pack-test.pack').write_bytes(bytes(out))
        names = sorted(keys)
        fanout = [sum(1 for k in names if int(k[:2], 16) <= byte) for byte in range(256)]
        index = (b'\xfftOc' + struct.pack('>I', 2) + b''.join(struct.pack('>I', n) for n in fanout)
                 + b''.join(bytes.fromhex(k) for k in names) + b'\0\0\0\0' * len(names)
                 + b''.join(struct.pack('>I', offsets[k]) for k in names))
        (self.git / 'objects' / 'pack' / 'pack-test.idx').write_bytes(index)


def _header(kind, size):
    first, size = (kind << 4) | (size & 15), size >> 4
    out = bytearray()
    while size:
        out.append(first | 0x80)
        first, size = size & 0x7f, size >> 7
    out.append(first)
    return bytes(out)


def _distance(value):
    out = [value & 0x7f]
    value >>= 7
    while value:
        value -= 1
        out.insert(0, 0x80 | (value & 0x7f))
        value >>= 7
    return bytes(out)


def _varint(value):
    out = bytearray()
    while True:
        byte, value = value & 0x7f, value >> 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(out)


def _delta(base, target):
    common = 0
    while common < min(len(base), len(target), 0xffff) and base[common] == target[common]:
        common += 1
    out = bytearray(_varint(len(base)) + _varint(len(target)))
    if common:
        out += bytes([0x80 | 0x10 | 0x20, common & 0xff, common >> 8])
    rest = target[common:]
    for at in range(0, len(rest), 127):
        out += bytes([len(rest[at:at + 127])]) + rest[at:at + 127]
    return bytes(out)


class OnBranchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.git = Path(self.temp.name) / 'repo' / '.git'
        self.store = Store(self.git)
        s = self.store
        self.first = s.commit(seconds=-300)
        self.second = s.commit([self.first], -200)
        self.third = s.commit([self.second], -100)
        self.amended = s.commit([self.second], -150)          # replaced by `third`, kept by no branch
        self.side = s.commit([self.second], -120)             # on a branch that was deleted
        self.everything = [self.first, self.second, self.third, self.amended, self.side]

    def answer(self, since=None):
        return on_branch(self.git, [self.third, self.second, self.amended, self.side], since)

    def expected(self, **changes):
        value = {self.third: True, self.second: True, self.amended: False, self.side: False}
        value.update(changes)
        return value

    def test_loose_objects(self):
        self.store.loose(*self.everything)
        self.store.ref('heads/main', self.third)
        self.assertEqual(self.answer(), self.expected())
        self.assertEqual(self.answer(since=NOW.timestamp() - 300), self.expected())

    def test_pack_with_offset_and_reference_deltas(self):
        self.store.pack(self.everything, deltas={self.second, self.third, self.amended, self.side})
        self.store.ref('heads/main', self.third)
        objects = Objects(self.git, 20)
        try:
            for key in self.everything:
                self.assertIsNotNone(objects.commit(key), 'delta entry not resolved')
            self.assertEqual(objects.commit(self.third)[1], [self.second])
        finally:
            objects.close()
        self.assertEqual(self.answer(), self.expected())

    def test_remote_tracking_packed_and_detached_tips_keep_commits(self):
        self.store.loose(*self.everything)
        self.store.ref('heads/main', self.third)
        self.store.ref('remotes/origin/feature', self.side)
        self.assertEqual(self.answer(), self.expected(**{self.side: True}))
        (self.git / 'refs' / 'remotes' / 'origin' / 'feature').unlink()
        (self.git / 'packed-refs').write_text('# pack-refs with: peeled\n%s refs/heads/old\n^%s\n' % (self.amended, TREE), 'ascii')
        self.assertEqual(self.answer(), self.expected(**{self.amended: True}))
        (self.git / 'packed-refs').unlink()
        (self.git / 'HEAD').write_text(self.side + '\n', 'ascii')
        self.assertEqual(self.answer(), self.expected(**{self.side: True}))

    def test_missing_history_alternates_and_links_are_unknown_not_dropped(self):
        self.store.loose(self.second, self.third, self.amended, self.side)   # first is missing (shallow)
        self.store.ref('heads/main', self.third)
        self.assertEqual(self.answer(), self.expected(**{self.amended: None, self.side: None}))
        self.store.loose(self.first)
        (self.git / 'objects' / 'info').mkdir()
        (self.git / 'objects' / 'info' / 'alternates').write_text('/elsewhere/objects\n', 'ascii')
        self.assertEqual(set(self.answer().values()), {None})
        (self.git / 'objects' / 'info' / 'alternates').unlink()
        with patch.object(git_objects, 'local_path', lambda value: None if 'objects' in str(value) else Path(value)):
            self.assertEqual(set(self.answer().values()), {None})

    def test_a_known_answer_is_reused_for_the_same_tips_and_an_unknown_one_is_walked_again(self):
        self.store.loose(self.second, self.third, self.amended, self.side)   # first is missing
        self.store.ref('heads/main', self.third)
        original, calls = Objects.commit, []
        def counted(store, key):
            calls.append(key)
            return original(store, key)
        with patch.object(Objects, 'commit', counted):
            self.assertEqual(self.answer(), self.expected(**{self.amended: None, self.side: None}))
            once = len(calls)
            self.answer()
            self.assertEqual(len(calls), 2 * once)
            self.store.loose(self.first)  # the missing object arrives
            value = self.answer()
            self.assertEqual(value, self.expected())
            walked = len(calls)
            value[self.third] = 'changed by the caller'
            self.assertEqual(self.answer(), self.expected())
            self.assertEqual(len(calls), walked)
            self.store.ref('heads/main', self.side)   # a moved tip is a new walk
            self.assertEqual(self.answer(), self.expected(**{self.third: False, self.side: True}))
            self.assertGreater(len(calls), walked)

    def test_walk_bound_leaves_unmet_targets_unknown(self):
        self.store.loose(*self.everything)
        self.store.ref('heads/main', self.third)
        with patch.object(git_objects, 'MAX_COMMITS', 2):
            value = on_branch(self.git, [self.third, self.amended])
        self.assertEqual(value, {self.third: True, self.amended: None})

    def test_linked_worktree_reads_objects_and_branches_from_the_common_directory(self):
        self.store.loose(*self.everything)
        self.store.ref('heads/main', self.third)
        worktree = self.git / 'worktrees' / 'second'
        worktree.mkdir(parents=True)
        (worktree / 'HEAD').write_text(self.side + '\n', 'ascii')
        (worktree / 'commondir').write_text('../..\n', 'ascii')
        self.assertEqual(on_branch(worktree, [self.third, self.side, self.amended]),
                         {self.third: True, self.side: True, self.amended: False})

    def test_sha256_repositories(self):
        git = Path(self.temp.name) / 'sha256' / '.git'
        store = Store(git, 'sha256')
        base = store.commit()
        kept = store.commit([base], 10)
        lost = store.commit([base], 20)
        store.loose(base, kept, lost)
        store.ref('heads/main', kept)
        self.assertEqual(len(kept), 64)
        self.assertEqual(on_branch(git, [kept, lost]), {kept: True, lost: False})

    def test_only_parents_and_time_leave_the_object(self):
        self.store.loose(*self.everything)
        objects = Objects(self.git, 20)
        try:
            value = objects.commit(self.third)
        finally:
            objects.close()
        self.assertEqual(value, (int(NOW.timestamp()) - 100, [self.second]))
        self.assertNotIn(SECRET, repr(value))


def reflog(*entries):
    lines = []
    for seconds, action, key in entries:
        lines.append('%s %s %s <secret@example.invalid> %d +0000\t%s: %s\n'
                     % ('0' * 40, key, SECRET, int(NOW.timestamp()) + seconds, action, SECRET))
    return ''.join(lines).encode()


class SessionOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.git = self.root / '.git'
        s = self.store = Store(self.git)
        self.base = s.commit(seconds=-3600)
        self.kept = s.commit([self.base], -60)
        self.lost = s.commit([self.base], -30)             # amended away below
        self.final = s.commit([self.kept], 30)
        s.loose(self.base, self.kept, self.lost, self.final)
        s.ref('heads/main', self.final)
        (self.git / 'logs').mkdir()
        (self.git / 'logs' / 'HEAD').write_bytes(reflog((-3600, 'commit (initial)', self.base), (-60, 'commit', self.kept),
                                                        (-30, 'commit', self.lost), (30, 'commit (amend)', self.final),
                                                        (40, 'checkout', self.final)))

    def session(self, name, start, end, tokens=100):
        value = Session('claude-code', name, 'source-' + name, project=str(self.root),
                        started=NOW + timedelta(seconds=start), ended=NOW + timedelta(seconds=end))
        value.tokens['input'] = tokens
        value.files_edited = {str(self.root / 'src' / 'main.py')}
        return value

    def test_session_projection_counts_commits_still_on_a_branch(self):
        snapshot = read_repository(str(self.root))
        check_branches(snapshot, [(NOW - timedelta(minutes=5), NOW + timedelta(minutes=5))])
        value = session_activity(snapshot, NOW - timedelta(minutes=5), NOW + timedelta(minutes=5))
        self.assertEqual(value['commits'], dict(total=3, on_branch=2, off_branch=1, unknown=0))
        marks = {event['commit']: event.get('on_branch') for event in value['events']}
        self.assertEqual((marks[self.kept[:8]], marks[self.lost[:8]], marks[self.final[:8]]), (True, False, True))
        self.assertNotIn('on_branch', [e for e in value['events'] if e['kind'] == 'checkout'][0])
        encoded = json.dumps(value)
        for private in (SECRET, 'secret@example.invalid', self.kept, self.lost, str(self.root)):
            self.assertNotIn(private, encoded)

    def test_unchecked_commits_are_unknown(self):
        value = session_activity(read_repository(str(self.root)), NOW - timedelta(minutes=5), NOW + timedelta(minutes=5))
        self.assertEqual(value['commits'], dict(total=3, on_branch=0, off_branch=0, unknown=3))

    def test_dashboard_summary_counts_each_commit_once_and_says_so_in_both_languages(self):
        early, late = self.session('a', -120, 0), self.session('b', -45, 120)  # overlap at `lost`
        dashboard = UsageDashboard(reader=lambda: ([early, late], dict(claude_files=1, codex_files=0, skipped=[])),
                                   survival=Saved(self.root.parent / 'counts'))
        dashboard.refresh()
        dashboard.thread.join(10)
        value = dashboard.view(days=0)
        # These invented commits name a tree that is not written, so their lines cannot be measured.
        self.assertEqual(value['git_outcome'], dict(sessions=2, commits=3, on_branch=2, off_branch=1, unknown=0,
                                                    token_share=1.0,
                                                    lines=dict(added=0, kept=0, commits=0, unmeasured=2)))
        card = [item for item in value['insights'] if item['kind'] == 'git_outcome'][0]
        self.assertIn('2 sessions', card['detail'])
        self.assertIn('3 commits', card['detail'])
        self.assertIn('100%', card['detail'])
        turkish = [item for item in dashboard.view(days=0, lang='tr')['insights'] if item['kind'] == 'git_outcome'][0]
        self.assertIn('2 oturum', turkish['detail'])
        encoded = json.dumps(value)
        for private in (SECRET, 'secret@example.invalid', self.kept, self.lost, str(self.root)):
            self.assertNotIn(private, encoded)


if __name__ == '__main__':
    unittest.main()
