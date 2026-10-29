"""Budgets cover fallback metadata, compressed tails and warm-cache admission."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler.usage import claude_code,codex,discovery,input_limits,zstd
from pler.usage.xxh64 import digest
from test_logs import USAGE,claude_reply,stored_zstd


class BudgetIntegrationTests(unittest.TestCase):
    def test_partial_live_claude_cannot_replace_admitted_rows_with_an_over_budget_archive(self):
        retained=[claude_code._slim(claude_reply('invented',str(n),str(n),USAGE,[],
                  '2026-10-20T10:00:00Z')) for n in range(20)]
        class Retained:
            def replay(self,*args):return []
            def begin(self,*args):pass
            def rows(self,*args,**kwargs):return retained
            def mark(self,*args):pass
            def observe(self,*args):raise AssertionError('partial source was retained')
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'invented.jsonl';source.write_bytes(b'{}\n')
            issues=[]
            @input_limits.scoped
            def read():return claude_code.read([source],issues,archive=Retained())
            partial=[retained[0],dict(type='pler_file_issue',reason='ReadLimitExceeded')]
            with patch.object(input_limits,'MAX_SCAN_ROWS',3),patch.object(claude_code,'_rows',return_value=partial):
                result=read()
            self.assertEqual(result,[])
            self.assertEqual(issues,[(str(source),'ReadLimitExceeded')])

    def test_late_compressed_checksum_and_tail_errors_survive_a_projection_limit(self):
        rows=[dict(type='session_meta',payload=dict(id='invented')),
              dict(type='turn_context',payload=dict(model='invented')),
              dict(type='ignored',padding='x'*(3*input_limits.CHUNK_BYTES))]
        raw=''.join(json.dumps(row)+'\n' for row in rows).encode('utf-8')
        plain=stored_zstd(raw)
        checked=(plain[:4]+bytes([plain[4]|4])+plain[5:]+(digest(raw)&0xffffffff).to_bytes(4,'little'))
        class Source:
            name='rollout-invented.jsonl.zst'
            def __init__(self,data):self.data=data
            def open(self,*args):return io.BytesIO(self.data)
        decode=zstd.decoder()[0]
        with patch.object(input_limits,'MAX_FILE_ROWS',1):
            projected=codex._rows(Source(checked),decode)
            self.assertEqual(projected[-1],dict(type='pler_incomplete_log',reason='ReadLimitExceeded'))
            for broken in (checked[:-1],checked[:-1]+bytes([checked[-1]^1]),checked+b'junk'):
                with self.subTest(bytes=len(broken)),self.assertRaises(ValueError):
                    codex._rows(Source(broken),decode)

    def test_batched_admission_preserves_exact_size_and_avoids_per_row_encoder_calls(self):
        rows=[dict(n=n,text='\u03bb\\"\n',nested=dict(value=[None,True,1.25])) for n in range(513)]
        expected=sum(len(json.dumps(row,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode('ascii'))
                     for row in rows)
        encode=json.dumps
        @input_limits.scoped
        def read():
            with patch.object(input_limits.json,'dumps',wraps=encode) as encoder:
                input_limits.admit(rows)
            sizes=[len(call.args[0]) for call in encoder.call_args_list]
            self.assertLessEqual(encoder.call_count,8)
            self.assertTrue(all(size<=256 for size in sizes))
            self.assertEqual(input_limits._CURRENT.get()['rows'],len(rows))
            self.assertEqual(input_limits._CURRENT.get()['metadata'],expected)
        with patch.object(input_limits,'MAX_SCAN_METADATA',expected):read()
        @input_limits.scoped
        def reject():
            with self.assertRaises(input_limits.ReadLimitExceeded):input_limits.admit(rows)
            self.assertEqual(input_limits._CURRENT.get()['rows'],0)
            self.assertEqual(input_limits._CURRENT.get()['metadata'],0)
        with patch.object(input_limits,'MAX_SCAN_METADATA',expected-1):reject()

    def test_a_row_count_excess_is_rejected_before_encoding_large_cached_metadata(self):
        @input_limits.scoped
        def read():
            with patch.object(input_limits.json,'dumps',side_effect=AssertionError('over-budget data encoded')):
                with self.assertRaises(input_limits.ReadLimitExceeded):input_limits.admit([dict(n=1),dict(n=2)])
        with patch.object(input_limits,'MAX_SCAN_ROWS',1):read()

    def test_directory_budget_also_bounds_the_discovery_frontier(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for n in range(10):(root/str(n)).mkdir()
            visited=[]
            actual=discovery.os.scandir
            class Counted:
                def __init__(self,path):self.stream=actual(path)
                def __enter__(self):return self
                def __exit__(self,*args):self.stream.close()
                def __iter__(self):
                    for entry in self.stream:
                        visited.append(True)
                        yield entry
            manifest=discovery.Manifest();issues=[]
            @input_limits.scoped
            def read():return discovery.files([root],lambda _:True,issues,manifest=manifest)
            with patch.object(input_limits,'MAX_DIRECTORIES',1),patch.object(discovery.os,'scandir',side_effect=Counted):
                self.assertEqual(read(),[])
            self.assertLessEqual(len(visited),2)
            self.assertFalse(manifest.complete)
            self.assertTrue(any(reason=='ReadLimitExceeded' for _,reason in issues))


if __name__=='__main__':unittest.main()
