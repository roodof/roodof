"""The usage page on http://127.0.0.1:<port>, reachable from this computer only.

It serves three fixed files and a JSON view of the usage summary. No request can name a file, folder or
command; the only actions are "read the logs again" and "close". It opens no connection to an external service. Selected WSL log roots allow only the fixed
local running-distribution status query; no Git or agent program runs.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import threading
from urllib.parse import parse_qs, urlsplit

from . import __version__
from .dashboard import UnknownProject, UsageDashboard
from .i18n import LANGUAGES, say

WEB = Path(__file__).with_name('web')
FILES = {'/app.js': 'text/javascript; charset=utf-8', '/app.css': 'text/css; charset=utf-8'}
SECURITY = {
    'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
    'X-Frame-Options': 'DENY',
    'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; "
                               "img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"}


class Server(ThreadingHTTPServer):
    daemon_threads = True
    # On Windows SO_REUSEADDR would let a second server share a port that is in use; elsewhere it only
    # allows a quick restart after closing.
    allow_reuse_address = os.name != 'nt'

    def __init__(self, port=0, dashboard=None):
        # A running server must not mix old Python code with files edited after startup.
        self.assets = {route: (WEB / filename).read_bytes() for route, filename in
                       (('/', 'index.html'), ('/app.js', 'app.js'), ('/app.css', 'app.css'))}
        super().__init__(('127.0.0.1', port), Handler)
        self.origin = 'http://127.0.0.1:%d' % self.server_port
        self.token = secrets.token_hex(32)
        self.access_url = self.origin + '/#access=' + self.token
        self.dashboard = dashboard or UsageDashboard()


class Handler(BaseHTTPRequestHandler):
    server_version = 'PLER'

    def log_message(self, *_):
        pass

    def _send(self, code, payload, content_type='application/json; charset=utf-8', filename=None):
        if isinstance(payload, dict):
            payload = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8')
        elif isinstance(payload, str):
            payload = payload.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        for name, value in SECURITY.items():
            self.send_header(name, value)
        if filename:
            self.send_header('Content-Disposition', 'attachment; filename="%s"' % filename)
        self.end_headers()
        self.wfile.write(payload)

    def _lang(self):
        """The page's language: ?lang= on the request, else the browser's first Accept-Language, else English."""
        asked = parse_qs(urlsplit(self.path).query).get('lang', [''])[0]
        browser = (self.headers.get('Accept-Language') or '')[:2].lower()
        return asked if asked in LANGUAGES else browser if browser in LANGUAGES else 'en'

    def _local(self):
        """Only this page may talk to the server: right host (no DNS rebinding), same origin, not cross-site."""
        if (self.headers.get('Host') != self.server.origin.split('//')[1]
                or self.headers.get('Origin', self.server.origin) != self.server.origin
                or self.headers.get('Sec-Fetch-Site') == 'cross-site'):
            self._send(403, dict(error=say(self._lang(), 'error.not_local')))
            return False
        return True

    def do_GET(self):
        if not self._local():
            return
        request, lang = urlsplit(self.path), self._lang()
        try:
            if request.path == '/':
                page = self.server.assets['/'].decode('utf-8').replace('__SESSION_TOKEN__', '')
                self._send(200, page, 'text/html; charset=utf-8')
            elif request.path in FILES:
                self._send(200, self.server.assets[request.path], FILES[request.path])
            elif request.path in ('/api/usage', '/api/usage/export'):
                if not secrets.compare_digest(self.headers.get('X-PLER-Token', ''), self.server.token):
                    self._send(401, dict(error=say(lang, 'error.read_token'), code='connection_required'))
                    return
                query = parse_qs(request.query, keep_blank_values=True)
                if (set(query) - {'days', 'agent', 'project', 'lang'} or any(len(v) != 1 for v in query.values())
                        or query.get('lang', ['en'])[0] not in LANGUAGES):
                    raise ValueError(say(lang, 'error.query'))
                days = query.get('days', ['30'])[0]
                if days not in ('0', '7', '30', '90'):
                    raise ValueError(say(lang, 'error.bad_period'))
                value = self.server.dashboard.view(int(days), query.get('agent', ['all'])[0], query.get('project', ['all'])[0], lang)
                if request.path.endswith('/export'):
                    if not value['has_snapshot']:
                        raise ValueError(say(lang, 'error.no_snapshot'))
                    value.pop('project_options', None)  # no project names outside the selected scope
                    self._send(200, value, filename=say(lang, 'export_file'))
                else:
                    self._send(200, value)
            elif request.path == '/api/health':
                self._send(200, dict(app='pler', version=__version__))
            else:
                self._send(404, dict(error=say(lang, 'error.not_found')))
        except UnknownProject as error:
            self._send(400, dict(error=str(error), code='unknown_project'))
        except ValueError as error:
            self._send(400, dict(error=str(error)))

    def do_POST(self):
        if not self._local():
            return
        route = urlsplit(self.path).path
        if route not in ('/api/usage/refresh', '/api/usage/archive/clear', '/api/quit'):
            self._send(404, dict(error=say(self._lang(), 'error.no_action')))
            return
        if (self.headers.get('Origin') != self.server.origin
                or not secrets.compare_digest(self.headers.get('X-PLER-Token', ''), self.server.token)):
            self._send(403, dict(error=say(self._lang(), 'error.token')))
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 64 or self.headers.get_content_type() != 'application/json':
                raise ValueError(say(self._lang(), 'error.bad_request'))
            if json.loads(self.rfile.read(size)) != {}:
                raise ValueError(say(self._lang(), 'error.fields'))
        except ValueError as error:
            self._send(400, dict(error=str(error)))
            return
        if route == '/api/usage/refresh':
            self._send(202, self.server.dashboard.refresh())
        elif route == '/api/usage/archive/clear':
            result = self.server.dashboard.clear_archive()
            if result.get('ok'):
                self._send(200, result)
            else:
                self._send(500, dict(error=say(self._lang(), 'error.archive_clear')))
        else:
            self._send(200, dict(closed=True))
            threading.Thread(target=self.server.shutdown, daemon=True).start()
