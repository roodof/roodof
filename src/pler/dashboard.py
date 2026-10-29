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
import os
import threading

from .i18n import LANGUAGES, count, say
from .git_activity import CREATED, check_branches, read_repository, session_activity
from .usage import scan, AGENTS
from .usage.forecast import outlook as quota_outlook
from .usage.insights import insights as find_insights
from .usage.projects import ProjectRoots, label
from .usage.records import total, timestamp
from .usage.reedit import analyze as subsequent_edits, insight as edit_insight
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


def _link_key(session):
    return session.agent, session.source, session.session_id


def git_links(sessions):
    """Repositories each session is linked to: its working folder, and the nearest repository above each
    file it edited (an agent started in a parent folder often edits a repository inside it). Paths stay
    in memory for reading the local Git history; the public view only gets counts and reasons."""
    roots, found, links = ProjectRoots(), {}, {}
    def repository(folder):
        if folder not in found:
            try:
                found[folder] = roots._git_root(folder)
            except (OSError, ValueError, RuntimeError):
                found[folder] = None
        return found[folder]
    for session in sessions:
        linked = {}
        if session.project:
            linked[os.path.normcase(os.path.normpath(session.project))] = [session.project, {'working_folder'}]
        for path in session.files_edited:
            root = repository(os.path.dirname(os.path.normpath(path))) if os.path.isabs(path) else None
            if root:
                linked.setdefault(os.path.normcase(os.path.normpath(root)), [root, set()])[1].add('edited_files')
        links[_link_key(session)] = {path: reasons for path, reasons in linked.values()}
    return links


def _git_for(session, sources):
    activity, links = sources.get('git_activity', {}), sources.get('git_links')
    if links is None:  # a snapshot made without links: the working folder only
        return activity.get(session.project)
    return [(activity.get(path), tuple(sorted(reasons))) for path, reasons in links.get(_link_key(session), {}).items()]


def git_outcome(rows, sources):
    """Commits recorded during the selected sessions in their linked repositories, each counted once even
    when sessions overlap, and how many are still on a branch. None without any such commit."""
    links, activity = sources.get('git_links'), sources.get('git_activity', {})
    if links is None:
        return None
    commits, sessions, tokens = {}, 0, 0
    for session in rows:
        if not session.started or not session.ended:
            continue
        found = False
        for path in links.get(_link_key(session), {}):
            snapshot = activity.get(path) or {}
            for event in snapshot.get('events', ()) if snapshot.get('state') == 'ready' else ():
                if event['kind'] in CREATED and event.get('full') and session.started <= event['at'] <= session.ended:
                    commits[(os.path.normcase(path), event['full'])] = snapshot.get('branch', {}).get(event['full'])
                    found = True
        if found:
            sessions += 1
            tokens += total(session.tokens)
    if not commits:
        return None
    states = list(commits.values())
    everything = sum(total(s.tokens) for s in rows)
    return dict(sessions=sessions, commits=len(states), on_branch=states.count(True), off_branch=states.count(False),
                unknown=sum(state is None for state in states), token_share=tokens / everything if everything else None)


def _git_insight(outcome, lang, usage_complete):
    if not outcome:
        return []
    rest = ''
    if outcome['off_branch']:
        rest += say(lang, 'insight.git.off', n=outcome['off_branch'])
    if outcome['unknown']:
        rest += say(lang, 'insight.git.unknown', n=outcome['unknown'])
    if usage_complete and outcome['token_share'] is not None:
        rest += say(lang, 'insight.git.share', share=round(outcome['token_share'] * 100))
    return [dict(kind='git_outcome', level='info', title=say(lang, 'insight.git.title'),
                 detail=say(lang, 'insight.git.detail', sessions=count(lang, outcome['sessions'], 'session'),
                            commits=count(lang, outcome['commits'], 'commit'), kept=outcome['on_branch'], rest=rest),
                 evidence=outcome)]


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
                source_state=getattr(session,'source_state','live'),
                source_deleted=bool(getattr(session,'source_deleted',False)),
                archive_files=getattr(session,'archive_files',0),
                archive_old_parser=bool(getattr(session,'archive_old_parser',False)),
                archive_unverified=bool(getattr(session,'archive_unverified',False)),
                source_note=(say(lang,'archive.source_mixed') if getattr(session,'source_state','live')=='mixed'
                             else say(lang,'archive.source_deleted' if getattr(session,'source_deleted',False)
                                      else 'archive.source_unverified')
                             if getattr(session,'source_state','live')=='archive' else ''),
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
    outcome=git_outcome(rows,sources)
    reedit=subsequent_edits(sessions,rows,timestamp(sources.get('observed_at')) or now)
    archive=sources.get('archive') or {}
    archive_public={key:archive.get(key,False if key=='enabled' else 0) for key in
                    ('enabled','stored_files','archive_files','old_parser_files','unverified_files','evicted_files','errors')}
    archive_public['sessions']=sum(getattr(s,'source_state','live')!='live' for s in rows)
    return dict(**provenance(archived=bool(archive_public['sessions'])),quality=trust,mode='local_agent_usage', new_model_calls=0, filters=dict(days=days, agent=agent, project=project),
                period=dict(since=_iso(since), mode='active_sessions_full_totals',
                            cross_period_sessions=sum(bool(s.started and since and s.started < since) for s in rows)),
                totals=summary['totals'], agents=summary['agents'], models=summary['models'], projects=projects,
                project_options=[dict(id=key, name=name) for key, name in options],
                sessions=sorted((session_view(s, lang, _git_for(s, sources)) for s in rows),
                                key=lambda row: (row['total_tokens'], row['ended'] or ''), reverse=True),
                quota=account_quota, claude_limit_events=summary['claude_limit_events'],
                outlook=windows, insights=find_insights(rows, windows, since, lang=lang,
                    usage_complete=trust['tokens_complete'] and trust['attribution_complete'])
                    + _git_insight(outcome, lang, trust['tokens_complete'] and trust['attribution_complete']) + edit_insight(reedit,lang),
                git_outcome=outcome, reedit=reedit, archive=archive_public, lang=lang, demo=bool(sources.get('demo')),
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
        self.generation = 0

    def refresh(self, force=False):
        with self.lock:
            if self.state == 'scanning' and not force:
                return dict(state='scanning', started=False, new_model_calls=0)
            self.state, self.error = 'scanning', None
            self.generation += 1
            self.thread = threading.Thread(target=self._scan, args=(self.generation,), daemon=True)
            self.thread.start()
            return dict(state='scanning', started=True, new_model_calls=0)

    def clear_archive(self):
        from .usage.archive import clear_archive
        with self.lock:
            result = clear_archive()
            if not result.get('ok'):
                return dict(ok=False, cleared_files=0, errors=result.get('errors',1))
            self.generation += 1
            self.sessions, self.sources = [], {}
            self.scanned_at, self.error, self.state = None, None, 'idle'
            self.refresh(force=True)
            return dict(ok=True, cleared_files=result.get('cleared_files',0), errors=0, state='scanning')

    def _scan(self, generation=None):
        if generation is None:
            with self.lock:
                generation = self.generation
        try:
            sessions, sources = self.reader()
            sources = dict(sources)
            sources['git_links'] = git_links(sessions)
            folders = {path for linked in sources['git_links'].values() for path in linked}
            sources['git_activity'] = {path: self.git_reader(path) for path in folders}
            windows = {}
            for session in sessions:
                if session.started and session.ended:
                    for path in sources['git_links'][_link_key(session)]:
                        windows.setdefault(path, []).append((session.started, session.ended))
            for path, snapshot in sources['git_activity'].items():
                check_branches(snapshot, windows.get(path, ()))
            # Validate the projection before publishing a replacement snapshot.
            project_view(sessions, sources, days=0)
            with self.lock:
                if generation != self.generation:
                    return
                self.sessions, self.sources = sessions, sources
                self.scanned_at = datetime.now(timezone.utc).isoformat()
                self.state, self.error = 'ready', None
        except Exception:
            # Reader errors may contain transcript excerpts or private paths.
            # Keep an earlier usable snapshot; never send a raw exception to UI.
            with self.lock:
                if generation != self.generation:
                    return
                self.state, self.error = 'error', 'error.scan'

    def view(self, days=30, agent='all', project='all', lang='en'):
        with self.lock:
            archive=self.sources.get('archive') or {}
            if archive.get('enabled') and self.scanned_at is not None:
                from .usage.archive import archive_generation
                current=archive_generation()
                if current is not None and current != archive.get('clear_generation'):
                    self.generation += 1
                    self.sessions,self.sources=[],{}
                    self.scanned_at,self.state,self.error=None,'idle',None
                    self.refresh(force=True)
            value = project_view(self.sessions, self.sources, days, agent, project, lang=lang)
            value.update(state=self.state, scanned_at=self.scanned_at, error=self.error and say(value['lang'], self.error),
                         has_snapshot=self.scanned_at is not None)
            return value
