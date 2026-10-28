"""Only explicitly selected, already-running WSL log roots can cross the UNC boundary.

No real share, WSL installation or distro is used. The end-to-end test maps a synthetic WSL namespace to
a temporary folder and asserts that status is checked before any UNC operation.
"""
import builtins
from contextlib import ExitStack
import os
from pathlib import Path, PureWindowsPath
import stat
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pler import paths, wsl
from pler.usage import claude_code, codex, discovery, scan
from pler.usage.records import total
from test_logs import USAGE, claude_reply, codex_rows, write_jsonl

ROOT = r'\\wsl.localhost\Ubuntu\home\invented\.codex'
CLAUDE = r'\\wsl.localhost\Ubuntu\home\invented\.claude'
UNSAFE = (r'\\example.invalid\share\logs', '//example.invalid/share/logs',
          '/\\example.invalid/share', '\\/example.invalid/share',
          r'\\?\UNC\wsl.localhost\Ubuntu\logs', r'\??\UNC\wsl.localhost\Ubuntu\logs',
          r'\\.\pipe\invented', r'\\?\Volume{invented}\logs',
          r'\\wsl.localhost.evil\Ubuntu\logs', r'\\wsl.localhost.\Ubuntu\logs',
          r'\\wsl$@evil\Ubuntu\logs', r'\\wsl.localhost:80\Ubuntu\logs',
          r'\\wsl.localhost\..\logs', r'\\wsl.localhost\Ubuntu\..\Debian\logs',
          r'\\wsl.localhost\Ubuntu\logs:stream', r'\\wsl.localhost\Ubuntu.\logs',
          r'\\wsl.localhost\Ubuntu\logs.\file', r'\\wsl.localhost\Ubuntu\\logs')


class StatusTests(unittest.TestCase):
    def test_status_output_decodes_utf8_and_utf16_without_tolerating_garbage(self):
        value = 'Ubuntu\r\nA distro\r\n'
        for encoding in ('utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le'):
            with self.subTest(encoding=encoding):
                self.assertEqual(wsl._names(value.encode(encoding)), {'ubuntu': 'Ubuntu', 'a distro': 'A distro'})
        self.assertEqual(wsl._names(b''), {})
        for raw in (b'\xff', b'\x00', b'Ubuntu\nubuntu', b'Ubuntu\x00bad', b' ../Ubuntu\n',
                    b'Ubuntu.\n', b'a/b\n', b'Ubuntu\nStarting WSL...\n', b'x' * 65537):
            with self.subTest(raw=raw[:40]):
                self.assertIsNone(wsl._names(raw))

    def test_only_the_absolute_status_program_and_literal_arguments_can_run(self):
        executable = Path(r'C:\Windows\System32\wsl.exe')
        result = SimpleNamespace(returncode=0, stdout=b'Ubuntu\r\n')
        with patch.object(wsl, 'WINDOWS', True), patch.object(wsl, '_executable', return_value=executable), \
                patch.object(wsl.subprocess, 'run', return_value=result) as run:
            self.assertEqual(wsl.running(), {'ubuntu': 'Ubuntu'})
        run.assert_called_once_with([str(executable), '--list', '--running', '--quiet'], shell=False,
                                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                    timeout=3, creationflags=0x08000000)

    def test_executable_does_not_use_path_or_an_unc_os_directory(self):
        with patch.dict(os.environ, SystemRoot=r'C:\Windows', PATH=r'C:\invented'), \
                patch.object(wsl, 'local_path', side_effect=lambda value: Path(value)) as local:
            self.assertEqual(wsl._executable(), Path(r'C:\Windows\System32\wsl.exe'))
        local.assert_called_once_with(r'C:\Windows\System32\wsl.exe')
        for base in ('', 'relative', r'\\example.invalid\Windows', r'\\wsl.localhost\Ubuntu\Windows', 'C:Windows'):
            with self.subTest(base=base), patch.dict(os.environ, SystemRoot=base), \
                    patch.object(wsl, 'local_path', side_effect=AssertionError('unsafe executable probe')):
                self.assertIsNone(wsl._executable())
        with patch.dict(os.environ, SystemRoot=r'C:\Windows'), patch.object(wsl, 'local_path', return_value=None):
            self.assertIsNone(wsl._executable())

    def test_failed_missing_or_timed_out_status_never_authorizes_access(self):
        with patch.object(wsl, 'WINDOWS', True), patch.object(wsl, '_executable', return_value=Path('invented')):
            for failure in (OSError('missing'), subprocess.TimeoutExpired('wsl', 3),
                            SimpleNamespace(returncode=1, stdout=b'Ubuntu\n'),
                            SimpleNamespace(returncode=0, stdout=b'\xff')):
                kwargs = dict(side_effect=failure) if isinstance(failure, Exception) else dict(return_value=failure)
                with self.subTest(failure=type(failure).__name__), patch.object(wsl.subprocess, 'run', **kwargs):
                    self.assertIsNone(wsl.running())
        with patch.object(wsl, 'WINDOWS', False), patch.object(wsl.subprocess, 'run', side_effect=AssertionError('process')):
            self.assertIsNone(wsl.running())


class BoundaryTests(unittest.TestCase):
    def test_ordinary_unc_device_and_lookalike_roots_get_no_status_or_filesystem_probe(self):
        with patch.object(wsl, 'WINDOWS', True), \
                patch.object(wsl, 'running', side_effect=AssertionError('status query')), \
                patch.object(Path, 'lstat', side_effect=AssertionError('filesystem probe')), \
                patch.object(Path, 'stat', side_effect=AssertionError('filesystem probe')), \
                patch.object(os, 'scandir', side_effect=AssertionError('filesystem probe')):
            for value in UNSAFE:
                with self.subTest(value=value):
                    issues = []
                    self.assertEqual(discovery.files([value], lambda _: True, issues, wsl.WslRoots()), [])
                    self.assertEqual([reason for _, reason in issues], ['UnsafePath'])

    def test_stopped_unknown_and_unavailable_distros_have_no_unc_probe(self):
        for status, reason in (({}, 'WSLNotRunning'), ({'debian': 'Debian'}, 'WSLNotRunning'),
                               (None, 'WSLUnavailable')):
            with self.subTest(status=status), patch.object(wsl, 'WINDOWS', True), \
                    patch.object(wsl, 'running', return_value=status), \
                    patch.object(Path, 'lstat', side_effect=AssertionError('UNC probe')), \
                    patch.object(os, 'scandir', side_effect=AssertionError('UNC probe')):
                issues = []
                self.assertEqual(discovery.files([ROOT], lambda _: True, issues, wsl.WslRoots()), [])
                self.assertEqual([why for _, why in issues], [reason])

    def test_a_default_home_or_a_direct_reader_does_not_select_a_wsl_root(self):
        with patch.object(wsl, 'WINDOWS', True), patch.object(wsl, 'running', side_effect=AssertionError('query')), \
                patch.object(Path, 'lstat', side_effect=AssertionError('UNC probe')), \
                patch.object(Path, 'home', return_value=Path(r'\\wsl.localhost\Ubuntu\home\invented')), \
                patch.dict(os.environ, CODEX_HOME='', CLAUDE_CONFIG_DIR=''):
            issues = []
            self.assertEqual(codex.files(skipped=issues), [])
            self.assertEqual(claude_code.files(skipped=issues), [])
            self.assertEqual(claude_code.read([ROOT + r'\s.jsonl'], issues), [])
            self.assertEqual(codex.read([ROOT + r'\rollout-test.jsonl'])[0], [])
        self.assertTrue(issues)
        self.assertTrue(all(reason == 'UnsafePath' for _, reason in issues))

    def test_approved_scope_is_per_scan_and_cannot_escape_to_another_folder_or_distro(self):
        with patch.object(wsl, 'WINDOWS', True), patch.object(wsl, 'running', return_value={'ubuntu': 'Ubuntu'}), \
                patch.object(wsl.WslRoots, '_checked', side_effect=lambda value: Path(str(value))):
            access = wsl.WslRoots()
            canonical, reason = access.chosen(ROOT.replace('wsl.localhost', 'wsl$'))
            self.assertEqual((canonical, reason), (Path(ROOT), None))
            self.assertIsNotNone(access.source(ROOT + r'\sessions\rollout-test.jsonl')[0])
            for value in (ROOT + '-other\\s.jsonl', CLAUDE + r'\projects\s.jsonl',
                          ROOT.replace('Ubuntu', 'Debian') + r'\s.jsonl',
                          ROOT + r'\..\other\s.jsonl'):
                with self.subTest(value=value):
                    self.assertEqual(access.source(value), (None, 'UnsafePath'))
            fresh = wsl.WslRoots()
            with patch.object(wsl, 'running', side_effect=AssertionError('unselected query')):
                self.assertEqual(fresh.source(ROOT + r'\sessions\s.jsonl'), (None, 'UnsafePath'))

    def test_git_and_cache_validators_do_not_inherit_wsl_permission(self):
        with patch.object(Path, 'lstat', side_effect=AssertionError('UNC probe')), \
                patch.object(wsl, 'running', side_effect=AssertionError('status query')), \
                patch.dict(os.environ, PLER_CACHE_DIR=ROOT):
            self.assertIsNone(paths.local_path(ROOT))
            self.assertIsNone(paths.cache_folder())
            self.assertIsNone(paths.user_folder(ROOT))

    def test_status_is_rechecked_before_reader_and_cache_access(self):
        with patch.object(wsl, 'WINDOWS', True), \
                patch.object(wsl, 'running', side_effect=[{'ubuntu': 'Ubuntu'}, {}]) as status, \
                patch.object(wsl.WslRoots, '_checked', side_effect=lambda value: Path(str(value))):
            access = wsl.WslRoots()
            access.chosen(ROOT)
            cache = SimpleNamespace(get=lambda _: self.fail('cache checked after distro stopped'))
            result, issues = codex.read([ROOT + r'\sessions\rollout-test.jsonl'], cache, access)
        self.assertEqual((result, [reason for _, reason in issues]), ([], ['WSLNotRunning']))
        self.assertEqual(status.call_count, 2)

    def test_root_links_and_reparse_points_are_never_followed_on_wsl(self):
        for info in (SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0),
                     SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)):
            with self.subTest(info=info), patch.object(wsl, 'WINDOWS', True), \
                    patch.object(wsl, 'running', return_value={'ubuntu': 'Ubuntu'}), \
                    patch.object(Path, 'lstat', return_value=info), \
                    patch.object(os, 'readlink', side_effect=AssertionError('WSL link followed')):
                self.assertEqual(wsl.WslRoots().chosen(ROOT), (None, 'UnsafePath'))

    def test_internal_wsl_links_are_skipped_without_traversal(self):
        entry = SimpleNamespace(name='linked', path=ROOT + r'\sessions\linked',
                                stat=lambda **_: SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400))
        with patch.object(wsl, 'WINDOWS', True), patch.object(wsl, 'running', return_value={'ubuntu': 'Ubuntu'}), \
                patch.object(wsl.WslRoots, '_checked', side_effect=lambda value: Path(str(value))), \
                patch.object(os, 'scandir') as directories, \
                patch.object(os, 'readlink', side_effect=AssertionError('internal link followed')):
            directories.return_value.__enter__.return_value = iter([entry])
            issues = []
            self.assertEqual(discovery.files([ROOT + r'\sessions'], lambda _: True, issues, wsl.WslRoots()), [])
        self.assertEqual(directories.call_count, 1)
        self.assertEqual(issues, [(entry.path, 'UnsafePath')])

    def test_case_distinct_wsl_files_remain_distinct_through_discovery_and_both_readers(self):
        names = ['rollout-A.jsonl', 'rollout-a.jsonl']
        files = [ROOT + '\\sessions\\' + name for name in names]
        entries = [SimpleNamespace(name=name, path=value,
                   stat=lambda **_: SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0))
                   for name,value in zip(names,files)]
        def codex_rows_for(path, _decode):
            result = codex_rows(str(path))
            for row in result:
                if row['type'] == 'token_usage_record':
                    row['payload']['response_id'] += str(path)
            return result
        def claude_rows_for(path):
            return [claude_reply(str(path), str(path), str(path), USAGE, [], '2026-10-20T10:00:05Z')]
        with patch.object(wsl, 'WINDOWS', True), patch.object(wsl, 'running', return_value={'ubuntu': 'Ubuntu'}), \
                patch.object(wsl.WslRoots, '_checked', side_effect=lambda value: Path(str(value))), \
                patch.object(os, 'scandir') as directories, \
                patch.object(codex, '_rows', side_effect=codex_rows_for), \
                patch.object(claude_code, '_rows', side_effect=claude_rows_for), \
                patch('pler.usage.reconcile.ProjectRoots._git_root', return_value=None):
            directories.return_value.__enter__.return_value = iter(entries)
            access = wsl.WslRoots()
            found = discovery.files([ROOT + r'\sessions'], lambda _: True, [], access)
            self.assertEqual([str(path) for path in found], files)
            codex_sessions, issues = codex.read(found, access=access)
            claude_sessions = claude_code.read(found, access=access)
        self.assertEqual(issues, [])
        self.assertEqual((len(codex_sessions), sum(total(s.tokens) for s in codex_sessions)), (2, 4200))
        self.assertEqual((len(claude_sessions), sum(total(s.tokens) for s in claude_sessions)), (2, 2520))


class SyntheticNamespaceTests(unittest.TestCase):
    def test_env_explicit_aliases_and_both_readers_work_without_leaking_scope(self):
        with tempfile.TemporaryDirectory() as folder, ExitStack() as stack:
            temporary = Path(folder)
            claude = temporary / 'home' / 'invented' / '.claude' / 'projects' / 'shop' / 's.jsonl'
            rollout = temporary / 'home' / 'invented' / '.codex' / 'sessions' / 'rollout-test.jsonl'
            write_jsonl(claude, [claude_reply('s1', 'm1', 'r1', USAGE, [], '2026-10-20T10:00:05Z')])
            write_jsonl(rollout, codex_rows())
            (temporary / 'home' / 'invented' / '.codex' / 'archived_sessions').mkdir()
            events = []
            original_stat, original_lstat = Path.stat, Path.lstat
            original_is_dir, original_is_file, original_exists = Path.is_dir, Path.is_file, Path.exists
            original_open, original_path_open, original_scandir = builtins.open, Path.open, os.scandir
            original_os_stat, original_os_lstat, original_os_open = os.stat, os.lstat, os.open

            def local(value):
                if not paths.network(value):
                    return value
                parsed = wsl.split(value)
                self.assertIsNotNone(parsed)
                self.assertEqual(parsed[0], 'Ubuntu')
                self.assertIn('status', events, 'UNC touched before status query')
                events.append('filesystem')
                return temporary.joinpath(*parsed[1])

            def fake_scandir(value):
                directory = local(value)
                if not paths.network(value):
                    return original_scandir(directory)
                class Entries:
                    def __enter__(self):
                        with original_scandir(directory) as entries:
                            self.entries = list(entries)
                        return iter(SimpleNamespace(name=e.name, path=str(PureWindowsPath(str(value)) / e.name),
                                                    stat=e.stat) for e in self.entries)
                    def __exit__(self, *args):
                        pass
                return Entries()

            def status():
                events.append('status')
                return {'ubuntu': 'Ubuntu'}

            stack.enter_context(patch.object(wsl, 'WINDOWS', True))
            query = stack.enter_context(patch.object(wsl, 'running', side_effect=status))
            stack.enter_context(patch.object(Path, 'lstat', lambda value, *a, **k: original_lstat(Path(local(value)), *a, **k)))
            stack.enter_context(patch.object(Path, 'stat', lambda value, *a, **k: original_stat(Path(local(value)), *a, **k)))
            # Python 3.14 is_dir uses os.path.isdir directly; older versions go through Path.stat.
            # Map both public layers, including low-level calls, before any fake UNC can reach the OS.
            stack.enter_context(patch.object(Path, 'is_dir', lambda value, *a, **k: original_is_dir(Path(local(value)), *a, **k)))
            stack.enter_context(patch.object(Path, 'is_file', lambda value, *a, **k: original_is_file(Path(local(value)), *a, **k)))
            stack.enter_context(patch.object(Path, 'exists', lambda value, *a, **k: original_exists(Path(local(value)), *a, **k)))
            stack.enter_context(patch.object(os, 'stat', lambda value, *a, **k: original_os_stat(local(value), *a, **k)))
            stack.enter_context(patch.object(os, 'lstat', lambda value, *a, **k: original_os_lstat(local(value), *a, **k)))
            stack.enter_context(patch.object(os, 'open', lambda value, *a, **k: original_os_open(local(value), *a, **k)))
            stack.enter_context(patch.object(builtins, 'open', lambda value, *a, **k: original_open(local(value), *a, **k)))
            stack.enter_context(patch.object(Path, 'open', lambda value, *a, **k: original_path_open(Path(local(value)), *a, **k)))
            stack.enter_context(patch.object(os, 'scandir', side_effect=fake_scandir))
            stack.enter_context(patch.dict(os.environ, PLER_CACHE_DIR=r'\\example.invalid\no-cache',
                                           CLAUDE_CONFIG_DIR=CLAUDE, CODEX_HOME=ROOT))
            sessions, sources = scan()
            self.assertEqual((len(sessions), sources['claude_files'], sources['codex_files']), (2, 1, 1),
                             (sources,[(s.agent,s.issues) for s in sessions]))
            self.assertEqual(sources['skipped'], [])
            self.assertEqual(sum(total(s.tokens) for s in sessions), 3360)
            self.assertEqual(query.call_count, 3)  # discovery, Codex reader, Claude reader
            sessions, sources = scan([CLAUDE + r'\projects', CLAUDE.replace('wsl.localhost', 'wsl$') + r'\projects'],
                                     [ROOT + r'\sessions', ROOT.replace('wsl.localhost', 'wsl$') + r'\sessions'])
            self.assertEqual((len(sessions), sources['claude_files'], sources['codex_files']), (2, 1, 1))
            self.assertEqual(sources['skipped'], [])
            # No permission is retained by a later reader or by a new scan context.
            self.assertEqual(codex.read([ROOT + r'\sessions\rollout-test.jsonl'])[0], [])


if __name__ == '__main__':
    unittest.main()
