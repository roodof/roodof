"""Bounded, read-only Git activity beside an agent session.

Only .git's HEAD reflog is read, never source files, objects or Git configuration.
Identities and commit messages are discarded. No Git program runs. Reflogs are local, incomplete
history; a coincident event proves neither authorship nor retained changes.
"""
from collections import Counter
from datetime import datetime, timezone
import os
from pathlib import Path
import re

from .paths import local_path, network

MAX_BYTES = 1 << 20
MAX_EVENTS = 20
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
            new = match[2]
            events.append(dict(at=moment, kind=_kind(message),
                               commit=new[:8].decode('ascii') if new.strip(b'0') else None))
        if not events:
            return dict(state='unavailable' if skipped else 'no_history')
        return dict(state='ready', events=events, truncated=bool(offset), skipped=skipped,
                    changed=(before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns))
    except (OSError, ValueError, RuntimeError):
        return dict(state='unavailable')


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
    selected = sorted((event for item, _ in ready for event in item['events'] if started <= event['at'] <= ended),
                      key=lambda event: event['at'], reverse=True)
    counts = Counter(event['kind'] for event in selected)
    beginnings = [min(event['at'] for event in item['events']) for item, _ in ready]
    limited = any(item['truncated'] or item['skipped'] or item['changed'] for item, _ in ready) \
        or max(beginnings) > started
    return dict(state='ready', matched_events=len(selected), counts=dict(counts),
                events=[dict(at=event['at'].isoformat(), kind=event['kind'], commit=event['commit'])
                        for event in selected[:MAX_EVENTS]],
                omitted_events=max(0, len(selected) - MAX_EVENTS), coverage_limited=limited,
                history_from=min(beginnings).isoformat(), repositories=len(ready),
                linked_by=sorted({reason for _, reasons in ready for reason in reasons}))
