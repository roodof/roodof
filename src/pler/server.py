"""The usage page on http://127.0.0.1:<port>, reachable from this computer only.

It serves three fixed files and a JSON view of the usage summary. No request can name a file, folder or
command; the actions are "read the logs again", metadata settings, your own verdict, Claude plan or work links,
prepare/check a private metadata backup and "close". An uploaded backup is checked in memory only;
recovery into a new folder is a CLI action. Only explicitly requested/opted-in updates contact the fixed release service. Selected WSL log roots allow only the fixed
local running-distribution status query; no Git or agent program runs.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import re
import threading
import time
from urllib.parse import parse_qs, urlsplit

from . import __version__
from .dashboard import UnknownProject, UsageDashboard
from .i18n import LANGUAGES, say

WEB = Path(__file__).with_name('web')
FILES = {'/app.js': 'text/javascript; charset=utf-8','/ui-state.js':'text/javascript; charset=utf-8','/updates.js':'text/javascript; charset=utf-8',
         '/updates.css':'text/css; charset=utf-8','/app.css': 'text/css; charset=utf-8',
         '/workspace.css':'text/css; charset=utf-8','/workspace.js':'text/javascript; charset=utf-8',
         '/workspace-font.woff2':'font/woff2','/sessions-grid.css':'text/css; charset=utf-8'}
SECURITY = {
    'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
    'X-Frame-Options': 'DENY',
    'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; "
                               "img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"}


def sys_argv():
    import sys
    return list(sys.argv[1:])


class Server(ThreadingHTTPServer):
    daemon_threads = True
    max_workers = 8
    idle_timeout = 5.0
    request_timeout = 15.0
    # On Windows SO_REUSEADDR would let a second server share a port that is in use; elsewhere it only
    # allows a quick restart after closing.
    allow_reuse_address = os.name != 'nt'

    def __init__(self, port=0, dashboard=None, updater=None):
        from .updates import Manager
        self.updates=updater if updater is not None else Manager(restart_args=sys_argv())
        self._action_lock=threading.RLock()
        self._slots = threading.BoundedSemaphore(self.max_workers)
        self._requests = {}
        self._requests_lock = threading.Lock()
        # At most one large backup body/projection is admitted by this server.
        self._backup_lock = threading.Lock()
        # A running server must not mix old Python code with files edited after startup.
        self.assets = {route: (WEB / filename).read_bytes() for route, filename in
                       (('/', 'index.html'), ('/app.js', 'app.js'),('/ui-state.js','ui-state.js'),('/updates.js','updates.js'),('/updates.css','updates.css'), ('/app.css', 'app.css'),('/workspace.css','workspace.css'),
                        ('/workspace.js','workspace.js'),('/workspace-font.woff2','workspace-font.woff2'),('/sessions-grid.css','sessions-grid.css'))}
        super().__init__(('127.0.0.1', port), Handler)
        self.origin = 'http://127.0.0.1:%d' % self.server_port
        self.token = secrets.token_hex(32)
        self.access_url = self.origin + '/#access=' + self.token
        self.dashboard = dashboard or UsageDashboard()
        def update_shutdown():
            time.sleep(1.0)  # let the open page observe the authenticated restarting status
            self.shutdown()
        self.updates.close_application=update_shutdown
        if self.updates.automatic and not self.updates.handoff:
            try:self.updates.check()
            except ValueError:pass

    def get_request(self):
        request, address = super().get_request()
        request.settimeout(self.idle_timeout)
        return request, address

    @staticmethod
    def _interrupt(request):
        try:
            # Socket shutdown mode 2 closes both directions, waking an incomplete read.
            request.shutdown(2)
        except OSError:
            pass

    def process_request(self, request, address):
        if not self._slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        with self._requests_lock:
            self._requests[request] = time.monotonic() + self.request_timeout
        try:
            super().process_request(request, address)
        except Exception:
            with self._requests_lock:
                self._requests.pop(request, None)
            self._slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            with self._requests_lock:
                self._requests.pop(request, None)
            self._slots.release()

    def service_actions(self):
        # The accept loop enforces total deadlines without one extra timer thread per peer.
        now = time.monotonic()
        with self._requests_lock:
            expired = [request for request, deadline in self._requests.items() if now >= deadline]
        for request in expired:
            self._interrupt(request)

    def server_close(self):
        if hasattr(self,'updates'):self.updates.close()
        if hasattr(self, 'dashboard'):
            self.dashboard.close()
        with self._requests_lock:
            requests = tuple(self._requests)
        for request in requests:
            self._interrupt(request)
        super().server_close()


class Handler(BaseHTTPRequestHandler):
    server_version = 'PLER'

    def handle(self):
        try:
            super().handle()
        except (OSError, TimeoutError):
            # A peer leaving or exhausting its budget must not print request data/tracebacks.
            self.close_connection = True

    def log_message(self, *_):
        pass

    def _token(self):
        supplied=self.headers.get('X-PLER-Token','')
        return bool(re.fullmatch('[a-f0-9]{64}',supplied)) and secrets.compare_digest(supplied,self.server.token)

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
                from .usage.backup import MAX_BUNDLE_BYTES
                page = (self.server.assets['/'].decode('utf-8').replace('__SESSION_TOKEN__', '')
                        .replace('__BACKUP_MAX_BYTES__',str(MAX_BUNDLE_BYTES))
                        .replace('__UPDATER_CAPABLE__','1' if self.server.updates.root else '0'))
                self._send(200, page, 'text/html; charset=utf-8')
            elif request.path=='/help':
                query=parse_qs(request.query,keep_blank_values=True)
                if set(query)-{'lang','chapter'} or any(len(v)!=1 for v in query.values()):
                    raise ValueError(say(lang,'error.query'))
                from .help import render
                self._send(200,render(lang,query.get('chapter',['guide'])[0]),'text/html; charset=utf-8')
            elif request.path in FILES:
                self._send(200, self.server.assets[request.path], FILES[request.path])
            elif request.path=='/api/updates':
                if not self._token():
                    self._send(401,dict(error=say(lang,'error.read_token'),code='connection_required'));return
                if request.query:raise ValueError(say(lang,'error.query'))
                self._send(200,self.server.updates.view())
            elif request.path in ('/api/usage', '/api/usage/export','/api/usage/session','/api/usage/work/followups','/api/usage/budgets','/api/usage/sources','/api/usage/diagnostics','/api/usage/reconnections'):
                if not self._token():
                    self._send(401, dict(error=say(lang, 'error.read_token'), code='connection_required'))
                    return
                query = parse_qs(request.query, keep_blank_values=True)
                if request.path=='/api/usage/reconnections':
                    if (set(query)-{'kind','q','offset','lang','source'} or any(len(v)!=1 for v in query.values())
                            or query.get('lang',['en'])[0] not in LANGUAGES or query.get('kind',['sources'])[0] not in ('sources','targets','state')
                            or len(query.get('q',[''])[0])>160 or not re.fullmatch('[0-9]{1,6}',query.get('offset',['0'])[0])
                            or 'source' in query and not re.fullmatch('[a-f0-9]{24}',query['source'][0])):
                        raise ValueError(say(lang,'error.query'))
                    self._send(200,self.server.dashboard.reconnect_view(query.get('kind',['sources'])[0],query.get('q',[''])[0],
                        int(query.get('offset',['0'])[0]),query.get('lang',['en'])[0],query.get('source',[None])[0]))
                    return
                if request.path == '/api/usage/diagnostics':
                    if set(query)-{'lang'} or any(len(v)!=1 for v in query.values()) or query.get('lang',['en'])[0] not in LANGUAGES:
                        raise ValueError(say(lang, 'error.query'))
                    self._send(200, self.server.dashboard.diagnostic_view(query.get('lang',['en'])[0]))
                    return
                if request.path == '/api/usage/sources':
                    if request.query: raise ValueError(say(lang, 'error.query'))
                    self._send(200, self.server.dashboard.source_view())
                    return
                if request.path == '/api/usage/budgets':
                    if request.query: raise ValueError(say(lang, 'error.query'))
                    self._send(200, self.server.dashboard.budget_view())
                    return
                if request.path=='/api/usage/work/followups':
                    if (set(query)-{'work','lang'} or any(len(v)!=1 for v in query.values())
                            or query.get('lang',['en'])[0] not in LANGUAGES
                            or not re.fullmatch('[a-f0-9]{24}',query.get('work',[''])[0])):
                        raise ValueError(say(lang,'error.query'))
                    self._followup_result(self.server.dashboard.followup_view(query['work'][0]))
                    return
                if request.path=='/api/usage/session':
                    if (set(query)-{'id','lang'} or any(len(v)!=1 for v in query.values())
                            or query.get('lang',['en'])[0] not in LANGUAGES
                            or not re.fullmatch('[a-f0-9]{24}',query.get('id',[''])[0])):
                        raise ValueError(say(lang,'error.query'))
                    session=self.server.dashboard.session(query['id'][0],lang)
                    self._send(200,dict(session=session)) if session else self._send(404,dict(error=say(lang,'error.session_missing')))
                    return
                fields={'days','agent','project','lang'}|({'mask_projects'} if request.path.endswith('/export') else set())
                if (set(query) - fields or any(len(v) != 1 for v in query.values())
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
                    from .reporting import without_work_items
                    value=without_work_items(value)
                    mask=query.get('mask_projects',['0'])[0]
                    if mask not in ('0','1'): raise ValueError(say(lang,'error.query'))
                    if mask=='1':
                        from .reporting import mask_projects
                        value=mask_projects(value,lang)
                    else: value['project_names_masked']=False
                    self._send(200, value, filename=say(lang, 'export_file'))
                else:
                    self._send(200, value)
            elif request.path == '/api/health':
                ready = getattr(self.server, 'desktop_ready', None)
                self._send(200 if ready is None or ready.is_set() else 503,
                           dict(app='pler', version=__version__))
            else:
                self._send(404, dict(error=say(lang, 'error.not_found')))
        except UnknownProject as error:
            self._send(400, dict(error=str(error), code='unknown_project'))
        except ValueError as error:
            self._send(400, dict(error=str(error)))

    def do_POST(self):
        if urlsplit(self.path).path in ('/api/usage/backup','/api/usage/backup/check'):
            return self._post()
        with self.server._action_lock:
            from .updates import BUSY
            if self.server.updates.state in BUSY-{'checking'} and urlsplit(self.path).path not in ('/api/updates/check','/api/updates/install','/api/updates/preferences'):
                if not self._local():return
                if not self._token():
                    self._send(403,dict(error=say(self._lang(),'error.token')));return
                self._send(409,dict(error=say(self._lang(),'error.update_busy'),code='update_busy'))
                return
            return self._post()

    def _post(self):
        if not self._local():
            return
        route = urlsplit(self.path).path
        if route not in ('/api/usage/refresh', '/api/usage/archive/clear', '/api/usage/retention','/api/usage/cache/reset',
                         '/api/usage/verdict','/api/usage/plan','/api/usage/work','/api/usage/work/details','/api/usage/work/followup','/api/usage/backup','/api/usage/backup/check','/api/usage/budgets','/api/usage/budgets/ack',
                         '/api/usage/sources','/api/usage/reconnections','/api/quit','/api/updates/check','/api/updates/install','/api/updates/preferences'):
            self._send(404, dict(error=say(self._lang(), 'error.no_action')))
            return
        if (self.headers.get('Origin') != self.server.origin
                or not self._token()):
            self._send(403, dict(error=say(self._lang(), 'error.token')))
            return
        if route=='/api/usage/reconnections':
            self._reconnection_action()
            return
        if route == '/api/usage/sources':
            self._source_action()
            return
        if route.startswith('/api/updates/'):
            self._update_action(route)
            return
        if route in ('/api/usage/backup','/api/usage/backup/check'):
            self._backup(route)
            return
        if route in ('/api/usage/budgets', '/api/usage/budgets/ack'):
            self._budget_action(route)
            return
        if route in ('/api/usage/work','/api/usage/work/details'):
            self._work_item(details=route.endswith('/details'))
            return
        if route=='/api/usage/work/followup':
            self._followup()
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= (128 if route=='/api/usage/verdict' else 64) or self.headers.get_content_type() != 'application/json':
                raise ValueError(say(self._lang(), 'error.bad_request'))
            body=json.loads(self.rfile.read(size))
            valid=(isinstance(body,dict) and set(body)=={'enabled'} and type(body['enabled']) is bool
                   if route=='/api/usage/retention' else
                   isinstance(body,dict) and set(body)=={'id','verdict'} and isinstance(body['id'],str)
                   and re.fullmatch('[a-f0-9]{24}',body['id']) is not None and body['verdict'] in ('useful','wasted',None)
                   if route=='/api/usage/verdict' else
                   isinstance(body,dict) and set(body)=={'plan'} and body['plan'] in ('pro','max','ultra','api',None)
                   if route=='/api/usage/plan' else body=={})
            if not valid:
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
        elif route == '/api/usage/verdict':
            result=self.server.dashboard.set_verdict(body['id'],body['verdict'])
            if result.get('ok'):
                self._send(200,result)
            elif result.get('reason')=='missing':
                self._send(404,dict(error=say(self._lang(),'error.session_missing')))
            else:
                self._send(500,dict(error=say(self._lang(),'error.verdict_'+('unreadable' if result.get('reason')=='unreadable' else 'save'))))
        elif route == '/api/usage/plan':
            result=self.server.dashboard.set_plan(body['plan'])
            if result.get('ok'):
                self._send(200,result)
            else:
                reason=result.get('reason')
                self._send(409 if reason in ('unavailable','unreadable') else 500,
                           dict(error=say(self._lang(),'error.plan_'+('unreadable' if reason=='unreadable' else 'save'))))
        elif route in ('/api/usage/retention','/api/usage/cache/reset'):
            result=(self.server.dashboard.set_retention(body['enabled']) if route.endswith('/retention')
                    else self.server.dashboard.reset_cache())
            self._send(200,result) if result.get('ok') else self._send(500,dict(error=say(self._lang(),'error.metadata_settings')))
        else:
            self.server.dashboard.close(timeout=0)
            self._send(200, dict(closed=True))
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    def _source_action(self):
        try:
            body = self._annotation_json(8192)
            action = body.get('action')
            fields = ({'action','agent','path'} if action == 'check' else
                      {'action','agent','path','expected'} if action == 'add' else
                      {'action','id','expected'} if action == 'remove' else set())
            if not fields or set(body) != fields:
                raise ValueError()
            if action in ('check','add') and (body['agent'] not in ('claude-code','codex')
                    or not isinstance(body['path'], str) or not 1 <= len(body['path']) <= 1024):
                raise ValueError()
            for field in ('expected','id'):
                if field in body and (not isinstance(body[field], str) or not re.fullmatch('[a-f0-9]{24}', body[field])):
                    raise ValueError()
            result = self.server.dashboard.source_action(body)
            if not result.get('ok'): result['code'] = result.get('reason', 'invalid')
            self._send(200 if result.get('ok') else 409, result)
        except (ValueError, TypeError):
            self._send(400, dict(ok=False, reason='invalid'))

    def _budget_action(self, route):
        from .usage.budgets import valid_limit
        try:
            body = self._annotation_json(256)
            if (not isinstance(body.get('id'), str) or not re.fullmatch('[a-f0-9]{24}', body['id'])):
                raise ValueError()
            if route.endswith('/ack'):
                if (set(body) != {'id', 'revision', 'level'} or not isinstance(body['revision'], str)
                        or not re.fullmatch('[a-f0-9]{24}', body['revision'])
                        or type(body['level']) is not int or body['level'] not in (80, 100)):
                    raise ValueError()
                result = self.server.dashboard.ack_budget(body['id'], body['revision'], body['level'])
            else:
                if (set(body) != {'id', 'metric', 'limit', 'expected'}
                        or (body['expected'] is not None and (not isinstance(body['expected'], str)
                            or not re.fullmatch('[a-f0-9]{24}', body['expected'])))
                        or not (body['metric'] is None and body['limit'] is None
                                or valid_limit(body['metric'], body['limit']))):
                    raise ValueError()
                result = self.server.dashboard.set_budget(body['id'], body['metric'], body['limit'], body['expected'])
            self._send(200 if result.get('ok') else 409, result)
        except (ValueError, TypeError, OverflowError):
            self._send(400, dict(error=say(self._lang(), 'error.fields')))

    def _update_action(self,route):
        from .updates import UpdateError
        try:
            body=self._annotation_json(128)
            if route.endswith('/preferences'):
                if set(body)!={'automatic'} or type(body['automatic']) is not bool:raise ValueError()
                result=self.server.updates.preferences(body['automatic'])
            else:
                if body!={}:raise ValueError()
                result=self.server.updates.check() if route.endswith('/check') else self.server.updates.install()
            self._send(202 if not route.endswith('/preferences') else 200,result)
        except UpdateError as error:
            self._send(409,dict(error=say(self._lang(),'error.update_unavailable'),code=error.code))
        except ValueError:
            self._send(400,dict(error=say(self._lang(),'error.fields'),code='invalid'))

    def _annotation_json(self,limit):
        """Bound and authenticate admission before reading a manual annotation."""
        try:
            query=parse_qs(urlsplit(self.path).query,keep_blank_values=True)
            lengths=self.headers.get_all('Content-Length') or []
            if (set(query)-{'lang'} or any(len(v)!=1 for v in query.values())
                    or query.get('lang',['en'])[0] not in LANGUAGES or len(lengths)!=1
                    or self.headers.get('Transfer-Encoding') is not None
                    or not re.fullmatch('[0-9]{1,5}',lengths[0])
                    or not 0<int(lengths[0])<=limit
                    or self.headers.get_content_type()!='application/json'):
                raise ValueError()
            size=int(lengths[0]);raw=self.rfile.read(size)
            if len(raw)!=size:raise ValueError()
            def pairs(items):
                result={}
                for key,value in items:
                    if key in result:raise ValueError()
                    result[key]=value
                return result
            body=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,
                            parse_constant=lambda _:(_ for _ in ()).throw(ValueError()))
            if not isinstance(body,dict):raise ValueError()
            return body
        except (UnicodeError,RecursionError,TypeError,OverflowError):
            raise ValueError() from None

    def _reconnection_action(self):
        try:
            body=self._annotation_json(1024)
            action=body.get('action')
            if action=='preview':fields={'action','source','target'}
            elif action=='transfer':fields={'action','source','target','expected','confirmed','verdict_choice','budget_choice'}
            elif action in ('undo','clear'):fields={'action','expected'}
            else:raise ValueError()
            if set(body)!=fields:raise ValueError()
            for key in ('source','target'):
                if key in body and (not isinstance(body[key],str) or not re.fullmatch('[a-f0-9]{24}',body[key])):raise ValueError()
            if 'expected' in body and (not isinstance(body['expected'],str) or not re.fullmatch('[a-f0-9]{64}',body['expected'])):raise ValueError()
            if action=='transfer' and (body['confirmed'] is not True or any(body[k] not in ('','source','target') for k in ('verdict_choice','budget_choice'))):raise ValueError()
            result=self.server.dashboard.reconnect_action(body,self._lang())
            self._send(200 if result.get('ok') else 409,result)
        except (ValueError,TypeError,KeyError):
            self._send(400,dict(ok=False,reason='invalid'))

    def _work_item(self,details=False):
        """Small, authenticated manual annotations; no request can select a disk path."""
        lang=self._lang()
        from .usage import work_items as work_rules
        try:
            body=self._annotation_json(work_rules.MAX_DETAILS_REQUEST if details else 1024)
            action=body.get('action')
            if details!=(action=='describe'): raise ValueError()
            fields=({'action','title'} if action=='create' else
                    {'action','id','title'} if action=='rename' else
                    {'action','id','goal','outcome','result_note','expected_revision'} if action=='describe' else
                    {'action','id','session'} if action in ('link','unlink') else
                    {'action','id'} if action=='delete' else None)
            if fields is None or set(body) not in (fields,fields|{'session'} if action=='create' else fields):
                raise ValueError()
            if any(not isinstance(body[key],str) or re.fullmatch('[a-f0-9]{24}',body[key]) is None
                   for key in ('id','session','expected_revision') if key in body):raise ValueError()
            if 'title' in body and not isinstance(body['title'],str):raise ValueError()
            if details: work_rules.validate_details({key:body[key] for key in ('goal','outcome','result_note')})
        except (ValueError,UnicodeError,RecursionError,TypeError,OverflowError):
            self._send(400,dict(error=say(lang,'error.work_invalid'),code='invalid'))
            return
        extra=dict(details={key:body[key] for key in ('goal','outcome','result_note')},
                   expected_revision=body['expected_revision']) if details else {}
        result=self.server.dashboard.mutate_work_item(action,identity=body.get('id'),
            title=body.get('title'),session=body.get('session'),**extra)
        if result.get('ok'):
            self._send(200,result)
            return
        reason=result.get('reason','unsaved')
        known={'unavailable','unreadable','missing_session','missing','limit','invalid','unsaved','conflict'}
        reason=reason if reason in known else 'unsaved'
        code=404 if reason in ('missing','missing_session') else 409 if reason in ('unavailable','unreadable','conflict') else 400 if reason in ('invalid','limit') else 500
        key='error.work_'+reason
        self._send(code,dict(error=say(lang,key),code=reason))

    def _followup_result(self,result):
        if result.get('ok'):
            self._send(200,result)
            return
        reason=result.get('reason')
        known={'invalid','unavailable','unreadable','missing','stale','conflict','early','active','closed','limit','unsaved'}
        reason=reason if reason in known else 'unsaved'
        status=404 if reason=='missing' else 400 if reason in ('invalid','limit') else 500 if reason=='unsaved' else 409
        key='error.followup_'+reason
        self._send(status,dict(error=say(self._lang(),key),code=reason))

    def _followup(self):
        from .usage import followups
        try:
            body=self._annotation_json(16384)
            action=body.get('action')
            base={'action','id','expected_revision'}
            fields=(base|{'change','observation','trigger'} if action=='start_followup' else
                    base|{'record_id','context','note'} if action=='review_followup' else
                    base|{'record_id','note'} if action=='cancel_followup' else
                    base|{'record_id'} if action=='delete_followup' else None)
            if fields is None or set(body)!=fields: raise ValueError()
            if any(not followups.code(body[k]) for k in ('id','expected_revision','record_id') if k in body): raise ValueError()
            for key in ('change','observation','note'):
                if key in body: followups.text(body[key],required=key=='change')
            if 'trigger' in body and body['trigger'] not in followups.TRIGGERS: raise ValueError()
            if 'context' in body and body['context'] not in followups.CONTEXTS: raise ValueError()
        except (ValueError,TypeError,OverflowError):
            self._followup_result(dict(ok=False,reason='invalid'))
            return
        args={k:v for k,v in body.items() if k not in ('action','id')}
        self._followup_result(self.server.dashboard.mutate_followup(action,identity=body['id'],**args))

    def _backup(self,route):
        """A private local backup, not a masked report; uploads are checked in memory only."""
        from .usage import backup
        lang=self._lang()
        with self.server.dashboard.lock:
            allowed=(self.server.dashboard.scanned_at is not None
                     and not self.server.dashboard.sources.get('demo')
                     and not self.server.dashboard._closed)
        if not allowed:
            self._send(409,dict(error=say(lang,'error.backup_unavailable'),code='unavailable'))
            return
        if not self.server._backup_lock.acquire(blocking=False):
            self._send(409,dict(error=say(lang,'error.backup_busy'),code='busy'))
            return
        try:
            query=parse_qs(urlsplit(self.path).query,keep_blank_values=True)
            if (set(query)-{'lang'} or any(len(values)!=1 for values in query.values())
                    or query.get('lang',['en'])[0] not in LANGUAGES):
                raise backup.BackupError('invalid')
            # This route deliberately admits a larger *bounded* body than JSON actions.
            # Authentication was checked before any body read or metadata access.
            lengths=self.headers.get_all('Content-Length') or []
            if len(lengths)!=1 or self.headers.get('Transfer-Encoding') is not None:
                raise backup.BackupError('invalid')
            raw_size=lengths[0]
            if not re.fullmatch('[0-9]{1,9}',raw_size):
                raise backup.BackupError('invalid')
            size=int(raw_size)
            checking=route.endswith('/check')
            if not 0<size<=(backup.MAX_BUNDLE_BYTES if checking else 64):
                raise backup.BackupError('limit')
            wanted='application/octet-stream' if checking else 'application/json'
            if self.headers.get_content_type()!=wanted:
                raise backup.BackupError('invalid')
            data=self.rfile.read(size)
            if len(data)!=size:
                raise backup.BackupError('invalid')
            if checking:
                self._send(200,dict(ok=True,backup=backup.inspect(data)))
            else:
                try:body=json.loads(data)
                except (ValueError,UnicodeError,RecursionError):raise backup.BackupError('invalid')
                if body!={}:raise backup.BackupError('invalid')
                data=backup.create()
                self._send(200,data,'application/zip',filename='PLER-backup.zip')
        except backup.BackupError as error:
            status=409 if error.code=='busy' else 400
            key='backup.error.'+error.code if error.code in ('invalid','unsupported','limit','unsafe_path','exists','io','busy') else 'error.backup_failed'
            self._send(status,dict(error=say(lang,key),
                                   code=error.code))
        except (OSError,ValueError,TypeError,OverflowError,MemoryError):
            self._send(500,dict(error=say(lang,'error.backup_failed'),code='io'))
        finally:
            self.server._backup_lock.release()
