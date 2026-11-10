"""Invented Claude Code and Codex logs and a small Git repository, for trying Roodof without private data.

`pler demo` writes them into a `demo` folder inside Roodof's own cache folder (never into the agents'
folders), then opens the page reading only that folder. Every name, number and time is invented; times
are relative to now so the period filters have something to show. The pilot tasks in docs/PILOT.md can
all be done with it: two agents, several projects, a quota forecast, a data-quality warning, sessions
that started in a parent folder, and commits that are, or are no longer, on a branch.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import random
import shutil
import zlib

from .paths import cache_folder

MARKER = 'PLER-DEMO.txt'


def _iso(moment):
    return moment.strftime('%Y-%m-%dT%H:%M:%S.000Z')


def _write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows), 'utf-8')


class _Repository:
    """A Git repository written byte by byte: loose files, folders and commits, a branch and a HEAD reflog."""

    def __init__(self, root):
        self.git, self.reflog, self.head = root / '.git', [], None
        (self.git / 'objects').mkdir(parents=True)
        (self.git / 'refs' / 'heads').mkdir(parents=True)
        (self.git / 'logs').mkdir()
        (self.git / 'HEAD').write_text('ref: refs/heads/main\n', 'ascii')

    def _put(self, kind, body):
        raw = kind + b' %d\0' % len(body) + body
        key = hashlib.sha1(raw).hexdigest()
        folder = self.git / 'objects' / key[:2]
        folder.mkdir(exist_ok=True)
        (folder / key[2:]).write_bytes(zlib.compress(raw))
        return key

    def _tree(self, files):
        entries, folders = [], {}
        for name, lines in files.items():
            first, _, rest = name.partition('/')
            if rest:
                folders.setdefault(first, {})[rest] = lines
            else:
                entries.append((b'100644', first.encode(), self._put(b'blob', ('\n'.join(lines) + '\n').encode())))
        entries += [(b'40000', name.encode(), self._tree(inner)) for name, inner in folders.items()]
        entries.sort(key=lambda entry: entry[1] + (b'/' if entry[0] == b'40000' else b''))
        return self._put(b'tree', b''.join(mode + b' ' + name + b'\0' + bytes.fromhex(key) for mode, name, key in entries))

    def commit(self, moment, parent, action='commit', files=None):
        """`files` is the invented content of the whole repository at this commit: {path: [lines]}."""
        seconds = int(moment.timestamp())
        body = ('tree %s\n' % self._tree(files or {}) + ('parent %s\n' % parent if parent else '')
                + 'author Demo <demo@example.invalid> %d +0000\ncommitter Demo <demo@example.invalid> %d +0000\n\n'
                  'Invented demo change\n' % (seconds, seconds)).encode()
        key = self._put(b'commit', body)
        self.reflog.append('%s %s Demo <demo@example.invalid> %d +0000\t%s: Invented demo change\n'
                           % (self.head or '0' * 40, key, seconds, action))
        self.head = key
        return key

    def save(self):
        (self.git / 'refs' / 'heads' / 'main').write_text(self.head + '\n', 'ascii')
        (self.git / 'logs' / 'HEAD').write_text(''.join(self.reflog), 'utf-8')


def _claude(folder, name, cwd, start, calls, edits=(), seed=1, model='claude-opus-5-5', tests=()):
    """A Claude Code session: prompts, replies with usage, Edit tool calls on the given files, and test
    commands (command, failed) with their tool answers."""
    rng, rows, moment, tests = random.Random(seed), [], start, list(tests)
    for index in range(calls):
        if index % 6 == 0:
            rows.append(dict(type='user', uuid='%s-p%d' % (name, index), sessionId=name, timestamp=_iso(moment),
                             cwd=str(cwd), message=dict(role='user', content='Invented request')))
        moment += timedelta(seconds=rng.randint(20, 90))
        usage = dict(input_tokens=rng.randint(3, 40), cache_read_input_tokens=rng.randint(30000, 60000) + index * 900,
                     cache_creation_input_tokens=rng.randint(500, 3000), output_tokens=rng.randint(150, 1400))
        blocks = [dict(type='text', text='Invented reply')]
        if edits and index % 4 == 1:
            target = edits[(index // 4) % len(edits)]
            blocks.append(dict(type='tool_use', name='Edit', id='%s-t%d' % (name, index),
                               input=dict(file_path=str(target), old_string='a', new_string='b')))
        answer = None
        if tests and index % 10 == 7:
            command, failed = tests.pop(0)
            blocks.append(dict(type='tool_use', name='Bash', id='%s-b%d' % (name, index), input=dict(command=command)))
            answer = dict(type='user', sessionId=name, timestamp=_iso(moment + timedelta(seconds=15)), cwd=str(cwd),
                          message=dict(role='user', content=[dict(type='tool_result', tool_use_id='%s-b%d' % (name, index),
                                                                  content='Invented output', is_error=failed)]))
        rows.append(dict(type='assistant', sessionId=name, requestId='%s-r%d' % (name, index), timestamp=_iso(moment),
                         cwd=str(cwd), version='2.1.300',
                         message=dict(id='%s-m%d' % (name, index), model=model, role='assistant', content=blocks, usage=usage)))
        if answer:
            rows.append(answer)
    _write(folder / 'projects' / cwd.name / (name + '.jsonl'), rows)
    return moment


def _codex(folder, name, cwd, start, calls, patches=(), quota=None, week=None, cumulative=False, seed=2, tests=()):
    """A Codex rollout: per-response usage (or only cumulative totals, as older CLIs wrote), patches, quota and
    finished test/build commands (command, exit code)."""
    rng, moment, tests = random.Random(seed), start, list(tests)
    rows = [dict(timestamp=_iso(moment), type='session_meta', payload=dict(id=name, cwd=str(cwd), cli_version='0.163.0')),
            dict(timestamp=_iso(moment), type='turn_context', payload=dict(model='gpt-6.1-sol', effort='medium', cwd=str(cwd)))]
    totals = dict(input_tokens=0, cached_input_tokens=0, output_tokens=0, reasoning_output_tokens=0)
    for index in range(calls):
        if index % 5 == 0:
            rows.append(dict(timestamp=_iso(moment), type='event_msg', payload=dict(type='task_started', turn_id='%s-u%d' % (name, index))))
        moment += timedelta(seconds=rng.randint(15, 70))
        cached = rng.randint(20000, 45000) + index * 700
        usage = dict(input_tokens=cached + rng.randint(200, 2500), cached_input_tokens=cached,
                     output_tokens=rng.randint(200, 1800), reasoning_output_tokens=rng.randint(0, 150))
        for key in totals:
            totals[key] += usage[key]
        if cumulative:
            rows.append(dict(timestamp=_iso(moment), type='event_msg', payload=dict(type='token_count', info=dict(total_token_usage=dict(totals)))))
        else:
            rows.append(dict(timestamp=_iso(moment), type='token_usage_record', payload=dict(response_id='%s-r%d' % (name, index), usage=usage)))
        if patches and index % 3 == 1:
            target = patches[(index // 3) % len(patches)]
            text = '*** Begin Patch\n*** Update File: %s\n@@\n-a\n+b\n*** End Patch' % target
            rows.append(dict(timestamp=_iso(moment), type='response_item', payload=dict(
                type='custom_tool_call', name='exec', call_id='%s-c%d' % (name, index),
                input='const result = await tools.apply_patch(%s);' % json.dumps(text))))
        if tests and index % 9 == 5:
            command, code = tests.pop(0)
            rows.append(dict(timestamp=_iso(moment), type='event_msg', payload=dict(type='item_completed', item=dict(
                type='CommandExecution', id='%s-x%d' % (name, index), command=command, exit_code=code,
                status='completed' if code == 0 else 'failed', aggregated_output='Invented output'))))
        if quota and index % 3 == 2:
            # quota: (five-hour start %, rise per call, weekly start %, rise per call); week: weekly reset
            rows.append(dict(timestamp=_iso(moment), type='event_msg', payload=dict(type='token_count', info=None, rate_limits=dict(
                plan_type='plus',
                primary=dict(used_percent=round(min(quota[0] + index * quota[1], 99.0), 1), window_minutes=300,
                             resets_at=int((start + timedelta(hours=4)).timestamp())),
                secondary=dict(used_percent=round(min(quota[2] + index * quota[3], 99.0), 1), window_minutes=10080,
                               resets_at=int(week.timestamp()))))))
        if index % 5 == 4:
            rows.append(dict(timestamp=_iso(moment), type='event_msg', payload=dict(type='task_complete', turn_id='%s-u%d' % (name, index - 4), duration_ms=rng.randint(20000, 240000))))
    day = start.strftime('%Y/%m/%d')
    _write(folder / 'sessions' / day / ('rollout-%s-%s.jsonl' % (start.strftime('%Y-%m-%dT%H-%M-%S'), name)), rows)
    return moment


def create(folder=None, now=None):
    """Write the invented data into `folder` (default: the demo folder in Roodof's cache) and return its paths.

    An existing folder is replaced only when it holds the demo marker; anything else is refused."""
    base = Path(folder) if folder is not None else (cache_folder() / 'demo' if cache_folder() is not None else None)
    if base is None:
        raise ValueError('no_folder')   # no safe local cache folder (e.g. PLER_CACHE_DIR on a network)
    if base.exists():
        if not (base / MARKER).is_file():
            raise ValueError('not_demo')  # never delete a folder Roodof did not create
        shutil.rmtree(base)
    base.mkdir(parents=True)
    (base / MARKER).write_text('Invented Roodof demo data. Safe to delete.\n', 'utf-8')
    now = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    work = base / 'work'
    shop, api, docs = work / 'shop', work / 'api', work / 'docs'
    for project in (shop / 'src', shop / 'tests', api / 'src', docs):
        project.mkdir(parents=True)
    claude, codex = base / 'claude', base / 'codex'
    repo = _Repository(shop)
    cart = ['def total(items):', '    return sum(item.price for item in items)']
    first = repo.commit(now - timedelta(days=20), None, 'commit (initial)', {'src/cart.py': cart, 'README.md': ['Invented shop']})
    discount = ['', 'def discount(total, code):', '    if code == "SPRING":', '        return total * 0.9', '    return total']
    tests = ['from cart import total', '', 'def test_total():', '    assert total([]) == 0']

    # Claude Code: a checkout feature in the shop repository, two days ago. One commit is later amended.
    start = now - timedelta(days=2, hours=3)
    end = _claude(claude, 'demo-checkout', shop, start, 42, [shop / 'src' / 'cart.py', shop / 'tests' / 'test_cart.py'], seed=11,
                  tests=[('python -m pytest -q', True), ('python -m pytest -q', False)])
    files = {'src/cart.py': cart + discount, 'README.md': ['Invented shop'], 'tests/test_cart.py': tests}
    kept = repo.commit(start + (end - start) / 3, first, files=files)
    repo.commit(start + (end - start) * 2 / 3, kept, files=dict(files, **{'src/cart.py': cart + discount + ['# draft']}))  # amended away
    amended = dict(files, **{'tests/test_cart.py': tests + ['', 'def test_discount():', '    assert discount(100, "SPRING") == 90']})
    repo.commit(end - timedelta(minutes=1), kept, 'commit (amend)', amended)
    # Codex: started in the parent folder, it patched the shop repository yesterday and committed once.
    week = now + timedelta(days=3, hours=4)  # when the invented weekly quota resets
    start = now - timedelta(days=1, hours=5)
    end = _codex(codex, 'demo-codex-shop', work, start, 36, [shop / 'src' / 'payment.py', shop / 'README.md'],
                 quota=(20, 0.8, 38, 0.2), week=week, seed=21,
                 tests=[(['bash', '-lc', 'python -m pytest -q'], 0), (['bash', '-lc', 'python -m pytest -q'], 1)])
    # The Codex change rewrites one line of the Claude Code discount, so not every added line is still in place.
    repo.commit(end - timedelta(minutes=2), repo.head, files=dict(amended, **{
        'src/cart.py': cart + [line.replace('0.9', 'RATE') for line in discount] + ['RATE = 0.85'],
        'src/payment.py': ['def pay(order, card):', '    return card.charge(order.total)']}))
    repo.save()
    # Codex, just now: its five-hour quota climbs fast, so the page forecasts it filling before it resets.
    _codex(codex, 'demo-codex-api', api, now - timedelta(minutes=45), 40, [api / 'src' / 'routes.py'],
           quota=(52, 0.5, 47, 0.1), week=week, seed=22,
           tests=[(['bash', '-lc', 'go build ./...'], 0), (['bash', '-lc', 'go test ./...'], 0)])
    # Claude Code: three shorter API sessions and one very long one (no Git repository there).
    for index, days in enumerate((9, 6, 4)):
        _claude(claude, 'demo-api-%d' % index, api, now - timedelta(days=days, hours=2), 18 + index * 6, [api / 'src' / 'routes.py'],
                seed=30 + index, tests=[('npm test 2>&1 | tail -20', False)] if index == 1 else ())
    _claude(claude, 'demo-api-long', api, now - timedelta(hours=9), 130, [api / 'src' / 'models.py'], seed=40)
    # Codex, older CLI format: only cumulative totals, so the per-call split is unknown (a quality warning).
    _codex(codex, 'demo-codex-docs', docs, now - timedelta(days=3), 14, cumulative=True,
           quota=(10, 0.5, 21, 0.3), week=week, seed=50)
    return dict(folder=base, claude=[claude / 'projects'], codex=[codex / 'sessions'])
