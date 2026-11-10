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
import secrets
import threading
import time

from .i18n import LANGUAGES, count, say
from .runtime import ScanCancelled, cancellation, checkpoint
from .git_activity import CREATED, check_branches, check_survival, read_repository, session_activity, _lines
from .git_survival import Saved
from .usage import Rescan, AGENTS
from .usage.forecast import outlook as quota_outlook
from .usage.insights import insights as find_insights
from .usage.projects import ProjectRoots, label, labels
from .usage.records import total, timestamp
from .usage.reedit import analyze as subsequent_edits, insight as edit_insight
from .usage.period_usage import analyze as dated_usage
from .usage.timeline import hourly as hourly_usage
from .usage.pricing import PRICES_AS_OF
from .usage.verdicts import Folder, session_code, summary as verdict_summary
from .usage.identities import IdentityError
from .usage.sources import SourceError
from . import diagnostics
from .usage.input_limits import ReadLimitExceeded
from .usage import work_items as work_rules
from .usage import plans as plan_rules
from .usage import followups as followup_rules
from .usage.checks import summary as check_summary
from .usage.insights import tests as test_insight
from .usage.summary import summarize, quota_burn
from .reporting import PARSER_VERSION,provenance,quality,affected,coverage_guidance

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
    if getattr(session, '_pler_identity_state', None) in ('unverified', 'conflict'):
        notes.append(say(lang, 'identity.unverified'))
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
        checkpoint()
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
    commits, sessions, tokens, measured = {}, 0, 0, {}
    for session in rows:
        if not session.started or not session.ended:
            continue
        found = False
        for path in links.get(_link_key(session), {}):
            snapshot = activity.get(path) or {}
            for event in snapshot.get('events', ()) if snapshot.get('state') == 'ready' else ():
                if event['kind'] in CREATED and event.get('full') and session.started <= event['at'] <= session.ended:
                    key = (os.path.normcase(path), event['full'])
                    commits[key] = snapshot.get('branch', {}).get(event['full'])
                    if commits[key]:
                        measured[key] = snapshot.get('survival', {}).get(event['full'])
                    found = True
        if found:
            sessions += 1
            tokens += total(session.tokens)
    if not commits:
        return None
    states = list(commits.values())
    everything = sum(total(s.tokens) for s in rows)
    return dict(sessions=sessions, commits=len(states), on_branch=states.count(True), off_branch=states.count(False),
                unknown=sum(state is None for state in states), token_share=tokens / everything if everything else None,
                lines=_lines(list(measured.values())))


def _git_insight(outcome, lang, usage_complete):
    if not outcome:
        return []
    rest = ''
    if outcome['off_branch']:
        rest += say(lang, 'insight.git.off', n=outcome['off_branch'])
    if outcome['unknown']:
        rest += say(lang, 'insight.git.unknown', n=outcome['unknown'])
    lines = outcome.get('lines') or {}
    if lines.get('added'):
        rest += say(lang, 'insight.git.lines', added=lines['added'], share=round(lines['kept'] / lines['added'] * 100),
                    commits=count(lang, lines['commits'], 'commit'))
    if usage_complete and outcome['token_share'] is not None:
        rest += say(lang, 'insight.git.share', share=round(outcome['token_share'] * 100))
    return [dict(kind='git_outcome', level='info', title=say(lang, 'insight.git.title'),
                 detail=say(lang, 'insight.git.detail', sessions=count(lang, outcome['sessions'], 'session'),
                            commits=count(lang, outcome['commits'], 'commit'), kept=outcome['on_branch'], rest=rest),
                 evidence=outcome)]


def session_view(session, lang='en', git=None, project_names=None, verdicts=None, titles=None, title_status=None):
    inputs = sum(session.tokens[k] for k in ('input', 'cache_read', 'cache_write'))
    span = (session.ended - session.started).total_seconds() if session.started and session.ended else None
    active = session.active_ms
    # Initially source-sensitive; a verified physical move retains the original code.
    # Provider IDs alone never reassign the user's annotations.
    code = session_code(session)
    return dict(id=code, agent=session.agent, verdict=(verdicts or {}).get(code),
                title=(titles or {}).get(code),
                title_info=diagnostics.title_info((title_status or {}).get(code), (titles or {}).get(code), lang),
                identity_state=getattr(session, '_pler_identity_state', 'original'),
                project_id=_id('project', session.project), project=(project_names or {}).get(session.project,_project(session.project, lang)),
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
                api_usd=round(session.api_usd, 2),
                api_priced_share=session.api_priced_tokens / total(session.tokens) if total(session.tokens) else None,
                models=[dict(model=m, calls=session.models.get(m, 0), total_tokens=t)
                        for m, t in sorted(session.model_tokens.items(), key=lambda row: row[1], reverse=True)],
                tool_calls=sum(session.tools.values()), edited_files=len(session.files_edited),
                checks={kind: {key: row[key] for key in ('runs', 'passed', 'failed', 'last')} for kind, row in session.checks.items()},
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
    project_names=labels([s.project for s in sessions],lang=lang)
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
        original=None if raw=='unknown' else raw
        projects.append(dict(value, id=_id('project',original), name=project_names.get(original,_project(original,lang))))
    options = sorted({(_id('project', s.project),project_names[s.project]) for s in sessions}, key=lambda row: row[1].casefold())
    # The meter is account-wide, so every session counts here, plus the Claude Code status line samples.
    windows = quota_outlook(sessions, now, sources.get('claude_quota', ()),sources.get('quota_source_groups'))
    # A plan is the account's: every session and every project, whatever the filters.
    plans = dict(rows=plan_rules.advise(sessions, sources.get('claude_quota', ()), now, sources.get('claude_plan'),
                                        sources.get('quota_source_groups'),sources=sources),
                 prices_as_of=plan_rules.PRICES_AS_OF, choices=list(plan_rules.CHOICES),
                 readable=not sources.get('claude_plan_error'))
    # Older logs lack reset timestamps, but their last meter sample is still account-wide.
    # Do not switch to a project's older percentage when a UI filter changes.
    account_rows = [replace(s, started=s.started or s.ended or epoch, ended=s.ended or s.started or epoch) for s in sessions]
    account_quota = summarize(account_rows, top=0)['quota']
    ambiguous={row['window_minutes'] for row in windows if row['agent']=='codex' and row['state']=='ambiguous'}
    for row in account_quota['latest']:
        mixed=(sources.get('quota_source_groups') or {}).get('codex',0)>1
        if row['window_minutes'] in ambiguous or mixed:
            reason=next((item.get('reason') for item in windows if item['agent']=='codex' and
                         item['window_minutes']==row['window_minutes']),'multiple_source_groups' if mixed else 'conflicting_meter_history')
            row.update(used_percent=None,state='ambiguous',reason=reason)
    skipped = sources.get('skipped', [])
    reason_keys={'MalformedRows':'malformed_file','InconsistentReasoning':'inconsistent_reasoning_file',
                 'ReadLimitExceeded':'read_limit_file'}
    reasons = Counter(say(lang,reason_keys.get(reason,'unreadable_file')) for _, reason in skipped)
    trust=quality(rows,sources,lang)
    outcome=git_outcome(rows,sources)
    reedit=subsequent_edits(sessions,rows,timestamp(sources.get('observed_at')) or now)
    observed=timestamp(sources.get('observed_at')) or now
    scoped=[s for s in sessions if (agent=='all' or s.agent==agent) and (project=='all' or _id('project',s.project)==project)]
    dated=dated_usage(scoped,observed-timedelta(days=days) if days else None,observed)
    # Same responses as the dated total, in UTC hours; the page groups them into local days.
    timeline=hourly_usage(scoped,observed-timedelta(days=days) if days else None,observed)
    archive=sources.get('archive') or {}
    boolean_fields=('enabled','available','retention_enabled','stored_files_known')
    archive_public={key:archive.get(key,False if key in boolean_fields else 0) for key in
                    (*boolean_fields,'stored_files','stored_bytes','max_bytes','max_files','max_days',
                     'archive_files','old_parser_files','unverified_files','evicted_files','errors')}
    archive_public['sessions']=sum(getattr(s,'source_state','live')!='live' for s in rows)
    verdicts=sources.get('verdicts') or {}
    public_sessions=sorted((session_view(s,lang,_git_for(s,sources),project_names,verdicts,sources.get('session_titles'),sources.get('title_status')) for s in rows),
                           key=lambda row:(row['total_tokens'],row['ended'] or ''),reverse=True)
    # Work subtotals round only after summing the original recorded price values.
    # The ordinary session row's display amount is already rounded to cents.
    recorded={session_code(session):session for session in rows}
    work_rows=[dict(row,api_usd=recorded[row['id']].api_usd,
                    api_priced_tokens=recorded[row['id']].api_priced_tokens) for row in public_sessions]
    work=work_rules.project(sources.get('work_items') or {},work_rows,
                            all_session_ids={session_code(session) for session in sessions})
    work['readable']=not sources.get('work_items_error',False)
    return dict(**provenance(archived=bool(archive_public['sessions'])),quality=trust,coverage=coverage_guidance(rows,sources),mode='local_agent_usage', new_model_calls=0, filters=dict(days=days, agent=agent, project=project),
                period=dict(since=_iso(since), mode='active_sessions_full_totals',
                            cross_period_sessions=sum(bool(s.started and since and s.started < since) for s in rows)),
                api_prices=dict(as_of=PRICES_AS_OF, tier='standard'),
                totals=summary['totals'], agents=summary['agents'], models=summary['models'], projects=projects,
                project_options=[dict(id=key, name=name) for key, name in options],
                sessions=public_sessions,
                identity=sources.get('identity') or dict(state='not_tracked',preserved=0,unverified=0,conflicts=0,limit_reached=False),
                quota=account_quota, claude_limit_events=summary['claude_limit_events'],
                outlook=windows, insights=find_insights(rows, windows, since, lang=lang,
                    usage_complete=trust['tokens_complete'] and trust['attribution_complete'])
                    + _git_insight(outcome, lang, trust['tokens_complete'] and trust['attribution_complete']) + edit_insight(reedit,lang)
                    + test_insight(rows, lang),
                checks=check_summary(rows),
                verdicts=dict(verdict_summary(public_sessions,verdicts),readable=not sources.get('verdicts_error')),
                work_items=work,
                plans=plans,
                git_outcome=outcome,reedit=reedit,dated_usage=dated,timeline=timeline,archive=archive_public,lang=lang,demo=bool(sources.get('demo')),
                quality_affected_sessions=sum(affected(s['quality']) for s in public_sessions),
                claude_statusline=bool(sources.get('claude_quota')),
                unknown_call_sessions=sum(not s.calls_complete or any(n.startswith('Older Codex log:') for n in s.notes) for s in rows),
                setup=dict(sessions=len(sessions), projects=len({s.project for s in sessions}),
                           agents=[dict(agent=key, sessions=sum(s.agent==key for s in sessions),
                                        files=sources.get('claude_files' if key=='claude-code' else 'codex_files',0))
                                   for key in AGENTS]),
                sources=dict(claude_files=sources.get('claude_files', 0), codex_files=sources.get('codex_files', 0),
                             unreadable=len(skipped), issues=[dict(reason=reason, files=count) for reason, count in reasons.items()]),
                privacy=say(lang, 'privacy'), scope=say(lang, 'scope'))


class UsageDashboard:
    def __init__(self, reader=None, git_reader=None, verdicts=None, survival=None, work_items=None, plan_choice=None, budgets=None, manage_sources=True):
        self.reader = reader or Rescan()
        self.manage_sources = manage_sources
        self.verdict_store = verdicts or Folder()
        self.work_store = work_items if work_items is not None else work_rules.Folder()
        self.plan_store = plan_choice if plan_choice is not None else plan_rules.Choice()
        self._demo_work_store = work_rules.Memory()
        self.survival_store = survival or Saved()
        self.git_reader = git_reader or read_repository
        self.lock = threading.RLock()
        self.sessions = []
        self.sources = {}
        self.state = 'idle'
        self.scanned_at = None
        self.error = None
        self.failure_code = None
        self.thread = None
        self.generation = 0
        self._pending = None
        self._cancel = None
        self._worker_running = False
        self._closed = False
        from .usage.budgets import Monitor, Store
        self.budgets = Monitor(budgets)
        self.demo_budgets = Monitor(Store(memory=True))
        from .usage.reconnections import Store as ReconnectionStore
        self.reconnections = (ReconnectionStore(self.work_store.base)
            if isinstance(self.work_store,work_rules.Folder) and isinstance(self.verdict_store,Folder)
            and not self.budgets.store.memory and self.work_store.base==self.verdict_store.base==self.budgets.store.base else None)
        self._reconnect_seen=None

    def _sync_reconnections(self):
        if self.reconnections is None or self.sources.get('demo'):return
        if self.reconnections.stamp()!=self._reconnect_seen:
            state=self.reconnections.state()
            self.sources.update(work_items=state['documents']['work-items.json'],work_items_error=False,
                verdicts={k:v['verdict'] for k,v in state['documents']['session-verdicts.json'].items()},verdicts_error=False)
            self._reconnect_seen=state['record']['id'] if state['record'] else None

    def _reconnect_selection(self,source,target):
        from .usage.reconnections import ReconnectError
        if self.state!='ready' or self.scanned_at is None or self._closed:raise ReconnectError('unavailable')
        if source==target:raise ReconnectError('invalid')
        old=next((s for s in self.sessions if session_code(s)==source),None)
        new=next((s for s in self.sessions if session_code(s)==target),None)
        if old and old.source_state!='archive':raise ReconnectError('source_live')
        if new is None or new.source_state not in ('live','mixed'):raise ReconnectError('target_missing')
        if old and old.agent!=new.agent:raise ReconnectError('agent_mismatch')
        return old,new

    def _reconnect_row(self,row,lang):
        if row is None:return None
        return dict(id=session_code(row),agent=row.agent,title=(self.sources.get('session_titles') or {}).get(session_code(row)),
                    project=labels([row.project],lang=lang).get(row.project,_project(row.project,lang)),
                    started=_iso(row.started),source_state=row.source_state,total_tokens=total(row.tokens))

    def reconnect_view(self,kind='sources',query='',offset=0,lang='en',source=None):
        from .usage import reconnections as rules
        with self.lock:
            if self.sources.get('demo'):return dict(ok=True,readable=True,demo=True,items=[],total=0,can_undo=False)
            if self.reconnections is None:return dict(ok=False,readable=False,reason='unavailable',items=[])
            try:
                self._sync_reconnections();state=self.reconnections.state()
                record=state['record'];refs=rules.inventory(state['documents'])
                by_code={session_code(row):row for row in self.sessions}
                items=[];needle=query.casefold()
                if kind=='sources':
                    for code,info in refs.items():
                        row=by_code.get(code)
                        if row is not None and row.source_state!='archive':continue
                        item=dict(self._reconnect_row(row,lang) or dict(id=code,agent=None,title=None,project=None,started=None,source_state='missing',total_tokens=None),**info)
                        if not needle or needle in ' '.join([code,item['title'] or '',item['project'] or '',*(w['title'] for w in info['works'])]).casefold():items.append(item)
                    items.sort(key=lambda row:row['id'])
                elif kind=='targets':
                    old=by_code.get(source)
                    for row in self.sessions:
                        if row.source_state not in ('live','mixed') or session_code(row)==source or old and old.agent!=row.agent:continue
                        item=self._reconnect_row(row,lang)
                        if not needle or needle in ' '.join([item['id'],item['agent'],item['title'] or '',item['project'] or '']).casefold():items.append(item)
                    items.sort(key=lambda row:(row['started'] or '',row['id']),reverse=True)
                elif kind!='state':raise rules.ReconnectError('invalid')
                latest=None if record is None else {k:record[k] for k in ('id','kind','at','source','target','summary')}
                return dict(ok=True,readable=True,demo=False,revision=state['revision'],items=items[offset:offset+20],
                    total=len(items),offset=offset,limit=20,latest=latest,can_undo=state['can_undo'],
                    ready=self.state=='ready' and self.scanned_at is not None,new_model_calls=0)
            except (OSError,ValueError,TypeError,UnicodeError):return dict(ok=False,readable=False,reason='unreadable',items=[])

    def reconnect_action(self,body,lang='en'):
        from .usage import reconnections as rules
        with self.lock:
            if self.sources.get('demo'):return dict(ok=False,reason='demo')
            if self.reconnections is None:return dict(ok=False,reason='unavailable')
            try:
                action=body['action'];state=self.reconnections.state()
                if action in ('undo','clear'):
                    self.reconnections.change(body['expected'],action=action)
                else:
                    source,target=body['source'],body['target'];old,new=self._reconnect_selection(source,target)
                    refs=rules.inventory(state['documents'])
                    if source not in refs:raise rules.ReconnectError('missing')
                    expected=rules.digest([state['revision'],self.generation,self.scanned_at,source,target])
                    if action=='preview':
                        old_info=refs[source];new_info=refs.get(target,dict(works=[],verdict=None,budget=None))
                        return dict(ok=True,expected=expected,source=dict(self._reconnect_row(old,lang) or dict(id=source,agent=None,title=None,project=None,source_state='missing'),**old_info),
                            target=dict(self._reconnect_row(new,lang),**new_info),snapshot_at=self.scanned_at,
                            verdict_conflict=bool(old_info['verdict'] and new_info['verdict'] and old_info['verdict']!=new_info['verdict']),
                            budget_conflict=bool(old_info['budget'] and new_info['budget']))
                    if action!='transfer' or body.get('confirmed') is not True:raise rules.ReconnectError('invalid')
                    if body['expected']!=expected:raise rules.ReconnectError('conflict')
                    self.reconnections.change(state['revision'],source,target,body.get('verdict_choice',''),body.get('budget_choice',''),
                        check=lambda:self._reconnect_selection(source,target))
                self._sync_reconnections()
                # Outside the filesystem lock: the monitor takes its own lock before reading preferences.
                self.budget_monitor().bind(self.sessions,demo=False)
                return dict(ok=True,**{k:v for k,v in self.reconnect_view('state',lang=lang).items() if k!='ok'})
            except rules.ReconnectError as error:return dict(ok=False,reason=error.reason)
            except (OSError,ValueError,TypeError,UnicodeError,KeyError):return dict(ok=False,reason='unreadable')

    def source_view(self):
        from .usage import sources
        with self.lock:
            return sources.view(demo=not self.manage_sources or bool(self.sources.get('demo')))

    def diagnostic_view(self, lang='en'):
        with self.lock:
            return diagnostics.view(self.sources, self.state, self.scanned_at, self.failure_code, lang)

    def source_action(self, body):
        from .usage import sources
        with self.lock:
            if not self.manage_sources or self.sources.get('demo'):
                return dict(ok=False, reason='demo')
        try:
            action = body['action']
            if action in ('check', 'add'):
                checked = sources.check(body['agent'], body['path'])
                if action == 'check':
                    return checked
                sources.Store().change(body['expected'], body['agent'], checked['roots'])
            else:
                sources.Store().change(body['expected'], remove=body['id'])
            with self.lock:
                # Stop watches on old bindings immediately; refresh publishes only selected sources.
                self.budgets.bind([])
                self.refresh(force=True)
            return dict(ok=True, state='scanning', **self.source_view())
        except sources.SourceError as error:
            return dict(ok=False, reason=error.reason)
        except (OSError, ValueError):
            return dict(ok=False, reason='unreadable')

    def budget_monitor(self):
        return self.demo_budgets if self.sources.get('demo') else self.budgets

    def budget_view(self):
        with self.lock:
            value = self.budget_monitor().view()
            titles = self.sources.get('session_titles') or {}
            for row in value['items']:
                row['title'] = titles.get(row['id'])  # live display only; never persisted with preferences
            return value

    def set_budget(self, identity, metric, limit, expected):
        try:
            return self.budget_monitor().configure(identity, metric, limit, expected)
        except (OSError, ValueError, UnicodeError):
            return dict(ok=False, reason='unreadable')

    def ack_budget(self, identity, revision, level):
        try:
            return self.budget_monitor().acknowledge(identity, revision, level)
        except (OSError, ValueError, UnicodeError):
            return dict(ok=False, reason='unreadable')

    def refresh(self, force=False):
        with self.lock:
            if self._closed:
                return dict(state='closed', started=False, new_model_calls=0)
            if self.state == 'scanning' and not force:
                return dict(state='scanning', started=False, new_model_calls=0)
            self.state, self.error = 'scanning', None
            self.generation += 1
            self._pending = self.generation
            if self._cancel is not None:
                self._cancel.set()
            if not self._worker_running:
                self._worker_running = True
                self.thread = threading.Thread(target=self._work, daemon=True)
                self.thread.start()
            return dict(state='scanning', started=True, new_model_calls=0)

    def _work(self):
        # At most one reader runs. Repeated forced refreshes replace one pending generation.
        while True:
            with self.lock:
                if self._closed or self._pending is None:
                    self._worker_running = False
                    return
                generation, self._pending = self._pending, None
                event = self._cancel = threading.Event()
            if self._closed:
                event.set()
            try:
                with cancellation(event):
                    self._scan(generation)
            except ScanCancelled:
                pass
            finally:
                with self.lock:
                    if self._cancel is event:
                        self._cancel = None

    def close(self, timeout=1.0):
        """Cancel future work; wait briefly, never promise to interrupt a blocked OS read."""
        # Set the stop flag before acquiring the snapshot lock: a slow report may hold it.
        self._closed = True
        self.budgets.close()
        self.demo_budgets.close()
        event = self._cancel
        if event is not None:
            event.set()
        deadline = time.monotonic() + max(0.0, timeout)
        if not self.lock.acquire(timeout=max(0.0, timeout)):
            return False
        try:
            self._pending = None
            self.generation += 1
            if self._cancel is not None:
                self._cancel.set()
            thread = self.thread
        finally:
            self.lock.release()
        if thread is not None and thread is not threading.current_thread():
            thread.join(max(0.0, deadline-time.monotonic()))
        return thread is None or not thread.is_alive()

    def clear_archive(self):
        from .usage.archive import clear_archive
        with self.lock:
            result = clear_archive()
            if not result.get('ok'):
                return dict(ok=False, cleared_files=0, errors=result.get('errors',1))
            self.generation += 1
            self.sessions, self.sources = [], {}
            self.scanned_at, self.error, self.state = None, None, 'idle'
            self.failure_code = None
            self.refresh(force=True)
            return dict(ok=True, cleared_files=result.get('cleared_files',0), errors=0, state='scanning')

    def set_retention(self,enabled):
        from .usage.archive import set_retention
        with self.lock:
            result=set_retention(enabled)
            if not result.get('ok'): return dict(ok=False,errors=result.get('errors',1))
            self._replace_after_settings()
            return dict(ok=True,retention_enabled=enabled,state='scanning')

    def reset_cache(self):
        from .usage.archive import reset_cache
        with self.lock:
            result=reset_cache()
            if not result.get('ok'): return result
            self._replace_after_settings()
            return dict(ok=True,cleared_files=result['cleared_files'],state='scanning')

    def _replace_after_settings(self):
        self.generation+=1
        self.sessions,self.sources=[],{}
        self.scanned_at,self.error,self.state=None,None,'idle'
        self.failure_code = None
        self.refresh(force=True)

    def _check_archive_generation(self):
        archive=self.sources.get('archive') or {}
        if archive.get('available',archive.get('enabled')) and self.scanned_at is not None:
            from .usage.archive import archive_generation
            current=archive_generation()
            if current is not None and current!=archive.get('scan_generation',archive.get('clear_generation')):
                self._replace_after_settings()

    def session(self,identity,lang='en'):
        """An already-read row outside the current filters; never opens a source."""
        with self.lock:
            try:self._sync_reconnections()
            except (OSError,ValueError):return None
            self._check_archive_generation()
            if self.scanned_at is not None:
                self.sources.update(self._read_work_items())
            project_names=labels([s.project for s in self.sessions],lang=lang)
            for session in self.sessions:
                if session_code(session)==identity:
                    return session_view(session,lang,_git_for(session,self.sources),project_names,self.sources.get('verdicts'),self.sources.get('session_titles'),self.sources.get('title_status'))
        return None

    def _read_plan_choice(self):
        try:
            return dict(claude_plan=self.plan_store.read(), claude_plan_error=False)
        except (OSError, ValueError, TypeError, UnicodeError):
            return dict(claude_plan=None, claude_plan_error=True)

    def set_plan(self, plan):
        """Save which Claude plan the user is on (or None); it changes only the plan advice."""
        with self.lock:
            if self._closed or self.scanned_at is None:
                return dict(ok=False, reason='unavailable')
            if self.sources.get('claude_plan_error'):
                return dict(ok=False, reason='unreadable')
            try:
                value = self.plan_store.save(plan)
            except (OSError, ValueError, TypeError, UnicodeError, KeyError):
                return dict(ok=False, reason='unsaved')
            self.sources = dict(self.sources, claude_plan=value, claude_plan_error=False)
            return dict(ok=True, plan=value)

    def _read_verdicts(self):
        try:
            return dict(verdicts=self.verdict_store.read(), verdicts_error=False)
        except (OSError, ValueError, TypeError, UnicodeError):
            return dict(verdicts={}, verdicts_error=True)

    def _work_items_store(self,demo=None):
        # Even a custom demo reader cannot fall through to a real on-disk store.
        demo=bool(self.sources.get('demo')) if demo is None else demo
        return self._demo_work_store if demo else self.work_store

    def _read_work_items(self,demo=None):
        try:
            return dict(work_items=self._work_items_store(demo).read(),work_items_error=False)
        except (OSError,ValueError,TypeError,UnicodeError):
            return dict(work_items={},work_items_error=True)

    def mutate_work_item(self,action,identity=None,title=None,session=None,details=None,expected_revision=None):
        """Change only explicit user work annotations; never rescan logs or infer an assignment."""
        with self.lock:
            if self._closed or self.scanned_at is None:
                return dict(ok=False,reason='unavailable')
            self.sources.update(self._read_work_items())
            if self.sources.get('work_items_error'):
                return dict(ok=False,reason='unreadable')
            if action=='link' or (action=='create' and session is not None):
                if not any(session_code(row)==session for row in self.sessions):
                    return dict(ok=False,reason='missing_session')
            try:
                extra=dict(details=details,expected_revision=expected_revision) if action=='describe' else {}
                value=self._work_items_store().mutate(action,identity=identity,title=title,session=session,**extra)
            except work_rules.WorkError as error:
                return dict(ok=False,reason=error.code if error.code in ('missing','limit','conflict') else 'invalid')
            except (OSError,ValueError,TypeError,UnicodeError,KeyError):
                return dict(ok=False,reason='unsaved')
            self.sources.update(work_items=value['items'],work_items_error=False)
            return dict(ok=True,id=value['id'])

    def _followup_view(self,identity,now):
        self._check_archive_generation()
        if self._closed or self.scanned_at is None or self.state=='scanning': return dict(ok=False,reason='unavailable')
        self.sources.update(self._read_work_items())
        if self.sources.get('work_items_error'): return dict(ok=False,reason='unreadable')
        item=self.sources['work_items'].get(identity)
        if item is None: return dict(ok=False,reason='missing')
        observed=timestamp(self.sources.get('observed_at')) or timestamp(self.scanned_at)
        if observed is None: return dict(ok=False,reason='unavailable')
        fresh=timedelta(0)<=now-observed<=followup_rules.MAX_AGE
        members=item['sessions'];scope=work_rules.membership_revision(item)
        preview=followup_rules.measure(self.sessions,members,observed-followup_rules.WINDOW,observed,observed,self.sources)
        preview_revision=followup_rules.digest([observed.isoformat(),scope,preview['fingerprint'],PARSER_VERSION])
        records=[]
        for record in item['followups']:
            entry=dict(record,revision=followup_rules.digest(record),comparison=followup_rules.comparison(record))
            anchor=followup_rules.date(record['baseline']['until']);end=anchor+followup_rules.WINDOW
            entry.update(due_at=end.isoformat(),ready=fresh and observed>=end,after_preview=None,review_revision=None)
            if record['status']=='open' and observed>=end:
                after=followup_rules.measure(self.sessions,members,anchor,end,observed,self.sources)
                prior=followup_rules.measure(self.sessions,members,anchor-followup_rules.WINDOW,anchor,observed,self.sources)
                entry['after_preview']=after
                entry['review_revision']=followup_rules.digest([entry['revision'],scope,observed.isoformat(),after['fingerprint'],prior['fingerprint'],PARSER_VERSION])
            records.append(entry)
        return dict(ok=True,fresh=fresh,preview=preview,preview_revision=preview_revision,items=records,
                    scope_revision=scope,observed_at=observed.isoformat(),new_model_calls=0)

    def followup_view(self,identity,now=None):
        with self.lock:
            try: return self._followup_view(identity,now or datetime.now(timezone.utc))
            except (ValueError,TypeError,OverflowError): return dict(ok=False,reason='unavailable')

    def mutate_followup(self,action,identity,expected_revision,change='',observation='',trigger='other',
                        record_id=None,context='unknown',note='',now=None):
        """Freeze source observations only on an explicit user action, never a model or provider call."""
        now=now or datetime.now(timezone.utc)
        with self.lock:
            view=self.followup_view(identity,now)
            if not view.get('ok'): return view
            item=self.sources['work_items'][identity]
            scope=view['scope_revision']
            try:
                if action=='start_followup':
                    if not view['fresh']: return dict(ok=False,reason='stale')
                    if expected_revision!=view['preview_revision']: return dict(ok=False,reason='conflict')
                    if trigger not in followup_rules.TRIGGERS: return dict(ok=False,reason='invalid')
                    payload=dict(id=secrets.token_hex(12),method=followup_rules.METHOD,parser_version=PARSER_VERSION,
                        created_at=int(now.timestamp()),trigger=trigger,observation=followup_rules.text(observation),
                        change=followup_rules.text(change,True),baseline=view['preview'],status='open',
                        review=None,cancelled_at=None,cancel_note='')
                    expected=scope
                else:
                    record=next((r for r in view['items'] if r['id']==record_id),None)
                    if record is None: return dict(ok=False,reason='missing')
                    if action=='review_followup':
                        if record['status']!='open': return dict(ok=False,reason='closed')
                        if not view['fresh']: return dict(ok=False,reason='stale')
                        if not record['ready']: return dict(ok=False,reason='early')
                        if expected_revision!=record['review_revision']: return dict(ok=False,reason='conflict')
                        if context not in followup_rules.CONTEXTS: return dict(ok=False,reason='invalid')
                        baseline=record['baseline'];anchor=followup_rules.date(baseline['until'])
                        current=followup_rules.measure(self.sessions,item['sessions'],anchor-followup_rules.WINDOW,anchor,
                                                       followup_rules.date(view['observed_at']),self.sources)
                        payload=dict(after=record['after_preview'],baseline_match=current['fingerprint']==baseline['fingerprint'],
                                     parser_match=record['parser_version']==PARSER_VERSION,context=context,note=followup_rules.text(note))
                        expected=record['revision']
                    elif action in ('cancel_followup','delete_followup'):
                        payload=followup_rules.text(note);expected=expected_revision
                    else: return dict(ok=False,reason='invalid')
                saved=self._work_items_store().followup(identity,action,record_id,payload,expected,scope)
            except work_rules.WorkError as error:
                return dict(ok=False,reason=error.code if error.code in ('missing','limit','conflict','active','closed') else 'invalid')
            except (ValueError,TypeError,OverflowError): return dict(ok=False,reason='invalid')
            except (OSError,UnicodeError): return dict(ok=False,reason='unsaved')
            self.sources.update(work_items=saved['items'],work_items_error=False)
            return dict(ok=True,id=identity,followup=saved['followup'])

    def set_verdict(self, identity, verdict):
        """Save the user's verdict for a session of the current snapshot; never one Roodof has not shown."""
        with self.lock:
            if not any(session_code(session) == identity for session in self.sessions):
                return dict(ok=False, reason='missing')
            if self.sources.get('verdicts_error'):
                return dict(ok=False, reason='unreadable')
            try:
                values = self.verdict_store.save(identity, verdict)
            except (OSError, ValueError, TypeError, UnicodeError, KeyError):
                return dict(ok=False, reason='unsaved')
            self.sources = dict(self.sources, verdicts=values, verdicts_error=False)
            return dict(ok=True, id=identity, verdict=verdict)

    def _scan(self, generation=None):
        if generation is None:
            with self.lock:
                generation = self.generation
        stage = 'logs'
        try:
            checkpoint()
            sessions, sources = self.reader()
            checkpoint()
            sources = dict(sources)
            stage = 'titles'
            if not sources.get('demo'):
                from .usage.session_titles import inspect as inspect_titles
                sources['session_titles'], sources['title_status'] = inspect_titles(sessions)
            else:
                sources['title_status'] = {session_code(s):dict(state='fallback', reason='demo') for s in sessions}
            if (sources.get('archive') or {}).get('stale_snapshot'):
                with self.lock:
                    if generation==self.generation: self._replace_after_settings()
                return
            stage = 'git'
            sources['git_links'] = git_links(sessions)
            checkpoint()
            folders = {path for linked in sources['git_links'].values() for path in linked}
            sources['git_activity'] = {}
            for path in folders:
                checkpoint()
                sources['git_activity'][path] = self.git_reader(path)
            windows = {}
            for session in sessions:
                checkpoint()
                if session.started and session.ended:
                    for path in sources['git_links'][_link_key(session)]:
                        windows.setdefault(path, []).append((session.started, session.ended))
            for path, snapshot in sources['git_activity'].items():
                checkpoint()
                check_branches(snapshot, windows.get(path, ()))
                checkpoint()
                check_survival(snapshot, self.survival_store)
            # Validate the projection before publishing a replacement snapshot.
            stage = 'projection'
            checkpoint()
            project_view(sessions, sources, days=0)
            with self.lock:
                if generation != self.generation or self._closed:
                    return
                # Read under the lock so a verdict saved during the scan is not replaced by an older copy.
                sources.update(self._read_verdicts())
                sources.update(self._read_plan_choice())
                sources.update(self._read_work_items(demo=bool(sources.get('demo'))))
                self.sessions, self.sources = sessions, sources
                self.budget_monitor().bind(sessions, demo=bool(sources.get('demo')))
                self.scanned_at = datetime.now(timezone.utc).isoformat()
                self.state, self.error = 'ready', None
                self.failure_code = None
        except ScanCancelled:
            raise
        except ReadLimitExceeded:
            with self.lock:
                if generation != self.generation or self._closed:
                    return
                self.state, self.error, self.failure_code = 'error', 'error.scan', 'scan_limit'
        except SourceError:
            with self.lock:
                if generation != self.generation or self._closed:
                    return
                self.state, self.error = 'error', 'error.log_sources'
                self.failure_code = 'source_preferences'
        except IdentityError:
            with self.lock:
                if generation != self.generation or self._closed:
                    return
                self.state, self.error = 'error', 'error.session_identity'
                self.failure_code = 'identity_preferences'
        except Exception:
            # Reader errors may contain transcript excerpts or private paths.
            # Keep an earlier usable snapshot; never send a raw exception to UI.
            with self.lock:
                if generation != self.generation or self._closed:
                    return
                self.state, self.error = 'error', 'error.scan'
                self.failure_code = stage + '_failed'

    def view(self, days=30, agent='all', project='all', lang='en'):
        with self.lock:
            try:self._sync_reconnections()
            except (OSError,ValueError):self.sources.update(work_items_error=True,verdicts_error=True)
            self._check_archive_generation()
            if self.scanned_at is not None:
                self.sources.update(self._read_work_items())
            value = project_view(self.sessions, self.sources, days, agent, project, lang=lang)
            value.update(state=self.state, scanned_at=self.scanned_at, error=self.error and say(value['lang'], self.error),
                         has_snapshot=self.scanned_at is not None, diagnostics=self.diagnostic_view(value['lang']))
            return value
