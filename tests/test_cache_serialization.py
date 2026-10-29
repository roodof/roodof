"""Cache serialization failure cannot replace a valid cache or discard extracted metadata."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler.usage.cache import FileCache


class CacheSerializationTests(unittest.TestCase):
    def test_encoder_memory_failure_keeps_previous_file_and_current_metadata(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,PLER_CACHE_DIR=folder):
            cache=FileCache('memory-check','v1')
            first=Path(folder)/'first.jsonl';first.write_text('{}\n','utf-8')
            cache.get(first);cache.put(first,[dict(type='metadata')])
            cache.save()
            previous=cache.path.read_bytes()
            second=Path(folder)/'second.jsonl';second.write_text('{}\n','utf-8')
            cache.get(second);cache.put(second,[dict(type='metadata')])
            with patch('pler.usage.cache.json.dumps',side_effect=MemoryError('invented encoder failure')):
                cache.save()
            self.assertEqual(cache.path.read_bytes(),previous)
            self.assertIn(str(second),cache.new)
            self.assertEqual(list(Path(folder).glob('*.tmp')),[])

    def write(self,folder):
        cache=FileCache('digest-check','v1')
        source=Path(folder)/'source.jsonl';source.write_text('{}\n','utf-8')
        cache.get(source);cache.put(source,[dict(type='metadata',n=1)])
        cache.save()
        return cache.path,source

    def test_an_intact_file_is_trusted_with_one_digest_instead_of_one_checksum_per_entry(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,PLER_CACHE_DIR=folder):
            path,source=self.write(folder)
            json.loads(path.read_text('utf-8'))  # still one ordinary JSON object
            with patch('pler.usage.cache._checksum',side_effect=AssertionError('per-entry checksum')):
                cache=FileCache('digest-check','v1')
                self.assertTrue(cache.intact)
                self.assertEqual(cache.get(source),[dict(type='metadata',n=1)])

    def test_a_rewritten_file_falls_back_to_per_entry_checksums(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,PLER_CACHE_DIR=folder):
            path,source=self.write(folder)
            value=json.loads(path.read_text('utf-8'))
            path.write_text(json.dumps(value),'utf-8')  # same content, different bytes
            cache=FileCache('digest-check','v1')
            self.assertFalse(cache.intact)
            self.assertEqual(cache.get(source),[dict(type='metadata',n=1)])
            next(iter(value['files'].values()))['rows'][0]['n']=999
            path.write_text(json.dumps(value),'utf-8')
            self.assertIsNone(FileCache('digest-check','v1').get(source))
            # A wrong digest in the exact layout only loses the shortcut; valid entries still pass one by one.
            next(iter(value['files'].values()))['rows'][0]['n']=1
            body=json.dumps(value['files'],separators=(',',':'))
            path.write_text('{"key":"v1","digest":"%s","files":%s}'%('0'*64,body),'utf-8')
            cache=FileCache('digest-check','v1')
            self.assertFalse(cache.intact)
            self.assertEqual(cache.get(source),[dict(type='metadata',n=1)])


if __name__=='__main__':unittest.main()
