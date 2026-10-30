"""Bounded, private local metadata archive. Never opens a retained source to replay its rows.

The archive contains the same narrow projections as the readers' disposable caches, not Session totals.
Everything PLER stores crosses the allowlist below, and stored rows cross it again before they are used.
A shared file lock and generation guard make clear atomic with respect to concurrent saves. No agent
settings, conversation text or account IDs are read.

A read only rewrites the archive when something in it changed. An unchanged live source keeps its stored
projection (same checksum) and refreshes its last-seen time at most once a day.
"""
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import threading
import time

from ..paths import cache_file, cache_folder
from . import accounting, discovery, preferences
from .records import timestamp

MAX_BYTES=64*1024*1024
MAX_FILES=2048
MAX_DAYS=365
SEEN_REFRESH=86400  # seconds; last_seen only drives the MAX_DAYS limit
FORMAT=1
FILENAME='metadata-archive.json'
GENERATION='metadata-archive-generation.json'
LOCKFILE='metadata-archive.lock'
_LOCK=threading.RLock()
_WORD=re.compile(r'^[\w./:+<>@-]{1,256}$',re.ASCII)
_REASONS={'MalformedRows','ReadLimitExceeded','PermissionError','FileNotFoundError','OSError','UnicodeError','ValueError',
          'RuntimeError','InconsistentReasoning'}


_CONTROL=re.compile(r'[\x00-\x1f]')


def _text(value,maximum=8192):
    # A C-level search; a per-character generator here dominated the first read on real logs.
    return isinstance(value,str) and len(value)<=maximum and not _CONTROL.search(value)


def _word(value):
    return isinstance(value,str) and bool(_WORD.fullmatch(value))


def _number(value):
    return type(value) in (int,float) and math.isfinite(value)


def _stamp(value):
    return value if timestamp(value) is not None and (isinstance(value,str) or _number(value)) else None


def _fields(value,names,maximum=8192,words=False):
    return {name:value[name] for name in names if
            (_word(value.get(name)) if words else _text(value.get(name),maximum))}


def _numbers(value,agent):
    accounting.tokens(value,agent)
    names=('input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens')
    if agent=='claude-code':
        names=('input_tokens','cache_read_input_tokens','cache_creation_input_tokens','output_tokens')
    result={name:value[name] for name in names if name in value}
    if agent=='claude-code' and isinstance(value.get('output_tokens_details'),dict):
        result['output_tokens_details']={'thinking_tokens':accounting.count(value['output_tokens_details'].get('thinking_tokens',0))}
    if agent=='claude-code':
        # Price inputs (pricing.py): the 1-hour share of cache writes, and the speed/region words.
        if 'ephemeral_1h_input_tokens' in value:
            written=accounting.count(value['ephemeral_1h_input_tokens'])
            if written>value.get('cache_creation_input_tokens',0): raise ValueError('inconsistent cache write split')
            result['ephemeral_1h_input_tokens']=written
        result.update(_fields(value,('speed','inference_geo'),words=True))
    return result


def sanitize(agent,rows):
    """Rebuild, never copy, every persisted object. Unknown/nested optional metadata is discarded."""
    if agent not in ('claude-code','codex') or not isinstance(rows,list):
        raise ValueError('invalid metadata archive')
    clean=[]
    malformed=False
    for row in rows:
        if not isinstance(row,dict):
            malformed=True
            continue
        try:
            kind=row.get('type')
            if agent=='claude-code':
                if kind=='pler_file_issue':
                    clean.append(dict(type=kind,reason=row['reason'] if row.get('reason') in _REASONS else 'MalformedRows'))
                    continue
                identity=row.get('sessionId')
                if not _text(identity,512):
                    if kind in ('assistant','user'): malformed=True
                    continue
                # Unknown transcript types may only establish dates/project metadata, as in the reader.
                kept=dict(type=kind if kind in ('assistant','user','cost-state') else None,
                          sessionId=identity,timestamp=_stamp(row.get('timestamp')))
                kept.update(_fields(row,('cwd','gitBranch','version')))
                if kind=='user':
                    kept.update(prompt=row.get('prompt') is True,isMeta=row.get('isMeta') is True,
                                uuid=row.get('uuid') if _text(row.get('uuid'),512) else None)
                    results=row.get('results')
                    if isinstance(results,list):
                        results=[dict(id=item['id'],error=item.get('error') is True) for item in results[:1000]
                                 if isinstance(item,dict) and _text(item.get('id'),512)]
                        if results: kept['results']=results
                elif kind=='cost-state' and _number(row.get('totalCostUSD')):
                    kept['totalCostUSD']=row['totalCostUSD']
                elif kind=='assistant':
                    message=row.get('message')
                    if not isinstance(message,dict):
                        malformed=True
                        continue
                    usage=message.get('usage')
                    blocks=[]
                    for block in message.get('content') if isinstance(message.get('content'),list) else []:
                        if not isinstance(block,dict) or block.get('type')!='tool_use' or not _word(block.get('name')): continue
                        from .claude_code import EDIT_TOOLS
                        field=EDIT_TOOLS.get(block['name'])
                        value=block.get('input') if isinstance(block.get('input'),dict) else {}
                        kept_block=dict(type='tool_use',name=block['name'],
                                        id=block.get('id') if _text(block.get('id'),512) else None,
                                        input={field:value[field]} if field and _text(value.get(field)) else {})
                        if block.get('check') in ('test','build'):
                            kept_block.update(check=block['check'],known=block.get('known') is True)
                        blocks.append(kept_block)
                    slim=dict(id=message.get('id') if _text(message.get('id'),512) else None,
                              model=message.get('model') if _word(message.get('model')) else None,
                              usage=_numbers(usage,agent) if usage else None,content=blocks)
                    thinking=message.get('zeroed_usage_thinking')
                    if type(thinking) is int and 0<thinking<=accounting.MAX_COUNT: slim['zeroed_usage_thinking']=thinking
                    quota=row.get('quotaLimits') if isinstance(row.get('quotaLimits'),dict) else {}
                    kept.update(message=slim,requestId=row.get('requestId') if _text(row.get('requestId'),512) else None,
                                isApiErrorMessage=row.get('isApiErrorMessage') is True,
                                effort=row.get('effort') if _word(row.get('effort')) else None,
                                quotaLimits=dict(status=quota.get('status') if _word(quota.get('status')) else None))
                clean.append(kept)
            else:
                if kind in ('pler_incomplete_log','pler_archive_ambiguous'):
                    clean.append(dict(type=kind,**({'reason':'ReadLimitExceeded'} if kind=='pler_incomplete_log' and
                                                  row.get('reason')=='ReadLimitExceeded' else {})))
                    continue
                payload=row.get('payload') if isinstance(row.get('payload'),dict) else {}
                sub=payload.get('type')
                if kind=='session_meta':
                    kept=_fields(payload,('session_id','id','parent_thread_id'),512)
                    kept.update(_fields(payload,('cwd',)))
                    kept.update(_fields(payload,('cli_version',),words=True))
                    if _stamp(payload.get('timestamp')) is not None: kept['timestamp']=payload['timestamp']
                elif kind=='turn_context':
                    kept=_fields(payload,('cwd',))
                    kept.update(_fields(payload,('model','effort'),words=True))
                elif kind=='token_usage_record':
                    kept=dict(response_id=payload.get('response_id') if _text(payload.get('response_id'),512) else None,
                              usage=_numbers(payload.get('usage'),agent))
                elif kind=='compacted':
                    kept=dict(compaction_response_id=payload.get('compaction_response_id') if _text(payload.get('compaction_response_id'),512) else None)
                elif kind=='event_msg' and sub=='token_count':
                    info=payload.get('info') if isinstance(payload.get('info'),dict) else {}
                    limits=payload.get('rate_limits') if isinstance(payload.get('rate_limits'),dict) else {}
                    windows={}
                    for name in ('primary','secondary'):
                        window=limits.get(name)
                        if not isinstance(window,dict): continue
                        used,minutes=window.get('used_percent'),window.get('window_minutes')
                        if _number(used) and 0<=used<=100 and type(minutes) is int and 0<minutes<=accounting.MAX_COUNT:
                            windows[name]=dict(used_percent=used,window_minutes=minutes,resets_at=_stamp(window.get('resets_at')))
                    kept=dict(type=sub,info=dict(total_token_usage=_numbers(info['total_token_usage'],agent)
                                                if info.get('total_token_usage') is not None else None),
                              rate_limits=dict(windows,plan_type=limits.get('plan_type') if _word(limits.get('plan_type')) else None))
                elif kind=='event_msg' and sub in ('task_started','task_complete','turn_aborted'):
                    kept=dict(type=sub,turn_id=payload.get('turn_id') if _text(payload.get('turn_id'),512) else None)
                    if sub=='task_complete':
                        kept.update(duration_ms=accounting.count(payload['duration_ms']) if payload.get('duration_ms') is not None else None,
                                    error=payload.get('error') is True)
                elif kind=='event_msg' and sub=='item_completed':
                    if payload.get('check') not in ('test','build'): continue
                    kept=dict(type=sub,item_id=payload.get('item_id') if _text(payload.get('item_id'),512) else None,
                              check=payload['check'],
                              outcome=payload.get('outcome') if payload.get('outcome') in ('passed','failed') else 'unknown')
                elif kind=='response_item' and sub in ('function_call','custom_tool_call'):
                    kept=dict(type=sub,name=payload.get('name') if _word(payload.get('name')) else None,
                              call_id=payload.get('call_id') if _text(payload.get('call_id'),512) else None)
                    edited=payload.get('edited_files')
                    if isinstance(edited,list): kept['edited_files']=sorted({v for v in edited if _text(v)})[:200]
                elif kind is None and _stamp(row.get('timestamp')) is not None:
                    clean.append(dict(timestamp=row['timestamp']))
                    continue
                else: continue
                clean.append(dict(type=kind,timestamp=_stamp(row.get('timestamp')),payload=kept))
        except (ValueError,TypeError,OverflowError):
            malformed=True
    if malformed:
        clean.append(dict(type='pler_file_issue',reason='MalformedRows') if agent=='claude-code' else dict(type='pler_incomplete_log'))
    return clean


def _encoded(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')


_SIZES={}  # checksum -> encoded size of those rows, shared by every scan of this process


def _measured(rows):
    """The rows' checksum, the same as the reader cache's (cache._checksum hashes these bytes); the encoded
    size that bounds the archive is remembered with it, so the rows are encoded once instead of twice."""
    data=_encoded(rows)
    checksum=hashlib.sha256(data).hexdigest()
    if len(_SIZES)>=4*MAX_FILES:_SIZES.clear()
    _SIZES[checksum]=len(data)
    return checksum


READ_LIMIT=65*1024*1024


def _read(path,maximum=READ_LIMIT):
    if path is None: return None
    try:
        # A fixed absolute bound also applies when tests reduce the retention budget.
        size=path.stat().st_size
        if size>maximum: raise ValueError('oversized archive')
        with path.open('rb') as stream:
            data=stream.read(size+1)
        if len(data)!=size: raise ValueError('archive changed while reading')
        try:
            return json.loads(data.decode('utf-8'),parse_constant=lambda _: (_ for _ in ()).throw(ValueError('invalid number')))
        except RecursionError as error:
            raise ValueError('over-nested metadata') from error
    except FileNotFoundError: return None


def _generation(base):
    value=_read(cache_file(GENERATION,base),4096)
    if value is None: return 0
    if not isinstance(value,dict) or type(value.get('generation')) is not int or value['generation']<0:
        raise ValueError('invalid generation')
    return value['generation']


def _sync_directory(path):
    """Persist an own-file rename/removal on POSIX; Windows has no portable directory fsync."""
    if os.name=='nt':return
    if path is None or cache_file(path.name,path.parent)!=path:raise OSError('unsafe archive')
    flags=os.O_RDONLY|getattr(os,'O_DIRECTORY',0)|getattr(os,'O_NOFOLLOW',0)
    descriptor=os.open(str(path.parent),flags)
    try:
        if cache_file(path.name,path.parent)!=path:raise OSError('unsafe archive')
        os.fsync(descriptor)
    finally:os.close(descriptor)


def _write(path,value):
    if path is None or cache_file(path.name,path.parent)!=path: raise OSError('unsafe archive')
    temporary=None
    try:
        data=_encoded(value)
        with tempfile.NamedTemporaryFile(mode='wb',dir=str(path.parent),prefix=path.name+'.',suffix='.tmp',delete=False) as stream:
            temporary=Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if cache_file(path.name,path.parent)!=path: raise OSError('unsafe archive')
        os.replace(str(temporary),str(path))
        # A failure here is reported, but the replacement may already be visible.
        _sync_directory(path)
    finally:
        if temporary is not None and cache_file(temporary.name,temporary.parent)==temporary:
            try: temporary.unlink(missing_ok=True)
            except OSError: pass


@contextmanager
def _locked(base):
    """A fixed local lock, bounded waiting, released by the OS even after process failure."""
    with _LOCK:
        path=cache_file(LOCKFILE,base)
        if path is None: raise OSError('unsafe archive')
        path.parent.mkdir(parents=True,exist_ok=True)
        if cache_file(path.name,path.parent)!=path: raise OSError('unsafe archive')
        with open(str(path),'a+b') as stream:
            if os.name=='nt':
                import msvcrt
                if stream.seek(0,2)==0: stream.write(b'0');stream.flush()
                def acquire():
                    stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
                def release():
                    stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                def acquire(): fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                def release(): fcntl.flock(stream.fileno(),fcntl.LOCK_UN)
            deadline=time.monotonic()+1
            while True:
                try: acquire();break
                except OSError:
                    if time.monotonic()>=deadline: raise
                    time.sleep(.01)
            try: yield
            finally: release()


def _identity(agent,path):
    return hashlib.sha256(_encoded([agent,discovery.key(path)])).hexdigest()


def _entry(value):
    if not isinstance(value,dict) or value.get('agent') not in ('claude-code','codex'):
        raise ValueError('invalid archive entry')
    if not all(_text(value.get(name)) and value.get(name) for name in ('source','root','reader_key')):
        raise ValueError('invalid archive entry')
    if not discovery.contains(value['root'],value['source']) or not _number(value.get('last_seen')):
        raise ValueError('invalid archive entry')
    rows=value.get('rows')
    if not isinstance(rows,list) or value.get('checksum')!=_measured(rows): raise ValueError('invalid archive checksum')
    # Rows are rebuilt through the allowlist when a read uses them (Archive.rows), not on every load.
    return dict(agent=value['agent'],source=value['source'],root=value['root'],reader_key=value['reader_key'],
                last_seen=value['last_seen'],rows=rows,checksum=value['checksum'],incomplete=value.get('incomplete') is True)


def _signature(base):
    try:
        info=cache_file(FILENAME,base).stat()
        return info.st_size,info.st_mtime_ns
    except (OSError,AttributeError): return None


def _load(base):
    value=_read(cache_file(FILENAME,base))
    if value is None: return {},0
    if not isinstance(value,dict) or value.get('format')!=FORMAT or not isinstance(value.get('files'),dict):
        raise ValueError('unsupported archive')
    entries,errors={},0
    for entry in value['files'].values():
        try:
            clean=_entry(entry)
            entries[_identity(clean['agent'],clean['source'])]=clean
        except (ValueError,TypeError,OverflowError,RecursionError): errors+=1
    return entries,errors


class Archive:
    def __init__(self,enabled=True,now=None):
        self.base=cache_folder() if enabled else None
        self.available=self.base is not None
        self.enabled=False
        self.retention_enabled=False
        self.now=time.time() if now is None else now
        self.entries={}
        self.keys={}
        self.manifests={}
        self.live={}
        self.used={}
        self.observed={}
        self.signatures={}
        self.errors=0
        self.evicted=0
        self._evicted=set()
        self.generation=0
        self.scan_generation=0
        self.stale_snapshot=False
        self.dirty=False
        self._clean=set()  # entries whose rows crossed the allowlist in this process
        self._sizes=_SIZES  # shared: a size depends only on the rows its checksum names
        self._loaded=None
        if self.available:
            try:
                with _locked(self.base):
                    self.generation=_generation(self.base)
                    self.scan_generation=self.generation
                    self.retention_enabled=preferences.read(self.base)
                    self.enabled=self.retention_enabled
                    if self.enabled:
                        self.entries,self.errors=_load(self.base)
                        self._loaded=_signature(self.base)
            except (OSError,ValueError,TypeError,OverflowError): self.errors+=1
        self._bound()

    def _size(self,key,entry):
        # Exact encoded size; the row part is measured once per checksum.
        rows=self._sizes.get(entry['checksum'])
        if rows is None: rows=self._sizes[entry['checksum']]=len(_encoded(entry['rows']))
        return len(_encoded(key))+1+len(_encoded(dict(entry,rows=[])))-2+rows

    def _bound(self):
        before=set(self.entries)
        self.entries={key:value for key,value in self.entries.items()
                      if self.now-MAX_DAYS*86400<=value['last_seen']<=self.now+300}
        ordered=sorted(self.entries,key=lambda key:(self.entries[key]['last_seen'],key),reverse=True)
        keep={}
        # Budget the actual encoded envelope, not just row payloads.
        used=len(_encoded(dict(format=FORMAT,files={})))
        for key in ordered:
            size=self._size(key,self.entries[key])+(1 if keep else 0)
            if len(keep)<MAX_FILES and used+size<=MAX_BYTES:
                keep[key]=self.entries[key];used+=size
        self.entries=keep
        if before-set(keep): self.dirty=True
        self._evicted.update(before-set(keep))
        self.evicted=len(self._evicted)

    def prepare(self,agent,paths,manifest,key,cache=None,persistent=True):
        self.keys[agent]=key
        self.manifests[agent]=manifest if persistent else discovery.Manifest()
        self.live[agent]={str(path) for path in paths}
        if not self.enabled or not persistent: return
        # Upgrade only existing metadata cache projections, never original conversations.
        for source,value in (cache.historical.items() if cache is not None and self.generation==0 else ()):
            identity=_identity(agent,source)
            if identity in self.entries or not manifest.selected(source) or not isinstance(value,dict): continue
            try:
                if value.get('checksum')!=_measured(value.get('rows')): raise ValueError('invalid cache')
                rows=sanitize(agent,value['rows'])
                root=manifest.scope(source)
                self.entries[identity]=dict(agent=agent,source=source,root=root,
                    reader_key=cache.historical_key if _text(cache.historical_key,256) else 'unknown',
                    rows=rows,checksum=_measured(rows),last_seen=self.now)
                self._clean.add(identity);self.dirty=True
            except (ValueError,TypeError,OverflowError): self.errors+=1

    def replay(self,agent):
        if not self.enabled: return []
        manifest=self.manifests[agent]
        return [Path(v['source']) for v in self.entries.values() if v['agent']==agent
                and v['source'] not in self.live[agent] and manifest.selected(v['source'])]

    def begin(self,agent,path):
        if not self.enabled or not self.manifests[agent].selected(path): return
        try:
            info=os.stat(path)
            self.signatures[(agent,str(path))]=(info.st_size,info.st_mtime_ns)
        except OSError: self.signatures[(agent,str(path))]=None

    def observe(self,agent,path,rows,checksum=None):
        """`checksum`: the reader cache's checksum of these rows, when it has one."""
        if not self.enabled: return
        source=str(path)
        root=self.manifests[agent].scope(source)
        if root is None: return
        identity=_identity(agent,source)
        previous=self.entries.get(identity)
        same=(checksum is not None and previous is not None and previous['checksum']==checksum
              and previous['reader_key']==self.keys[agent] and previous['root']==root and not previous['incomplete'])
        if same:
            # The same projection is already stored: reader rows are allowlisted when they are made.
            seen=previous['last_seen'] if 0<=self.now-previous['last_seen']<SEEN_REFRESH else self.now
            entry=dict(previous,last_seen=seen)
        else:
            clean=sanitize(agent,rows)
            entry=dict(agent=agent,source=source,root=root,reader_key=self.keys[agent],last_seen=self.now,
                       rows=clean,checksum=_measured(clean),incomplete=False)
        self.observed[identity]=entry
        self.used[(agent,source)]=dict(state='live',deleted=False,old=False,unverified=False)
        if (agent,source) in self.signatures:
            try:
                info=os.stat(path)
                if (info.st_size,info.st_mtime_ns)!=self.signatures[(agent,source)]: return
            except OSError: return
        bad=lambda rows: any(row.get('type') in ('pler_incomplete_log','pler_file_issue') for row in rows)
        if not same and previous is not None and bad(entry['rows']) and not bad(previous['rows']):
            # Keep the last complete projection, with a durable fixed warning. The live
            # reader still publishes its valid partial rows; no two snapshots are added.
            entry=dict(previous,incomplete=True)
        else: self._clean.add(identity)
        if entry!=previous: self.dirty=True
        self.entries[identity]=entry

    def rows(self,agent,path,unreadable=False):
        identity=_identity(agent,path)
        entry=self.entries.get(identity) if self.enabled else None
        if entry is None or not self.manifests[agent].selected(path): return None
        if identity not in self._clean:
            clean=sanitize(agent,entry['rows'])
            checksum=_measured(clean)
            if checksum!=entry['checksum']:
                entry=self.entries[identity]=dict(entry,rows=clean,checksum=checksum);self.dirty=True
            self._clean.add(identity)
        deleted=not unreadable and self.manifests[agent].missing(path)
        self.used[(agent,str(path))]=dict(state='archive',deleted=deleted,
            old=entry['reader_key']!=self.keys[agent],unverified=not deleted)
        rows=entry['rows']
        if entry.get('incomplete'):
            marker=dict(type='pler_file_issue',reason='MalformedRows') if agent=='claude-code' else dict(type='pler_incomplete_log')
            rows=rows+[marker]
        rows,ambiguous=self._overlap(agent,rows)
        if ambiguous: self.used[(agent,str(path))]['unverified']=True
        return rows

    def _overlap(self,agent,rows):
        """Anonymous old events cannot prove disjointness from a resumed live history.

        Withhold only their unidentifiable quantities in an overlapping native session. Keep dates,
        headers and stable-ID evidence, and make the lost coverage explicit rather than count twice.
        """
        identities=set()
        for value in self.observed.values():
            if value['agent']!=agent: continue
            for row in value['rows']:
                if agent=='claude-code':
                    if _text(row.get('sessionId'),512): identities.add(row['sessionId'])
                elif row.get('type')=='session_meta':
                    payload=row.get('payload',{})
                    identities.update(payload[name] for name in ('session_id','id') if _text(payload.get(name),512))
        own={row.get('sessionId') for row in rows} if agent=='claude-code' else set()
        if agent=='codex':
            own={row['payload'].get('session_id') or row['payload'].get('id') for row in rows if row.get('type')=='session_meta'}
        overlap=identities & own
        if not overlap: return rows,False
        result=[]
        ambiguous=set()
        for original in rows:
            row=original
            if agent=='claude-code' and row.get('sessionId') in overlap:
                sid=row['sessionId']
                if row.get('type')=='user' and row.get('prompt') and not row.get('uuid'):
                    row=dict(row,prompt=False);ambiguous.add(sid)
                if row.get('type')=='assistant':
                    message=row.get('message',{})
                    blocks=message.get('content',[])
                    stable=[block for block in blocks if block.get('id')]
                    if len(stable)!=len(blocks):
                        message=dict(message,content=stable);ambiguous.add(sid)
                    if not message.get('id') and not row.get('requestId'):
                        message=dict(message,usage=None,content=[])
                        row=dict(row,isApiErrorMessage=False,quotaLimits=dict(status=None))
                        ambiguous.add(sid)
                    row=dict(row,message=message)
            elif agent=='codex':
                payload=row.get('payload',{})
                if (row.get('type')=='token_usage_record' and not payload.get('response_id')
                    or row.get('type')=='event_msg' and payload.get('type') in ('task_started','task_complete','turn_aborted') and not payload.get('turn_id')
                    or row.get('type')=='response_item' and not payload.get('call_id')):
                    ambiguous.update(overlap)
                    continue
            result.append(row)
        if ambiguous:
            if agent=='claude-code':
                result.extend(dict(type='pler_archive_ambiguous',sessionId=sid) for sid in sorted(ambiguous))
            else: result.append(dict(type='pler_archive_ambiguous'))
        return result,bool(ambiguous)

    def mark(self,session,agent,path):
        state=self.used.get((agent,str(path)),dict(state='live',deleted=False,old=False,unverified=False))
        session.source_evidence(str(path),**state)

    def finish(self):
        self._bound()
        if self.available:
            try:
                with _locked(self.base):
                    current=_generation(self.base)
                    retained=preferences.read(self.base)
                    if current!=self.generation:
                        self.generation=current
                        self.entries={}
                        self.enabled=self.retention_enabled=retained
                        self.stale_snapshot=True
                        return self.info()
                    self.enabled=self.enabled and retained
                    self.retention_enabled=retained
                    if not self.enabled:
                        self.entries={}
                        return self.info()
                    if not self.dirty: return self.info()
                    # Preserve another scan's newer observations without resurrecting cleared entries.
                    if _signature(self.base)!=self._loaded:
                        try: other,errors=_load(self.base)
                        except (OSError,ValueError,TypeError,OverflowError): other,errors={},1
                        self.errors+=errors
                        for key,value in other.items():
                            if key not in self.entries or value['last_seen']>self.entries[key]['last_seen']:
                                self.entries[key]=value;self._clean.discard(key)
                        self._bound()
                    _write(cache_file(FILENAME,self.base),dict(format=FORMAT,files=self.entries))
                    self._loaded,self.dirty=_signature(self.base),False
            except (OSError,ValueError,TypeError,OverflowError,MemoryError): self.errors+=1
        return self.info()

    def info(self):
        retained=[state for state in self.used.values() if state['state']=='archive']
        signature=_signature(self.base) if self.available else None
        return dict(enabled=self.enabled,available=self.available,retention_enabled=self.retention_enabled,
                    stored_files=len(self.entries),stored_files_known=self.enabled and not self.stale_snapshot,
                    stored_bytes=signature[0] if signature is not None else 0,
                    max_bytes=MAX_BYTES,max_files=MAX_FILES,max_days=MAX_DAYS,
                    archive_files=len(retained),
                    old_parser_files=sum(state['old'] for state in retained),
                    unverified_files=sum(state['unverified'] for state in retained),
                    evicted_files=self.evicted,errors=self.errors,clear_generation=self.generation,
                    scan_generation=self.scan_generation,stale_snapshot=self.stale_snapshot)


def archive_info():
    return Archive().info()


def archive_generation():
    """Cheap external-clear check; reads only the tiny fixed generation marker."""
    base=cache_folder()
    if base is None: return None
    try: return _generation(base)
    except (OSError,ValueError,TypeError,OverflowError): return None


def clear_archive():
    """Forget only PLER's archive. Generation changes before removal, under the shared save lock."""
    base=cache_folder()
    result=dict(ok=False,cleared_files=0,errors=0,clear_generation=0)
    if base is None:
        result['errors']=1
        return result
    try:
        with _locked(base):
            try: result['clear_generation']=_generation(base)+1
            except (ValueError,TypeError,OverflowError): result['clear_generation']=time.time_ns()
            try:
                entries,_=_load(base)
                result['cleared_files']=len(entries)
            except (OSError,ValueError,TypeError,OverflowError): pass
            _write(cache_file(GENERATION,base),dict(generation=result['clear_generation']))
            path=cache_file(FILENAME,base)
            if path is None: raise OSError('unsafe archive')
            path.unlink(missing_ok=True)
            _sync_directory(path)
            result['ok']=True
    except (OSError,ValueError,TypeError,OverflowError): result['errors']=1
    return result


def set_retention(enabled):
    """Change future retention/replay without deleting existing retained metadata.

    The shared generation changes before the preference is replaced. Any scan
    started before either a disable or a later re-enable must be discarded, and
    its finish() cannot write an old projection over the current archive.
    """
    result=dict(ok=False,retention_enabled=None,clear_generation=0,errors=0)
    if type(enabled) is not bool:
        result['errors']=1
        return result
    base=cache_folder()
    if base is None:
        result['errors']=1
        return result
    try:
        with _locked(base):
            try: prior=preferences.read(base)
            except (OSError,ValueError,TypeError,OverflowError): prior=None
            broken_generation=False
            try: current=_generation(base)
            except (ValueError,TypeError,OverflowError):
                current=time.time_ns();broken_generation=True
            if prior is not enabled or broken_generation:
                current+=1
                _write(cache_file(GENERATION,base),dict(generation=current))
                _write(cache_file(preferences.FILENAME,base),preferences.value(enabled))
            result.update(ok=True,retention_enabled=enabled,clear_generation=current)
    except (OSError,ValueError,TypeError,OverflowError): result['errors']=1
    return result


def reset_cache():
    """Remove only rebuildable reader caches; preserve archive, quota and preferences.

    No folder is recursively removed, no archived source is opened, and an
    unsafe file is never followed. A concurrent scan may rebuild these caches;
    the caller refreshes its snapshot after this action.
    """
    result=dict(ok=False,cleared_files=0,errors=0)
    base=cache_folder()
    if base is None:
        result['errors']=1
        return result
    try:
        with _locked(base):
            for name in ('claude.json','codex.json'):
                path=cache_file(name,base)
                if path is None:
                    result['errors']+=1
                    continue
                try:
                    path.unlink()
                    result['cleared_files']+=1
                except FileNotFoundError: pass
                except OSError: result['errors']+=1
            result['ok']=not result['errors']
    except (OSError,ValueError,TypeError,OverflowError): result['errors']+=1
    return result
