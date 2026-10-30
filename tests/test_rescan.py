"""The page's refresh reuses its previous sessions only while every input is unchanged."""
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from pler.dashboard import UsageDashboard
from pler.usage import Rescan, archive, claude_code, codex, scan
from pler.usage.records import total
from test_logs import USAGE, claude_reply, write_jsonl


class RescanTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.temp), True)
        self.cache = self.temp / 'cache'
        self.claude = self.temp / 'claude' / 'projects'
        self.codex = self.temp / 'codex' / 'sessions'
        (self.codex.parent / 'archived_sessions').mkdir(parents=True)
        self.codex.mkdir(parents=True)
        env = patch.dict(os.environ, PLER_CACHE_DIR=str(self.cache), CLAUDE_CONFIG_DIR=str(self.claude.parent),
                         CODEX_HOME=str(self.codex.parent))
        env.start(); self.addCleanup(env.stop)
        self.log = self.claude / 'shop' / 's1.jsonl'
        write_jsonl(self.log, [claude_reply('s1', 'm1', 'r1', USAGE, [], '2026-10-20T10:00:00Z')])
        self.memo = Rescan()

    def read(self):
        """Sessions, and whether the logs were merged again."""
        with patch.object(claude_code, 'read', wraps=claude_code.read) as claude, \
                patch.object(codex, 'read', wraps=codex.read) as rollouts:
            sessions, details = self.memo()
        self.assertEqual(claude.called, rollouts.called)
        return sessions, details, claude.called

    def test_unchanged_inputs_return_the_previous_sessions_without_reading(self):
        first, details, merged = self.read()
        self.assertTrue(merged)
        again, fresh, merged = self.read()
        self.assertFalse(merged)
        self.assertIs(again, first)
        self.assertEqual({key: value for key, value in fresh.items() if key != 'observed_at'},
                         {key: value for key, value in details.items() if key != 'observed_at'})
        self.assertEqual(again, scan()[0])  # the same as a full read

    def test_every_input_change_merges_again(self):
        def grow():
            with self.log.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(claude_reply('s1', 'm2', 'r2', USAGE, [], '2026-10-20T10:05:00Z')) + '\n')
        def new_log():
            write_jsonl(self.log.with_name('s2.jsonl'), [claude_reply('s2', 'm3', 'r3', USAGE, [], '2026-10-20T11:00:00Z')])
        def remove_log():
            self.log.with_name('s2.jsonl').unlink()
        def reset_cache():
            archive.reset_cache()
        def retention_off():
            archive.set_retention(False)
        def retention_on():
            archive.set_retention(True)
        def clear_archive():
            archive.clear_archive()
        self.read()
        for change in (grow, new_log, remove_log, reset_cache, retention_off, retention_on, clear_archive):
            with self.subTest(change=change.__name__):
                change()
                sessions, _, merged = self.read()
                self.assertTrue(merged)
                self.assertEqual(sessions, scan()[0])
                self.assertFalse(self.read()[2])

    def test_a_result_is_reused_for_at_most_an_hour(self):
        now = [1000.0]
        with patch('pler.usage.time.monotonic', side_effect=lambda: now[0]):
            self.read()
            now[0] += Rescan.MAX_AGE - 1
            self.assertFalse(self.read()[2])
            now[0] += 2
            self.assertTrue(self.read()[2])

    def test_a_stale_archive_snapshot_is_not_kept(self):
        original = archive.Archive.finish
        def stale(board):
            return dict(original(board), stale_snapshot=True)
        with patch.object(archive.Archive, 'finish', stale):
            self.read()
        self.assertIsNone(self.memo.kept)
        self.assertTrue(self.read()[2])

    def test_the_page_refreshes_through_a_rescan_and_the_terminal_report_does_not(self):
        self.assertIsInstance(UsageDashboard().reader, Rescan)
        sessions, _ = scan()
        self.assertEqual(total(sessions[0].tokens), sum(USAGE.values()))
