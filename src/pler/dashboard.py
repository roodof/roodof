"""Local, metadata-only view of existing agent logs. Never constructs a model client.

Readers stay in pler.usage. The browser receives an explicit projection: no raw
transcript, prompt, command, tool output, absolute source path or cost figure.
Periods select sessions active since the cutoff; totals cover those whole sessions.
Words are in the requested language, en or tr (i18n.py).
"""
from collections import Counter
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import threading

from .i18n import LANGUAGES, say
from .git_activity import read_repository, session_activity
from .usage import scan, AGENTS
from .usage.forecast import outlook as quota_outlook
from .usage.insights import insights as find_insights
from .usage.projects import label
from .usage.records import total
from .usage.summary import summarize, quota_burn
from .reporting import provenance,quality

PERIODS = (0, 7, 30, 90)


class UnknownProject(ValueError):
    pass


def _id(kind, value):
    return hashlib.sha256((kind + ':' + (value or 'unknown')).encode('utf-8')).hexdigest()[:24]


def _project(value, lang):
    return label(value, lang=lang) or say(lang, 'unknown_project').capitalize()


def _iso(value):
    return value.isoformat() if value else None


def _notes(session, lang):
    notes = []
    if any(n.startswith('Older Codex log:') for n in session.notes):
        notes.append(say(lang, 'note.older_codex'))
    if any(n.startswith('codex-auto-review') for n in session.notes):
        notes.append(say(lang, 'note.routing_alias'))
    notes.extend(item['detail'] for item in quality([session],{},lang)['issues'])
    return notes


def session_view(session, lang='en', git=None):
    inputs = sum(session.tokens[k] for k in ('input', 'cache_read', 'cache_write'))
    span = (session.ended - session.started).total_seconds() if session.started and session.ended else None
    active = session.active_ms
    # Forked/copied logs can carry the same provider session ID. The visible
    # code identifies the row's source too, without disclosing either value.
    return dict(id=_id(session.agent, session.source + '\0' + session.session_id), agent=session.agent,
                project_id=_id('project', session.project), project=_project(session.project, lang),
                started=_iso(session.started), ended=_iso(session.ended),
                span_seconds=span if span is not None and span >= 0 else None,
                active_ms=active if type(active) is int and active >= 0 else None,
                calls=session.calls, prompts=session.prompts, errors=session.errors, aborted=session.aborted,
                calls_complete=session.calls_complete and not any(n.startswith('Older Codex log:') for n in session.notes),
                quality=quality([session],{},lang),
                tokens=dict(session.tokens), total_tokens=total(session.tokens),
                cache_read_share=session.tokens['cache_read'] / inputs if inputs else None,
                models=[dict(model=m, calls=session.models.get(m, 0), total_tokens=t)
                        for m, t in sorted(session.model_tokens.items(), key=lambda row: row[1], reverse=True)],
                tool_calls=sum(session.tools.values()), edited_files=len(session.files_edited),
                quota_burn=[dict(window_minutes=w, percentage_points=used) for w, used in quota_burn(session).items()],
                notes=_notes(session, lang), git_activity=session_activity(git, session.started, session.ended))


def project_view(sessions, sources, days=30, agent='all', project='all', now=None, lang='en'):
    lang = lang if lang in LANGUAGES else 'en'
    if type(days) is not int or days not in PERIODS:
        raise ValueError(say(lang, 'error.period'))
    if agent not in ('all', *AGENTS):
        raise ValueError(say(lang, 'error.agent'))
    known_projects = {_id('project', s.project) for s in sessions}
    if project != 'all' and project not in known_projects:
        raise UnknownProject(say(lang, 'error.unknown_project'))
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=days) if days else None
    rows = [s for s in sessions if (since is None or (s.ended is not None and s.ended >= since))
            and (agent == 'all' or s.agent == agent) and (project == 'all' or _id('project', s.project) == project)]
    # The common summary sorts timestamps; preserve unknown dates in the public
    # session row rather than replacing them with an invented date in the UI.
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    safe = [replace(s, started=s.started or s.ended or epoch, ended=s.ended or s.started or epoch) for s in rows]
    summary = summarize(safe, top=0)
    projects = []
    for p in summary['projects']:
        raw = p['project']
        value = {k: v for k, v in p.items() if k != 'project'}
        projects.append(dict(value, id=_id('project', None if raw == 'unknown' else raw), name=_project(None if raw == 'unknown' else raw, lang)))
    options = sorted({(_id('project', s.project), _project(s.project, lang)) for s in sessions}, key=lambda row: row[1].casefold())
    # The meter is account-wide, so every session counts here, plus the Claude Code status line samples.
    windows = quota_outlook(sessions, now, sources.get('claude_quota', ()))
    # Older logs lack reset timestamps, but their last meter sample is still account-wide.
    # Do not switch to a project's older percentage when a UI filter changes.
    account_rows = [replace(s, started=s.started or s.ended or epoch, ended=s.ended or s.started or epoch) for s in sessions]
    account_quota = summarize(account_rows, top=0)['quota']
    skipped = sources.get('skipped', [])
    reason_keys={'MalformedRows':'malformed_file','InconsistentReasoning':'inconsistent_reasoning_file'}
    reasons = Counter(say(lang,reason_keys.get(reason,'unreadable_file')) for _, reason in skipped)
    trust=quality(rows,sources,lang)
    return dict(**provenance(),quality=trust,mode='local_agent_usage', new_model_calls=0, filters=dict(days=days, agent=agent, project=project),
                period=dict(since=_iso(since), mode='active_sessions_full_totals',
                            cross_period_sessions=sum(bool(s.started and since and s.started < since) for s in rows)),
                totals=summary['totals'], agents=summary['agents'], models=summary['models'], projects=projects,
                project_options=[dict(id=key, name=name) for key, name in options],
                sessions=sorted((session_view(s, lang, sources.get('git_activity', {}).get(s.project)) for s in rows),
                                key=lambda row: (row['total_tokens'], row['ended'] or ''), reverse=True),
                quota=account_quota, claude_limit_events=summary['claude_limit_events'],
                outlook=windows, insights=find_insights(rows, windows, since, lang=lang,
                    usage_complete=trust['tokens_complete'] and trust['attribution_complete']), lang=lang,
                claude_statusline=bool(sources.get('claude_quota')),
                unknown_call_sessions=sum(not s.calls_complete or any(n.startswith('Older Codex log:') for n in s.notes) for s in rows),
                sources=dict(claude_files=sources.get('claude_files', 0), codex_files=sources.get('codex_files', 0),
                             unreadable=len(skipped), issues=[dict(reason=reason, files=count) for reason, count in reasons.items()]),
                privacy=say(lang, 'privacy'), scope=say(lang, 'scope'))


class UsageDashboard:
    def __init__(self, reader=None, git_reader=None):
        self.reader = reader or scan
        self.git_reader = git_reader or read_repository
        self.lock = threading.RLock()
        self.sessions = []
        self.sources = {}
        self.state = 'idle'
        self.scanned_at = None
        self.error = None
        self.thread = None

    def refresh(self):
        with self.lock:
            if self.state == 'scanning':
                return dict(state='scanning', started=False, new_model_calls=0)
            self.state, self.error = 'scanning', None
            self.thread = threading.Thread(target=self._scan, daemon=True)
            self.thread.start()
            return dict(state='scanning', started=True, new_model_calls=0)

    def _scan(self):
        try:
            sessions, sources = self.reader()
            sources = dict(sources)
            sources['git_activity'] = {project: self.git_reader(project) for project in {s.project for s in sessions} if project}
            # Validate the projection before publishing a replacement snapshot.
            project_view(sessions, sources, days=0)
            with self.lock:
                self.sessions, self.sources = sessions, sources
                self.scanned_at = datetime.now(timezone.utc).isoformat()
                self.state, self.error = 'ready', None
        except Exception:
            # Reader errors may contain transcript excerpts or private paths.
            # Keep an earlier usable snapshot; never send a raw exception to UI.
            with self.lock:
                self.state, self.error = 'error', 'error.scan'

    def view(self, days=30, agent='all', project='all', lang='en'):
        with self.lock:
            value = project_view(self.sessions, self.sources, days, agent, project, lang=lang)
            value.update(state=self.state, scanned_at=self.scanned_at, error=self.error and say(value['lang'], self.error),
                         has_snapshot=self.scanned_at is not None)
            return value
