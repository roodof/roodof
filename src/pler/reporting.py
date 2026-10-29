"""Public report provenance and fixed quality indicators, shared by the terminal and browser."""
from . import __version__
from .i18n import say

SCHEMA_VERSION=2
PARSER_VERSION='accounting-2026-10-29.2'
ISSUES={'invalid_records':'quality.invalid_records','conflicting_usage':'quality.conflicting_usage',
        'unreconciled_totals':'quality.unreconciled_totals','shared_attribution':'quality.shared_attribution',
        'unknown_model':'quality.unknown_model','cumulative_usage':'quality.cumulative_usage',
        'unidentified_records':'quality.unidentified_records','reconciled_copies':'quality.reconciled_copies',
        'wsl_unavailable':'quality.wsl_unavailable',
        'archive_old_parser':'quality.archive_old_parser','archive_unverified':'quality.archive_unverified',
        'archive_evicted':'quality.archive_evicted','archive_invalid':'quality.archive_invalid'}


def provenance(archived=False):
    return dict(version=__version__,schema_version=SCHEMA_VERSION,parser_version=PARSER_VERSION,
                source_scope='retained_local_agent_logs_with_pler_archive' if archived else 'retained_local_agent_logs')


def quality(rows,sources,lang='en'):
    codes={code for row in rows for code in row.issues}
    if sources.get('skipped'): codes.add('invalid_records')
    if any(reason in ('WSLUnavailable','WSLNotRunning') for _,reason in sources.get('skipped',())):
        codes.add('wsl_unavailable')
    archive=sources.get('archive') or {}
    if archive.get('evicted_files'): codes.add('archive_evicted')
    if archive.get('errors'): codes.add('archive_invalid')
    archive_incomplete=bool(archive.get('evicted_files') or archive.get('errors'))
    return dict(tokens_complete=not sources.get('skipped') and not archive_incomplete and all(s.tokens_complete for s in rows),
                calls_complete=all(s.calls_complete for s in rows),counts_complete=all(s.counts_complete for s in rows),
                attribution_complete=all(s.attribution_complete for s in rows),models_complete=all(s.models_complete for s in rows),
                issues=[dict(code=code,detail=say(lang,ISSUES[code])) for code in sorted(codes) if code in ISSUES])
