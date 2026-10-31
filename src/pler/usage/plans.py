"""Does the subscription fit? Per agent: the plan, its list price, what the same agent work would cost with an
API key, and how often the plan's limits were reached in the last 30 days.

Prices and limit ratios are the providers' published figures of PRICES_AS_OF, in US dollars before tax (the
providers show local prices elsewhere). Only published ratios are used: Anthropic states that Max gives 5x
Pro's usage every 5 hours and every week, and Ultra 10x Pro's weekly usage with no 5-hour limit. OpenAI
publishes no ratio between Plus and its Pro plans, so PLER never says which of them would be enough.

A subscription also covers chat outside the coding agents, which PLER does not see: the API equivalent is the
agents' work only. The subscription meter is account-wide, so a limit reached there includes everything.
Codex logs its plan with its meter; Claude Code logs neither, so its plan is what the user chose here and its
meter comes from PLER's status line. The choice is kept only on this computer (plan-choice.json).
"""
from datetime import timedelta
import json

from ..paths import cache_file
from .records import percentage, total

PRICES_AS_OF = '2026-10-31'
PERIOD = timedelta(days=30)
MIN_HISTORY = timedelta(days=14)  # meter history needed before a smaller plan is named
HEADROOM = 0.8                    # a smaller plan must have fitted with a fifth of it to spare
SAME_RESET = timedelta(minutes=5)
FIVE_HOURS, WEEK = 300, 7 * 24 * 60
FILENAME = 'plan-choice.json'
FORMAT = 1
CHOICES = ('pro', 'max', 'ultra', 'api')  # what the user can say about Claude; 'api' = an API key, no plan

# usd: monthly list price; limits: usage per window as a multiple of the smallest paid plan, None = no
# such limit; a plan without published ratios has limits=None.
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


def _meter(samples, since, now):
    """{window minutes: samples, first/last time, peak, periods seen and periods that reached 100%}."""
    windows = {}
    for sample in samples:
        if (len(sample) > 3 and sample[0] is not None and sample[0].tzinfo is not None and since <= sample[0] <= now
                and type(sample[1]) is int and percentage(sample[2]) is not None and sample[3] is not None
                and sample[3].tzinfo is not None):
            windows.setdefault(sample[1], set()).add((sample[0], percentage(sample[2]), sample[3]))
    result = {}
    for minutes, rows in windows.items():
        rows = sorted(rows)
        periods = []
        for at, used, resets in rows:
            # One window period per reset time; samples arrive in time order, so compare with the last period.
            if periods and abs(periods[-1][0] - resets) <= SAME_RESET:
                periods[-1][1] = max(periods[-1][1], used)
            else:
                periods.append([resets, used])
        result[minutes] = dict(samples=len(rows), first=rows[0][0], last=rows[-1][0],
                               peak=max(used for _, used, _ in rows), periods=len(periods),
                               full=sum(peak >= 100 for _, peak in periods))
    return result


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
        if not session.tokens_complete or (events is None and (total(session.tokens) or session.calls)):
            partial = True
        counted = 0
        for event in events or ():
            first, at = event.get('first'), event.get('at')
            if at is None or first is None or first < since <= at:
                partial = True
                continue
            counted += 1
            if since <= at <= now:
                tokens += total(event['tokens'])
                if event.get('usd') is not None:
                    usd += event['usd']
                    priced += total(event['tokens'])
        if events is not None and counted != session.calls:
            partial = True
    return usd, priced, tokens, partial


def _smaller(agent, plan, meter):
    """The next smaller plan when the meter shows it would have fitted with headroom, else None; and whether
    that judgement leaves out a window the current plan does not limit."""
    smaller = SMALLER.get(agent, {}).get(plan)
    if smaller is None:
        return None
    current, lower = PLANS[agent][plan]['limits'], PLANS[agent][smaller]['limits']
    unmeasured, shares, peaks = False, [], []
    for minutes, ratio in lower.items():
        if ratio is None:
            continue
        if current.get(minutes) is None:
            unmeasured = True  # e.g. Ultra has no 5-hour limit, so its meter says nothing about Max's
            continue
        window = meter.get(minutes)
        if window is None or window['last'] - window['first'] < MIN_HISTORY:
            return None
        if window['peak'] > 100 * ratio / current[minutes] * HEADROOM:
            return None
        shares.append(ratio / current[minutes])
        peaks.append(window['peak'])
    if not shares:
        return None
    # share: the smaller plan's limits as a part of the current ones; peak: the highest use seen, in percent.
    return dict(plan=smaller, usd=PLANS[agent][smaller]['usd'], unmeasured=unmeasured, share=min(shares), peak=max(peaks))


def advise(sessions, claude_samples, now, claude_plan=None, scopes=None):
    """One row per agent seen in the last 30 days (see module docstring); findings are fixed codes."""
    since = now - PERIOD
    rows = []
    for agent in ('claude-code', 'codex'):
        own = [s for s in sessions if s.agent == agent]
        if not own:
            continue
        if agent == 'codex':
            recent = sorted((s for s in own if s.quota_plan and s.ended and s.ended >= since), key=lambda s: s.ended)
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
        first = min((s.started for s in own if s.started), default=None)
        row = dict(agent=agent, plan=plan if (known or plan == 'api') else None, plan_word=plan, plan_source=source,
                   plan_changed=len(plans_seen) > 1, price_usd=known['usd'] if known else None, prices_as_of=PRICES_AS_OF,
                   period_days=PERIOD.days, api_usd=round(api_usd, 2), total_tokens=tokens,
                   api_priced_share=round(priced / tokens, 4) if tokens else None,
                   history_days=min(PERIOD.days, max(0, (now - first).days)) if first else 0,
                   usage_partial=partial,
                   limit_hits=sum(1 for s in own for hit in s.limit_hits if hit and since <= hit <= now))
        meter = {} if (scopes or {}).get(agent, 0) > 1 else _meter(samples, since, now)
        row['meter'] = [dict(window_minutes=minutes, samples=value['samples'], peak=value['peak'], periods=value['periods'],
                             full=value['full'], history_days=round((value['last'] - value['first']).total_seconds() / 86400, 1))
                        for minutes, value in sorted(meter.items())]
        row['meter_ambiguous'] = (scopes or {}).get(agent, 0) > 1
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
        # Not when a limit was reached: then the account also carries use PLER does not see, and moving the agent
        # work to an API key would not free the plan of it.
        if (known and known['usd'] is not None and row['history_days'] >= PERIOD.days - 2 and not partial
                and not full and not row['limit_hits'] and api_usd < known['usd']):
            findings.append('api_cheaper')
        smaller = _smaller(agent, plan, meter) if known and not full and not row['limit_hits'] else None
        if smaller:
            row['smaller'] = smaller
            findings.append('smaller_fits_weekly' if smaller['unmeasured'] else 'smaller_fits')
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
