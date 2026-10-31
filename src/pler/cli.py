"""pler: what your AI coding agents used, read from their own logs on this computer.

  pler             open the usage page in your browser (stop with Ctrl+C or the page's Close button)
  pler report      the same summary in the terminal (pler report --help for options)
  pler statusline --install
                   show context and Claude subscription use in Claude Code's status line, and let PLER
                   read the Claude Code quota from there (asks before changing Claude Code's settings)
  pler demo        try the page with invented logs and an invented Git repository, not your own
  pler backup     create, check or restore a private local metadata backup
  pler --data-dir <folder>
                   open using the explicitly selected local PLER data folder
  pler --version

No model is called, nothing is sent anywhere, and the logs are only read.
"""
import argparse
import os
import sys
import webbrowser

from . import __version__
from .i18n import language, say

PORT = 8765


def serve(port=PORT, browser=True, lang='en', dashboard=None):
    from .server import Server
    try:
        server = Server(port, dashboard)
    except OSError:  # the usual port is taken, e.g. by another PLER window: take any free one
        server = Server(0, dashboard)
    print(say(lang, 'cli.open', server.access_url), flush=True)
    if browser:
        webbrowser.open(server.access_url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.dashboard.close(timeout=0)
        server.server_close()
    print(say(lang, 'cli.closed'))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    # One global folder option works before or after any existing subcommand.
    # Keep it process-local: a completed command never rewrites a saved profile
    # or changes another running PLER's folder.
    from .backup_cli import _Parser, _Arguments, _failure
    parser = _Parser(add_help=False, allow_abbrev=False)
    parser.add_argument('--data-dir', action='append')
    try:
        args, rest = parser.parse_known_args(argv)
    except _Arguments:
        return _failure('arguments', language(), '--json' in argv)
    if args.data_dir is None:
        return _main(rest)
    if len(args.data_dir) != 1:
        return _failure('arguments', language(), '--json' in rest)
    if any(option in rest for option in ('--help', '-h', '--version')):
        return _main(rest)
    if not args.data_dir[0]:
        return _failure('unsafe_path', language(), '--json' in rest)
    previous = os.environ.get('PLER_CACHE_DIR')
    os.environ['PLER_CACHE_DIR'] = args.data_dir[0]
    try:
        from .paths import cache_folder
        try:
            selected = cache_folder()
            if selected is not None and selected.exists() and not selected.is_dir():
                selected = None
        except (OSError, ValueError, RuntimeError):
            selected = None
        if selected is None:
            return _failure('unsafe_path', language(), '--json' in rest)
        os.environ['PLER_CACHE_DIR'] = str(selected)
        return _main(rest)
    finally:
        if previous is None:
            os.environ.pop('PLER_CACHE_DIR', None)
        else:
            os.environ['PLER_CACHE_DIR'] = previous


def _main(argv):
    if argv[:1] == ['backup']:
        from .backup_cli import main as backup
        return backup(argv[1:])
    if argv[:1] == ['report']:
        from .usage import main as report
        return report(argv[1:])
    if argv[:1] == ['statusline']:
        from .statusline import main as statusline
        return statusline(argv[1:])
    if argv[:1] == ['archive']:
        import json
        from .usage.archive import clear_archive,set_retention
        lang = language()
        parser = argparse.ArgumentParser(prog='pler archive', description=say(lang, 'archive.clear_help'))
        parser.add_argument('action', choices=('clear','on','off'))
        parser.add_argument('--json', action='store_true')
        args = parser.parse_args(argv[1:])
        result = clear_archive() if args.action=='clear' else set_retention(args.action=='on')
        public = {name: result.get(name) for name in ('ok', 'cleared_files', 'retention_enabled','errors')}
        if args.json:
            print(json.dumps(public))
        else:
            key=('archive.cleared' if args.action=='clear' else 'archive.retention_on' if args.action=='on' else 'archive.retention_off')
            print(say(lang,key if result.get('ok') else 'error.archive_clear'))
        return 0 if result.get('ok') else 1
    if argv[:1]==['cache']:
        import json
        from .usage.archive import reset_cache
        lang=language()
        parser=argparse.ArgumentParser(prog='pler cache',description=say(lang,'cache.reset_help'))
        parser.add_argument('action',choices=('reset',))
        parser.add_argument('--json',action='store_true')
        args=parser.parse_args(argv[1:])
        result=reset_cache()
        print(json.dumps(result) if args.json else say(lang,'cache.reset_done' if result.get('ok') else 'error.metadata_settings'))
        return 0 if result.get('ok') else 1
    lang = language()
    demo = argv[:1] == ['demo']
    parser = argparse.ArgumentParser(prog='pler demo' if demo else 'pler', description=__doc__.split('\n')[0],
                                     epilog=say(lang, 'cli.demo_epilog' if demo else 'cli.epilog'))
    parser.add_argument('--version', action='version', version='PLER ' + __version__)
    parser.add_argument('--port', type=int, default=PORT, help=say(lang, 'cli.port', PORT))
    parser.add_argument('--no-browser', action='store_true', help=say(lang, 'cli.no_browser'))
    # The global parser removes this option before routing. Advertising it here
    # keeps the normal page help discoverable without reading any local data.
    parser.add_argument('--data-dir', metavar='FOLDER', help=say(lang, 'backup.data_dir_help'))
    args = parser.parse_args(argv[1:] if demo else argv)
    if not demo:
        return serve(args.port, not args.no_browser, lang)
    from .dashboard import UsageDashboard
    from .demo import create
    from .usage import scan
    from .usage.verdicts import Memory
    from .usage.work_items import Memory as WorkMemory
    from .usage.plans import Memory as PlanMemory
    from .git_survival import Saved
    try:
        made = create()
    except ValueError as error:
        reason = {'no_folder': 'cli.demo_no_folder', 'not_demo': 'cli.demo_not_demo'}.get(str(error), 'cli.demo_failed')
        print(say(lang, reason), file=sys.stderr)
        return 1
    except OSError:
        print(say(lang, 'cli.demo_failed'), file=sys.stderr)
        return 1
    print(say(lang, 'cli.demo_ready', made['folder']), flush=True)

    def reader():
        # Only the demo folder is read, never the agents' own folders. Every read rewrites the invented
        # data relative to now, so its times and quota sample stay current during a long trial.
        fresh = create(made['folder'])
        sessions, sources = scan(fresh['claude'], fresh['codex'])
        return sessions, dict(sources, demo=True)
    # Verdicts, work labels and the Claude plan choice stay in memory, code counts in the demo folder; the real cache keeps only
    # those of your own sessions.
    return serve(args.port, not args.no_browser, lang,
                 UsageDashboard(reader, verdicts=Memory(), survival=Saved(made['folder']), work_items=WorkMemory(),
                                plan_choice=PlanMemory()))
