"""pler: what your AI coding agents used, read from their own logs on this computer.

  pler             open the usage page in your browser (stop with Ctrl+C or the page's Close button)
  pler report      the same summary in the terminal (pler report --help for options)
  pler statusline --install
                   show context and Claude subscription use in Claude Code's status line, and let PLER
                   read the Claude Code quota from there (asks before changing Claude Code's settings)
  pler --version

No model is called, nothing is sent anywhere, and the logs are only read.
"""
import argparse
import sys
import webbrowser

from . import __version__
from .i18n import language, say

PORT = 8765


def serve(port=PORT, browser=True, lang='en'):
    from .server import Server
    try:
        server = Server(port)
    except OSError:  # the usual port is taken, e.g. by another PLER window: take any free one
        server = Server(0)
    print(say(lang, 'cli.open', server.access_url), flush=True)
    if browser:
        webbrowser.open(server.access_url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    print(say(lang, 'cli.closed'))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if argv[:1] == ['report']:
        from .usage import main as report
        return report(argv[1:])
    if argv[:1] == ['statusline']:
        from .statusline import main as statusline
        return statusline(argv[1:])
    lang = language()
    parser = argparse.ArgumentParser(prog='pler', description=__doc__.split('\n')[0], epilog=say(lang, 'cli.epilog'))
    parser.add_argument('--version', action='version', version='PLER ' + __version__)
    parser.add_argument('--port', type=int, default=PORT, help=say(lang, 'cli.port', PORT))
    parser.add_argument('--no-browser', action='store_true', help=say(lang, 'cli.no_browser'))
    args = parser.parse_args(argv)
    return serve(args.port, not args.no_browser, lang)
