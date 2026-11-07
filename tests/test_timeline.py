"""The usage-over-time chart adds up to the dated total and never spreads a session total."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from pler.usage import claude_code, codex
from pler.usage.period_usage import analyze
from pler.usage.timeline import hourly
from test_logs import write_jsonl
from test_period_usage import NOW, OLD, SECRET, SINCE, TRANSCRIPT, cumulative, meta, reply, response


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def codex(self, rows, name='rollout-a.jsonl', identity='one'):
        path = self.root / name
        write_jsonl(path, [meta(identity)] + rows)
        sessions, issues = codex.read([path])
        self.assertEqual(issues, [])
        return sessions

    def claude(self, rows, name='claude.jsonl'):
        path = self.root / name
        write_jsonl(path, rows)
        issues = []
        sessions = claude_code.read([path], issues)
        self.assertEqual(issues, [])
        return sessions

    def agrees(self, sessions, since=SINCE):
        value = hourly(sessions, since, NOW)
        dated = analyze(sessions, since, NOW)
        self.assertEqual(sum(row[2] for row in value['rows']), dated['total_tokens'])
        self.assertEqual(sum(row[3] for row in value['rows']), dated['response_calls'])
        text = json.dumps(value, allow_nan=False)
        self.assertNotIn(SECRET, text)
        self.assertNotIn(TRANSCRIPT, text)
        return value['rows']

    def test_responses_fall_in_their_own_utc_hour_per_agent(self):
        at = NOW - timedelta(hours=5, minutes=20)
        sessions = (self.codex([response('a', 10, at), response('b', 5, at + timedelta(minutes=30)),
                                response('c', 7, NOW - timedelta(minutes=10))])
                    + self.claude([reply('d', 3, at)]))
        rows = self.agrees(sessions)
        hour = at.replace(minute=0, second=0, microsecond=0).isoformat()
        self.assertIn([hour, 'codex', 10, 1], rows)
        self.assertIn([hour, 'claude-code', 3, 1], rows)
        later = (at + timedelta(minutes=30)).replace(minute=0, second=0, microsecond=0).isoformat()
        self.assertIn([later, 'codex', 5, 1], rows)
        self.assertEqual(rows, sorted(rows))
        self.assertTrue(all(row[0].endswith('+00:00') for row in rows))

    def test_old_and_future_responses_stay_out_like_the_dated_total(self):
        sessions = self.codex([response('old', 1000000, OLD), response('start', 2, SINCE),
                               response('now', 3, NOW), response('future', 4, NOW + timedelta(microseconds=1))])
        rows = self.agrees(sessions)
        self.assertEqual(sum(row[2] for row in rows), 5)
        self.assertEqual(sum(row[2] for row in self.agrees(sessions, since=None)), 1000005)

    def test_a_cumulative_only_session_is_never_spread_over_time(self):
        sessions = self.codex([cumulative(1000000, NOW - timedelta(hours=1))])
        self.assertEqual(self.agrees(sessions), [])

    def test_empty_and_invalid_intervals(self):
        self.assertEqual(hourly([], SINCE, NOW), dict(unit='hour_utc', rows=[]))
        with self.assertRaises(ValueError):
            hourly([], NOW, SINCE)
        with self.assertRaises(ValueError):
            hourly([], SINCE, datetime(2026, 10, 29, 12))


if __name__ == '__main__':
    unittest.main()
