"""Synthetic metadata only: lexical paths and preregistered subsequent edits."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from pler.usage.edit_paths import canonical_target
from pler.usage.records import Session
from pler.usage.reedit import analyze, WINDOW_SECONDS


NOW = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
DAY = timedelta(days=1)
HOUR = timedelta(hours=1)
SECOND = timedelta(seconds=1)
PRIVATE = 'PRIVATE-REEDIT-CANARY'


def session(name, started=None, ended=None, targets=('/work/a.py',), group=None, agent='codex', tokens=100):
    ended = NOW - 10 * DAY if ended is None else ended
    started = ended - HOUR if started is None else started
    value = Session(agent, name, '/logs/' + name + '.jsonl', started=started, ended=ended)
    value.files_edited = set(targets)
    value.tokens['input'] = tokens
    value._history_group = group if group is not None else (agent, name)
    value._history_uncertain = False
    return value


class LexicalEditPathTests(unittest.TestCase):
    def test_windows_rules_apply_on_every_host(self):
        expected = r'c:\work\app\src\main.py'
        for value, cwd in ((r'C:\Work\App\src\MAIN.py', None),
                           ('c:/work/app/src/../src/main.py', None),
                           ('src/MAIN.py', 'C:/Work/App'),
                           (r'..\src\MAIN.py', r'C:\Work\App\tests')):
            with self.subTest(value=value, cwd=cwd):
                self.assertEqual(canonical_target(value, cwd), expected)

    def test_posix_rules_preserve_case_and_use_the_supplied_cwd(self):
        self.assertEqual(canonical_target('/Work/src/../Main.py'), '/Work/Main.py')
        self.assertEqual(canonical_target('../Main.py', '/Work/src'), '/Work/Main.py')
        self.assertNotEqual(canonical_target('/Work/Main.py'), canonical_target('/work/main.py'))
        self.assertEqual(canonical_target('main.py', '/first'), '/first/main.py')
        self.assertEqual(canonical_target('main.py', '/second'), '/second/main.py')
        self.assertNotEqual(canonical_target('C:/work/a.py'), canonical_target('/mnt/c/work/a.py'))

    def test_ambiguous_unresolved_and_network_targets_are_rejected(self):
        rejected = [(None, None), (False, None), ('', None), ('/a\0b', None),
                    ('relative.py', None), ('relative.py', 'relative-cwd'),
                    ('relative.py', '//server/share'), ('C:relative.py', 'C:/work'), ('C:', None),
                    (r'\rooted.py', 'C:/work'), ('/rooted.py', 'C:/work'),
                    ('//server/share/a.py', None), (r'\\server\share\a.py', None),
                    ('/\\server/share/a.py', None), ('\\/server/share/a.py', None),
                    (r'\\?\C:\work\a.py', None), (r'\\.\C:\work\a.py', None),
                    (r'src\a.py', '/work'), (r'/work\a.py', None)]
        for value, cwd in rejected:
            with self.subTest(value=value, cwd=cwd):
                self.assertIsNone(canonical_target(value, cwd))
        self.assertIsNone(canonical_target('/' + 'a' * 1024))
        self.assertIsNone(canonical_target('b' * 600, '/' + 'a' * 600))

    def test_no_filesystem_resolution_or_process_cwd_is_consulted(self):
        def forbidden(*args, **kwargs):
            raise AssertionError('filesystem access')
        with patch('builtins.open', forbidden), patch.object(Path, 'resolve', forbidden), \
                patch.object(Path, 'stat', forbidden), patch.object(os, 'stat', forbidden), \
                patch.object(os, 'getcwd', forbidden):
            self.assertEqual(canonical_target('../a.py', 'C:/work/src'), r'c:\work\a.py')
            self.assertEqual(canonical_target('../a.py', '/work/src'), '/work/a.py')


class SubsequentEditTests(unittest.TestCase):
    def assertPartition(self, value):
        self.assertEqual(value['origin_sessions'], value['eligible_sessions'] + sum(value['excluded'].values()))
        self.assertEqual(value['eligible_sessions'], value['matched_sessions'] + value['pending_sessions']
                         + value['observed_unmatched_sessions'])

    def test_earliest_later_session_wins_and_each_origin_counts_once(self):
        origin = session('origin', targets=('/work/a.py', '/work/b.py'), tokens=100)
        later = session('later', started=origin.ended + HOUR, ended=origin.ended + 2 * HOUR,
                        targets=('/work/a.py', '/work/b.py'), tokens=200, agent='claude-code')
        slow = session('slow', started=origin.ended + DAY, ended=origin.ended + DAY + HOUR, tokens=300)
        value = analyze([slow, later, origin], [origin, origin], NOW)
        self.assertEqual((value['origin_sessions'], value['eligible_sessions'], value['matched_sessions']), (1, 1, 1))
        self.assertEqual((value['eligible_origin_tokens'], value['matched_origin_tokens']), (100, 100))
        match, = value['matches']
        self.assertEqual((match['gap_seconds'], match['matching_targets']), (3600, 2))
        self.assertEqual((match['origin_agent'], match['later_agent']), ('codex', 'claude-code'))
        self.assertEqual((match['origin_tokens'], match['later_tokens']), (100, 200))
        expected = hashlib.sha256(('claude-code:' + later.source + '\0' + later.session_id).encode()).hexdigest()[:24]
        self.assertEqual(match['later_id'], expected)
        self.assertPartition(value)

    def test_exact_seven_days_is_inclusive_and_a_later_microsecond_is_outside(self):
        origins, timeline = [], []
        for name, gap in (('edge', 7 * DAY), ('outside', 7 * DAY + timedelta(microseconds=1))):
            origin = session(name, targets=('/work/' + name,))
            later = session(name + '-later', started=origin.ended + gap, ended=origin.ended + gap + HOUR,
                            targets=origin.files_edited)
            origins.append(origin)
            timeline.extend([origin, later])
        value = analyze(timeline, origins, NOW)
        self.assertEqual(value['window_seconds'], WINDOW_SECONDS)
        self.assertEqual(value['matched_sessions'], 1)
        self.assertEqual(value['matches'][0]['gap_seconds'], WINDOW_SECONDS)
        self.assertEqual(value['observed_unmatched_sessions'], 1)
        self.assertPartition(value)

    def test_overlap_equal_boundary_and_earlier_sessions_do_not_match(self):
        origin = session('origin')
        overlap = session('overlap', started=origin.ended - SECOND, ended=origin.ended + HOUR)
        equal = session('equal', started=origin.ended, ended=origin.ended + HOUR)
        earlier = session('earlier', started=origin.started - HOUR, ended=origin.started)
        value = analyze([origin, overlap, equal, earlier], [origin], NOW)
        self.assertEqual((value['matched_sessions'], value['observed_unmatched_sessions']), (0, 1))
        self.assertEqual(value['matches'], [])

    def test_same_history_is_skipped_and_cross_agent_evidence_survives_origin_filters(self):
        origin = session('origin', group=('codex', 'family'))
        origin.project = '/selected-project'
        child = session('child', started=origin.ended + SECOND, ended=origin.ended + HOUR,
                        group=('codex', 'family'))
        sibling = session('sibling', started=origin.ended + HOUR, ended=origin.ended + 2 * HOUR,
                          group=('codex', 'family'))
        later = session('later', started=origin.ended + 3 * HOUR, ended=origin.ended + 4 * HOUR, agent='claude-code')
        later.project = '/different-project'
        value = analyze([origin, child, sibling, later], [origin], NOW)
        self.assertEqual(value['evidence_scope'], 'selected_roots_all_sessions')
        self.assertEqual((value['origin_sessions'], value['timeline_sessions']), (1, 4))
        self.assertEqual(value['matches'][0]['later_agent'], 'claude-code')
        self.assertEqual(value['matches'][0]['gap_seconds'], 3 * 3600)

    def test_unmatched_recent_origins_are_pending_and_the_full_boundary_is_observed(self):
        mature = session('mature', ended=NOW - 7 * DAY, targets=('/work/mature',))
        recent = session('recent', ended=NOW - 7 * DAY + timedelta(microseconds=1), targets=('/work/recent',))
        positive = session('positive', ended=NOW - DAY, targets=('/work/positive',))
        later = session('later', started=positive.ended + HOUR, ended=positive.ended + 2 * HOUR,
                        targets=positive.files_edited)
        value = analyze([mature, recent, positive, later], [mature, recent, positive], NOW)
        self.assertEqual((value['matched_sessions'], value['pending_sessions'], value['observed_unmatched_sessions']), (1, 1, 1))
        self.assertPartition(value)

    def test_missing_reversed_future_and_naive_spans_are_excluded(self):
        values = [session('missing-start'), session('missing-end'), session('reversed'), session('future'), session('naive')]
        values[0].started = None
        values[1].ended = None
        values[2].started = values[2].ended + SECOND
        values[3].ended = NOW + SECOND
        values[4].started = values[4].started.replace(tzinfo=None)
        result = analyze(values, values, NOW)
        self.assertEqual(result['excluded']['invalid_time'], 5)
        self.assertEqual(result['timeline_eligible_sessions'], 0)
        self.assertPartition(result)

    def test_timezone_offsets_are_compared_as_utc(self):
        origin = session('origin')
        later = session('later', started=(origin.ended + HOUR).astimezone(timezone(timedelta(hours=3))),
                        ended=(origin.ended + 2 * HOUR).astimezone(timezone(timedelta(hours=-5))))
        self.assertEqual(analyze([origin, later], [origin], NOW)['matches'][0]['gap_seconds'], 3600)

    def test_unverified_history_is_excluded_without_guessing_from_project(self):
        unknown = session('unknown')
        del unknown._history_group
        uncertain = session('uncertain')
        uncertain._history_uncertain = True
        origin = session('origin')
        origin.attribution_complete = False  # Project conflict alone does not establish relatedness.
        origin.project = None
        later = session('later', started=origin.ended + HOUR, ended=origin.ended + 2 * HOUR)
        value = analyze([unknown, uncertain, origin, later], [unknown, uncertain, origin], NOW)
        self.assertEqual(value['excluded']['uncertain_history'], 2)
        self.assertEqual(value['matched_sessions'], 1)
        self.assertFalse(value['matches'][0]['origin_usage_complete'])
        self.assertFalse(value['matched_usage_complete'])

    def test_current_verified_missing_source_archive_can_match_but_old_and_unverified_cannot(self):
        origin = session('origin')
        verified = session('verified', started=origin.ended + 3 * HOUR, ended=origin.ended + 4 * HOUR)
        verified.source_state, verified.source_deleted, verified.archive_files = 'archive', True, 1
        old = session('old', started=origin.ended + HOUR, ended=origin.ended + 2 * HOUR)
        old.source_state, old.source_deleted, old.archive_old_parser = 'archive', True, True
        unverified = session('unverified', started=origin.ended + SECOND, ended=origin.ended + HOUR)
        unverified.archive_unverified = True
        not_missing = session('not-missing')
        not_missing.source_state = 'archive'
        value = analyze([origin, old, unverified, verified, not_missing], [origin, verified, old, unverified, not_missing], NOW)
        self.assertEqual(value['timeline_excluded']['archive_old_parser'], 1)
        self.assertEqual(value['timeline_excluded']['archive_unverified'], 2)
        self.assertEqual(value['matches'][0]['gap_seconds'], 3 * 3600)
        self.assertEqual(value['eligible_sessions'], 2)
        self.assertPartition(value)

    def test_targets_are_normalized_but_never_reconstructed_from_final_project(self):
        origin = session('origin', targets=('C:/Work/SRC/A.py',))
        later = session('later', started=origin.ended + HOUR, ended=origin.ended + 2 * HOUR,
                        targets=(r'c:\work\src\a.py',))
        unresolved = session('relative', targets=('src/a.py',))
        unresolved.project = 'C:/Work'
        value = analyze([origin, later, unresolved], [origin, unresolved], NOW)
        self.assertEqual(value['matched_sessions'], 1)
        self.assertEqual(value['excluded']['missing_targets'], 1)

    def test_whole_session_tokens_are_disjoint_and_flags_do_not_depend_on_calls_or_models(self):
        origin = session('origin')
        origin.tokens.update(output=20, reasoning=10)
        origin.calls_complete = origin.models_complete = False
        later = session('later', started=origin.ended + HOUR, ended=origin.ended + 2 * HOUR)
        later.tokens_complete = False
        unmatched = session('unmatched', targets=('/work/other',), agent='claude-code', tokens=50)
        unmatched.tokens_complete = False
        value = analyze([origin, later, unmatched], [origin, unmatched], NOW)
        match, = value['matches']
        self.assertEqual((match['origin_tokens'], value['matched_origin_tokens']), (120, 120))
        self.assertTrue(match['origin_usage_complete'])
        self.assertFalse(match['later_usage_complete'])
        self.assertEqual(value['eligible_origin_tokens'], 170)
        self.assertFalse(value['eligible_usage_complete'])
        self.assertTrue(value['matched_usage_complete'])
        agents = {row['agent']: row for row in value['agents']}
        self.assertEqual(agents['codex']['matched_origin_tokens'], 120)
        self.assertEqual(agents['claude-code']['observed_unmatched_sessions'], 1)

    def test_top_five_and_ties_are_deterministic_in_any_input_order(self):
        origins, timeline = [], []
        for number in range(8):
            origin = session('origin-%d' % number, targets=('/work/%d' % number,))
            later = session('later-%d' % number, started=origin.ended + HOUR, ended=origin.ended + 2 * HOUR,
                            targets=origin.files_edited)
            origins.append(origin)
            timeline.extend([origin, later])
        first = analyze(timeline, origins, NOW)
        second = analyze(reversed(timeline), reversed(origins), NOW)
        self.assertEqual(first, second)
        self.assertEqual((first['matched_sessions'], len(first['matches'])), (8, 5))
        self.assertEqual([row['origin_id'] for row in first['matches']], sorted(row['origin_id'] for row in first['matches']))
        self.assertEqual(first['gap_seconds'], dict(minimum=3600, median=3600, maximum=3600))

    def test_equal_start_candidates_choose_the_opaque_id_across_different_targets(self):
        origin = session('origin', targets=('/work/a.py', '/work/b.py'))
        first = session('first', started=origin.ended + HOUR, ended=origin.ended + 2 * HOUR,
                        targets=('/work/a.py',))
        second = session('second', started=first.started, ended=first.ended, targets=('/work/b.py',))
        def row_id(value):
            return hashlib.sha256((value.agent + ':' + value.source + '\0' + value.session_id).encode()).hexdigest()[:24]
        value = analyze([second, origin, first], [origin], NOW)
        self.assertEqual(value['matches'][0]['later_id'], min(row_id(first), row_id(second)))

    def test_no_paths_native_ids_commands_or_session_objects_reach_the_result(self):
        origin = session(PRIVATE + '-origin', targets=('/work/' + PRIVATE,))
        origin.notes = [PRIVATE + '-command-or-tool-output']
        later = session(PRIVATE + '-later', started=origin.ended + HOUR, ended=origin.ended + 2 * HOUR,
                        targets=origin.files_edited)
        value = analyze([origin, later], [origin], NOW)
        encoded = json.dumps(value, allow_nan=False)
        self.assertNotIn(PRIVATE, encoded)
        self.assertNotIn('/work/', encoded)
        self.assertNotIn('/logs/', encoded)
        self.assertEqual(set(value['matches'][0]), {'origin_id', 'later_id', 'origin_agent', 'later_agent',
                         'gap_seconds', 'matching_targets', 'origin_tokens', 'later_tokens',
                         'origin_usage_complete', 'later_usage_complete'})

    def test_calculation_does_not_read_files_or_launch_git_or_another_process(self):
        origin = session('origin')
        later = session('later', started=origin.ended + HOUR, ended=origin.ended + 2 * HOUR)
        def forbidden(*args, **kwargs):
            raise AssertionError('external access')
        with patch('builtins.open', forbidden), patch.object(Path, 'resolve', forbidden), \
                patch.object(Path, 'stat', forbidden), patch.object(Path, 'read_bytes', forbidden), \
                patch.object(Path, 'read_text', forbidden), patch.object(os, 'stat', forbidden), \
                patch.object(subprocess, 'run', forbidden), patch.object(subprocess, 'Popen', forbidden):
            self.assertEqual(analyze([origin, later], [origin], NOW)['matched_sessions'], 1)

    def test_common_target_related_runs_are_jumped_without_quadratic_group_comparisons(self):
        class Group:
            comparisons = 0
            def __init__(self, value): self.value = value
            def __hash__(self): return hash(self.value)
            def __eq__(self, other):
                Group.comparisons += 1
                return isinstance(other, Group) and self.value == other.value
        size = 2000
        related = Group('family')
        start = NOW - 2 * DAY
        origins = [session('related-%d' % number, started=start + number * SECOND,
                           ended=start + number * SECOND, group=related) for number in range(size)]
        independent = session('independent', started=start + (size + 1) * SECOND,
                              ended=start + (size + 2) * SECOND, group=Group('other'))
        value = analyze(origins + [independent], origins, NOW)
        self.assertEqual(value['matched_sessions'], size)
        self.assertLess(Group.comparisons, 5 * size)

    def test_cutoff_must_be_an_explicit_aware_scan_time(self):
        for cutoff in (None, NOW.replace(tzinfo=None), '2026-10-28T12:00:00Z'):
            with self.subTest(cutoff=cutoff), self.assertRaises(ValueError):
                analyze([], [], cutoff)
        value = analyze([], [], NOW)
        self.assertEqual(value['cutoff'], NOW.isoformat())
        self.assertEqual(value['gap_seconds'], dict(minimum=None, median=None, maximum=None))
        self.assertPartition(value)


if __name__ == '__main__':
    unittest.main()
