"""Invented subsequent-edit evidence through the page and terminal projections."""
import contextlib
from datetime import datetime, timedelta, timezone
import io
import json
import unittest
from unittest.mock import patch

from pler.dashboard import project_view
from pler.i18n import say
from pler.usage import main
from pler.usage.records import Session


NOW = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)
PRIVATE = 'PRIVATE-EDIT-PROJECTION-CANARY'


def session(identity='origin', agent='codex', ended=None, project='/work/selected'):
    ended = ended or NOW - timedelta(days=1)
    value = Session(agent, identity + PRIVATE, '/logs/' + identity + PRIVATE + '.jsonl',
                    project=project, started=ended-timedelta(hours=1), ended=ended,
                    calls=1, tokens=dict(input=100, cache_read=0, cache_write=0, output=0, reasoning=0),
                    files_edited={'/work/target/' + PRIVATE + '.py'})
    value._history_group = (agent, identity)
    value._history_uncertain = False
    return value


def sources(cutoff=NOW):
    return dict(claude_files=1, codex_files=1, skipped=[], claude_quota=[], observed_at=cutoff.isoformat())


class EditProjectionTests(unittest.TestCase):
    def test_recorded_scan_cutoff_keeps_pending_stable_when_page_clock_advances(self):
        origin = session()
        before = project_view([origin], sources(), days=0, now=NOW)
        after = project_view([origin], sources(), days=0, now=NOW+timedelta(days=20))
        self.assertEqual(before['reedit'], after['reedit'])
        self.assertEqual(before['reedit']['pending_sessions'], 1)
        self.assertEqual(before['reedit']['observed_unmatched_sessions'], 0)
        self.assertEqual(before['reedit']['cutoff'], NOW.isoformat())
        rescanned = project_view([origin], sources(NOW+timedelta(days=20)), days=0, now=NOW+timedelta(days=20))
        self.assertEqual((rescanned['reedit']['pending_sessions'], rescanned['reedit']['observed_unmatched_sessions']), (0, 1))

    def test_a_later_record_after_scan_cutoff_cannot_enter_evidence_on_page_refresh(self):
        origin = session(ended=NOW-timedelta(days=2))
        future = session('future', 'claude-code', ended=NOW+timedelta(days=1))
        result = project_view([origin, future], sources(), days=0, now=NOW+timedelta(days=5))['reedit']
        self.assertEqual(result['matched_sessions'], 0)
        self.assertEqual(result['timeline_excluded']['invalid_time'], 1)
        self.assertEqual(result['pending_sessions'], 1)

    def test_agent_and_project_filters_select_origins_but_keep_cross_agent_later_evidence(self):
        origin = session(ended=NOW-timedelta(days=3))
        later = session('later', 'claude-code', ended=NOW-timedelta(days=2), project='/work/other')
        whole = project_view([origin, later], sources(), days=0, now=NOW)
        project = next(row['project_id'] for row in whole['sessions'] if row['agent']=='codex')
        for filters in (dict(agent='codex'), dict(project=project), dict(agent='codex', project=project)):
            result = project_view([origin, later], sources(), days=0, now=NOW, **filters)
            self.assertEqual((result['totals']['sessions'], result['totals']['total_tokens']), (1, 100))
            self.assertEqual((result['reedit']['origin_sessions'], result['reedit']['timeline_sessions'],
                              result['reedit']['matched_sessions']), (1, 2, 1))
            match, = result['reedit']['matches']
            self.assertEqual((match['origin_agent'], match['later_agent']), ('codex', 'claude-code'))
            self.assertEqual(match['origin_id'], result['sessions'][0]['id'])
            self.assertNotIn(PRIVATE, json.dumps(result['reedit']))

    def test_unknown_original_time_is_excluded_before_summary_uses_safe_dates(self):
        value = session()
        value.started = None
        result = project_view([value], sources(), days=0, now=NOW)
        self.assertEqual(result['totals']['total_tokens'], 100)
        self.assertIsNone(result['sessions'][0]['started'])
        self.assertEqual((result['reedit']['eligible_sessions'], result['reedit']['excluded']['invalid_time']), (0, 1))

    def test_cli_json_uses_scan_cutoff_and_safe_session_codes(self):
        origin = session(ended=NOW-timedelta(days=3))
        later = session('later', 'claude-code', ended=NOW-timedelta(days=2))
        buffer = io.StringIO()
        with patch('pler.usage.scan', return_value=([origin, later], sources())), contextlib.redirect_stdout(buffer):
            main(['--json', '--sessions', '--days', '0', '--lang', 'tr'])
        value = json.loads(buffer.getvalue())
        self.assertEqual(value['reedit']['cutoff'], NOW.isoformat())
        self.assertEqual(value['reedit']['matched_sessions'], 1)
        self.assertEqual((value['totals']['sessions'], value['totals']['total_tokens']), (2, 200))
        self.assertNotIn(PRIVATE, buffer.getvalue())
        note, = [note for note in value['insights'] if note['kind']=='subsequent_edit']
        self.assertEqual(note['title'], say('tr', 'insight.reedit.title'))
        self.assertEqual(note['evidence'], value['reedit'])
        self.assertEqual(value['reedit']['matches'][0]['origin_id'],
                         next(row['id'] for row in value['sessions'] if row['agent']=='codex'))

    def test_terminal_has_shared_localized_observation_and_keeps_whole_session_totals(self):
        origin = session()
        for lang in ('en', 'tr'):
            buffer = io.StringIO()
            with patch('pler.usage.scan', return_value=([origin], sources())), contextlib.redirect_stdout(buffer):
                main(['--days', '0', '--lang', lang])
            text = buffer.getvalue()
            self.assertIn(say(lang, 'insight.reedit.title'), text)
            self.assertIn(say(lang, 'insight.reedit.limits').strip(), text)
            self.assertNotIn(PRIVATE, text)


if __name__ == '__main__':
    unittest.main()
