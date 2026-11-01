"""E02: what PLER can tell about account scope without reading any account identity.

Codex logs its plan with every meter sample. A plan change is evidence that later percentages measure another
limit (another plan or another account), so forecasts and limit counts start at the latest change. A switch
between accounts on the same plan leaves no such evidence; the tests below pin that it is not claimed either way.
Sessions and meters are invented.
"""
from datetime import datetime, timedelta, timezone
import json
import unittest

from pler.usage import plans
from pler.usage.forecast import outlook, plan_boundary
from pler.usage.records import Session

NOW = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)
WEEK = 7 * 24 * 60


def codex(name, samples):
    value = Session('codex', name, '/invented/%s.jsonl' % name, started=NOW - timedelta(days=12), ended=NOW,
                    quota_plan=samples[-1][4] if samples and len(samples[-1]) > 4 else None)
    value._usage_events = []
    value.quota = list(samples)
    return value


def weekly(days_ago, used, plan, reset_in_days=3):
    at = NOW - timedelta(days=days_ago)
    return (at, WEEK, used, NOW + timedelta(days=reset_in_days), plan)


def window(row_list, minutes):
    return next(row for row in row_list if row['window_minutes'] == minutes)


class PlanBoundaryTests(unittest.TestCase):
    def test_weekly_pace_uses_only_samples_since_the_latest_plan_change(self):
        before = [weekly(9.5 - day, 10 + 20 * day, 'plus', -3) for day in range(4)]     # 20 points a day on Plus
        after = [weekly(3 - day * 1.5, 1 + 3 * day, 'pro') for day in range(3)]        # 2 points a day on Pro
        row = window(outlook([codex('one', before + after)], NOW), WEEK)
        self.assertEqual(row['percent_per_day'], 2.0)
        self.assertEqual(row['plan_changed_at'], (NOW - timedelta(days=3)).isoformat())
        unbounded = window(outlook([codex('one', [s[:4] for s in before + after])], NOW), WEEK)
        self.assertNotEqual(unbounded.get('percent_per_day'), 2.0)  # without the plan the old rises leak in

    def test_a_change_inside_a_short_window_drops_the_earlier_samples_of_that_window(self):
        reset = NOW + timedelta(hours=3)
        samples = [(NOW - timedelta(minutes=90), 300, 10, reset, 'plus'), (NOW - timedelta(minutes=60), 300, 70, reset, 'plus'),
                   (NOW - timedelta(minutes=40), 300, 5, reset, 'pro'), (NOW, 300, 15, reset, 'pro')]
        row, = outlook([codex('one', samples)], NOW)
        self.assertEqual((row['state'], row['used_percent'], row['percent_per_hour']), ('lasts_until_reset', 15, 15.0))
        self.assertIn('plan_changed_at', row)

    def test_alternating_plans_never_mix_their_rises(self):
        reset = NOW + timedelta(hours=3)
        samples = [(NOW - timedelta(minutes=50 - 10 * i), 300, (10 if i % 2 else 80) + i, reset, 'pro' if i % 2 else 'plus')
                   for i in range(6)]
        row, = outlook([codex('one', samples)], NOW)
        self.assertEqual(row['used_percent'], 15)
        self.assertNotIn('percent_per_hour', row)  # one sample since the last change: no pace, never 70-point jumps

    def test_the_boundary_ignores_samples_without_a_plan_and_naive_times(self):
        at = NOW - timedelta(hours=1)
        self.assertIsNone(plan_boundary([(at, 300, 1, NOW, None), (NOW, 300, 2, NOW, 'plus'), (at, 300, 1, NOW)]))
        self.assertIsNone(plan_boundary([(at.replace(tzinfo=None), 300, 1, NOW, 'pro'), (NOW, 300, 2, NOW, 'plus')]))
        self.assertEqual(plan_boundary([(at, 300, 1, NOW, 'pro'), (NOW, 300, 2, NOW, 'plus')]), NOW)

    def test_claude_status_line_samples_have_no_plan_and_are_never_cut(self):
        reset = NOW + timedelta(hours=3)
        claude = [(NOW - timedelta(minutes=40), 300, 10, reset), (NOW, 300, 20, reset)]
        row, = outlook([], NOW, claude)
        self.assertNotIn('plan_changed_at', row)
        self.assertEqual(row['percent_per_hour'], 15.0)


class SameFolderAccountTests(unittest.TestCase):
    def test_a_same_plan_switch_with_a_later_reset_reads_as_a_new_window_not_as_one_proven_account(self):
        # Account A at 80% resetting in 1 hour; account B starts at 5% with its own later reset. The logs carry no
        # identity, and a single real meter also restarts windows early, so PLER shows B's window and claims no
        # account continuity: no plan boundary, no conflict, and the scope notes stay in place.
        samples = [(NOW - timedelta(minutes=50), 300, 80, NOW + timedelta(hours=1), 'plus'),
                   (NOW - timedelta(minutes=30), 300, 5, NOW + timedelta(hours=4), 'plus'),
                   (NOW, 300, 12, NOW + timedelta(hours=4), 'plus')]
        row, = outlook([codex('a', samples[:1]), codex('b', samples[1:])], NOW)
        self.assertEqual((row['state'], row['used_percent']), ('lasts_until_reset', 12))
        self.assertNotIn('plan_changed_at', row)

    def test_a_same_plan_switch_with_an_earlier_reset_is_a_conflict(self):
        samples = [(NOW - timedelta(minutes=50), 300, 40, NOW + timedelta(hours=3), 'plus'),
                   (NOW - timedelta(minutes=30), 300, 45, NOW + timedelta(hours=1), 'plus')]
        row, = outlook([codex('a', samples[:1]), codex('b', samples[1:])], NOW)
        self.assertEqual((row['state'], row['reason']), ('ambiguous', 'conflicting_meter_history'))


class PlanCheckBoundaryTests(unittest.TestCase):
    def test_limit_counts_start_at_the_latest_change_and_the_newest_sample_names_the_plan(self):
        def five(days_ago, used, plan):
            at = NOW - timedelta(days=days_ago)
            return (at, 300, used, at + timedelta(hours=4), plan)
        samples = [five(20 - day, 100, 'plus') for day in range(10)] + [five(8 - day, 30, 'pro') for day in range(8)]
        row, = [r for r in plans.advise([codex('one', samples)], (), NOW) if r['agent'] == 'codex']
        self.assertEqual(row['plan'], 'pro')
        self.assertIn('plan_changed', row['limitations'])
        self.assertEqual(row['plan_changed_at'], (NOW - timedelta(days=8)).isoformat())
        five_hours = next(m for m in row['meter'] if m['window_minutes'] == 300)
        self.assertEqual((five_hours['full'], five_hours['periods']), (0, 8))  # Plus's full windows are not Pro's
        self.assertNotIn('/invented/', json.dumps(row))


if __name__ == '__main__':
    unittest.main()
