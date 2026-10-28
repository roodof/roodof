"""Deterministic accounting of retained metadata. Uncertainty is explicit, never a fabricated allocation."""
import hashlib
import json

from .records import TOKEN_FIELDS, empty_tokens

MAX_COUNT = (1 << 53) - 1  # the browser must be able to represent each logged count exactly


def count(value):
    if type(value) is not int or not 0 <= value <= MAX_COUNT:
        raise ValueError('invalid usage count')
    return value


def tokens(usage, agent):
    if not isinstance(usage, dict) or not {'input_tokens','output_tokens'} <= set(usage):
        raise ValueError('missing usage fields')
    incoming, output = count(usage['input_tokens']), count(usage['output_tokens'])
    if agent == 'codex':
        cached = count(usage.get('cached_input_tokens',0))
        written = count(usage.get('cache_write_input_tokens',0))
        reasoning = count(usage.get('reasoning_output_tokens',0))
        if cached + written > incoming or reasoning > output:
            raise ValueError('inconsistent usage fields')
        incoming -= cached + written
    else:
        cached = count(usage.get('cache_read_input_tokens',0))
        written = count(usage.get('cache_creation_input_tokens',0))
        details = usage.get('output_tokens_details')
        reasoning = count(details.get('thinking_tokens',0)) if isinstance(details,dict) else 0
        if reasoning > output:
            raise ValueError('inconsistent reasoning usage')
    return dict(input=incoming,cache_read=cached,cache_write=written,output=output,reasoning=reasoning)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()


def dominates(a,b):
    return all(a[k] >= b[k] for k in TOKEN_FIELDS)


def largest(values):
    """Select an actual compatible snapshot. Crossing component updates are unresolved, not mixed together."""
    unique = {tuple(v[k] for k in TOKEN_FIELDS):v for v in values}
    if not unique:
        return None
    # A snapshot dominating every other one must also be the lexicographic maximum.
    # Verify that actual logged candidate once instead of comparing every pair.
    candidate = max(unique.values(), key=lambda value: tuple(value[k] for k in TOKEN_FIELDS))
    return candidate if all(dominates(candidate, other) for other in unique.values()) else None


def subtract(a,b):
    return {k:a[k]-b[k] for k in TOKEN_FIELDS}


def owner(candidates):
    """Stable aggregation anchor; conflicting source ownership never chooses a project by file order."""
    unique = {s.session_id:s for s in candidates}
    chosen = unique[sorted(unique)[0]]
    # A larger usage snapshot may come from a copied archive stream owned by another
    # native session. Its evidence must follow the counts to the aggregation anchor.
    for session in candidates:
        for source,state in getattr(session,'_sources',{}).items():
            chosen.source_evidence(source,**state)
    if len(unique) > 1:
        for session in unique.values():
            session.attribution_complete = False
            session.issues.add('shared_attribution')
        evidence={getattr(s,'_project_evidence',frozenset([s.project])) for s in unique.values()}
        if len(evidence)>1 or any(len(v)>1 for v in evidence):
            chosen.project = None
    return chosen


def model_for(candidates):
    values = {value for value in candidates if value and value != 'unknown'}
    return next(iter(values)) if len(values)==1 else 'unknown'


def metadata(session, projects, branches=()):
    values = set(projects)
    session._project_evidence=frozenset(values)
    if len(values) > 1:
        session.project = None
        session.attribution_complete = False
        session.issues.add('shared_attribution')
    elif values:
        session.project = next(iter(values))
    values = set(branches)
    session.branch = next(iter(values)) if len(values)==1 else None
