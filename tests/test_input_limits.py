"""Bounded synthetic input preserves good usage and makes excluded coverage explicit."""
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from pler.runtime import ScanCancelled,cancellation
from pler.usage import archive,claude_code,codex,discovery,input_limits,scan
from pler.usage.cache import FileCache
from pler.usage.records import json_row,total
from pler.reporting import quality
from test_logs import USAGE,claude_reply,codex_rows,write_jsonl


class InputLimitsTests(unittest.TestCase):
    def test_long_line_is_drained_once_and_following_utf8_line_survives(self):
        with patch.object(input_limits,'MAX_LINE_BYTES',5):
            lines=list(input_limits.lines([b'123',b'45678',b'90\nok\r\n',b'\xce',b'\xbb']))
        self.assertEqual(lines,[None,b'ok\r','\u03bb'.encode('utf-8')])

    def test_read_requests_do_not_cross_file_limit_by_more_than_one_byte(self):
        reads=[]
        class Stream(io.BytesIO):
            def read(self,size=-1):reads.append(size);return super().read(size)
        with self.assertRaises(input_limits.ReadLimitExceeded):list(input_limits.chunks(Stream(b'x'*100),7))
        self.assertEqual(reads,[8])

    def test_deep_json_is_rejected_consistently_but_braces_inside_strings_are_not_depth(self):
        with self.assertRaises(ValueError):json_row('{"extra":'+'['*300+'0'+']'*300+'}')
        text='[{'*400+'\\"'
        self.assertEqual(json_row(json.dumps(dict(text=text))),dict(text=text))
        # Escaped quotes inside a string cannot end it early and expose its brackets as structure.
        tricky=dict(a='\\"'+'{'*300,b=[[1]])
        self.assertEqual(json_row(json.dumps(tricky)),tricky)
        with self.assertRaises(ValueError):json_row('{"s":"]]]]","x":'+'{"y":'*300+'0'+'}'*300+'}')

    def test_deep_claude_row_keeps_both_good_replies_and_no_transcript(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'session.jsonl'
            good=[claude_reply('s',str(n),str(n),USAGE,[],'2026-10-20T10:00:00Z') for n in (1,2)]
            text=json.dumps(good[0])+'\n'+ '{"secret":'+'['*1500+'0'+']'*1500+'}\n'+json.dumps(good[1])+'\n'
            path.write_text(text,'utf-8');issues=[]
            session,=claude_code.read([path],issues)
            self.assertEqual(session.calls,2)
            self.assertEqual(total(session.tokens),2520)
            self.assertFalse(session.tokens_complete)
            self.assertEqual(issues,[(str(path),'MalformedRows')])
            self.assertNotIn('secret',json.dumps(claude_code._rows(path)))

    def test_codex_plain_reader_is_streamed_and_oversize_row_does_not_hide_good_usage(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'rollout-s.jsonl'
            write_jsonl(path,codex_rows())
            with path.open('ab') as stream:stream.write(b'{"ignored":"'+b'x'*3000+b'"}\n')
            with patch.object(input_limits,'MAX_LINE_BYTES',2000),patch.object(Path,'read_bytes',side_effect=AssertionError('whole-file read')):
                sessions,issues=codex.read([path])
            self.assertEqual(total(sessions[0].tokens),2100)
            self.assertIn((str(path),'ReadLimitExceeded'),issues)
            self.assertFalse(sessions[0].tokens_complete)

    def test_metadata_budget_marks_partial_projection_and_survives_archive_sanitization(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'rollout-s.jsonl';write_jsonl(path,codex_rows())
            with patch.object(input_limits,'MAX_FILE_ROWS',2):rows=codex._rows(path,lambda data:data)
            self.assertEqual(rows[-1],dict(type='pler_incomplete_log',reason='ReadLimitExceeded'))
            self.assertEqual(archive.sanitize('codex',rows)[-1],rows[-1])

    def test_discovery_limit_never_claims_a_whole_root_was_enumerated(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for n in range(3):(root/('%s.jsonl'%n)).write_bytes(b'{}\n')
            manifest=discovery.Manifest();issues=[]
            @input_limits.scoped
            def read():return discovery.files([root],lambda name:name.endswith('.jsonl'),issues,manifest=manifest)
            with patch.object(input_limits,'MAX_FILES',1):found=read()
            self.assertEqual(len(found),1)
            self.assertFalse(manifest.complete)
            self.assertTrue(any(reason=='ReadLimitExceeded' for _,reason in issues))

    def test_global_metadata_budget_counts_cached_or_archived_rows_too(self):
        @input_limits.scoped
        def run():
            input_limits.admit([dict(n=1)])
            with self.assertRaises(input_limits.ReadLimitExceeded):input_limits.admit([dict(n=2)])
        with patch.object(input_limits,'MAX_SCAN_ROWS',1):run()
        # Scope does not leak to a later invocation.
        with patch.object(input_limits,'MAX_SCAN_ROWS',1):run()

    def test_source_budget_and_cancel_are_enforced_between_reads(self):
        @input_limits.scoped
        def run():
            first=input_limits.Source(io.BytesIO(b'1234'))
            self.assertEqual(first.read(4),b'1234')
            with self.assertRaises(input_limits.ReadLimitExceeded):input_limits.Source(io.BytesIO(b'56')).read(4)
        with patch.object(input_limits,'MAX_SCAN_SOURCE_BYTES',5):run()
        event=threading.Event();event.set()
        with self.assertRaises(ScanCancelled),cancellation(event):list(input_limits.chunks(io.BytesIO(b'abc'),10))

    def test_oversized_disposable_cache_is_a_miss_without_opening_it(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,PLER_CACHE_DIR=folder):
            (Path(folder)/'codex.json').write_bytes(b' '*65)
            with patch.object(input_limits,'MAX_CACHE_BYTES',64),patch.object(Path,'open',side_effect=AssertionError('oversize cache opened')):
                cache=FileCache('codex','invented')
            self.assertEqual(cache.old,{})

    def test_read_limit_is_explicit_in_both_languages(self):
        for lang in ('en','tr'):
            value=quality([],dict(skipped=[('invented','ReadLimitExceeded')]),lang)
            self.assertFalse(value['tokens_complete'])
            self.assertIn('read_limits',[row['code'] for row in value['issues']])
