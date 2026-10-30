"""Bounded, read-only Git activity beside an agent session.

.git's HEAD reflog gives the events. For commits recorded during a session, git_objects.py then checks
whether they are still on a branch, reading only commit parents and times, and git_survival.py counts how
many of the lines they added are still in place at HEAD, reading the changed files in memory only. Git
configuration is never read. Identities, commit messages, file names and contents are discarded; only
counts remain. No Git program runs. Reflogs are local, incomplete history; a coincident event does not
prove authorship.
"""
from collections import Counter
from datetime import datetime, timezone
import os
from pathlib import Path
import re

from .git_objects import on_branch
from .git_survival import survival
from .paths import local_path, network

MAX_BYTES = 1 << 20
MAX_EVENTS = 20
CREATED = ('commit', 'amend', 'merge')   # events whose destination is a commit made at that moment
_HEX = rb'[0-9a-f]{40}(?:[0-9a-f]{24})?'
_HEADER = re.compile(rb'^(' + _HEX + rb') (' + _HEX + rb') .+ ([0-9]{1,12}) [+-][0-9]{4}$')


def _local_path(value):
    return local_path(value)


def _kind(message):
    # Names and messages after the action prefix are deliberately discarded.
    action = message.split(b':', 1)[0]
    if action == b'commit (amend)':
        return 'amend'
    if action in (b'commit', b'commit (initial)'):
        return 'commit'
    for name in ('reset', 'checkout', 'merge', 'rebase'):
        if action == name.encode() or action.startswith(name.encode() + b' '):
            return name
    return 'other'


def read_repository(project):
    """Small metadata snapshot, keyed internally by the already-known project.

    Worktrees and submodules with a gitdir file use their own HEAD log. UNC
    paths, missing folders, relative paths and a home-folder repository are skipped.
    Error messages and private paths are never returned.
    """
    try:
        root = _local_path(project)
        if root is None or root == Path(os.path.abspath(Path.home())):
            return dict(state='not_repository')
        marker = _local_path(root / '.git')
        if marker is None:
            return dict(state='unavailable')
        if marker.is_dir():
            directory = _local_path(marker)
        elif marker.is_file():
            with marker.open('rb') as stream:
                pointer = stream.read(4097)
            if len(pointer) > 4096 or not pointer.startswith(b'gitdir: '):
                return dict(state='unavailable')
            target = pointer[8:].decode('utf-8').strip()
            # Reject a network pointer before joining/resolving it.
            if not target or network(target):
                return dict(state='unavailable')
            directory = _local_path(root / target)
        else:
            return dict(state='not_repository')
        if directory is None:
            return dict(state='unavailable')
        path = directory / 'logs' / 'HEAD'
        # Refuse symlinks/junctions before following any metadata path.
        path = _local_path(path)
        if path is None:
            return dict(state='unavailable')
        try:
            with path.open('rb') as stream:
                before = path.stat()
                stream.seek(0, 2)
                offset = max(0, stream.tell() - MAX_BYTES)
                stream.seek(offset)
                raw = stream.read(MAX_BYTES)
                after = path.stat()
        except FileNotFoundError:
            return dict(state='no_history')
        if offset:
            raw = raw.partition(b'\n')[2]  # first line can be cut in half
        events, skipped = [], 0
        for line in raw.splitlines():
            header, separator, message = line.partition(b'\t')
            match = _HEADER.fullmatch(header) if separator else None
            if not match or len(match[1]) != len(match[2]):
                skipped += 1
                continue
            try:
                moment = datetime.fromtimestamp(int(match[3]), timezone.utc)
            except (ValueError, OverflowError, OSError):
                skipped += 1
                continue
            new = match[2] if match[2].strip(b'0') else None
            # The full id stays internal (branch check); only eight characters are ever projected.
            events.append(dict(at=moment, kind=_kind(message), commit=new[:8].decode('ascii') if new else None,
                               full=new.decode('ascii') if new else None))
        if not events:
            return dict(state='unavailable' if skipped else 'no_history')
        return dict(state='ready', events=events, truncated=bool(offset), skipped=skipped, directory=str(directory),
                    changed=(before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns))
    except (OSError, ValueError, RuntimeError):
        return dict(state='unavailable')


def check_branches(snapshot, windows):
    """Mark which commits recorded inside the given session windows are still on a branch."""
    try:
        if not snapshot or snapshot.get('state') != 'ready' or not snapshot.get('directory'):
            return
        created = {event['full']: event['at'] for event in snapshot['events']
                   if event['kind'] in CREATED and event.get('full')
                   and any(start <= event['at'] <= end for start, end in windows)}
        if created:
            snapshot['branch'] = on_branch(snapshot['directory'], created, since=min(created.values()).timestamp())
    except (OSError, ValueError, RuntimeError, MemoryError):
        snapshot.pop('branch', None)  # unknown, never a guess


def check_survival(snapshot, store=None):
    """Count, for commits found on a branch, how many of their added lines HEAD still has. `store` (a
    git_survival.Saved) keeps the counts across restarts."""
    try:
        if not snapshot or snapshot.get('state') != 'ready' or not snapshot.get('branch'):
            return
        kept = [commit for commit, value in snapshot['branch'].items() if value]
        times = [event['at'] for event in snapshot['events'] if event.get('full') in kept]
        if kept:
            snapshot['survival'] = survival(snapshot['directory'], kept, since=min(times).timestamp() if times else None,
                                            store=store)
    except (OSError, ValueError, RuntimeError, MemoryError):
        snapshot.pop('survival', None)  # unknown, never a guess


def _lines(measured):
    """Sum of per-commit survival counts; None entries are commits that could not be measured."""
    values = [value for value in measured if value is not None]
    return dict(added=sum(v['added'] for v in values), kept=sum(v['kept'] for v in values), commits=len(values),
                unmeasured=len(measured) - len(values))


def session_activity(snapshot, started, ended):
    """Explicit public projection. Never expose the raw log, identity, message or repository path.

    `snapshot` is one repository's snapshot, or a list of (snapshot, reasons) pairs: every repository the
    session is linked to, through its working folder or the files it edited. An empty list means no
    folder of the session is a repository."""
    if snapshot is None:
        return dict(state='not_scanned')
    linked = snapshot if isinstance(snapshot, list) else [(snapshot, ('working_folder',))]
    ready = [(item, reasons) for item, reasons in linked if item and item['state'] == 'ready']
    if not ready:
        states = {item['state'] if item else 'not_scanned' for item, _ in linked}
        for state in ('unavailable', 'no_history', 'not_scanned', 'not_repository'):
            if state in states or state == 'not_repository':
                return dict(state=state)
    if not started or not ended or ended < started:
        return dict(state='unknown_time')
    selected = sorted(((event, item.get('branch', {}).get(event.get('full')) if event['kind'] in CREATED else None)
                       for item, _ in ready for event in item['events'] if started <= event['at'] <= ended),
                      key=lambda pair: pair[0]['at'], reverse=True)
    counts = Counter(event['kind'] for event, _ in selected)
    states = [kept for event, kept in selected if event['kind'] in CREATED]
    measured = {}
    for item, _ in ready:
        for event in item['events']:
            if event['kind'] in CREATED and event.get('full') and started <= event['at'] <= ended \
                    and item.get('branch', {}).get(event['full']):
                measured[event['full']] = item.get('survival', {}).get(event['full'])
    beginnings = [min(event['at'] for event in item['events']) for item, _ in ready]
    limited = any(item['truncated'] or item['skipped'] or item['changed'] for item, _ in ready) \
        or max(beginnings) > started
    return dict(state='ready', matched_events=len(selected), counts=dict(counts),
                events=[dict(at=event['at'].isoformat(), kind=event['kind'], commit=event['commit'],
                             **(dict(on_branch=kept) if event['kind'] in CREATED else {}))
                        for event, kept in selected[:MAX_EVENTS]],
                omitted_events=max(0, len(selected) - MAX_EVENTS), coverage_limited=limited,
                history_from=min(beginnings).isoformat(), repositories=len(ready),
                linked_by=sorted({reason for _, reasons in ready for reason in reasons}),
                commits=dict(total=len(states), on_branch=states.count(True), off_branch=states.count(False),
                             unknown=sum(kept is None for kept in states)),
                **(dict(lines=_lines(list(measured.values()))) if measured else {}))
