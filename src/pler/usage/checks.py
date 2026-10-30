"""Which shell commands an agent ran were tests or builds, and can their exit code be trusted?

The command text is read only here, in memory, while a log is read; it is never stored, cached, archived
or shown. Only the kind ('test' or 'build') and whether the command's exit code is that check's own
survive. A check's exit code is its own when it is the last step of the command line: a later pipe
(`| tail`), step (`; echo`), alternative (`||`) or a background job would replace or hide it.
"""
import re

TEST, BUILD = 'test', 'build'
MAX_COMMAND = 20000   # characters left after here-document bodies are removed
MAX_INPUT = 4 * 1024 * 1024
_SHELLS = {'bash', 'sh', 'zsh', 'dash', 'pwsh', 'powershell', 'cmd'}
_WRAPPERS = {'timeout', 'time', 'env', 'nice', 'nohup', 'stdbuf', 'xvfb-run', 'npx', 'pnpx', 'bunx', 'uv', 'uvx', 'poetry',
             'pipenv', 'pdm', 'hatch', 'rye', 'conda', 'mamba', 'bundle', 'exec', 'command', 'call', 'start-process'}
_WRAPPER_WORDS = {'run', 'exec', '--', '-n', '--no-install', '--yes', '-y', '/c', '/b', '/wait'}
_PYTHON = re.compile(r'(python|py|pypy)(\d+(\.\d+)*)?w?$')
_TEST_SCRIPT = re.compile(r'(^|[\\/])(test[_\-\w]*|[\w\-]*[_\-.](test|tests|spec))\.(py|c?js|mjs|ts|rb|php|sh|ps1)$|(^|[\\/])run_?tests?\.\w+$', re.I)
_TOOLS = {
    'pytest': TEST, 'py.test': TEST, 'tox': TEST, 'nox': TEST, 'nose2': TEST, 'jest': TEST, 'vitest': TEST, 'mocha': TEST,
    'ava': TEST, 'jasmine': TEST, 'karma': TEST, 'rspec': TEST, 'phpunit': TEST, 'pest': TEST, 'paratest': TEST,
    'ctest': TEST, 'invoke-pester': TEST, 'tsc': BUILD, 'javac': BUILD, 'kotlinc': BUILD, 'rustc': BUILD, 'gcc': BUILD,
    'g++': BUILD, 'cc': BUILD, 'c++': BUILD, 'clang': BUILD, 'clang++': BUILD, 'cl': BUILD, 'swiftc': BUILD,
    'msbuild': BUILD, 'ninja': BUILD, 'scons': BUILD, 'bazel': None, 'buck2': None}
# Tool -> {first argument: kind}; a tool listed here counts only with one of these arguments.
_VERBS = {
    'go': {'test': TEST, 'build': BUILD, 'vet': BUILD},
    'cargo': {'test': TEST, 'nextest': TEST, 'build': BUILD, 'check': BUILD, 'clippy': BUILD},
    'dotnet': {'test': TEST, 'build': BUILD},
    'deno': {'test': TEST, 'check': BUILD},
    'bun': {'test': TEST},
    'mix': {'test': TEST, 'compile': BUILD},
    'swift': {'test': TEST, 'build': BUILD},
    'flutter': {'test': TEST, 'build': BUILD},
    'dart': {'test': TEST, 'compile': BUILD},
    'stack': {'test': TEST, 'build': BUILD},
    'cabal': {'test': TEST, 'build': BUILD},
    'meson': {'test': TEST, 'compile': BUILD},
    'rake': {'test': TEST, 'spec': TEST},
    'rails': {'test': TEST},
    'composer': {'test': TEST},
    'playwright': {'test': TEST},
    'cypress': {'run': TEST},
    'bazel': {'test': TEST, 'build': BUILD},
    'buck2': {'test': TEST, 'build': BUILD},
}
_MAKE = {'make', 'gmake', 'nmake', 'mingw32-make'}
_MAKE_NOT_BUILD = {'clean', 'distclean', 'install', 'uninstall', 'format', 'fmt', 'lint', 'help', 'docs', 'doc', 'run', 'dist'}
_PACKAGE = {'npm', 'pnpm', 'yarn'}


# Matched in C, so a long command costs no Python loop per character. An unterminated quote runs to the end.
_WORD = re.compile(r'''(?:"(?:[^"\\]|\\.)*"?|'[^']*'?|[^\s"'])+''', re.S)
_TOKEN = re.compile(r'''"(?:[^"\\]|\\.)*"?|'[^']*'?|\\.|&&|\|\||[;\n|&]|[^"'\\;\n|&]+''', re.S)
_SEPARATORS = {'&&', '||', ';', '\n', '|'}
# Here-document and here-string bodies are data, not commands: `<<'EOF' ... EOF`, PowerShell `@' ... '@`.
_HEREDOC = re.compile(r'''(<<-?[ \t]*(['"]?)([A-Za-z_][A-Za-z0-9_]*)\2)([^\n]*)\n.*?\n[ \t]*\3[ \t]*(?=\n|$)''', re.S)
_HERESTRING = re.compile(r'''@(['"])\r?\n.*?\r?\n\1@''', re.S)
_MAX_WORDS = 40


def _words(segment, maximum=_MAX_WORDS):
    """The first words of one shell step; quote characters are removed, nothing is evaluated."""
    words = []
    for match in _WORD.finditer(segment):
        words.append(match.group().replace('"', '').replace("'", ''))
        if len(words) >= maximum:
            break
    return words


def _steps(script):
    """[(operator before, text)] for the top-level steps of a shell line; quoted text is never split."""
    steps, current, operator = [], [], None
    for match in _TOKEN.finditer(script):
        token = match.group()
        if token in _SEPARATORS:
            steps.append((operator, ''.join(current))); current, operator = [], token
        elif token == '&':
            text = ''.join(current)
            # `cmd &` runs in the background; `2>&1`, `&>` and PowerShell's leading call operator are not steps.
            if text.strip() and not text.rstrip().endswith(('>', '<')) and script[match.end():match.end() + 1] != '>':
                steps.append((operator, text)); current, operator = [], '&'
            else:
                current.append(token)
        else:
            current.append(token)
    steps.append((operator, ''.join(current)))
    return [(op, text) for op, text in steps if text.strip() or op == '&']


def _program(word):
    name = word.replace('\\', '/').rsplit('/', 1)[-1].lower()
    for suffix in ('.exe', '.cmd', '.bat', '.ps1', '.sh'):
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    return name


def _unwrap(command):
    """The script inside `bash -lc "..."`, `powershell -Command "..."` or an argument list; else the line."""
    if isinstance(command, list):
        if not all(isinstance(word, str) for word in command) or not command:
            return None
        if _program(command[0]) in _SHELLS and len(command) >= 3 and command[-2].lower() in ('-c', '-lc', '-command', '/c'):
            return command[-1]
        return ' '.join(('"%s"' % word if not word or any(c.isspace() for c in word) else word) for word in command)
    if not isinstance(command, str):
        return None
    words = _words(command[:2000])
    if len(words) >= 3 and _program(words[0]) in _SHELLS:
        for position, word in enumerate(words[1:], 1):
            if word.lower() in ('-c', '-lc', '-command', '/c'):
                marker = command.lower().find(word.lower(), len(words[0]))
                rest = command[marker + len(word):].strip() if marker >= 0 else ''
                if len(rest) >= 2 and rest[0] == rest[-1] and rest[0] in '"\'':
                    rest = rest[1:-1]
                return rest
            if not word.startswith('-'):
                break
    return command


def _command(words):
    """The tool and its arguments after the supported environment/wrapper prefixes."""
    while words and (re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*=.*', words[0]) or words[0] in ('&', '.')):
        words = words[1:]
    while words and _program(words[0]) in _WRAPPERS:
        words = words[1:]
        while words and (words[0].lower() in _WRAPPER_WORDS or re.fullmatch(r'-?[\d.]+[smh]?|-[A-Za-z-]+(=\S+)?', words[0])
                         or re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*=.*', words[0])):
            words = words[1:]
    return (_program(words[0]), words[1:]) if words else ('', [])


def _non_running(words):
    """Known inspection/dry-run modes are not evidence that a check ran.

    Match complete options, never pieces of paths or argument values. This only
    recognises explicit modes; a zero exit still cannot establish how many tests ran.
    """
    name, rest = _command(words)
    options = {word.split('=', 1)[0] for word in rest if word.startswith('--')}
    if options & {'--help', '--version', '--dry-run', '--dryrun', '--collect-only', '--co',
                  '--list-tests', '--listTests', '--list-test-names-only', '--list-suites',
                  '--collectonly', '--fixtures', '--fixtures-per-test', '--setup-plan', '--setup-only'}:
        return True
    # javac -h generates headers while compiling; it is not that tool's help switch.
    if name != 'javac' and '-h' in rest:
        return True
    if '-V' in rest or (name in ('javac', 'java') and '-version' in rest):
        return True
    if name in _MAKE:
        return (any(word in ('--just-print', '--recon', '--question') for word in rest)
                or any(re.fullmatch(r'-[A-Za-z]*[nq][A-Za-z]*', word) for word in rest)
                or name == 'nmake' and any(word.lower() in ('/n', '/q', '/?') for word in rest))
    if name == 'ctest' and ('-N' in rest or '--show-only' in options):
        return True
    if name == 'go' and any(word in ('-c', '-n', '-list') or word.startswith('-list=') for word in rest):
        return True
    if name == 'cargo' and ('--no-run' in options or rest[:2] == ['nextest', 'list'] or '--list' in options):
        return True
    if name in ('vitest', 'playwright') and 'list' in rest:
        return True
    if name in ('gradle', 'gradlew') and '-m' in rest:
        return True
    if name == 'tox' and (any(word in ('-l', '-a', '--listenvs', '--listenvs-all', '--showconfig') for word in rest)
                          or rest[:1] in (['list'], ['config'])):
        return True
    if name == 'nox' and any(word in ('-l', '--list', '--list-sessions') for word in rest):
        return True
    if name in ('ninja', 'scons', 'rake') and '-n' in rest:
        return True
    if name == 'tsc' and options & {'--showConfig', '--listFilesOnly'}:
        return True
    if name == 'javac' and '-help' in rest:
        return True
    if name == 'cl' and '/?' in rest:
        return True
    if name in ('mvn', 'mvnw') and any(re.fullmatch(r'-D(?:skipTests|maven\.test\.skip)(?:=true)?', word) for word in rest):
        return True
    if name == 'dotnet' and any(word.lower() in ('-t', '/listtests', '/listtests:true') for word in rest):
        return True
    return False


def _kind(words):
    name, rest = _command(words)
    first = next((word.lower() for word in rest if not word.startswith('-')), '')
    if _PYTHON.fullmatch(name):
        for position, word in enumerate(rest):
            if word == '-m' and position + 1 < len(rest):
                module = rest[position + 1].lower()
                return TEST if module in ('pytest', 'unittest', 'nose2', 'tox', 'nox', 'py.test') else BUILD if module == 'build' else None
            if word in ('-c', '-'):
                return None
            if not word.startswith('-'):
                if _program(word) in ('manage.py', 'setup.py') and position + 1 < len(rest):
                    verb = rest[position + 1].lower()
                    return TEST if verb == 'test' else BUILD if verb in ('build', 'build_ext') else None
                return TEST if _TEST_SCRIPT.search(word) else None
        return None
    if name == 'node':
        if '--test' in rest:
            return TEST
        script = next((word for word in rest if not word.startswith('-')), '')
        return TEST if _TEST_SCRIPT.search(script) else None
    if name in _PACKAGE:
        verbs = [word.lower() for word in rest if not word.startswith('-')]
        if verbs[:1] in (['run'], ['run-script']):
            verbs = verbs[1:]
        script = verbs[0] if verbs else ''
        return (TEST if script in ('test', 't') or script.startswith(('test:', 'test-')) else
                BUILD if script == 'build' or script.startswith(('build:', 'build-')) else None)
    if name in _MAKE:
        targets = [word.lower() for word in rest if not word.startswith('-') and '=' not in word]
        if any(target in ('test', 'tests', 'check') for target in targets):
            return TEST
        return BUILD if not any(target in _MAKE_NOT_BUILD for target in targets) else None
    if name == 'cmake':
        return BUILD if '--build' in rest else None
    if name in ('mvn', 'mvnw'):
        goals = {word.lower() for word in rest if not word.startswith('-')}
        return TEST if goals & {'test', 'verify'} else BUILD if goals & {'compile', 'package', 'install'} else None
    if name in ('gradle', 'gradlew'):
        tasks = {word.lower().rsplit(':', 1)[-1] for word in rest if not word.startswith('-')}
        return TEST if tasks & {'test', 'check'} else BUILD if tasks & {'build', 'assemble', 'compilejava', 'compilekotlin'} else None
    if name == 'zig':
        return TEST if rest[:2] == ['build', 'test'] or first == 'test' else BUILD if first == 'build' else None
    if name in _VERBS:
        return _VERBS[name].get(first)
    if name == 'ninja' and first == 'test':
        return TEST
    return _TOOLS.get(name)


_FIRST = re.compile(r'''\s*(?:&\s*)?(?:"([^"]*)"|'([^']*)'|([^\s"']+))''')
_CANDIDATES = (set(_TOOLS) | set(_VERBS) | _MAKE | _PACKAGE | _WRAPPERS
               | {'node', 'cmake', 'mvn', 'mvnw', 'gradle', 'gradlew', 'zig', '.'})


def _candidate(text):
    """A cheap look at the first word, so most steps never need splitting into words."""
    match = _FIRST.match(text)
    if not match:
        return False
    name = _program(next(group for group in match.groups() if group is not None))
    return name in _CANDIDATES or '=' in name or _PYTHON.fullmatch(name) is not None


def classify(command):
    """None for an ordinary command; else dict(kind='test'|'build', known=bool) for a test or build check."""
    script = _unwrap(command)
    if not isinstance(script, str) or len(script) > MAX_INPUT:
        return None
    if '<<' in script:
        script = _HEREDOC.sub(r'\1\4', script)
    if "@'" in script or '@"' in script:
        script = _HERESTRING.sub("''", script)
    script = script.replace('\\\n', ' ')
    if not script.strip() or len(script) > MAX_COMMAND:
        return None
    steps = _steps(script)
    found = None
    for position, (operator, text) in enumerate(steps):
        words = _words(text, _MAX_WORDS + 1) if _candidate(text) else []
        truncated = len(words) > _MAX_WORDS
        kind = _kind(words[:_MAX_WORDS]) if words and not _non_running(words) else None
        if kind is not None:
            found = position, kind, truncated
    if found is None:
        return None
    position, kind, truncated = found
    last = position == len(steps) - 1
    hidden = any(operator in ('||', '&') for operator, _ in steps[1:position + 1])
    background = position + 1 < len(steps) and steps[position + 1][0] == '&'
    return dict(kind=kind, known=last and not hidden and not background and not truncated)


def outcome(check, failed):
    """'passed', 'failed' or 'unknown' for a classified check and the tool call's failure flag (or None)."""
    if not check or not check.get('known') or type(failed) is not bool:
        return 'unknown'
    return 'failed' if failed else 'passed'


def summary(rows):
    """Per kind: sessions, runs, outcomes, and how the selected sessions' last visible check ended."""
    from .records import total
    result = {}
    for kind in (TEST, BUILD):
        chosen = [session for session in rows if kind in session.checks]
        last = [session.checks[kind]['last'] for session in chosen]
        result[kind] = dict(sessions=len(chosen), runs=sum(s.checks[kind]['runs'] for s in chosen),
                            passed=sum(s.checks[kind]['passed'] for s in chosen),
                            failed=sum(s.checks[kind]['failed'] for s in chosen),
                            ended_passed=last.count('passed'), ended_failed=last.count('failed'), ended_unknown=last.count(None),
                            ended_failed_tokens=sum(total(s.tokens) for s in chosen if s.checks[kind]['last'] == 'failed'))
    return result
