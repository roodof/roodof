"""A few plain observations from the user's own records, each with the numbers behind it.

They describe what the logs show and suggest what to try; none of them is a controlled comparison. Rules:
- quota: a Codex or Claude Code window is full, or fills before it resets at the current pace;
- long sessions: in long sessions each model call costs several times more than in short ones (the
  context is read again at every step); shown only with enough sessions on both sides;
- concentration: one session holds a large share of the period;
- limit hits: Claude Code refused requests at its limit;
- interrupted work: many failed or interrupted turns.
Titles and details are written in the requested language (i18n.py).
"""
from datetime import datetime
import statistics

from ..i18n import big, count, decimal, moment, say, window
from .records import total

AGENTS = {'claude-code': 'Claude Code', 'codex': 'Codex'}
SHORT, LONG = 50, 100   # model calls per session


def _time(iso, lang):
    return moment(datetime.fromisoformat(iso), lang, year=False)


def _quota(outlook, lang):
    found = []
    for row in outlook:
        name = say(lang, 'insight.quota_name', agent=AGENTS.get(row.get('agent'), 'Codex'), window=window(row['window_minutes'], lang))
        name = name[0].upper() + name[1:]
        if row['state'] == 'full':
            found.append(dict(kind='quota', level='warn', title=say(lang, 'insight.full.title', name=name),
                              detail=say(lang, 'insight.full.detail', at=_time(row['at'], lang), resets=_time(row['resets_at'], lang)),
                              evidence=row))
        elif row['state'] == 'fills_before_reset':
            pace = (say(lang, 'insight.pace.hour', rate=decimal(row['percent_per_hour'], lang)) if 'percent_per_hour' in row
                    else say(lang, 'insight.pace.day', days=round(row['history_days']), rate=decimal(row['percent_per_day'], lang)))
            found.append(dict(kind='quota', level='warn', title=say(lang, 'insight.fills.title', name=name),
                              detail=say(lang, 'insight.fills.detail', used=decimal(row['used_percent'], lang),
                                         pace=pace[0].upper() + pace[1:], full=_time(row['full_at'], lang),
                                         resets=_time(row['resets_at'], lang)),
                              evidence=row))
    return found


def _long_sessions(rows, lang):
    best = None
    for agent in AGENTS:
        mine = [s for s in rows if s.agent == agent and s.calls >= 5 and s.calls_complete and s.tokens_complete and s.attribution_complete]
        short = [total(s.tokens) / s.calls for s in mine if s.calls < SHORT]
        long = [total(s.tokens) / s.calls for s in mine if s.calls >= LONG]
        if len(short) < 3 or not long:
            continue
        baseline = statistics.median(short)
        if baseline <= 0:
            continue  # a zero-token record is not a usable comparison, nor a reason to fail the scan
        ratio = statistics.median(long) / baseline
        if ratio >= 2 and (best is None or ratio > best[0]):
            best = (ratio, agent, statistics.median(short), statistics.median(long), len(short), len(long))
    if not best:
        return []
    ratio, agent, short, long, n_short, n_long = best
    return [dict(kind='long_sessions', level='tip', title=say(lang, 'insight.long.title'),
                 detail=say(lang, 'insight.long.detail', agent=AGENTS[agent], long=LONG, long_tokens=big(long, lang),
                            short=SHORT, short_tokens=big(short, lang), ratio=decimal(ratio, lang)),
                 evidence=dict(agent=agent, median_tokens_per_call_short=round(short), median_tokens_per_call_long=round(long),
                               short_sessions=n_short, long_sessions=n_long, ratio=round(ratio, 2)))]


def _concentration(rows, lang):
    tokens = [total(s.tokens) for s in rows]
    whole = sum(tokens)
    if len(rows) < 3 or not whole:
        return []
    top = max(rows, key=lambda s: total(s.tokens))
    share = total(top.tokens) / whole
    if share < 0.4:
        return []
    calls = (say(lang, 'insight.calls_unknown') if any(n.startswith('Older Codex log:') for n in top.notes)
             else count(lang, top.calls, 'call', big(top.calls, lang)))
    return [dict(kind='concentration', level='info', title=say(lang, 'insight.concentration.title'),
                 detail=say(lang, 'insight.concentration.detail', share=round(share * 100), agent=AGENTS.get(top.agent, top.agent),
                            tokens=big(total(top.tokens), lang), calls=calls),
                 evidence=dict(share=round(share, 3), session_tokens=total(top.tokens), period_tokens=whole))]


def _limit_hits(rows, since, lang):
    hits = sorted(when for s in rows for when in s.limit_hits if since is None or when >= since)
    if not hits:
        return []
    return [dict(kind='limit_hits', level='warn', title=say(lang, 'insight.limits.title'),
                 detail=say(lang, 'insight.limits.detail', count=count(lang, len(hits), 'request'), last=moment(hits[-1], lang, year=False)),
                 evidence=dict(count=len(hits), last=hits[-1].isoformat()))]


def _interrupted(rows, lang):
    found = []
    for agent in AGENTS:
        mine = [s for s in rows if s.agent == agent]
        failed = sum(s.errors + s.aborted for s in mine)
        prompts = sum(s.prompts for s in mine)
        if failed >= 3 and prompts and failed / prompts >= 0.05:
            found.append(dict(kind='interrupted', level='info', title=say(lang, 'insight.interrupted.title'),
                              detail=say(lang, 'insight.interrupted.detail', agent=AGENTS[agent],
                                         errors=count(lang, sum(s.errors for s in mine), 'error'),
                                         aborted=count(lang, sum(s.aborted for s in mine), 'interrupted_turn'),
                                         requests=count(lang,prompts,'request')),
                              evidence=dict(agent=agent, errors=sum(s.errors for s in mine),
                                            aborted=sum(s.aborted for s in mine), prompts=prompts)))
    return found


def insights(rows, outlook, since=None, limit=4, lang='en',usage_complete=True):
    return (_quota(outlook, lang) + _limit_hits(rows, since, lang) +
            ((_long_sessions(rows, lang) + _concentration(rows, lang)) if usage_complete else [])
            + _interrupted(rows, lang))[:limit]
