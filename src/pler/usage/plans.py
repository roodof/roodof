"""Recorded usage and published plan thresholds, never a bill or switching recommendation.

Prices and limit ratios are the providers' published figures of PRICES_AS_OF, in US dollars before tax (the
providers show local prices elsewhere). Only published ratios are used: Anthropic states that Max gives 5x
Pro's usage every 5 hours and every week, and Ultra 10x Pro's weekly usage, with no 5-hour limit for verified accounts. OpenAI
publishes no ratio between Plus and its Pro plans, so PLER never says which of them would be enough.

A subscription also covers chat outside the coding agents, which PLER does not see: the API equivalent is the
agents' recorded work only. Account-wide meter observations can include activity outside these logs.
Codex logs its plan with its meter; Claude Code logs neither, so its plan is what the user chose here and its
meter comes from PLER's status line. The choice is kept only on this computer (plan-choice.json).
"""
from datetime import timedelta
import json

from ..paths import cache_file
from .records import TOKEN_FIELDS, add_tokens, empty_tokens, percentage, total
from .period_usage import event_time
from .forecast import LARGE_DROP, SHORT_MAX_AGE, LONG_MAX_AGE

PRICES_AS_OF = '2026-11-01'
PERIOD = timedelta(days=30)
MIN_HISTORY = timedelta(days=14)  # minimum span for an observed threshold comparison, not proof of fit
MIN_OBSERVED_DAYS = 14            # distinct UTC dates, not just two distant samples
MAX_SAMPLE_GAP = timedelta(days=2)
HEADROOM = 0.8                    # a smaller plan must have fitted with a fifth of it to spare
SAME_RESET = timedelta(minutes=5)
FIVE_HOURS, WEEK = 300, 7 * 24 * 60
FILENAME = 'plan-choice.json'
FORMAT = 1
CHOICES = ('pro', 'max', 'ultra', 'api')  # what the user can say about Claude; 'api' = an API key, no plan

# usd: monthly list price; limits: published multiples of the smallest paid plan.
# None means no uniform comparable limit (Ultra's verification-dependent 5-hour
# rule cannot be established from a user plan selection).
PLANS = {
    'claude-code': {
        'pro': dict(usd=20, limits={FIVE_HOURS: 1, WEEK: 1}),    # $17 a month with annual billing
        'max': dict(usd=100, limits={FIVE_HOURS: 5, WEEK: 5}),
        'ultra': dict(usd=200, limits={FIVE_HOURS: None, WEEK: 10}),  # no 5-hour limit for verified accounts
    },
    'codex': {
        'go': dict(usd=8, limits=None),
        'plus': dict(usd=20, limits=None),
        'pro': dict(usd=None, limits=None),  # Pro 100, 200 or 500; the tier is not logged
    },
}
SMALLER = {'claude-code': {'max': 'pro', 'ultra': 'max'}}


def _without_conflicts(rows):
    """Samples outside contradictory episodes, and whether any were dropped.

    Same contradiction rule as forecast._consistent_history, which keeps only the clean tail after the last
    episode; a historical count keeps the clean periods on both sides and drops the whole window period in which
    a contradiction appeared, up to its latest reset.
    """
    kept, previous, until, dropped = [], None, None, False
    for sample in rows:
        if until is not None:
            if sample[0] < until:
                until = max(until, sample[3])
                continue
            previous, until = None, None
        if previous is not None and sample[0] < previous[3]:
            moved = sample[3] - previous[3]
            if (moved < -SAME_RESET
                    or abs(moved) <= SAME_RESET and previous[2] - sample[2] > LARGE_DROP
                    or sample[0] == previous[0] and (sample[2] != previous[2] or abs(moved) > SAME_RESET)):
                start = min(previous[3], sample[3]) - timedelta(minutes=sample[1])
                kept = [row for row in kept if row[0] < start]
                until, dropped = max(previous[3], sample[3]), True
                continue
        kept.append(sample)
        previous = sample
    return kept, dropped


def _meter(samples, since, now):
    """Historical observed maxima, with conflicting or unusable evidence withheld.

    A contradictory episode is left out of the period counts; any such episode, even an expired one, still
    rules out a lower-plan comparison (the 'meter_conflicting' limitation).
    """
    windows, limits = {}, set()
    for sample in samples:
        if not isinstance(sample, (list, tuple)) or len(sample) < 4:
            limits.add('meter_incomplete'); continue
        at, resets = event_time(sample[0]), event_time(sample[3])
        if at is not None and at < since: continue
        if (at is None or at > now or type(sample[1]) is not int or sample[1] <= 0
                or percentage(sample[2]) is None or resets is None or resets <= at
                or (resets-at).total_seconds() > sample[1]*60+SAME_RESET.total_seconds()):
            limits.add('meter_incomplete'); continue
        windows.setdefault(sample[1], set()).add((at, sample[1], percentage(sample[2]), resets))
    result = {}
    for minutes, rows in windows.items():
        rows, dropped = _without_conflicts(sorted(rows))
        if dropped:
            limits.add('meter_conflicting')
        if not rows:
            continue
        periods = []
        for at, _, used, resets in rows:
            # One window period per reset time; samples arrive in time order, so compare with the last period.
            if periods and abs(periods[-1][0] - resets) <= SAME_RESET:
                periods[-1][1] = max(periods[-1][1], used)
            else:
                periods.append([resets, used])
        result[minutes] = dict(samples=len(rows), first=rows[0][0], last=rows[-1][0],
                               resets_at=rows[-1][3], observed_days=len({at.date() for at,_,_,_ in rows}),
                               max_gap=max((b[0]-a[0] for a,b in zip(rows,rows[1:])),default=PERIOD),
                               peak=max(used for _, _, used, _ in rows), periods=len(periods),
                               full=sum(peak >= 100 for _, peak in periods))
    return result, limits


def _spent(sessions, since, now):
    """List-price dollars, priced tokens and tokens of the responses dated inside the period, from each accepted
    response's own time and price (period_usage.record_response). Unlike the dated-usage view this keeps
    sessions whose project is unknown: a plan is the account's, not a project's. `partial` says that some
    usage of these sessions has no usable date (undated, straddling the period start, cumulative-only or
    incomplete), so the sum may be low."""
    usd = priced = tokens = 0
    partial = False
    for session in sessions:
        events = getattr(session, '_usage_events', None)
        if (not session.tokens_complete or not session.calls_complete or not session.models_complete
                or session.archive_old_parser or session.archive_unverified
                or session.issues & {'archive_old_parser', 'archive_unverified'}
                or getattr(session, '_history_uncertain', False)
                or not isinstance(events,list) and (total(session.tokens) or session.calls)):
            partial = True
        counted = 0
        allocated = empty_tokens()
        for event in events if isinstance(events,list) else ():
            first, at = event_time(event.get('first')), event_time(event.get('at'))
            if at is None or first is None or first > at or at > now or first < since <= at:
                partial = True
                continue
            counted += 1
            add_tokens(allocated,event['tokens'])
            if since <= at <= now:
                tokens += total(event['tokens'])
                if event.get('usd') is not None:
                    usd += event['usd']
                    priced += total(event['tokens'])
        if (counted != session.calls or any(allocated[key] != session.tokens[key] for key in TOKEN_FIELDS)):
            partial = True
    return usd, priced, tokens, partial


def _comparison_limit(agent, plan, meter, now):
    smaller = SMALLER.get(agent, {}).get(plan)
    if smaller is None: return None
    required=[minutes for minutes,ratio in PLANS[agent][smaller]['limits'].items()
              if ratio is not None and PLANS[agent][plan]['limits'].get(minutes) is not None]
    for minutes in required:
        value=meter.get(minutes)
        if value is not None:
            max_age=SHORT_MAX_AGE if minutes < 24*60 else LONG_MAX_AGE
            if now-value['last'] > max_age or value['resets_at'] <= now:
                return 'meter_stale'
    if any(minutes not in meter or meter[minutes]['last']-meter[minutes]['first'] < MIN_HISTORY
           or meter[minutes]['observed_days'] < MIN_OBSERVED_DAYS
           or meter[minutes]['max_gap'] > MAX_SAMPLE_GAP for minutes in required):
        return 'meter_sparse'
    return None


def _lower_plan_comparison(agent, plan, meter):
    """A conditional comparison of observed samples to published ratios, never proof of fit."""
    smaller = SMALLER.get(agent, {}).get(plan)
    if smaller is None:
        return None
    current, lower = PLANS[agent][plan]['limits'], PLANS[agent][smaller]['limits']
    unmeasured, shares, peaks, expires = False, [], [], []
    for minutes, ratio in lower.items():
        if ratio is None:
            continue
        if current.get(minutes) is None:
            unmeasured = True  # e.g. Ultra has no 5-hour limit, so its meter says nothing about Max's
            continue
        window = meter.get(minutes)
        if window is None:
            return None
        if window['peak'] > 100 * ratio / current[minutes] * HEADROOM:
            return None
        shares.append(ratio / current[minutes])
        peaks.append(window['peak'])
        expires.append(min(window['resets_at'],window['last']+
                           (SHORT_MAX_AGE if minutes < 24*60 else LONG_MAX_AGE)))
    if not shares:
        return None
    # share: the smaller plan's limits as a part of the current ones; peak: the highest use seen, in percent.
    return dict(plan=smaller, usd=PLANS[agent][smaller]['usd'], unmeasured=unmeasured,
                share=min(shares), peak=max(peaks), observed_only=True, assumed_plan=plan,
                expires_at=min(expires).isoformat())


def advise(sessions, claude_samples, now, claude_plan=None, scopes=None, sources=None):
    """One row per agent seen in the last 30 days (see module docstring); findings are fixed codes."""
    since = now - PERIOD
    sources = sources or {}
    archive = sources.get('archive') or {}
    source_incomplete = bool(sources.get('skipped') or archive.get('errors') or archive.get('evicted_files'))
    rows = []
    for agent in ('claude-code', 'codex'):
        own = [s for s in sessions if s.agent == agent]
        if not own:
            continue
        if agent == 'codex':
            recent = sorted((s for s in own if s.quota_plan and s.ended and since <= s.ended <= now), key=lambda s: s.ended)
            plan = recent[-1].quota_plan if recent else None
            plans_seen = sorted({s.quota_plan for s in recent})
            source = 'log' if plan else None
            samples = [sample for s in own for sample in s.quota]
        else:
            plan, plans_seen = claude_plan, []
            source = 'user' if plan else None
            samples = list(claude_samples)
        known = PLANS[agent].get(plan)
        api_usd, priced, tokens, partial = _spent(own, since, now)
        partial = partial or source_incomplete
        first = min((s.started for s in own if s.started), default=None)
        row = dict(agent=agent, plan=plan if (known or plan == 'api') else None, plan_word=plan, plan_source=source,
                   plan_changed=len(plans_seen) > 1, price_usd=known['usd'] if known else None, prices_as_of=PRICES_AS_OF,
                   period_days=PERIOD.days, api_usd=round(api_usd, 2), total_tokens=tokens,
                   api_priced_share=round(priced / tokens, 4) if tokens else None,
                   history_days=min(PERIOD.days, max(0, (now - first).days)) if first else 0,
                   usage_partial=partial, actual_payment_usd=None, history_complete=False,
                   scope='retained_agent_records_all_projects', since=since.isoformat(), until=now.isoformat(),
                   limit_hits=sum(1 for s in own for hit in s.limit_hits if hit and since <= hit <= now))
        meter, limits = _meter(samples, since, now)
        if (scopes or {}).get(agent, 0) > 1:
            meter={}; limits.add('multiple_source_groups')
        if source_incomplete: limits.add('source_incomplete')
        if partial: limits.add('usage_incomplete')
        if priced < tokens: limits.add('unpriced_usage')
        if row['plan_changed']: limits.add('plan_changed')
        row['meter'] = [dict(window_minutes=minutes, samples=value['samples'], peak=value['peak'], periods=value['periods'],
                             full=value['full'], observed_days=value['observed_days'], last_at=value['last'].isoformat(),
                             history_days=round((value['last'] - value['first']).total_seconds() / 86400, 1))
                        for minutes, value in sorted(meter.items())]
        row['meter_ambiguous'] = bool(limits & {'multiple_source_groups','meter_conflicting'})
        findings = []
        if agent == 'claude-code' and plan is None:
            findings.append('choose_plan')
        if not meter and not row['meter_ambiguous']:
            findings.append('no_meter')
        full = {minutes: value['full'] for minutes, value in meter.items() if value['full']}
        if full or row['limit_hits']:
            findings.append('limits_reached')
            if agent == 'codex' and plan in ('go', 'plus'):
                findings.append('larger_ratio_unpublished')
            elif agent == 'claude-code' and plan in ('pro', 'max'):
                findings.append('larger_need_unseen')
        # Even a fully dated retained month is not proof of complete billing or
        # all account use. State a numeric observation, never a switching saving.
        if (known and known['usd'] is not None and tokens > 0 and priced == tokens and not limits
                and row['history_days'] >= PERIOD.days - 2 and not full and not row['limit_hits']
                and api_usd < known['usd']):
            findings.append('api_below_list_price')
        if known and meter:
            reason = _comparison_limit(agent,plan,meter,now)
            if reason: limits.add(reason)
        lower = (_lower_plan_comparison(agent,plan,meter)
                 if known and not limits and not full and not row['limit_hits'] else None)
        if lower:
            row['lower_plan_comparison'] = lower
            findings.append('lower_weekly_observed' if lower['unmeasured'] else 'lower_observed')
        row['limitations'] = sorted(limits)
        row['findings'] = findings
        rows.append(row)
    return rows


def _valid(value):
    return isinstance(value, dict) and set(value) == {'format', 'claude'} and type(value['format']) is int \
        and value['format'] == FORMAT and value['claude'] in (*CHOICES, None)


class Choice:
    """The Claude plan the user chose, in PLER's cache folder (or `base`); a file PLER cannot understand is
    reported and never overwritten."""

    def __init__(self, base=None):
        self.base = base

    def _path(self):
        path = cache_file(FILENAME, self.base)
        if path is None:
            raise OSError('unsafe plan choice')
        return path

    def read(self):
        path = self._path()
        try:
            size = path.stat().st_size
            if size > 4096:
                raise ValueError('oversized plan choice')
            with path.open('rb') as stream:
                data = stream.read(size + 1)
        except FileNotFoundError:
            return None
        if len(data) != size:
            raise ValueError('plan choice changed while reading')
        value = json.loads(data.decode('utf-8'))
        if not _valid(value):
            raise ValueError('invalid plan choice')
        return value['claude']

    def save(self, plan):
        from .archive import _locked, _write
        if plan not in (*CHOICES, None):
            raise ValueError('invalid plan')
        path = self._path()
        with _locked(path.parent):
            self.read()  # refuse to replace a file that cannot be understood
            _write(path, dict(format=FORMAT, claude=plan))
        return plan


class Memory:
    """The demo's choice lives only as long as the page."""

    def __init__(self, plan=None):
        self.plan = plan

    def read(self):
        return self.plan

    def save(self, plan):
        if plan not in (*CHOICES, None):
            raise ValueError('invalid plan')
        self.plan = plan
        return plan
