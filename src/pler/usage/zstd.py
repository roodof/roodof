"""Read zstd-compressed logs (Codex compresses older rollouts): with the standard library on Python 3.14+, the
`zstandard` package when it is installed, and otherwise the plain-Python decoder in unzstd.py (slower, same
bytes). Nothing is installed and no other program is started."""
from . import unzstd


def _library_frames(module, data):
    """Incremental APIs may return partial output or stop after one frame; require EOF for every frame."""
    if not data:
        raise ValueError('zstd: empty compressed file')
    parts = []
    while data:
        stream = module.ZstdDecompressor().decompressobj()
        parts.append(stream.decompress(data))
        if not stream.eof or len(stream.unused_data) >= len(data):
            raise ValueError('zstd: incomplete compressed frame')
        data = stream.unused_data
    return b''.join(parts)


def _checked(decompress):
    """Library errors become ValueError, so one damaged file is listed as unreadable instead of stopping a scan."""
    def run(data):
        try:
            return decompress(data)
        except ValueError:
            raise
        except Exception as error:
            raise ValueError('zstd: the file could not be decompressed') from error
    return run


def decoder():
    """A function bytes -> bytes, and its name."""
    try:
        from compression import zstd  # Python 3.14+
        return _checked(zstd.decompress), 'standard library'
    except ImportError:
        pass
    try:
        import zstandard
        return _checked(lambda data: _library_frames(zstandard, data)), 'zstandard'
    except ImportError:
        pass
    return unzstd.decompress, 'plain python'
