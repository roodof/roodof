"""Verified local history backups, restored only into a new folder.

No original agent log, setting, disposable cache, access token or executable is included.
The archive can contain private local paths and identifiers; this is not an anonymous export.
SHA-256 detects accidental damage, not a maliciously rewritten or untrusted backup.
"""
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import struct
import tempfile
import zipfile

from .. import __version__
from ..paths import cache_file, cache_folder, local_path, network
from ..reporting import PARSER_VERSION, SCHEMA_VERSION
from .. import statusline
from . import archive, preferences, verdicts, work_items, identities, budgets
from .records import _too_deep

FORMAT = 1
MANIFEST = 'manifest.json'
MAX_MANIFEST_BYTES = 16384
LIMITS = {archive.FILENAME: archive.MAX_BYTES,
          preferences.FILENAME: preferences.MAX_BYTES,
          verdicts.FILENAME: verdicts.MAX_BYTES,
          statusline.FILE: statusline.MAX_JOURNAL_BYTES,
          work_items.FILENAME: work_items.MAX_BYTES,
          identities.FILENAME: identities.MAX_BYTES,
          budgets.FILENAME: budgets.MAX_BYTES}
MAX_BUNDLE_BYTES = sum(LIMITS.values()) + MAX_MANIFEST_BYTES + 4096
MAX_ROWS = 500000
_HEX = re.compile('[a-f0-9]{64}')
_VERSION = re.compile(r'\d{1,4}\.\d{1,4}\.\d{1,4}')
_PARSER = re.compile(r'accounting-\d{4}-\d{2}-\d{2}\.\d{1,4}')


class BackupError(ValueError):
    """Only a fixed error code crosses a user interface; never exception paths or data."""
    def __init__(self, code='invalid'):
        self.code = code
        super().__init__(code)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BackupError('invalid')
        result[key] = value
    return result


def _json(data):
    try:
        text = data.decode('utf-8')
        if _too_deep(text):
            raise BackupError('limit')
        value = json.loads(text, object_pairs_hook=_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(BackupError('invalid')))
        if not isinstance(value, dict):
            raise BackupError('invalid')
        return value
    except BackupError:
        raise
    except (ValueError, UnicodeError, RecursionError, TypeError, OverflowError) as error:
        raise BackupError('invalid') from error


def _encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _path(value):
    try:
        # Reject network/device spellings before abspath/expanduser or filesystem access.
        if not value or network(value) or str(value).replace('/', '\\').startswith('\\??\\'):
            raise BackupError('unsafe_path')
        found = local_path(os.path.abspath(os.path.expanduser(str(value))))
        if found is None:
            raise BackupError('unsafe_path')
        return found
    except BackupError:
        raise
    except (OSError, ValueError, TypeError, RuntimeError) as error:
        raise BackupError('unsafe_path') from error


def _signature(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def _read_bytes(path, maximum, absent=False):
    observed = False
    try:
        if _path(path) != path:
            raise BackupError('unsafe_path')
        before = path.stat()
        observed = True
        if not stat.S_ISREG(before.st_mode):
            raise BackupError('unsafe_path')
        if before.st_size > maximum:
            raise BackupError('limit')
        with path.open('rb') as stream:
            opened = os.fstat(stream.fileno())
            if _signature(before) != _signature(opened):
                raise BackupError('io')
            data = stream.read(before.st_size + 1)
            after = os.fstat(stream.fileno())
        if (len(data) != before.st_size or _signature(after) != _signature(before)
                or _path(path) != path or _signature(path.stat()) != _signature(before)):
            raise BackupError('io')
        return data
    except FileNotFoundError as error:
        if absent and not observed:
            return None
        raise BackupError('io') from error
    except BackupError:
        raise
    except OSError as error:
        raise BackupError('io') from error


def read_file(path):
    """Read an explicitly chosen local backup, never more than its observed bounded size."""
    return _read_bytes(_path(path), MAX_BUNDLE_BYTES)


def _archive(data):
    value = _json(data)
    if (set(value) != {'format', 'files'} or type(value['format']) is not int
            or value['format'] != archive.FORMAT or not isinstance(value['files'], dict)):
        raise BackupError('unsupported')
    if len(value['files']) > archive.MAX_FILES:
        raise BackupError('limit')
    rows = 0
    for key, entry in value['files'].items():
        if (not isinstance(key, str) or not _HEX.fullmatch(key) or not isinstance(entry, dict)
                or not {'agent', 'source', 'root', 'reader_key', 'last_seen', 'rows', 'checksum'} <= set(entry)
                or set(entry) - {'agent', 'source', 'root', 'reader_key', 'last_seen', 'rows', 'checksum', 'incomplete'}
                or ('incomplete' in entry and type(entry['incomplete']) is not bool)):
            raise BackupError('invalid')
        if not isinstance(entry['rows'], list):
            raise BackupError('invalid')
        rows += len(entry['rows'])
        if len(entry['rows']) > 200000 or rows > MAX_ROWS:
            raise BackupError('limit')
        try:
            clean = archive._entry(entry)
            if (archive._identity(clean['agent'], clean['source']) != key
                    or archive.sanitize(clean['agent'], clean['rows']) != clean['rows']):
                raise BackupError('invalid')
        except BackupError:
            raise
        except (ValueError, TypeError, OverflowError, RecursionError, KeyError) as error:
            raise BackupError('invalid') from error
    return len(value['files'])


def _preferences(data):
    value = _json(data)
    if (set(value) != {'format', 'retention_enabled'} or type(value['format']) is not int
            or value['format'] != preferences.FORMAT or type(value['retention_enabled']) is not bool):
        raise BackupError('invalid')
    return value['retention_enabled']


def _verdicts(data):
    value = _json(data)
    if (set(value) != {'format', 'verdicts'} or type(value['format']) is not int
            or value['format'] != verdicts.FORMAT or not verdicts._valid(value['verdicts'])):
        raise BackupError('invalid')
    return len(value['verdicts'])


def _quota(data):
    count = 0
    for line in data.splitlines():
        if not line or len(line) > statusline.MAX_LINE_BYTES:
            raise BackupError('invalid')
        value = _json(line)
        at, windows = value.get('at'), value.get('windows')
        if (set(value) != {'at', 'windows'} or not statusline._number(at)
                or not 0 <= at <= 253402300799 or not isinstance(windows, dict)
                or not windows or windows != statusline._windows(windows)
                or any(type(pair) is not list or len(pair) != 2 for pair in windows.values())):
            raise BackupError('invalid')
        count += 1
        if count > statusline.MAX_KEPT_ROWS:
            raise BackupError('limit')
    return count


def _validate_files(files):
    result = dict(archive_files=0, verdicts=0, quota_samples=0, retention_enabled=True,
                  work_items=0,work_links=0)
    for name, data in files.items():
        if name not in LIMITS or len(data) > LIMITS[name]:
            raise BackupError('limit')
        if name == archive.FILENAME:
            result['archive_files'] = _archive(data)
        elif name == preferences.FILENAME:
            result['retention_enabled'] = _preferences(data)
        elif name == verdicts.FILENAME:
            result['verdicts'] = _verdicts(data)
        elif name == work_items.FILENAME:
            try: items=work_items.validate(data)
            except (ValueError,TypeError,UnicodeError,OverflowError) as error:
                raise BackupError('invalid') from error
            result['work_items']=len(items)
            result['work_links']=sum(len(item['sessions']) for item in items.values())
        elif name in (identities.FILENAME, budgets.FILENAME):
            try:
                (identities.validate if name == identities.FILENAME else budgets.validate_document)(data)
            except (ValueError, TypeError, UnicodeError, OverflowError) as error:
                raise BackupError('invalid') from error
        else:
            result['quota_samples'] = _quota(data)
    return result


def _manifest(value):
    fields = {'format', 'version', 'parser_version', 'schema_version', 'created_at', 'files'}
    if set(value) != fields:
        raise BackupError('invalid')
    if type(value['format']) is not int or value['format'] != FORMAT:
        raise BackupError('unsupported')
    if type(value['schema_version']) is not int or value['schema_version'] != SCHEMA_VERSION:
        raise BackupError('unsupported')
    version, parser = value['version'], value['parser_version']
    if (not isinstance(version, str) or not _VERSION.fullmatch(version)
            or tuple(map(int, version.split('.'))) > tuple(map(int, __version__.split('.')))
            or not isinstance(parser, str) or not _PARSER.fullmatch(parser)):
        raise BackupError('unsupported')
    try:
        def parser_key(text):
            day, revision = text[len('accounting-'):].rsplit('.', 1)
            return datetime.strptime(day, '%Y-%m-%d').date(), int(revision)
        if parser_key(parser) > parser_key(PARSER_VERSION):
            raise BackupError('unsupported')
    except (ValueError, OverflowError) as error:
        raise BackupError('unsupported') from error
    try:
        at = datetime.fromisoformat(value['created_at'])
        if at.tzinfo is None or at.utcoffset() is None:
            raise ValueError()
    except (ValueError, TypeError, OverflowError):
        raise BackupError('invalid')
    descriptors = value['files']
    if not isinstance(descriptors, dict) or set(descriptors) - set(LIMITS):
        raise BackupError('invalid')
    for name, item in descriptors.items():
        if (not isinstance(item, dict) or set(item) != {'bytes', 'sha256'}
                or type(item['bytes']) is not int or not 0 <= item['bytes'] <= LIMITS[name]
                or not isinstance(item['sha256'], str) or not _HEX.fullmatch(item['sha256'])):
            raise BackupError('invalid')
    return value


def _unpack(data):
    if type(data) is not bytes:
        raise BackupError('invalid')
    if len(data) > MAX_BUNDLE_BYTES:
        raise BackupError('limit')
    # Check the tiny ordinary EOCD before ZipFile constructs objects for every central entry.
    # Our seekable writer emits no comments, ZIP64, extra fields or data descriptors.
    if len(data) < 22 or data[-22:-18] != b'PK\x05\x06':
        raise BackupError('invalid')
    end = struct.unpack('<4s4H2IH', data[-22:])
    if (end[1] or end[2] or end[3] != end[4] or not 1 <= end[4] <= 1 + len(LIMITS)
            or end[7] or end[5] > (1 + len(LIMITS)) * (46 + max(map(len, (MANIFEST, *LIMITS))))
            or end[5] + end[6] != len(data) - 22):
        raise BackupError('invalid')
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as bundle:
            members = bundle.infolist()
            if not 1 <= len(members) <= 1 + len(LIMITS):
                raise BackupError('invalid')
            names = [item.filename for item in members]
            if len(set(names)) != len(names) or set(names) - {MANIFEST, *LIMITS} or MANIFEST not in names:
                raise BackupError('invalid')
            position = 0
            for item in sorted(members, key=lambda item: item.header_offset):
                maximum = MAX_MANIFEST_BYTES if item.filename == MANIFEST else LIMITS[item.filename]
                mode = item.external_attr >> 16
                if (item.compress_type != zipfile.ZIP_STORED or item.flag_bits & 1
                        or item.flag_bits & ~0x800 or item.is_dir()
                        or item.orig_filename != item.filename
                        or stat.S_IFMT(mode) not in (0, stat.S_IFREG) or item.extra or item.comment
                        or item.file_size > maximum or item.compress_size != item.file_size):
                    raise BackupError('invalid')
                if item.header_offset != position or position + 30 > end[6]:
                    raise BackupError('invalid')
                header = struct.unpack('<4s5H3I2H', data[position:position + 30])
                if (header[0] != b'PK\x03\x04' or header[2] != item.flag_bits or header[3] != 0
                        or header[6] != item.CRC or header[7] != item.file_size
                        or header[8] != item.file_size or header[10]):
                    raise BackupError('invalid')
                position += 30 + header[9] + header[10] + item.file_size
                if position > end[6]:
                    raise BackupError('invalid')
            if position != end[6]:
                raise BackupError('invalid')
            raw = {}
            for item in members:
                maximum = MAX_MANIFEST_BYTES if item.filename == MANIFEST else LIMITS[item.filename]
                with bundle.open(item) as stream:
                    raw[item.filename] = stream.read(maximum + 1)
                if len(raw[item.filename]) != item.file_size:
                    raise BackupError('invalid')
            value = _manifest(_json(raw.pop(MANIFEST)))
            if set(value['files']) != set(raw):
                raise BackupError('invalid')
            for name, content in raw.items():
                descriptor = value['files'][name]
                if len(content) != descriptor['bytes'] or hashlib.sha256(content).hexdigest() != descriptor['sha256']:
                    raise BackupError('invalid')
            summary = _validate_files(raw)
            summary.update({key: value[key] for key in ('format', 'version', 'parser_version', 'schema_version', 'created_at')})
            summary.update(files=len(raw), bytes=len(data))
            return raw, summary
    except BackupError:
        raise
    except (OSError, ValueError, zipfile.BadZipFile, EOFError, RuntimeError, NotImplementedError,
            OverflowError, RecursionError) as error:
        raise BackupError('invalid') from error


def inspect(data):
    """Verify the complete bundle and return only counts/provenance, without private paths or IDs."""
    return _unpack(data)[1]


def create(base=None):
    """Snapshot only PLER-owned durable metadata under both writers' locks."""
    base = cache_folder() if base is None else _path(base)
    if base is None:
        raise BackupError('unsafe_path')
    try:
        with archive._locked(base), statusline._quota_locked(base):
            files = {}
            for name, maximum in LIMITS.items():
                path = cache_file(name, base)
                if path is None:
                    raise BackupError('unsafe_path')
                content = _read_bytes(path, maximum, absent=True)
                if content is not None:
                    files[name] = content
            _validate_files(files)
    except BackupError:
        raise
    except OSError as error:
        raise BackupError('busy') from error
    value = dict(format=FORMAT, version=__version__, parser_version=PARSER_VERSION,
                 schema_version=SCHEMA_VERSION, created_at=datetime.now(timezone.utc).isoformat(timespec='seconds'),
                 files={name: dict(bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
                        for name, content in files.items()})
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as bundle:
        bundle.writestr(MANIFEST, _encoded(value))
        for name, content in files.items():
            bundle.writestr(name, content)
    data = output.getvalue()
    if len(data) > MAX_BUNDLE_BYTES:
        raise BackupError('limit')
    return data


def _sync_directory(path):
    if os.name == 'nt':
        return
    if _path(path) != path:
        raise BackupError('unsafe_path')
    descriptor = os.open(str(path), os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0) | getattr(os, 'O_NOFOLLOW', 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_new(path, data):
    if _path(path) != path:
        raise BackupError('unsafe_path')
    descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _cleanup_stage(stage):
    """Only fixed own files; never recursively delete a computed path."""
    if stage is None:
        return
    try:
        if _path(stage) != stage:
            return
        for name in (*LIMITS, archive.GENERATION, MANIFEST):
            item = cache_file(name, stage)
            if item is not None:
                item.unlink(missing_ok=True)
        stage.rmdir()  # fails rather than deleting an unexpected extra entry
    except (OSError, BackupError):
        pass


def restore(data, target):
    """Validate first, stage/fsync fixed files, then publish a new local directory.

    An existing folder is always refused. No current PLER data is replaced, no archived source is
    queried, and original reader keys remain unchanged. A post-publish directory-sync error can leave
    the complete new directory visible; an incomplete staged directory is never the target.
    """
    files, summary = _unpack(data)
    target = _path(target)
    stage = None
    published = False
    try:
        if target.exists():
            raise BackupError('exists')
        if not target.parent.is_dir() or _path(target.parent) != target.parent:
            raise BackupError('unsafe_path')
        stage = Path(tempfile.mkdtemp(prefix='.pler-restore-', dir=str(target.parent)))
        for name, content in files.items():
            _write_new(stage / name, content)
        _write_new(stage / archive.GENERATION, _encoded(dict(generation=1)))
        _sync_directory(stage)
        if _path(target) != target or target.exists():
            raise BackupError('exists')
        os.rename(str(stage), str(target))
        published = True
        _sync_directory(target.parent)
        return dict(summary)
    except BackupError:
        raise
    except FileExistsError as error:
        raise BackupError('exists') from error
    except OSError as error:
        raise BackupError('io') from error
    finally:
        if not published:
            _cleanup_stage(stage)


def write_file(data, path):
    """Save a validated backup without overwriting any existing file; fsync before success."""
    summary = inspect(data)
    path = _path(path)
    temporary = None
    try:
        if path.exists():
            raise BackupError('exists')
        if not path.parent.is_dir():
            raise BackupError('unsafe_path')
        # Windows rename refuses an existing target. POSIX rename may overwrite, so publish there
        # with an exclusive hard link instead. Both expose only the fully flushed file.
        descriptor, name = tempfile.mkstemp(prefix='.pler-backup-', suffix='.tmp', dir=str(path.parent))
        temporary = Path(name)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if _path(path) != path:
            raise BackupError('unsafe_path')
        if os.name == 'nt':
            os.rename(str(temporary), str(path))
        else:
            os.link(str(temporary), str(path))
        _sync_directory(path.parent)
        return summary
    except BackupError:
        raise
    except FileExistsError as error:
        raise BackupError('exists') from error
    except OSError as error:
        raise BackupError('io') from error
    finally:
        if temporary is not None:
            try:
                if _path(temporary) == temporary:
                    temporary.unlink(missing_ok=True)
            except (OSError, BackupError):
                pass
