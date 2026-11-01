"""Synthetic coverage failures must lead to different, non-destructive next steps."""
from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from pler.dashboard import project_view
from pler.reporting import coverage_guidance
from pler.usage.records import Session

NOW = datetime(2026, 11, 1, tzinfo=timezone.utc)
PRIVATE = 'PRIVATE-SOURCE-AND-ERROR'


def row(**changes):
    return Session('codex', 'example', '/'+PRIVATE+'/rollout.jsonl',
                   started=NOW, ended=NOW, **changes)


def codes(value):
    return [item['code'] for item in value['notices']]


class CoverageGuidanceTests(unittest.TestCase):
    def test_access_wsl_and_missing_sources_are_distinct_even_without_sessions(self):
        for reason, expected in [('PermissionError', 'source_access'), ('WSLNotRunning', 'wsl_unavailable'),
                                 ('WSLUnavailable', 'wsl_unavailable'), ('FileNotFoundError', 'source_missing'),
                                 ('MalformedRows', 'invalid_records'), ('ReadLimitExceeded', 'read_limits'),
                                 ('UnsafePath', 'unsafe_path'), ('FutureError: '+PRIVATE, 'source_access')]:
            with self.subTest(reason=reason):
                result = project_view([], dict(skipped=[(PRIVATE,reason)]), days=0, now=NOW)
                self.assertEqual(codes(result['coverage']), [expected])
                self.assertNotIn(PRIVATE, json.dumps(result))
                self.assertEqual(result['totals']['total_tokens'], 0)

    def test_source_limits_survive_filters_but_session_limits_follow_them(self):
        old = row(archive_old_parser=True, tokens_complete=False)
        old.source_deleted=True
        normal = Session('claude-code', 'other', 'invented', started=NOW, ended=NOW)
        sources=dict(skipped=[(PRIVATE, 'PermissionError')])
        all_rows=project_view([old,normal], sources, days=0, now=NOW)
        filtered=project_view([old,normal], sources, days=0, agent='claude-code', now=NOW)
        self.assertEqual(codes(all_rows['coverage']), ['source_access','archive_old_parser','retained_history'])
        self.assertEqual(codes(filtered['coverage']), ['source_access'])
        self.assertEqual(filtered['coverage']['source_scope'], 'all_selected_folders')
        self.assertEqual(filtered['coverage']['session_scope'], 'current_filters')

    def test_unchecked_archive_does_not_claim_deletion(self):
        s=row(archive_unverified=True, tokens_complete=False, source_state='archive')
        self.assertEqual(codes(coverage_guidance([s],{})), ['archive_unverified'])
        s.source_deleted=True
        self.assertEqual(codes(coverage_guidance([s],{})), ['archive_unverified','retained_history'])

    def test_old_archive_issue_code_also_works_without_computed_flag(self):
        s=row(issues={'archive_old_parser'}, tokens_complete=False)
        self.assertEqual(codes(coverage_guidance([s],{})), ['archive_old_parser'])

    def test_archive_loss_is_global_and_missing_unread_history_is_never_invented(self):
        self.assertEqual(codes(coverage_guidance([],{})), [])
        for archive in ({'evicted_files':2}, {'errors':1}):
            result=coverage_guidance([],dict(archive=archive))
            self.assertEqual(codes(result), ['archive_loss'])
            self.assertNotIn('lost_sessions', result)

    def test_unknown_price_and_attribution_do_not_turn_into_a_repaired_total(self):
        s=row(tokens=dict(input=10,cache_read=0,cache_write=0,output=0,reasoning=0),
              attribution_complete=False, calls_complete=False)
        before=s.as_dict()
        self.assertEqual(codes(coverage_guidance([s],{})),
                         ['incomplete_usage','uncertain_attribution','unpriced_usage'])
        self.assertEqual(s.as_dict(),before)
        s.api_priced_tokens=10
        self.assertNotIn('unpriced_usage',codes(coverage_guidance([s],{})))
        self.assertEqual(codes(coverage_guidance([row(models_complete=False)],{})), ['uncertain_attribution'])

    def test_every_notice_has_both_translations_and_local_help(self):
        source=Path(__file__).resolve().parents[1]/'src'/'pler'
        script=(source/'web'/'app.js').read_text('utf-8')
        table=json.loads(script.split('/*I18N*/',1)[1].split('/*END*/',1)[0])
        s=row(archive_old_parser=True,archive_unverified=True,source_deleted=True,
              calls_complete=False,attribution_complete=False,
              tokens=dict(input=10,cache_read=0,cache_write=0,output=0,reasoning=0))
        s2=row(tokens_complete=False)
        reasons=['WSLNotRunning','ReadLimitExceeded','UnsafePath','FileNotFoundError',
                 'MalformedRows','PermissionError']
        result=coverage_guidance([s,s2],dict(skipped=list(zip(map(str,range(len(reasons))),reasons)),
                                           archive={'errors':1}))
        self.assertEqual(len(codes(result)),13)
        for lang in ('en','tr'):
            for code in codes(result):
                for part in ('title','impact','next'):
                    self.assertTrue(table[lang]['coverage_'+code+'_'+part])
            help_text=(source/'help'/(lang+'.html')).read_text('utf-8')
            self.assertIn('id="coverage"',help_text)
            self.assertIn('--claude-dir',help_text)
            self.assertIn('--codex-dir',help_text)
            self.assertNotIn('--claude-root',help_text)


if __name__ == '__main__':
    unittest.main()
