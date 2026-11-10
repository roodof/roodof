"""Where a subscription meter is heading: the current window, its pace, and whether it fills first.

Codex logs its meter in every rollout. Claude Code logs none; its samples come from Roodof's status line
(statusline.py), when the user has turned it on.

The meter is account-wide and moves only while agents work, so the pace depends on the window:
- short windows (5 hours): the average rise since the first sample of the current window, i.e. the pace of
  the work going on now;
- day-long or longer windows (weekly): the average rise per calendar day over the last 14 days, across
  resets, because people do not work around the clock.
A forecast assumes that pace continues.
Contradictory meter histories are withheld. This detects inconsistent evidence,
not provider account identity; compatible samples alone cannot prove one account.
Codex logs its plan with every sample: after a plan change (another plan or another
account) only the samples since the latest change describe the current limit.
"""
from datetime import datetime, timedelta

from .records import percentage

MIN_SPAN = timedelta(minutes=20)
SAME_RESET = timedelta(minutes=5)
HISTORY = timedelta(days=14)
MIN_HISTORY = timedelta(days=2)
SHORT_MAX_AGE = timedelta(minutes=30)
LONG_MAX_AGE = timedelta(hours=24)
LARGE_DROP = 25  # percentage points within one window; set after measuring real single-account meters (max 11)


def _rise(samples):
    return sum(max(0.0, later[2] - earlier[2]) for earlier, later in zip(samples, samples[1:]))


def _consistent_history(samples):
    """Discard a contradictory expired episode only after a later reset is observed.

    A single real meter is not monotonic: in one user's Codex logs the 5-hour
    level fell by 1 point 622 times and by at most 11 within a window, and the
    provider sometimes restarted a window early (a later reset, a lower level).
    Neither is a contradiction. Within a still-active window these are: a reset
    moving back to an earlier time, a fall of more than LARGE_DROP points, or
    different readings at exactly the same instant. A known elapsed reset
    permits a lower level in the next window. Old contradictions must not poison
    a newly observed window, but none of their artificial rises enter its forecast.
    """
    first, previous, uncertain_until = 0, None, None
    for index, sample in enumerate(samples):
        if uncertain_until is not None:
            if sample[0] >= uncertain_until:
                first, previous, uncertain_until = index, None, None
            else:
                uncertain_until = max(uncertain_until, sample[3])
                continue
        if previous is not None and sample[0] < previous[3]:
            moved = sample[3] - previous[3]
            if (moved < -SAME_RESET
                    or abs(moved) <= SAME_RESET and previous[2] - sample[2] > LARGE_DROP
                    or sample[0] == previous[0] and (sample[2] != previous[2] or abs(moved) > SAME_RESET)):
                uncertain_until = max(previous[3], sample[3])
        previous = sample
    return samples[first:], uncertain_until is not None


def plan_boundary(samples):
    """When the logged plan last changed among these samples (a fifth item, as Codex logs it), or None.
    Percentages from before it measure a different limit: another plan or another account."""
    boundary, previous = None, None
    for sample in sorted((s for s in samples if len(s) > 4 and isinstance(s[4], str) and s[4]
                          and isinstance(s[0], datetime) and s[0].tzinfo is not None), key=lambda s: (s[0], s[4])):
        if previous is not None and sample[4] != previous:
            boundary = sample[0]
        previous = sample[4]
    return boundary


def outlook(sessions, now, claude=(), scopes=None):
    """One row per agent and window length: last used percent, reset time, pace and state. `claude` holds the
    status line samples (time, window minutes, used percent, resets_at).

    States: full, fills_before_reset (with full_at), lasts_until_reset, no_pace (too little history or no
    rise), reset (the window ended after the last record), ambiguous (conflicting
    meter histories; neither a current level nor a forecast can be established)."""
    windows, cut = {}, set()
    sources = [(session.agent, session.quota) for session in sessions] + [('claude-code', claude)]
    boundaries = {}
    for agent, quota in sources:
        boundaries.setdefault(agent, []).extend(sample for sample in quota if len(sample) > 4 and isinstance(sample[0], datetime)
                                                and sample[0].tzinfo is not None and sample[0] <= now)
    boundaries = {agent: plan_boundary(samples) for agent, samples in boundaries.items()}
    for agent, quota in sources:
        for sample in quota:
            if (len(sample) > 3 and isinstance(sample[0], datetime) and sample[0].tzinfo is not None
                    and isinstance(sample[3], datetime) and sample[3].tzinfo is not None
                    and type(sample[1]) is int and sample[1] > 0 and percentage(sample[2]) is not None
                    and sample[0] <= now):
                if boundaries.get(agent) and sample[0] < boundaries[agent]:
                    cut.add((agent, sample[1]))
                    continue
                # Different files and copied sessions often repeat one account
                # sample. They supply no additional rise or ordering evidence.
                windows.setdefault((agent, sample[1]), set()).add(
                    (sample[0], sample[1], percentage(sample[2]), sample[3]))
    rows = []
    for (agent, minutes), samples in sorted(windows.items()):
        samples = sorted(samples, key=lambda sample: (sample[0], sample[3], sample[2]))
        if minutes >= 24 * 60:
            samples = [sample for sample in samples if sample[0] >= samples[-1][0] - HISTORY]
        samples, ambiguous = _consistent_history(samples)
        at, _, used, resets = samples[-1]
        max_age = SHORT_MAX_AGE if minutes < 24 * 60 else LONG_MAX_AGE
        row = dict(agent=agent, window_minutes=minutes, used_percent=used, at=at.isoformat(), resets_at=resets.isoformat(),
                   max_age_seconds=max_age.total_seconds())
        if (agent, minutes) in cut:
            row['plan_changed_at'] = boundaries[agent].isoformat()
        if (scopes or {}).get(agent,0)>1:
            row.update(state='ambiguous',used_percent=None,resets_at=None,reason='multiple_source_groups')
            rows.append(row)
            continue
        if ambiguous:
            row.update(state='ambiguous', used_percent=None, resets_at=None,
                       reason='conflicting_meter_history')
            rows.append(row)
            continue
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
