"""Recovery proofs use invented data, local temporary caches, and no provider calls."""
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import struct
import tempfile
import unittest
import warnings
from unittest.mock import patch
import zipfile

from pler import paths, statusline
from pler.usage import archive, backup, preferences, scan, verdicts
from pler.usage.records import total
from test_archive import claude_rows, codex_rows
from test_logs import write_jsonl


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.claude = self.root / 'claude' / 'projects'
        self.codex = self.root / 'codex' / 'sessions'
        self.claude.mkdir(parents=True)
        self.codex.mkdir(parents=True)
        (self.codex.parent / 'archived_sessions').mkdir()
        self.cache = self.root / 'cache'
        self.environment = patch.dict(os.environ, CLAUDE_CONFIG_DIR=str(self.claude.parent),
                                      CODEX_HOME=str(self.codex.parent), PLER_CACHE_DIR=str(self.cache))
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def seed(self):
        sources = [self.claude / 'invented.jsonl', self.codex / 'rollout-invented.jsonl']
        write_jsonl(sources[0], claude_rows())
        write_jsonl(sources[1], codex_rows())
        sessions, details = scan()
        self.assertEqual(sum(total(row.tokens) for row in sessions), 350)
        code = verdicts.session_code(sessions[0])
        verdicts.save(code, 'useful')
        statusline.record({'300': [25, 1793440800]}, now=1793430000)
        return sources, sessions, code

    def rewrite(self, data, change):
        with zipfile.ZipFile(io.BytesIO(data)) as bundle:
            files = {name: bundle.read(name) for name in bundle.namelist()}
        manifest = json.loads(files.pop(backup.MANIFEST))
        change(manifest, files)
        manifest['files'] = {name: {'bytes': len(value), 'sha256': hashlib.sha256(value).hexdigest()}
                             for name, value in files.items()}
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as bundle:
            bundle.writestr(backup.MANIFEST, json.dumps(manifest).encode())
            for name, value in files.items():
                bundle.writestr(name, value)
        return output.getvalue()

    def test_full_roundtrip_after_sources_deleted_preserves_totals_quality_verdicts_and_quota(self):
        sources, _, code = self.seed()
        for source in sources:
            source.unlink()
        old, _ = scan()
        describe = lambda row: (row.session_id, row.tokens, row.calls, row.source_deleted,
                                row.tokens_complete, row.calls_complete, row.counts_complete,
                                row.attribution_complete, row.models_complete, row.issues)
        before = [describe(row) for row in old]
        data = backup.create()
        info = backup.inspect(data)
        self.assertEqual((info['archive_files'], info['verdicts'], info['quota_samples']), (2, 1, 1))
        restored = self.root / 'recovered'
        backup.restore(data, restored)
        with patch.dict(os.environ, PLER_CACHE_DIR=str(restored)):
            recovered, _ = scan()
            self.assertEqual([describe(row) for row in recovered], before)
            self.assertEqual(verdicts.read(), {code: 'useful'})
            self.assertEqual(len(statusline.samples()), 1)
        self.assertTrue(all(not source.exists() for source in sources))

    def test_snapshot_and_restore_do_not_open_any_original_source(self):
        sources, _, _ = self.seed()
        original = Path.open
        def guarded(path, *args, **kwargs):
            if path in sources:
                raise AssertionError('original source opened')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'open', guarded):
            data = backup.create()
            backup.restore(data, self.root / 'restored')

    def test_bundle_includes_only_durable_fixed_metadata_and_no_canary_content(self):
        self.seed()
        (self.cache / 'invented-user-file.txt').write_text('PRIVATE-CANARY')
        (self.cache / 'claude.json').write_text('PRIVATE-CANARY')
        data = backup.create()
        self.assertNotIn(b'PRIVATE-CANARY', data)
        self.assertNotIn(b'REPLY-CANARY', data)
        with zipfile.ZipFile(io.BytesIO(data)) as bundle:
            self.assertTrue(set(bundle.namelist()) <= {backup.MANIFEST, *backup.LIMITS})
            self.assertNotIn(archive.GENERATION, bundle.namelist())

    def test_empty_history_is_a_valid_default_snapshot(self):
        data = backup.create()
        info = backup.inspect(data)
        self.assertEqual((info['files'], info['archive_files'], info['verdicts']), (0, 0, 0))
        self.assertTrue(info['retention_enabled'])
        backup.restore(data, self.root / 'empty')

    def test_retention_off_and_original_reader_keys_are_preserved(self):
        self.seed()
        archive.set_retention(False)
        original = json.loads((self.cache / archive.FILENAME).read_text())
        for entry in original['files'].values():
            entry['reader_key'] = 'invented-old-reader'
        archive._write(self.cache / archive.FILENAME, original)
        data = backup.create()
        restored = self.root / 'off'
        backup.restore(data, restored)
        self.assertFalse(backup.inspect(data)['retention_enabled'])
        self.assertFalse(preferences.read(restored))
        self.assertEqual({entry['reader_key'] for entry in json.loads((restored / archive.FILENAME).read_text())['files'].values()},
                         {'invented-old-reader'})

    def test_invalid_snapshot_file_is_refused_instead_of_exporting_partial_history(self):
        self.seed()
        for name in backup.LIMITS:
            path = self.cache / name
            original = path.read_bytes() if path.exists() else None
            path.write_bytes(b'{"format":999,"secret":"PRIVATE-CANARY"}')
            with self.subTest(name=name), self.assertRaises(backup.BackupError):
                backup.create()
            if original is None:
                path.unlink()
            else:
                path.write_bytes(original)

    def test_private_unknown_archive_row_rejected_even_with_recomputed_checksum(self):
        self.seed()
        data = backup.create()
        def change(manifest, files):
            value = json.loads(files[archive.FILENAME])
            entry = next(iter(value['files'].values()))
            entry['rows'][0]['secret'] = 'PRIVATE-CANARY'
            entry['checksum'] = archive._measured(entry['rows'])
            files[archive.FILENAME] = archive._encoded(value)
        with self.assertRaises(backup.BackupError):
            backup.inspect(self.rewrite(data, change))

    def test_unknown_archive_entry_field_and_wrong_source_identity_refused(self):
        self.seed()
        data = backup.create()
        for kind in ('extra', 'identity'):
            def change(manifest, files):
                value = json.loads(files[archive.FILENAME])
                entry = next(iter(value['files'].values()))
                if kind == 'extra':
                    entry['prompt'] = 'PRIVATE-CANARY'
                else:
                    entry['source'] += '-different'
                files[archive.FILENAME] = archive._encoded(value)
            with self.subTest(kind=kind), self.assertRaises(backup.BackupError):
                backup.inspect(self.rewrite(data, change))

    def test_damaged_or_truncated_zip_is_refused_without_destination(self):
        self.seed()
        data = backup.create()
        for bad in (b'not a backup', data[:-1], data + b'hidden', b'hidden' + data):
            target = self.root / 'bad'
            with self.subTest(length=len(bad)), self.assertRaises(backup.BackupError):
                backup.restore(bad, target)
            self.assertFalse(target.exists())

    def test_unsupported_versions_and_schema_refused_before_mutation(self):
        self.seed()
        data = backup.create()
        for key, value in (('format', 999), ('schema_version', 999), ('version', '999.0.0'),
                           ('parser_version', 'accounting-9999-01-01.1')):
            bad = self.rewrite(data, lambda manifest, files: manifest.update({key: value}))
            with self.subTest(key=key), self.assertRaises(backup.BackupError) as caught:
                backup.restore(bad, self.root / 'future')
            self.assertEqual(caught.exception.code, 'unsupported')
            self.assertFalse((self.root / 'future').exists())

    def test_checksum_mismatch_refused(self):
        self.seed()
        data = backup.create()
        with zipfile.ZipFile(io.BytesIO(data)) as bundle:
            files = {name: bundle.read(name) for name in bundle.namelist()}
        manifest = json.loads(files[backup.MANIFEST])
        manifest['files'][archive.FILENAME]['sha256'] = '0' * 64
        files[backup.MANIFEST] = json.dumps(manifest).encode()
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as bundle:
            for name, value in files.items():
                bundle.writestr(name, value)
        with self.assertRaises(backup.BackupError):
            backup.inspect(output.getvalue())

    def test_unknown_duplicate_traversal_and_compressed_members_refused(self):
        self.seed()
        data = backup.create()
        with zipfile.ZipFile(io.BytesIO(data)) as bundle:
            files = {name: bundle.read(name) for name in bundle.namelist()}
        for extra in ('../outside', '/absolute', 'unknown.json', backup.MANIFEST):
            output = io.BytesIO()
            with zipfile.ZipFile(output, 'w') as bundle:
                for name, value in files.items():
                    bundle.writestr(name, value)
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', UserWarning)
                    bundle.writestr(extra, b'{}')
            with self.subTest(extra=extra), self.assertRaises(backup.BackupError):
                backup.inspect(output.getvalue())
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
            for name, value in files.items():
                bundle.writestr(name, value)
        with self.assertRaises(backup.BackupError):
            backup.inspect(output.getvalue())

    def test_symlink_member_and_zip_comments_refused(self):
        data = backup.create()
        with zipfile.ZipFile(io.BytesIO(data)) as bundle:
            manifest = bundle.read(backup.MANIFEST)
        for kind in ('symlink', 'comment'):
            output = io.BytesIO()
            with zipfile.ZipFile(output, 'w') as bundle:
                info = zipfile.ZipInfo(backup.MANIFEST)
                if kind == 'symlink':
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                else:
                    bundle.comment = b'private extra'
                bundle.writestr(info, manifest)
            with self.subTest(kind=kind), self.assertRaises(backup.BackupError):
                backup.inspect(output.getvalue())

    def test_duplicate_json_keys_and_excessive_nesting_refused(self):
        data = backup.create()
        for content in (b'{"format":1,"format":1}', b'{"a":' + b'[' * 257 + b'0' + b']' * 257 + b'}'):
            output = io.BytesIO()
            with zipfile.ZipFile(output, 'w') as bundle:
                bundle.writestr(backup.MANIFEST, content)
            with self.assertRaises(backup.BackupError):
                backup.inspect(output.getvalue())

    def test_existing_target_and_current_cache_are_never_overwritten(self):
        self.seed()
        data = backup.create()
        before = {name: (self.cache / name).read_bytes() for name in backup.LIMITS if (self.cache / name).exists()}
        for target in (self.cache, self.root / 'already-empty'):
            target.mkdir(exist_ok=True)
            with self.assertRaises(backup.BackupError) as caught:
                backup.restore(data, target)
            self.assertEqual(caught.exception.code, 'exists')
        self.assertEqual(before, {name: (self.cache / name).read_bytes() for name in before})

    def test_staging_failure_keeps_target_absent_and_current_history_unchanged(self):
        self.seed()
        data = backup.create()
        before = (self.cache / archive.FILENAME).read_bytes()
        original = backup._write_new
        count = [0]
        def interrupted(path, content):
            count[0] += 1
            if count[0] == 2:
                raise OSError('invented interrupted write')
            original(path, content)
        with patch.object(backup, '_write_new', interrupted), self.assertRaises(backup.BackupError):
            backup.restore(data, self.root / 'interrupted')
        self.assertFalse((self.root / 'interrupted').exists())
        self.assertEqual(list(self.root.glob('.pler-restore-*')), [])
        self.assertEqual((self.cache / archive.FILENAME).read_bytes(), before)

    def test_publish_failure_removes_only_owned_staging_files(self):
        data = backup.create()
        with patch.object(backup.os, 'rename', side_effect=OSError('invented publish failure')):
            with self.assertRaises(backup.BackupError):
                backup.restore(data, self.root / 'interrupted')
        self.assertFalse((self.root / 'interrupted').exists())
        self.assertEqual(list(self.root.glob('.pler-restore-*')), [])

    def test_network_paths_are_refused_before_filesystem_queries(self):
        data = backup.create()
        with patch.object(Path, 'lstat', side_effect=AssertionError('network probed')):
            for path in ('//server/share/private', '\\\\server\\share\\private'):
                with self.assertRaises(backup.BackupError) as caught:
                    backup.restore(data, path)
                self.assertEqual(caught.exception.code, 'unsafe_path')

    def test_path_link_is_refused(self):
        link = self.root / 'linked'
        try:
            link.symlink_to(self.cache, target_is_directory=True)
        except OSError:
            self.skipTest('symlink creation unavailable')
        with self.assertRaises(backup.BackupError):
            backup.restore(backup.create(), link / 'new')

    def test_file_save_read_roundtrip_is_exclusive_and_local(self):
        self.seed()
        data = backup.create()
        path = self.root / 'history.pler-backup'
        self.assertEqual(backup.write_file(data, path)['archive_files'], 2)
        self.assertEqual(backup.read_file(path), data)
        with self.assertRaises(backup.BackupError) as caught:
            backup.write_file(data, path)
        self.assertEqual(caught.exception.code, 'exists')
        self.assertEqual(path.read_bytes(), data)

    def test_invalid_save_and_input_budgets_do_not_create_files(self):
        path = self.root / 'bad.pler-backup'
        with self.assertRaises(backup.BackupError):
            backup.write_file(b'bad', path)
        self.assertFalse(path.exists())
        data = backup.create()
        with patch.object(backup, 'MAX_BUNDLE_BYTES', len(data) - 1):
            with self.assertRaises(backup.BackupError) as caught:
                backup.inspect(data)
            self.assertEqual(caught.exception.code, 'limit')
            path.write_bytes(data)
            with self.assertRaises(backup.BackupError):
                backup.read_file(path)

    def test_large_central_directory_is_refused_before_zipfile_parses_members(self):
        data = backup.create()
        trailer = list(struct.unpack('<4s4H2IH', data[-22:]))
        trailer[5] = 2000
        trailer[6] = 1
        malicious = b'X' * 2001 + struct.pack('<4s4H2IH', *trailer)
        with patch.object(backup.zipfile, 'ZipFile', side_effect=AssertionError('central directory parsed')):
            with self.assertRaises(backup.BackupError):
                backup.inspect(malicious)

    def test_growth_after_observed_size_is_refused_instead_of_read_unbounded(self):
        path = self.root / 'growing'
        path.write_bytes(b'first')
        original = backup.os.fstat
        changed = [False]
        def grow(descriptor):
            info = original(descriptor)
            if not changed[0]:
                changed[0] = True
                with path.open('ab') as stream:
                    stream.write(b'-more-bytes-than-observed')
            return info
        with patch.object(backup.os, 'fstat', grow), self.assertRaises(backup.BackupError) as caught:
            backup.read_file(path)
        self.assertEqual(caught.exception.code, 'io')

    def test_partial_archive_corruption_never_exports_only_the_good_entries(self):
        self.seed()
        path = self.cache / archive.FILENAME
        value = json.loads(path.read_bytes())
        entry = next(iter(value['files'].values()))
        entry['checksum'] = '0' * 64
        path.write_bytes(archive._encoded(value))
        with self.assertRaises(backup.BackupError):
            backup.create()

    def test_row_budget_refuses_snapshot_instead_of_truncating(self):
        self.seed()
        with patch.object(backup, 'MAX_ROWS', 1), self.assertRaises(backup.BackupError) as caught:
            backup.create()
        self.assertEqual(caught.exception.code, 'limit')

    def test_public_inspection_contains_counts_without_sources_or_session_codes(self):
        _, _, code = self.seed()
        text = json.dumps(backup.inspect(backup.create()))
        self.assertNotIn(str(self.root), text)
        self.assertNotIn(code, text)
        self.assertNotIn('rollout-invented', text)

    def test_post_publish_sync_failure_leaves_only_complete_new_copy(self):
        self.seed()
        data = backup.create()
        target = self.root / 'complete-after-sync-failure'
        original = backup._sync_directory
        def fail_parent(path):
            if path == target.parent:
                raise OSError('invented parent sync failure')
            original(path)
        with patch.object(backup, '_sync_directory', fail_parent), self.assertRaises(backup.BackupError):
            backup.restore(data, target)
        self.assertTrue(target.is_dir())
        with zipfile.ZipFile(io.BytesIO(data)) as bundle:
            for name in bundle.namelist():
                if name != backup.MANIFEST:
                    self.assertEqual((target / name).read_bytes(), bundle.read(name))
        self.assertTrue((self.cache / archive.FILENAME).exists())

    @unittest.skipIf(os.name == 'nt', 'POSIX private permissions')
    def test_backup_and_restored_data_are_private_on_posix(self):
        self.seed()
        data = backup.create()
        target = self.root / 'restored'
        backup.restore(data, target)
        path = self.root / 'history.pler-backup'
        backup.write_file(data, path)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o700)
        for child in target.iterdir():
            self.assertEqual(stat.S_IMODE(child.stat().st_mode), 0o600)


if __name__ == '__main__':
    unittest.main()
