"""Sessions link to the repositories holding the files they edited, not only to their working folder.

Synthetic repositories and logs only. No git process; paths never reach the public projection.
"""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler.dashboard import UsageDashboard, _git_for, git_links, project_view
from pler.git_activity import read_repository, session_activity
from pler.usage import codex
from pler.usage.codex import _edited_files, _slim
from pler.usage.records import Session
from test_logs import write_jsonl

NOW = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
SECRET = 'PRIVATE-PATCH-BODY'


def reflog(*offsets, action='commit'):
    return b''.join(('%s %s Someone <someone@example.invalid> %d +0000\t%s: message\n'
                     % ('a' * 40, 'b' * 40, int(NOW.timestamp()) + offset, action)).encode() for offset in offsets)


def patch_text(*targets, escaped=False):
    lines = ['*** Begin Patch'] + ['*** Update File: %s\n@@\n-%s\n+%s' % (t, SECRET, SECRET) for t in targets] + ['*** End Patch']
    text = '\n'.join(lines)
    if escaped:  # as the code tool carries it: inside a quoted string
        return 'const result = await tools.apply_patch(%s);' % json.dumps(text)
    return text


class CodexPatchTargetTests(unittest.TestCase):
    def test_targets_come_from_raw_escaped_and_json_patches(self):
        targets = ['C:/work/app/src/main.py', 'docs/readme.md', 'C:\\work\\app\\tests\\test_main.py']
        for text in (patch_text(*targets), patch_text(*targets, escaped=True),
                     json.dumps(dict(input=patch_text(*targets)))):
            with self.subTest(text=text[:20]):
                self.assertEqual(_edited_files(dict(input=text)), sorted(targets))
        self.assertEqual(_edited_files(dict(arguments=json.dumps(dict(input=patch_text('a.py'))))), ['a.py'])
        moved = '*** Begin Patch\n*** Update File: old.py\n*** Move to: new.py\n*** Delete File: gone.py\n*** End Patch'
        self.assertEqual(_edited_files(dict(input=moved)), ['gone.py', 'new.py', 'old.py'])

    def test_patch_body_and_unrelated_tool_input_are_never_kept(self):
        row = dict(type='response_item', timestamp='2026-10-28T12:00:00Z',
                   payload=dict(type='custom_tool_call', name='exec', call_id='c1', input=patch_text('a.py', escaped=True)))
        kept = _slim(row)
        self.assertEqual(kept['payload']['edited_files'], ['a.py'])
        self.assertNotIn(SECRET, json.dumps(kept))
        plain = _slim(dict(row, payload=dict(row['payload'], input='print("%s")' % SECRET)))
        self.assertNotIn('edited_files', plain['payload'])
        self.assertNotIn(SECRET, json.dumps(plain))

    def test_relative_targets_resolve_against_the_working_folder_of_that_moment(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / 'rollout-test.jsonl'
            first, second = os.path.join(folder, 'one'), os.path.join(folder, 'two')
            write_jsonl(log, [
                dict(timestamp='2026-10-28T12:00:00Z', type='session_meta', payload=dict(id='s', cwd=first)),
                dict(timestamp='2026-10-28T12:00:01Z', type='response_item',
                     payload=dict(type='custom_tool_call', name='exec', call_id='c1', input=patch_text('a.py', escaped=True))),
                dict(timestamp='2026-10-28T12:00:02Z', type='turn_context', payload=dict(model='m', cwd=second)),
                dict(timestamp='2026-10-28T12:00:03Z', type='response_item',
                     payload=dict(type='custom_tool_call', name='exec', call_id='c2',
                                  input=patch_text('b.py', os.path.join(folder, 'abs.py'), escaped=True))),
            ])
            session, = codex.read([log])[0]
            expected={os.path.normpath(os.path.join(first, 'a.py')),
                      os.path.normpath(os.path.join(second, 'b.py')),
                      os.path.normpath(os.path.join(folder, 'abs.py'))}
            self.assertEqual(session.files_edited,{os.path.normcase(path).casefold() if os.name=='nt' else path for path in expected})


class GitLinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name) / 'workspace'          # where the agent was started; not a repository
        self.repo = self.parent / 'product'                      # the repository it edited
        self.other = Path(self.temp.name) / 'library'
        for root in (self.repo, self.other):
            (root / '.git' / 'logs').mkdir(parents=True)
            (root / 'src').mkdir()

    def session(self, files, project=None):
        value = Session('claude-code', 's-%d' % len(files), 'source-%d' % len(files), project=project or str(self.parent),
                        started=NOW - timedelta(minutes=30), ended=NOW + timedelta(minutes=30))
        value.files_edited = set(files)
        return value

    def activity(self, session):
        links = git_links([session])
        sources = dict(git_links=links, git_activity={path: read_repository(path)
                                                      for linked in links.values() for path in linked})
        return session_activity(_git_for(session, sources), session.started, session.ended)

    def test_agent_started_in_a_parent_folder_is_linked_to_the_repository_it_edited(self):
        (self.repo / '.git' / 'logs' / 'HEAD').write_bytes(reflog(-3600 * 5, -600, 600))
        value = self.activity(self.session([str(self.repo / 'src' / 'main.py')]))
        self.assertEqual((value['state'], value['matched_events'], value['repositories']), ('ready', 2, 1))
        self.assertEqual(value['linked_by'], ['edited_files'])
        before = session_activity(read_repository(str(self.parent)), NOW - timedelta(minutes=30), NOW + timedelta(minutes=30))
        self.assertEqual(before['state'], 'not_repository')  # what the working folder alone could show

    def test_working_folder_and_edited_files_in_one_repository_are_counted_once(self):
        (self.repo / '.git' / 'logs' / 'HEAD').write_bytes(reflog(0))
        session = self.session([str(self.repo / 'src' / 'a.py'), str(self.repo / 'b.py')], project=str(self.repo))
        value = self.activity(session)
        self.assertEqual((value['matched_events'], value['repositories']), (1, 1))
        self.assertEqual(value['linked_by'], ['edited_files', 'working_folder'])

    def test_edits_in_two_repositories_merge_their_events(self):
        (self.repo / '.git' / 'logs' / 'HEAD').write_bytes(reflog(-60))
        (self.other / '.git' / 'logs' / 'HEAD').write_bytes(reflog(60, action='reset'))
        value = self.activity(self.session([str(self.repo / 'src' / 'a.py'), str(self.other / 'src' / 'b.py')]))
        self.assertEqual((value['repositories'], value['counts']), (2, dict(commit=1, reset=1)))

    def test_no_repository_anywhere_is_reported_as_such(self):
        loose = Path(self.temp.name) / 'loose'
        loose.mkdir()
        value = self.activity(self.session([str(loose / 'notes.md')], project=str(loose)))
        self.assertEqual(value, dict(state='not_repository'))
        self.assertEqual(self.activity(Session('codex', 'x', 'y', started=NOW, ended=NOW)), dict(state='not_repository'))

    def test_network_and_relative_edited_paths_are_not_probed(self):
        session = self.session(['//server/share/repo/a.py', '\\\\server\\share\\repo\\b.py', 'relative/c.py'],
                               project=None)
        session.project = None
        real = Path.lstat
        def guarded(path, *args, **kwargs):
            if str(path).startswith(('\\\\', '//')):
                raise AssertionError('network probe')
            return real(path, *args, **kwargs)
        with patch.object(Path, 'lstat', guarded):
            self.assertEqual(git_links([session]), {('claude-code', session.source, session.session_id): {}})

    def test_projection_and_export_carry_counts_and_reasons_but_no_path(self):
        (self.repo / '.git' / 'logs' / 'HEAD').write_bytes(reflog(0))
        session = self.session([str(self.repo / 'src' / 'main.py')])
        session.tokens['input'] = 100
        dashboard = UsageDashboard(reader=lambda: ([session], dict(claude_files=1, codex_files=0, skipped=[])))
        dashboard.refresh()
        dashboard.thread.join(10)
        value = dashboard.view(days=0)
        row, = value['sessions']
        self.assertEqual((row['git_activity']['matched_events'], row['git_activity']['linked_by']), (1, ['edited_files']))
        encoded = json.dumps(value)
        for private in (str(self.repo), str(self.parent), 'main.py', 'someone@example.invalid'):
            self.assertNotIn(private.replace('\\', '\\\\'), encoded)
            self.assertNotIn(private, encoded)

    def test_snapshots_without_links_keep_the_working_folder_behaviour(self):
        (self.repo / '.git' / 'logs' / 'HEAD').write_bytes(reflog(0))
        session = self.session([], project=str(self.repo))
        sources = dict(git_activity={str(self.repo): read_repository(str(self.repo))})
        value = project_view([session], sources, days=0, now=NOW)
        self.assertEqual(value['sessions'][0]['git_activity']['matched_events'], 1)


if __name__ == '__main__':
    unittest.main()
