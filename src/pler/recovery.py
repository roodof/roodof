"""One bounded, expiring manual recovery preview; existing history is never replaced."""
from datetime import datetime, timezone
import secrets
import threading
import time

from . import desktop_profiles as profiles
from .usage import backup


class Manager:
    def __init__(self, current=None, install=None, anchor=None, previous=None, issue=None):
        self.current = current
        self.install = install
        self.anchor = anchor
        self.previous = previous
        self.issue = issue
        self.lock = threading.RLock()
        self.preview = None
        self.restored = None
        self.timer = None
        self.closed = False
        self.switching = False

    def _discard(self):
        if self.timer is not None:
            self.timer.cancel(); self.timer = None
        self.preview = None

    def close(self):
        with self.lock:
            self.closed = True
            self._discard()

    def _ready(self):
        if self.closed or self.switching:
            raise backup.BackupError('busy')

    def state(self):
        with self.lock:
            value = dict(ok=True, current=str(self.current) if self.current else None,
                         remembered=self.anchor is not None, previous=str(self.previous) if self.previous else None,
                         issue=self.issue, switching=self.switching, preview=None, restored=self.restored)
            if self.preview:
                value['preview'] = {k: self.preview[k] for k in ('ticket', 'expected', 'summary', 'target', 'parent')}
            return value

    def inspect(self, data):
        with self.lock:
            self._ready()
            summary = backup.inspect(data)
            self._discard()
            ticket = secrets.token_hex(24)
            self.preview = dict(ticket=ticket, expected=secrets.token_hex(32), summary=summary,
                                target=None, parent=None, data=data, expires=time.monotonic()+600)
            def expire():
                with self.lock:
                    if self.preview and self.preview['ticket'] == ticket:
                        self._discard()
            self.timer = threading.Timer(600, expire)
            self.timer.daemon = True; self.timer.start()
            return self.state()

    def _selection(self, body):
        self._ready()
        if (self.preview is None or time.monotonic() >= self.preview['expires']
                or body.get('ticket') != self.preview['ticket'] or body.get('expected') != self.preview['expected']):
            raise backup.BackupError('conflict')
        return self.preview

    def act(self, body):
        with self.lock:
            action = body['action']
            if action == 'discard':
                self._selection(body); self._discard()
            elif action == 'destination':
                preview = self._selection(body)
                parent = profiles.folder(body['parent'])
                for forbidden in (self.current, self.install):
                    if forbidden and (parent == forbidden or forbidden in parent.parents):
                        raise backup.BackupError('unsafe_path')
                name = 'PLER-history-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-') + secrets.token_hex(4)
                preview['target'] = str(parent / name)
                preview['parent'] = str(parent)
                preview['expected'] = secrets.token_hex(32)
            elif action == 'restore':
                preview = self._selection(body)
                if body['confirmed'] is not True or not preview['target']:
                    raise backup.BackupError('invalid')
                try:
                    summary = backup.restore(preview['data'], preview['target'])
                except backup.BackupError as error:
                    # A post-publish sync error may leave a complete folder. Only
                    # expose it if every fixed restored byte matches the preview.
                    if error.code != 'io':raise
                    files, summary = backup._unpack(preview['data'])
                    target = profiles.folder(preview['target'])
                    if set(p.name for p in target.iterdir()) != {*files, backup.archive.GENERATION}:
                        raise error
                    for name, content in files.items():
                        if backup._read_bytes(target/name, backup.LIMITS[name]) != content:
                            raise error
                    summary = dict(summary, durability_uncertain=True)
                target = profiles.folder(preview['target'])
                stat = target.stat()
                self.restored = dict(target=str(target), summary=summary, token=secrets.token_hex(24))
                self._restored_identity = (stat.st_dev, stat.st_ino)
                self._discard()
            else:
                raise backup.BackupError('invalid')
            return self.state()

    def select(self, body):
        """Called only by a desktop owner, after it can guarantee a close/open handoff."""
        with self.lock:
            self._ready()
            if body['action'] == 'open':
                if not self.restored or body['token'] != self.restored['token']:
                    raise backup.BackupError('conflict')
                target = profiles.folder(self.restored['target'])
                stat = target.stat()
                if (stat.st_dev, stat.st_ino) != self._restored_identity:
                    raise backup.BackupError('conflict')
            elif body['action'] == 'previous' and self.previous:
                target = profiles.folder(self.previous)
            else:
                raise backup.BackupError('invalid')
            if body['confirmed'] is not True or self.current is None or target == self.current:
                raise backup.BackupError('invalid')
            # Validate durable data before changing any remembered selection. No original log is read.
            backup.inspect(backup.create(target))
            if self.anchor is not None:
                profiles.save(self.anchor, target, self.current)
            self.switching = True
            return target
