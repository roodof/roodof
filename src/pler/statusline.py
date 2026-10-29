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
from contextlib import contextmanager
import threading

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
LOCKFILE = 'claude-quota.lock'
LOCK_WAIT = .25
MAX_JOURNAL_BYTES = 4 << 20
MAX_LINE_BYTES = 2048
MAX_KEPT_ROWS = 8192
MAX_INPUT_BYTES = 1 << 20
_QUOTA_LOCK = threading.Lock()


@contextmanager
def _quota_locked(base):
    """One short process-shared writer critical section; failure never delays a status refresh indefinitely."""
    deadline = time.monotonic() + LOCK_WAIT
    if not _QUOTA_LOCK.acquire(timeout=LOCK_WAIT):
        raise OSError('quota writer busy')
    try:
        path = cache_file(LOCKFILE, base)
        if path is None:
            raise OSError('unsafe quota lock')
        path.parent.mkdir(parents=True, exist_ok=True)
        if cache_file(path.name, path.parent) != path:
            raise OSError('unsafe quota lock')
        with path.open('a+b') as stream:
            if os.name == 'nt':
                import msvcrt
                if stream.seek(0, 2) == 0:
                    stream.write(b'0'); stream.flush()
                def acquire():
                    stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                def release():
                    stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                def acquire():
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                def release():
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
            while True:
                try:
                    acquire(); break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(.005)
            try:
                yield
            finally:
                release()
    finally:
        _QUOTA_LOCK.release()


def _journal_rows(path):
    """Read only a bounded tail, skip long/partial rows, and project numbers before retaining them."""
    if cache_file(path.name, path.parent) != path:
        raise OSError('unsafe quota journal')
    with path.open('rb') as stream:
        size = stream.seek(0, 2)
        offset = max(0, size - MAX_JOURNAL_BYTES)
        stream.seek(offset)
        remaining, skipping = size - offset, bool(offset)
        while remaining:
            raw = stream.readline(min(MAX_LINE_BYTES + 1, remaining))
            if not raw:
                break
            remaining -= len(raw)
            complete = raw.endswith(b'\n') or remaining == 0
            if skipping or len(raw) > MAX_LINE_BYTES or not complete:
                skipping = not complete
                continue
            try:
                row = json.loads(raw)
                at = row.get('at') if isinstance(row, dict) else None
                windows = _windows(row.get('windows')) if isinstance(row, dict) else {}
                if _number(at) and 0 <= at <= 253402300799 and windows:
                    yield dict(at=at, windows=windows)
            except (ValueError, RecursionError, UnicodeError):
                continue


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
            lines = stream.read(512).splitlines()
        return json.loads(lines[-1]) if lines else None
    except (OSError, ValueError, RecursionError):
        return None


def _prune(path, now):
    """Called under the writer lock; retain a bounded recent tail of numeric samples."""
    temporary = None
    try:
        if cache_file(path.name, path.parent) != path:
            return
        if path.stat().st_size <= PRUNE_BYTES:
            return True
        from collections import deque
        rows, byte_count = deque(), 0
        for row in _journal_rows(path):
            if now - KEEP_DAYS * 86400 <= row['at'] <= 253402300799:
                encoded = json.dumps(row, separators=(',', ':')) + '\n'
                rows.append(encoded); byte_count += len(encoded)
                while len(rows) > MAX_KEPT_ROWS or byte_count > PRUNE_BYTES:
                    byte_count -= len(rows.popleft())
        if cache_file(path.name, path.parent) != path:
            return
        # Imported only when pruning a large file; the frequent status refresh stays lightweight.
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=str(path.parent),
                                         prefix=path.name + '.', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.writelines(rows)
        if cache_file(path.name, path.parent) != path:
            return
        os.replace(str(temporary), str(path))
        return True
    except (OSError, ValueError, AttributeError):
        return False
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
    now = now if now is not None else time.time()
    if not _number(now) or not 0 <= now <= 253402300799:
        return False
    now = int(now)
    try:
        # Revalidate the journal after its first read before creating even our lock file.
        # This preflight value is never used for deduplication; that read belongs under the OS lock.
        _last(path)
        if cache_file(FILE, path.parent) != path:
            return False
        with _quota_locked(path.parent):
            if cache_file(FILE, path.parent) != path:
                return False
            last = _last(path)
            if isinstance(last, dict) and last.get('windows') == found:
                return False
            if path.exists() and not _prune(path, now):
                return False
            if cache_file(FILE, path.parent) != path:
                return False
            with path.open('a+b') as stream:
                if stream.seek(0, 2):
                    stream.seek(-1, 2)
                    if stream.read(1) != b'\n':
                        stream.write(b'\n')
                stream.write((json.dumps(dict(at=now, windows=found), separators=(',', ':')) + '\n').encode('ascii'))
            _prune(path, now)
    except OSError:
        return False
    return True


def samples(folder=None):
    """(time, window minutes, used percent, resets_at) tuples, oldest first, in the shape forecast.py reads."""
    from datetime import datetime, timezone
    from collections import deque
    found = []
    path = cache_file(FILE, folder)
    if path is None:
        return []
    try:
        rows = deque(_journal_rows(path), maxlen=MAX_KEPT_ROWS)
        for row in rows:
            try:
                at = datetime.fromtimestamp(row['at'], timezone.utc)
                for minutes, (used, resets) in row['windows'].items():
                    found.append((at, int(minutes), float(used), datetime.fromtimestamp(resets, timezone.utc)))
            except (ValueError, KeyError, TypeError, AttributeError, OverflowError, OSError):
                continue
    except OSError:
        return []
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
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        data = json.loads(raw.decode('utf-8', 'replace') or '{}') if len(raw) <= MAX_INPUT_BYTES else {}
    except (ValueError, AttributeError, OSError, RecursionError):
        data = {}
    found = limits(data)
    record(found)
    sys.stdout.buffer.write(line(data, found).encode('utf-8'))
    sys.stdout.flush()
    return 0


if __name__ == '__main__':
    sys.exit(main())
