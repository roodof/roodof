"""pler report: what your AI coding agents used, read from their own local logs.

No model call is made and nothing leaves the computer. Claude Code (~/.claude/projects,
~/.config/claude/projects or CLAUDE_CONFIG_DIR) and Codex (~/.codex/sessions and archived_sessions, or
CODEX_HOME) are read. Only numbers and metadata are kept; see records.py.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import sys

from . import claude_code, codex, records, unzstd, xxh64, zstd, accounting, reconcile
from ..i18n import LANGUAGES, big, count, decimal, language, moment, say, window
from ..statusline import samples as claude_quota
from .cache import FileCache, version
from .forecast import outlook
from .insights import insights
from .projects import assign, label
from .records import total
from .summary import summarize
from ..reporting import provenance,quality

AGENTS = {'claude-code': 'Claude Code', 'codex': 'Codex'}


def scan(claude_folders=None, codex_folders=None):
    """Sessions from the agents' log folders. Both readers' metadata extracts are cached (cache.py), so
    unchanged logs are not decompressed and parsed again; explicitly given folders are always read. With the
    default folders, the Claude Code quota samples of PLER's status line come along in sources['claude_quota']."""
    skipped=[]
    claude_files = claude_code.files(claude_folders,skipped)
    codex_files = codex.files(codex_folders,skipped)
    cached = FileCache('codex', version(codex, records, zstd, unzstd, xxh64, accounting, reconcile)) if codex_folders is None else None
    codex_sessions, codex_skipped = codex.read(codex_files, cached)
    skipped.extend(codex_skipped)
    if cached:
        cached.save()
    claude_cache = FileCache('claude', version(claude_code, records, accounting)) if claude_folders is None else None
    sessions = assign(claude_code.read(claude_files, skipped, cache=claude_cache) + codex_sessions)
    if claude_cache:
        claude_cache.save()
    return sessions, dict(claude_files=len(claude_files), codex_files=len(codex_files), skipped=skipped,
                          claude_quota=claude_quota() if claude_folders is None else [])


def _local(iso, lang):
    return moment(datetime.fromisoformat(iso), lang)


def _pct(share, lang):
    if share is None:
        return '—'
    return ('%%%d' if lang == 'tr' else '%d%%') % round(share * 100)


def render(summary, sources, notes=(), windows=(), lang='en'):
    """The terminal summary, in the given language (i18n.py)."""
    lines, n = [], lambda value: big(value, lang)
    project = lambda path: label(path, lang=lang) or say(lang, 'unknown_project')
    lines.append((say(lang, 'report.period', sources['days']) if sources.get('days') else say(lang, 'report.all'))
                 + say(lang, 'report.header'))
    if sources.get('days'):
        lines.append(say(lang, 'scope'))
    totals = summary['totals']
    lines.append('')
    lines.append(say(lang, 'report.total', tokens=n(totals['total_tokens']), sessions=count(lang, totals['sessions'], 'session'),
                     calls=count(lang, totals['calls'], 'model_call', n(totals['calls'])),
                     prompts=count(lang, totals['prompts'], 'request', n(totals['prompts']))))
    if totals['total_tokens']:
        cached = totals['tokens']['cache_read']
        lines.append(say(lang, 'report.cache', share=_pct(cached / totals['total_tokens'], lang), tokens=n(totals['total_tokens'] - cached)))
    for agent, row in summary['agents'].items():
        lines.append(say(lang, 'report.agent', agent=AGENTS.get(agent, agent), tokens=n(row['total_tokens']),
                         sessions=count(lang, row['sessions'], 'session'), share=_pct(row['cache_read_share'], lang),
                         errors=count(lang, row['errors'], 'error'), aborted=count(lang, row['aborted'], 'interrupted')))
    if notes:
        lines.append('')
        lines.append(say(lang, 'report.notes'))
        for note in notes:
            lines.append('  • %s — %s' % (note['title'], note['detail']))
    if summary['models']:
        lines.append('')
        lines.append(say(lang, 'report.models'))
        for row in summary['models'][:6]:
            lines.append(say(lang, 'report.model', agent=AGENTS.get(row['agent'], row['agent']), model=row['model'],
                             tokens=n(row['total_tokens']), calls=count(lang, row['calls'], 'call', n(row['calls']))))
    if summary['projects']:
        lines.append('')
        lines.append(say(lang, 'report.projects'))
        for row in summary['projects'][:5]:
            lines.append(say(lang, 'report.project', tokens=n(row['total_tokens']), sessions=count(lang, row['sessions'], 'session'),
                             project=project(row['project'])))
    if summary['largest_sessions']:
        lines.append('')
        lines.append(say(lang, 'report.largest'))
        for row in summary['largest_sessions']:
            burn = row['quota_burn_percent']
            used = ', '.join(say(lang, 'report.burn_item', window=window(w, lang), times=decimal(v / 100, lang, 2))
                             for w, v in sorted(burn.items()) if v) if burn else ''
            lines.append(say(lang, 'report.session', tokens=n(row['total_tokens']), agent=AGENTS.get(row['agent'], row['agent']),
                             date=_local(row['started'], lang)[:10] if row['started'] else '?', project=project(row['project'])))
            if used:
                lines.append(say(lang, 'report.burn') + used)
    quota = summary['quota']
    if quota['latest']:
        lines.append('')
        lines.append(say(lang, 'report.codex_quota', plan=say(lang, 'report.plan', quota['plan']) if quota['plan'] else '',
                         at=_local(quota['latest'][-1]['at'], lang)))
        for row in quota['latest']:
            current = next((item for item in windows if item.get('agent') == 'codex'
                            and item['window_minutes'] == row['window_minutes']), None)
            state = current['state'] if current else None
            key = 'report.reset' if state == 'reset' else 'report.stale' if state == 'stale' else 'report.quota_line'
            lines.append(say(lang, key, window=window(row['window_minutes'], lang), used=decimal(row['used_percent'], lang)))
    claude = [row for row in windows if row.get('agent') == 'claude-code']
    if claude:
        lines.append('')
        lines.append(say(lang, 'report.claude_quota', at=_local(max(row['at'] for row in claude), lang)))
        for row in claude:
            key = 'report.reset' if row['state'] == 'reset' else 'report.stale' if row['state'] == 'stale' else 'report.quota_line'
            lines.append(say(lang, key, window=window(row['window_minutes'], lang), used=decimal(row['used_percent'], lang)))
    rejected = summary['claude_limit_events'].get('rejected')
    if rejected:
        lines.append(say(lang, 'report.limit_hits', count(lang, rejected, 'time')))
    if not claude and 'claude-code' in summary['agents']:
        lines.append(say(lang, 'report.statusline_hint'))
    lines.append('')
    lines.append(say(lang, 'report.read', claude=count(lang, sources['claude_files'], 'claude_file'),
                     codex=count(lang, sources['codex_files'], 'codex_file')))
    if sources['skipped']:
        lines.append(say(lang, 'report.unreadable', count=count(lang, len(sources['skipped']), 'log_file'),
                         reasons=', '.join(sorted({reason for _, reason in sources['skipped']}))))
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(prog='pler report', description=__doc__.split('\n')[0])
    parser.add_argument('--days', type=int, default=30, help='Last N days (0 = everything); default 30')
    parser.add_argument('--json', action='store_true', help='Structured output')
    parser.add_argument('--sessions', action='store_true', help='With --json: include one row per session')
    parser.add_argument('--claude-dir', action='append', help='Claude Code projects folder (repeatable)')
    parser.add_argument('--codex-dir', action='append', help='Codex sessions folder (repeatable)')
    parser.add_argument('--lang', choices=LANGUAGES, help='en or tr; default: PLER_LANG, else the system language')
    args = parser.parse_args(argv)
    if args.days < 0:
        parser.error('--days must be 0 or more')
    sessions, sources = scan(args.claude_dir, args.codex_dir)
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=args.days) if args.days else None
    summary = summarize(sessions, since)
    rows = [s for s in sessions if since is None or (s.ended and s.ended >= since)]
    windows = outlook(sessions, now, sources['claude_quota'])
    lang = args.lang or language()
    trust=quality(rows,sources,lang)
    notes = insights(rows, windows, since, lang=lang,usage_complete=trust['tokens_complete'] and trust['attribution_complete'])
    sources['days'] = args.days
    if args.json:
        # The terminal and page share one allowlist for session metadata.
        from ..dashboard import session_view
        summary.pop('reported_cost_usd', None)  # a partial agent process figure is not a bill or a usage estimate
        summary.pop('days', None)  # whole-session totals are not a daily spending series
        summary['period']['mode'] = 'active_sessions_full_totals'
        for row in summary['projects']:
            row['project'] = label(None if row['project'] == 'unknown' else row['project'], lang=lang) or say(lang,'unknown_project')
        for row in summary['largest_sessions']:
            row['project'] = label(row['project'], lang=lang) or say(lang,'unknown_project')
        value = dict(summary,**provenance(),quality=trust,generated_at=now.isoformat(),outlook=windows, insights=notes,
                     sources=dict(claude_files=sources['claude_files'],codex_files=sources['codex_files'],days=args.days,
                                  skipped=[dict(reason=r) for _, r in sources['skipped']],claude_quota=len(sources['claude_quota'])))
        if args.sessions:
            value['sessions'] = [session_view(s,lang) for s in rows]
        print(json.dumps(value, ensure_ascii=False, indent=2))
    else:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        sys.stdout.write(render(summary, sources, notes, windows, lang))
        if trust['issues']:
            sys.stdout.write(say(lang,'quality.header')+'\n'+'\n'.join('  '+item['detail'] for item in trust['issues'])+'\n')
