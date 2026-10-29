"""Synthetic reader evidence for the preregistered subsequent-edit observation."""
from datetime import datetime, timezone
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler.usage import claude_code, codex
from pler.usage.records import total
from pler.usage.reedit import analyze
from test_logs import claude_reply, write_jsonl


NOW = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)
EARLY = '2026-10-20T10:00:00Z'
END = '2026-10-20T11:00:00Z'
LATER = '2026-10-21T10:00:00Z'
LATER_END = '2026-10-21T11:00:00Z'
PRIVATE = 'PRIVATE-EDIT-EVIDENCE-CANARY'


def row(kind, payload, at=EARLY):
    return dict(type=kind, payload=payload, timestamp=at)


def meta(identity, cwd='/work/app', **extra):
    return row('session_meta', dict(id=identity, cwd=cwd, **extra))


def reply(identity, count=100, at=END):
    return row('token_usage_record', dict(response_id=identity,
               usage=dict(input_tokens=count, output_tokens=0)), at)


def edit(identity, target, at=END):
    return row('response_item', dict(type='custom_tool_call', name='apply_patch', call_id=identity,
               input='*** Begin Patch\n*** Update File: ' + target + '\n@@\n-' + PRIVATE
                     + '\n+changed\n*** End Patch'), at)


def claude_edit(identity, message, target, at=END, cwd='/work/app', count=100):
    value = claude_reply(identity, message, 'request-' + message,
                         dict(input_tokens=count, output_tokens=0),
                         [dict(type='tool_use', name='Edit', id='tool-' + message,
                               input=dict(file_path=target, old_string=PRIVATE))], at)
    value['cwd'] = cwd
    return value


class EditEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # The observation does not need a repository. Keep invented cwd spellings
        # independent of the viewing machine's actual filesystem.
        project = patch('pler.usage.projects.ProjectRoots._git_root', return_value=None)
        project.start()
        self.addCleanup(project.stop)

    def codex(self, streams):
        paths = []
        for index, rows in enumerate(streams):
            path = self.root / ('rollout-%d.jsonl' % index)
            write_jsonl(path, rows)
            paths.append(path)
        values, issues = codex.read(paths)
        self.assertEqual(issues, [])
        return {s.session_id: s for s in values}

    def claude(self, streams):
        paths = []
        for name, rows in streams:
            path = self.root / name
            write_jsonl(path, rows)
            paths.append(path)
        return {s.session_id: s for s in claude_code.read(paths)}

    def test_codex_relative_targets_use_each_turn_cwd_and_keep_usage(self):
        sessions = self.codex([[meta('origin', 'C:/Work/First'),
            row('turn_context', dict(model='test-model')),
            edit('first', 'src/MAIN.py', EARLY),
            row('turn_context', dict(cwd='C:/Work/Second')),
            edit('second', '../Third/other.py'), reply('response', 123)]])
        value = sessions['origin']
        self.assertEqual(value.files_edited, {r'c:\work\first\src\main.py', r'c:\work\third\other.py'})
        self.assertEqual((total(value.tokens), value.calls, value.tools), (123, 1, {'apply_patch': 2}))
        self.assertFalse(value._history_uncertain)

    def test_codex_posix_case_is_preserved_on_every_viewing_host(self):
        value = self.codex([[meta('origin', '/Work/First'), edit('first', 'src/Main.py', EARLY),
            row('turn_context', dict(cwd='/Work/Second')), edit('second', '../Third/main.py'),
            reply('response')]])['origin']
        self.assertEqual(value.files_edited, {'/Work/First/src/Main.py', '/Work/Third/main.py'})
        self.assertEqual((total(value.tokens), value.calls), (100, 1))

    def test_claude_relative_targets_use_each_edit_row_cwd_without_recounting_copies(self):
        first = claude_edit('origin', 'one', 'src/MAIN.py', EARLY, 'C:/Work/First', 100)
        second = claude_edit('origin', 'two', '../Third/other.py', END, 'C:/Work/Second', 200)
        values = self.claude([('origin.jsonl', [first, second]), ('copy.jsonl', [copy.deepcopy(first)])])
        value = values['origin']
        self.assertEqual(value.files_edited, {r'c:\work\first\src\main.py', r'c:\work\third\other.py'})
        self.assertEqual((total(value.tokens), value.calls, value.tools), (300, 2, {'Edit': 2}))

    def test_claude_posix_relative_and_absolute_targets_keep_logged_case(self):
        value = self.claude([('origin.jsonl', [
            claude_edit('origin', 'one', '../Main.py', EARLY, '/Work/src'),
            claude_edit('origin', 'two', '/work/Main.py', END, '/ignored')])])['origin']
        self.assertEqual(value.files_edited, {'/Work/Main.py', '/work/Main.py'})
        self.assertEqual((total(value.tokens), value.calls), (200, 2))

    def test_unresolved_relative_and_ambiguous_targets_are_not_invented(self):
        rows = [meta('origin', 'C:/Work'), edit('ambiguous', '/rooted.py', EARLY),
                edit('drive-relative', 'C:relative.py', EARLY), reply('response')]
        value = self.codex([rows])['origin']
        self.assertEqual(value.files_edited, set())
        self.assertEqual((total(value.tokens), value.calls, sum(value.tools.values())), (100, 1, 2))
        self.assertEqual(analyze([value], [value], NOW)['excluded']['missing_targets'], 1)

    def test_codex_parent_child_and_sibling_histories_are_one_group(self):
        parent = [meta('parent'), edit('p', 'same.py', EARLY), reply('p-response', at=END)]
        child = [meta('child', parent_thread_id='parent'), edit('c', 'same.py', LATER), reply('c-response', at=LATER_END)]
        sibling = [meta('sibling', parent_thread_id='parent'), edit('s', 'same.py', LATER), reply('s-response', at=LATER_END)]
        values = self.codex([parent, child, sibling])
        self.assertEqual(len({s._history_group for s in values.values()}), 1)
        self.assertFalse(any(s._history_uncertain for s in values.values()))
        self.assertEqual((sum(total(s.tokens) for s in values.values()), sum(s.calls for s in values.values())), (300, 3))
        self.assertEqual(analyze(list(values.values()), [values['parent']], NOW)['matched_sessions'], 0)

    def test_codex_internal_thread_parent_is_inside_merged_native_session(self):
        main = [meta('root-thread', session_id='native'), edit('main', 'same.py', EARLY), reply('main-response')]
        child = [meta('child-thread', session_id='native', parent_thread_id='root-thread'),
                 edit('child', 'same.py', LATER), reply('child-response', at=LATER_END)]
        value = self.codex([main, child])['native']
        self.assertIsNone(value.parent_id)
        self.assertFalse(value._history_uncertain)
        self.assertEqual((total(value.tokens), value.calls), (200, 2))

    def test_missing_codex_parent_excludes_observation_without_losing_usage(self):
        value = self.codex([[meta('child', parent_thread_id='not-retained'),
                            edit('edit', 'same.py'), reply('response', 321)]])['child']
        self.assertTrue(value._history_uncertain)
        self.assertEqual((total(value.tokens), value.calls), (321, 1))
        self.assertEqual(analyze([value], [value], NOW)['excluded']['uncertain_history'], 1)

    def test_cyclic_codex_parent_excludes_cycle_and_related_descendant(self):
        streams = [[meta('a', parent_thread_id='b'), edit('a-edit', 'same.py'), reply('a-response', 100)],
                   [meta('b', parent_thread_id='a'), edit('b-edit', 'same.py'), reply('b-response', 200)],
                   [meta('child', parent_thread_id='a'), edit('child-edit', 'same.py'), reply('child-response', 300)]]
        values = self.codex(streams)
        self.assertTrue(all(s._history_uncertain for s in values.values()))
        self.assertEqual((sum(total(s.tokens) for s in values.values()), sum(s.calls for s in values.values())), (600, 3))
        result = analyze(list(values.values()), list(values.values()), NOW)
        self.assertEqual((result['eligible_sessions'], result['excluded']['uncertain_history']), (0, 3))

    def test_codex_self_parent_is_not_treated_as_an_independent_session(self):
        value = self.codex([[meta('self', parent_thread_id='self'), edit('self-edit', 'same.py'),
                             reply('response', 123)]])['self']
        self.assertTrue(value._history_uncertain)
        self.assertEqual((total(value.tokens), value.calls), (123, 1))

    def test_shared_codex_response_connects_distinct_session_histories(self):
        values = self.codex([[meta('a'), edit('a-edit', 'same.py'), reply('shared', 100)],
                             [meta('b'), edit('b-edit', 'same.py', LATER), reply('shared', 100, LATER_END),
                              reply('unique', 50, LATER_END)]])
        self.assertEqual(values['a']._history_group, values['b']._history_group)
        self.assertEqual((sum(total(s.tokens) for s in values.values()), sum(s.calls for s in values.values())), (150, 2))
        self.assertEqual(analyze(list(values.values()), [values['a']], NOW)['matched_sessions'], 0)

    def test_claude_separate_subagent_without_parent_evidence_is_excluded(self):
        value = self.claude([('session/subagents/agent-worker.jsonl', [
            claude_edit('child', 'reply', 'same.py')])])['child']
        self.assertTrue(value._history_uncertain)
        self.assertEqual((total(value.tokens), value.calls), (100, 1))
        self.assertEqual(analyze([value], [value], NOW)['excluded']['uncertain_history'], 1)

    def test_claude_merged_native_session_retains_main_source_evidence_in_any_file_order(self):
        main = claude_edit('native', 'main', 'same.py', EARLY)
        child = claude_edit('native', 'child', 'same.py', END)
        # Classification must use every source, not the lexicographically smallest
        # source selected for a stable public row code.
        for streams in ([('z-main.jsonl', [main]), ('session/subagents/agent-worker.jsonl', [child])],
                        [('session/subagents/agent-worker.jsonl', [child]), ('z-main.jsonl', [main])]):
            value = self.claude(streams)['native']
            self.assertFalse(value._history_uncertain)
            self.assertEqual((total(value.tokens), value.calls), (200, 2))

    def test_shared_claude_response_connects_histories_without_losing_distinct_usage(self):
        first = claude_edit('a', 'shared', 'same.py', EARLY)
        repeated = copy.deepcopy(first)
        repeated['sessionId'] = 'b'
        repeated['timestamp'] = LATER
        second = claude_edit('b', 'unique', 'same.py', LATER_END, count=50)
        values = self.claude([('a.jsonl', [first]), ('b.jsonl', [repeated, second])])
        self.assertEqual(values['a']._history_group, values['b']._history_group)
        self.assertEqual((sum(total(s.tokens) for s in values.values()), sum(s.calls for s in values.values())), (150, 2))
        self.assertEqual(analyze(list(values.values()), [values['a']], NOW)['matched_sessions'], 0)

    def test_shared_claude_prompt_uuid_connects_resumed_history_without_shared_response(self):
        prompt = dict(type='user', sessionId='a', uuid='shared-prompt', timestamp=EARLY,
                      cwd='/work/app', message=dict(role='user', content=PRIVATE))
        copied = dict(prompt, sessionId='b', timestamp=LATER)
        values = self.claude([('a.jsonl', [prompt, claude_edit('a', 'a-response', 'same.py', END)]),
                              ('b.jsonl', [copied, claude_edit('b', 'b-response', 'same.py', LATER_END)])])
        self.assertEqual(values['a']._history_group, values['b']._history_group)
        self.assertEqual((sum(total(s.tokens) for s in values.values()), sum(s.calls for s in values.values()),
                          sum(s.prompts for s in values.values())), (200, 2, 1))
        self.assertEqual(analyze(list(values.values()), [values['a']], NOW)['matched_sessions'], 0)

    def test_private_history_and_patch_content_do_not_leak_through_observation(self):
        first = self.codex([[meta('native-' + PRIVATE), edit('edit', PRIVATE + '.py', EARLY),
                             reply('response', at=END)]])['native-' + PRIVATE]
        later = self.claude([('later.jsonl', [claude_edit('later-' + PRIVATE, 'later-reply',
                                      PRIVATE + '.py', LATER_END)])])['later-' + PRIVATE]
        result = analyze([first, later], [first], NOW)
        self.assertEqual(result['matched_sessions'], 1)
        encoded = json.dumps(result)
        self.assertNotIn(PRIVATE, encoded)
        self.assertNotIn(str(self.root), encoded)
        self.assertNotIn('"_history_group"', encoded)
        self.assertNotIn('"_history_uncertain"', encoded)
        for session in (first, later):
            self.assertNotIn('_history', json.dumps(session.as_dict()))
        # Aggregate usage remains reader usage; the comparison does not allocate
        # those whole-session tokens to individual edits.
        self.assertEqual((result['matched_origin_tokens'], result['matches'][0]['later_tokens']), (100, 100))


if __name__ == '__main__':
    unittest.main()
