"""A user's own link or junction to a log folder is followed; links inside it, network targets and loops are not.

People move ~/.claude or ~/.codex to another disk and leave a link behind. Refusing that link showed them an
empty page although their logs were intact."""
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pler import paths
from pler.usage import claude_code, codex, discovery, scan
from pler.usage.records import total
from test_logs import USAGE, claude_reply, codex_rows, write_jsonl

LINK = SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0)
NETWORK = (r'\\example.invalid\share\claude', '//example.invalid/share/claude',
           r'\\?\UNC\example.invalid\share\claude', r'\??\UNC\example.invalid\share',
           r'\\?\Volume{00000000-0000-0000-0000-000000000000}\claude', r'\\.\pipe\invented')


def symlink(target, link):
    os.symlink(str(target), str(link), target_is_directory=True)


def junction(target, link):
    import _winapi
    _winapi.CreateJunction(str(target), str(link))


def makers():
    """The directory links this computer lets a user make: junctions always on Windows, symlinks where allowed."""
    found = []
    with tempfile.TemporaryDirectory() as folder:
        for maker in ((junction, symlink) if os.name == 'nt' else (symlink,)):
            try:
                maker(folder, os.path.join(folder, maker.__name__))
                found.append(maker)
            except (OSError, NotImplementedError):
                pass
    return found


def same(left, right):
    return os.path.realpath(str(left)) == os.path.realpath(str(right))


class LinkedRootTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.makers = makers()
        if not self.makers:
            self.skipTest('this computer cannot make directory links')

    def claude_session(self, projects):
        source = projects / 'shop' / 's1.jsonl'
        write_jsonl(source, [claude_reply('s1', 'm1', 'r1', USAGE, [dict(type='text', text='x')], '2026-10-20T10:00:05Z')])
        return source

    def test_moved_agent_folders_behind_user_links_are_read_end_to_end(self):
        for make in self.makers:
            with self.subTest(link=make.__name__):
                case = self.root / make.__name__
                home = case / 'home'
                home.mkdir(parents=True)
                claude = self.claude_session(case / 'disk' / 'claude' / 'projects')
                rollout = case / 'disk' / 'codex' / 'sessions' / '2026' / '10' / '21' / 'rollout-test.jsonl'
                write_jsonl(rollout, codex_rows())
                make(case / 'disk' / 'claude', home / '.claude')
                make(case / 'disk' / 'codex', home / '.codex')
                with patch.dict(os.environ, PLER_CACHE_DIR=str(case / 'cache')), \
                        patch.object(Path, 'home', return_value=home):
                    for variable in ('CLAUDE_CONFIG_DIR', 'CODEX_HOME'):
                        os.environ.pop(variable, None)
                    sessions, sources = scan()
                    found = claude_code.files() + codex.files()
                self.assertEqual(sources['skipped'], [])
                self.assertEqual((sources['claude_files'], sources['codex_files']), (1, 1))
                self.assertEqual(sorted(s.agent for s in sessions), ['claude-code', 'codex'])
                self.assertTrue(all(total(s.tokens) > 0 for s in sessions))
                # The files are reported where they really are, never through the link.
                self.assertTrue(same(found[0], claude) and same(found[1], rollout))
                self.assertFalse(any(part in ('.claude', '.codex') for path in found for part in path.parts))

    def test_linked_projects_or_sessions_folder_and_configured_folder(self):
        for make in self.makers:
            with self.subTest(link=make.__name__):
                case = self.root / make.__name__
                config = case / 'config'
                config.mkdir(parents=True)
                source = self.claude_session(case / 'elsewhere')
                make(case / 'elsewhere', config / 'projects')
                rollout = case / 'codex-real' / 'sessions' / 'rollout-test.jsonl'
                write_jsonl(rollout, codex_rows())
                make(case / 'codex-real', case / 'codex-link')
                issues = []
                with patch.dict(os.environ, CLAUDE_CONFIG_DIR=str(config), CODEX_HOME=str(case / 'codex-link')):
                    claude_files, codex_files = claude_code.files(skipped=issues), codex.files(skipped=issues)
                self.assertEqual(issues, [])
                self.assertEqual(len(claude_files), 1)
                self.assertTrue(same(claude_files[0], source))
                self.assertEqual(len(codex_files), 1)
                self.assertTrue(same(codex_files[0], rollout))
                sessions, read_issues = codex.read(codex_files)
                expected, _ = codex.read([rollout])
                self.assertEqual(read_issues, [])
                self.assertEqual([s.as_dict() for s in sessions], [s.as_dict() for s in expected])

    def test_links_inside_a_log_folder_are_still_not_followed(self):
        for make in self.makers:
            with self.subTest(link=make.__name__):
                case = self.root / make.__name__
                projects = case / 'config' / 'projects'
                self.claude_session(projects)
                outside = case / 'outside'
                write_jsonl(outside / 'other.jsonl', [dict(type='user')])
                make(outside, projects / 'other')
                issues = []
                with patch.dict(os.environ, CLAUDE_CONFIG_DIR=str(case / 'config')):
                    found = claude_code.files(skipped=issues)
                self.assertEqual([path.name for path in found], ['s1.jsonl'])
                self.assertEqual([(Path(path).name, reason) for path, reason in issues], [('other', 'UnsafePath')])


class LinkTargetTests(unittest.TestCase):
    """Simulated links: the network, loop and reparse cases must never depend on a real share or privilege."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(os.path.realpath(self.temp.name))
        self.link = self.root / 'claude'
        self.link.mkdir()

    def pretend(self, readlink, info=LINK):
        real = Path.lstat
        def guarded(path, *args, **kwargs):
            if paths.network(str(path)):
                raise AssertionError('network probe')
            return info if path == self.link else real(path, *args, **kwargs)
        return patch.object(Path, 'lstat', guarded), patch.object(os, 'readlink', side_effect=readlink)

    def test_link_to_a_network_volume_or_device_is_refused_before_it_is_touched(self):
        for target in NETWORK:
            with self.subTest(target=target):
                lstat, readlink = self.pretend(lambda _, target=target: target)
                issues = []
                with lstat, readlink:
                    self.assertIsNone(paths.user_folder(self.link / 'projects'))
                    self.assertEqual(discovery.folders([self.link], ('projects',), issues), [])
                self.assertEqual([reason for _, reason in issues], ['UnsafePath'])

    def test_link_loop_stops_after_the_bound(self):
        calls = []
        def readlink(path):
            calls.append(path)
            return str(self.link)
        lstat, readlink = self.pretend(readlink)
        with lstat, readlink:
            self.assertIsNone(paths.user_folder(self.link))
        self.assertEqual(len(calls), paths.MAX_LINKS)

    def test_other_reparse_points_stay_refused(self):
        # A Windows reparse point that is not a link (cloud placeholder, deduplicated folder): readlink fails.
        info = SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
        lstat, readlink = self.pretend(OSError('not a link'), info)
        with lstat, readlink:
            self.assertIsNone(paths.user_folder(self.link / 'projects'))

    def test_relative_and_extended_targets_resolve_to_the_real_folder(self):
        real = self.root / 'disk' / 'claude'
        (real / 'projects').mkdir(parents=True)
        for target in (os.path.join('disk', 'claude'), str(real)) + ((r'\\?' + '\\' + str(real),) if os.name == 'nt' else ()):
            with self.subTest(target=target):
                lstat, readlink = self.pretend(lambda _, target=target: target)
                with lstat, readlink:
                    self.assertEqual(paths.user_folder(self.link / 'projects'), real / 'projects')

    def test_target_spellings(self):
        self.assertEqual(paths._target(r'\\?\C:\data\claude'), r'C:\data\claude')
        self.assertEqual(paths._target(r'\??\D:\claude'), r'D:\claude')
        for local in ('relative', os.path.join('..', 'claude'), '/home/user/claude', r'C:\data'):
            self.assertEqual(paths._target(local), local)
        for remote in NETWORK:
            self.assertIsNone(paths._target(remote))

    def test_missing_and_unlinked_folders_are_unchanged(self):
        self.assertEqual(paths.user_folder(self.root / 'missing' / 'projects'), self.root / 'missing' / 'projects')
        self.assertEqual(paths.user_folder(self.link), self.link)
        for remote in NETWORK[:3]:
            self.assertIsNone(paths.user_folder(remote))


if __name__ == '__main__':
    unittest.main()
