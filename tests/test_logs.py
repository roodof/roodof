"""Local agent logs -> one session shape. Synthetic logs only: no real transcript is read or copied here.

fixtures/zstd was made with the reference zstd program 1.5.2 from the samples defined below."""
import contextlib
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from pler.usage import claude_code, codex, main, render, scan
from pler.usage import unzstd, zstd as zstd_module
from pler.usage.records import total
from pler.usage.summary import quota_burn, summarize

SECRET = 'SECRET-PROMPT-TEXT'


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')


def claude_reply(session, message_id, request, usage, blocks, at, **extra):
    return dict(type='assistant', sessionId=session, requestId=request, timestamp=at, cwd='/work/shop', gitBranch='main',
                version='2.1.300', message=dict(id=message_id, model='claude-opus-5-5', role='assistant', content=blocks,
                                                usage=usage), **extra)


USAGE = dict(input_tokens=10, cache_read_input_tokens=1000, cache_creation_input_tokens=200, output_tokens=50)


class ClaudeCodeTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.temp), True)
        self.projects = self.temp / 'projects'

    def test_a_reply_split_over_lines_and_copied_into_a_resumed_file_is_counted_once(self):
        lines = [
            dict(type='user', sessionId='s1', timestamp='2026-10-20T10:00:00Z', cwd='/work/shop',
                 message=dict(role='user', content=SECRET)),
            claude_reply('s1', 'm1', 'r1', USAGE, [dict(type='text', text=SECRET)], '2026-10-20T10:00:05Z'),
            claude_reply('s1', 'm1', 'r1', USAGE, [dict(type='tool_use', name='Edit', id='t1',
                                                         input=dict(file_path='/work/shop/cart.c', old_string=SECRET))],
                         '2026-10-20T10:00:06Z'),
            claude_reply('s1', 'm2', 'r2', dict(USAGE, output_tokens=5), [dict(type='tool_use', name='Bash', id='t2',
                                                                                   input=dict(command='echo ' + SECRET))],
                         '2026-10-20T10:01:00Z'),
            dict(type='user', sessionId='s1', timestamp='2026-10-20T10:01:01Z',
                 message=dict(role='user', content=[dict(type='tool_result', tool_use_id='t2', content=SECRET)])),
            claude_reply('s1', 'm3', 'r3', dict(input_tokens=0, output_tokens=0), [dict(type='text', text='x')],
                         '2026-10-20T10:02:00Z', isApiErrorMessage=True),
        ]
        write_jsonl(self.projects / 'shop' / 's1.jsonl', lines)
        # a resumed session repeats the earlier replies in its own file
        write_jsonl(self.projects / 'shop' / 's2.jsonl', [dict(line, sessionId='s2') for line in lines[:3]])
        sessions = {s.session_id: s for s in claude_code.read(claude_code.files([self.projects]))}
        first = sessions['s1']
        self.assertEqual(first.calls, 3)
        self.assertEqual(first.tokens, dict(input=20, cache_read=2000, cache_write=400, output=55, reasoning=0))
        self.assertEqual(total(first.tokens), 2475)
        self.assertEqual((first.prompts, first.errors, first.project, first.branch), (1, 1, '/work/shop', 'main'))
        self.assertEqual(first.tools, {'Edit': 1, 'Bash': 1})
        self.assertEqual(first.files_edited, {'/work/shop/cart.c'})
        self.assertEqual(sessions['s2'].calls, 0)  # nothing counted twice
        for session in sessions.values():
            self.assertNotIn(SECRET, json.dumps(session.as_dict()))

    def test_the_largest_copy_of_a_streamed_reply_is_kept(self):
        write_jsonl(self.projects / 'p' / 's.jsonl', [
            claude_reply('s', 'm', 'r', dict(USAGE, output_tokens=1), [], '2026-10-20T10:00:00Z'),
            claude_reply('s', 'm', 'r', dict(USAGE, output_tokens=90), [], '2026-10-20T10:00:01Z')])
        session, = claude_code.read(claude_code.files([self.projects]))
        self.assertEqual((session.calls, session.tokens['output']), (1, 90))

    def test_config_dir_variable_selects_the_folders(self):
        (self.temp / 'a' / 'projects').mkdir(parents=True)
        with mock.patch.dict('os.environ', CLAUDE_CONFIG_DIR=str(self.temp / 'a') + ',' + str(self.temp / 'missing')):
            self.assertEqual(claude_code.roots(), [self.temp / 'a' / 'projects'])


def codex_rows(session_id='c1'):
    limits = lambda primary, weekly: dict(plan_type='plus', primary=dict(used_percent=primary, window_minutes=300, resets_at=1),
                                          secondary=dict(used_percent=weekly, window_minutes=10080, resets_at=2))
    usage = dict(input_tokens=1000, cached_input_tokens=800, cache_write_input_tokens=0, output_tokens=60,
                 reasoning_output_tokens=20, total_tokens=1060)
    return [
        dict(timestamp='2026-10-21T09:00:00Z', type='session_meta',
             payload=dict(id=session_id, cwd='/work/engine', cli_version='0.163.0', originator='Codex Desktop',
                          base_instructions=SECRET)),
        dict(timestamp='2026-10-21T09:00:01Z', type='turn_context', payload=dict(model='gpt-6.1-sol', effort='low', cwd='/work/engine')),
        dict(timestamp='2026-10-21T09:00:01Z', type='event_msg', payload=dict(type='task_started')),
        dict(timestamp='2026-10-21T09:00:02Z', type='response_item',
             payload=dict(type='function_call', name='exec', arguments=json.dumps(dict(cmd=SECRET)))),
        dict(timestamp='2026-10-21T09:00:03Z', type='token_usage_record', payload=dict(response_id='a', usage=usage)),
        dict(timestamp='2026-10-21T09:00:03Z', type='token_usage_record', payload=dict(response_id='a', usage=usage)),  # repeated
        dict(timestamp='2026-10-21T09:00:04Z', type='event_msg', payload=dict(type='token_count', info=None, rate_limits=limits(10.0, 40.0))),
        dict(timestamp='2026-10-21T09:00:05Z', type='token_usage_record', payload=dict(response_id='b', usage=dict(usage, output_tokens=40))),
        dict(timestamp='2026-10-21T09:00:06Z', type='event_msg', payload=dict(type='token_count', info=None, rate_limits=limits(12.0, 41.0))),
        dict(timestamp='2026-10-21T14:10:00Z', type='event_msg', payload=dict(type='token_count', info=None, rate_limits=limits(3.0, 41.0))),
        dict(timestamp='2026-10-21T14:11:00Z', type='event_msg', payload=dict(type='token_count', info=None, rate_limits=limits(5.0, 42.5))),
        dict(timestamp='2026-10-21T14:12:00Z', type='event_msg', payload=dict(type='task_complete', duration_ms=4000, error=dict(x=1))),
        dict(timestamp='2026-10-21T14:12:01Z', type='event_msg', payload=dict(type='turn_aborted')),
        dict(timestamp='2026-10-21T14:12:02Z', type='response_item', payload=dict(type='message', content=[dict(text=SECRET)])),
    ]


def stored_zstd(data):
    """A valid zstd frame that stores `data` in raw blocks: compressed logs without needing a compressor."""
    frame = (0xFD2FB528).to_bytes(4, 'little') + bytes([0xE0]) + len(data).to_bytes(8, 'little')
    chunks = [data[i:i + 131072] for i in range(0, len(data), 131072)] or [b'']
    for index, chunk in enumerate(chunks):
        frame += ((len(chunk) << 3) | (index == len(chunks) - 1)).to_bytes(3, 'little') + chunk
    return frame


class CodexTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.temp), True)
        self.sessions = self.temp / 'sessions' / '2026' / '10' / '21'

    def test_per_call_records_are_made_disjoint_and_the_quota_meter_is_sampled(self):
        write_jsonl(self.sessions / 'rollout-2026-10-21T09-00-00-c1.jsonl', codex_rows())
        (session,), skipped = codex.read(codex.files([self.temp / 'sessions']))
        self.assertEqual(skipped, [])
        self.assertEqual((session.session_id, session.project, session.client_version), ('c1', '/work/engine', '0.163.0'))
        self.assertEqual(session.calls, 2)  # response 'a' counted once
        self.assertEqual(session.tokens, dict(input=400, cache_read=1600, cache_write=0, output=100, reasoning=40))
        self.assertEqual(session.models, {'gpt-6.1-sol': 2})
        self.assertEqual(session.model_tokens, {'gpt-6.1-sol': 2100})
        self.assertEqual((session.prompts, session.errors, session.aborted, session.active_ms), (1, 1, 1, 4000))
        self.assertEqual(session.tools, {'exec': 1})
        self.assertEqual(session.quota_plan, 'plus')
        self.assertEqual(quota_burn(session), {300: 4.0, 10080: 2.5})  # 10->12, reset, 3->5
        self.assertNotIn(SECRET, json.dumps(session.as_dict()))

    def test_older_logs_fall_back_to_the_cumulative_total(self):
        rows = [r for r in codex_rows() if r['type'] != 'token_usage_record']
        rows.append(dict(timestamp='2026-10-21T15:00:00Z', type='event_msg', payload=dict(type='token_count', info=dict(
            total_token_usage=dict(input_tokens=500, cached_input_tokens=100, cache_write_input_tokens=0, output_tokens=30,
                                   reasoning_output_tokens=0, total_tokens=530)), rate_limits=None)))
        write_jsonl(self.sessions / 'rollout-old.jsonl', rows)
        (session,), _ = codex.read(codex.files([self.temp / 'sessions']))
        self.assertEqual((session.calls, total(session.tokens)), (0, 530))
        self.assertTrue(any('cumulative' in note for note in session.notes))

    def test_compressed_rollouts_are_read_or_listed_as_skipped(self):
        plain = self.temp / 'plain.jsonl'
        write_jsonl(plain, codex_rows())
        target = self.sessions / 'rollout-zipped.jsonl.zst'
        target.parent.mkdir(parents=True)
        target.write_bytes(stored_zstd(plain.read_bytes()))
        (session,), skipped = codex.read(codex.files([self.temp / 'sessions']))
        self.assertEqual((session.calls, skipped), (2, []))
        with mock.patch.object(codex, 'decoder', return_value=(unzstd.decompress, 'plain python')):
            (again,), skipped = codex.read(codex.files([self.temp / 'sessions']))
        self.assertEqual((again.as_dict(), skipped), (session.as_dict(), []))
        target.write_bytes(target.read_bytes()[:-9])
        sessions, skipped = codex.read(codex.files([self.temp / 'sessions']))
        self.assertEqual((sessions, len(skipped)), ([], 1))

    def test_unchanged_rollouts_come_from_the_cache_which_holds_no_text(self):
        rollout = self.sessions / 'rollout-2026-10-21T09-00-00-c1.jsonl'
        write_jsonl(rollout, codex_rows())
        environment = dict(CODEX_HOME=str(self.temp), CLAUDE_CONFIG_DIR=str(self.temp / 'no-claude'),
                           PLER_CACHE_DIR=str(self.temp / 'cache'))
        with mock.patch.dict(os.environ, environment):
            (first,), _ = scan()
            with mock.patch.object(codex, '_rows', side_effect=AssertionError('read again')):
                (second,), _ = scan()
            self.assertEqual(second.as_dict(), first.as_dict())
            stored = (self.temp / 'cache' / 'codex.json').read_text('utf-8')
            self.assertNotIn(SECRET, stored)
            self.assertNotIn('base_instructions', stored)
            write_jsonl(rollout, codex_rows() + [dict(timestamp='2026-10-21T16:00:00Z', type='event_msg',
                                                       payload=dict(type='task_started'))])
            (third,), _ = scan()
        self.assertEqual(third.prompts, first.prompts + 1)
        self.assertEqual(first.ended.isoformat(), '2026-10-21T14:12:02+00:00')  # a dropped row still moves the end


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.temp), True)
        write_jsonl(self.temp / 'claude' / 'shop' / 's1.jsonl',
                    [claude_reply('s1', 'm1', 'r1', USAGE, [], '2026-10-20T10:00:05Z',
                                  quotaLimits=dict(status='rejected', rateLimitType='five_hour'))])
        write_jsonl(self.temp / 'codex' / '2026' / 'rollout-c1.jsonl', codex_rows())

    def test_totals_add_up_across_agents_and_render_in_plain_turkish(self):
        sessions, sources = scan([self.temp / 'claude'], [self.temp / 'codex'])
        summary = summarize(sessions)
        self.assertEqual(summary['totals']['total_tokens'], 1260 + 2100)
        self.assertEqual(sorted(summary['agents']), ['claude-code', 'codex'])
        self.assertEqual(summary['agents']['codex']['cache_read_share'], 1600 / 2000)
        self.assertEqual(summary['quota']['plan'], 'plus')
        self.assertEqual([w['used_percent'] for w in summary['quota']['latest']], [5.0, 42.5])
        self.assertEqual(summary['claude_limit_events'], {'rejected': 1})
        self.assertEqual(summary['model_calls'], 0)
        text = render(summary, dict(sources, days=0), lang='tr')
        for expected in ('Bütün kayıtlar', 'Toplam: 3,4 bin token', '%77 kadarı önbellekten', 'önbellek dışı: 760 token',
                         'Claude Code', 'Codex', 'plan: plus', '5 saatlik kota: %5 dolu', 'haftalık kota: %42,5 dolu',
                         'kota sınırına 1 kez', 'model çağrısı yok', 'pler statusline --install'):
            self.assertIn(expected, text)
        text = render(summary, dict(sources, days=0))
        for expected in ('All records', 'Total: 3.4 thousand tokens', '77% of it is context read again from the cache',
                         'outside the cache: 760 tokens', 'plan: plus', '5-hour quota: 5% used', 'weekly quota: 42.5% used',
                         'hit its quota limit 1 time.', '1 session ·', '2 sessions', 'Read: 1 Claude Code file, 1 Codex file.',
                         'no model calls', 'pler statusline --install'):
            self.assertIn(expected, text)
        self.assertNotIn('ı', text)  # no Turkish left in the English report

    def test_the_period_filter_uses_the_session_end(self):
        sessions, _ = scan([self.temp / 'claude'], [self.temp / 'codex'])
        from datetime import datetime, timezone
        summary = summarize(sessions, since=datetime(2026, 10, 21, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(list(summary['agents']), ['codex'])

    def test_command_line_reads_the_given_folders_without_a_model(self):
        output = io.StringIO()
        with mock.patch('subprocess.Popen', side_effect=AssertionError('no process')), contextlib.redirect_stdout(output):
            main(['--days', '0', '--json', '--sessions', '--claude-dir', str(self.temp / 'claude'),
                  '--codex-dir', str(self.temp / 'codex')])
        value = json.loads(output.getvalue())
        self.assertEqual((value['totals']['sessions'], value['sources']['codex_files'], len(value['sessions'])), (2, 1, 2))
        self.assertNotIn(SECRET, output.getvalue())


class ProjectRootTests(unittest.TestCase):
    def test_subfolders_join_their_repository_and_spellings_join_one_project(self):
        from pler.usage.projects import ProjectRoots
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / 'home'
            repo = home / 'Desktop' / 'Shop'
            (repo / '.git').mkdir(parents=True)
            (repo / 'panel').mkdir()
            (home / 'loose').mkdir()
            roots = ProjectRoots(home, Path(temp) / 'tmp')
            self.assertEqual(roots.root(str(repo / 'panel')), os.path.normpath(str(repo)))
            self.assertEqual(roots.root(str(repo) + os.sep), os.path.normpath(str(repo)))
            if os.name == 'nt':  # Windows paths are case-insensitive
                self.assertEqual(roots.root(str(repo).lower()), os.path.normpath(str(repo)))
            self.assertEqual(roots.root(str(home / 'loose')), os.path.normpath(str(home / 'loose')))
            self.assertEqual(roots.root(str(home / 'gone' / 'x')), os.path.normpath(str(home / 'gone' / 'x')))

    def test_a_repository_at_home_never_swallows_projects(self):
        from pler.usage.projects import ProjectRoots
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / 'home'
            (home / '.git').mkdir(parents=True)  # a dotfiles repository
            (home / 'work').mkdir()
            self.assertEqual(ProjectRoots(home, Path(temp) / 'tmp').root(str(home / 'work')), os.path.normpath(str(home / 'work')))

    def test_temporary_folders_form_one_group_and_home_and_temp_are_named(self):
        from pler.usage.projects import ProjectRoots, label
        with tempfile.TemporaryDirectory() as temp:
            home, scratch = Path(temp) / 'home', Path(temp) / 'tmp'
            (scratch / 'run-1' / 'project' / '.git').mkdir(parents=True)
            roots = ProjectRoots(home, scratch)
            for folder in (scratch / 'run-1' / 'project', scratch / 'run-2', scratch):
                self.assertEqual(roots.root(str(folder)), os.path.normpath(str(scratch)))
            self.assertEqual(roots.root(str(Path(temp) / 'tmpfiles')), os.path.normpath(str(Path(temp) / 'tmpfiles')))
            self.assertEqual(label(str(scratch), home, scratch), 'Temporary folders')
            self.assertEqual(label(str(home), home, scratch, lang='tr'), 'Ev klasörü (proje dışı)')
            self.assertEqual(label(str(home / 'Desktop' / 'Shop'), home, scratch), 'Desktop/Shop')


class OutlookTests(unittest.TestCase):
    NOW = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc)

    def session(self, samples):
        from pler.usage.records import Session
        return Session('codex', 'q', 'x', quota=samples)

    def test_short_windows_use_the_current_pace_and_warn_before_reset(self):
        from pler.usage.forecast import outlook
        reset = self.NOW + timedelta(hours=3)
        old = self.NOW - timedelta(hours=6)
        rows = outlook([self.session([(old, 300, 90.0, old + timedelta(hours=1)),  # an earlier window is ignored
                                      (self.NOW - timedelta(hours=1), 300, 40.0, reset),
                                      (self.NOW, 300, 60.0, reset)])], self.NOW)
        self.assertEqual(rows[0]['state'], 'fills_before_reset')
        self.assertEqual(rows[0]['percent_per_hour'], 20.0)
        self.assertEqual(rows[0]['full_at'], (self.NOW + timedelta(hours=2)).isoformat())

    def test_weekly_windows_use_the_daily_average_and_reset_or_full_windows_say_so(self):
        from pler.usage.forecast import outlook
        reset = self.NOW + timedelta(days=5)
        samples = [(self.NOW - timedelta(days=10), 10080, 0.0, self.NOW - timedelta(days=2)),
                   (self.NOW - timedelta(days=3), 10080, 35.0, self.NOW - timedelta(days=2)),
                   (self.NOW - timedelta(days=1), 10080, 5.0, reset), (self.NOW, 10080, 15.0, reset)]
        row, = outlook([self.session(samples)], self.NOW)
        self.assertEqual((row['state'], row['percent_per_day']), ('lasts_until_reset', 4.5))  # 45 points over 10 days
        ended = outlook([self.session([(self.NOW - timedelta(hours=2), 300, 95.0, self.NOW - timedelta(minutes=5))])], self.NOW)
        self.assertEqual(ended[0]['state'], 'reset')
        full = outlook([self.session([(self.NOW, 300, 100.0, self.NOW + timedelta(hours=1))])], self.NOW)
        self.assertEqual(full[0]['state'], 'full')
        # old logs without reset times give no forecast rather than a guess
        self.assertEqual(outlook([self.session([(self.NOW, 300, 50.0)])], self.NOW), [])


class InsightTests(unittest.TestCase):
    def sessions(self):
        from pler.usage.records import Session
        rows = []
        for index, (calls, per_call) in enumerate([(10, 40000), (20, 50000), (30, 45000), (150, 180000)]):
            rows.append(Session('codex', str(index), 'x', calls=calls, prompts=10,
                                tokens=dict(input=0, cache_read=calls * per_call, cache_write=0, output=0, reasoning=0)))
        return rows

    def test_each_observation_carries_its_numbers_and_needs_enough_sessions(self):
        from pler.usage.insights import insights
        found = {note['kind']: note for note in insights(self.sessions(), [], lang='tr')}
        self.assertEqual(found['long_sessions']['evidence']['median_tokens_per_call_long'], 180000)
        self.assertEqual(found['long_sessions']['evidence']['median_tokens_per_call_short'], 45000)
        self.assertIn('4 kat', found['long_sessions']['detail'])
        self.assertIn('sabit tutulmadı', found['long_sessions']['detail'])
        self.assertIn('kanıtlamaz', found['long_sessions']['detail'])
        self.assertEqual(round(found['concentration']['evidence']['share'], 2), 0.91)
        self.assertNotIn('long_sessions', {n['kind'] for n in insights(self.sessions()[2:], [])})  # too few short ones

    def test_zero_token_baseline_does_not_break_an_otherwise_readable_snapshot(self):
        from pler.dashboard import project_view
        rows = self.sessions()
        for row in rows[:3]:
            row.tokens = dict.fromkeys(row.tokens, 0)
        value = project_view(rows, {}, days=0)
        self.assertEqual(value['totals']['sessions'], 4)
        self.assertNotIn('long_sessions', [note['kind'] for note in value['insights']])

    def test_concentration_does_not_invent_a_call_count_for_old_records(self):
        from pler.usage.insights import insights
        rows = self.sessions()
        rows[-1].notes = ['Older Codex log: cumulative totals only.']
        rows[-1].calls = 0
        note = next(note for note in insights(rows, [], lang='tr') if note['kind'] == 'concentration')
        self.assertIn('çağrı sayısı bilinmiyor', note['detail'])
        self.assertNotIn('0 çağrı', note['detail'])

    def test_the_dashboard_carries_outlook_and_observations_without_private_paths(self):
        from pler.dashboard import project_view
        rows = self.sessions()
        for row in rows:
            row.project = '/home/' + SECRET + '/shop'
            row.ended = row.started = datetime(2026, 10, 26, tzinfo=timezone.utc)
        view = project_view(rows, {}, days=0, now=datetime(2026, 10, 26, 12, tzinfo=timezone.utc))
        self.assertEqual(view['outlook'], [])
        self.assertIn('long_sessions', [note['kind'] for note in view['insights']])
        self.assertNotIn(SECRET, json.dumps(view['insights']))

    def test_quota_and_limit_observations_come_first(self):
        from pler.usage.insights import insights
        rows = self.sessions()
        rows[0].limit_hits = [datetime(2026, 10, 25, 9, 0, tzinfo=timezone.utc)]
        window = dict(window_minutes=300, used_percent=60.0, at='2026-10-26T12:00:00+00:00', resets_at='2026-10-26T15:00:00+00:00',
                      percent_per_hour=20.0, full_at='2026-10-26T14:00:00+00:00', state='fills_before_reset')
        kinds = [note['kind'] for note in insights(rows, [window])]
        self.assertEqual(kinds[:2], ['quota', 'limit_hits'])
        self.assertLessEqual(len(kinds), 4)


def xorshift(seed):
    while True:
        seed ^= (seed << 13) & 0xFFFFFFFF
        seed ^= seed >> 17
        seed ^= (seed << 5) & 0xFFFFFFFF
        yield seed


def zstd_sample(size, seed):
    """Deterministic log-like bytes: JSON lines with repeated words and base64-like noise, as in agent logs."""
    words = ['token', 'usage', 'session', 'cache', 'read', 'model', 'call', 'project', 'tool', 'shell', 'patch', 'turn']
    alphabet = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    numbers, out = xorshift(seed), bytearray()
    while len(out) < size:
        n = next(numbers)
        text = ' '.join(words[(n >> shift) % len(words)] for shift in range(0, 24, 3))
        out += ('{"type":"%s","n":%d,"text":"%s","blob":"' % (words[n % len(words)], n % 1000, text)).encode()
        out += bytes(alphabet[next(numbers) & 63] for _ in range(next(numbers) % 120))
        out += b'"}\n'
    return bytes(out[:size])


def zstd_mixed():
    """Incompressible, small-alphabet and repeated stretches, so that small blocks take every block form."""
    numbers = xorshift(11)
    noise = bytes(next(numbers) & 255 for _ in range(20000))
    digits = bytes(48 + next(numbers) % 10 for _ in range(12000))
    pairs = bytes(97 + (next(numbers) & 1) for _ in range(6000))
    return noise + digits + noise[:9000] + b'a' * 5000 + pairs + zstd_sample(9000, 3) * 2


def zstd_shape(kind):
    """Small inputs that make the reference encoder pick rarer forms (named in the comments)."""
    numbers = xorshift(5)
    if kind == 'nibbles':  # Huffman weights written directly, not FSE-compressed
        return bytes(next(numbers) & 15 for _ in range(8000))
    if kind == 'b64':  # blocks of literals with no sequences
        return bytes(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'[next(numbers) & 63] for _ in range(12000))
    if kind == 'ids':  # RLE-mode sequence tables
        return b''.join(('%08x' % next(numbers)).encode() + b' ' * 40 for _ in range(300))
    return bytes(next(numbers) & 255 for _ in range(6000)) * 2  # 'bigraw': raw literals with a 3-byte header


ZSTD_SAMPLES = dict({'tiny': lambda: zstd_sample(60, 1), 'rle': lambda: b'a' * 200000, 'log': lambda: zstd_sample(150000, 7),
                     'mixed': zstd_mixed}, **{kind: (lambda kind=kind: zstd_shape(kind)) for kind in ('nibbles', 'b64', 'ids', 'bigraw')})
ZSTD_FILES = Path(__file__).resolve().parent / 'fixtures' / 'zstd'


class PlainPythonZstdTests(unittest.TestCase):
    """fixtures/zstd holds the samples above compressed by the reference zstd program 1.5.2: name-level[-options].zst;
    "stream" files were compressed from a pipe in small blocks, so they have a window descriptor and every block type."""

    def test_reference_files_decompress_to_the_same_bytes(self):
        files = sorted(ZSTD_FILES.glob('*.zst'))
        self.assertGreaterEqual(len(files), 7)
        for path in files:
            with self.subTest(path.name):
                self.assertEqual(unzstd.decompress(path.read_bytes()), ZSTD_SAMPLES[path.name.split('-')[0]]())

    def test_concatenated_and_skippable_frames(self):
        skippable = (0x184D2A53).to_bytes(4, 'little') + (5).to_bytes(4, 'little') + b'xxxxx'
        tiny, log = (ZSTD_FILES / 'tiny-3.zst').read_bytes(), (ZSTD_FILES / 'log-19.zst').read_bytes()
        self.assertEqual(unzstd.decompress(skippable + tiny + log), ZSTD_SAMPLES['tiny']() + ZSTD_SAMPLES['log']())

    def test_rle_literals_in_a_block_without_sequences(self):
        # Made by hand: single-segment frame of 10 bytes; one compressed block whose literals are 'q' x 10 (RLE).
        frame = bytes.fromhex('28b52ffd' '20' '0a' '1d0000' '51' '71' '00')
        self.assertEqual(unzstd.decompress(frame), b'q' * 10)

    def test_corrupt_input_is_a_value_error(self):
        data = (ZSTD_FILES / 'log-3.zst').read_bytes()
        for broken in (data[:len(data) // 2], b'not zstd', data[:6]):
            with self.assertRaises(ValueError):
                unzstd.decompress(broken)

    def test_the_plain_python_decoder_is_the_last_resort(self):
        with mock.patch.dict('sys.modules', {'compression': None, 'zstandard': None}):
            self.assertEqual(zstd_module.decoder(), (unzstd.decompress, 'plain python'))


if __name__ == '__main__':
    unittest.main()
