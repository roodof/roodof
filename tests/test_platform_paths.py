"""macOS/Linux system links are usable; user links, junctions and network spellings stay refused."""
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pler import paths
from pler.usage import codex
from pler.usage.records import total
from test_logs import codex_rows, write_jsonl


def link(uid):
    return SimpleNamespace(st_mode=stat.S_IFLNK, st_uid=uid, st_file_attributes=0)


class PlatformPathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.linked = self.root / 'var'
        self.target = self.linked / 'folders' / 'cache'

    def run_as(self, system, info):
        """local_path on `system` when one ancestor of the target is the given link."""
        real = Path.lstat
        def guarded(path, *args, **kwargs):
            return info if path == self.linked else real(path, *args, **kwargs)
        fake_os = SimpleNamespace(name=system, path=os.path, environ=os.environ)
        with patch.object(paths, 'os', fake_os), patch.object(Path, 'lstat', guarded):
            return paths.local_path(self.target)

    def test_network_spellings_in_any_slash_mix(self):
        for value in ('//server/share', '\\\\server\\share', '/\\server/share', '\\/server/share',
                      '\\\\?\\UNC\\server\\share', Path('//server/share/project')):
            with self.subTest(value=value):
                self.assertTrue(paths.network(value))
                self.assertIsNone(paths.local_path(value))
        for value in ('/home/user', '\\folder', 'C:\\Users', 'relative', '', '/'):
            with self.subTest(value=value):
                self.assertFalse(paths.network(value))

    def test_root_owned_system_link_ancestor_is_usable_on_posix(self):
        # As on macOS, where TMPDIR and ~/Library live behind /var -> /private/var style links.
        self.assertEqual(self.run_as('posix', link(0)), Path(os.path.abspath(self.target)))

    def test_user_owned_link_ancestor_is_still_refused_on_posix(self):
        self.assertIsNone(self.run_as('posix', link(1000)))
        self.assertIsNone(self.run_as('posix', SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0)))

    def test_windows_never_trusts_a_link_by_owner(self):
        # Windows reports uid 0 for every file, so ownership cannot make a link or junction trusted.
        self.assertIsNone(self.run_as('nt', link(0)))
        junction = SimpleNamespace(st_mode=stat.S_IFDIR, st_uid=0, st_file_attributes=0x400)
        self.assertIsNone(self.run_as('nt', junction))
        self.assertIsNone(self.run_as('posix', junction))

    def test_logs_behind_a_system_link_are_read(self):
        source = self.linked / 'logs' / 'rollout-test.jsonl'
        source.parent.mkdir(parents=True)
        write_jsonl(source, codex_rows())
        expected, _ = codex.read([source])
        real = Path.lstat
        def guarded(path, *args, **kwargs):
            return link(0) if path == self.linked else real(path, *args, **kwargs)
        fake_os = SimpleNamespace(name='posix', path=os.path, environ=os.environ)
        with patch.object(paths, 'os', fake_os), patch.object(Path, 'lstat', guarded):
            found, issues = codex.read([source])
        self.assertEqual(issues, [])
        self.assertEqual([s.as_dict() for s in found], [s.as_dict() for s in expected])
        self.assertGreater(sum(total(s.tokens) for s in found), 0)
        with patch.object(paths, 'os', fake_os), \
                patch.object(Path, 'lstat', lambda path, *a, **k: link(1000) if path == self.linked else real(path, *a, **k)):
            refused, issues = codex.read([source])
        self.assertEqual(refused, [])
        self.assertTrue(issues)


if __name__ == '__main__':
    unittest.main()
