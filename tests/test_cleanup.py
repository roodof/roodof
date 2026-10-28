"""Professional-use regressions: ownership, stale meters, invalid numbers and missing coverage."""
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler import statusline
from pler.dashboard import project_view
from pler.usage import main as report, render, scan
from pler.usage.forecast import outlook
from pler.usage.insights import insights
from pler.usage.records import Session
from pler.usage.summary import summarize
from test_logs import USAGE, claude_reply, codex_rows, write_jsonl

NOW = datetime(2026, 10, 26, 12, tzinfo=timezone.utc)


class SettingsSafetyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'settings.json'

    def test_similar_command_and_modified_plers_are_never_replaced_or_removed(self):
        for line in (dict(type='command', command='python C:/tools/pler-statusline-wrapper.py'),
                     dict(type='command', command=statusline.command()+' --custom'),
                     dict(type='command', command=statusline.command(), padding=4)):
            original = json.dumps(dict(statusLine=line, model='keep'))
            self.path.write_text(original, 'utf-8')
            with self.subTest(line=line), redirect_stdout(io.StringIO()):
                self.assertEqual(statusline.install(self.path, ask=lambda _: self.fail('must not ask'), lang='en'), 1)
                self.assertEqual(statusline.remove(self.path, lang='en'), 0)
            self.assertEqual(self.path.read_text('utf-8'), original)
            self.assertFalse(self.path.with_name('settings.json.pler-backup').exists())

    def test_settings_changed_during_confirmation_are_preserved(self):
        for existed in (True, False):
            if self.path.exists():
                self.path.unlink()
            if existed:
                self.path.write_text('{"model":"original"}', 'utf-8')
            newer = '{"model":"changed-elsewhere","permissions":{"keep":true}}'
            def approve(_):
                self.path.write_text(newer, 'utf-8')
                return 'yes'
            shown = io.StringIO()
            with self.subTest(existed=existed), redirect_stdout(shown):
                self.assertEqual(statusline.install(self.path, ask=approve, lang='en'), 1)
            self.assertEqual(self.path.read_text('utf-8'), newer)
            self.assertIn('Nothing was overwritten', shown.getvalue())

    def test_write_failure_has_a_useful_error_and_keeps_original_and_backup(self):
        original = b'{"model":"keep"}'
        self.path.write_bytes(original)
        shown = io.StringIO()
        with patch('pler.statusline.os.replace', side_effect=PermissionError('PRIVATE')), redirect_stdout(shown):
            self.assertEqual(statusline.install(self.path, ask=lambda _: 'yes', lang='en'), 1)
        self.assertIn('could not be saved', shown.getvalue())
        self.assertNotIn('PRIVATE', shown.getvalue())
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(self.path.with_name('settings.json.pler-backup').read_bytes(), original)
        self.assertEqual(list(self.path.parent.glob('*.tmp')), [])


class BadMeterTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.folder = Path(self.directory.name)

    def test_status_line_rejects_invalid_percentages_without_writing_or_crashing(self):
        for invalid in (float('nan'), float('inf'), -1, 101, True, '20', 10**1000):
            data = dict(context_window=dict(used_percentage=invalid),
                        rate_limits=dict(five_hour=dict(used_percentage=invalid, resets_at=100)))
            with self.subTest(invalid=str(invalid)[:20]):
                self.assertEqual(statusline.limits(data), {})
                self.assertEqual(statusline.line(data, {}, 'en'), 'PLER')
                self.assertFalse(statusline.record({'300': [invalid, 100]}, self.folder))
        self.assertFalse((self.folder/statusline.FILE).exists())
        self.assertEqual(statusline.line(dict(context_window=dict(used_percentage=0)), {}, 'en'), 'ctx 0%')

    def test_invalid_reset_or_window_does_not_hide_an_independent_valid_window(self):
        for invalid in (float('nan'), float('inf'), -1, True, 10**1000):
            data = dict(rate_limits=dict(five_hour=dict(used_percentage=20, resets_at=invalid),
                                         seven_day=dict(used_percentage=40, resets_at=1000)))
            self.assertEqual(statusline.limits(data), {'10080': [40.0, 1000]})

    def test_corrupt_cache_lines_are_skipped_and_valid_windows_survive(self):
        good = dict(at=int(NOW.timestamp()), windows={'300': [float('nan'), 99], '10080': [50, int(NOW.timestamp())+3600]})
        path = self.folder/statusline.FILE
        path.write_bytes(b'\xffbroken\n'+json.dumps(good).encode()+b'\n'+json.dumps(dict(at=True, windows={'300':[10,99]})).encode())
        samples = statusline.samples(self.folder)
        self.assertEqual(len(samples), 1)
        self.assertEqual((samples[0][1], samples[0][2]), (10080, 50.0))
        json.dumps(project_view([],dict(claude_quota=samples),days=0,now=NOW),allow_nan=False)

    def test_one_bad_line_does_not_prevent_pruning(self):
        path = self.folder/statusline.FILE
        old = json.dumps(dict(at=1, windows={'300':[1,2]}))+'\n'
        path.write_text('bad\n'+old*(statusline.PRUNE_BYTES//len(old)+10), 'utf-8')
        self.assertTrue(statusline.record({'300':[5,99]},self.folder,now=40*86400))
        rows = path.read_text('utf-8').splitlines()
        self.assertEqual(len(rows),1)
        self.assertEqual(json.loads(rows[0])['windows'],{'300':[5.0,99]})

    def test_codex_invalid_meter_values_never_reach_public_json(self):
        rows = codex_rows()
        for row in rows:
            limits = row.get('payload',{}).get('rate_limits',{})
            for window in ('primary','secondary'):
                if window in limits:
                    limits[window]['used_percent'] = float('nan') if window=='primary' else True
        write_jsonl(self.folder/'rollout-test.jsonl', rows)
        sessions,sources = scan([], [self.folder])
        self.assertEqual(sessions[0].quota, [])
        json.dumps(project_view(sessions,sources,days=0),allow_nan=False)


class ForecastTrustTests(unittest.TestCase):
    def session(self, samples):
        return Session('codex','q','synthetic',quota=samples)

    def test_old_short_sample_is_unknown_not_a_current_forecast(self):
        reset = NOW+timedelta(hours=3)
        row, = outlook([self.session([(NOW-timedelta(hours=2),300,20,reset),
                                      (NOW-timedelta(hours=1),300,60,reset)])],NOW)
        self.assertEqual(row['state'],'stale')
        self.assertNotIn('full_at',row)
        self.assertEqual(insights([], [row]), [])

    def test_age_policy_and_reset_take_precedence_over_old_full_percentage(self):
        for minutes,age in ((300,timedelta(minutes=30)),(10080,timedelta(hours=24))):
            reset = NOW+timedelta(days=2)
            current, = outlook([self.session([(NOW-age,minutes,100,reset)])],NOW)
            old, = outlook([self.session([(NOW-age-timedelta(seconds=1),minutes,100,reset)])],NOW)
            self.assertEqual((current['state'],old['state']),('full','stale'))
        reset, = outlook([self.session([(NOW-timedelta(hours=2),300,100,NOW-timedelta(seconds=1))])],NOW)
        self.assertEqual(reset['state'],'reset')

    def test_forecast_that_would_already_have_happened_is_withheld(self):
        reset = NOW+timedelta(hours=3)
        row, = outlook([self.session([(NOW-timedelta(minutes=40),300,20,reset),
                                      (NOW-timedelta(minutes=10),300,99,reset)])],NOW)
        self.assertEqual(row['state'],'stale')
        self.assertNotIn('full_at',row)

    def test_invalid_or_future_samples_do_not_create_a_meter(self):
        reset = NOW+timedelta(hours=3)
        samples = [(NOW,300,float('nan'),reset),(NOW,300,-1,reset),(NOW,True,30,reset),
                   (NOW,300,True,reset),(NOW+timedelta(seconds=1),300,30,reset)]
        self.assertEqual(outlook([self.session(samples)],NOW),[])

    def test_terminal_also_labels_old_codex_and_claude_samples_as_old(self):
        reset = NOW+timedelta(hours=3)
        sample = (NOW-timedelta(hours=1),300,20,reset)
        session = self.session([sample])
        windows = outlook([session],NOW,[sample])
        text = render(summarize([session]),dict(claude_files=0,codex_files=1,skipped=[]),windows=windows)
        self.assertEqual(text.count('current level unknown (old data)'),2)


class CoverageTests(unittest.TestCase):
    def test_terminal_period_is_not_presented_as_daily_spending(self):
        text=render(summarize([]),dict(days=7,claude_files=0,codex_files=0,skipped=[]))
        self.assertIn('Sessions active in the last 7 days',text)
        self.assertIn('Tokens cover those whole sessions',text)

    def test_terminal_json_does_not_export_partial_price_equivalents(self):
        rows=[Session('claude-code','s','synthetic',reported_cost_usd=999)]
        sources=dict(claude_files=1,codex_files=0,skipped=[],claude_quota=[])
        shown=io.StringIO()
        with patch('pler.usage.scan',return_value=(rows,sources)),redirect_stdout(shown):
            report(['--days','0','--json','--sessions','--lang','en'])
        value=json.loads(shown.getvalue())
        self.assertNotIn('reported_cost_usd',value)
        self.assertNotIn('reported_cost_usd',value['sessions'][0])

    def test_unreadable_claude_file_is_reported_without_hiding_the_other_file_or_leaking_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            blocked = root/'PRIVATE-FILE-NAME.jsonl'
            good = root/'good.jsonl'
            row = claude_reply('s1','m1','r1',USAGE,[],'2026-10-26T10:00:00Z')
            write_jsonl(blocked,[row])
            write_jsonl(good,[row])
            real_open = open
            def guarded(name,*args,**kwargs):
                if str(name)==str(blocked):
                    raise PermissionError('PRIVATE-FILE-NAME')
                return real_open(name,*args,**kwargs)
            with patch('builtins.open',guarded):
                sessions,sources = scan([root],[])
            self.assertEqual((len(sessions),len(sources['skipped'])),(1,1))
            data = project_view(sessions,sources,days=0)
            self.assertEqual(data['sources']['unreadable'],1)
            self.assertNotIn('PRIVATE-FILE-NAME',json.dumps(data))
            self.assertIn('1 log file',render(summarize(sessions),sources))


if __name__=='__main__':
    unittest.main()
