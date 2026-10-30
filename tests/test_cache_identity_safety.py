"""File replacement and interior rewrites cannot reuse stale synthetic projections."""
import os
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from pler.runtime import ScanCancelled,cancellation
from pler.usage import cache as rules
from pler.usage.cache import FileCache
from pler.usage import claude_code,codex
from test_grown_logs import claude_parts,codex_parts,append
from test_logs import write_jsonl


class CacheIdentitySafetyTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        env=patch.dict(os.environ,PLER_CACHE_DIR=str(self.root/'cache'))
        env.start();self.addCleanup(env.stop)
        self.source=self.root/'invented.jsonl'
        self.source.write_bytes(b'a\n'*30000)

    def seed(self):
        cache=FileCache('identity','v1');cache.get(self.source)
        cache.put(self.source,[dict(n=1)],dict(offset=self.source.stat().st_size))
        cache.save()
        self.assertIn(str(self.source),cache.new)
        return cache

    def test_same_size_and_mtime_replacement_is_a_cache_miss(self):
        self.seed();before=self.source.stat()
        replacement=self.root/'replacement.jsonl';replacement.write_bytes(b'b\n'*30000)
        os.utime(replacement,ns=(before.st_atime_ns,before.st_mtime_ns))
        os.replace(str(replacement),str(self.source))
        self.assertNotEqual(before.st_ino,self.source.stat().st_ino)
        self.assertIsNone(FileCache('identity','v1').get(self.source))

    def test_unchanged_identity_keeps_the_fast_cache_hit(self):
        self.seed()
        with patch.object(rules,'_prefix',side_effect=AssertionError('unchanged source read')):
            self.assertEqual(FileCache('identity','v1').get(self.source),[dict(n=1)])

    def test_interior_rewrite_then_append_cannot_reuse_old_prefix(self):
        self.seed()
        with self.source.open('r+b') as stream:
            stream.seek(20000);stream.write(b'b');stream.seek(0,2);stream.write(b'c\n')
        cache=FileCache('identity','v1');self.assertIsNone(cache.get(self.source))
        self.assertIsNone(cache.grown(self.source))

    def test_pure_append_still_reuses_the_verified_prefix(self):
        self.seed()
        with self.source.open('ab') as stream:stream.write(b'c\n')
        cache=FileCache('identity','v1');self.assertIsNone(cache.get(self.source))
        rows,resume=cache.grown(self.source)
        self.assertEqual(rows,[dict(n=1)])
        self.assertEqual(resume['offset'],60000)
        self.assertEqual(resume['verification'],rules.PREFIX_FORMAT)

    def test_missing_file_identity_never_justifies_a_cache_hit(self):
        self.seed()
        with patch.object(rules,'_identity',return_value=None):
            cache=FileCache('identity','v1')
            self.assertIsNone(cache.get(self.source));self.assertIsNone(cache.grown(self.source))

    def test_replacement_during_prefix_verification_is_not_saved(self):
        cache=FileCache('identity','v1');cache.get(self.source)
        original=rules._prefix
        def replace(path,offset,identity):
            digest=original(path,offset,identity)
            target=self.root/'replacement.jsonl';target.write_bytes(b'b\n'*30000)
            os.replace(str(target),str(path))
            return digest
        with patch.object(rules,'_prefix',side_effect=replace):
            cache.put(self.source,[dict(n=1)],dict(offset=60000))
        self.assertFalse(cache.new)

    def test_prefix_verification_obeys_scan_cancellation(self):
        event=threading.Event();identity=rules._identity(self.source.stat())
        with cancellation(event):
            event.set()
            with self.assertRaises(ScanCancelled):rules._prefix(self.source,60000,identity)

    def test_replacement_after_grown_cannot_mix_prefix_and_tail_in_either_reader(self):
        for agent,parts in ((claude_code,claude_parts),(codex,codex_parts)):
            with self.subTest(agent=agent.__name__):
                first,second=parts()
                source=self.root/(agent.__name__.rsplit('.',1)[-1]+'.jsonl')
                write_jsonl(source,first)
                read=(lambda resume,point:agent._rows(source,resume,point)) if agent is claude_code else \
                     (lambda resume,point:agent._rows(source,agent.decoder()[0],resume,point))
                cache=FileCache(agent.__name__,'rotation');cache.get(source);point={}
                cache.put(source,read(None,point),point);cache.save()
                append(source,second)
                cache=FileCache(agent.__name__,'rotation');self.assertIsNone(cache.get(source))
                resumed=cache.grown(source);self.assertIsNotNone(resumed)
                replacement=source.with_name(source.name+'.replacement')
                # Same shape, different content/identity after verification, before the next open.
                changed=json.loads(json.dumps(first+second).replace('s1','z9').replace('c1','z8'))
                write_jsonl(replacement,changed);os.replace(str(replacement),str(source))
                point={};actual=read(resumed,point);full_point={};expected=read(None,full_point)
                self.assertEqual(actual,expected);self.assertEqual(point,full_point)

    def test_legacy_cache_without_file_identity_is_rebuilt(self):
        self.seed()
        path=FileCache('identity','v1').path
        value=json.loads(path.read_text('utf-8'))
        del value['files'][str(self.source)]['file']
        path.write_text(json.dumps(value),'utf-8')
        self.assertIsNone(FileCache('identity','v1').get(self.source))
