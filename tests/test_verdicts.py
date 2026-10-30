"""Your one-click verdicts stay on this computer, name only page session codes and never replace a file
PLER cannot read. Sessions, folders and caches are invented and isolated.
"""
import http.client
import io
import json
import threading
from unittest.mock import patch

from pler.dashboard import UsageDashboard
from pler.server import Server
from pler.usage import main, scan, verdicts
from pler.usage.verdicts import Memory
import test_adoption_api
from test_adoption_api import PRIVATE, IsolatedMetadata, invented_sessions, join_scan
from test_logs import codex_rows, write_jsonl

CODE = 'a' * 24


class VerdictFileTests(IsolatedMetadata):
    def test_saving_and_removing_keeps_only_code_word_and_time(self):
        self.assertEqual(verdicts.read(), {})
        self.assertEqual(verdicts.save(CODE, 'useful'), {CODE: 'useful'})
        self.assertEqual(verdicts.save('b' * 24, 'wasted'), {CODE: 'useful', 'b' * 24: 'wasted'})
        self.assertEqual(verdicts.save(CODE, None), {'b' * 24: 'wasted'})
        stored = json.loads((self.cache / verdicts.FILENAME).read_text('utf-8'))
        self.assertEqual(set(stored), {'format', 'verdicts'})
        self.assertEqual(set(stored['verdicts']['b' * 24]), {'verdict', 'at'})
        self.assertEqual(verdicts.read(), {'b' * 24: 'wasted'})

    def test_invalid_code_or_word_is_refused_before_any_write(self):
        for code, word in (('C:/private/log.jsonl', 'useful'), ('A' * 24, 'useful'), (CODE, 'great'), (CODE, ''), (None, 'useful')):
            with self.subTest(code=code, word=word):
                with self.assertRaises(ValueError):
                    verdicts.save(code, word)
        self.assertFalse((self.cache / verdicts.FILENAME).exists())

    def test_unreadable_or_newer_file_is_never_overwritten(self):
        self.cache.mkdir()
        path = self.cache / verdicts.FILENAME
        for content in (b'{damaged', json.dumps(dict(format=2, verdicts={})).encode(),
                        json.dumps(dict(format=1, verdicts={CODE: dict(verdict='useful', at=1, note='x')})).encode()):
            with self.subTest(content=content):
                path.write_bytes(content)
                with self.assertRaises(ValueError):
                    verdicts.read()
                with self.assertRaises(ValueError):
                    verdicts.save(CODE, 'wasted')
                self.assertEqual(path.read_bytes(), content)

    def test_memory_store_never_touches_the_cache(self):
        store = Memory()
        self.assertEqual(store.save(CODE, 'wasted'), {CODE: 'wasted'})
        self.assertEqual(store.save(CODE, None), {})
        with self.assertRaises(ValueError):
            store.save('../x', 'useful')
        self.assertFalse(self.cache.exists())


class VerdictDashboardTests(IsolatedMetadata):
    def board(self, store=None):
        rows = invented_sessions()
        board = UsageDashboard(lambda: (rows, dict(claude_files=1, codex_files=1, skipped=[])),
                               git_reader=lambda path: dict(state='not_repository'), verdicts=store)
        board.refresh(); join_scan(board)
        return board

    def test_only_a_shown_session_can_be_judged_and_the_view_sums_tokens_per_verdict(self):
        board = self.board()
        view = board.view(days=0)
        self.assertEqual({row['verdict'] for row in view['sessions']}, {None})
        self.assertEqual(view['verdicts']['none'], dict(sessions=2, total_tokens=120, api_usd=0.0))
        self.assertEqual(board.set_verdict(CODE, 'useful'), dict(ok=False, reason='missing'))
        self.assertFalse((self.cache / verdicts.FILENAME).exists())
        later = next(row for row in view['sessions'] if row['agent'] == 'claude-code')
        self.assertTrue(board.set_verdict(later['id'], 'wasted')['ok'])
        view = board.view(days=0)
        self.assertEqual(next(row['verdict'] for row in view['sessions'] if row['id'] == later['id']), 'wasted')
        self.assertEqual(view['verdicts']['wasted'], dict(sessions=1, total_tokens=20, api_usd=0.0))
        self.assertEqual(view['verdicts']['none']['sessions'], 1)
        self.assertTrue(view['verdicts']['readable'])
        self.assertEqual(board.session(later['id'])['verdict'], 'wasted')
        stored = (self.cache / verdicts.FILENAME).read_text('utf-8')
        self.assertNotIn(PRIVATE, stored)
        self.assertNotIn('invented', stored)

    def test_a_new_read_keeps_verdicts_and_a_verdict_saved_during_a_read_survives_it(self):
        board = self.board()
        identity = board.view(days=0)['sessions'][0]['id']
        release, started = threading.Event(), threading.Event()
        rows = invented_sessions()

        def slow():
            started.set(); release.wait(5)
            return rows, dict(claude_files=1, codex_files=1, skipped=[])
        board.reader = slow
        board.refresh(); started.wait(5)
        self.assertTrue(board.set_verdict(identity, 'useful')['ok'])
        release.set(); join_scan(board)
        self.assertEqual(board.view(days=0)['verdicts']['useful']['sessions'], 1)

    def test_unreadable_file_is_reported_and_saving_is_refused(self):
        self.cache.mkdir()
        (self.cache / verdicts.FILENAME).write_bytes(b'{damaged')
        board = self.board()
        view = board.view(days=0)
        self.assertFalse(view['verdicts']['readable'])
        self.assertEqual(board.set_verdict(view['sessions'][0]['id'], 'useful'), dict(ok=False, reason='unreadable'))
        self.assertEqual((self.cache / verdicts.FILENAME).read_bytes(), b'{damaged')

    def test_demo_store_keeps_verdicts_in_memory(self):
        board = self.board(Memory())
        identity = board.view(days=0)['sessions'][0]['id']
        self.assertTrue(board.set_verdict(identity, 'useful')['ok'])
        self.assertEqual(board.view(days=0)['verdicts']['useful']['sessions'], 1)
        self.assertFalse((self.cache / verdicts.FILENAME).exists())


class VerdictHttpTests(IsolatedMetadata):
    request = test_adoption_api.AdoptionHttpTests.request

    def setUp(self):
        super().setUp()
        rows = invented_sessions()
        self.board = UsageDashboard(lambda: (rows, dict(claude_files=1, codex_files=1, skipped=[])),
                                    git_reader=lambda path: dict(state='not_repository'))
        self.board.refresh(); join_scan(self.board)
        self.server = Server(0, self.board)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def post_raw(self, raw, auth=True):
        """The reply status, or None when Windows resets an upload the server refused before reading it."""
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        headers = {'Host': self.server.origin.split('//')[1], 'Content-Type': 'application/json'}
        if auth:
            headers.update({'Origin': self.server.origin, 'X-PLER-Token': self.server.token})
        try:
            connection.request('POST', '/api/usage/verdict', body=raw, headers=headers)
            response = connection.getresponse()
            response.read()
            return response.status
        except (ConnectionResetError, ConnectionAbortedError):
            return None
        finally:
            connection.close()

    def test_verdict_route_takes_only_a_shown_code_and_one_of_two_words(self):
        identity = self.board.view(days=0)['sessions'][0]['id']
        unsigned = json.dumps(dict(id=identity, verdict='useful')).encode('ascii')
        self.assertIn(self.post_raw(unsigned, auth=False), (403, None))
        self.assertIsNone(self.board.view(days=0)['sessions'][0]['verdict'])
        for body in (dict(id=identity), dict(id=identity, verdict='great'), dict(id=identity, verdict=1),
                     dict(id='C:/' + PRIVATE, verdict='useful'), dict(id=identity, verdict='useful', path='C:/x'),
                     dict(id=identity.upper(), verdict='useful'), [identity, 'useful']):
            with self.subTest(body=body):
                self.assertEqual(self.request('/api/usage/verdict', 'POST', body)[0], 400)
        compact = json.dumps(dict(id=identity, verdict=None), separators=(',', ':'))
        self.assertEqual(self.post_raw((compact[:-1] + ' ' * (128 - len(compact)) + '}').encode('ascii')), 200)
        # Refused before the body is read: a 400 reply, or on Windows possibly a reset of the unread upload.
        self.assertIn(self.post_raw((compact[:-1] + ' ' * (129 - len(compact)) + '}').encode('ascii')), (400, None))
        self.assertEqual(self.request('/api/usage/verdict', 'POST', dict(id=CODE, verdict='useful'))[0], 404)
        code, _, raw = self.request('/api/usage/verdict', 'POST', dict(id=identity, verdict='useful'))
        self.assertEqual((code, json.loads(raw)), (200, dict(ok=True, id=identity, verdict='useful')))
        self.assertEqual(json.loads(self.request('/api/usage?days=0')[2])['verdicts']['useful']['sessions'], 1)
        code, _, raw = self.request('/api/usage/verdict', 'POST', dict(id=identity, verdict=None))
        self.assertEqual((code, json.loads(raw)['verdict']), (200, None))

    def test_failed_save_is_reported_without_claiming_success(self):
        identity = self.board.view(days=0)['sessions'][0]['id']
        with patch.object(self.board.verdict_store, 'save', side_effect=OSError('disk')):
            code, _, raw = self.request('/api/usage/verdict', 'POST', dict(id=identity, verdict='wasted'))
        self.assertEqual(code, 500)
        self.assertNotIn('disk', raw.decode('utf-8'))
        self.assertIsNone(self.board.view(days=0)['sessions'][0]['verdict'])


class VerdictReportTests(IsolatedMetadata):
    def test_terminal_and_json_report_sum_saved_verdicts_and_write_utf8(self):
        write_jsonl(self.codex / 'rollout-invented.jsonl', codex_rows())
        folders = ['--claude-dir', str(self.claude), '--codex-dir', str(self.codex)]
        sessions, _ = scan([self.claude], [self.codex])
        verdicts.save(verdicts.session_code(sessions[0]), 'wasted')
        stream = io.TextIOWrapper(io.BytesIO(), encoding='cp1254', newline='')
        with patch('sys.stdout', stream):
            main(['--days', '0', '--lang', 'tr'] + folders)
            stream.flush()
            text = stream.buffer.getvalue().decode('utf-8')
        self.assertIn('Değerlendirmelerin: 0 oturum işe yaradı (0 token), 1 oturum boşa gitti', text)
        stream = io.TextIOWrapper(io.BytesIO(), encoding='cp1254', newline='')
        with patch('sys.stdout', stream):
            main(['--days', '0', '--json', '--sessions', '--lang', 'tr'] + folders)
            stream.flush()
            value = json.loads(stream.buffer.getvalue().decode('utf-8'))
        self.assertEqual(value['verdicts']['wasted']['sessions'], 1)
        self.assertEqual([row['verdict'] for row in value['sessions']], ['wasted'])
