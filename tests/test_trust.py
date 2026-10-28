"""What PLER promises, checked: it calls no model, sends nothing anywhere, starts no program and only reads logs.

The source is checked statically (no module that can open a connection or start a process is imported), and a
whole run is checked at runtime (a scan and every page request, with outgoing connections and new processes
recorded). Synthetic logs only."""
import ast
import contextlib
import http.client
import io
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import threading
import unittest
from unittest import mock

from pler import cli
from pler.server import Server
from test_logs import SECRET, USAGE, claude_reply, codex_rows, stored_zstd, write_jsonl

SOURCE = Path(__file__).resolve().parent.parent / 'src' / 'pler'
FORBIDDEN = {'socket', 'ssl', 'subprocess', 'multiprocessing', 'asyncio', 'ctypes', 'urllib.request', 'http.client',
             'ftplib', 'smtplib', 'poplib', 'imaplib', 'telnetlib', 'xmlrpc', 'requests', 'httpx', 'aiohttp', 'urllib3'}
ONLY_IN = {'http.server': 'server.py', 'webbrowser': 'cli.py'}
PROCESS_CALLS = {'system', 'popen', 'startfile', 'spawnl', 'spawnv', 'execv', 'execl', 'fork'}


def imported(tree):
    for item in ast.walk(tree):
        if isinstance(item, ast.Import):
            yield from (alias.name for alias in item.names)
        elif isinstance(item, ast.ImportFrom) and item.module and not item.level:
            yield item.module
            yield from (item.module + '.' + alias.name for alias in item.names)


class SourceTests(unittest.TestCase):
    def test_no_module_that_can_reach_out_or_start_a_program_is_imported(self):
        files = sorted(SOURCE.rglob('*.py'))
        self.assertGreater(len(files), 10)
        for path in files:
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for name in imported(tree):
                with self.subTest(file=path.name, module=name):
                    self.assertFalse(any(name == bad or name.startswith(bad + '.') for bad in FORBIDDEN))
                    if name in ONLY_IN:
                        self.assertEqual(path.name, ONLY_IN[name])
            calls = {item.func.attr for item in ast.walk(tree) if isinstance(item, ast.Call)
                     and isinstance(item.func, ast.Attribute) and isinstance(item.func.value, ast.Name)
                     and item.func.value.id == 'os'}
            self.assertFalse(calls & PROCESS_CALLS, path.name)

    def test_the_page_loads_nothing_from_the_internet(self):
        for name in ('index.html', 'app.js', 'app.css'):
            text = (SOURCE / 'web' / name).read_text(encoding='utf-8')
            self.assertNotIn('http://', text.replace('http://127.0.0.1', ''), name)
            self.assertNotIn('https://', text, name)
            self.assertNotIn('//cdn', text, name)

    def test_the_package_ships_the_page(self):
        project = (SOURCE.parent.parent / 'pyproject.toml').read_text(encoding='utf-8')
        self.assertIn('pler = ["web/*"]', project)
        self.assertIn('pler = "pler.cli:main"', project)
        self.assertIn('dependencies = []', project)


class RunTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.temp), True)
        write_jsonl(self.temp / 'claude' / 'projects' / 'shop' / 's1.jsonl',
                    [claude_reply('s1', 'm1', 'r1', USAGE, [dict(type='text', text=SECRET)], '2026-10-20T10:00:05Z')])
        folder = self.temp / 'codex' / 'sessions' / '2026' / '10' / '21'
        write_jsonl(folder / 'rollout-plain.jsonl', codex_rows('c1'))
        # These are independent sessions; response IDs must not describe copied history.
        second=codex_rows('c2')
        for row in second:
            if row['type']=='token_usage_record': row['payload']['response_id']+='-c2'
        folder.joinpath('rollout-old.jsonl.zst').write_bytes(
            stored_zstd(''.join(json.dumps(row) + '\n' for row in second).encode('utf-8')))
        environment = dict(CLAUDE_CONFIG_DIR=str(self.temp / 'claude'), CODEX_HOME=str(self.temp / 'codex'),
                           PLER_CACHE_DIR=str(self.temp / 'cache'))
        patcher = mock.patch.dict(os.environ, environment)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.connections = []
        real_connect = socket.socket.connect

        def connect(sock, address):
            self.connections.append(address)
            return real_connect(sock, address)
        for patch in (mock.patch.object(socket.socket, 'connect', connect),
                      mock.patch.object(subprocess, 'Popen', side_effect=AssertionError('a program was started'))):
            patch.start()
            self.addCleanup(patch.stop)

    def test_a_whole_session_talks_to_this_computer_only_and_starts_no_program(self):
        server = Server(0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            def request(path, method='GET', body=None):
                connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=20)
                headers = {'Origin': server.origin, 'X-PLER-Token': server.token, 'Content-Type': 'application/json'}
                connection.request(method, path, body=body, headers=headers)
                response = connection.getresponse()
                value = response.status, response.read()
                connection.close()
                return value
            for path in ('/', '/app.js', '/app.css', '/api/health', '/api/usage'):
                self.assertEqual(request(path)[0], 200, path)
            self.assertEqual(request('/api/usage/refresh', 'POST', b'{}')[0], 202)
            server.dashboard.thread.join(20)
            code, body = request('/api/usage?days=0')
            data = json.loads(body)
            self.assertEqual((code, data['state'], data['totals']['sessions']), (200, 'ready', 3))
            self.assertNotIn(SECRET, body.decode('utf-8'))
            self.assertEqual(request('/api/usage/export?days=0')[0], 200)
            self.assertEqual(request('/api/quit', 'POST', b'{}')[0], 200)
            thread.join(5)
        finally:
            server.server_close()
        self.assertTrue(self.connections)
        self.assertEqual({address[0] for address in self.connections}, {'127.0.0.1'})
        self.assertNotIn(SECRET, (self.temp / 'cache' / 'codex.json').read_text(encoding='utf-8'))

    def test_the_terminal_report_reads_the_same_logs_without_reaching_out(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli.main(['report', '--days', '0', '--json'])
        value = json.loads(output.getvalue())
        self.assertEqual((value['totals']['sessions'], value['model_calls']), (3, 0))
        self.assertEqual(self.connections, [])
        with self.assertRaises(SystemExit) as stopped, contextlib.redirect_stdout(io.StringIO()) as shown:
            cli.main(['--version'])
        self.assertEqual((stopped.exception.code, shown.getvalue().strip()), (0, 'PLER 0.2.6'))


if __name__ == '__main__':
    unittest.main()
