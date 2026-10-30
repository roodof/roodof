"""Local backup entrypoints: invented paths/data, fixed output and explicit profile scope."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pler import backup_cli, cli, usage
from pler.i18n import TEXT


class BackupCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.base = self.root / 'invented-data'
        self.base.mkdir()
        self.environment = patch.dict(os.environ, PLER_CACHE_DIR=str(self.base), PLER_LANG='en')
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def run_cli(self, args):
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            result = cli.main(args)
        return result, output.getvalue(), errors.getvalue()

    def fake(self):
        class BackupError(ValueError):
            def __init__(self, code):
                self.code = code
                super().__init__('PRIVATE-RAW-ERROR')
        summary = dict(format=1, version='0.2.25', parser_version='invented-parser',
                       schema_version=2, created_at='2026-10-30T00:00:00+00:00',
                       archive_files=2, verdicts=1, quota_samples=3, retention_enabled=False,
                       files=4, bytes=1234, private_path='PRIVATE-SOURCE-PATH')
        return SimpleNamespace(BackupError=BackupError, create=Mock(return_value=b'invented-bundle'),
                               read_file=Mock(return_value=b'invented-bundle'),
                               write_file=Mock(return_value=summary), inspect=Mock(return_value=summary),
                               restore=Mock(return_value=summary))

    def test_create_reports_counts_without_paths_or_private_diagnostics(self):
        core = self.fake()
        with patch.object(usage, 'backup', core, create=True):
            result, output, errors = self.run_cli(['backup', 'create', 'PRIVATE-DESTINATION', '--json'])
        value = json.loads(output)
        self.assertEqual((result, errors, value['ok'], value['archive_files']), (0, '', True, 2))
        self.assertEqual(value['action'], 'create')
        self.assertNotIn('PRIVATE', output)
        core.write_file.assert_called_once_with(b'invented-bundle', 'PRIVATE-DESTINATION')
        core.read_file.assert_not_called()

    def test_check_never_creates_or_restores_data(self):
        core = self.fake()
        with patch.object(usage, 'backup', core, create=True):
            result, output, errors = self.run_cli(['backup', 'check', 'PRIVATE-SOURCE', '--json'])
        self.assertEqual((result, errors, json.loads(output)['quota_samples']), (0, '', 3))
        core.read_file.assert_called_once_with('PRIVATE-SOURCE')
        core.inspect.assert_called_once_with(b'invented-bundle')
        core.create.assert_not_called()
        core.write_file.assert_not_called()
        core.restore.assert_not_called()
        self.assertNotIn('PRIVATE', output)

    def test_restore_requires_an_explicit_new_destination_and_keeps_current_profile(self):
        core = self.fake()
        with patch.object(usage, 'backup', core, create=True):
            result, output, errors = self.run_cli(['backup', 'restore', 'input.zip', '--to', 'new-data', '--json'])
        self.assertEqual((result, errors, json.loads(output)['action']), (0, '', 'restore'))
        core.restore.assert_called_once_with(b'invented-bundle', 'new-data')
        self.assertEqual(os.environ['PLER_CACHE_DIR'], str(self.base))

    def test_incomplete_or_unsupported_arguments_do_not_read_data(self):
        for args in (['restore', 'PRIVATE-FILE'], ['create', 'PRIVATE-FILE', '--to', 'PRIVATE-FOLDER'],
                     ['check', 'PRIVATE-FILE', '--to', 'PRIVATE-FOLDER'], ['unknown', 'PRIVATE-FILE'],
                     ['restore', 'PRIVATE-FILE', '--to'], ['create'], ['create', 'PRIVATE-FILE', '--extra']):
            with self.subTest(args=args):
                core = self.fake()
                with patch.object(usage, 'backup', core, create=True):
                    result, output, errors = self.run_cli(['backup', *args, '--json'])
                self.assertEqual((result, errors, json.loads(output)),
                                 (2, '', dict(ok=False, code='arguments')))
                for name in ('read_file', 'write_file', 'create', 'inspect', 'restore'):
                    getattr(core, name).assert_not_called()
                self.assertNotIn('PRIVATE', output)

    def test_all_core_errors_have_fixed_safe_json_codes(self):
        for code in ('invalid', 'unsupported', 'limit', 'unsafe_path', 'exists', 'io', 'busy', 'PRIVATE-UNKNOWN'):
            with self.subTest(code=code):
                core = self.fake()
                core.read_file.side_effect = core.BackupError(code)
                with patch.object(usage, 'backup', core, create=True):
                    result, output, errors = self.run_cli(['backup', 'check', 'PRIVATE-FILE', '--json'])
                self.assertEqual((result, errors), (1, ''))
                self.assertEqual(json.loads(output), dict(ok=False, code=code if code != 'PRIVATE-UNKNOWN' else 'io'))
                self.assertNotIn('PRIVATE', output)

    def test_unexpected_filesystem_error_does_not_echo_a_private_path(self):
        core = self.fake()
        core.read_file.side_effect = OSError('PRIVATE-ERROR-PATH')
        with patch.object(usage, 'backup', core, create=True):
            result, output, errors = self.run_cli(['backup', 'check', 'PRIVATE-FILE', '--json'])
        self.assertEqual((result, errors, json.loads(output)), (1, '', dict(ok=False, code='io')))

    def test_human_output_and_help_explain_privacy_and_restore_activation_in_both_languages(self):
        for lang in ('en', 'tr'):
            with self.subTest(lang=lang), patch.dict(os.environ, PLER_LANG=lang):
                core = self.fake()
                with patch.object(usage, 'backup', core, create=True):
                    result, output, errors = self.run_cli(['backup', 'restore', 'input.zip', '--to', 'new-data'])
                self.assertEqual((result, errors), (0, ''))
                self.assertIn('pler --data-dir', output)
                self.assertIn(TEXT[lang]['backup.restore_open'], output)
                output = io.StringIO()
                with redirect_stdout(output), self.assertRaises(SystemExit) as stopped:
                    backup_cli.main(['--help'])
                self.assertEqual(stopped.exception.code, 0)
                self.assertIn(TEXT[lang]['backup.privacy'], ' '.join(output.getvalue().split()))

    def test_explicit_data_folder_works_before_and_after_subcommand_and_restores_environment(self):
        folder = self.root / 'recovered ü data'
        variants = (['--data-dir', str(folder), 'report', '--json'],
                    ['report', '--json', '--data-dir', str(folder)],
                    ['report', '--data-dir=' + str(folder), '--json'])
        for argv in variants:
            seen = []
            def routed(args):
                seen.append((args, os.environ['PLER_CACHE_DIR']))
                return 17
            with self.subTest(argv=argv), patch.object(cli, '_main', side_effect=routed):
                self.assertEqual(cli.main(argv), 17)
            self.assertEqual(seen, [(['report', '--json'], str(folder))])
            self.assertEqual(os.environ['PLER_CACHE_DIR'], str(self.base))
            self.assertFalse(folder.exists())

    def test_data_folder_override_is_restored_when_the_command_fails(self):
        with patch.object(cli, '_main', side_effect=RuntimeError('invented')):
            with self.assertRaises(RuntimeError):
                cli.main(['--data-dir', str(self.root / 'new'), 'report'])
        self.assertEqual(os.environ['PLER_CACHE_DIR'], str(self.base))

    def test_empty_or_network_data_folder_is_refused_without_routing_or_network_probe(self):
        for value in ('', r'\\server\PRIVATE-SHARE', '//server/PRIVATE-SHARE'):
            with self.subTest(value=value), patch.object(cli, '_main', side_effect=AssertionError('routed')):
                if value:
                    with patch.object(Path, 'lstat', side_effect=AssertionError('network probe')):
                        result, output, errors = self.run_cli(['--data-dir', value, 'backup', 'check', 'input.zip', '--json'])
                else:
                    result, output, errors = self.run_cli(['--data-dir', value, 'backup', 'check', 'input.zip', '--json'])
            self.assertEqual((result, errors, json.loads(output)), (1, '', dict(ok=False, code='unsafe_path')))
            self.assertEqual(os.environ['PLER_CACHE_DIR'], str(self.base))

    def test_file_cannot_be_used_as_a_data_folder(self):
        path = self.root / 'ordinary-file'
        path.write_bytes(b'invented')
        with patch.object(cli, '_main', side_effect=AssertionError('routed')):
            result, output, errors = self.run_cli(['backup', 'check', 'input.zip', '--data-dir', str(path), '--json'])
        self.assertEqual((result, errors, json.loads(output)), (1, '', dict(ok=False, code='unsafe_path')))
        self.assertEqual(path.read_bytes(), b'invented')

    def test_missing_or_repeated_data_folder_is_a_safe_argument_error(self):
        for argv in (['backup', 'check', 'PRIVATE-FILE', '--json', '--data-dir'],
                     ['--data-dir', 'PRIVATE-ONE', 'backup', 'check', 'PRIVATE-FILE', '--data-dir', 'PRIVATE-TWO', '--json']):
            with self.subTest(argv=argv):
                result, output, errors = self.run_cli(argv)
                self.assertEqual((result, errors, json.loads(output)), (2, '', dict(ok=False, code='arguments')))
                self.assertNotIn('PRIVATE', output)

    def test_help_and_version_do_not_read_or_validate_a_data_folder(self):
        for argv in (['--data-dir', 'PRIVATE-NOT-OPENED', '--help'],
                     ['backup', '--help', '--data-dir', 'PRIVATE-NOT-OPENED'],
                     ['--data-dir', 'PRIVATE-NOT-OPENED', '--version']):
            with self.subTest(argv=argv), patch('pler.paths.cache_folder', side_effect=AssertionError('data opened')):
                with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as stopped:
                    cli.main(argv)
                self.assertEqual(stopped.exception.code, 0)

    def test_real_empty_metadata_bundle_roundtrip_uses_only_explicit_local_folders(self):
        # Complete file roundtrip at the CLI boundary, not just mocked routing.
        from pler.usage import preferences
        (self.base / preferences.FILENAME).write_text(json.dumps(preferences.value(False)), 'utf-8')
        before = (self.base / preferences.FILENAME).read_bytes()
        saved = self.root / 'invented.backup'
        target = self.root / 'recovered'
        result, output, errors = self.run_cli(['backup', 'create', str(saved), '--json'])
        self.assertEqual((result, errors, json.loads(output)['ok']), (0, '', True))
        result, output, errors = self.run_cli(['backup', 'check', str(saved), '--json'])
        self.assertEqual((result, errors, json.loads(output)['retention_enabled']), (0, '', False))
        result, output, errors = self.run_cli(['backup', 'restore', str(saved), '--to', str(target), '--json'])
        self.assertEqual((result, errors, json.loads(output)['ok']), (0, '', True))
        self.assertEqual(preferences.read(target), False)
        self.assertEqual((self.base / preferences.FILENAME).read_bytes(), before)
        result, output, errors = self.run_cli(['backup', 'restore', str(saved), '--to', str(target), '--json'])
        self.assertEqual((result, errors, json.loads(output)['code']), (1, '', 'exists'))
        result, output, errors = self.run_cli(['backup', 'create', str(saved), '--json'])
        self.assertEqual((result, errors, json.loads(output)['code']), (1, '', 'exists'))


if __name__ == '__main__':
    unittest.main()
