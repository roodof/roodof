"""Dated, reconciled response usage from metadata already read by PLER.

This is never a provider ledger or an allocation of whole-session totals.
Cumulative residuals have no event here. No files, Git, clock or identifiers
are queried or published by the calculation.
"""
from collections import Counter
from datetime import datetime, timezone
import math

from .records import TOKEN_FIELDS, add_tokens, empty_tokens, timestamp, total


EXCLUSIONS=('archive_old_parser','archive_unverified','uncertain_history',
            'incomplete_usage','unverified_attribution','missing_event_evidence')


def _utc(value):
    if not isinstance(value,datetime): return None
    if value.tzinfo is timezone.utc: return value  # already UTC (readers store this); skip the conversion
    try:
        return value.astimezone(timezone.utc) if value.utcoffset() is not None else None
    except (OverflowError,TypeError,ValueError): return None


def event_time(value):
    """Require an explicit UTC offset or epoch; never assume a naive log time is UTC."""
    if isinstance(value,datetime): return _utc(value)
    if isinstance(value,str):
        try: return _utc(datetime.fromisoformat(value.replace('Z','+00:00')))
        except (ValueError,OverflowError): return None
    if type(value) in (int,float):
        try:
            return _utc(timestamp(value)) if math.isfinite(value) else None
        except OverflowError: return None
    return None


def record_response(session,tokens,candidates,usd=None):
    """Attach one accepted stable response, with only its selected snapshot's times and its list-price
    equivalent (`usd`, None when unpriced).

    Every copy carrying the selected actual usage must give an aware timestamp;
    a missing or naive one leaves the response undated. Claude Code writes one
    row per content block of a response, each with the same usage and its own
    time (in real logs 75% of responses, seconds apart), so the response spans
    its earliest to latest copy. Earlier smaller snapshots cannot date a later
    larger usage report.
    """
    times={_utc(copy.get('usage_at')) for copy in candidates if copy.get('tokens')==tokens}
    dated=bool(times) and None not in times
    if not hasattr(session,'_usage_events'): session._usage_events=[]
    session._usage_events.append(dict(first=min(times) if dated else None,at=max(times) if dated else None,
                                      tokens=dict(tokens),usd=usd))


def _reason(session):
    issues=getattr(session,'issues',())
    if getattr(session,'archive_old_parser',False) or 'archive_old_parser' in issues:
        return 'archive_old_parser'
    archived=getattr(session,'source_state','live') in ('archive','mixed') or getattr(session,'archive_files',0)
    if (getattr(session,'archive_unverified',False) or 'archive_unverified' in issues
            or archived and not getattr(session,'source_deleted',False)):
        return 'archive_unverified'
    if getattr(session,'_history_uncertain',False): return 'uncertain_history'
    if not session.tokens_complete: return 'incomplete_usage'
    if not session.attribution_complete: return 'unverified_attribution'
    if not isinstance(getattr(session,'_usage_events',None),list) and (total(session.tokens) or session.calls):
        return 'missing_event_evidence'
    return None


def analyze(sessions,since,cutoff):
    """Only timestamped accepted responses within the inclusive selected interval.

    The caller supplies all reconciled sessions in the selected agent/project
    scope, not just sessions ending within this period. `since=None` means all
    dated records through cutoff. Coverage refers only to this retained input.
    """
    requested_since=since
    cutoff=_utc(cutoff)
    since=_utc(since) if since is not None else None
    if (cutoff is None or requested_since is not None and since is None
            or since is not None and since>cutoff):
        raise ValueError('dated usage requires an aware, ordered interval')
    selected={}
    for session in sessions:
        selected.setdefault((session.agent,session.source,session.session_id),session)
    result=dict(mode='dated_recorded_responses',since=since.isoformat() if since is not None else None,
                cutoff=cutoff.isoformat(),tokens=empty_tokens(),total_tokens=0,response_calls=0,
                contributing_sessions=0,selected_sessions=len(selected),eligible_sessions=0,
                dated_response_calls=0,outside_period_calls=0,undated_response_calls=0,
                future_response_calls=0,unallocated_sessions=0,retained_usage_fully_dated=True)
    excluded=Counter()
    agents={}
    for session in selected.values():
        reason=_reason(session)
        if reason is not None:
            excluded[reason]+=1
            result['unallocated_sessions']+=1
            continue
        result['eligible_sessions']+=1
        allocated,inside=empty_tokens(),empty_tokens()
        dated=calls=0
        unknown=False
        for event in getattr(session,'_usage_events',()):
            at=_utc(event['at'])
            first=_utc(event.get('first',event['at']))
            # A response whose copies straddle the period start cannot be allocated to either side.
            if at is None or first is None or since is not None and first<since<=at:
                result['undated_response_calls']+=1;unknown=True
                continue
            if at>cutoff:
                result['future_response_calls']+=1;unknown=True
                continue
            dated+=1
            values=event['tokens']
            # add_tokens, inlined: these loops run once per response; the session's sums are added once below.
            for key in TOKEN_FIELDS: allocated[key]+=values.get(key) or 0
            if since is not None and at<since:
                result['outside_period_calls']+=1
                continue
            for key in TOKEN_FIELDS: inside[key]+=values.get(key) or 0
            calls+=1
        result['dated_response_calls']+=dated
        if calls:
            add_tokens(result['tokens'],inside)
            result['response_calls']+=calls;result['contributing_sessions']+=1
            agent=session.agent if session.agent in ('claude-code','codex') else 'unknown'
            value=agents.setdefault(agent,dict(agent=agent,tokens=empty_tokens(),total_tokens=0,
                                               response_calls=0,contributing_sessions=0))
            add_tokens(value['tokens'],inside);value['response_calls']+=calls;value['contributing_sessions']+=1
        if (unknown or any(allocated[key]!=session.tokens[key] for key in TOKEN_FIELDS)
                or dated!=session.calls or not session.calls_complete):
            result['unallocated_sessions']+=1
    result['total_tokens']=total(result['tokens'])
    result['excluded']={reason:excluded[reason] for reason in EXCLUSIONS}
    result['retained_usage_fully_dated']=not result['unallocated_sessions']
    for value in agents.values(): value['total_tokens']=total(value['tokens'])
    result['agents']=[agents[agent] for agent in sorted(agents)]
    return result
