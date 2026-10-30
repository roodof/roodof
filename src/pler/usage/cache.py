"""Per-user cache of what a reader extracted from a log file, reused while the file is unchanged (same size
and modification time). A plain log that has only grown since is read on from where the last read ended
(see grown()). It holds the reader's numbers and metadata only, never prompt or output text, and it lives in
the user's cache folder, not next to the logs. PLER_CACHE_DIR moves it."""
import hashlib
import json
import os
from pathlib import Path
import tempfile

from ..paths import cache_folder as folder, cache_file
from . import input_limits

PREFIX_FORMAT = 'sha256-prefix-v1'


class ResumeChanged(Exception):
    """The path no longer opens the file whose prefix was verified."""


def resume_matches(stream,resume):
    info=os.fstat(stream.fileno())
    return (_identity(info)==resume.get('file') and
            [info.st_size,info.st_mtime_ns]==resume.get('observed'))


def _identity(info):
    """A file identity includes its device; unavailable identities never justify a cache hit."""
    return [info.st_dev,info.st_ino] if info.st_ino else None


def _checksum(rows):
    raw = json.dumps(rows, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _encode(key, files):
    """One JSON object whose `files` bytes carry a digest, so an intact file needs one hash, not one per entry."""
    body = json.dumps(files, separators=(',', ':'))
    return '{"key":%s,"digest":"%s","files":%s}' % (json.dumps(key), hashlib.sha256(body.encode('utf-8')).hexdigest(), body)


def _intact(text, data):
    """True only for a file exactly as _encode wrote it; anything else falls back to per-entry checksums."""
    digest = data.get('digest')
    if not isinstance(digest, str) or len(digest) != 64:
        return False
    prefix = '{"key":%s,"digest":"%s","files":' % (json.dumps(data.get('key')), digest)
    if not (text.startswith(prefix) and text.endswith('}')):
        return False
    return hashlib.sha256(text[len(prefix):-1].encode('utf-8')).hexdigest() == digest


def _prefix(path, offset, identity):
    """Verify every old byte before appending, with bounded memory and cancellable reads."""
    if identity is None or not 0 < offset <= input_limits.MAX_SOURCE_BYTES:return None
    digest=hashlib.sha256();remaining=offset
    with open(str(path), 'rb') as stream:
        before=os.fstat(stream.fileno())
        if _identity(before)!=identity or before.st_size<offset:return None
        source=input_limits.Source(stream)
        while remaining:
            input_limits.checkpoint()
            data=source.read(min(input_limits.CHUNK_BYTES,remaining))
            if not data:return None
            digest.update(data);remaining-=len(data)
        after=os.fstat(stream.fileno())
        if (_identity(after),after.st_size,after.st_mtime_ns)!=(_identity(before),before.st_size,before.st_mtime_ns):return None
    return digest.hexdigest()


def version(*modules):
    """Changes whenever a reader's source changes, so an edited reader never sees its old extracts."""
    digest = hashlib.sha256()
    for module in modules:
        digest.update(Path(module.__file__).read_bytes())
    return digest.hexdigest()[:16]


class FileCache:
    def __init__(self, name, key):
        base = folder()
        self.path = cache_file(name + '.json', base) if base is not None else None
        self.key, self.old, self.new, self.signatures, self.files = key, {}, {}, {}, {}
        self.historical,self.historical_key={},None
        self.intact = False
        if self.path is None:
            return
        try:
            size=self.path.stat().st_size
            if size>input_limits.MAX_CACHE_BYTES:return
            with self.path.open('rb') as stream:data=stream.read(size+1)
            if len(data)!=size:return
            text=data.decode('utf-8')
            data = json.loads(text)
            if isinstance(data.get('files'),dict):
                self.historical,self.historical_key=data['files'],data.get('key')
            if data.get('key') == key and isinstance(data.get('files'), dict):
                self.old = data['files']
                self.intact = _intact(text, data)
        except (OSError, ValueError, AttributeError, RecursionError):
            pass

    def get(self, path):
        input_limits.checkpoint()
        if self.path is None:
            return None
        stat = os.stat(path)
        name, signature = str(path), [stat.st_size, stat.st_mtime_ns]
        self.signatures[name], self.files[name] = signature, _identity(stat)
        entry = self.old.get(name)
        if (self.files[name] is not None and isinstance(entry,dict) and
                entry.get('signature')==signature and entry.get('file')==self.files[name]):
            rows = self._stored(entry)
            if rows is not None:
                self.new[name] = entry
                return rows
        return None

    def _stored(self, entry):
        rows = entry.get('rows')
        try:
            # put() stored each checksum from its rows; an intact file proves they still match.
            valid = (isinstance(rows, list) and all(isinstance(row, dict) for row in rows)
                     and isinstance(entry.get('checksum'), str)
                     and (self.intact or entry.get('checksum') == _checksum(rows)))
        except (TypeError, ValueError, OverflowError, RecursionError):
            valid = False
        return rows if valid else None

    def grown(self, path):
        """After get() missed: (rows, resume) of the last read of `path` when the file has only grown since,
        else None. Only a read that ended at a line end leaves a resume point. All old bytes are hashed,
        and the reader rechecks the newly opened descriptor against this observation before seeking.
        Missing identity, an old verification format or any mismatch means a full read."""
        input_limits.checkpoint()
        name = str(path)
        entry = self.old.get(name)
        resume = entry.get('resume') if isinstance(entry, dict) else None
        if name not in self.signatures or not isinstance(resume, dict):
            return None
        offset, window = resume.get('offset'), resume.get('window')
        if (type(offset) is not int or not 0 < offset < self.signatures[name][0] or not isinstance(window, str)
                or resume.get('file') != self.files[name] or self.files[name] is None
                or resume.get('verification')!=PREFIX_FORMAT):
            return None
        rows = self._stored(entry)
        if rows is None:
            return None
        try:
            same = _prefix(path, offset, self.files[name]) == window
        except (OSError,ValueError):
            return None
        return (rows,dict(resume,observed=list(self.signatures[name]))) if same else None

    def checksum(self, path):
        """The checksum of the rows this read got or stored for `path`, or None."""
        entry = self.new.get(str(path)) if self.path is not None else None
        return entry.get('checksum') if isinstance(entry, dict) else None

    def put(self, path, rows, resume=None):
        """`resume`: where a later read of this plain log may go on (offset, the reader's projected size and
        state), when the read ended at a line end."""
        if self.path is None:
            return
        name = str(path)
        if name in self.signatures:
            try:
                stat = os.stat(path)
                if ([stat.st_size,stat.st_mtime_ns]!=self.signatures[name] or
                        _identity(stat)!=self.files[name] or self.files[name] is None):
                    return  # a growing/replaced log must be re-read on the next scan
                checksum = _checksum(rows)
                entry = dict(signature=self.signatures[name], file=self.files[name], rows=rows, checksum=checksum)
                if resume and type(resume.get('offset')) is int and 0 < resume['offset'] <= stat.st_size:
                    window = _prefix(path,resume['offset'],self.files[name])
                    if window is not None:
                        entry['resume'] = dict(resume,file=self.files[name],window=window,verification=PREFIX_FORMAT)
                final=os.stat(path)
                if ([final.st_size,final.st_mtime_ns]!=self.signatures[name] or _identity(final)!=self.files[name]):return
            except (OSError, TypeError, ValueError, OverflowError):
                return  # a cache must never prevent reading the original
            self.new[name] = entry

    def save(self):
        """Keeps only the files of this scan. A cache that cannot be written is skipped, never an error."""
        if self.path is None or self.new == self.old:
            return
        temporary = None
        try:
            if cache_file(self.path.name, self.path.parent) != self.path:
                return
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if cache_file(self.path.name, self.path.parent) != self.path:
                return
            # dumps uses the standard library's fast encoder; dump would emit many tiny writes
            # through the Python iterator. Keep one JSON object and an atomic replace.
            encoded = _encode(self.key, self.new)
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=str(self.path.parent),
                                             prefix=self.path.name+'.',suffix='.tmp',delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(encoded)
            os.replace(str(temporary), str(self.path))
        except (OSError, MemoryError):
            pass
        finally:
            if temporary is not None:
                try:
                    if cache_file(temporary.name, temporary.parent) == temporary:
                        temporary.unlink(missing_ok=True)
                except OSError:
                    pass
