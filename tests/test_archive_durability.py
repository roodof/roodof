"""Own metadata survives pre-replace failures; durability failures never claim rollback."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler.usage import archive


class ArchiveDurabilityTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base=Path(self.temporary.name)
        environment=patch.dict(os.environ,PLER_CACHE_DIR=str(self.base))
        environment.start();self.addCleanup(environment.stop)
        self.path=self.base/archive.FILENAME

    def test_failed_file_sync_keeps_prior_archive_and_removes_temporary(self):
        old=b'{"format":1,"files":{}}'
        self.path.write_bytes(old)
        with patch.object(archive.os,'fsync',side_effect=OSError('invented failure')),patch.object(archive.os,'replace') as replace:
            with self.assertRaises(OSError):archive._write(self.path,{'format':2})
        replace.assert_not_called()
        self.assertEqual(self.path.read_bytes(),old)
        self.assertEqual(list(self.base.glob('*.tmp')),[])

    def test_buffered_file_is_flushed_and_synced_before_replace(self):
        events=[];replace=os.replace
        def synced(descriptor):
            pending=list(self.base.glob('*.tmp'))
            self.assertEqual(len(pending),1)
            self.assertEqual(json.loads(pending[0].read_bytes()),{'format':1,'files':{}})
            events.append('file_sync')
        def replaced(source,target):
            self.assertEqual(events,['file_sync'])
            replace(source,target);events.append('replace')
        def directory(path):
            self.assertEqual(path,self.path)
            self.assertEqual(json.loads(path.read_bytes()),{'format':1,'files':{}})
            events.append('directory_sync')
        with patch.object(archive.os,'fsync',side_effect=synced),patch.object(archive.os,'replace',side_effect=replaced),patch.object(archive,'_sync_directory',side_effect=directory):
            archive._write(self.path,{'format':1,'files':{}})
        self.assertEqual(events,['file_sync','replace','directory_sync'])
        self.assertEqual(list(self.base.glob('*.tmp')),[])

    def test_failed_replace_keeps_prior_archive_and_removes_temporary(self):
        old=b'{"format":1,"files":{}}';self.path.write_bytes(old)
        with patch.object(archive.os,'replace',side_effect=OSError('invented replacement failure')):
            with self.assertRaises(OSError):archive._write(self.path,{'format':2})
        self.assertEqual(self.path.read_bytes(),old)
        self.assertEqual(list(self.base.glob('*.tmp')),[])

    def test_directory_sync_failure_reports_error_after_visible_replacement(self):
        self.path.write_bytes(b'{"old":true}')
        with patch.object(archive,'_sync_directory',side_effect=OSError('invented sync failure')):
            with self.assertRaises(OSError):archive._write(self.path,{'new':True})
        self.assertEqual(json.loads(self.path.read_bytes()),{'new':True})
        self.assertEqual(list(self.base.glob('*.tmp')),[])

    def test_clear_syncs_removal_after_generation_is_written(self):
        self.path.write_bytes(b'{"format":1,"files":{}}')
        seen=[]
        def synced(path):
            seen.append(path.name)
            if path.name==archive.FILENAME:self.assertFalse(path.exists())
        with patch.object(archive,'_sync_directory',side_effect=synced):
            result=archive.clear_archive()
        self.assertTrue(result['ok'])
        self.assertEqual(seen,[archive.GENERATION,archive.FILENAME])

    def test_clear_does_not_claim_success_if_removal_sync_fails(self):
        self.path.write_bytes(b'{"format":1,"files":{}}')
        def synced(path):
            if path.name==archive.FILENAME:raise OSError('invented removal sync failure')
        with patch.object(archive,'_sync_directory',side_effect=synced):
            result=archive.clear_archive()
        self.assertFalse(result['ok'])
        self.assertGreater(result['errors'],0)
        self.assertFalse(self.path.exists())

    @unittest.skipIf(os.name=='nt','POSIX directory descriptors only')
    def test_directory_sync_closes_its_descriptor_even_on_failure(self):
        descriptor=os.open(str(self.base),os.O_RDONLY)
        close=os.close
        with patch.object(archive.os,'open',return_value=descriptor),patch.object(archive.os,'fsync',side_effect=OSError('invented sync failure')),patch.object(archive.os,'close',wraps=close) as closed:
            with self.assertRaises(OSError):archive._sync_directory(self.path)
        closed.assert_called_once_with(descriptor)

