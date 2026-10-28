"""Public report provenance and fixed quality indicators, shared by the terminal and browser."""
from . import __version__
from .i18n import say

SCHEMA_VERSION=2
PARSER_VERSION='accounting-2026-10-28.4'
ISSUES={'invalid_records':'quality.invalid_records','conflicting_usage':'quality.conflicting_usage',
        'unreconciled_totals':'quality.unreconciled_totals','shared_attribution':'quality.shared_attribution',
        'unknown_model':'quality.unknown_model','cumulative_usage':'quality.cumulative_usage',
        'unidentified_records':'quality.unidentified_records','reconciled_copies':'quality.reconciled_copies'}


def provenance():
    return dict(version=__version__,schema_version=SCHEMA_VERSION,parser_version=PARSER_VERSION,
                source_scope='retained_local_agent_logs')


def quality(rows,sources,lang='en'):
    codes={code for row in rows for code in row.issues}
    if sources.get('skipped'): codes.add('invalid_records')
    return dict(tokens_complete=not sources.get('skipped') and all(s.tokens_complete for s in rows),
                calls_complete=all(s.calls_complete for s in rows),counts_complete=all(s.counts_complete for s in rows),
                attribution_complete=all(s.attribution_complete for s in rows),models_complete=all(s.models_complete for s in rows),
                issues=[dict(code=code,detail=say(lang,ISSUES[code])) for code in sorted(codes) if code in ISSUES])
