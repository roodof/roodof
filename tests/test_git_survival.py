"""Do a session's committed lines survive to HEAD? Invented repositories written byte by byte; no git process.

File names and contents carry a secret that must never reach any output: only counts may leave.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import unittest.mock
import zlib

from pler.git_activity import check_branches, check_survival, read_repository, session_activity
from pler import git_survival
from pler.git_survival import head, survival

SECRET = 'PRIVATE-FILE-CONTENT'
NOW = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)


class Repo:
    """Loose blobs, trees and commits in an invented .git folder, plus a HEAD reflog."""

    def __init__(self, root):
        self.git = root / '.git'
        (self.git / 'objects').mkdir(parents=True)
        (self.git / 'refs' / 'heads').mkdir(parents=True)
        (self.git / 'logs').mkdir()
        (self.git / 'HEAD').write_text('ref: refs/heads/main\n', 'ascii')
        self.reflog = []

    def put(self, kind, body):
        raw = kind + b' %d\0' % len(body) + body
        key = hashlib.sha1(raw).hexdigest()
        folder = self.git / 'objects' / key[:2]
        folder.mkdir(exist_ok=True)
        (folder / key[2:]).write_bytes(zlib.compress(raw))
        return key

    def tree(self, files):
        """files: {'a/b.py': bytes}; folders become nested trees."""
        entries, folders = [], {}
        for name, value in files.items():
            first, _, rest = name.partition('/')
            if rest:
                folders.setdefault(first, {})[rest] = value
            else:
                entries.append((b'100644', first.encode(), self.put(b'blob', value)))
        for name, inner in folders.items():
            entries.append((b'40000', name.encode(), self.tree(inner)))
        entries.sort(key=lambda entry: entry[1] + (b'/' if entry[0] == b'40000' else b''))
        return self.put(b'tree', b''.join(mode + b' ' + name + b'\0' + bytes.fromhex(key) for mode, name, key in entries))

    def commit(self, files, parents=(), minutes=0, branch='main', kind='commit'):
        when = int((NOW + timedelta(minutes=minutes)).timestamp())
        body = ('tree %s\n' % self.tree(files) + ''.join('parent %s\n' % p for p in parents)
                + 'author %s <x@example.invalid> %d +0000\ncommitter %s <x@example.invalid> %d +0000\n\n%s\n'
                % (SECRET, when, SECRET, when, SECRET)).encode()
        key = self.put(b'commit', body)
        previous = self.reflog[-1][1] if self.reflog else '0' * 40
        self.reflog.append((previous, key, when, kind))
        (self.git / 'refs' / 'heads' / branch).write_text(key + '\n', 'ascii')
        return key

    def save(self):
        (self.git / 'logs' / 'HEAD').write_text(''.join(
            '%s %s %s <x@example.invalid> %d +0000\t%s: %s\n' % (a, b, SECRET, when, kind, SECRET)
            for a, b, when, kind in self.reflog), 'utf-8')


def text(*lines):
    return ('\n'.join(lines) + '\n').encode()


class SurvivalTests(unittest.TestCase):
    def setUp(self):
        git_survival._MEMO.clear()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'shop'
        self.repo = Repo(self.root)
        self.base = {'src/app.py': text('def total(cart):', '    return sum(cart)', '}'), 'README.md': text('Invented shop')}
        self.first = self.repo.commit(self.base)

    def test_added_lines_are_matched_at_head_and_trivial_binary_lines_are_left_out(self):
        session = self.repo.commit(dict(self.base, **{
            'src/app.py': text('def total(cart):', '    return sum(cart)', '}', '', 'def tax(value):', '    rate = 0.2',
                               '    return value * rate', '}', '# ' + SECRET),
            'src/new.py': text('VALUE = 1', 'OTHER = 2'),
            'logo.bin': b'\x89PNG\0' + SECRET.encode()}), [self.first], minutes=10)
        later = self.repo.commit(dict(self.base, **{
            'src/app.py': text('def total(cart):', '    return sum(cart)', '}', 'def tax(value):', '    return value * 0.2', '}'),
            'src/new.py': text('VALUE = 1', 'OTHER = 2'), 'logo.bin': b'\x89PNG\0'}), [session], minutes=60)
        self.assertEqual(head(self.repo.git, 20), later)
        value = survival(self.repo.git, [session])[session]
        # Added: tax def, rate, return, the secret comment (4 in app.py) and two in new.py. Kept: def, two new.py lines.
        self.assertEqual(value, dict(added=6, kept=3, files=2, skipped=1))
        self.assertNotIn(SECRET, json.dumps(value))

    def test_repeated_lines_count_only_the_copies_a_commit_added(self):
        session = self.repo.commit(dict(self.base, **{'src/app.py': text(
            'def total(cart):', '    return sum(cart)', '}', 'def other(cart):', '    return sum(cart)')}), [self.first], minutes=5)
        self.assertEqual(survival(self.repo.git, [session])[session], dict(added=2, kept=2, files=1, skipped=0))
        later = self.repo.commit(self.base, [session], minutes=30)  # the copy is removed again
        self.assertEqual(survival(self.repo.git, [session])[session], dict(added=2, kept=0, files=1, skipped=0))
        self.assertTrue(later)

    def test_a_moved_file_does_not_count_as_kept(self):
        session = self.repo.commit(dict(self.base, **{'src/new.py': text('VALUE = 1')}), [self.first], minutes=5)
        self.repo.commit(dict(self.base, **{'lib/new.py': text('VALUE = 1')}), [session], minutes=30)
        self.assertEqual(survival(self.repo.git, [session])[session], dict(added=1, kept=0, files=1, skipped=0))

    def test_merges_roots_other_branches_and_unreadable_commits_are_not_measured(self):
        side = self.repo.commit(dict(self.base, **{'side.py': text('SIDE = 1')}), [self.first], minutes=5, branch='side')
        main = self.repo.commit(dict(self.base, **{'main.py': text('MAIN = 1')}), [self.first], minutes=6)
        merge = self.repo.commit(dict(self.base, **{'main.py': text('MAIN = 1'), 'side.py': text('SIDE = 1')}),
                                 [main, side], minutes=7)
        other = self.repo.commit(dict(self.base, **{'other.py': text('OTHER = 1')}), [side], minutes=8, branch='side')
        value = survival(self.repo.git, [self.first, main, merge, other, 'f' * 40])
        self.assertEqual(value, {self.first: None, main: dict(added=1, kept=1, files=1, skipped=0), merge: None,
                                 other: None, 'f' * 40: None})

    def test_detached_and_packed_head_references(self):
        session = self.repo.commit(dict(self.base, **{'a.py': text('A = 1')}), [self.first], minutes=5)
        (self.repo.git / 'refs' / 'heads' / 'main').unlink()
        (self.repo.git / 'packed-refs').write_text('# pack-refs with: peeled\n%s refs/heads/main\n' % session, 'ascii')
        self.assertEqual(head(self.repo.git, 20), session)
        (self.repo.git / 'HEAD').write_text(self.first + '\n', 'ascii')
        self.assertEqual(head(self.repo.git, 20), self.first)
        self.assertIsNone(survival(self.repo.git, [session])[session])  # no longer in HEAD's history
        (self.repo.git / 'HEAD').write_text('ref: refs/heads/../../escape\n', 'ascii')
        self.assertIsNone(head(self.repo.git, 20))

    def test_session_projection_and_outcome_carry_only_counts(self):
        session = self.repo.commit(dict(self.base, **{'a.py': text('A = 1', 'B = 2')}), [self.first], minutes=5)
        self.repo.commit(dict(self.base, **{'a.py': text('A = 1')}), [session], minutes=50)
        self.repo.save()
        snapshot = read_repository(str(self.root))
        window = (NOW + timedelta(minutes=1), NOW + timedelta(minutes=20))
        check_branches(snapshot, [window])
        check_survival(snapshot)
        activity = session_activity(snapshot, *window)
        self.assertEqual(activity['lines'], dict(added=2, kept=1, commits=1, unmeasured=0))
        self.assertNotIn(SECRET, json.dumps(activity))
        self.assertNotIn('a.py', json.dumps(activity))


    def test_counts_for_the_same_head_are_reused_and_a_new_head_is_measured_again(self):
        session = self.repo.commit(dict(self.base, **{'a.py': text('A = 1')}), [self.first], minutes=5)
        self.assertEqual(survival(self.repo.git, [session])[session]['kept'], 1)
        with unittest.mock.patch.object(git_survival._Reader, 'lines', side_effect=AssertionError('read again')):
            self.assertEqual(survival(self.repo.git, [session])[session]['kept'], 1)
        self.repo.commit(self.base, [session], minutes=30)
        self.assertEqual(survival(self.repo.git, [session])[session]['kept'], 0)


class SavedCountTests(unittest.TestCase):
    def setUp(self):
        SurvivalTests.setUp(self)
        self.cache = self.root.parent / 'cache'
        self.saved = self.cache / git_survival.Saved.FILENAME
        self.session = self.repo.commit(dict(self.base, **{'a.py': text('A = 1', 'B = 2')}), [self.first], minutes=5)

    def restart(self):
        """A new process: the in-memory counts are gone."""
        git_survival._MEMO.clear()
        return git_survival.Saved(self.cache)

    def test_counts_survive_a_restart_and_the_file_names_nothing(self):
        first = survival(self.repo.git, [self.session], store=git_survival.Saved(self.cache))
        self.assertEqual(first[self.session]['added'], 2)
        stored = self.saved.read_text('utf-8')
        for private in (self.session, self.first, str(self.repo.git), str(self.root), SECRET, 'a.py', 'A = 1'):
            self.assertNotIn(private, stored)
        value = json.loads(stored)
        self.assertEqual(sorted(value), ['counts', 'format', 'version'])
        self.assertEqual(list(value['counts'].values()), [[2, 2, 1, 0]])
        with unittest.mock.patch.object(git_survival._Reader, 'lines', side_effect=AssertionError('read again')):
            self.assertEqual(survival(self.repo.git, [self.session], store=self.restart()), first)

    def test_damaged_foreign_or_cut_short_counts_are_never_reused(self):
        survival(self.repo.git, [self.session], store=git_survival.Saved(self.cache))
        value = json.loads(self.saved.read_text('utf-8'))
        damaged = (json.dumps(dict(value, version='0' * 16)), 'not json',
                   json.dumps(dict(value, counts={key: [2, -1, 1, 0] for key in value['counts']})),
                   json.dumps(dict(value, counts={key: [2, '2', 1, 0] for key in value['counts']})))
        original, reads = git_survival._Reader.lines, []
        def counted(reader, key):
            reads.append(key)
            return original(reader, key)
        for text_value in damaged:
            with self.subTest(saved=text_value[:40]):
                self.saved.write_text(text_value, 'utf-8')
                reads.clear()
                with unittest.mock.patch.object(git_survival._Reader, 'lines', counted):
                    self.assertEqual(survival(self.repo.git, [self.session], store=self.restart())[self.session]['kept'], 2)
                self.assertTrue(reads)
        self.saved.unlink()
        with unittest.mock.patch.object(git_survival, 'MAX_BYTES', 1):
            survival(self.repo.git, [self.session], store=self.restart())
        self.assertEqual(json.loads(self.saved.read_text('utf-8'))['counts'], {})

    def test_cache_reset_removes_the_counts_and_the_page_keeps_them_by_default(self):
        from pler.dashboard import UsageDashboard
        from pler.usage import archive
        survival(self.repo.git, [self.session], store=git_survival.Saved(self.cache))
        with unittest.mock.patch.dict('os.environ', PLER_CACHE_DIR=str(self.cache)):
            self.assertEqual(archive.reset_cache()['cleared_files'], 1)
            self.assertFalse(self.saved.exists())
            store = UsageDashboard(lambda: ([], {})).survival_store
        self.assertIsInstance(store, git_survival.Saved)
        self.assertIsNone(store.base)


if __name__ == '__main__':
    unittest.main()
