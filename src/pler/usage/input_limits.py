"""Input budgets for local readers; no text, paths or identifiers are retained here."""
from contextvars import ContextVar
from functools import wraps
import json

CHUNK_BYTES=64*1024
MAX_SOURCE_BYTES=512*1024*1024
MAX_EXPANDED_BYTES=512*1024*1024
MAX_LINE_BYTES=8*1024*1024
MAX_JSON_DEPTH=256
MAX_FILE_ROWS=200000
MAX_FILE_METADATA=64*1024*1024
MAX_SCAN_ROWS=500000
MAX_SCAN_METADATA=256*1024*1024
MAX_SCAN_SOURCE_BYTES=2*1024*1024*1024
MAX_SCAN_EXPANDED_BYTES=4*1024*1024*1024
MAX_CACHE_BYTES=256*1024*1024
MAX_FILES=20000
MAX_DIRECTORIES=100000
_CURRENT=ContextVar('pler_input_budget',default=None)


class ReadLimitExceeded(ValueError):
    def __init__(self):super().__init__('local input limit exceeded')


def checkpoint():
    from ..runtime import checkpoint as check
    check()


def scoped(function):
    @wraps(function)
    def run(*args,**kwargs):
        token=_CURRENT.set(dict(rows=0,metadata=0,files=0,directories=0,source_bytes=0,expanded_bytes=0))
        try:return function(*args,**kwargs)
        finally:_CURRENT.reset(token)
    return run


def count(kind,amount,maximum):
    checkpoint()
    budget=_CURRENT.get()
    if budget is not None:
        if budget[kind]+amount>maximum:
            budget[kind]=maximum
            raise ReadLimitExceeded()
        budget[kind]+=amount


# json.dumps with non-default options builds a new encoder per call; one shared encoder measures the same
# ASCII bytes without that cost on every projected row.
_ENCODER=json.JSONEncoder(ensure_ascii=True,separators=(',',':'),allow_nan=False)


def metadata_size(row):
    return len(_ENCODER.encode(row))


def admit(rows):
    """Charge cached, archived and newly read projections exactly once before reconciliation."""
    budget=_CURRENT.get()
    if budget is None:return
    if budget['rows']+len(rows)>MAX_SCAN_ROWS:raise ReadLimitExceeded()
    remaining=MAX_SCAN_METADATA-budget['metadata']
    size=0
    for index in range(0,len(rows),256):
        checkpoint()
        part=rows[index:index+256]
        # One bounded batch encoding avoids reintroducing per-entry warm-cache serialization.
        size+=len(json.dumps(part,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode('ascii'))-2-max(0,len(part)-1)
        if size>remaining:raise ReadLimitExceeded()
    budget['rows']+=len(rows);budget['metadata']+=size


def available():
    checkpoint()
    budget=_CURRENT.get()
    if budget is not None and (budget['rows']>=MAX_SCAN_ROWS or budget['metadata']>=MAX_SCAN_METADATA):
        raise ReadLimitExceeded()


def chunks(stream,maximum=MAX_SOURCE_BYTES):
    used=0
    while True:
        checkpoint()
        data=stream.read(min(CHUNK_BYTES,maximum-used+1))
        if not data:return
        used+=len(data)
        if used>maximum:raise ReadLimitExceeded()
        yield data


class Source:
    """Count physical source bytes across one scan before a decoder sees them."""
    def __init__(self,stream):self.stream=stream
    def read(self,size):
        checkpoint()
        budget=_CURRENT.get()
        if budget is not None:
            remaining=MAX_SCAN_SOURCE_BYTES-budget['source_bytes']
            if remaining<=0:raise ReadLimitExceeded()
            size=min(size,remaining+1)
        data=self.stream.read(size)
        count('source_bytes',len(data),MAX_SCAN_SOURCE_BYTES)
        return data


def expanded(parts):
    for part in parts:
        count('expanded_bytes',len(part),MAX_SCAN_EXPANDED_BYTES)
        yield part


def lines(parts):
    """Bound a JSONL line before decoding; drain oversize lines without retaining them.

    None signals one rejected line. CRLF is accepted; escaped JSON newlines are
    ordinary bytes. A final complete JSON value without a newline is retained.
    """
    pending=bytearray();discard=False
    for part in parts:
        checkpoint()
        start=0
        while start<len(part):
            end=part.find(b'\n',start)
            stop=len(part) if end<0 else end
            if not discard:
                if len(pending)+stop-start>MAX_LINE_BYTES:
                    pending.clear();discard=True;yield None
                else:pending.extend(part[start:stop])
            if end<0:break
            if not discard:yield bytes(pending)
            pending.clear();discard=False;start=end+1
    if pending and not discard:yield bytes(pending)


class Projection:
    """Per-file projected metadata bound, independent of discarded transcript size."""
    def __init__(self):self.rows=[];self.bytes=0
    def append(self,row):
        checkpoint()
        size=metadata_size(row)
        budget=_CURRENT.get()
        row_limit=min(MAX_FILE_ROWS,MAX_SCAN_ROWS-budget['rows']) if budget is not None else MAX_FILE_ROWS
        byte_limit=min(MAX_FILE_METADATA,MAX_SCAN_METADATA-budget['metadata']) if budget is not None else MAX_FILE_METADATA
        if len(self.rows)>=row_limit or self.bytes+size>byte_limit:
            raise ReadLimitExceeded()
        self.rows.append(row);self.bytes+=size
