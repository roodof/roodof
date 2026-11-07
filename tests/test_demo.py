"""`pler demo`: invented data that exercises every pilot task, written only into PLER's own demo folder."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler import cli
from pler.dashboard import UsageDashboard
from pler.git_survival import Saved
from pler.demo import MARKER, create
from pler.usage import claude_code, codex, scan


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def view(self, made):
        def reader():
            sessions, sources = scan(made['claude'], made['codex'])
            return sessions, dict(sources, demo=True)
        board = UsageDashboard(reader, survival=Saved(self.root / 'counts'))
        board.refresh()
        board.thread.join(60)
        return board.view(days=0)

    def test_demo_covers_the_pilot_tasks(self):
        value = self.view(create(self.root / 'demo'))
        self.assertTrue(value['demo'])
        self.assertEqual(set(value['agents']), {'claude-code', 'codex'})
        self.assertEqual(value['totals']['sessions'], 8)
        # a data-quality warning to explain, and nothing else unexplained
        self.assertEqual([issue['code'] for issue in value['quality']['issues']], ['cumulative_usage'])
        # a current quota observation with a forecast
        states = {(row['agent'], row['window_minutes']): row['state'] for row in value['outlook']}
        self.assertEqual(states, {('codex', 300): 'fills_before_reset', ('codex', 10080): 'lasts_until_reset'})
        # where usage builds up, and what came of it in Git
        kinds = [item['kind'] for item in value['insights']]
        self.assertEqual(kinds, ['quota', 'concentration', 'git_outcome', 'subsequent_edit', 'tests'])
        tests = value['checks']['test']
        self.assertEqual((tests['sessions'], tests['ended_passed'], tests['ended_failed'], tests['ended_unknown']), (4, 2, 1, 1))
        self.assertEqual(value['checks']['build']['ended_passed'], 1)
        # One added discount line is rewritten by the later Codex commit; the amended-away commit is not measured.
        self.assertEqual(value['git_outcome']['lines'], dict(added=13, kept=12, commits=3, unmeasured=0))
        self.assertEqual((value['reedit']['origin_sessions'],value['reedit']['eligible_sessions'],
                          value['reedit']['matched_sessions']),(8,7,3))
        self.assertTrue(all(m['gap_seconds']>0 for m in value['reedit']['matches']))
        self.assertEqual(value['git_outcome'], dict(value['git_outcome'], sessions=2, commits=4, on_branch=3,
                                                    off_branch=1, unknown=0))
        linked = [s['git_activity'] for s in value['sessions'] if s['git_activity'].get('state') == 'ready']
        self.assertEqual(sorted(a['linked_by'][0] for a in linked), ['edited_files', 'edited_files'])
        # every period filter has something to show
        self.assertGreater(value['totals']['total_tokens'], 0)

    def test_existing_folders_are_replaced_only_when_they_are_a_demo(self):
        other = self.root / 'mine'
        other.mkdir()
        (other / 'keep.txt').write_text('not a demo', 'utf-8')
        with self.assertRaisesRegex(ValueError, 'not_demo'):
            create(other)
        self.assertEqual((other / 'keep.txt').read_text('utf-8'), 'not a demo')
        made = create(self.root / 'demo')
        (made['folder'] / 'stale.txt').write_text('old run', 'utf-8')
        again = create(self.root / 'demo')
        self.assertTrue((again['folder'] / MARKER).is_file())
        self.assertFalse((again['folder'] / 'stale.txt').exists())

    def test_no_local_cache_folder_means_no_demo(self):
        with patch.dict(os.environ, PLER_CACHE_DIR='//server/share/cache'):
            with self.assertRaisesRegex(ValueError, 'no_folder'):
                create()

    def test_cli_demo_reads_only_the_demo_folder_and_marks_the_page(self):
        captured = {}
        def fake_serve(port, browser, lang, dashboard=None, desktop=False):
            captured.update(port=port, browser=browser, dashboard=dashboard)
            return 0
        # The real demo folder is in PLER's cache folder, outside the system temporary folder, whose
        # sessions PLER groups together; this test's own temporary folder must not look like one.
        with patch('pler.usage.projects.tempfile.gettempdir', return_value=str(self.root / 'system-temp')), \
                patch.dict(os.environ, PLER_CACHE_DIR=str(self.root / 'cache')), patch.object(cli, 'serve', fake_serve), \
                patch.object(claude_code, 'roots', side_effect=AssertionError('read the real Claude Code folder')), \
                patch.object(codex, 'roots', side_effect=AssertionError('read the real Codex folder')), \
                patch('pler.usage.claude_quota', side_effect=AssertionError('read the real quota samples')):
            self.assertEqual(cli.main(['demo', '--no-browser', '--port', '0']), 0)
            self.assertEqual((captured['port'], captured['browser']), (0, False))
            board = captured['dashboard']
            board.refresh()
            board.thread.join(60)
            value = board.view(days=0)
        self.assertEqual(value['state'], 'ready')
        self.assertTrue(value['demo'])
        self.assertEqual(value['totals']['sessions'], 8)
        self.assertTrue((self.root / 'cache' / 'demo' / MARKER).is_file())
        self.assertEqual(sorted(p['name'] for p in value['projects']), ['demo/work', 'work/api', 'work/docs', 'work/shop'])

    def test_the_real_view_is_not_marked_as_a_demo(self):
        board = UsageDashboard(lambda: ([], dict(claude_files=0, codex_files=0, skipped=[])))
        board.refresh()
        board.thread.join(10)
        self.assertFalse(board.view(days=0)['demo'])


if __name__ == '__main__':
    unittest.main()
