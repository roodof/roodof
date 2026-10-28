"""Retained counters do not prove inherited boundaries; activity without usage must not disappear."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler.dashboard import project_view
from pler.usage import codex
from pler.usage.cache import FileCache
from pler.usage.records import total
from test_logs import write_jsonl


def row(kind, payload, at='2026-10-28T10:00:00Z'):
    return dict(type=kind, payload=payload, timestamp=at)


def meta(identity='s', parent=None):
    payload=dict(id=identity, cwd='/synthetic/project')
    if parent is not None:
        payload['parent_thread_id']=parent
    return row('session_meta', payload)


def cumulative(value):
    return row('event_msg', dict(type='token_count', info=dict(
        total_token_usage=dict(input_tokens=value, output_tokens=0))))


def response(value=100, identity='r'):
    return row('token_usage_record', dict(response_id=identity,
        usage=dict(input_tokens=value, output_tokens=0)))


def event(kind, **payload):
    return row('event_msg', dict(type=kind, **payload))


class HistoryBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.a,self.b,self.c=(self.root/name for name in
            ('rollout-a.jsonl','rollout-b.jsonl','rollout-c.jsonl'))

    def assert_incomplete(self, session):
        self.assertFalse(session.tokens_complete)
        self.assertIn('unreconciled_totals', session.issues)

    def test_related_different_cumulative_totals_keep_numbers_but_warn_about_overlap(self):
        for reverse in (False,True):
            parent=[meta('parent'),cumulative(100)]
            child=[meta('child','parent'),cumulative(150)]
            write_jsonl(self.a,child if reverse else parent)
            write_jsonl(self.b,parent if reverse else child)
            for paths in ([self.a,self.b],[self.b,self.a]):
                with self.subTest(reverse=reverse,paths_reversed=paths[0]==self.b):
                    sessions,issues=codex.read(paths)
                    self.assertEqual((len(sessions),sum(total(s.tokens) for s in sessions),issues),(2,250,[]))
                    for session in sessions:
                        self.assert_incomplete(session)
                    self.assertFalse(project_view(sessions,{},days=0)['quality']['tokens_complete'])

    def test_related_response_and_cumulative_history_do_not_claim_disjointness(self):
        write_jsonl(self.a,[meta('parent'),response(100)])
        write_jsonl(self.b,[meta('child','parent'),cumulative(150)])
        sessions,issues=codex.read([self.a,self.b])
        self.assertEqual((sum(total(s.tokens) for s in sessions),sum(s.calls for s in sessions),issues),(250,1,[]))
        for session in sessions:
            self.assert_incomplete(session)

    def test_cumulative_child_with_missing_parent_is_incomplete(self):
        write_jsonl(self.a,[meta('child','missing-parent'),cumulative(150)])
        sessions,issues=codex.read([self.a])
        session,=sessions
        self.assertEqual((total(session.tokens),session.parent_id,issues),(150,'missing-parent',[]))
        self.assert_incomplete(session)

    def test_unrelated_cumulative_histories_are_not_marked_related_by_equal_numbers(self):
        write_jsonl(self.a,[meta('one'),cumulative(100)])
        write_jsonl(self.b,[meta('two'),cumulative(100)])
        sessions,issues=codex.read([self.a,self.b])
        self.assertEqual((len(sessions),sum(total(s.tokens) for s in sessions),issues),(2,200,[]))
        self.assertTrue(all(s.tokens_complete for s in sessions))

    def test_identified_responses_without_cumulative_history_remain_counted_once(self):
        write_jsonl(self.a,[meta('parent'),response(100,'one')])
        write_jsonl(self.b,[meta('child','parent'),response(50,'two')])
        sessions,issues=codex.read([self.a,self.b])
        self.assertEqual((sum(total(s.tokens) for s in sessions),sum(s.calls for s in sessions),issues),(150,2,[]))
        self.assertTrue(all(s.tokens_complete for s in sessions))

    def test_contradictory_parent_metadata_does_not_choose_last_parent(self):
        for parents in (('first','second'),('second','first')):
            with self.subTest(parents=parents):
                write_jsonl(self.a,[meta('child',parents[0]),meta('child',parents[1]),cumulative(100)])
                session,=codex.read([self.a])[0]
                self.assertIsNone(session.parent_id)
                self.assertFalse(session.attribution_complete)
                self.assertIn('shared_attribution',session.issues)
                self.assert_incomplete(session)
                self.assertEqual(total(session.tokens),100)

    def test_empty_parent_does_not_erase_real_parent_evidence(self):
        write_jsonl(self.a,[meta('child','missing-parent'),meta('child',''),cumulative(100)])
        session,=codex.read([self.a])[0]
        self.assertEqual(session.parent_id,'missing-parent')
        self.assert_incomplete(session)

    def test_cyclic_parent_references_are_bounded_and_not_used_as_proven_lineage(self):
        for self_parent in (True,False):
            write_jsonl(self.a,[meta('one','one' if self_parent else 'two'),cumulative(100)])
            paths=[self.a]
            if not self_parent:
                write_jsonl(self.b,[meta('two','one'),cumulative(150)])
                paths.append(self.b)
            with self.subTest(self_parent=self_parent):
                sessions,issues=codex.read(paths)
                self.assertEqual(sum(total(s.tokens) for s in sessions),100 if self_parent else 250)
                self.assertEqual(issues,[])
                for session in sessions:
                    self.assertIsNone(session.parent_id)
                    self.assert_incomplete(session)

    def test_subagent_threads_inside_one_session_are_not_contradictory_parents(self):
        # Real Codex shape: subagent files keep the root session_id, have their own thread id and
        # name the root or another subagent thread as parent.
        def thread(identity, parent=None):
            payload=dict(session_id='root', id=identity, cwd='/synthetic/project')
            if parent: payload['parent_thread_id']=parent
            return row('session_meta', payload)
        write_jsonl(self.a,[thread('root'),response(100,'one')])
        write_jsonl(self.b,[thread('first','root'),response(50,'two')])
        write_jsonl(self.c,[thread('nested','first'),response(25,'three')])
        for paths in ([self.a,self.b,self.c],[self.c,self.b,self.a]):
            with self.subTest(reversed=paths[0]==self.c):
                session,=codex.read(paths)[0]
                self.assertEqual((total(session.tokens),session.calls,session.parent_id),(175,3,None))
                self.assertTrue(session.tokens_complete and session.attribution_complete)
                self.assertFalse({'shared_attribution','unreconciled_totals'}&session.issues)

    def test_outside_parent_of_a_merged_session_is_still_evidence(self):
        def thread(identity, parent=None):
            payload=dict(session_id='fork', id=identity)
            if parent: payload['parent_thread_id']=parent
            return row('session_meta', payload)
        write_jsonl(self.a,[thread('fork','origin'),thread('helper','fork'),response(100)])
        session,=codex.read([self.a])[0]
        self.assertEqual(session.parent_id,'origin')
        self.assertTrue(session.attribution_complete)
        write_jsonl(self.a,[thread('fork','origin'),thread('helper','elsewhere'),response(100)])
        session,=codex.read([self.a])[0]
        self.assertIsNone(session.parent_id)
        self.assertIn('shared_attribution',session.issues)
        write_jsonl(self.a,[thread('fork'),thread('helper','helper'),response(100)])
        session,=codex.read([self.a])[0]
        self.assertIn('shared_attribution',session.issues)

    def test_compaction_without_cumulative_checkpoint_still_marks_incomplete_history(self):
        write_jsonl(self.a,[meta(),response(),row('compacted',dict(compaction_response_id='r'))])
        session,=codex.read([self.a])[0]
        self.assertEqual((total(session.tokens),session.calls),(100,1))
        self.assert_incomplete(session)

    def test_compaction_only_is_an_explicit_unknown_boundary_not_a_known_empty_session(self):
        write_jsonl(self.a,[meta(),row('compacted',dict(compaction_response_id='r'))])
        sessions,issues=codex.read([self.a])
        session,=sessions
        self.assertEqual((total(session.tokens),session.calls,issues),(0,0,[]))
        self.assert_incomplete(session)

    def test_abort_only_session_is_preserved(self):
        write_jsonl(self.a,[meta(),event('turn_aborted',turn_id='turn')])
        sessions,issues=codex.read([self.a])
        session,=sessions
        self.assertEqual((session.aborted,session.calls,total(session.tokens),issues),(1,0,0,[]))

    def test_tool_only_session_is_preserved(self):
        write_jsonl(self.a,[meta(),row('response_item',dict(type='function_call',name='synthetic-tool',call_id='tool'))])
        session,=codex.read([self.a])[0]
        self.assertEqual((session.tools,session.calls,total(session.tokens)),({'synthetic-tool':1},0,0))

    def test_quota_only_session_is_preserved_without_inventing_calls(self):
        write_jsonl(self.a,[meta(),event('token_count',info=None,rate_limits=dict(primary=dict(
            used_percent=25,window_minutes=300,resets_at=1793199600)))])
        session,=codex.read([self.a])[0]
        self.assertEqual((len(session.quota),session.quota[0][2],session.calls,total(session.tokens)),(1,25,0,0))

    def test_successful_completion_only_is_preserved_even_without_duration(self):
        for duration in (None,0,200):
            with self.subTest(duration=duration):
                payload=dict(turn_id='turn')
                if duration is not None:
                    payload['duration_ms']=duration
                write_jsonl(self.a,[meta(),event('task_complete',**payload)])
                session,=codex.read([self.a])[0]
                self.assertEqual((session.active_ms,session.calls,session.errors),(duration,0,0))

    def test_metadata_only_and_context_only_files_do_not_invent_active_sessions(self):
        for extra in ([],[row('turn_context',dict(model='synthetic',cwd='/synthetic/project'))]):
            with self.subTest(context=bool(extra)):
                write_jsonl(self.a,[meta()]+extra)
                self.assertEqual(codex.read([self.a]),([],[]))

    def test_copied_abort_only_event_is_counted_once_and_owner_is_uncertain(self):
        write_jsonl(self.a,[meta('one'),event('turn_aborted',turn_id='shared-turn')])
        write_jsonl(self.b,[meta('two'),event('turn_aborted',turn_id='shared-turn')])
        sessions,issues=codex.read([self.b,self.a])
        self.assertEqual((len(sessions),sum(s.aborted for s in sessions),issues),(1,1,[]))
        self.assertFalse(sessions[0].attribution_complete)

    def test_anonymous_abort_count_is_preserved_but_not_claimed_verified(self):
        write_jsonl(self.a,[meta(),event('turn_aborted')])
        session,=codex.read([self.a])[0]
        self.assertEqual(session.aborted,1)
        self.assertFalse(session.counts_complete)
        self.assertIn('unidentified_records',session.issues)

    def test_cached_history_flags_and_event_only_metrics_match_uncached_read(self):
        write_jsonl(self.a,[meta('parent'),cumulative(100)])
        write_jsonl(self.b,[meta('child','parent'),cumulative(150),event('turn_aborted',turn_id='t')])
        with patch.dict(os.environ,PLER_CACHE_DIR=str(self.root/'cache')):
            cache=FileCache('history-boundaries','synthetic-key')
            fresh,issues=codex.read([self.a,self.b],cache)
            cache.save()
            with patch.object(codex,'_rows',side_effect=AssertionError('reopened unchanged log')):
                cached,cached_issues=codex.read([self.b,self.a],FileCache('history-boundaries','synthetic-key'))
        self.assertEqual([s.as_dict() for s in fresh],[s.as_dict() for s in cached])
        self.assertEqual(issues,cached_issues)
        self.assertEqual((sum(total(s.tokens) for s in cached),sum(s.aborted for s in cached)),(250,1))
        self.assertTrue(all(not s.tokens_complete for s in cached))
