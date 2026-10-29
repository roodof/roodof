"""Read zstd-compressed logs (Codex compresses older rollouts): with the standard library on Python 3.14+, the
`zstandard` package when it is installed, and otherwise the plain-Python decoder in unzstd.py (slower, same
bytes). Nothing is installed and no other program is started."""
from . import unzstd
from ..runtime import checkpoint, ScanCancelled
from .input_limits import ReadLimitExceeded

MAX_WINDOW=128*1024*1024


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
        except ScanCancelled:
            raise
        except Exception as error:
            raise ValueError('zstd: the file could not be decompressed') from error
    return run


def decoder():
    """A function bytes -> bytes, and its name."""
    try:
        from compression import zstd  # Python 3.14+
        result=_checked(zstd.decompress)
        result.iter_chunks=iter_chunks
        return result, 'standard library'
    except ImportError:
        pass
    try:
        import zstandard
        result=_checked(lambda data: _library_frames(zstandard, data))
        result.iter_chunks=iter_chunks
        return result, 'zstandard'
    except ImportError:
        pass
    unzstd.decompress.iter_chunks=iter_chunks
    return unzstd.decompress, 'plain python'


class _Frames:
    """Validate encoded frame boundaries without buffering blocks or trusting a native EOF shortcut."""
    def __init__(self,maximum):
        self.maximum=maximum
        self.state,self.need,self.header='magic',4,bytearray()
        self.seen=False
        self.flags=self.last=0

    def _next(self,state,size):
        self.state,self.need=state,size

    def _block_end(self):
        if not self.last:self._next('block',3)
        elif self.flags&4:self._next('checksum',4)
        else:self._next('magic',4)

    def feed(self,data):
        pos=0
        while pos<len(data) or not self.need:
            checkpoint()
            amount=min(self.need,len(data)-pos)
            if self.state not in ('body','skip','checksum'):
                self.header.extend(data[pos:pos+amount])
            pos+=amount;self.need-=amount
            if self.need:return
            value=bytes(self.header);self.header.clear()
            state=self.state
            if state=='magic':
                magic=int.from_bytes(value,'little')
                if magic==unzstd.MAGIC:
                    self.seen=True;self._next('descriptor',1)
                elif 0x184D2A50<=magic<=0x184D2A5F:
                    self.seen=True;self._next('skip_size',4)
                else:raise ValueError('zstd: invalid frame magic')
            elif state=='descriptor':
                self.flags=value[0]
                if self.flags&8:raise ValueError('zstd: reserved frame flag')
                self.single=bool(self.flags&32)
                self.dictionary=(0,1,2,4)[self.flags&3]
                self.content_bytes=((1 if self.single else 0),2,4,8)[self.flags>>6]
                self._next('frame_header',(not self.single)+self.dictionary+self.content_bytes)
            elif state=='frame_header':
                if not self.single:
                    descriptor=value[0];base=1<<(10+(descriptor>>3))
                    if base+(base>>3)*(descriptor&7)>MAX_WINDOW:
                        raise ReadLimitExceeded()
                if self.content_bytes:
                    size=int.from_bytes(value[-self.content_bytes:],'little')+(256 if self.content_bytes==2 else 0)
                    if size>self.maximum:raise ReadLimitExceeded()
                    if self.single and size>MAX_WINDOW:raise ReadLimitExceeded()
                self._next('block',3)
            elif state=='block':
                head=int.from_bytes(value,'little');kind,size=(head>>1)&3,head>>3
                if kind==3 or size>131072:raise ValueError('zstd: invalid block')
                self.last=head&1
                self._next('body',1 if kind==1 else size)
            elif state=='body':self._block_end()
            elif state=='checksum':self._next('magic',4)
            elif state=='skip_size':self._next('skip',int.from_bytes(value,'little'))
            elif state=='skip':self._next('magic',4)

    def finish(self):
        if not self.seen:raise ValueError('zstd: empty compressed file')
        if self.state!='magic' or self.need!=4 or self.header:
            raise ValueError('zstd: incomplete compressed frame')


class _Input:
    def __init__(self,stream,maximum,output,chunk_size):
        self.stream,self.maximum,self.chunk_size=stream,maximum,chunk_size
        self.used=0
        self.frames=_Frames(output)
        self.ended=False

    def read(self,size):
        checkpoint()
        if self.ended:return b''
        if type(size) is not int or size<0:raise ValueError('zstd: unbounded input read')
        if not size:return b''
        count=min(size,self.chunk_size,self.maximum-self.used+1)
        data=self.stream.read(count)
        if not isinstance(data,bytes) or len(data)>count:
            raise ValueError('zstd: invalid input stream')
        self.used+=len(data)
        if self.used>self.maximum:raise ReadLimitExceeded()
        if data:self.frames.feed(data)
        else:
            self.frames.finish();self.ended=True
        return data


def _standard_chunks(module,source,maximum,chunk_size):
    total=0;decoder=None
    while True:
        data=source.read(chunk_size)
        if not data:
            if decoder is not None and not decoder.eof:
                raise ValueError('zstd: incomplete compressed frame')
            return
        while data or (decoder is not None and not decoder.needs_input):
            checkpoint()
            if decoder is None:
                decoder=module.ZstdDecompressor(options={module.DecompressionParameter.window_log_max:27})
            output=decoder.decompress(data,max_length=min(chunk_size,maximum-total+1))
            data=b'';total+=len(output)
            if total>maximum:raise ReadLimitExceeded()
            if output:yield output
            if decoder.eof:
                data=decoder.unused_data;decoder=None


def _optional_chunks(module,source,maximum,chunk_size):
    total=0
    context=module.ZstdDecompressor(max_window_size=MAX_WINDOW//1024)
    with context.stream_reader(source,read_size=chunk_size,read_across_frames=True,closefd=False) as reader:
        while True:
            checkpoint()
            output=reader.read(min(chunk_size,maximum-total+1))
            if not output:break
            total+=len(output)
            if total>maximum:raise ReadLimitExceeded()
            yield output
    # Some library readers accept a physically truncated last frame at EOF.
    # The independent wire validator must have seen a complete terminal frame.
    if not source.ended:
        if source.read(1):raise ValueError('zstd: unconsumed compressed data')


def iter_chunks(stream,*,max_output,max_input,chunk_size=65536):
    """Bounded compressed reads and decoded chunks; no backend may bypass frame/byte limits.

    Native decoders stream. The compatibility Python decoder retains its bounded
    compressed input and bounded output; it checks growth before every block/sequence.
    """
    for value in (max_output,max_input,chunk_size):
        if type(value) is not int or value<0:raise ValueError('zstd: invalid read limit')
    if not chunk_size:raise ValueError('zstd: invalid chunk size')
    source=_Input(stream,max_input,max_output,chunk_size)
    try:
        try:from compression import zstd as module
        except ImportError:module=None
        if module is not None:
            yield from _standard_chunks(module,source,max_output,chunk_size)
            return
        try:import zstandard as module
        except ImportError:module=None
        if module is not None:
            yield from _optional_chunks(module,source,max_output,chunk_size)
            return
        data=bytearray()
        while True:
            part=source.read(chunk_size)
            if not part:break
            data.extend(part)
        result=unzstd.decompress(data,max_output=max_output)
        for offset in range(0,len(result),chunk_size):
            checkpoint()
            yield result[offset:offset+chunk_size]
    except (ValueError,ScanCancelled):raise
    except Exception as error:
        raise ValueError('zstd: the file could not be decompressed') from error
