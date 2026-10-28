"""Totals that answer: how much, where, with which model, and how the subscription meter moved."""
from collections import defaultdict
from datetime import datetime, timezone

from .records import add_tokens, empty_tokens, total


def _bucket():
    return dict(sessions=0, calls=0, prompts=0, errors=0, aborted=0, tokens=empty_tokens())


def _add(bucket, session):
    bucket['sessions'] += 1
    for name in ('calls', 'prompts', 'errors', 'aborted'):
        bucket[name] += getattr(session, name)
    add_tokens(bucket['tokens'], session.tokens)


def _finish(bucket):
    tokens = bucket['tokens']
    inputs = tokens['input'] + tokens['cache_read'] + tokens['cache_write']
    return dict(bucket, total_tokens=total(tokens), cache_read_share=tokens['cache_read'] / inputs if inputs else None)


def quota_burn(session):
    """Per window: the sum of increases of the used percent during the session; a reset is not a decrease.
    The meter is account-wide, so concurrent sessions are included."""
    windows = defaultdict(list)
    for sample in sorted(session.quota, key=lambda sample: sample[0]):
        windows[sample[1]].append(sample[2])
    return {window: round(sum(max(0.0, later - earlier) for earlier, later in zip(values, values[1:])), 2)
            for window, values in windows.items()}


def _local_day(moment):
    return moment.astimezone().date().isoformat() if moment else 'unknown'


def summarize(sessions, since=None, top=5):
    rows = [s for s in sessions if since is None or (s.ended is not None and s.ended >= since)]
    agents, projects, days = defaultdict(_bucket), defaultdict(_bucket), defaultdict(_bucket)
    models = defaultdict(lambda: dict(calls=0, total_tokens=0))
    for session in rows:
        _add(agents[session.agent], session)
        _add(projects[session.project or 'unknown'], session)
        _add(days[_local_day(session.started)], session)
        for model, tokens in session.model_tokens.items():
            models[(session.agent, model)]['total_tokens'] += tokens
            models[(session.agent, model)]['calls'] += session.models.get(model, 0)
    samples = sorted((sample for s in rows for sample in s.quota), key=lambda sample: sample[0])
    latest = {}
    for sample in samples:
        latest[sample[1]] = dict(at=sample[0].isoformat(), window_minutes=sample[1], used_percent=sample[2])
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    plans = [s.quota_plan for s in sorted(rows, key=lambda s: s.ended or s.started or epoch) if s.quota_plan]
    largest = sorted(rows, key=lambda s: total(s.tokens), reverse=True)[:top]
    starts = [s.started for s in rows if s.started]
    ends = [s.ended for s in rows if s.ended]
    return dict(
        period=dict(first=min(starts).isoformat() if starts else None, last=max(ends).isoformat() if ends else None,
                    since=since.isoformat() if since else None),
        totals=_finish(_bucket() if not rows else _merge(agents.values())),
        agents={name: _finish(bucket) for name, bucket in sorted(agents.items())},
        projects=sorted(({'project': name, **_finish(bucket)} for name, bucket in projects.items()),
                        key=lambda row: row['total_tokens'], reverse=True),
        days=[{'day': name, **_finish(bucket)} for name, bucket in sorted(days.items())],
        models=sorted(({'agent': agent, 'model': model, **value} for (agent, model), value in models.items()
                       if value['total_tokens'] or value['calls']),
                      key=lambda row: row['total_tokens'], reverse=True),
        largest_sessions=[dict(agent=s.agent, project=s.project, started=s.started.isoformat() if s.started else None,
                               total_tokens=total(s.tokens), calls=s.calls, prompts=s.prompts,
                               quota_burn_percent=quota_burn(s) or None) for s in largest],
        quota=dict(plan=plans[-1] if plans else None, latest=sorted(latest.values(), key=lambda w: w['window_minutes'] or 0),
                   agent='codex' if latest else None),
        claude_limit_events=_events(rows),
        reported_cost_usd=_reported_cost(rows),
        model_calls=0,
    )


def _merge(buckets):
    merged = _bucket()
    for bucket in buckets:
        for name in ('sessions', 'calls', 'prompts', 'errors', 'aborted'):
            merged[name] += bucket[name]
        add_tokens(merged['tokens'], bucket['tokens'])
    return merged


def _events(rows):
    counts = defaultdict(int)
    for session in rows:
        for status, count in session.quota_events.items():
            counts[status] += count
    return dict(counts)


def _reported_cost(rows):
    known = [s.reported_cost_usd for s in rows if s.reported_cost_usd is not None]
    return dict(sessions_with_figure=len(known), usd=round(sum(known), 2) if known else None,
                note="Claude Code's own running figure; it covers only the latest app process of a session, "
                     "so it is a partial API-price equivalent, not a session total or a bill.")
