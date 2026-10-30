"""Reusing a synthetic snapshot never erases reader failures or indefinitely hides recovery."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler.reporting import quality
from pler.usage import Rescan,claude_code,codex,scan
from test_logs import USAGE,claude_reply,codex_rows,write_jsonl


class RescanSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.claude=self.root/'claude/projects';self.codex=self.root/'codex/sessions'
        self.codex.mkdir(parents=True);(self.codex.parent/'archived_sessions').mkdir()
        write_jsonl(self.claude/'invented/session.jsonl',[
            claude_reply('s','m','r',USAGE,[],'2026-10-20T10:00:00Z')])
        env=patch.dict(os.environ,PLER_CACHE_DIR=str(self.root/'cache'),
                       CLAUDE_CONFIG_DIR=str(self.claude.parent),CODEX_HOME=str(self.codex.parent))
        env.start();self.addCleanup(env.stop)

    def test_unchanged_bad_compressed_source_keeps_incomplete_coverage_on_memo_hit(self):
        (self.codex/'rollout-bad.jsonl.zst').write_bytes(b'invented damaged frame')
        memo=Rescan();sessions,details=memo()
        self.assertEqual(len(sessions),1);self.assertTrue(details['skipped'])
        with patch.object(codex,'read',side_effect=AssertionError('memo should reuse')):
            again,current=memo()
        self.assertIs(again,sessions)
        self.assertEqual(current['skipped'],details['skipped'])
        self.assertFalse(quality(again,current)['tokens_complete'])
        current['skipped'].clear()
        self.assertTrue(memo()[1]['skipped'])

    def test_transient_reader_failure_is_retried_after_the_short_error_ttl(self):
        write_jsonl(self.codex/'rollout-good.jsonl',codex_rows())
        memo=Rescan();now=[1000.0]
        with patch('pler.usage.time.monotonic',side_effect=lambda:now[0]):
            with patch.object(codex,'_rows',side_effect=PermissionError('invented private error')):
                _,details=memo()
            self.assertTrue(details['skipped'])
            now[0]+=Rescan.ERROR_MAX_AGE-1
            with patch.object(codex,'read',side_effect=AssertionError('reuse before error ttl')):
                self.assertEqual(memo()[1]['skipped'],details['skipped'])
            now[0]+=2
            with patch.object(codex,'read',wraps=codex.read) as reader:
                recovered,current=memo()
            self.assertTrue(reader.called)
            self.assertFalse(current['skipped'])
            self.assertEqual(len(recovered),2)

    def test_a_damaged_file_does_not_disappear_from_a_public_quality_report(self):
        (self.codex/'rollout-bad.jsonl').write_bytes(b'{unfinished\n')
        memo=Rescan()
        for _ in range(2):
            sessions,sources=memo()
            value=quality(sessions,sources)
            self.assertFalse(value['tokens_complete'])
            self.assertIn('invalid_records',[item['code'] for item in value['issues']])
