"""Where a subscription meter is heading: the current window, its pace, and whether it fills first.

Codex logs its meter in every rollout. Claude Code logs none; its samples come from PLER's status line
(statusline.py), when the user has turned it on.

The meter is account-wide and moves only while agents work, so the pace depends on the window:
- short windows (5 hours): the average rise since the first sample of the current window, i.e. the pace of
  the work going on now;
- day-long or longer windows (weekly): the average rise per calendar day over the last 14 days, across
  resets, because people do not work around the clock.
A forecast assumes that pace continues.
"""
from datetime import datetime, timedelta

from .records import percentage

MIN_SPAN = timedelta(minutes=20)
SAME_RESET = timedelta(minutes=5)
HISTORY = timedelta(days=14)
MIN_HISTORY = timedelta(days=2)
SHORT_MAX_AGE = timedelta(minutes=30)
LONG_MAX_AGE = timedelta(hours=24)


def _rise(samples):
    return sum(max(0.0, later[2] - earlier[2]) for earlier, later in zip(samples, samples[1:]))


def outlook(sessions, now, claude=()):
    """One row per agent and window length: last used percent, reset time, pace and state. `claude` holds the
    status line samples (time, window minutes, used percent, resets_at).

    States: full, fills_before_reset (with full_at), lasts_until_reset, no_pace (too little history or no
    rise), reset (the window ended after the last record, so the current percentage is unknown)."""
    windows = {}
    sources = [(session.agent, session.quota) for session in sessions] + [('claude-code', claude)]
    for agent, quota in sources:
        for sample in quota:
            if (len(sample) > 3 and isinstance(sample[0], datetime) and sample[0].tzinfo is not None
                    and isinstance(sample[3], datetime) and sample[3].tzinfo is not None
                    and type(sample[1]) is int and sample[1] > 0 and percentage(sample[2]) is not None
                    and sample[0] <= now):
                windows.setdefault((agent, sample[1]), []).append(sample)
    rows = []
    for (agent, minutes), samples in sorted(windows.items()):
        samples.sort(key=lambda sample: sample[0])
        at, _, used, resets = samples[-1]
        max_age = SHORT_MAX_AGE if minutes < 24 * 60 else LONG_MAX_AGE
        row = dict(agent=agent, window_minutes=minutes, used_percent=used, at=at.isoformat(), resets_at=resets.isoformat(),
                   max_age_seconds=max_age.total_seconds())
        if resets <= now:
            row['state'] = 'reset'
            rows.append(row)
            continue
        if now - at > max_age:
            row['state'] = 'stale'
            rows.append(row)
            continue
        if used >= 100:
            row['state'] = 'full'
            rows.append(row)
            continue
        if minutes < 24 * 60:
            current = [s for s in samples if abs(s[3] - resets) <= SAME_RESET]
            span, rise = at - current[0][0], _rise(current)
            per_second = rise / span.total_seconds() if span >= MIN_SPAN and rise > 0 else None
            if per_second:
                row['percent_per_hour'] = round(per_second * 3600, 2)
        else:
            recent = [s for s in samples if s[0] >= at - HISTORY]
            span, rise = at - recent[0][0], _rise(recent)
            per_second = rise / span.total_seconds() if span >= MIN_HISTORY and rise > 0 else None
            if per_second:
                row['percent_per_day'] = round(per_second * 86400, 2)
                row['history_days'] = round(span.total_seconds() / 86400, 1)
        if not per_second:
            row['state'] = 'no_pace'
        else:
            full_at = at + timedelta(seconds=(100 - used) / per_second)
            if full_at <= now:
                row['state'] = 'stale'
            else:
                row.update(full_at=full_at.isoformat(), state='fills_before_reset' if full_at < resets else 'lasts_until_reset')
        rows.append(row)
    return rows
