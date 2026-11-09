"""Explicit annotation transfers; never infer identity or modify agent/accounting data.

One bounded private write-ahead/undo record makes the three annotation files a
recoverable unit. The common cache lock completes pending writes before readers
or writers enter. Backups contain the resulting annotations, not this undo copy.
"""
from base64 import b64decode, b64encode
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import tempfile
import time

from ..paths import cache_file
from . import archive
from .records import _too_deep
from .verdicts import CODE

FILENAME='session-reconnection.json'
MAX_BYTES=16*1024*1024
NAMES=('work-items.json','session-verdicts.json','session-budgets.json')
_MEMO={}


class ReconnectError(ValueError):
    def __init__(self,reason='unreadable'):
        self.reason=reason
        super().__init__('Session annotations could not be reconnected.')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')).hexdigest()


def _pairs(items):
    result={}
    for key,value in items:
        if key in result:raise ReconnectError()
        result[key]=value
    return result


def _json(raw):
    try:
        text=raw.decode('utf-8')
        if _too_deep(text):raise ReconnectError()
        return json.loads(text,object_pairs_hook=_pairs,parse_constant=lambda _:(_ for _ in ()).throw(ReconnectError()))
    except (ValueError,UnicodeError,TypeError,RecursionError,OverflowError) as error:
        raise ReconnectError() from error


def _limits():
    from . import work_items,verdicts,budgets
    return {work_items.FILENAME:work_items.MAX_BYTES,verdicts.FILENAME:verdicts.MAX_BYTES,budgets.FILENAME:budgets.MAX_BYTES}


def decode(name,raw):
    from . import work_items,verdicts,budgets
    if raw is None:return {}
    if name not in NAMES or len(raw)>_limits()[name]:raise ReconnectError()
    if name==work_items.FILENAME:return work_items.validate(raw)
    if name==budgets.FILENAME:return budgets.validate_document(raw)
    value=_json(raw)
    if (not isinstance(value,dict) or set(value)!={'format','verdicts'}
            or type(value['format']) is not int or value['format']!=1 or not verdicts._valid(value['verdicts'])):raise ReconnectError()
    return value['verdicts']


def encode(name,entries):
    from . import work_items
    doc=work_items.document(entries) if name==NAMES[0] else dict(format=1,**{('verdicts' if name==NAMES[1] else 'entries'):entries})
    raw=json.dumps(doc,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
    decode(name,raw)
    return raw


def _signature(info):return info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns


def _read(base,name,limit):
    path=cache_file(name,base)
    if path is None:raise ReconnectError()
    try:before=path.stat()
    except FileNotFoundError:return None
    if not stat.S_ISREG(before.st_mode) or before.st_size>limit:raise ReconnectError()
    try:
        with path.open('rb') as stream:
            if _signature(os.fstat(stream.fileno()))!=_signature(before):raise ReconnectError()
            raw=stream.read(before.st_size+1)
            if _signature(os.fstat(stream.fileno()))!=_signature(before):raise ReconnectError()
        if len(raw)!=before.st_size or _signature(path.stat())!=_signature(before):raise ReconnectError()
        return raw
    except FileNotFoundError as error:raise ReconnectError() from error


def _install(base,name,raw):
    path=cache_file(name,base)
    if path is None:raise ReconnectError()
    if raw is None:
        path.unlink(missing_ok=True)
        return
    fd,temporary=tempfile.mkstemp(prefix='.pler-reconnect-',dir=str(path.parent))
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        if cache_file(name,base)!=path:raise ReconnectError()
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)


def validate(raw):
    if type(raw) is not bytes or len(raw)>MAX_BYTES:raise ReconnectError()
    value=_json(raw)
    if (not isinstance(value,dict) or set(value)!={'format','phase','kind','id','at','source','target','files','summary'}
            or type(value['format']) is not int or value['format']!=1 or value['phase'] not in ('pending','complete')
            or value['kind'] not in ('transfer','undo') or not isinstance(value['id'],str) or not CODE.fullmatch(value['id'])
            or type(value['at']) is not int or not 0<=value['at']<=253402300799
            or any(not isinstance(value[k],str) or not CODE.fullmatch(value[k]) for k in ('source','target'))
            or value['source']==value['target'] or not isinstance(value['files'],dict)
            or not value['files'] or set(value['files'])-set(NAMES)
            or not isinstance(value['summary'],dict) or set(value['summary'])!={'works','verdict','budget'}
            or type(value['summary']['works']) is not int or not 0<=value['summary']['works']<=2000
            or any(type(value['summary'][k]) is not bool for k in ('verdict','budget'))):raise ReconnectError()
    decoded={}
    try:
        for name,pair in value['files'].items():
            if not isinstance(pair,dict) or set(pair)!={'before','after'}:raise ReconnectError()
            decoded[name]={}
            for side,encoded in pair.items():
                if encoded is not None and not isinstance(encoded,str):raise ReconnectError()
                data=None if encoded is None else b64decode(encoded,validate=True)
                if data is not None and b64encode(data).decode('ascii')!=encoded:raise ReconnectError()
                decode(name,data)
                decoded[name][side]=data
    except (ValueError,TypeError,UnicodeError,RecursionError,OverflowError) as error:raise ReconnectError() from error
    return value,decoded


def _record(base):
    path=cache_file(FILENAME,base)
    if path is None:raise ReconnectError()
    try:signature=_signature(path.stat())
    except FileNotFoundError:return None,{}
    cached=_MEMO.get(str(path))
    if cached and cached[0]==signature:return cached[1],cached[2]
    raw=_read(base,FILENAME,MAX_BYTES)
    value,decoded=validate(raw)
    if len(_MEMO)>=4:_MEMO.clear()
    _MEMO[str(path)]=(signature,value,decoded)
    return value,decoded


def _write_record(base,value):
    raw=json.dumps(value,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode('ascii')
    validate(raw)
    _install(base,FILENAME,raw)


def recover_locked(base):
    """Called only after the shared cache lock is acquired; roll forward or refuse."""
    value,files=_record(base)
    if value is None or value['phase']=='complete':return
    # Refuse unexpected external edits before touching any participant.
    for name,pair in files.items():
        if _read(base,name,_limits()[name]) not in (pair['before'],pair['after']):raise ReconnectError('recovery_conflict')
    for name,pair in files.items():
        current=_read(base,name,_limits()[name])
        if current not in (pair['before'],pair['after']):raise ReconnectError('recovery_conflict')
        if current!=pair['after']:_install(base,name,pair['after'])
    following=dict(value,phase='complete')
    _write_record(base,following)


def snapshots_locked(base):
    raw={name:_read(base,name,limit) for name,limit in _limits().items()}
    return raw,{name:decode(name,data) for name,data in raw.items()}


def inventory(documents):
    works,verdicts,budgets=(documents[name] for name in NAMES)
    result={}
    for key,item in works.items():
        for code in item['sessions']:result.setdefault(code,dict(works=[],verdict=None,budget=None))['works'].append(dict(id=key,title=item['title']))
    for code,row in verdicts.items():result.setdefault(code,dict(works=[],verdict=None,budget=None))['verdict']=row['verdict']
    for code,row in budgets.items():result.setdefault(code,dict(works=[],verdict=None,budget=None))['budget']={k:row[k] for k in ('metric','limit')}
    return result


def transfer(documents,source,target,verdict_choice='',budget_choice=''):
    from . import work_items
    if source==target or any(not isinstance(c,str) or not CODE.fullmatch(c) for c in (source,target)):raise ReconnectError('invalid')
    info=inventory(documents).get(source)
    if not info:raise ReconnectError('missing')
    result=deepcopy(documents);works,verdicts,budgets=(result[name] for name in NAMES)
    now=int(time.time());count=0
    for item in works.values():
        if source in item['sessions']:
            item['sessions']=sorted((set(item['sessions'])-{source})|{target});item['updated_at']=now;count+=1
    if source in verdicts:
        if target in verdicts and verdicts[source]['verdict']!=verdicts[target]['verdict'] and verdict_choice not in ('source','target'):raise ReconnectError('verdict_choice')
        chosen=verdicts.get(target) if target in verdicts and verdict_choice!='source' else verdicts[source]
        verdicts[target]=deepcopy(chosen);del verdicts[source]
    if source in budgets:
        if target in budgets and budget_choice not in ('source','target'):raise ReconnectError('budget_choice')
        chosen=budgets[target] if target in budgets and budget_choice=='target' else budgets[source]
        budgets[target]=dict(deepcopy(chosen),revision=secrets.token_hex(12));del budgets[source]
    work_items.validate_document(work_items.document(works))
    return result,dict(works=count,verdict=info['verdict'] is not None,budget=info['budget'] is not None)


def inverse(current,record,files):
    """Undo only this transfer's changes, preserving unrelated edits and notes."""
    if record is None or record['kind']!='transfer':raise ReconnectError('no_undo')
    from . import work_items
    result=deepcopy(current);source,target=record['source'],record['target']
    for name,pair in files.items():
        before,after=decode(name,pair['before']),decode(name,pair['after'])
        if name==NAMES[0]:
            for key,old in before.items():
                following=after.get(key)
                if following and old['sessions']!=following['sessions']:
                    live=result[name].get(key)
                    if live is None or set(live['sessions'])!=set(following['sessions']):raise ReconnectError('changed')
                    live['sessions']=list(old['sessions']);live['updated_at']=int(time.time())
            work_items.validate_document(work_items.document(result[name]))
        else:
            for code in (source,target):
                expected=after.get(code);actual=result[name].get(code)
                if name==NAMES[2] and expected is not None and actual is not None:
                    # Only monotonic automatic notification acknowledgements may differ.
                    if {k:v for k,v in actual.items() if k!='notified'}!={k:v for k,v in expected.items() if k!='notified'} or actual['notified'][:len(expected['notified'])]!=expected['notified']:raise ReconnectError('changed')
                elif actual!=expected:raise ReconnectError('changed')
                if code in before:result[name][code]=deepcopy(before[code])
                else:result[name].pop(code,None)
    return result


class Store:
    def __init__(self,base=None):self.base=base

    def stamp(self):
        path=cache_file(FILENAME,self.base)
        if path is None:raise ReconnectError()
        if not path.exists():return None
        with archive._locked(path.parent):
            record,_=_record(path.parent)
            return record['id'] if record else None

    def state(self):
        path=cache_file(FILENAME,self.base)
        if path is None:raise ReconnectError()
        with archive._locked(path.parent):
            record,files=_record(path.parent)
            raw,documents=snapshots_locked(path.parent)
            token=digest([record,[(name,None if data is None else hashlib.sha256(data).hexdigest()) for name,data in raw.items()]])
            can_undo=False
            if record and record['kind']=='transfer':
                try:inverse(documents,record,files);can_undo=True
                except ReconnectError:pass
            return dict(revision=token,record=record,documents=documents,can_undo=can_undo)

    def _commit(self,base,raw,documents,source,target,summary,kind):
        files={}
        for name,entries in documents.items():
            data=encode(name,entries)
            if decode(name,raw[name])==entries:continue
            files[name]=dict(before=None if raw[name] is None else b64encode(raw[name]).decode('ascii'),after=b64encode(data).decode('ascii'))
        if not files:raise ReconnectError('missing')
        record=dict(format=1,phase='pending',kind=kind,id=secrets.token_hex(12),at=int(time.time()),source=source,target=target,files=files,summary=summary)
        _write_record(base,record)  # logical commit point; readers must finish it before exposure
        recover_locked(base)

    def change(self,expected,source=None,target=None,verdict_choice='',budget_choice='',action='transfer',check=None):
        path=cache_file(FILENAME,self.base)
        if path is None:raise ReconnectError()
        with archive._locked(path.parent):
            state=self.state()
            if state['revision']!=expected:raise ReconnectError('conflict')
            record,files=_record(path.parent)
            if action=='clear':
                path.unlink(missing_ok=True);return
            raw,documents=snapshots_locked(path.parent)
            if action=='undo':
                changed=inverse(documents,record,files)
                self._commit(path.parent,raw,changed,record['target'],record['source'],record['summary'],'undo')
            elif action=='transfer':
                if check:check()
                changed,summary=transfer(documents,source,target,verdict_choice,budget_choice)
                self._commit(path.parent,raw,changed,source,target,summary,'transfer')
            else:raise ReconnectError('invalid')
