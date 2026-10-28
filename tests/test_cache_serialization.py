"""Cache serialization failure cannot replace a valid cache or discard extracted metadata."""
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


if __name__=='__main__':unittest.main()
