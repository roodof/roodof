"""Opt-in Windows portable updates. GET/status never contacts the release service.

Only a pinned-key signed release can select a package at the fixed release origin.
No agent/account data is transmitted. Installation runs outside the live installation.
"""
import base64
from datetime import datetime,timedelta,timezone
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
from urllib.error import HTTPError,URLError
from urllib.parse import urlsplit
import zipfile

from . import __version__,update_crypto
from .paths import cache_folder,local_path

ORIGIN='https://pler-local-usage.oguzay5555.chatgpt.site'
FEED='/updates/windows-x64/early-beta.json'
COMPATIBILITY=dict(updater=2,schema=2,work=3,backup=1)
MAX_PACKAGE=256*1024*1024
MAX_EXPANDED=768*1024*1024
MAX_FEED=32768
BUSY={'checking','downloading','preparing','backing_up','restarting','activating'}


class UpdateError(Exception):
    def __init__(self,code):self.code=code;super().__init__(code)


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('utf-8')


def decoded(raw,limit=MAX_FEED):
    if not isinstance(raw,bytes) or len(raw)>limit:raise UpdateError('invalid_release')
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('duplicate')
            result[key]=value
        return result
    try:return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('number')))
    except (ValueError,UnicodeError,RecursionError):raise UpdateError('invalid_release')


def read_small(path,limit=MAX_FEED):
    path=local(path)
    with path.open('rb') as file:
        raw=file.read(limit+1)
    if len(raw)>limit:raise UpdateError('invalid_release')
    return raw


def version(value):
    if not isinstance(value,str) or not re.fullmatch(r'(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})',value):
        raise UpdateError('invalid_release')
    return tuple(map(int,value.split('.')))


def stamp(value):
    try:
        result=datetime.fromisoformat(value)
        if result.tzinfo is None:raise ValueError('timezone')
        return result.astimezone(timezone.utc)
    except (ValueError,TypeError):raise UpdateError('invalid_release')


def validate_payload(p,origin=ORIGIN,now=None):
    now=now or datetime.now(timezone.utc)
    fields={'format','product','channel','platform','version','published_at','expires_at','url','sha256','size','compatibility','notes'}
    if not isinstance(p,dict) or set(p)!=fields:raise UpdateError('invalid_release')
    if type(p['format']) is not int or p['format']!=1 or p['product']!='pler' or p['platform']!='windows-x64' or p['channel']!='early-beta':
        raise UpdateError('invalid_release')
    version(p['version'])
    if p['url']!=origin+'/downloads/PLER-'+p['version']+'-windows-x64.zip':raise UpdateError('invalid_release')
    if not isinstance(p['sha256'],str) or not re.fullmatch('[a-f0-9]{64}',p['sha256']):raise UpdateError('invalid_release')
    if type(p['size']) is not int or not 0<p['size']<=MAX_PACKAGE:raise UpdateError('invalid_release')
    start,end=stamp(p['published_at']),stamp(p['expires_at'])
    if not start<=now+timedelta(minutes=5) or not start<end<=start+timedelta(days=91) or end<=now:raise UpdateError('expired_release')
    compat=p['compatibility']
    if not isinstance(compat,dict) or set(compat)!=set(COMPATIBILITY) or any(type(x) is not int or x<1 for x in compat.values()):raise UpdateError('invalid_release')
    if not isinstance(p['notes'],dict) or set(p['notes'])!={'en','tr'} or any(not isinstance(x,str) or len(x)>1000 for x in p['notes'].values()):
        raise UpdateError('invalid_release')
    return p


def trusted_keys():
    data=decoded(read_small(Path(__file__).with_name('update_keys.json')))
    if not isinstance(data,dict) or set(data)!={'format','keys'} or data['format']!=1 or not isinstance(data['keys'],dict):raise UpdateError('trust_unavailable')
    for kid,blob in data['keys'].items():
        if update_crypto.key_id(blob)!=kid:raise UpdateError('trust_unavailable')
    return data['keys']


def verified(raw,keys,origin=ORIGIN,now=None):
    e=decoded(raw)
    if not isinstance(e,dict) or set(e)!={'payload','key_id','signature'}:raise UpdateError('invalid_release')
    if not isinstance(e['key_id'],str) or e['key_id'] not in keys:raise UpdateError('untrusted_release')
    try:
        if not isinstance(e['signature'],str) or len(e['signature'])>800:raise ValueError('signature')
        signature=base64.b64decode(e['signature'],validate=True)
        if not update_crypto.verify(keys[e['key_id']],canonical(e['payload']),signature):raise ValueError('signature')
    except (ValueError,TypeError,OSError):raise UpdateError('untrusted_release')
    return validate_payload(e['payload'],origin,now)


def fetch(url,limit,destination=None,expected=None,progress=None,cancel=None):
    """Bounded HTTPS, system trust, no redirects or caller-supplied headers/credentials."""
    import ssl
    from urllib.request import build_opener,HTTPSHandler,HTTPRedirectHandler,Request
    if urlsplit(url).scheme!='https':raise UpdateError('network')
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):raise UpdateError('network')
    context=ssl.create_default_context();context.minimum_version=ssl.TLSVersion.TLSv1_2
    opener=build_opener(HTTPSHandler(context=context),NoRedirect())
    started=time.monotonic();result=bytearray();written=0;digest=hashlib.sha256()
    try:
        with opener.open(Request(url,headers={'User-Agent':'PLER-update/1','Accept-Encoding':'identity'}),timeout=15) as response:
            if response.status!=200 or response.headers.get('Content-Encoding') not in (None,'identity'):raise UpdateError('network')
            length=response.headers.get('Content-Length')
            if length is not None and (not length.isdecimal() or int(length)>limit or expected is not None and int(length)!=expected):
                raise UpdateError('package_size')
            while True:
                if cancel and cancel.is_set():raise UpdateError('cancelled')
                if time.monotonic()-started>120:raise UpdateError('network')
                chunk=response.read(min(65536,limit-written+1))
                if not chunk:break
                written+=len(chunk)
                if written>limit:raise UpdateError('package_size')
                digest.update(chunk)
                if destination:destination.write(chunk)
                else:result.extend(chunk)
                if progress:progress(written)
        if expected is not None and written!=expected:raise UpdateError('package_size')
        return digest.hexdigest() if destination else bytes(result)
    except (HTTPError,URLError,TimeoutError,OSError,ValueError):raise UpdateError('network')


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.update-',dir=str(path.parent))
    try:
        with os.fdopen(fd,'wb') as file:file.write(canonical(value));file.flush();os.fsync(file.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


def local(value):
    path=local_path(str(Path(value).absolute()))
    if path is None:raise UpdateError('unsafe_path')
    return path


def pointer(root):
    path=local(root/'.pler-current')
    if not path.exists():return None
    value=read_small(path,64).decode('ascii').strip();version(value)
    return value


def selected_root(root):
    value=pointer(root);selected=local(root/'.pler-versions'/value) if value else root
    if not (selected/'runtime/python.exe').is_file() or not (selected/'app/start.py').is_file():raise UpdateError('invalid_installation')
    return selected


def write_pointer(root,value):
    target=local(root/'.pler-current')
    if value is None:target.unlink(missing_ok=True);return
    version(value);fd,name=tempfile.mkstemp(prefix='.pler-pointer-',dir=str(root))
    try:
        with os.fdopen(fd,'wb') as file:file.write((value+'\n').encode('ascii'));file.flush();os.fsync(file.fileno())
        os.replace(name,target)
    finally:
        if os.path.exists(name):os.unlink(name)


def write_pending(root,new,old):
    version(new)
    if old is not None:version(old)
    target=local(root/'.pler-pending')
    if target.exists():raise UpdateError('application_busy')
    fd,name=tempfile.mkstemp(prefix='.pler-journal-',dir=str(root))
    try:
        with os.fdopen(fd,'wb') as file:
            file.write((new+'\n'+(old or 'base')+'\n').encode('ascii'));file.flush();os.fsync(file.fileno())
        os.rename(name,target)  # complete journal exists before the active pointer can change
    finally:
        if os.path.exists(name):os.unlink(name)


def recover_pending(root):
    """Called under the exclusive installation lease before a normal user launch."""
    path=local(root/'.pler-pending')
    if not path.exists():return False
    lines=read_small(path,128).decode('ascii').splitlines()
    if len(lines)!=2:raise UpdateError('invalid_installation')
    new,old=lines;version(new)
    old=None if old=='base' else old
    if old is not None:version(old)
    if pointer(root) not in (new,old):raise UpdateError('invalid_installation')
    previous=local(root/'.pler-versions'/old) if old else root
    if not (previous/'runtime/python.exe').is_file() or not (previous/'app/start.py').is_file():raise UpdateError('invalid_installation')
    write_pointer(root,old);path.unlink();return True


def handoff_stage(root):
    stage=os.environ.get('PLER_UPDATE_STAGE');nonce=os.environ.get('PLER_UPDATE_NONCE')
    if not stage or not nonce:return None
    try:
        stage=local(stage);plan=decoded(read_small(stage/'plan.json'))
        if (stage.parent==root.parent and stage.name.startswith('.pler-update-') and plan['root']==str(root)
                and plan['nonce']==nonce and re.fullmatch('[a-f0-9]{48}',nonce)):
            return stage
    except (UpdateError,OSError,KeyError,ValueError,TypeError):pass
    return None


def recover_guard(root,guard):
    """Only reclaim a matching dead-parent/dead-worker guard; never steal a live update."""
    raw=read_small(guard,32)
    try:pid=int(raw.decode('ascii'))
    except (ValueError,UnicodeError):raise UpdateError('busy_installation')
    if update_crypto.process_running(pid):raise UpdateError('busy_installation')
    count=0
    for entry in os.scandir(root.parent):
        if not entry.name.startswith('.pler-update-') or not entry.is_dir(follow_symlinks=False):continue
        count+=1
        if count>64:raise UpdateError('busy_installation')
        stage=local(root.parent/entry.name)
        try:plan=decoded(read_small(stage/'plan.json'))
        except FileNotFoundError:continue
        if plan.get('root')!=str(root) or plan.get('parent_pid')!=pid:continue
        try:ack=decoded(read_small(stage/'prepared.json'))
        except FileNotFoundError:continue  # no prepared/committed worker can switch the pointer
        if update_crypto.process_running(ack.get('worker_pid')):raise UpdateError('busy_installation')
    if read_small(guard,32)!=raw:raise UpdateError('busy_installation')
    guard.unlink()


def unpack(package,destination,payload):
    """Validate every ZIP name, bounded size and manifest hash before using extracted code."""
    destination=local(destination)
    if destination.exists():raise UpdateError('invalid_package')
    root='PLER-'+payload['version']+'-windows-x64'
    try:
        with zipfile.ZipFile(package) as bundle:
            entries=bundle.infolist();seen=set();files={};expanded=0
            if len(entries)>2048:raise UpdateError('invalid_package')
            for info in entries:
                name=info.filename;parts=PurePosixPath(name).parts
                if (not parts or parts[0]!=root or name!='/'.join(parts)+('/' if info.is_dir() else '') or '\\' in name or name.startswith('/') or info.flag_bits&1
                        or any(x in ('.','..') or not x or x[-1] in ' .' or ':' in x or any(ord(c)<32 for c in x)
                               or re.fullmatch(r'(?i)(con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\..*)?',x) for x in parts)):
                    raise UpdateError('invalid_package')
                normalized='/'.join(parts).casefold()
                if normalized in seen:raise UpdateError('invalid_package')
                seen.add(normalized)
                kind=stat.S_IFMT(info.external_attr>>16)
                if kind not in (0,stat.S_IFDIR if info.is_dir() else stat.S_IFREG) or info.external_attr&0x400:
                    raise UpdateError('invalid_package')
                if info.is_dir():continue
                if len(parts)<2 or info.file_size>256*1024*1024:raise UpdateError('invalid_package')
                expanded+=info.file_size
                if expanded>MAX_EXPANDED:raise UpdateError('invalid_package')
                relative='/'.join(parts[1:]);files[relative]=info
            if 'manifest.json' not in files or files['manifest.json'].file_size>1024*1024:raise UpdateError('invalid_package')
            manifest=decoded(bundle.read(files['manifest.json']),1024*1024)
            hashes=manifest.get('files') if isinstance(manifest,dict) else None
            if (not isinstance(manifest,dict) or manifest.get('version')!=payload['version'] or manifest.get('platform')!='windows-x64'
                    or manifest.get('channel')!=payload['channel'] or not isinstance(hashes,dict)
                    or set(hashes)!=set(files)-{'manifest.json'}
                    or not {'PLER.exe','app/start.py','app/pler/__init__.py','runtime/python.exe'}<=set(hashes)
                    or any(not isinstance(v,str) or not re.fullmatch('[a-f0-9]{64}',v) for v in hashes.values())):
                raise UpdateError('invalid_package')
            destination.mkdir()
            for relative,info in files.items():
                path=destination.joinpath(*relative.split('/'));path.parent.mkdir(parents=True,exist_ok=True)
                digest=hashlib.sha256();count=0
                with bundle.open(info) as source,path.open('xb') as target:
                    while True:
                        chunk=source.read(65536)
                        if not chunk:break
                        count+=len(chunk)
                        if count>info.file_size:raise UpdateError('invalid_package')
                        digest.update(chunk);target.write(chunk)
                if count!=info.file_size or relative!='manifest.json' and digest.hexdigest()!=hashes[relative]:raise UpdateError('invalid_package')
            return manifest
    except (OSError,ValueError,KeyError,zipfile.BadZipFile,RuntimeError,NotImplementedError):raise UpdateError('invalid_package')


def portable_root():
    if os.name!='nt':return None
    run_root=Path(__file__).absolute().parents[2]
    root=local(os.environ.get('PLER_INSTALL_ROOT',str(run_root)))
    if (Path(sys.executable).absolute()!=run_root/'runtime/python.exe' or not (root/'PLER.exe').is_file()
            or not (root/'manifest.json').is_file()):return None
    if selected_root(root)!=run_root:return None
    return root


class Manager:
    def __init__(self,root=None,data=None,keys=None,origin=ORIGIN,current=__version__,transport=fetch,restart_args=()):
        self.root=portable_root() if root is None else local(root)
        self.run_root=Path(__file__).absolute().parents[2]
        self.data=local(data) if data is not None else None
        self.keys=keys;self.origin=origin;self.current=current;self.transport=transport
        self.args=list(restart_args);self.lock=threading.RLock();self.cancel=threading.Event();self.thread=None
        self.state='idle' if self.root else 'unsupported';self.error=None;self.payload=None;self.envelope=None;self.received=0
        self.automatic=False;self.seen=None;self.close_application=None;self.closed=False
        self.last_result=None
        self.lease=None
        self.handoff=handoff_stage(self.root) if self.root else None
        if self.root:
            if os.name=='nt' and (self.root/'runtime/python.exe').is_file() and self.handoff is None:
                try:self.lease=update_crypto.InstallationLease(self.root)
                except ValueError:raise UpdateError('application_busy')
            try:
                self.data=self.data or local(cache_folder());self.settings=local(self.data/'update-choice.json')
                if self.root==self.data or self.root in self.data.parents:raise UpdateError('unsafe_path')
                if self.settings.exists():
                    settings=decoded(read_small(self.settings))
                    if set(settings)!={'format','automatic','seen'} or settings['format']!=1 or type(settings['automatic']) is not bool:raise ValueError('preferences')
                    self.automatic=settings['automatic'];self.seen=settings['seen']
                    if self.seen is not None:version(self.seen)
            except (OSError,ValueError,TypeError,UpdateError):self.state='error';self.error='preferences';self.automatic=False

    def view(self):
        with self.lock:
            return dict(supported=bool(self.root),state=self.state,error=self.error,current_version=self.current,
                        available_version=self.payload['version'] if self.payload else None,
                        size=self.payload['size'] if self.payload else None,received=self.received,
                        notes=self.payload['notes'] if self.payload else {},automatic=self.automatic,
                        installable=bool(self.state=='available' and self.payload and self.payload['compatibility']==COMPATIBILITY and version(self.payload['version'])>version(self.current)),
                        last_result=self.last_result,network_scope='release_metadata_and_package_only',new_model_calls=0)

    def _save(self):write_json(self.settings,dict(format=1,automatic=self.automatic,seen=self.seen))

    def preferences(self,automatic):
        with self.lock:
            if not self.root or self.state in BUSY or self.error=='preferences':raise UpdateError('unavailable')
            prior=self.automatic;self.automatic=automatic
            try:self._save()
            except OSError:self.automatic=prior;raise UpdateError('preferences')
        return self.view()

    def check(self):
        with self.lock:
            if self.closed or not self.root or self.state in BUSY or self.error=='preferences':raise UpdateError('unavailable')
            self.state='checking';self.error=None;self.payload=None;self.envelope=None;self.received=0
            self.thread=threading.Thread(target=self._check,daemon=True);self.thread.start()
        return self.view()

    def _check(self):
        try:
            keys=trusted_keys() if self.keys is None else self.keys
            if not keys:raise UpdateError('trust_unavailable')
            raw=self.transport(self.origin+FEED,MAX_FEED,cancel=self.cancel)
            payload=verified(raw,keys,self.origin)
            if self.seen and version(payload['version'])<version(self.seen):raise UpdateError('older_release')
            with self.lock:
                self.seen=payload['version'];self._save();self.payload=payload;self.envelope=raw
                self.state=('current' if version(payload['version'])<=version(self.current) else
                            'available' if payload['compatibility']==COMPATIBILITY else 'manual_required')
        except Exception as error:
            with self.lock:self.state='error';self.error=error.code if isinstance(error,UpdateError) else 'preferences'

    def install(self):
        with self.lock:
            if self.closed or self.state!='available' or not self.close_application:raise UpdateError('unavailable')
            self.state='downloading';self.error=None
            self.thread=threading.Thread(target=self._install,daemon=True);self.thread.start()
        return self.view()

    def _install(self):
        stage=None;guard=None;worker=None
        try:
            payload=verified(self.envelope,trusted_keys() if self.keys is None else self.keys,self.origin)
            if payload['compatibility']!=COMPATIBILITY or version(payload['version'])<=version(self.current):raise UpdateError('manual_required')
            root=local(self.root);parent=local(root.parent)
            guard=parent/('.pler-update-'+hashlib.sha256(str(root).casefold().encode()).hexdigest()[:20]+'.lock')
            try:
                with guard.open('xb') as file:file.write(str(os.getpid()).encode('ascii'))
            except FileExistsError:
                try:
                    recover_guard(root,guard)
                    with guard.open('xb') as file:file.write(str(os.getpid()).encode('ascii'))
                except Exception:guard=None;raise UpdateError('busy_installation')
            if shutil.disk_usage(parent).free<MAX_EXPANDED+128*1024*1024:raise UpdateError('disk_space')
            try:
                probe_fd,probe_name=tempfile.mkstemp(prefix='.pler-write-probe-',dir=str(root))
                os.close(probe_fd);os.unlink(probe_name)
            except OSError:raise UpdateError('unsafe_path')
            stage=Path(tempfile.mkdtemp(prefix='.pler-update-',dir=str(parent)))
            update_crypto.private_directory(stage)
            package=stage/'package.zip'
            def progress(amount):
                with self.lock:self.received=amount
            with package.open('xb') as file:
                actual=self.transport(payload['url'],payload['size'],destination=file,expected=payload['size'],progress=progress,cancel=self.cancel)
                file.flush();os.fsync(file.fileno())
            if actual!=payload['sha256']:raise UpdateError('package_hash')
            with self.lock:self.state='preparing'
            candidate=stage/'candidate';unpack(package,candidate,payload)
            if self.cancel.is_set():raise UpdateError('cancelled')
            with self.lock:self.state='backing_up'
            from .usage import backup
            data=backup.create(self.data);backup.inspect(data)
            with (stage/'data-backup.zip').open('xb') as file:file.write(data);file.flush();os.fsync(file.fileno())
            # The worker's runtime stays outside both installations, including its loaded DLLs.
            shutil.copytree(self.run_root/'runtime',stage/'worker/runtime')
            shutil.copytree(self.run_root/'app',stage/'worker/app',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            (stage/'release.json').write_bytes(self.envelope)
            nonce=secrets.token_hex(24)
            plan=dict(format=1,root=str(root),data=str(self.data),parent_pid=os.getpid(),launcher_pid=int(os.environ.get('PLER_LAUNCHER_PID','0')),
                      current=self.current,version=payload['version'],old_pointer=pointer(root),args=self.args,nonce=nonce,origin=self.origin)
            write_json(stage/'plan.json',plan)
            worker=subprocess.Popen([str(stage/'worker/runtime/python.exe'),'-I','-S',str(stage/'worker/app/update_worker.py'),str(stage)],
                                    stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            deadline=time.monotonic()+45
            while time.monotonic()<deadline:
                if (stage/'prepared.json').exists():
                    ack=decoded(read_small(stage/'prepared.json'))
                    if ack.get('nonce')==nonce and ack.get('ready') is True and type(ack.get('worker_pid')) is int:break
                    raise UpdateError('preflight')
                if worker.poll() is not None:raise UpdateError('preflight')
                if self.cancel.wait(.1):raise UpdateError('cancelled')
            else:raise UpdateError('preflight')
            # The action handler freezes edits while BUSY. Only now request a normal shutdown.
            write_json(stage/'commit.json',dict(nonce=nonce,install=True))
            with self.lock:self.state='restarting'
            guard=None  # worker now owns the installation lock
            self.close_application()
        except Exception as error:
            if worker and worker.poll() is None:worker.terminate();worker.wait(10)
            with self.lock:self.state='error';self.error=error.code if isinstance(error,UpdateError) else 'prepare_failed'
        finally:
            if guard:
                try:guard.unlink()
                except OSError:pass

    def close(self):
        with self.lock:
            self.closed=True
            if self.state!='restarting':self.cancel.set()
        if self.thread and self.thread is not threading.current_thread() and self.state!='restarting':self.thread.join(17)
        if self.lease:self.lease.close()
