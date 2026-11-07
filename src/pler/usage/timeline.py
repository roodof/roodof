"""Hourly buckets of the dated responses that period_usage counts, for the usage-over-time chart.

Buckets are UTC hours; the page groups them into the viewer's local days. Eligibility and the
interval rules are period_usage's own, so the chart always adds up to the dated total shown
beside it. Whole-session totals are never spread over time, and nothing else is read.
"""
from collections import defaultdict

from .period_usage import _reason, _utc
from .records import ADDED


def hourly(sessions, since, cutoff):
    """Rows of [UTC hour ISO, agent, total tokens, response calls] in time order."""
    cutoff = _utc(cutoff)
    since = _utc(since) if since is not None else None
    if cutoff is None or since is not None and since > cutoff:
        raise ValueError('timeline requires an aware, ordered interval')
    selected = {}
    for session in sessions:
        selected.setdefault((session.agent, session.source, session.session_id), session)
    buckets = defaultdict(lambda: [0, 0])
    for session in selected.values():
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
