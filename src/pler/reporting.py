"""Public report provenance and fixed quality indicators, shared by the terminal and browser."""
from . import __version__
from .i18n import say

SCHEMA_VERSION=2
PARSER_VERSION='accounting-2026-11-01.1'
ISSUES={'invalid_records':'quality.invalid_records','conflicting_usage':'quality.conflicting_usage',
        'unreconciled_totals':'quality.unreconciled_totals','shared_attribution':'quality.shared_attribution',
        'unknown_model':'quality.unknown_model','cumulative_usage':'quality.cumulative_usage',
        'unidentified_records':'quality.unidentified_records','reconciled_copies':'quality.reconciled_copies',
        'wsl_unavailable':'quality.wsl_unavailable',
        'archive_old_parser':'quality.archive_old_parser','archive_unverified':'quality.archive_unverified',
        'archive_evicted':'quality.archive_evicted','archive_invalid':'quality.archive_invalid',
        'read_limits':'quality.read_limits'}


def provenance(archived=False):
    return dict(version=__version__,schema_version=SCHEMA_VERSION,parser_version=PARSER_VERSION,
                source_scope='retained_local_agent_logs_with_pler_archive' if archived else 'retained_local_agent_logs')


def affected(value):
    """A data-quality issue is distinct from a recorded agent error or interruption."""
    return any(value.get(name) is False for name in
               ('tokens_complete','calls_complete','counts_complete','attribution_complete','models_complete'))


def without_work_items(value):
    """Ordinary exports never carry saved session titles or private work content."""
    result=dict(value)
    result.pop('work_items',None)
    # Keep this boundary explicit if session-level membership is added later.
    if 'sessions' in result:
        result['sessions']=[{key:item for key,item in row.items()
                             if key not in ('work_items','work_item_ids','work_item_titles','title')}
                            for row in result['sessions']]
    return result


def mask_projects(value,lang='en'):
    """Mask project labels consistently in the fixed public dashboard export.

    Opaque row/project codes, times, models and counts remain: this is reduced
    disclosure, not anonymization. The input projection is not modified.
    """
    from copy import deepcopy
    result=deepcopy(without_work_items(value))
    keys=sorted({p['id'] for p in result.get('projects',())}|
                {s['project_id'] for s in result.get('sessions',())})
    names={key:say(lang,'export.project_alias',n=index+1) for index,key in enumerate(keys)}
    for project in result.get('projects',()): project['name']=names[project['id']]
    for session in result.get('sessions',()): session['project']=names[session['project_id']]
    result.pop('project_options',None)
    result['project_names_masked']=True
    return result


def quality(rows,sources,lang='en'):
    codes={code for row in rows for code in row.issues}
    if sources.get('skipped'): codes.add('invalid_records')
    if any(reason=='ReadLimitExceeded' for _,reason in sources.get('skipped',())):codes.add('read_limits')
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


def coverage_guidance(rows, sources):
    """Fixed, path-free explanations; no inference that retained logs cover an account.

    File failures cover all selected source folders, even when session filters
    exclude their readable rows. Session evidence follows the current selection.
    This projection does not change accounting, forecast or recommendation rules.
    """
    reasons={reason for _,reason in sources.get('skipped',())}
    notices=[]
    def add(code, present):
        if present: notices.append(dict(code=code))
    add('wsl_unavailable', reasons & {'WSLUnavailable','WSLNotRunning'})
    add('read_limits', 'ReadLimitExceeded' in reasons)
    add('unsafe_path', 'UnsafePath' in reasons)
    add('source_missing', 'FileNotFoundError' in reasons)
    add('invalid_records', reasons & {'MalformedRows','InconsistentReasoning'})
    known={'WSLUnavailable','WSLNotRunning','ReadLimitExceeded','UnsafePath',
           'FileNotFoundError','MalformedRows','InconsistentReasoning'}
    add('source_access', reasons-known)
    add('archive_old_parser', any(s.archive_old_parser or 'archive_old_parser' in s.issues for s in rows))
    add('archive_unverified', any(s.archive_unverified or 'archive_unverified' in s.issues for s in rows))
    archive=sources.get('archive') or {}
    add('archive_loss', archive.get('evicted_files') or archive.get('errors'))
    add('retained_history', any(s.source_deleted for s in rows))
    add('incomplete_usage', any(not s.tokens_complete or not s.calls_complete or not s.counts_complete
                                for s in rows
                                if not (s.archive_old_parser or s.archive_unverified
                                        or s.issues & {'archive_old_parser','archive_unverified'})))
    add('uncertain_attribution', any(not s.attribution_complete or not s.models_complete for s in rows))
    add('unpriced_usage', any(s.api_priced_tokens < sum(s.tokens[k] for k in ('input','cache_read','cache_write','output'))
                              for s in rows))
    return dict(notices=notices, source_scope='all_selected_folders', session_scope='current_filters')
