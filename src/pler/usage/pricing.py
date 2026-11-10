"""What the recorded tokens would cost at the providers' public API list prices.

This is an equivalent for comparison with a subscription or a budget, never a bill: subscriptions are flat fees,
and Roodof does not know discounts, taxes or which account paid. Each accepted response is priced once, by its own
model and prompt size, at the standard tier. A response is left unpriced (and counted as such) when its model is
not in the table, its prompt is above a tier the table covers, or it ran at a different speed or region price.
Cumulative totals without per-response usage are never priced. No network is used; prices are fixed below.
"""
import re

PRICES_AS_OF = '2026-11-01'
SOURCES = ('https://platform.claude.com/docs/en/about-claude/pricing',
           'https://developers.openai.com/api/docs/pricing',
           'https://developers.openai.com/api/docs/guides/prompt-caching')


def _claude(base, write_5m, write_1h, read, output, up_to=None):
    return (up_to, dict(input=base, write_5m=write_5m, write_1h=write_1h, cache_read=read, output=output))


def _openai(base, cached, output, up_to=None, legacy_writes=False):
    # GPT-5.6+ writes use 30m/12h rates, not Claude's 5m/1h categories.
    # Codex's retained counts have no lifetime split: withhold that response's price.
    written=base if legacy_writes else None
    return (up_to, dict(input=base, write_5m=written, write_1h=written, cache_read=cached, output=output))


# USD per million tokens. Each model lists (largest prompt covered, prices) tiers in ascending order;
# None covers any size. A prompt counts input, cache reads and cache writes of that one response.
_OPUS_45 = [_claude(5, 6.25, 10, 0.50, 25)]
_SONNET_4 = [_claude(3, 3.75, 6, 0.30, 15, up_to=200_000)]  # longer prompts had a separate beta price
PRICES = {
    'claude-code': {
        'claude-fable-5-1': [_claude(10, 12.50, 20, 0.25, 50)],
        'claude-mythos-5-1': [_claude(10, 12.50, 20, 0.25, 50)],
        'claude-fable-5': [_claude(10, 12.50, 20, 1, 50)],
        'claude-mythos-5': [_claude(10, 12.50, 20, 1, 50)],
        'claude-opus-5-5': [_claude(4, 5, 8, 0.20, 20)],
        'claude-opus-5': [_claude(5, 6.25, 10, 0.50, 25)],
        'claude-opus-4-8': _OPUS_45, 'claude-opus-4-7': _OPUS_45, 'claude-opus-4-6': _OPUS_45,
        'claude-opus-4-5': _OPUS_45,
        'claude-opus-4-1': [_claude(15, 18.75, 30, 1.50, 75)],
        'claude-opus-4': [_claude(15, 18.75, 30, 1.50, 75)],
        'claude-sonnet-5-5': [_claude(2, 2.50, 4, 0.10, 10)],
        'claude-sonnet-5': [_claude(2, 2.50, 4, 0.20, 10)],
        'claude-sonnet-4-6': [_claude(3, 3.75, 6, 0.30, 15)],
        'claude-sonnet-4-5': _SONNET_4, 'claude-sonnet-4': _SONNET_4,
        'claude-haiku-5-5': [_claude(0.10, 0.125, 0.20, 0.01, 0.50, up_to=100_000), _claude(0.50, 0.625, 1, 0.05, 2.50)],
        'claude-haiku-4-5': [_claude(1, 1.25, 2, 0.10, 5)],
        'claude-3-5-haiku': [_claude(0.80, 1, 1.60, 0.08, 4)],
    },
    'codex': {
        'gpt-6-astra': [_openai(10, 1, 50, up_to=272_000), _openai(20, 2, 75)],
        'gpt-6.1-sol': [_openai(2, 0.10, 10, up_to=272_000), _openai(4, 0.20, 15)],
        'gpt-6.1-terra': [_openai(1, 0.05, 5, up_to=272_000), _openai(2, 0.10, 7.50)],
        'gpt-6-luna': [_openai(0.10, 0.01, 0.50, up_to=272_000), _openai(0.20, 0.02, 0.75)],
        'gpt-6-sol': [_openai(2, 0.20, 10, up_to=272_000), _openai(4, 0.40, 15)],
        'gpt-5.3-codex': [_openai(1.75, 0.175, 14, up_to=272_000, legacy_writes=True)],  # no published long-context price
    },
}
_DATED = re.compile(r'-\d{8}$')  # claude-sonnet-4-5-20250929 is claude-sonnet-4-5


def _tiers(agent, model):
    table = PRICES.get(agent, {})
    if not isinstance(model, str):
        return None
    return table.get(model) or (table.get(_DATED.sub('', model)) if agent=='claude-code' else None)


def response_cost(agent, model, tokens, write_1h=0, standard=True):
    """USD for one accepted response, or None when it cannot be priced honestly."""
    tiers = _tiers(agent, model)
    if not tiers or not standard:
        return None
    written = tokens['cache_write']
    if not 0 <= write_1h <= written:
        return None
    prompt = tokens['input'] + tokens['cache_read'] + written
    prices = next((value for limit, value in tiers if limit is None or prompt <= limit), None)
    if prices is None:
        return None
    components=((tokens['input'],prices['input']),(tokens['cache_read'],prices['cache_read']),
                (written-write_1h,prices['write_5m']),(write_1h,prices['write_1h']),(tokens['output'],prices['output']))
    if any(count and rate is None for count,rate in components):return None
    return sum(count*rate for count,rate in components if count)/1e6


def charge(session, agent, model, tokens, write_1h=0, standard=True):
    """Add one accepted response's list-price equivalent to its owning session; return it, or None when the
    response cannot be priced."""
    value = response_cost(agent, model, tokens, write_1h, standard)
    if value is None:
        return None
    session.api_usd += value
    session.api_priced_tokens += sum(tokens[name] for name in ('input', 'cache_read', 'cache_write', 'output'))
    return value
