"""The plan check uses only published prices and limit ratios, the account-wide meter and dated responses; it
never names a plan it cannot justify. Sessions, logs and folders are invented and isolated."""
from datetime import datetime, timedelta, timezone
import io
import json
import threading
import unittest
from unittest.mock import patch

from pler.dashboard import UsageDashboard
from pler.server import Server
from pler.usage import main, plans, scan
from pler.usage.records import Session, empty_tokens
import test_adoption_api
from test_adoption_api import IsolatedMetadata, invented_sessions, join_scan
from test_logs import write_jsonl

NOW = datetime(2026, 10, 31, 12, tzinfo=timezone.utc)


def tokens(n):
    return dict(empty_tokens(), input=n)


def session(agent='claude-code', days=40, usd=(), plan=None, quota=(), **extra):
    """A session that started `days` ago with one dated, priced response per entry of `usd` (one a day)."""
    value = Session(agent, 'invented-%s' % agent, '/invented/%s.jsonl' % agent, started=NOW - timedelta(days=days),
                    ended=NOW - timedelta(hours=1), quota_plan=plan, **extra)
    value._usage_events = []
    for index, price in enumerate(usd):
        at = NOW - timedelta(days=index + 1)
        value._usage_events.append(dict(first=at, at=at, tokens=tokens(1000), usd=price))
        value.tokens['input'] += 1000
        value.calls += 1
    value.quota = list(quota)
    return value


def meter(minutes, peaks, days=20):
    """Samples spread evenly over `days`, one reset period per sample, with the given peak percentages."""
    step = timedelta(days=days) / max(1, len(peaks) - 1)
    return [(NOW - timedelta(days=days) + step * index, minutes, peak, NOW - timedelta(days=days) + step * index + timedelta(minutes=minutes))
            for index, peak in enumerate(peaks)]


def row(rows, agent):
    return next(value for value in rows if value['agent'] == agent)


def dense_meter(minutes, peak, now=NOW):
    result=[]
    for days in range(20,-1,-1):
        at=now-timedelta(days=days)
        reset=(at+timedelta(hours=5) if minutes==300 else
               now+timedelta(days=2)-timedelta(days=7*((days+1)//7)))
        result.append((at,minutes,peak,reset))
    return result


class PlanRuleTests(unittest.TestCase):
    def test_codex_plan_limits_and_api_equivalent_never_name_an_unpublished_larger_plan(self):
        samples = meter(300, [40, 100, 100, 60]) + meter(10080, [55, 100])
        codex = session('codex', usd=[5, 7], plan='plus', quota=samples)
        value = row(plans.advise([codex], (), NOW), 'codex')
        # $12 is below the $20 plan, but a reached limit means the account carries more than this agent work.
        self.assertEqual((value['plan'], value['plan_source'], value['price_usd'], value['api_usd']), ('plus', 'log', 20, 12))
        self.assertEqual({m['window_minutes']: (m['full'], m['periods']) for m in value['meter']}, {300: (2, 4), 10080: (1, 2)})
        self.assertEqual(value['findings'], ['limits_reached', 'larger_ratio_unpublished'])
        self.assertNotIn('smaller', value)

    def test_a_smaller_claude_plan_is_named_only_with_published_ratios_history_and_headroom(self):
        low = dense_meter(300,15) + dense_meter(10080,14)
        value = row(plans.advise([session(usd=[150])], low, NOW, claude_plan='max'), 'claude-code')
        self.assertEqual(value['findings'], ['lower_observed'])
        lower=value['lower_plan_comparison']
        self.assertEqual((lower['plan'],lower['usd'],lower['share'],lower['peak'],lower['observed_only']),('pro',20,0.2,15,True))
        self.assertNotIn('smaller',value)  # legacy "fits" advice is not exported
        # 16% is the most Pro could have carried with a fifth to spare; 17% is too close.
        close = dense_meter(300,17) + dense_meter(10080,14)
        self.assertNotIn('lower_plan_comparison', row(plans.advise([session(usd=[150])], close, NOW, claude_plan='max'), 'claude-code'))
        short = meter(300, [5, 12], days=10) + meter(10080, [9, 14], days=10)
        self.assertNotIn('lower_plan_comparison', row(plans.advise([session(usd=[150])], short, NOW, claude_plan='max'), 'claude-code'))
        ultra = dense_meter(10080,38)
        value = row(plans.advise([session(usd=[250])], ultra, NOW, claude_plan='ultra'), 'claude-code')
        self.assertEqual((value['findings'], value['lower_plan_comparison']['plan'], value['lower_plan_comparison']['share']), (['lower_weekly_observed'], 'max', 0.5))
        self.assertNotIn('smaller', row(plans.advise([session(usd=[150])], meter(300, [5, 8]) + meter(10080, [5, 9]),
                                                      NOW, claude_plan='pro'), 'claude-code'))

    def test_limits_reached_on_claude_say_a_larger_need_is_unseen(self):
        full = meter(300, [100, 30]) + meter(10080, [40, 60])
        value = row(plans.advise([session(usd=[1])], full, NOW, claude_plan='pro'), 'claude-code')
        self.assertEqual(value['findings'], ['limits_reached', 'larger_need_unseen'])  # no api_cheaper at a limit
        hit = session(usd=[1], limit_hits=[NOW - timedelta(days=2)])
        self.assertIn('limits_reached', row(plans.advise([hit], (), NOW, claude_plan='max'), 'claude-code')['findings'])

    def test_numeric_api_comparison_does_not_claim_a_switching_saving(self):
        cheap = row(plans.advise([session(usd=[3, 4])], (), NOW, claude_plan='max'), 'claude-code')
        self.assertEqual(cheap['findings'], ['no_meter', 'api_below_list_price'])
        self.assertIsNone(cheap['actual_payment_usd'])
        self.assertFalse(cheap['history_complete'])
        young = row(plans.advise([session(days=10, usd=[3, 4])], (), NOW, claude_plan='max'), 'claude-code')
        self.assertNotIn('api_below_list_price', young['findings'])
        undated = session(usd=[3, 4])
        undated._usage_events.append(dict(first=None, at=None, tokens=tokens(1000), usd=None))
        undated.calls += 1
        value = row(plans.advise([undated], (), NOW, claude_plan='max'), 'claude-code')
        self.assertTrue(value['usage_partial'])
        self.assertNotIn('api_below_list_price', value['findings'])

    def test_a_session_with_unknown_project_still_counts_for_the_account(self):
        # Regression: the dated-usage view leaves such sessions out; a plan belongs to the account.
        value = session('codex', usd=[50, 60], plan='plus', attribution_complete=False)
        self.assertEqual(row(plans.advise([value], (), NOW), 'codex')['api_usd'], 110)

    def test_older_responses_and_other_sources_stay_out_and_a_mixed_meter_is_not_judged(self):
        old = session('codex', days=90, usd=[5], plan='plus')
        old._usage_events.append(dict(first=NOW - timedelta(days=45), at=NOW - timedelta(days=45), tokens=tokens(1000), usd=500))
        old.calls += 1
        old.quota = meter(300, [100, 100])
        value = row(plans.advise([old], (), NOW, scopes={'codex': 2}), 'codex')
        self.assertEqual((value['api_usd'], value['meter'], value['meter_ambiguous']), (5, [], True))
        self.assertNotIn('limits_reached', value['findings'])
        self.assertEqual(row(plans.advise([session()], (), NOW), 'claude-code')['findings'], ['choose_plan', 'no_meter'])


class PlanReaderTests(IsolatedMetadata):
    def rollout(self):
        usage = dict(input_tokens=100000, cached_input_tokens=90000, cache_write_input_tokens=0, output_tokens=2000,
                     reasoning_output_tokens=500)
        now = datetime.now(timezone.utc)
        rows = [dict(timestamp=(now - timedelta(days=3)).isoformat(), type='session_meta', payload=dict(id='c1', cwd='/work/engine')),
                dict(timestamp=(now - timedelta(days=3)).isoformat(), type='turn_context', payload=dict(model='gpt-5.3-codex', cwd='/work/engine'))]
        for index in range(3):
            at = now - timedelta(days=3) + timedelta(hours=index)
            rows.append(dict(timestamp=at.isoformat(), type='token_usage_record', payload=dict(response_id='r%d' % index, usage=usage)))
            rows.append(dict(timestamp=at.isoformat(), type='event_msg', payload=dict(type='token_count', info=None, rate_limits=dict(
                primary=dict(used_percent=[50, 100, 20][index], window_minutes=300, resets_at=int((at + timedelta(hours=1)).timestamp())),
                plan_type='plus'))))
        return rows

    def test_dated_prices_flow_from_the_codex_reader_into_the_plan_check_and_report(self):
        write_jsonl(self.codex / 'rollout-invented.jsonl', self.rollout())
        sessions, sources = scan()
        value = row(plans.advise(sessions, (), datetime.now(timezone.utc)), 'codex')
        self.assertEqual(value['plan'], 'plus')
        self.assertGreater(value['api_usd'], 0)
        self.assertEqual(value['api_priced_share'], 1.0)
        self.assertEqual([(m['window_minutes'], m['full'], m['periods']) for m in value['meter']], [(300, 1, 3)])
        output = io.StringIO()
        with patch('sys.stdout', output):
            main(['--lang', 'en'])
        text = output.getvalue()
        self.assertIn('Plan check', text)
        self.assertIn('Codex: Plus (list price: $20 a month)', text)
        self.assertIn('Observed at 100% in 1 of 3 sampled 5-hour reset periods', text)
        output = io.StringIO()
        with patch('sys.stdout', output):
            main(['--json'])
        self.assertEqual(json.loads(output.getvalue())['plans']['rows'][0]['plan'], 'plus')


class PlanChoiceTests(IsolatedMetadata):
    def test_the_choice_is_one_word_on_this_computer_and_an_unreadable_file_is_kept(self):
        store = plans.Choice()
        self.assertIsNone(store.read())
        self.assertEqual(store.save('max'), 'max')
        self.assertEqual(json.loads((self.cache / plans.FILENAME).read_text('utf-8')), dict(format=1, claude='max'))
        self.assertEqual(plans.Choice().read(), 'max')
        with self.assertRaises(ValueError):
            store.save('enterprise')
        (self.cache / plans.FILENAME).write_text('{"format": 2, "claude": "max"}', 'utf-8')
        with self.assertRaises(ValueError):
            store.save('pro')
        self.assertEqual(json.loads((self.cache / plans.FILENAME).read_text('utf-8'))['format'], 2)
        memory = plans.Memory()
        memory.save('ultra')
        self.assertEqual(memory.read(), 'ultra')


class PlanHttpTests(IsolatedMetadata):
    request = test_adoption_api.AdoptionHttpTests.request

    def setUp(self):
        super().setUp()
        rows = invented_sessions()
        self.board = UsageDashboard(lambda: (rows, dict(claude_files=1, codex_files=1, skipped=[])),
                                    git_reader=lambda path: dict(state='not_repository'))
        self.board.refresh(); join_scan(self.board)
        self.server = Server(0, self.board)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def test_the_plan_route_takes_one_known_word_and_the_view_uses_it(self):
        for body in (dict(plan='enterprise'), dict(plan=1), dict(plan='max', path='C:/x'), dict(), ['max']):
            with self.subTest(body=body):
                self.assertEqual(self.request('/api/usage/plan', 'POST', body)[0], 400)
        code, _, raw = self.request('/api/usage/plan', 'POST', dict(plan='max'))
        self.assertEqual((code, json.loads(raw)), (200, dict(ok=True, plan='max')))
        view = json.loads(self.request('/api/usage?days=0')[2])
        claude = row(view['plans']['rows'], 'claude-code')
        self.assertEqual((claude['plan'], claude['price_usd'], view['plans']['prices_as_of']), ('max', 100, plans.PRICES_AS_OF))
        self.assertEqual(plans.Choice().read(), 'max')
        self.assertEqual(json.loads(self.request('/api/usage/plan', 'POST', dict(plan=None))[2]), dict(ok=True, plan=None))

    def test_failed_save_is_reported_and_the_demo_keeps_its_choice_in_memory(self):
        with patch.object(self.board.plan_store, 'save', side_effect=OSError('disk')):
            code, _, raw = self.request('/api/usage/plan', 'POST', dict(plan='pro'))
        self.assertEqual(code, 500)
        self.assertNotIn('disk', raw.decode('utf-8'))
        demo = UsageDashboard(lambda: (invented_sessions(), dict(claude_files=1, codex_files=0, skipped=[], demo=True)),
                              git_reader=lambda path: dict(state='not_repository'), plan_choice=plans.Memory())
        demo.refresh(); join_scan(demo)
        self.assertEqual(demo.set_plan('ultra'), dict(ok=True, plan='ultra'))
        self.assertFalse((self.cache / plans.FILENAME).exists())


if __name__ == '__main__':
    unittest.main()
