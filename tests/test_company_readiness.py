"""Reproduce professional trust failures using temporary, invented records only."""
import contextlib
from datetime import datetime, timezone
import http.client
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from pler.dashboard import UsageDashboard, project_view, session_view
from pler.server import Server
from pler.usage import claude_code, codex, main, scan
from pler.usage.cache import FileCache
from pler.usage.records import Session, total
from test_logs import SECRET, USAGE, claude_reply, codex_rows, write_jsonl


class OriginalLogRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = self.root/'sessions'/'rollout-example.jsonl'
        write_jsonl(self.log, codex_rows())
        environment = dict(CODEX_HOME=str(self.root), CLAUDE_CONFIG_DIR=str(self.root/'no-claude'),
                           PLER_CACHE_DIR=str(self.root/'cache'))
        self.environment = patch.dict(os.environ, environment)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.cache = self.root/'cache'/'codex.json'

    def corrupt(self, edit):
        data = json.loads(self.cache.read_text('utf-8'))
        edit(next(iter(data['files'].values())))
        self.cache.write_text(json.dumps(data), 'utf-8')

    def test_wrong_cache_shape_falls_back_to_original_and_rebuilds(self):
        first, _ = scan()
        for rows in ('bad shape', [None], [{'payload': 'wrong'}]):
            with self.subTest(rows=rows):
                self.corrupt(lambda entry: entry.update(rows=rows))
                again, sources = scan()
                self.assertEqual([s.as_dict() for s in again], [s.as_dict() for s in first])
                self.assertEqual(sources['skipped'], [])
                self.assertIsInstance(next(iter(json.loads(self.cache.read_text('utf-8'))['files'].values()))['rows'], list)

    def test_changed_cached_numbers_are_not_trusted_when_checksum_disagrees(self):
        scan()
        def damage(entry):
            next(row for row in entry['rows'] if row.get('type')=='token_usage_record')['payload']['usage']['output_tokens'] = 999999
        self.corrupt(damage)
        sessions, _ = scan()
        self.assertEqual(total(sessions[0].tokens), 2100)
        self.assertNotIn('999999', self.cache.read_text('utf-8'))

    def test_old_cache_without_checksum_is_rebuilt_from_original(self):
        scan()
        self.corrupt(lambda entry: entry.pop('checksum'))
        with patch.object(codex, '_rows', wraps=codex._rows) as reader:
            sessions, _ = scan()
        self.assertEqual((reader.call_count, total(sessions[0].tokens)), (1, 2100))

    def test_cache_write_failure_does_not_hide_verified_usage(self):
        with patch('pler.usage.cache.os.replace', side_effect=PermissionError('private path')):
            sessions, sources = scan()
        self.assertEqual((total(sessions[0].tokens), sources['skipped']), (2100, []))

    def test_partial_file_warning_survives_a_cache_hit_without_reopening_log(self):
        with self.log.open('a', encoding='utf-8') as stream:
            stream.write('\n{"unfinished":\n[]\n{"invalid":NaN}\n')
        first, sources = scan()
        self.assertEqual((total(first[0].tokens), sources['skipped']), (2100, [(str(self.log), 'MalformedRows')]))
        with patch.object(codex, '_rows', side_effect=AssertionError('cache should be reused')):
            second, cached_sources = scan()
        self.assertEqual([s.as_dict() for s in second], [s.as_dict() for s in first])
        self.assertEqual(cached_sources['skipped'], sources['skipped'])
        stored = self.cache.read_text('utf-8')
        self.assertNotIn(SECRET, stored)
        self.assertNotIn('unfinished', stored)
        public = project_view(second, cached_sources, days=0)
        self.assertEqual(public['sources']['issues'], [dict(reason='Malformed or incomplete log rows', files=1)])


class PartialRecordsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.good = claude_reply('s1', 'm1', 'r1', USAGE, [], '2026-10-26T10:00:00Z')

    def test_invalid_codex_response_ids_skip_only_the_bad_usage(self):
        rows = codex_rows()
        rows = [row for row in rows if row['type'] != 'token_usage_record'] + [codex_rows()[4]]
        for index, identity in enumerate(([], {}, True, 3)):
            bad = codex_rows()[4]
            bad['payload']['response_id'] = identity
            rows.append(bad)
        log = self.root/'rollout-test.jsonl'
        write_jsonl(log, rows)
        sessions, issues = codex.read([log])
        self.assertEqual((sessions[0].calls, total(sessions[0].tokens)), (1, 1060))
        self.assertEqual(issues, [(str(log), 'MalformedRows')])

    def test_bad_claude_identities_and_broken_rows_keep_valid_usage(self):
        path = self.root/'claude.jsonl'
        rows = [self.good]
        for identity in ([], {}, True, 3):
            rows.extend([dict(self.good, sessionId=identity),
                         dict(self.good, requestId=identity),
                         dict(self.good, message=dict(self.good['message'], id=identity))])
        write_jsonl(path, rows)
        with path.open('a', encoding='utf-8') as stream:
            stream.write('{"unfinished":\n[]\n{"bad":Infinity}\n')
        issues = []
        sessions = claude_code.read([path], issues)
        self.assertEqual((len(sessions), sessions[0].calls, total(sessions[0].tokens)), (1, 1, 1260))
        self.assertEqual(issues, [(str(path), 'MalformedRows')])
        self.assertNotIn('unfinished', json.dumps(project_view(sessions, dict(skipped=issues), days=0)))

    def test_claude_midstream_read_failure_preserves_previous_records(self):
        path = self.root/'private.jsonl'
        class FailingStream:
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def read(stream,size):
                if not getattr(stream,'sent',False):
                    stream.sent=True
                    return (json.dumps(self.good)+'\n').encode('utf-8')
                raise PermissionError('PRIVATE-READ-ERROR')
        with patch('builtins.open', return_value=FailingStream()):
            issues = []
            sessions = claude_code.read([path], issues)
        self.assertEqual((len(sessions), total(sessions[0].tokens)), (1, 1260))
        self.assertEqual(issues, [(str(path), 'PermissionError')])

    def test_stable_prompt_and_tool_ids_count_once_in_copied_files(self):
        prompt = dict(type='user', sessionId='s1', uuid='stable-prompt', timestamp='2026-10-26T10:00:00Z',
                      message=dict(content=SECRET))
        tool = dict(type='tool_use', name='Edit', id='stable-tool', input=dict(file_path='/example/file.py'))
        reply = dict(self.good, message=dict(self.good['message'], content=[tool]))
        paths = [self.root/name for name in ('first.jsonl', 'same-session-copy.jsonl', 'resumed-copy.jsonl')]
        for path, identity in zip(paths, ('s1', 's1', 's2')):
            write_jsonl(path, [dict(prompt, sessionId=identity), dict(reply, sessionId=identity)])
        sessions = claude_code.read(paths)
        self.assertEqual(len(sessions), 1)
        row = sessions[0]
        self.assertEqual((row.session_id, row.prompts, row.calls, row.tools, row.files_edited),
                         ('s1', 1, 1, {'Edit': 1}, {'/example/file.py'}))

    def test_tool_seen_only_in_resumed_copy_belongs_to_the_reply_owner(self):
        first, second = self.root/'first.jsonl', self.root/'second.jsonl'
        tool = dict(type='tool_use', name='Write', id='stable-tool', input=dict(file_path='/example/file.py'))
        write_jsonl(first, [self.good])
        write_jsonl(second, [dict(self.good, sessionId='s2', message=dict(self.good['message'], content=[tool]))])
        row, = claude_code.read([first, second])
        self.assertEqual((row.session_id, row.tools, row.files_edited), ('s1', {'Write': 1}, {'/example/file.py'}))

    def test_missing_prompt_ids_remain_separate_and_malformed_content_kind_cannot_crash(self):
        prompt = dict(type='user', sessionId='s1', message=dict(content=[dict(type={}), dict(type='text', text=SECRET)]))
        path = self.root/'no-identities.jsonl'
        write_jsonl(path, [prompt, prompt])
        row, = claude_code.read([path])
        self.assertEqual(row.prompts, 2)


class PublicReportTests(unittest.TestCase):
    def test_copied_provider_ids_still_have_distinct_private_row_codes(self):
        first = Session('codex', 'PRIVATE-shared-id', 'C:/PRIVATE/first.jsonl')
        second = Session('codex', 'PRIVATE-shared-id', 'C:/PRIVATE/second.jsonl')
        public = [session_view(first), session_view(second)]
        self.assertNotEqual(public[0]['id'], public[1]['id'])
        self.assertNotEqual(public[0]['id'][:8], public[1]['id'][:8])
        self.assertEqual(session_view(first)['id'], public[0]['id'])
        self.assertNotIn('PRIVATE', json.dumps(public))

    def test_json_uses_the_page_allowlist_and_retains_unknown_dates(self):
        now = datetime(2026, 10, 26, tzinfo=timezone.utc)
        row = Session('codex', 'RAW-PRIVATE-ID', 'C:/PRIVATE/rollout.jsonl', project='C:/PRIVATE/work/shop',
                      branch='PRIVATE-BRANCH', parent_id='PRIVATE-PARENT', files_edited={'C:/PRIVATE/file.py'},
                      notes=['PRIVATE-NOTE'], tools={'PRIVATE-TOOL': 2})
        dated = Session('codex', 'dated', 'synthetic', started=now, ended=now)
        sources = dict(claude_files=0, codex_files=2, skipped=[('C:/PRIVATE/unreadable.jsonl', 'PermissionError')],
                       claude_quota=[], future_private_field='PRIVATE')
        output = io.StringIO()
        with patch('pler.usage.scan', return_value=([row, dated], sources)), contextlib.redirect_stdout(output):
            main(['--days', '0', '--json', '--sessions', '--lang', 'en'])
        value = json.loads(output.getvalue())
        self.assertNotIn('PRIVATE', output.getvalue())
        self.assertNotIn('days', value)
        self.assertEqual(value['period']['mode'], 'active_sessions_full_totals')
        self.assertEqual(value['sessions'][0], session_view(row))
        self.assertIsNone(value['sessions'][0]['started'])
        self.assertEqual(value['sources']['skipped'], [{'reason': 'PermissionError'}])
        self.assertEqual(value['sources']['claude_quota'], 0)
        self.assertEqual(value['sessions'][0]['project'], 'work/shop')


class RunningVersionTests(unittest.TestCase):
    def test_running_assets_stay_consistent_until_a_new_server_is_started(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ('index.html', 'app.js', 'app.css'):
                (root/name).write_text('old-'+name+' __SESSION_TOKEN__', 'utf-8')
            with patch('pler.server.WEB', root):
                old = Server(0, UsageDashboard(lambda: ([], {})))
                for name in ('index.html', 'app.js', 'app.css'):
                    (root/name).write_text('new-'+name+' __SESSION_TOKEN__', 'utf-8')
                new = Server(0, UsageDashboard(lambda: ([], {})))
            for server, expected in ((old, 'old-'), (new, 'new-')):
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    for route, name in (('/', 'index.html'), ('/app.js', 'app.js'), ('/app.css', 'app.css')):
                        connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=10)
                        connection.request('GET', route)
                        response = connection.getresponse()
                        text = response.read().decode('utf-8')
                        connection.close()
                        self.assertEqual(response.status, 200)
                        self.assertTrue(text.startswith(expected+name), text)
                        if route=='/': self.assertNotIn(server.token, text)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(5)


if __name__=='__main__':
    unittest.main()
