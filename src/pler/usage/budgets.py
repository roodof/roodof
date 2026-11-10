"""Optional local session alerts. Read-only agent integration; never enforces a spending cap.

Only opaque row codes, limits, revisions and notification acknowledgements are persisted.
Bindings come from the current reconciled snapshot. A moved/missing source is not silently
rebound by provider ID (copies/forks can share that ID). Ordinary exports/backups omit this
independent preference file. Demo preferences are memory-only.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import secrets
import stat
import threading

from ..paths import cache_file
from ..runtime import cancellation, ScanCancelled
from .records import total
from .verdicts import CODE, session_code
from . import input_limits

FILENAME = 'session-budgets.json'
MAX_ENTRIES = 20
MAX_BYTES = 32768
INTERVAL = 10
MAX_GROUP_FILES = 64
MAX_TICK_BYTES = 64 * 1024 * 1024


def valid_limit(metric, limit):
    return (metric in ('tokens', 'usd') and type(limit) in (int, float)
            and 0 < limit <= (10**12 if metric == 'tokens' else 10**6) and math.isfinite(limit)
            and (metric != 'tokens' or type(limit) is int))


def validate(entries):
    if not isinstance(entries, dict) or len(entries) > MAX_ENTRIES:
        raise ValueError('invalid budgets')
    for code, row in entries.items():
        if (not isinstance(code, str) or not CODE.fullmatch(code) or not isinstance(row, dict)
                or set(row) != {'metric', 'limit', 'revision', 'notified'}
                or not valid_limit(row['metric'], row['limit'])
                or not isinstance(row['revision'], str) or not CODE.fullmatch(row['revision'])
                or row['notified'] not in ([], [80], [80, 100])
                or not all(type(n) is int for n in row['notified'])):
            raise ValueError('invalid budget')
    return entries


def validate_document(data):
    if type(data) is not bytes or len(data) > MAX_BYTES:
        raise ValueError('oversized budgets')
    try:
        value = json.loads(data.decode('utf-8'))
    except RecursionError as error:
        raise ValueError('over-nested budgets') from error
    if (not isinstance(value, dict) or set(value) != {'format', 'entries'}
            or type(value['format']) is not int or value['format'] != 1):
        raise ValueError('invalid budgets')
    return validate(value['entries'])


class Store:
    def __init__(self, base=None, memory=False):
        self.base, self.memory, self.entries = base, memory, {}

    def read(self):
        if self.memory:
            return deepcopy(self.entries)
        path = cache_file(FILENAME, self.base)
        if path is None:
            raise OSError('unsafe budget file')
        from .archive import _locked
        with _locked(path.parent):
            return self._read(path)

    def _read(self,path):
        try:
            with path.open('rb') as stream:
                data = stream.read(MAX_BYTES + 1)
        except FileNotFoundError:
            return {}
        return validate_document(data)

    def change(self, action):
        from .archive import _locked, _write
        if self.memory:
            entries = self.read()
            result = action(entries)
            self.entries = validate(entries)
            return result
        path = cache_file(FILENAME, self.base)
        if path is None:
            raise OSError('unsafe budget file')
        with _locked(path.parent):
            entries = self.read()  # preserve other Roodof windows' changes
            result = action(entries)
            _write(path, dict(format=1, entries=validate(entries)))
            return result


def binding(session, sessions):
    group = getattr(session, '_history_group', session.session_id)
    related = [s for s in sessions if s.agent == session.agent
               and getattr(s, '_history_group', s.session_id) == group]
    paths, objects = set(), {}
    for row in related:
        relocated = getattr(row, '_pler_live_sources', None)
        if row.source_state != 'live' and not relocated:
            return dict(reason='archive', paths=())
        paths.update(relocated or getattr(row, '_sources', {}) or {row.source: {}})
        objects.update(getattr(row, '_pler_file_objects', {}))
    return dict(reason=None, paths=tuple(sorted(paths)), objects={p:objects[p] for p in paths if p in objects})


def verify_file_objects(objects):
    if not objects: return
    from .identities import sample
    current = sample(objects)
    if any(current.get(path, ())[:3] != expected for path, expected in objects.items()):
        raise OSError('budget source object changed')


@input_limits.scoped
def read_group(agent, paths, access):
    from . import claude_code, codex
    if agent == 'codex':
        rows, issues = codex.read([Path(p) for p in paths], access=access)
    else:
        issues = []
        rows = claude_code.read([Path(p) for p in paths], issues, access=access)
    if issues:
        raise ValueError('incomplete budget source')
    return rows


def matching_session(rows, target, code):
    candidates = [row for row in rows if session_code(row) == code or (
        getattr(target, '_pler_identity', None) == code and row.agent == target.agent
        and row.session_id == target.session_id)]
    return candidates[0] if len(candidates) == 1 else None


class Monitor:
    def __init__(self, store=None, reader=read_group, autostart=True):
        self.store = store if store is not None else Store()
        self.reader = reader
        self.lock = threading.RLock()
        self.targets, self.observations, self.signatures = {}, {}, {}
        self.error = False
        self.stop, self.wake = threading.Event(), threading.Event()
        self.thread = None
        self.autostart = autostart

    def _start(self, entries):
        if (self.autostart and entries and not self.stop.is_set()
                and (self.thread is None or not self.thread.is_alive())):
            self.thread = threading.Thread(target=self._run, daemon=True, name='pler-budget-alerts')
            self.thread.start()

    def bind(self, sessions, demo=False):
        with self.lock:
            targets, groups, bindings = {}, {}, {}
            for session in sessions:
                key = (session.agent, getattr(session, '_history_group', session.session_id))
                groups.setdefault(key, []).append(session)
            for session in sessions:
                key = (session.agent, getattr(session, '_history_group', session.session_id))
                if key not in bindings:
                    bindings[key] = binding(session, groups[key])
                targets[session_code(session)] = dict(session=session, demo=demo,
                                                     **bindings[key])
            self.targets = targets
            self.signatures.clear()
            self.wake.set()
            try:
                entries = self.store.read()
                self.error = False
            except (OSError, ValueError, UnicodeError):
                self.error = True
                entries = {}
            self._start(entries)

    def _run(self):
        while not self.stop.is_set():
            self.wake.clear()
            try:
                with cancellation(self.stop):
                    self.tick()
            except ScanCancelled:
                return
            except Exception:
                # Never expose source paths or excerpts in a support-facing response.
                with self.lock:
                    self.error = True
            self.wake.wait(INTERVAL)

    def close(self):
        self.stop.set()
        self.wake.set()

    def configure(self, code, metric, limit, expected):
        if not isinstance(code, str) or not CODE.fullmatch(code):
            raise ValueError('invalid budget session')
        if metric is not None and not valid_limit(metric, limit):
            raise ValueError('invalid budget limit')
        with self.lock:
            if metric is not None and code not in self.targets:
                return dict(ok=False, reason='missing')
            def change(entries):
                old = entries.get(code)
                if expected != (old['revision'] if old else None):
                    return dict(ok=False, reason='conflict')
                if metric is None:
                    entries.pop(code, None)
                elif not old or (old['metric'], old['limit']) != (metric, limit):
                    if not old and len(entries) >= MAX_ENTRIES:
                        return dict(ok=False, reason='limit')
                    entries[code] = dict(metric=metric, limit=limit, revision=secrets.token_hex(12), notified=[])
                return dict(ok=True)
            result = self.store.change(change)
            if result['ok']:
                self.bind([t['session'] for t in self.targets.values()],
                          demo=any(t['demo'] for t in self.targets.values()))
            return result

    def acknowledge(self, code, revision, level):
        if type(level) is not int or level not in (80, 100):
            raise ValueError('invalid budget acknowledgement')
        with self.lock:
            def change(entries):
                row = entries.get(code)
                if row is None or row['revision'] != revision:
                    return dict(ok=False, reason='conflict')
                observation = self.observations.get(code, {})
                if observation.get('state') != 'watching' or observation.get('level', 0) < level:
                    return dict(ok=False, reason='unavailable')
                row['notified'] = sorted(set(row['notified']) | ({80, 100} if level == 100 else {80}))
                return dict(ok=True)
            return self.store.change(change)

    def tick(self):
        from . import discovery
        access = discovery.WslRoots()
        with self.lock:
            entries = self.store.read()
            targets = dict(self.targets)
        spent, grouped = 0, {}
        for code, config in entries.items():
            input_limits.checkpoint()
            target = targets.get(code)
            observation = dict(state='missing', amount=None, checked_at=None, level=0)
            signature = None
            if target is not None:
                session = target['session']
                try:
                    if target['demo']:
                        signature = ('demo', total(session.tokens), session.api_usd)
                        found = session
                    elif target['reason']:
                        observation['state'] = target['reason']
                        found = None
                    elif not target['paths'] or len(target['paths']) > MAX_GROUP_FILES:
                        observation['state'] = 'read_limit'
                        found = None
                    else:
                        verify_file_objects(target.get('objects'))
                        signatures = []
                        for name in target['paths']:
                            path = discovery.local(name, access=access)
                            if path is None:
                                raise OSError('source unavailable')
                            info = path.stat()
                            if not stat.S_ISREG(info.st_mode):
                                raise OSError('not a regular source')
                            signatures.append((name, info.st_size, info.st_mtime_ns, info.st_ino))
                        signature = tuple(signatures)
                        key = (session.agent, target['paths'])
                        with self.lock:
                            cached = self.signatures.get(code)
                        if cached and cached[0] == signature:
                            found = cached[1]
                        elif key in grouped:
                            found = matching_session(grouped[key], session, code)
                        elif spent + sum(s[1] for s in signature) > MAX_TICK_BYTES:
                            observation['state'] = 'read_limit'
                            found = None
                        else:
                            spent += sum(s[1] for s in signature)
                            grouped[key] = self.reader(session.agent, target['paths'], access)
                            found = matching_session(grouped[key], session, code)
                        verify_file_objects(target.get('objects'))
                    if found is not None:
                        amount = total(found.tokens) if config['metric'] == 'tokens' else found.api_usd
                        priced = found.api_priced_tokens == total(found.tokens)
                        retained_trusted = (session.source_state == 'live' or (
                            session.tokens_complete and session.attribution_complete and (
                                config['metric'] != 'usd' or session.models_complete
                                and session.api_priced_tokens == total(session.tokens))))
                        complete = (found.tokens_complete and found.attribution_complete
                                    and retained_trusted
                                    and all(found.tokens[k] >= session.tokens[k] for k in ('input','cache_read','cache_write','output'))
                                    and not found.archive_unverified and not found.archive_old_parser
                                    and (config['metric'] != 'usd' or priced))
                        level = 100 if amount >= config['limit'] else 80 if amount >= config['limit'] * .8 else 0
                        observation = dict(state='watching' if complete else 'partial', amount=amount,
                                           checked_at=datetime.now(timezone.utc).isoformat(),
                                           level=level if complete else 0,
                                           last_event_at=found.ended.isoformat() if found.ended else None)
                except ScanCancelled:
                    raise
                except (OSError, ValueError, RuntimeError):
                    observation['state'] = 'read_error'
                    found = None
            with self.lock:
                if self.targets.get(code) is not target:
                    continue  # a newer scan replaced this binding while I/O was in flight
                observation['revision'] = config['revision']
                self.observations[code] = observation
                if target is not None and found is not None and signature is not None:
                    self.signatures[code] = (signature, found)
        with self.lock:
            self.error = False

    def view(self):
        with self.lock:
            try:
                entries = self.store.read()
                self.error = False
            except (OSError, ValueError, UnicodeError):
                self.error = True
                entries = {}
            rows = []
            self._start(entries)
            for code, config in entries.items():
                observed = self.observations.get(code, {})
                if observed.get('revision') != config['revision']:
                    observed = dict(state='checking', amount=None, checked_at=None, level=0)
                if observed.get('checked_at') and observed.get('state') == 'watching':
                    age = (datetime.now(timezone.utc) - datetime.fromisoformat(observed['checked_at'])).total_seconds()
                    if age > INTERVAL * 4:
                        observed = dict(observed, state='stale')
                level = observed.get('level', 0)
                rows.append(dict(dict(id=code, **config), **observed,
                                 pending_level=level if observed.get('state') == 'watching' and level
                                 and level not in config['notified'] else 0))
            return dict(items=rows, readable=not self.error, interval_seconds=INTERVAL,
                        max_entries=MAX_ENTRIES, hard_cap=False)
