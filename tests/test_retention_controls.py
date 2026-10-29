"""Retained history is a choice; rebuilding caches must never erase its only copy.

All records, settings and cache paths are invented in an isolated local folder.
"""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler.usage import archive,preferences,scan
from pler.usage.records import total
from test_archive import codex_rows
from test_logs import write_jsonl


class RetentionControlTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.claude=self.root/'claude/projects'
        self.codex=self.root/'codex/sessions'
        self.claude.mkdir(parents=True)
        self.codex.mkdir(parents=True)
        (self.codex.parent/'archived_sessions').mkdir()
        self.cache=self.root/'cache'
        self.environment=patch.dict(os.environ,CLAUDE_CONFIG_DIR=str(self.claude.parent),
            CODEX_HOME=str(self.codex.parent),PLER_CACHE_DIR=str(self.cache))
        self.environment.start();self.addCleanup(self.environment.stop)

    def seed(self):
        source=self.codex/'rollout-invented.jsonl'
        write_jsonl(source,codex_rows())
        rows,details=scan()
        self.assertEqual(sum(total(row.tokens) for row in rows),230)
        return source,details

    def test_live_sources_expose_retention_state_size_and_limits_from_first_read(self):
        _,details=self.seed()
        value=details['archive']
        self.assertTrue(value['available'])
        self.assertTrue(value['enabled'])
        self.assertTrue(value['retention_enabled'])
        self.assertTrue(value['stored_files_known'])
        self.assertEqual((value['stored_files'],value['archive_files']),(1,0))
        self.assertGreater(value['stored_bytes'],0)
        self.assertEqual((value['max_days'],value['max_files'],value['max_bytes']),
                         (365,2048,64*1024*1024))
        self.assertFalse(value['stale_snapshot'])

    def test_disabling_hides_deleted_history_without_loading_or_erasing_it_then_reenable_restores(self):
        source,_=self.seed()
        source.unlink()
        prior=(self.cache/archive.FILENAME).read_bytes()
        disabled=archive.set_retention(False)
        self.assertTrue(disabled['ok'])
        with patch.object(archive,'_load',side_effect=AssertionError('read disabled archive')):
            rows,details=scan()
        self.assertEqual(rows,[])
        self.assertTrue(details['archive']['available'])
        self.assertFalse(details['archive']['enabled'])
        self.assertFalse(details['archive']['retention_enabled'])
        self.assertFalse(details['archive']['stored_files_known'])
        self.assertEqual(details['archive']['stored_bytes'],len(prior))
        self.assertEqual((self.cache/archive.FILENAME).read_bytes(),prior)
        self.assertTrue(archive.set_retention(True)['ok'])
        rows,details=scan()
        self.assertEqual(sum(total(row.tokens) for row in rows),230)
        self.assertTrue(rows[0].source_deleted)
        self.assertEqual(details['archive']['archive_files'],1)

    def test_disabling_stops_new_retention_but_keeps_reading_live_records(self):
        self.assertTrue(archive.set_retention(False)['ok'])
        source=self.codex/'rollout-invented.jsonl'
        write_jsonl(source,codex_rows())
        rows,details=scan()
        self.assertEqual(sum(total(row.tokens) for row in rows),230)
        self.assertFalse(details['archive']['enabled'])
        self.assertFalse((self.cache/archive.FILENAME).exists())
        source.unlink()
        self.assertEqual(scan()[0],[])

    def test_reenable_does_not_import_deleted_history_observed_only_while_disabled(self):
        archive.set_retention(False)
        source=self.codex/'rollout-invented.jsonl'
        write_jsonl(source,codex_rows())
        scan()
        self.assertTrue((self.cache/'codex.json').exists())
        source.unlink()
        archive.set_retention(True)
        rows,details=scan()
        self.assertEqual(rows,[])
        self.assertEqual(details['archive']['stored_files'],0)

    def test_reset_removes_only_disposable_caches_preserving_deleted_history_and_controls(self):
        source,_=self.seed()
        # Include an unreadable disposable cache too: reset is a supported repair.
        (self.cache/'claude.json').write_bytes(b'invented damaged cache')
        quota=self.cache/'claude-quota.jsonl'
        quota.write_bytes(b'invented quota bytes')
        self.assertTrue(archive.set_retention(False)['ok'])
        self.assertTrue(archive.set_retention(True)['ok'])
        extra=self.cache/'invented-user-file.txt'
        extra.write_bytes(b'keep this')
        preserved={name:(self.cache/name).read_bytes() for name in
                   (archive.FILENAME,archive.GENERATION,preferences.FILENAME,quota.name,extra.name)}
        source.unlink()
        result=archive.reset_cache()
        self.assertTrue(result['ok'])
        self.assertEqual(result['cleared_files'],2)
        for name in ('claude.json','codex.json'):
            self.assertFalse((self.cache/name).exists())
        self.assertEqual(preserved,{name:(self.cache/name).read_bytes() for name in preserved})
        rows,details=scan()
        self.assertEqual(sum(total(row.tokens) for row in rows),230)
        self.assertTrue(rows[0].source_deleted)
        self.assertEqual(details['archive']['archive_files'],1)

    def test_inflight_loaded_scan_cannot_write_after_disabling(self):
        self.seed()
        inflight=archive.Archive()
        prior=(self.cache/archive.FILENAME).read_bytes()
        old=inflight.scan_generation
        # Mark an actual dirty projection: without the boundary this would rewrite.
        inflight.dirty=True
        disabled=archive.set_retention(False)
        with patch.object(archive,'_write',side_effect=AssertionError('stale scan wrote')):
            result=inflight.finish()
        self.assertTrue(result['stale_snapshot'])
        self.assertEqual(result['scan_generation'],old)
        self.assertEqual(result['clear_generation'],disabled['clear_generation'])
        self.assertFalse(result['enabled'])
        self.assertEqual((self.cache/archive.FILENAME).read_bytes(),prior)

    def test_disable_then_reenable_still_invalidates_a_scan_from_before_both_actions(self):
        self.seed()
        inflight=archive.Archive()
        inflight.dirty=True
        archive.set_retention(False)
        enabled=archive.set_retention(True)
        with patch.object(archive,'_write',side_effect=AssertionError('stale scan wrote')):
            result=inflight.finish()
        self.assertTrue(result['stale_snapshot'])
        self.assertTrue(result['retention_enabled'])
        self.assertEqual(result['clear_generation'],enabled['clear_generation'])

    def test_a_scan_started_while_disabled_is_stale_after_reenable(self):
        archive.set_retention(False)
        inflight=archive.Archive()
        self.assertFalse(inflight.enabled)
        archive.set_retention(True)
        self.assertTrue(inflight.finish()['stale_snapshot'])

    def test_identical_choice_is_not_rewritten_and_has_no_new_generation(self):
        first=archive.set_retention(False)
        with patch.object(archive,'_write',side_effect=AssertionError('unchanged preference rewritten')):
            second=archive.set_retention(False)
        self.assertEqual(first,second)

    def test_failed_preference_write_is_not_reported_as_a_successful_toggle(self):
        self.seed()
        inflight=archive.Archive()
        inflight.dirty=True
        write=archive._write
        def fail_preference(path,value):
            if path.name==preferences.FILENAME:
                raise OSError('invented write failure')
            return write(path,value)
        with patch.object(archive,'_write',side_effect=fail_preference):
            result=archive.set_retention(False)
        self.assertFalse(result['ok'])
        self.assertGreater(result['errors'],0)
        self.assertTrue(archive.Archive().retention_enabled)
        self.assertTrue(inflight.finish()['stale_snapshot'])

    def test_reset_never_recursively_removes_a_directory_with_a_cache_filename(self):
        self.cache.mkdir()
        directory=self.cache/'codex.json'
        directory.mkdir()
        keep=directory/'invented-user-data.txt'
        keep.write_bytes(b'keep this')
        result=archive.reset_cache()
        self.assertFalse(result['ok'])
        self.assertEqual(result['errors'],1)
        self.assertEqual(keep.read_bytes(),b'keep this')

    def test_explicit_choice_repairs_a_corrupt_generation_marker(self):
        self.seed()
        (self.cache/archive.GENERATION).write_text('{broken','utf-8')
        result=archive.set_retention(False)
        self.assertTrue(result['ok'])
        self.assertEqual(archive.archive_generation(),result['clear_generation'])
        self.assertFalse(archive.Archive().enabled)

    def test_malformed_preference_fails_closed_until_explicitly_repaired(self):
        self.seed()
        path=self.cache/preferences.FILENAME
        for value in ({'format':1,'retention_enabled':'false'}, {'format':1,'retention_enabled':True,'private':'never'},
                      {'format':True,'retention_enabled':True},[],None):
            with self.subTest(value=value):
                path.write_text(json.dumps(value),'utf-8')
                with patch.object(archive,'_load',side_effect=AssertionError('opened archive with invalid preference')):
                    value=archive.Archive().info()
                self.assertFalse(value['enabled'])
                self.assertGreater(value['errors'],0)
        self.assertTrue(archive.set_retention(True)['ok'])
        self.assertTrue(archive.Archive().enabled)

    def test_unsafe_cache_never_probes_a_network_preference_or_archive(self):
        with patch.dict(os.environ,PLER_CACHE_DIR=r'\\invented-server\private-cache'):
            with patch.object(Path,'stat',side_effect=AssertionError('network stat')), \
                    patch.object(Path,'lstat',side_effect=AssertionError('network lstat')), \
                    patch.object(Path,'open',side_effect=AssertionError('network open')):
                self.assertFalse(archive.set_retention(False)['ok'])
                self.assertFalse(archive.reset_cache()['ok'])
                value=archive.Archive().info()
                self.assertFalse(value['available'])
                self.assertFalse(value['enabled'])

    def test_invalid_api_value_cannot_toggle_retention(self):
        for value in (0,1,'false',None,{},[]):
            with self.subTest(value=value):
                self.assertFalse(archive.set_retention(value)['ok'])
        self.assertFalse(self.cache.exists())


if __name__=='__main__':unittest.main()
