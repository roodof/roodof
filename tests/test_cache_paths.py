"""Cache configuration cannot direct metadata reads/writes through network or link paths."""
import contextlib
import json
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pler import paths, statusline
from pler.usage import codex
from pler.usage.cache import FileCache
from pler.usage.records import total
from test_logs import codex_rows, write_jsonl

REMOTE = (r'\\example.invalid\audit', '//example.invalid/audit',
          r'\\?\UNC\example.invalid\audit', r'\\.\UNC\example.invalid\audit',
          r'\\?\C:\invented-device-path')
FOUND = {'300': [10, 2000000000]}


class CachePathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def blocked_io(self, *, probe=False):
        stack = contextlib.ExitStack()
        for method in ('read_text', 'open', 'mkdir'):
            stack.enter_context(patch.object(Path, method, side_effect=AssertionError('unsafe cache I/O')))
        stack.enter_context(patch('pler.usage.cache.tempfile.NamedTemporaryFile',
                                  side_effect=AssertionError('unsafe temporary file')))
        if probe:
            stack.enter_context(patch.object(Path, 'lstat', side_effect=AssertionError('network probe')))
        return stack

    def exercise_disabled_cache(self):
        cache = FileCache('codex', 'synthetic')
        self.assertIsNone(cache.path)
        self.assertIsNone(cache.get(self.root / 'not-opened.jsonl'))
        cache.put(self.root / 'not-opened.jsonl', [dict(type='metadata')])
        cache.new = {'invented': dict(signature=[1, 1], rows=[], checksum='invented')}
        cache.save()
        self.assertEqual(statusline.samples(), [])
        self.assertFalse(statusline.record(FOUND, now=1900000000))
        self.assertEqual(statusline.line({}, FOUND, 'en'), '5h 10%')

    def test_unc_and_device_config_disable_cache_without_filesystem_probe(self):
        for remote in REMOTE:
            with self.subTest(remote=remote), patch.dict(os.environ, PLER_CACHE_DIR=remote), self.blocked_io(probe=True):
                self.assertIsNone(paths.cache_folder())
                self.exercise_disabled_cache()

    def test_explicit_quota_folder_uses_same_network_boundary(self):
        for remote in REMOTE:
            with self.subTest(remote=remote), self.blocked_io(probe=True):
                self.assertEqual(statusline.samples(remote), [])
                self.assertFalse(statusline.record(FOUND, remote, now=1900000000))

    def test_network_default_environment_base_is_rejected_before_probe(self):
        for system, platform, variable in (('nt', 'win32', 'LOCALAPPDATA'), ('posix', 'linux', 'XDG_CACHE_HOME')):
            fake_os = SimpleNamespace(name=system, environ={variable: REMOTE[0]}, path=os.path)
            with self.subTest(system=system), patch.object(paths, 'os', fake_os), \
                    patch.object(paths.sys, 'platform', platform), self.blocked_io(probe=True):
                self.assertIsNone(paths.cache_folder())

    def test_local_default_environment_and_home_locations_are_preserved(self):
        # Resolved: the simulated Windows cases must not depend on a macOS-style system link in TMPDIR.
        root = Path(os.path.realpath(self.root))
        home = root / 'synthetic-home'
        selected = root / 'selected-cache'
        cases = [('nt', 'win32', {'LOCALAPPDATA': str(selected)}, selected / 'pler'),
                 ('nt', 'win32', {}, home / 'AppData' / 'Local' / 'pler'),
                 ('posix', 'darwin', {}, home / 'Library' / 'Caches' / 'pler'),
                 ('posix', 'linux', {'XDG_CACHE_HOME': str(selected)}, selected / 'pler'),
                 ('posix', 'linux', {}, home / '.cache' / 'pler')]
        for system, platform, environment, expected in cases:
            fake_os = SimpleNamespace(name=system, environ=environment, path=os.path)
            with self.subTest(system=system, platform=platform, environment=environment), \
                    patch.object(paths, 'os', fake_os), patch.object(paths.sys, 'platform', platform), \
                    patch.object(Path, 'home', return_value=home):
                self.assertEqual(paths.cache_folder(), expected)

    def test_network_home_fallback_does_not_probe(self):
        fake_os = SimpleNamespace(name='nt', environ={}, path=os.path)
        with patch.object(paths, 'os', fake_os), patch.object(Path, 'home', return_value=Path(REMOTE[0])), \
                self.blocked_io(probe=True):
            self.assertIsNone(paths.cache_folder())

    def test_local_and_relative_configured_directories_stay_supported(self):
        for folder in (str(self.root / 'cache'), os.path.relpath(self.root / 'cache')):
            with self.subTest(folder=folder), patch.dict(os.environ, PLER_CACHE_DIR=folder):
                self.assertEqual(paths.cache_folder(), self.root / 'cache')

    def test_unreadable_or_invalid_cache_location_is_disabled_without_fallback(self):
        for error in (PermissionError('invented denial'), ValueError('invalid local path')):
            with self.subTest(error=type(error).__name__), patch.dict(os.environ, PLER_CACHE_DIR=str(self.root)), \
                    patch.object(Path, 'lstat', side_effect=error), self.blocked_io():
                self.exercise_disabled_cache()

    def test_symlink_and_junction_ancestors_stop_before_child_or_file_access(self):
        linked = self.root / 'linked'
        real = Path.lstat
        for info in (SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0),
                     SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)):
            visited = []
            def guarded(path, *args, **kwargs):
                visited.append(path)
                if path == linked:
                    return info
                if linked in path.parents:
                    self.fail('a child through a link was probed')
                return real(path, *args, **kwargs)
            with self.subTest(info=info), patch.dict(os.environ, PLER_CACHE_DIR=str(linked / 'cache')), \
                    patch.object(Path, 'lstat', guarded), self.blocked_io():
                self.exercise_disabled_cache()
            self.assertIn(linked, visited)

    def test_symlink_or_reparse_final_cache_files_are_not_read_or_written(self):
        real = Path.lstat
        targets = {self.root / 'codex.json', self.root / statusline.FILE}
        for info in (SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0),
                     SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0x400)):
            def guarded(path, *args, **kwargs):
                return info if path in targets else real(path, *args, **kwargs)
            with self.subTest(info=info), patch.dict(os.environ, PLER_CACHE_DIR=str(self.root)), \
                    patch.object(Path, 'lstat', guarded), self.blocked_io():
                self.exercise_disabled_cache()
                self.assertEqual(statusline.samples(self.root), [])
                self.assertFalse(statusline.record(FOUND, self.root, now=1900000000))

    def test_local_cache_and_quota_files_still_persist(self):
        with patch.dict(os.environ, PLER_CACHE_DIR=str(self.root / 'cache')):
            source = self.root / 'source.jsonl'
            source.write_text('{}\n', 'utf-8')
            cache = FileCache('codex', 'synthetic')
            self.assertIsNone(cache.get(source))
            cache.put(source, [dict(type='metadata')]); cache.save()
            self.assertEqual(FileCache('codex', 'synthetic').get(source), [dict(type='metadata')])
            self.assertTrue(statusline.record(FOUND, now=1900000000))
            self.assertEqual(statusline.samples()[0][2], 10)

    def test_cache_target_or_parent_replaced_after_load_is_not_written(self):
        source = self.root / 'source.jsonl'
        source.write_text('{}\n', 'utf-8')
        (self.root / 'cache').mkdir()
        real = Path.lstat
        for blocked in (self.root / 'cache', self.root / 'cache' / 'codex.json'):
            with patch.dict(os.environ, PLER_CACHE_DIR=str(self.root / 'cache')):
                cache = FileCache('codex', 'synthetic')
                cache.get(source); cache.put(source, [dict(type='metadata')])
                def guarded(path, *args, **kwargs):
                    if path == blocked:
                        return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
                    return real(path, *args, **kwargs)
                with self.subTest(blocked=blocked), patch.object(Path, 'lstat', guarded), self.blocked_io():
                    cache.save()

    def test_quota_path_is_revalidated_after_reading_last_sample(self):
        target = self.root / statusline.FILE
        real = Path.lstat
        changed = [False]
        def last(_):
            changed[0] = True
            return None
        def guarded(path, *args, **kwargs):
            if changed[0] and path == target:
                return SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0)
            return real(path, *args, **kwargs)
        with patch.object(statusline, '_last', last), patch.object(Path, 'lstat', guarded), self.blocked_io():
            self.assertFalse(statusline.record(FOUND, self.root, now=1900000000))

    def test_failed_quota_prune_replace_cleans_temporary_file(self):
        self.assertTrue(statusline.record(FOUND, self.root, now=1900000000))
        before = (self.root / statusline.FILE).read_bytes()
        with patch.object(statusline, 'PRUNE_BYTES', 1), \
                patch('pler.statusline.os.replace', side_effect=PermissionError('invented replace denial')):
            statusline._prune(self.root / statusline.FILE, 1900000000)
        self.assertEqual((self.root / statusline.FILE).read_bytes(), before)
        self.assertEqual(list(self.root.glob('*.tmp')), [])

    def test_disabled_cache_preserves_original_reader_results(self):
        source = self.root / 'rollout-test.jsonl'
        write_jsonl(source, codex_rows())
        expected, expected_issues = codex.read([source])
        before = source.read_bytes()
        with patch.dict(os.environ, PLER_CACHE_DIR=REMOTE[0]):
            cache = FileCache('codex', 'synthetic')
            actual, issues = codex.read([source], cache)
            cache.save()
        self.assertEqual([s.as_dict() for s in actual], [s.as_dict() for s in expected])
        self.assertEqual(issues, expected_issues)
        self.assertEqual(source.read_bytes(), before)
        self.assertGreater(sum(total(s.tokens) for s in actual), 0)


if __name__ == '__main__':
    unittest.main()
