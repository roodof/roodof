"""Conflicting synthetic account meters must not manufacture a forecast.

No provider identity is logged or inferred: contradictions suppress a result,
and compatible records remain a conditional observation of the selected scope.
"""
from datetime import datetime, timedelta, timezone
import json
import unittest

from pler.usage.forecast import outlook
from pler.usage.records import Session


NOW = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)
SECRET = 'PRIVATE-ACCOUNT-PATH-OR-IDENTITY'


def session(name, samples, agent='codex'):
    return Session(agent, name, SECRET + name, quota=samples)


def sample(at, used, reset, minutes=300):
    return at, minutes, used, reset


class ConflictingMetersTests(unittest.TestCase):
    def ambiguous(self, sessions, now=NOW, claude=()):
        row, = outlook(sessions, now, claude)
        self.assertEqual(row['state'], 'ambiguous')
        self.assertIsNone(row['used_percent'])
        self.assertIsNone(row['resets_at'])
        self.assertEqual(row['reason'], 'conflicting_meter_history')
        for key in ('full_at', 'percent_per_hour', 'percent_per_day', 'history_days'):
            self.assertNotIn(key, row)
        encoded=json.dumps(row, allow_nan=False)
        self.assertNotIn(SECRET, encoded)
        return row

    def test_two_constant_histories_do_not_produce_a_320_point_hourly_rise(self):
        start, reset = NOW-timedelta(minutes=30), NOW+timedelta(hours=4)
        personal = session('personal', [sample(start,10,reset), sample(start+timedelta(minutes=20),10,reset)])
        work = session('work', [sample(start,90,reset), sample(NOW,90,reset)])
        self.assertEqual(outlook([personal],NOW)[0]['state'], 'no_pace')
        self.assertEqual(outlook([work],NOW)[0]['state'], 'no_pace')
        self.ambiguous([personal,work])
        self.assertEqual(outlook([personal,work],NOW), outlook([work,personal],NOW))

    def test_decrease_before_reset_suppresses_both_short_and_weekly_windows(self):
        for minutes, gap in ((300,timedelta(minutes=30)), (10080,timedelta(days=3))):
            reset=NOW+timedelta(days=5)
            with self.subTest(minutes=minutes):
                self.ambiguous([session('s',[sample(NOW-gap,90,reset,minutes), sample(NOW,10,reset,minutes)])])

    def test_same_instant_conflicting_levels_cannot_choose_a_source_by_input_order(self):
        reset=NOW+timedelta(hours=4)
        for values in ((20,30),(30,20)):
            rows=[session(str(index),[sample(NOW,value,reset)]) for index,value in enumerate(values)]
            row=self.ambiguous(rows)
            self.assertEqual(row['at'],NOW.isoformat())

    def test_conflicting_active_reset_dates_are_unknown_even_when_levels_agree(self):
        self.ambiguous([session('one',[sample(NOW,20,NOW+timedelta(hours=1))]),
                        session('two',[sample(NOW,20,NOW+timedelta(hours=3))])])

    def test_reset_date_jitter_keeps_a_nondecreasing_single_window_usable(self):
        reset=NOW+timedelta(hours=3)
        samples=[sample(NOW-timedelta(minutes=30),20,reset),
                 sample(NOW,30,reset+timedelta(minutes=2))]
        row,=outlook([session('s',samples)],NOW)
        self.assertEqual((row['state'],row['percent_per_hour']),('lasts_until_reset',20.0))

    def test_exact_copies_do_not_create_a_rise_or_make_results_order_dependent(self):
        reset=NOW+timedelta(hours=3)
        samples=[sample(NOW-timedelta(minutes=30),20,reset),sample(NOW,30,reset)]
        original=outlook([session('one',samples)],NOW)
        self.assertEqual(original,outlook([session('one',samples*3),session('copy',list(reversed(samples)))],NOW))

    def test_a_known_reset_permits_a_decrease_and_recovers_the_short_window(self):
        old_reset=NOW-timedelta(hours=1)
        reset=NOW+timedelta(hours=3)
        samples=[sample(old_reset-timedelta(hours=1),90,old_reset),
                 sample(NOW-timedelta(minutes=30),10,reset),sample(NOW,20,reset)]
        row,=outlook([session('s',samples)],NOW)
        self.assertEqual((row['state'],row['percent_per_hour']),('lasts_until_reset',20.0))

    def test_weekly_average_still_includes_valid_rises_across_a_known_reset(self):
        old_reset=NOW-timedelta(days=2)
        reset=NOW+timedelta(days=5)
        samples=[sample(NOW-timedelta(days=10),0,old_reset,10080),
                 sample(NOW-timedelta(days=3),35,old_reset,10080),
                 sample(NOW-timedelta(days=1),5,reset,10080),sample(NOW,15,reset,10080)]
        row,=outlook([session('s',samples)],NOW)
        self.assertEqual((row['state'],row['percent_per_day']),('lasts_until_reset',4.5))

    def test_old_conflict_does_not_poison_new_short_reset_or_artificially_raise_its_pace(self):
        old_reset=NOW-timedelta(hours=1)
        reset=NOW+timedelta(hours=3)
        samples=[sample(old_reset-timedelta(hours=1),90,old_reset),
                 sample(old_reset-timedelta(minutes=30),10,old_reset),
                 sample(NOW-timedelta(minutes=30),10,reset),sample(NOW,20,reset)]
        row,=outlook([session('s',samples)],NOW)
        self.assertEqual((row['state'],row['percent_per_hour']),('lasts_until_reset',20.0))

    def test_old_weekly_conflict_is_dropped_only_after_its_reset_was_observed_to_expire(self):
        old_reset=NOW-timedelta(days=4)
        reset=NOW+timedelta(days=3)
        samples=[sample(NOW-timedelta(days=6),90,old_reset,10080),
                 sample(NOW-timedelta(days=5),10,old_reset,10080),
                 sample(NOW-timedelta(days=3),10,reset,10080),sample(NOW,25,reset,10080)]
        row,=outlook([session('s',samples)],NOW)
        self.assertEqual((row['state'],row['percent_per_day']),('lasts_until_reset',5.0))

    def test_conflict_in_obsolete_weekly_history_is_outside_the_forecast_horizon(self):
        old_reset=NOW-timedelta(days=15)
        reset=NOW+timedelta(days=3)
        samples=[sample(NOW-timedelta(days=17),90,old_reset,10080),
                 sample(NOW-timedelta(days=16),10,old_reset,10080),
                 sample(NOW-timedelta(days=3),10,reset,10080),sample(NOW,25,reset,10080)]
        row,=outlook([session('s',samples)],NOW)
        self.assertEqual(row['percent_per_day'],5.0)

    def test_full_latest_percentage_cannot_hide_a_conflicting_history(self):
        reset=NOW+timedelta(hours=3)
        self.ambiguous([session('s',[sample(NOW-timedelta(minutes=30),90,reset),
                                     sample(NOW-timedelta(minutes=20),10,reset),sample(NOW,100,reset)])])

    def test_claude_statusline_conflicts_use_the_same_guard(self):
        reset=NOW+timedelta(hours=3)
        self.ambiguous([],claude=[sample(NOW-timedelta(minutes=30),70,reset),sample(NOW,20,reset)])

    def test_other_agent_meter_is_not_mixed_with_a_conflicting_agent(self):
        reset=NOW+timedelta(hours=3)
        rows=outlook([session('s',[sample(NOW-timedelta(minutes=30),90,reset),sample(NOW,10,reset)])],NOW,
                     [sample(NOW-timedelta(minutes=30),20,reset),sample(NOW,30,reset)])
        by_agent={row['agent']:row for row in rows}
        self.assertEqual(by_agent['codex']['state'],'ambiguous')
        self.assertEqual(by_agent['claude-code']['percent_per_hour'],20.0)

    def test_small_falls_of_one_real_meter_keep_the_window_usable(self):
        # Shaped like real Codex logs: within one window the level often falls back by a few points.
        reset=NOW+timedelta(hours=3)
        levels=(30,29,31,30,27,33)
        samples=[sample(NOW-timedelta(minutes=50-10*index),level,reset) for index,level in enumerate(levels)]
        row,=outlook([session('s',samples)],NOW)
        self.assertNotEqual(row['state'],'ambiguous')
        self.assertEqual(row['used_percent'],33.0)

    def test_an_early_provider_reset_starts_the_new_window_instead_of_hiding_it(self):
        old_reset,reset=NOW+timedelta(days=3),NOW+timedelta(days=5)
        samples=[sample(NOW-timedelta(days=3),40,old_reset,10080),sample(NOW-timedelta(days=2),0,reset,10080),
                 sample(NOW,10,reset,10080)]
        row,=outlook([session('s',samples)],NOW)
        self.assertNotEqual(row['state'],'ambiguous')
        self.assertEqual((row['used_percent'],row['resets_at']),(10.0,reset.isoformat()))

    def test_a_reset_moving_back_to_an_earlier_time_is_a_conflict(self):
        self.ambiguous([session('one',[sample(NOW-timedelta(minutes=30),10,NOW+timedelta(hours=8))]),
                        session('two',[sample(NOW,80,NOW+timedelta(hours=3))])])

    def test_ambiguity_cannot_be_resolved_merely_by_repeated_copies_of_one_level(self):
        reset=NOW+timedelta(hours=3)
        first=[sample(NOW-timedelta(minutes=30),90,reset),sample(NOW-timedelta(minutes=20),10,reset)]
        last=[sample(NOW,20,reset)]*10
        self.ambiguous([session('s',first+last)])


if __name__=='__main__':unittest.main()
