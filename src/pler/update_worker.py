"""Detached, locally staged portable update worker. Never restores/overwrites user data."""
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

from . import __version__,update_crypto
from .updates import (COMPATIBILITY,ORIGIN,UpdateError,decoded,local,read_small,version,verified,trusted_keys,write_json,
                      pointer,selected_root,write_pointer,write_pending,handoff_stage)


def probe(stage,expected):
    """Executed with the candidate runtime, before either installation is moved."""
    import ssl
    from . import server,update_crypto
    from .usage import backup,work_items
    from .reporting import SCHEMA_VERSION
    if expected!=__version__ or COMPATIBILITY!=dict(updater=1,schema=SCHEMA_VERSION,work=work_items.FORMAT,backup=backup.FORMAT):
        raise UpdateError('preflight')
    ssl.create_default_context();update_crypto.api()
    backup.inspect(read_small(Path(stage)/'data-backup.zip',backup.MAX_BUNDLE_BYTES))
    for name in ('index.html','app.js','app.css'):
        if not (server.WEB/name).is_file():raise UpdateError('preflight')


def process_handle(pid):
    if type(pid) is not int or not 0<pid<2**32:raise UpdateError('preflight')
    kernel=c.WinDLL('kernel32.dll',use_last_error=True)
    kernel.OpenProcess.argtypes=[c.c_ulong,c.c_int,c.c_ulong];kernel.OpenProcess.restype=c.c_void_p
    kernel.WaitForSingleObject.argtypes=[c.c_void_p,c.c_ulong];kernel.WaitForSingleObject.restype=c.c_ulong
    kernel.CloseHandle.argtypes=[c.c_void_p];kernel.CloseHandle.restype=c.c_int
    handle=kernel.OpenProcess(0x100000,0,pid)
    if not handle:raise UpdateError('preflight')
    return kernel,handle


def candidate_check(stage,p):
    candidate=local(stage/'candidate')
    manifest=decoded(read_small(candidate/'manifest.json',1024*1024),1024*1024)
    for name,wanted in manifest['files'].items():
        path=local(candidate.joinpath(*name.split('/')))
        if candidate not in path.parents or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=wanted:
            raise UpdateError('preflight')
    command=[str(candidate/'runtime/python.exe'),'-I','-S',str(candidate/'app/update_probe.py'),str(stage),p['version']]
    try:result=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                              timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    except (OSError,subprocess.TimeoutExpired):raise UpdateError('preflight')
    if result.returncode:raise UpdateError('preflight')


def start(root,stage,p,result):
    run=selected_root(root)
    env=os.environ.copy();env.pop('PLER_LAUNCHER_PID',None)
    env.update(PLER_INSTALL_ROOT=str(root),PLER_CACHE_DIR=p['data'],PLER_UPDATE_STAGE=str(stage),PLER_UPDATE_NONCE=p['nonce'],PLER_UPDATE_RESULT=result)
    return subprocess.Popen([str(run/'runtime/python.exe'),'-I','-S',str(run/'app/start.py'),*p['args']],
                            env=env,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))


def startup_ready(server,open_browser=None):
    """Write only to the validated updater's existing private staging directory."""
    value=os.environ.pop('PLER_UPDATE_STAGE',None);nonce=os.environ.pop('PLER_UPDATE_NONCE',None)
    result=os.environ.pop('PLER_UPDATE_RESULT',None)
    if not value:return False
    try:
        stage=local(value);p=decoded(read_small(stage/'plan.json'))
        root=local(p['root'])
        if (p['nonce']!=nonce or stage.parent!=root.parent or not stage.name.startswith('.pler-update-')
                or selected_root(root)!=Path(__file__).absolute().parents[2] or len(nonce)!=48):return False
        server.updates.state='activating'
        write_json(stage/'started.json',dict(nonce=nonce,version=__version__,origin=server.origin,token=server.token,result=result))
        server.updates.last_result=result
        def activate():
            deadline=time.monotonic()+30
            while time.monotonic()<deadline:
                try:
                    if decoded(read_small(stage/'activated.json'))==dict(nonce=nonce,active=True):
                        server.updates.lease=update_crypto.InstallationLease(root)
                        server.updates.state='idle'
                        if open_browser:open_browser()
                        if server.updates.automatic:server.updates.check()
                        return
                except (OSError,UpdateError,ValueError):pass
                time.sleep(.1)
            server.shutdown()
        import threading
        threading.Thread(target=activate,daemon=True).start()
        return True
    except (UpdateError,OSError,ValueError,TypeError,KeyError):return False


def healthy(stage,p,child,timeout=20):
    from http.client import HTTPConnection
    from urllib.parse import urlsplit
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if child.poll() is not None:return False
        try:
            result=decoded(read_small(stage/'started.json'))
            url=urlsplit(result['origin'])
            if (result['nonce']!=p['nonce'] or result['version']!=p['version'] or url.scheme!='http'
                    or url.hostname!='127.0.0.1' or not url.port or url.path or url.query or url.fragment):return False
            connection=HTTPConnection('127.0.0.1',url.port,timeout=2)
            try:
                connection.request('GET','/api/health',headers={'Host':url.netloc})
                response=connection.getresponse();body=decoded(response.read(4097),4096)
                return response.status==200 and body==dict(app='pler',version=p['version'])
            finally:connection.close()
        except (OSError,UpdateError,KeyError,ValueError):time.sleep(.1)
    return False


def perform(stage):
    stage=local(stage);p=decoded(read_small(stage/'plan.json'));root=local(p['root']);data=local(p['data'])
    if (p.get('format')!=1 or stage.parent!=root.parent or not stage.name.startswith('.pler-update-')
            or root==data or root in data.parents or not isinstance(p.get('args'),list)
            or len(p['args'])>32 or any(not isinstance(a,str) or len(a)>4096 for a in p['args'])
            or not isinstance(p.get('nonce'),str) or len(p['nonce'])!=48):raise UpdateError('preflight')
    payload=verified(read_small(stage/'release.json'),trusted_keys(),p['origin'])
    if payload['version']!=p['version'] or payload['compatibility']!=COMPATIBILITY or version(p['version'])<=version(p['current']):
        raise UpdateError('preflight')
    if hashlib.sha256((stage/'package.zip').read_bytes()).hexdigest()!=payload['sha256']:raise UpdateError('package_hash')
    guard=root.parent/('.pler-update-'+hashlib.sha256(str(root).casefold().encode()).hexdigest()[:20]+'.lock')
    if read_small(guard,32)!=str(p['parent_pid']).encode('ascii'):raise UpdateError('preflight')
    handles=[];switched=False;child=None;committed=False;lease=None
    candidate=stage/'candidate';installed=local(root/'.pler-versions'/p['version']);journal=local(root/'.pler-pending')
    try:
        handles.append(process_handle(p['parent_pid']))
        if p['launcher_pid']:handles.append(process_handle(p['launcher_pid']))
        candidate_check(stage,p)
        write_json(stage/'prepared.json',dict(nonce=p['nonce'],ready=True,worker_pid=os.getpid()))
        deadline=time.monotonic()+60
        while time.monotonic()<deadline:
            try:
                if decoded(read_small(stage/'commit.json'))==dict(nonce=p['nonce'],install=True):committed=True;break
            except OSError:pass
            if handles[0][0].WaitForSingleObject(handles[0][1],0)==0:raise UpdateError('cancelled')
            time.sleep(.1)
        else:raise UpdateError('cancelled')
        for kernel,handle in handles:
            if kernel.WaitForSingleObject(handle,30000)!=0:raise UpdateError('application_busy')
        try:lease=update_crypto.InstallationLease(root,exclusive=True)
        except ValueError:raise UpdateError('application_busy')
        if read_small(guard,32)!=str(p['parent_pid']).encode('ascii') or pointer(root)!=p['old_pointer']:raise UpdateError('application_busy')
        # The root launcher/runtime is never renamed or overwritten. Only a small pointer changes.
        installed.parent.mkdir(exist_ok=True)
        if installed.exists():
            if installed.parent!=local(root/'.pler-versions'):raise UpdateError('unsafe_path')
            installed.rename(stage/'unused-candidate')
        candidate.rename(installed)
        write_pending(root,p['version'],p['old_pointer'])
        write_pointer(root,p['version']);switched=True
        child=start(root,stage,p,'updated')
        if not healthy(stage,p,child):raise UpdateError('startup_failed')
        journal.unlink();lease.close();lease=None
        write_json(stage/'activated.json',dict(nonce=p['nonce'],active=True))
        write_json(stage/'result.json',dict(ok=True,version=p['version'],result='updated',data_restored=False))
    except Exception as error:
        if child and child.poll() is None:
            child.terminate();child.wait(10)
        if switched:
            write_pointer(root,p['old_pointer']);journal.unlink(missing_ok=True)
            lease.close();lease=None
            # Same data schema was required; never overwrite newer annotations with the backup.
            (stage/'started.json').unlink(missing_ok=True)
            fallback=dict(p,version=p['current'])
            child=start(root,stage,fallback,'rolled_back')
        elif committed and handles and handles[0][0].WaitForSingleObject(handles[0][1],0)==0:
            journal.unlink(missing_ok=True)
            if lease:lease.close();lease=None
            child=start(root,stage,dict(p,version=p['current']),'rolled_back')
        if child and committed:
            write_json(stage/'activated.json',dict(nonce=p['nonce'],active=True))
        write_json(stage/'result.json',dict(ok=False,version=p['version'],result='rolled_back' if switched else 'unchanged',
                                          code=error.code if isinstance(error,UpdateError) else 'switch_failed',data_restored=False))
    finally:
        if lease:lease.close()
        for kernel,handle in handles:kernel.CloseHandle(handle)
        try:
            if read_small(guard,32)==str(p['parent_pid']).encode('ascii'):guard.unlink()
        except OSError:pass


def main():
    try:perform(Path(sys.argv[1]));return 0
    except Exception:return 1


if __name__=='__main__':raise SystemExit(main())
