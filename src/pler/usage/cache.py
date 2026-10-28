"""Per-user cache of what a reader extracted from a log file, reused while the file is unchanged (same size
and modification time). It holds the reader's numbers and metadata only, never prompt or output text, and it
lives in the user's cache folder, not next to the logs. PLER_CACHE_DIR moves it."""
import hashlib
import json
import os
from pathlib import Path
import tempfile

from ..paths import cache_folder as folder, cache_file


def _checksum(rows):
    raw = json.dumps(rows, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


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
        self.key, self.old, self.new, self.signatures = key, {}, {}, {}
        self.historical,self.historical_key={},None
        if self.path is None:
            return
        try:
            data = json.loads(self.path.read_text('utf-8'))
            if isinstance(data.get('files'),dict):
                self.historical,self.historical_key=data['files'],data.get('key')
            if data.get('key') == key and isinstance(data.get('files'), dict):
                self.old = data['files']
        except (OSError, ValueError, AttributeError):
            pass

    def get(self, path):
        if self.path is None:
            return None
        stat = os.stat(path)
        name, signature = str(path), [stat.st_size, stat.st_mtime_ns]
        self.signatures[name] = signature
        entry = self.old.get(name)
        if isinstance(entry, dict) and entry.get('signature') == signature:
            rows = entry.get('rows')
            try:
                valid = (isinstance(rows, list) and all(isinstance(row, dict) for row in rows)
                         and entry.get('checksum') == _checksum(rows))
            except (TypeError, ValueError, OverflowError):
                valid = False
            if valid:
                self.new[name] = entry
                return rows
        return None

    def checksum(self, path):
        """The checksum of the rows this read got or stored for `path`, or None."""
        entry = self.new.get(str(path)) if self.path is not None else None
        return entry.get('checksum') if isinstance(entry, dict) else None

    def put(self, path, rows):
        if self.path is None:
            return
        name = str(path)
        if name in self.signatures:
            try:
                stat = os.stat(path)
                if [stat.st_size, stat.st_mtime_ns] != self.signatures[name]:
                    return  # a growing/replaced log must be re-read on the next scan
                checksum = _checksum(rows)
            except (OSError, TypeError, ValueError, OverflowError):
                return  # a cache must never prevent reading the original
            self.new[name] = dict(signature=self.signatures[name], rows=rows, checksum=checksum)

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
            # through the Python iterator. Keep the same JSON representation and atomic replace.
            encoded = json.dumps(dict(key=self.key, files=self.new), separators=(',', ':'))
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
