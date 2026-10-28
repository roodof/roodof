"""Claude Code status line: only the subscription numbers are kept, Claude Code's settings change only on request,
and the samples give Claude Code the same quota forecast as Codex. Synthetic input only."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from pler import statusline
from pler.dashboard import project_view
from pler.usage.forecast import outlook
from pler.usage.insights import insights

SECRET = 'SECRET-PROMPT-OR-PATH'
NOW = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc)
SOURCE = Path(statusline.__file__).resolve()


def status(five, week, five_reset, week_reset=None, context=37.4):
    """The JSON Claude Code pipes to a status line command, as documented, with private fields around the limits."""
    limits = dict(five_hour=dict(used_percentage=five, resets_at=five_reset))
    if week is not None:
        limits['seven_day'] = dict(used_percentage=week, resets_at=week_reset)
    return dict(session_id=SECRET, transcript_path='C:/Users/x/' + SECRET + '.jsonl', cwd='/work/' + SECRET,
                model=dict(id='claude-opus-5-5', display_name='Opus'), workspace=dict(current_dir='/work/' + SECRET),
                cost=dict(total_cost_usd=1.5), context_window=dict(used_percentage=context), rate_limits=limits)


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.temp), True)

    def test_only_the_limit_numbers_are_kept_and_only_when_they_change(self):
        reset = int(NOW.timestamp()) + 3600
        data = status(23.5, 41.2, reset, reset + 86400)
        found = statusline.limits(data)
        self.assertEqual(found, {'300': [23.5, reset], '10080': [41.2, reset + 86400]})
        self.assertTrue(statusline.record(found, self.temp, now=100))
        self.assertFalse(statusline.record(found, self.temp, now=160))  # unchanged: nothing written
        self.assertTrue(statusline.record(statusline.limits(status(25, 41.2, reset, reset + 86400)), self.temp, now=220))
        stored = (self.temp / statusline.FILE).read_text('utf-8')
        self.assertEqual(len(stored.splitlines()), 2)
        for private in (SECRET, 'cwd', 'session', 'cost', 'Opus', 'context'):
            self.assertNotIn(private, stored)
        self.assertEqual(statusline.line(data, found, 'tr'), 'bağlam %37 · 5 saat %24 · hafta %41')
        self.assertEqual(statusline.line(data, found, 'en'), 'ctx 37% · 5h 24% · week 41%')

    def test_no_limits_no_file_and_a_plain_line(self):
        self.assertEqual(statusline.limits(dict(model=dict(id='x'))), {})
        self.assertFalse(statusline.record({}, self.temp))
        self.assertFalse((self.temp / statusline.FILE).exists())
        self.assertEqual(statusline.line({}, {}), 'PLER')
        broken = status(10, None, 'soon')
        self.assertEqual(statusline.limits(broken), {})

    def test_samples_read_back_for_the_forecast(self):
        reset = int((NOW + timedelta(hours=3)).timestamp())
        start = int((NOW - timedelta(hours=2)).timestamp())
        for minutes, used in ((0, 10.0), (60, 30.0), (120, 50.0)):
            statusline.record({'300': [used, reset]}, self.temp, now=start + minutes * 60)
        (self.temp / statusline.FILE).open('a', encoding='utf-8').write('not json\n')
        samples = statusline.samples(self.temp)
        self.assertEqual([sample[2] for sample in samples], [10.0, 30.0, 50.0])
        (row,) = outlook([], NOW, samples)
        self.assertEqual((row['agent'], row['window_minutes'], row['percent_per_hour'], row['state']),
                         ('claude-code', 300, 20.0, 'fills_before_reset'))
        (note,) = insights([], [row])
        self.assertEqual(note['title'], 'Claude Code 5-hour quota may fill before it resets')
        self.assertIn('Claude Code 5 saatlik kotası', insights([], [row], lang='tr')[0]['title'])

    def test_large_files_keep_only_recent_weeks(self):
        path = self.temp / statusline.FILE
        old = json.dumps(dict(at=1, windows={'300': [1.0, 2]})) + '\n'
        path.write_text(old * (statusline.PRUNE_BYTES // len(old) + 10), 'utf-8')
        statusline.record({'300': [5.0, 99]}, self.temp, now=40 * 86400)
        self.assertEqual(len(path.read_text('utf-8').splitlines()), 1)

    def test_claude_code_can_run_the_installed_command(self):
        # The exact command written to settings.json, run through the shell as Claude Code does.
        reset = int(NOW.timestamp()) + 600
        run = dict(shell=True, capture_output=True, env=dict(os.environ, PLER_CACHE_DIR=str(self.temp), PLER_LANG='en'), timeout=60)
        result = subprocess.run(statusline.command(), input=json.dumps(status(42, 7, reset, reset)).encode(), **run)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.decode('utf-8'), 'ctx 37% · 5h 42% · week 7%')
        self.assertEqual(statusline.samples(self.temp)[0][2], 42.0)
        garbage = subprocess.run(statusline.command(), input=b'{broken', **run)
        self.assertEqual((garbage.returncode, garbage.stdout), (0, b'PLER'))


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.temp), True)
        self.path = self.temp / 'settings.json'

    def quiet(self, function, *args, **options):
        with mock.patch('builtins.print'):
            return function(*args, **options)

    def test_install_asks_keeps_other_settings_and_backs_up(self):
        self.path.write_text(json.dumps(dict(model='opus', permissions=dict(allow=['Read']))), 'utf-8')
        self.assertEqual(self.quiet(statusline.install, self.path, ask=lambda _: 'n', lang='en'), 1)
        self.assertNotIn('statusLine', json.loads(self.path.read_text('utf-8')))
        self.assertEqual(self.quiet(statusline.install, self.path, ask=lambda _: 'yes', lang='en'), 0)
        settings = json.loads(self.path.read_text('utf-8'))
        self.assertEqual((settings['model'], settings['permissions']), ('opus', dict(allow=['Read'])))
        self.assertEqual(settings['statusLine'], dict(type='command', command=statusline.command()))
        self.assertIn(SOURCE.as_posix(), settings['statusLine']['command'])
        self.assertNotIn('statusLine', json.loads((self.temp / 'settings.json.pler-backup').read_text('utf-8')))
        self.assertEqual(self.quiet(statusline.install, self.path, ask=lambda _: self.fail('asked twice')), 0)
        self.assertEqual(self.quiet(statusline.remove, self.path), 0)
        self.assertEqual(json.loads(self.path.read_text('utf-8')), dict(model='opus', permissions=dict(allow=['Read'])))

    def test_another_status_line_or_a_broken_file_is_never_touched(self):
        mine = dict(statusLine=dict(type='command', command='~/.claude/my-line.sh'))
        self.path.write_text(json.dumps(mine), 'utf-8')
        self.assertEqual(self.quiet(statusline.install, self.path, ask=lambda _: self.fail('must not ask')), 1)
        self.assertEqual(self.quiet(statusline.remove, self.path), 0)
        self.assertEqual(json.loads(self.path.read_text('utf-8')), mine)
        self.path.write_text('{"model": ', 'utf-8')
        self.assertEqual(self.quiet(statusline.install, self.path, ask=lambda _: self.fail('must not ask')), 1)
        self.assertEqual(self.path.read_text('utf-8'), '{"model": ')
        self.assertFalse((self.temp / 'settings.json.pler-backup').exists())

    def test_a_missing_settings_file_is_created(self):
        self.assertEqual(self.quiet(statusline.install, self.temp / 'new' / 'settings.json', ask=lambda _: 'evet', lang='tr'), 0)
        self.assertEqual(set(json.loads((self.temp / 'new' / 'settings.json').read_text('utf-8'))), {'statusLine'})


class PageTests(unittest.TestCase):
    def test_the_page_gets_claude_rows_only_from_status_line_samples(self):
        reset = NOW + timedelta(hours=2)
        samples = [(NOW - timedelta(minutes=50), 300, 20.0, reset), (NOW - timedelta(minutes=10), 300, 28.0, reset)]
        without = project_view([], {}, days=0, now=NOW)
        self.assertEqual((without['outlook'], without['claude_statusline']), ([], False))
        value = project_view([], dict(claude_quota=samples), days=0, now=NOW)
        (row,) = value['outlook']
        self.assertEqual((row['agent'], row['used_percent'], value['claude_statusline']), ('claude-code', 28.0, True))
        json.dumps(value)  # the page data stays plain JSON


if __name__ == '__main__':
    unittest.main()
