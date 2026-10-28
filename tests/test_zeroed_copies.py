"""Zeroed Claude copies need an exact verified witness; all records here are invented."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler.dashboard import project_view, session_view
from pler.usage.accounting import MAX_COUNT
from pler.usage import claude_code
from pler.usage.cache import FileCache, version
from pler.usage.records import total
from test_logs import claude_reply, write_jsonl

SECRET = 'INVENTED-PRIVATE-TEXT-AND-COMMAND'
FIELDS = ('input_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens', 'output_tokens')
GOOD = dict(input_tokens=10, cache_read_input_tokens=100, cache_creation_input_tokens=20,
            output_tokens=50, output_tokens_details=dict(thinking_tokens=30))


def reply(usage=None):
    return claude_reply('s', 'm', 'r', copy.deepcopy(GOOD if usage is None else usage),
                        [dict(type='text', text=SECRET),
                         dict(type='tool_use', id='tool', name='Bash', input=dict(command=SECRET))],
                        '2026-10-28T10:00:00Z')


def zeroed():
    return reply(dict.fromkeys(FIELDS, 0) | dict(output_tokens_details=dict(thinking_tokens=30)))


def prompt():
    return dict(type='user', sessionId='s', uuid='prompt', timestamp='2026-10-28T09:59:00Z',
                message=dict(content=SECRET))


class ZeroedCopyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.a, self.b = self.root/'a.jsonl', self.root/'b.jsonl'

    def read(self, rows):
        write_jsonl(self.a, rows)
        issues = []
        sessions = claude_code.read([self.a], issues)
        return sessions, issues

    def test_verified_snapshot_resolves_zeroed_copies_without_adding_calls_or_tokens(self):
        for rows in ([zeroed(), reply(), zeroed(), reply()], [reply(), zeroed(), reply(), zeroed()]):
            with self.subTest(zeroed_first=rows[0]['message']['usage']['output_tokens'] == 0):
                sessions, issues = self.read(rows)
                session, = sessions
                self.assertEqual((session.calls, total(session.tokens), session.tokens['reasoning']), (1, 180, 30))
                self.assertEqual(issues, [])
                self.assertTrue(session.tokens_complete)
                self.assertIn('reconciled_copies', session.issues)
                self.assertEqual(session.tools, {'Bash': 1})
                self.assertNotIn(SECRET, json.dumps(project_view(sessions, {}, days=0)))

    def test_a_verified_copy_in_another_file_is_a_witness_independent_of_path_order(self):
        write_jsonl(self.a, [zeroed(), zeroed()])
        write_jsonl(self.b, [reply(), reply()])
        result = []
        for paths in ([self.a, self.b], [self.b, self.a]):
            issues = []
            sessions = claude_code.read(paths, issues)
            self.assertEqual(issues, [])
            session, = sessions
            self.assertEqual((session.calls, total(session.tokens)), (1, 180))
            self.assertTrue(session.tokens_complete)
            result.append(session.as_dict())
        self.assertEqual(result[0], result[1])

    def test_zeroed_copy_alone_is_not_verified_zero_usage(self):
        sessions, issues = self.read([prompt(), zeroed()])
        self.assertEqual((sessions[0].calls, total(sessions[0].tokens)), (0, 0))
        self.assertEqual(issues, [(str(self.a), 'InconsistentReasoning')])
        self.assertFalse(sessions[0].tokens_complete)
        self.assertFalse(project_view(sessions, dict(skipped=issues), days=0)['quality']['tokens_complete'])
        self.assertNotIn('reconciled_copies', sessions[0].issues)

    def test_mismatched_thinking_model_message_or_request_cannot_be_a_witness(self):
        mutations = [('thinking', lambda r: r['message']['usage']['output_tokens_details'].update(thinking_tokens=31)),
                     ('model', lambda r: r['message'].update(model='different-model')),
                     ('message', lambda r: r['message'].update(id='different-message')),
                     ('request', lambda r: r.update(requestId='different-request'))]
        for name, mutate in mutations:
            with self.subTest(mismatch=name):
                bad = zeroed();mutate(bad)
                sessions, issues = self.read([reply(), bad])
                self.assertEqual((sum(s.calls for s in sessions), sum(total(s.tokens) for s in sessions)), (1, 180))
                self.assertEqual(issues, [(str(self.a), 'InconsistentReasoning')])
                self.assertFalse(project_view(sessions, dict(skipped=issues), days=0)['quality']['tokens_complete'])
                self.assertTrue(all('reconciled_copies' not in s.issues for s in sessions))

    def test_nonzero_invalid_usage_remains_malformed_even_with_a_good_copy(self):
        bad = zeroed();bad['message']['usage']['input_tokens'] = 1
        sessions, issues = self.read([reply(), bad])
        self.assertEqual((sessions[0].calls, total(sessions[0].tokens)), (1, 180))
        self.assertEqual(issues, [(str(self.a), 'MalformedRows')])
        self.assertFalse(sessions[0].tokens_complete)

    def test_missing_or_non_exact_zero_fields_and_empty_identity_cannot_be_reconciled(self):
        mutations = [('missing output', lambda r: r['message']['usage'].pop('output_tokens')),
                     ('missing cache', lambda r: r['message']['usage'].pop('cache_read_input_tokens')),
                     ('boolean', lambda r: r['message']['usage'].update(input_tokens=False)),
                     ('float', lambda r: r['message']['usage'].update(input_tokens=0.0)),
                     ('string', lambda r: r['message']['usage'].update(input_tokens='0')),
                     ('empty message', lambda r: r['message'].update(id='')),
                     ('empty request', lambda r: r.update(requestId='')),
                     ('empty model', lambda r: r['message'].update(model='')),
                     ('blank message', lambda r: r['message'].update(id='  ')),
                     ('blank request', lambda r: r.update(requestId='  ')),
                     ('blank model', lambda r: r['message'].update(model='  ')),
                     ('unknown model', lambda r: r['message'].update(model='unknown'))]
        for name, mutate in mutations:
            with self.subTest(ineligible=name):
                bad = zeroed();mutate(bad)
                sessions, issues = self.read([reply(), bad])
                self.assertEqual((sessions[0].calls, total(sessions[0].tokens)), (1, 180))
                self.assertEqual(issues, [(str(self.a), 'MalformedRows')])
                self.assertNotIn('reconciled_copies', sessions[0].issues)

    def test_invalid_thinking_values_are_never_zeroed_copy_candidates(self):
        for value in (True, 30.0, '30', -1, MAX_COUNT + 1):
            with self.subTest(thinking=value):
                bad = zeroed();bad['message']['usage']['output_tokens_details']['thinking_tokens'] = value
                sessions, issues = self.read([reply(), bad])
                self.assertEqual((sessions[0].calls, total(sessions[0].tokens)), (1, 180))
                self.assertEqual(issues, [(str(self.a), 'MalformedRows')])
                self.assertNotIn('reconciled_copies', sessions[0].issues)

    def test_an_older_smaller_snapshot_cannot_resolve_the_selected_larger_snapshot(self):
        older = reply();older['message']['usage']['output_tokens'] = 40
        current = reply();current['message']['usage']['output_tokens_details']['thinking_tokens'] = 35
        sessions, issues = self.read([older, zeroed(), current])
        self.assertEqual((sessions[0].calls, total(sessions[0].tokens), sessions[0].tokens['reasoning']), (1, 180, 35))
        self.assertEqual(issues, [(str(self.a), 'InconsistentReasoning')])
        self.assertFalse(sessions[0].tokens_complete)
        self.assertNotIn('reconciled_copies', sessions[0].issues)

    def test_crossing_valid_snapshots_do_not_resolve_the_zeroed_copy(self):
        other = reply();other['message']['usage'].update(input_tokens=20, output_tokens=40)
        sessions, issues = self.read([reply(), other, zeroed()])
        self.assertEqual((sessions[0].calls, total(sessions[0].tokens)), (1, 0))
        self.assertEqual(issues, [(str(self.a), 'InconsistentReasoning')])
        self.assertFalse(sessions[0].tokens_complete)
        self.assertIn('conflicting_usage', sessions[0].issues)
        self.assertNotIn('reconciled_copies', sessions[0].issues)

    def test_other_corruption_is_not_hidden_by_a_resolved_zeroed_copy(self):
        for kind in ('json', 'negative'):
            with self.subTest(kind=kind):
                rows = [reply(), zeroed()]
                if kind == 'negative':
                    bad = reply();bad['message']['usage']['input_tokens'] = -1;rows.append(bad)
                write_jsonl(self.a, rows)
                if kind == 'json':
                    with self.a.open('a', encoding='utf-8') as stream:stream.write('{"unfinished":\n')
                issues = [];sessions = claude_code.read([self.a], issues)
                self.assertEqual((sessions[0].calls, total(sessions[0].tokens)), (1, 180))
                self.assertEqual(issues, [(str(self.a), 'MalformedRows')])
                self.assertFalse(sessions[0].tokens_complete)

    def test_original_and_cached_reads_agree_and_cache_never_contains_transcript_text(self):
        for witnessed in (True, False):
            with self.subTest(witnessed=witnessed), patch.dict(os.environ, PLER_CACHE_DIR=str(self.root/'cache')):
                write_jsonl(self.a, [prompt(), zeroed()] + ([reply()] if witnessed else []))
                cache = FileCache('zeroed-'+str(witnessed), version(claude_code))
                issues = [];first = claude_code.read([self.a], issues, cache=cache);cache.save()
                saved = cache.path.read_text('utf-8')
                for private in (SECRET, '"command"', '"text"'):
                    self.assertNotIn(private, saved)
                cached = FileCache('zeroed-'+str(witnessed), version(claude_code))
                again = []
                with patch.object(claude_code, '_rows', side_effect=AssertionError('unchanged log reopened')):
                    second = claude_code.read([self.a], again, cache=cached)
                self.assertEqual([s.as_dict() for s in first], [s.as_dict() for s in second])
                self.assertEqual(issues, again)
                self.assertEqual(len(issues), int(not witnessed))
                public = project_view(second, dict(skipped=again), days=0)
                self.assertNotIn(SECRET, json.dumps(public))

    def test_cached_candidate_resolves_when_a_witness_arrives_and_warns_again_when_it_leaves(self):
        with patch.dict(os.environ, PLER_CACHE_DIR=str(self.root/'cache')):
            write_jsonl(self.a, [prompt(), zeroed()])
            key = version(claude_code)
            cache = FileCache('contextual-witness', key)
            issues = [];claude_code.read([self.a], issues, cache=cache);cache.save()
            self.assertEqual(issues, [(str(self.a), 'InconsistentReasoning')])
            write_jsonl(self.b, [reply()])
            parse = claude_code._rows
            def only_new_file(path):
                self.assertNotEqual(path, self.a, 'unchanged cached candidate was reopened')
                return parse(path)
            cache = FileCache('contextual-witness', key)
            with patch.object(claude_code, '_rows', side_effect=only_new_file):
                issues = [];resolved = claude_code.read([self.a, self.b], issues, cache=cache)
            cache.save()
            self.assertEqual(issues, [])
            self.assertEqual((resolved[0].calls, total(resolved[0].tokens)), (1, 180))
            self.assertTrue(resolved[0].tokens_complete)
            self.assertIn('reconciled_copies', resolved[0].issues)
            cache = FileCache('contextual-witness', key)
            with patch.object(claude_code, '_rows', side_effect=AssertionError('unchanged candidate reopened')):
                issues = [];unresolved = claude_code.read([self.a], issues, cache=cache)
            self.assertEqual(issues, [(str(self.a), 'InconsistentReasoning')])
            self.assertEqual((unresolved[0].calls, total(unresolved[0].tokens)), (0, 0))
            self.assertFalse(unresolved[0].tokens_complete)
            self.assertNotIn('reconciled_copies', unresolved[0].issues)

    def test_unresolved_copy_in_a_different_session_marks_the_canonical_public_row_incomplete(self):
        good = reply();good['sessionId'] = 'a'
        bad = zeroed();bad['sessionId'] = 'z'
        bad['message']['usage']['output_tokens_details']['thinking_tokens'] = 31
        write_jsonl(self.a, [good]);write_jsonl(self.b, [bad])
        issues = [];sessions = claude_code.read([self.a, self.b], issues)
        canonical = next(s for s in sessions if s.session_id == 'a')
        self.assertEqual((canonical.calls, total(canonical.tokens)), (1, 180))
        self.assertEqual(issues, [(str(self.b), 'InconsistentReasoning')])
        self.assertFalse(canonical.tokens_complete)
        self.assertFalse(session_view(canonical)['quality']['tokens_complete'])
        self.assertFalse(project_view(sessions, dict(skipped=issues), days=0)['quality']['tokens_complete'])


if __name__ == '__main__':unittest.main()
