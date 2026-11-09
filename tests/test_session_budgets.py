"""Session alerts with invented logs, isolated preferences and real loopback admission."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import http.client
import json
from pathlib import Path
import threading
from unittest.mock import patch

from pler.dashboard import UsageDashboard
from pler.server import Server
from pler.usage import budgets, scan
from pler.usage.records import Session, total
from pler.usage.verdicts import session_code
from test_adoption_api import IsolatedMetadata, join_scan
from test_archive import codex_rows, claude_rows
from test_logs import write_jsonl


class BudgetTests(IsolatedMetadata):
    def monitor(self, rows, demo=True, store=None, reader=budgets.read_group):
        monitor = budgets.Monitor(store or budgets.Store(memory=True), reader=reader, autostart=False)
        monitor.bind(rows, demo)
        self.addCleanup(monitor.close)
        return monitor

    def configure(self, monitor, session, metric='tokens', limit=100, expected=None):
        self.assertTrue(monitor.configure(session_code(session), metric, limit, expected)['ok'])
        monitor.tick()
        return monitor.view()['items'][0]

    def test_thresholds_restart_acknowledgements_and_edits(self):
        row = Session('codex', 'invented', '/invented/one', tokens=dict(input=79, cache_read=0, cache_write=0, output=0, reasoning=0))
        store = budgets.Store(self.cache)
        monitor = self.monitor([row], store=store)
        value = self.configure(monitor, row)
        self.assertEqual(value['level'], 0)
        row.tokens['input'] = 80
        monitor.tick(); value = monitor.view()['items'][0]
        revision = value['revision']
        self.assertEqual(value['pending_level'], 80)
        self.assertTrue(monitor.acknowledge(value['id'], revision, 80)['ok'])
        again = self.monitor([row], store=budgets.Store(self.cache)); again.tick()
        self.assertEqual(again.view()['items'][0]['pending_level'], 0)
        row.tokens['input'] = 130; again.tick()
        self.assertEqual(again.view()['items'][0]['pending_level'], 100)
        self.assertTrue(again.acknowledge(value['id'], revision, 100)['ok'])
        self.assertEqual(again.view()['items'][0]['notified'], [80, 100])
        # Repeated identical saves preserve acknowledgements. A changed limit explicitly re-arms.
        self.configure(again, row, limit=100, expected=revision)
        self.assertEqual(again.view()['items'][0]['pending_level'], 0)
        changed = self.configure(again, row, limit=120, expected=revision)
        self.assertNotEqual(changed['revision'], revision)
        self.assertEqual(changed['pending_level'], 100)
        self.assertEqual(again.configure(value['id'], 'tokens', 200, revision)['reason'], 'conflict')
        self.assertEqual(again.acknowledge(value['id'], revision, 100)['reason'], 'conflict')
        self.assertTrue(again.configure(value['id'], None, None, changed['revision'])['ok'])
        self.assertEqual(again.view()['items'], [])
        contents = (self.cache / budgets.FILENAME).read_text(encoding='utf-8')
        self.assertNotIn('/invented', contents)

    def test_usd_full_precision_and_partial_usage_pause(self):
        row = Session('codex', 'usd', '/invented/usd', tokens=dict(input=100, cache_read=0, cache_write=0, output=0, reasoning=0), api_priced_tokens=100, api_usd=.0041)
        monitor = self.monitor([row])
        value = self.configure(monitor, row, 'usd', .005)
        self.assertEqual(value['amount'], .0041)  # not rounded UI $0.00
        self.assertEqual(value['level'], 80)
        row.api_usd = .005; monitor.tick()
        self.assertEqual(monitor.view()['items'][0]['level'], 100)
        row.api_priced_tokens = 99; monitor.tick()
        self.assertEqual(monitor.view()['items'][0]['state'], 'partial')
        self.assertEqual(monitor.view()['items'][0]['pending_level'], 0)
        row.tokens_complete = False
        value = self.configure(monitor, row, 'tokens', 100, monitor.view()['items'][0]['revision'])
        self.assertEqual(value['state'], 'partial')

    def test_changed_known_sources_only_and_both_agent_parsers(self):
        for agent, folder, make in [('codex', self.codex, codex_rows), ('claude-code', self.claude, claude_rows)]:
            with self.subTest(agent=agent):
                source = folder / ('rollout-watch.jsonl' if agent == 'codex' else 'watch.jsonl')
                def rows(amount):
                    return make(identity='watch', amount=amount, output=0)
                write_jsonl(source, rows(79))
                sessions, _ = scan([self.claude], [self.codex])
                row = next(s for s in sessions if s.agent == agent)
                reads = []
                def reader(a, paths, access):
                    reads.append(tuple(paths))
                    return budgets.read_group(a, paths, access)
                monitor = self.monitor(sessions, demo=False, reader=reader)
                value = self.configure(monitor, row)
                self.assertEqual(value['amount'], 79)
                monitor.tick(); self.assertEqual(len(reads), 1)
                write_jsonl(source, rows(110)); monitor.tick()
                value = monitor.view()['items'][0]
                self.assertEqual(value['amount'], 110)
                self.assertEqual(value['pending_level'], 100)
                self.assertEqual(len(reads), 2)
                self.assertEqual(reads[-1], (str(source),))
                source.unlink(); monitor.tick()
                self.assertEqual(monitor.view()['items'][0]['state'], 'read_error')

    def test_moved_source_and_archived_group_never_silently_rebind(self):
        original = Session('codex', 'same-provider-id', '/invented/old')
        monitor = self.monitor([original])
        value = self.configure(monitor, original)
        monitor.bind([replace(original, source='/invented/new')], demo=True)
        monitor.tick()
        self.assertEqual(monitor.view()['items'][0]['state'], 'missing')
        archived = replace(original, source_state='archive')
        monitor.bind([archived], demo=False); monitor.tick()
        self.assertEqual(monitor.view()['items'][0]['state'], 'archive')
        self.assertTrue(monitor.configure(value['id'], None, None, value['revision'])['ok'])

    def test_related_copied_sources_reconcile_once_and_limit_before_read(self):
        a, b = self.codex / 'rollout-a.jsonl', self.codex / 'rollout-b.jsonl'
        write_jsonl(a, codex_rows('copied', 80, 0)); write_jsonl(b, codex_rows('copied', 80, 0))
        sessions, _ = scan([self.claude], [self.codex], retain=True)
        row = sessions[0]
        self.assertEqual(len(row._sources), 2)
        monitor = self.monitor(sessions, demo=False)
        self.assertEqual(self.configure(monitor, row)['amount'], 80)
        monitor.signatures.clear()
        with patch.object(budgets, 'MAX_TICK_BYTES', 1), patch.object(monitor, 'reader', side_effect=AssertionError('oversized read')):
            monitor.tick()
        self.assertEqual(monitor.view()['items'][0]['state'], 'read_limit')

    def test_corrupt_preferences_are_preserved_and_limits_are_strict(self):
        self.cache.mkdir(parents=True)
        path = self.cache / budgets.FILENAME
        path.write_bytes(b'{broken-budget-file')
        store = budgets.Store(self.cache)
        monitor = self.monitor([Session('codex', 'one', '/invented/one')], store=store)
        self.assertFalse(monitor.view()['readable'])
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            monitor.configure(next(iter(monitor.targets)), 'tokens', 100, None)
        self.assertEqual(path.read_bytes(), before)
        for metric, limit in [('tokens', True), ('tokens', 1.5), ('usd', float('nan')), ('usd', float('inf')), ('usd', 10**1000), ('tokens', 0)]:
            self.assertFalse(budgets.valid_limit(metric, limit))

    def test_stale_observation_cannot_issue_a_new_notification(self):
        row = Session('codex', 'stale', '/invented/stale', tokens=dict(input=100, cache_read=0, cache_write=0, output=0, reasoning=0))
        monitor = self.monitor([row]); value = self.configure(monitor, row)
        monitor.observations[value['id']]['checked_at'] = (datetime.now(timezone.utc)-timedelta(seconds=50)).isoformat()
        self.assertEqual(monitor.view()['items'][0]['state'], 'stale')
        self.assertEqual(monitor.view()['items'][0]['pending_level'], 0)
        monitor.tick()
        self.assertEqual(monitor.view()['items'][0]['pending_level'], 100)

    def test_entry_limit_and_another_window_cannot_drop_existing_preferences(self):
        rows = [Session('codex', str(n), '/invented/'+str(n)) for n in range(21)]
        first = self.monitor(rows, store=budgets.Store(self.cache))
        second = self.monitor(rows, store=budgets.Store(self.cache))
        for row in rows[:20]:
            self.assertTrue(first.configure(session_code(row), 'tokens', 100, None)['ok'])
        self.assertEqual(second.configure(session_code(rows[20]), 'tokens', 100, None)['reason'], 'limit')
        value = second.view()['items'][0]
        self.assertTrue(second.configure(value['id'], 'tokens', 200, value['revision'])['ok'])
        self.assertEqual(len(first.view()['items']), 20)
        self.assertEqual(first.configure(value['id'], 'tokens', 300, value['revision'])['reason'], 'conflict')


class BudgetHttpTests(IsolatedMetadata):
    def setUp(self):
        super().setUp()
        self.row = Session('codex', 'http', '/invented/http', tokens=dict(input=100, cache_read=0, cache_write=0, output=0, reasoning=0))
        self.board = UsageDashboard(lambda: ([self.row], dict(demo=True)), git_reader=lambda _: dict(state='not_repository'))
        self.board.refresh(); join_scan(self.board)
        self.board.demo_budgets.autostart = False
        self.server = Server(0, self.board)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close); self.addCleanup(self.server.shutdown)

    def request(self, path, body=None, auth=True, origin=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        headers = {'Content-Type': 'application/json', 'Origin': origin or self.server.origin}
        if auth: headers['X-PLER-Token'] = self.server.token
        connection.request('POST' if body is not None else 'GET', path, json.dumps(body) if body is not None else None, headers)
        response = connection.getresponse(); status, raw = response.status, response.read(); connection.close()
        return status, json.loads(raw)

    def test_authenticated_roundtrip_outside_filters_and_export_boundary(self):
        code = session_code(self.row)
        body = dict(id=code, metric='tokens', limit=100, expected=None)
        self.assertEqual(self.request('/api/usage/budgets', body)[0], 200)
        self.board.demo_budgets.tick()
        status, value = self.request('/api/usage/budgets')
        self.assertEqual(status, 200); self.assertEqual(value['items'][0]['pending_level'], 100)
        self.assertNotIn('/invented', json.dumps(value))
        self.assertNotIn('budgets', self.board.view(days=7, agent='claude-code'))
        row = value['items'][0]
        self.assertEqual(self.request('/api/usage/budgets/ack', dict(id=code, revision=row['revision'], level=100))[0], 200)
        self.assertEqual(self.request('/api/usage/budgets')[1]['items'][0]['pending_level'], 0)
        self.assertEqual(self.request('/api/usage/budgets', body)[0], 409)
        self.assertFalse((self.cache / budgets.FILENAME).exists())  # demo never touches real preferences

    def test_auth_origin_fields_and_query_validation(self):
        code = session_code(self.row)
        body = dict(id=code, metric='tokens', limit=100, expected=None)
        self.assertEqual(self.request('/api/usage/budgets', auth=False)[0], 401)
        self.assertEqual(self.request('/api/usage/budgets', body, auth=False)[0], 403)
        self.assertEqual(self.request('/api/usage/budgets', body, origin='https://example.invalid')[0], 403)
        for invalid in [dict(body, limit=True), dict(body, limit=1.5), dict(body, path='/private'), dict(body, id='../a'), dict(body, expected=2)]:
            self.assertEqual(self.request('/api/usage/budgets', invalid)[0], 400)
        self.assertEqual(self.request('/api/usage/budgets?days=0')[0], 400)
