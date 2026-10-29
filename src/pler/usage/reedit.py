"""Preregistered subsequent-edit observations from already-read session metadata.

No filesystem, Git or source-log access occurs here. Targets are logged edit
intentions; session tokens do not measure the cost or quality of an edit.
"""
from bisect import bisect_right
from collections import Counter
from datetime import datetime, timezone
import hashlib
import statistics

from .edit_paths import canonical_target
from .records import total
from ..i18n import say


WINDOW_SECONDS = 7 * 24 * 60 * 60
DISPLAY_LIMIT = 5
EXCLUSION_REASONS = ('archive_old_parser', 'archive_unverified', 'uncertain_history',
                     'invalid_time', 'missing_targets')
AGENTS = ('claude-code', 'codex')


def insight(observation, lang='en'):
    """Shared localized observation for the page and terminal, including absent coverage."""
    excluded=sum(observation['excluded'].values())
    detail=(say(lang,'insight.reedit.detail',matched=observation['matched_sessions'],
                eligible=observation['eligible_sessions'],pending=observation['pending_sessions'])
            if observation['eligible_sessions'] else say(lang,'insight.reedit.none'))
    detail+=' '+say(lang,'insight.reedit.coverage',excluded=excluded)+' '+say(lang,'insight.reedit.limits')
    return [dict(kind='subsequent_edit',level='info',title=say(lang,'insight.reedit.title'),
                 detail=detail,evidence=observation)]


def _public_id(session):
    value = session.agent + ':' + session.source + '\0' + session.session_id
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:24]


def _utc(value):
    if not isinstance(value, datetime):
        return None
    try:
        return value.astimezone(timezone.utc) if value.utcoffset() is not None else None
    except (OverflowError, TypeError, ValueError):
        return None


class _Entry:
    """Private calculation values. Only explicit projections can leave analyze()."""
    def __init__(self, session, identity, started, ended, targets, group):
        self.identity = identity
        self.started, self.ended = started, ended
        self.targets, self.group = targets, group
        self.agent = session.agent if session.agent in AGENTS else 'unknown'
        self.tokens = total(session.tokens)
        self.usage_complete = bool(session.tokens_complete and session.attribution_complete)


def _prepare(session, cutoff):
    issues = getattr(session, 'issues', ())
    if getattr(session, 'archive_old_parser', False) or 'archive_old_parser' in issues:
        return None, 'archive_old_parser'
    archived = getattr(session, 'source_state', 'live') in ('archive', 'mixed') or getattr(session, 'archive_files', 0)
    if (getattr(session, 'archive_unverified', False) or 'archive_unverified' in issues
            or archived and not getattr(session, 'source_deleted', False)):
        return None, 'archive_unverified'
    group = getattr(session, '_history_group', None)
    try:
        group_valid = group is not None and bool(group)
        hash(group)
    except (TypeError, ValueError):
        group_valid = False
    if getattr(session, '_history_uncertain', False) or not group_valid:
        return None, 'uncertain_history'
    started, ended = _utc(session.started), _utc(session.ended)
    if started is None or ended is None or started > ended or ended > cutoff:
        return None, 'invalid_time'
    # Reader integration already resolved relative targets at their row cwd.
    # Never try the final project folder here, which may describe a later row.
    targets = {target for target in (canonical_target(value) for value in session.files_edited) if target is not None}
    if not targets:
        return None, 'missing_targets'
    return _Entry(session, _public_id(session), started, ended, targets, group), None


class _TargetIndex:
    """Sorted starts and one jump over a consecutive run of the same history.

    A common file in thousands of related sessions therefore does not require
    scanning those sessions again for each origin.
    """
    def __init__(self, entries):
        self.entries = sorted(entries, key=lambda entry: (entry.started, entry.identity))
        self.starts = [entry.started for entry in self.entries]
        size = len(self.entries)
        self.next_group = [size] * size
        for index in range(size - 2, -1, -1):
            self.next_group[index] = (self.next_group[index + 1]
                                      if self.entries[index].group == self.entries[index + 1].group else index + 1)

    def first_after(self, ended, group):
        index = bisect_right(self.starts, ended)
        if index < len(self.entries) and self.entries[index].group == group:
            index = self.next_group[index]
        return self.entries[index] if index < len(self.entries) else None


def _unique(sessions):
    """Inputs are reconciled logical sessions; repeated references count once."""
    found = {}
    for session in sessions:
        found.setdefault(_public_id(session), session)
    return found


def _empty_counts():
    return dict(eligible_sessions=0, matched_sessions=0, pending_sessions=0, observed_unmatched_sessions=0,
                eligible_origin_tokens=0, matched_origin_tokens=0,
                eligible_usage_complete=True, matched_usage_complete=True)


def _add_origin(counts, origin, later, cutoff):
    counts['eligible_sessions'] += 1
    counts['eligible_origin_tokens'] += origin.tokens
    counts['eligible_usage_complete'] &= origin.usage_complete
    if later is not None:
        counts['matched_sessions'] += 1
        counts['matched_origin_tokens'] += origin.tokens
        counts['matched_usage_complete'] &= origin.usage_complete
    elif (cutoff - origin.ended).total_seconds() < WINDOW_SECONDS:
        counts['pending_sessions'] += 1
    else:
        counts['observed_unmatched_sessions'] += 1


def _match(origin, later):
    return dict(origin_id=origin.identity, later_id=later.identity,
                origin_agent=origin.agent, later_agent=later.agent,
                gap_seconds=(later.started - origin.ended).total_seconds(),
                matching_targets=len(origin.targets & later.targets),
                origin_tokens=origin.tokens, later_tokens=later.tokens,
                origin_usage_complete=origin.usage_complete, later_usage_complete=later.usage_complete)


def analyze(all_sessions, origin_rows, cutoff):
    """Return only safe aggregate values and the five fastest observed origins.

    all_sessions is the reconciled timeline from all explicitly selected roots;
    origin_rows is its period/agent/project selection. The scan cutoff must be an
    aware datetime. Reader-created _history_group and _history_uncertain values
    describe independence; absent evidence is excluded instead of invented.
    """
    cutoff = _utc(cutoff)
    if cutoff is None:
        raise ValueError('subsequent-edit cutoff requires an aware datetime')
    timeline, origins = _unique(all_sessions), _unique(origin_rows)
    prepared, reasons = {}, {}
    for identity, session in timeline.items():
        prepared[identity], reasons[identity] = _prepare(session, cutoff)
    # Accept a standalone selected origin conservatively, even when a caller
    # omitted it from the evidence list; it supplies no extra later evidence.
    for identity, session in origins.items():
        if identity not in prepared:
            prepared[identity], reasons[identity] = _prepare(session, cutoff)
    by_target = {}
    for identity in timeline:
        entry = prepared[identity]
        if entry is not None:
            for target in entry.targets:
                by_target.setdefault(target, []).append(entry)
    indexes = {target: _TargetIndex(entries) for target, entries in by_target.items()}
    counts, per_agent, matches = _empty_counts(), {}, []
    for identity in origins:
        origin = prepared[identity]
        if origin is None:
            continue
        later = None
        for target in origin.targets:
            index = indexes.get(target)
            candidate = index.first_after(origin.ended, origin.group) if index is not None else None
            if candidate is None or (candidate.started - origin.ended).total_seconds() > WINDOW_SECONDS:
                continue
            if later is None or (candidate.started, candidate.identity) < (later.started, later.identity):
                later = candidate
        _add_origin(counts, origin, later, cutoff)
        agent_counts = per_agent.setdefault(origin.agent, _empty_counts())
        _add_origin(agent_counts, origin, later, cutoff)
        if later is not None:
            matches.append(_match(origin, later))
    matches.sort(key=lambda match: (match['gap_seconds'], match['origin_id'], match['later_id']))
    gaps = [match['gap_seconds'] for match in matches]
    excluded = Counter(reasons[identity] for identity in origins if reasons[identity] is not None)
    timeline_excluded = Counter(reasons[identity] for identity in timeline if reasons[identity] is not None)
    return dict(window_seconds=WINDOW_SECONDS, cutoff=cutoff.isoformat(), evidence_scope='selected_roots_all_sessions',
                origin_sessions=len(origins), **counts,
                excluded={reason: excluded[reason] for reason in EXCLUSION_REASONS},
                timeline_sessions=len(timeline), timeline_eligible_sessions=sum(prepared[key] is not None for key in timeline),
                timeline_excluded={reason: timeline_excluded[reason] for reason in EXCLUSION_REASONS},
                gap_seconds=dict(minimum=min(gaps) if gaps else None, median=statistics.median(gaps) if gaps else None,
                                 maximum=max(gaps) if gaps else None),
                agents=[dict(agent=agent, **per_agent[agent]) for agent in sorted(per_agent)],
                matches=matches[:DISPLAY_LIMIT])
