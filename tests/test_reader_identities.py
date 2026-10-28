"""Consumed identities stay strict; unrelated fields cannot reject verified Codex usage.

Only invented records in temporary folders are used. No real agent log is read.
"""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler.usage import codex
from pler.usage.cache import FileCache, version
from pler.usage.records import total
from test_logs import write_jsonl

SECRET = 'INVENTED-PRIVATE-PROMPT-AND-COMMAND'
IDENTITIES = ('session_id', 'id', 'parent_thread_id', 'response_id', 'compaction_response_id', 'turn_id', 'call_id')


def record(kind, payload, at='2026-10-28T09:00:00Z'):
    return dict(type=kind, payload=payload, timestamp=at)


def example():
    return [
        record('session_meta', dict(id='session', cwd='/invented/project', base_instructions=SECRET)),
        record('turn_context', dict(model='invented-model')),
        record('event_msg', dict(type='task_started', turn_id='turn-one')),
        record('response_item', dict(type='function_call', call_id='tool-one', name='exec', arguments=SECRET)),
        record('token_usage_record', dict(response_id='reply', usage=dict(input_tokens=100, cached_input_tokens=20,
                                                                       output_tokens=10, reasoning_output_tokens=5))),
        record('event_msg', dict(type='task_complete', turn_id='turn-one', duration_ms=4000, error=False)),
        record('event_msg', dict(type='turn_aborted', turn_id='turn-two')),
    ]


class ReaderIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = self.root/'rollout-invented.jsonl'

    def test_ignored_rows_with_unrelated_identities_keep_their_times_without_a_warning(self):
        ignored = [record('response_item', dict(type='message', content=[dict(text=SECRET)],
                                              **{name: [] for name in IDENTITIES}), '2026-10-28T08:00:00Z'),
                   record('event_msg', dict(type='unconsumed-event', text=SECRET,
                                           **{name: 42 for name in IDENTITIES}), '2026-10-28T10:00:00Z')]
        write_jsonl(self.log, example()+ignored)
        sessions, issues = codex.read([self.log])
        session, = sessions
        self.assertEqual((session.calls, total(session.tokens), issues), (1, 110, []))
        self.assertEqual(session.started.isoformat(), '2026-10-28T08:00:00+00:00')
        self.assertEqual(session.ended.isoformat(), '2026-10-28T10:00:00+00:00')
        self.assertTrue(session.tokens_complete)
        self.assertNotIn(SECRET, json.dumps(session.as_dict()))

    def test_consumed_record_projections_ignore_unrelated_identity_fields(self):
        cases = [(example()[0], {'session_id', 'id', 'parent_thread_id'}),
                 (example()[1], set()), (example()[2], {'turn_id'}),
                 (example()[3], {'call_id'}), (example()[4], {'response_id'}),
                 (example()[5], {'turn_id'}), (example()[6], {'turn_id'}),
                 (record('compacted', dict(compaction_response_id='compaction')), {'compaction_response_id'}),
                 (record('event_msg', dict(type='token_count', info=None)), set()),
                 (record('response_item', dict(type='custom_tool_call', name='edit', call_id='custom')), {'call_id'})]
        for row, consumed in cases:
            with self.subTest(kind=row['type'], sub=row['payload'].get('type')):
                augmented = copy.deepcopy(row)
                augmented['payload'].update({name: {SECRET: []} for name in IDENTITIES if name not in consumed})
                self.assertEqual(codex._slim(augmented), codex._slim(row))

    def test_used_non_string_identities_are_still_rejected(self):
        cases = [(example()[0], name) for name in ('session_id', 'id', 'parent_thread_id')]
        cases += [(example()[2], 'turn_id'), (example()[3], 'call_id'), (example()[4], 'response_id'),
                  (example()[5], 'turn_id'), (example()[6], 'turn_id'),
                  (record('compacted', dict(compaction_response_id='compaction')), 'compaction_response_id'),
                  (record('response_item', dict(type='custom_tool_call', name='edit', call_id='custom')), 'call_id')]
        for row, name in cases:
            for invalid in ([], {}, True, 3):
                with self.subTest(kind=row['type'], identity=name, invalid=invalid):
                    damaged = copy.deepcopy(row)
                    damaged['payload'][name] = invalid
                    with self.assertRaises(ValueError):
                        codex._slim(damaged)

    def test_bad_used_identity_keeps_the_file_warning_and_preserves_other_usage(self):
        bad = example()[4]
        bad['payload']['response_id'] = []
        write_jsonl(self.log, example()+[bad])
        sessions, issues = codex.read([self.log])
        self.assertEqual((sessions[0].calls, total(sessions[0].tokens)), (1, 110))
        self.assertEqual(issues, [(str(self.log), 'MalformedRows')])
        self.assertFalse(sessions[0].tokens_complete)

    def test_original_and_cached_reads_agree_and_never_keep_private_text(self):
        for damaged in (False, True):
            with self.subTest(damaged=damaged), patch.dict(os.environ, PLER_CACHE_DIR=str(self.root/'cache')):
                rows = example()
                rows[4]['payload']['id'] = {SECRET: True}  # not the response identity
                rows.append(record('response_item', dict(type='message', id=42, content=[dict(text=SECRET)]),
                                   '2026-10-28T11:00:00Z'))
                if damaged:
                    bad = example()[4]
                    bad['payload']['response_id'] = []
                    rows.append(bad)
                write_jsonl(self.log, rows)
                cache = FileCache('identities-'+str(damaged), version(codex))
                first, issues = codex.read([self.log], cache)
                cache.save()
                saved = cache.path.read_text('utf-8')
                for private in (SECRET, 'base_instructions', 'arguments', 'content'):
                    self.assertNotIn(private, saved)
                cached = FileCache('identities-'+str(damaged), version(codex))
                with patch.object(codex, '_rows', side_effect=AssertionError('unchanged log was reopened')):
                    second, again = codex.read([self.log], cached)
                self.assertEqual([s.as_dict() for s in first], [s.as_dict() for s in second])
                self.assertEqual(issues, again)
                self.assertEqual(len(issues), int(damaged))
                self.assertEqual((second[0].calls, total(second[0].tokens)), (1, 110))
                self.assertEqual(second[0].ended.isoformat(), '2026-10-28T11:00:00+00:00')

    def test_json_corruption_is_still_reported_even_in_an_ignored_record(self):
        write_jsonl(self.log, example())
        with self.log.open('a', encoding='utf-8') as stream:
            stream.write('{"type":"unconsumed","payload":{"id":NaN}}\n')
        sessions, issues = codex.read([self.log])
        self.assertEqual(total(sessions[0].tokens), 110)
        self.assertEqual(issues, [(str(self.log), 'MalformedRows')])


if __name__ == '__main__':
    unittest.main()
