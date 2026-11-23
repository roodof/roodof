"""Hourly buckets of the dated responses that period_usage counts, for the usage-over-time chart.

Buckets are UTC hours; the page groups them into the viewer's local days. Eligibility and the
interval rules are period_usage's own, so the chart always adds up to the dated total shown
beside it. Whole-session totals are never spread over time, and nothing else is read.
"""
from collections import Counter, defaultdict
from datetime import timedelta

from .period_usage import _reason, _utc
from .records import ADDED


def _distinct_sessions(sessions):
    selected = {}
    for session in sessions:
        selected.setdefault((session.agent, session.source, session.session_id), session)
    return selected.values()


def hourly(sessions, since, cutoff):
    """Rows of [UTC hour ISO, agent, total tokens, response calls] in time order."""
    cutoff = _utc(cutoff)
    since = _utc(since) if since is not None else None
    if cutoff is None or since is not None and since > cutoff:
        raise ValueError('timeline requires an aware, ordered interval')
    buckets = defaultdict(lambda: [0, 0])
    for session in _distinct_sessions(sessions):
        if _reason(session) is not None:
            continue
        agent = session.agent if session.agent in ('claude-code', 'codex') else 'unknown'
        for event in getattr(session, '_usage_events', ()):
            at = _utc(event['at'])
            first = _utc(event.get('first', event['at']))
            # The same exclusions as the dated total: undated, straddling the start, future, or before it.
            if at is None or first is None or since is not None and first < since <= at:
                continue
            if at > cutoff or since is not None and at < since:
                continue
            row = buckets[(at.replace(minute=0, second=0, microsecond=0), agent)]
            row[0] += sum(event['tokens'].get(name) or 0 for name in ADDED)  # records.total, tolerant of absent fields
            row[1] += 1
    return dict(unit='hour_utc',
                rows=[[hour.isoformat(), agent, tokens, calls]
                      for (hour, agent), (tokens, calls) in sorted(buckets.items())])


def projects_for_day(sessions, start, end, since, cutoff):
    """A local calendar day expressed as exact UTC bounds, end exclusive."""
    start, end, cutoff = _utc(start), _utc(end), _utc(cutoff)
    if start is None or end is None or cutoff is None or not timedelta(0) < end - start <= timedelta(days=2):
        raise ValueError('invalid calendar day interval')
    projects = Counter()
    boundary_calls = 0
    for session in _distinct_sessions(sessions):
        if _reason(session) is not None:
            continue
        for event in getattr(session, '_usage_events', ()):
            at = _utc(event['at'])
            first = _utc(event.get('first', event['at']))
            if at is None or first is None or at > cutoff or (since is not None and first < since):
                continue
            if first >= end or at < start:
                continue
            if first < start or at >= end:
                boundary_calls += 1
                continue
            projects[session.project] += sum(event['tokens'].get(key) or 0 for key in ADDED)
    return projects, boundary_calls
