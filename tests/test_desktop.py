"""Desktop ownership and startup readiness; invented data only."""
from http.client import HTTPConnection
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from pler.desktop import Window
from pler.server import Server


class DesktopTests(unittest.TestCase):
    def test_update_health_retries_desktop_loading_instead_of_rolling_back_immediately(self):
        from pler.update_worker import healthy
        child = Mock(); child.poll.return_value = None
        started = json.dumps(dict(nonce='test-nonce',version='0.3.0',origin='http://127.0.0.1:49152')).encode()
        waiting = Mock(status=503); waiting.read.return_value = b'{"app":"pler","version":"0.3.0"}'
        loaded = Mock(status=200); loaded.read.return_value = waiting.read.return_value
        first, second = Mock(), Mock()
        first.getresponse.return_value = waiting; second.getresponse.return_value = loaded
        with patch('pler.update_worker.read_small',return_value=started), \
             patch('http.client.HTTPConnection',side_effect=[first,second]):
            self.assertTrue(healthy(Path('invented-stage'),dict(nonce='test-nonce',version='0.3.0'),child))
        first.close.assert_called_once(); second.close.assert_called_once()

    def test_missing_window_never_falls_back_to_a_browser(self):
        with tempfile.TemporaryDirectory() as folder, patch('pler.desktop.executable_path', return_value=Path(folder)/'missing.exe'):
            with patch('pler.desktop.subprocess.Popen') as spawn, self.assertRaisesRegex(OSError, 'desktop window is missing'):
                Window(Mock())
            spawn.assert_not_called()

    def test_private_environment_and_marker_lifetime_never_put_credentials_in_files_or_argv(self):
        server = Mock(access_url='http://127.0.0.1:49152/#access=' + 'a'*64)
        child = Mock(); child.poll.return_value = None
        with tempfile.TemporaryDirectory() as folder:
            exe = Path(folder)/'PLER-Desktop.exe'; exe.write_bytes(b'invented')
            with patch('pler.desktop.executable_path', return_value=exe), \
                 patch('pler.desktop.subprocess.Popen', return_value=child) as spawn, \
                 patch('pler.desktop.threading.Thread'), \
                 patch.dict('os.environ', ELECTRON_RUN_AS_NODE='1', NODE_OPTIONS='--inspect', NODE_PATH='evil'):
                window = Window(server)
                args, kwargs = spawn.call_args
                self.assertEqual(args[0], [str(exe)])
                self.assertNotIn('access=', str(args))
                for name in ('ELECTRON_RUN_AS_NODE','NODE_OPTIONS','NODE_PATH'):
                    self.assertNotIn(name, kwargs['env'])
                self.assertEqual(kwargs['env']['PLER_DESKTOP_URL'], server.access_url)
                self.assertEqual((window.control/'running').read_text(), '1')
                self.assertEqual(list(window.control.iterdir()), [window.control/'running'])
                self.assertFalse(server.desktop_ready.is_set())
                (window.control/'ready').write_text('1')
                window._ready(server)
                self.assertTrue(server.desktop_ready.is_set())
                window._watch(server)
                server.shutdown.assert_called_once()
                control = window.control
                window.close()
                self.assertFalse(control.exists())
                child.terminate.assert_not_called()

    def test_health_waits_for_actual_desktop_document_before_updater_accepts(self):
        board = Mock()
        with Server(0, dashboard=board, updater=Mock(automatic=False)) as server:
            server.desktop_ready = threading.Event()
            worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
            try:
                for ready, expected in ((False,503),(True,200)):
                    if ready: server.desktop_ready.set()
                    connection = HTTPConnection('127.0.0.1',server.server_port,timeout=3)
                    connection.request('GET','/api/health')
                    response = connection.getresponse()
                    self.assertEqual(response.status, expected)
                    self.assertEqual(json.loads(response.read())['app'], 'pler')
                    connection.close()
            finally:
                server.shutdown();worker.join(3)
