"""Claude Code status line for PLER: shows context and subscription use, and keeps the subscription numbers.

Claude Code pipes a JSON description of the session to its status line command. For Pro and Max subscribers it
holds `rate_limits` (5-hour and 7-day used percentage and reset time), which Claude Code's own logs never record.
Only those numbers and the time are appended to claude-quota.jsonl in PLER's cache folder, and only when they
change; nothing else from the input is kept. It runs on every status refresh, so it imports almost nothing.

  pler statusline            what Claude Code runs: reads its JSON on stdin, prints one line
  pler statusline --install  adds itself to Claude Code's settings.json after asking; never replaces another one
  pler statusline --remove   takes itself out again
"""
import json
import math
import os
from pathlib import Path
import sys
import time

if __package__:
    from .i18n import YES, language, say
    from .paths import cache_file
else:  # run by path, as Claude Code's settings call it
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from pler.i18n import YES, language, say
    from pler.paths import cache_file

FILE = 'claude-quota.jsonl'
WINDOWS = (('five_hour', 300), ('seven_day', 10080))
KEEP_DAYS, PRUNE_BYTES = 35, 1 << 20


def _number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def _percent(value):
    return _number(value) and 0 <= value <= 100


def _windows(values):
    """Accept only the two supported windows with finite percentages and usable epochs."""
    clean = {}
    if isinstance(values, dict):
        for minutes in ('300', '10080'):
            pair = values.get(minutes)
            if (isinstance(pair, (list, tuple)) and len(pair) == 2 and _percent(pair[0])
                    and _number(pair[1]) and 0 < pair[1] <= 253402300799):
                clean[minutes] = [round(float(pair[0]), 2), int(pair[1])]
    return clean


def limits(data):
    """{"300" | "10080": [used percent, resets_at epoch seconds]} from the status line input; {} when absent."""
    rate = data.get('rate_limits') if isinstance(data, dict) else None
    found = {}
    for name, minutes in WINDOWS:
        window = rate.get(name) if isinstance(rate, dict) else None
        if isinstance(window, dict):
            found[str(minutes)] = [window.get('used_percentage'), window.get('resets_at')]
    return _windows(found)


def _last(path):
    try:
        if cache_file(path.name, path.parent) != path:
            return None
        with path.open('rb') as stream:
            stream.seek(0, 2)
            stream.seek(max(0, stream.tell() - 512))
            lines = stream.read().splitlines()
        return json.loads(lines[-1]) if lines else None
    except (OSError, ValueError):
        return None


def _prune(path, now):
    """Keeps the file small: past PRUNE_BYTES, only the last KEEP_DAYS days stay."""
    temporary = None
    try:
        if cache_file(path.name, path.parent) != path:
            return
        if path.stat().st_size <= PRUNE_BYTES:
            return
        rows = []
        for line in path.read_text('utf-8', errors='replace').splitlines():
            try:
                row = json.loads(line)
                at = row.get('at') if isinstance(row, dict) else None
                windows = _windows(row.get('windows')) if isinstance(row, dict) else {}
                if _number(at) and now - KEEP_DAYS * 86400 <= at <= 253402300799 and windows:
                    rows.append(json.dumps(dict(at=at, windows=windows), separators=(',', ':')))
            except ValueError:
                continue
        if cache_file(path.name, path.parent) != path:
            return
        # Imported only when pruning a large file; the frequent status refresh stays lightweight.
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=str(path.parent),
                                         prefix=path.name + '.', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(''.join(line + '\n' for line in rows))
        if cache_file(path.name, path.parent) != path:
            return
        os.replace(str(temporary), str(path))
    except (OSError, ValueError, AttributeError):
        pass
    finally:
        if temporary is not None:
            try:
                if cache_file(temporary.name, temporary.parent) == temporary:
                    temporary.unlink(missing_ok=True)
            except OSError:
                pass


def record(found, folder=None, now=None):
    """Appends {"at": epoch seconds, "windows": found} unless the last line says the same. Never raises."""
    found = _windows(found)
    if not found:
        return False
    path = cache_file(FILE, folder)
    if path is None:
        return False
    now = int(now if now is not None else time.time())
    last = _last(path)
    if isinstance(last, dict) and last.get('windows') == found:
        return False
    try:
        if cache_file(FILE, path.parent) != path:
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        if cache_file(FILE, path.parent) != path:
            return False
        with path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(dict(at=now, windows=found), separators=(',', ':')) + '\n')
    except OSError:
        return False
    _prune(path, now)
    return True


def samples(folder=None):
    """(time, window minutes, used percent, resets_at) tuples, oldest first, in the shape forecast.py reads."""
    from datetime import datetime, timezone
    found = []
    path = cache_file(FILE, folder)
    if path is None:
        return found
    try:
        lines = path.read_text('utf-8', errors='replace').splitlines()
    except OSError:
        return found
    for line in lines:
        try:
            row = json.loads(line)
            if not isinstance(row, dict) or not _number(row.get('at')) or not 0 <= row['at'] <= 253402300799:
                continue
            at = datetime.fromtimestamp(row['at'], timezone.utc)
            for minutes, (used, resets) in _windows(row.get('windows')).items():
                found.append((at, int(minutes), float(used), datetime.fromtimestamp(resets, timezone.utc)))
        except (ValueError, KeyError, TypeError, AttributeError, OverflowError, OSError):
            continue
    return sorted(found, key=lambda sample: sample[0])


def line(data, found, lang=None):
    """The text Claude Code shows: context use, then the subscription windows (ctx 37% · 5h 24% · week 41%)."""
    lang = lang or language()
    parts = []
    context = data.get('context_window') if isinstance(data, dict) else None
    if isinstance(context, dict) and _percent(context.get('used_percentage')):
        parts.append(say(lang, 'status.context', round(context['used_percentage'])))
    found = _windows(found)
    parts.extend(say(lang, 'status.' + minutes, round(found[minutes][0])) for minutes in ('300', '10080') if minutes in found)
    return ' · '.join(parts) or 'PLER'


def settings_path():
    configured = os.environ.get('CLAUDE_CONFIG_DIR')
    base = Path(configured.split(',')[0].strip()).expanduser() if configured else Path.home() / '.claude'
    return base / 'settings.json'


def command():
    """How Claude Code should start this file: this Python by absolute path (works installed or not), isolated
    and without site packages, which also starts faster on every refresh."""
    return '"%s" -I -S "%s"' % (Path(sys.executable).as_posix(), Path(__file__).resolve().as_posix())


def _ours(value):
    return value == dict(type='command', command=command())


def _load(path):
    if not path.exists():
        return {}, None
    original = path.read_bytes()
    settings = json.loads(original.decode('utf-8-sig'))
    if not isinstance(settings, dict):
        raise ValueError('not an object')
    return settings, original


def _save(path, settings, original):
    from tempfile import NamedTemporaryFile
    current = path.read_bytes() if path.exists() else None
    if current != original:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = path.with_name(path.name + '.pler-backup')
    if original is not None and not backup.exists():
        with backup.open('xb') as stream:
            stream.write(original)
    temporary = None
    try:
        with NamedTemporaryFile(mode='w', encoding='utf-8', dir=str(path.parent), prefix=path.name+'.', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(settings, ensure_ascii=False, indent=2) + '\n')
        if (path.read_bytes() if path.exists() else None) != original:
            return False
        os.replace(str(temporary), str(path))
        return True
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def install(path=None, ask=input, lang=None):
    path, lang = Path(path or settings_path()), lang or language()
    try:
        settings, original = _load(path)
    except (OSError, ValueError, UnicodeError):
        print(say(lang, 'status.unreadable', path))
        return 1
    current, wanted = settings.get('statusLine'), dict(type='command', command=command())
    if current and not _ours(current):
        print(say(lang, 'status.other', json.dumps(current, ensure_ascii=False)))
        print(say(lang, 'status.pipe', command()))
        return 1
    if current == wanted:
        print(say(lang, 'status.installed', path))
        return 0
    print(say(lang, 'status.plan', path=path, setting=json.dumps(dict(statusLine=wanted), ensure_ascii=False, indent=2)))
    print(say(lang, 'status.explain'))
    if ask(say(lang, 'status.ask')).strip().lower() not in YES.get(lang, YES['en']):
        print(say(lang, 'status.unchanged'))
        return 1
    settings['statusLine'] = wanted
    try:
        saved = _save(path, settings, original)
    except OSError:
        print(say(lang, 'status.write_failed'))
        return 1
    if not saved:
        print(say(lang, 'status.changed'))
        return 1
    print(say(lang, 'status.added'))
    return 0


def remove(path=None, lang=None):
    path, lang = Path(path or settings_path()), lang or language()
    try:
        settings, original = _load(path)
    except (OSError, ValueError, UnicodeError):
        print(say(lang, 'status.unreadable_short', path))
        return 1
    if not _ours(settings.get('statusLine')):
        print(say(lang, 'status.not_installed'))
        return 0
    del settings['statusLine']
    try:
        saved = _save(path, settings, original)
    except OSError:
        print(say(lang, 'status.write_failed'))
        return 1
    if not saved:
        print(say(lang, 'status.changed'))
        return 1
    print(say(lang, 'status.removed', path))
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if argv == ['--install']:
        return install()
    if argv == ['--remove']:
        return remove()
    if argv:
        print(__doc__.strip())
        return 2
    try:
        data = json.loads(sys.stdin.buffer.read().decode('utf-8', 'replace') or '{}')
    except (ValueError, AttributeError, OSError):
        data = {}
    found = limits(data)
    record(found)
    sys.stdout.buffer.write(line(data, found).encode('utf-8'))
    sys.stdout.flush()
    return 0


if __name__ == '__main__':
    sys.exit(main())
