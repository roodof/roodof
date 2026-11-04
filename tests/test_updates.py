"""Invented signed releases only; never use owner keys, real agent data or a live service."""
import base64
import copy
from datetime import datetime,timedelta,timezone
import hashlib
from http.client import HTTPConnection
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile

from pler import updates as u,update_crypto
from pler.server import Server

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('update_signing_tools',ROOT/'tools/update_release.py')
signer=importlib.util.module_from_spec(spec);spec.loader.exec_module(signer)


def payload(release='0.2.32'):
    now=datetime.now(timezone.utc).replace(microsecond=0)
    return dict(format=1,product='pler',channel='early-beta',platform='windows-x64',version=release,
                published_at=now.isoformat(),expires_at=(now+timedelta(days=90)).isoformat(),
                url=u.ORIGIN+'/downloads/PLER-'+release+'-windows-x64.zip',sha256='a'*64,size=100,
                compatibility=dict(u.COMPATIBILITY),notes=dict(en='Invented update',tr='Uydurma güncelleme'))


def package_bytes(p,overrides=None,extra=()):
    files={'PLER.exe':b'invented executable','app/start.py':b'invented entry','app/pler/__init__.py':b'invented module',
           'runtime/python.exe':b'invented runtime'}
    files.update(overrides or {})
    manifest=dict(version=p['version'],platform='windows-x64',channel='early-beta',files={k:hashlib.sha256(v).hexdigest() for k,v in files.items()})
    out=io.BytesIO();root='PLER-'+p['version']+'-windows-x64/'
    with zipfile.ZipFile(out,'w') as z:
        for name,data in files.items():z.writestr(root+name,data)
        z.writestr(root+'manifest.json',u.canonical(manifest))
        for name,data in extra:z.writestr(name,data)
    return out.getvalue()


@unittest.skipUnless(os.name=='nt','Windows CNG release verification')
class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private,cls.public=signer.generate();cls.keys={update_crypto.key_id(cls.public):cls.public}

    def envelope(self,p=None):
        p=p or payload();_,sig=signer.sign(self.private,u.canonical(p))
        return u.canonical(dict(payload=p,key_id=update_crypto.key_id(self.public),signature=base64.b64encode(sig).decode()))

    def test_signed_payload_passes_and_changed_content_signature_and_key_fail_closed(self):
        raw=self.envelope();self.assertEqual(u.verified(raw,self.keys)['version'],'0.2.32')
        e=json.loads(raw);e['payload']['size']+=1
        for changed,keys in [(u.canonical(e),self.keys),(raw,{}),(raw.replace(b'Invented update',b'tampered update'),self.keys)]:
            with self.assertRaises(u.UpdateError):u.verified(changed,keys)
        e=json.loads(raw);e['signature']=base64.b64encode(b'\0'*384).decode()
        with self.assertRaises(u.UpdateError):u.verified(u.canonical(e),self.keys)

    def test_signed_wrong_product_url_platform_time_and_bad_fields_are_refused(self):
        for key,value in [('product','other'),('platform','linux'),('url','https://untrusted.invalid/a.zip'),
                          ('size',True),('version','01.2.3'),('published_at','2099-01-01T00:00:00+00:00'),
                          ('expires_at','2020-01-01T00:00:00+00:00')]:
            p=payload();p[key]=value
            with self.subTest(key=key),self.assertRaises(u.UpdateError):u.verified(self.envelope(p),self.keys)
        with self.assertRaises(u.UpdateError):u.decoded(b'{"x":1,"x":1}')
        with self.assertRaises(u.UpdateError):u.decoded(b'{"x":NaN}')

    def test_user_bound_key_file_roundtrips_without_shipping_private_material(self):
        sealed=signer.protect(self.private)
        self.assertNotEqual(sealed,self.private);self.assertEqual(signer.protect(sealed,True),self.private)
        self.assertNotIn(base64.b64encode(self.private),u.canonical(self.keys))

    def test_checking_is_opt_in_and_new_current_and_incompatible_releases_are_distinct(self):
        with tempfile.TemporaryDirectory() as folder:
            calls=[];p=payload();raw=[self.envelope(p)]
            def transport(url,*args,**kwargs):calls.append(url);return raw[0]
            manager=u.Manager(root=Path(folder)/'app',data=Path(folder)/'data',keys=self.keys,current='0.2.31',transport=transport)
            self.assertFalse(manager.view()['automatic']);manager.view();self.assertEqual(calls,[])
            manager.check();manager.thread.join(5);self.assertEqual(manager.state,'available')
            self.assertEqual(calls,[u.ORIGIN+u.FEED]);self.assertNotIn(folder,json.dumps(manager.view()))
            p=payload('0.2.32');p['compatibility']['work']=4;raw[0]=self.envelope(p)
            manager.check();manager.thread.join(5);self.assertEqual(manager.state,'manual_required');self.assertFalse(manager.view()['installable'])
            manager.current='0.2.32';manager.check();manager.thread.join(5);self.assertEqual(manager.state,'current')

    def test_signed_older_feed_cannot_undo_a_newer_seen_release(self):
        with tempfile.TemporaryDirectory() as folder:
            raw=[self.envelope(payload('0.2.33'))]
            manager=u.Manager(root=Path(folder)/'app',data=Path(folder)/'data',keys=self.keys,current='0.2.31',transport=lambda *a,**k:raw[0])
            manager.check();manager.thread.join(5)
            raw[0]=self.envelope(payload('0.2.32'));manager.check();manager.thread.join(5)
            self.assertEqual((manager.state,manager.error),('error','older_release'))

    def test_corrupt_preferences_are_preserved_and_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'data').mkdir();path=root/'data/update-choice.json';path.write_bytes(b'broken')
            manager=u.Manager(root=root/'app',data=root/'data',keys=self.keys)
            with self.assertRaises(u.UpdateError):manager.preferences(True)
            self.assertEqual(path.read_bytes(),b'broken')

    def test_bad_package_hash_never_closes_or_changes_the_running_installation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'app').mkdir();(root/'app/keep').write_bytes(b'old application');(root/'data').mkdir();(root/'data/private').write_bytes(b'private data')
            raw=self.envelope();closed=[]
            def transport(url,limit,destination=None,**kwargs):
                if destination:destination.write(b'bad');return 'b'*64
                return raw
            manager=u.Manager(root=root/'app',data=root/'data',keys=self.keys,current='0.2.31',transport=transport)
            manager.close_application=lambda:closed.append(True);manager.check();manager.thread.join(5);manager.install();manager.thread.join(10)
            self.assertEqual(manager.error,'package_hash');self.assertEqual(closed,[])
            self.assertEqual((root/'app/keep').read_bytes(),b'old application');self.assertEqual((root/'data/private').read_bytes(),b'private data')
            self.assertFalse(any(root.glob('*.lock')))

    def test_successful_package_extraction_matches_each_manifest_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            p=payload();path=Path(folder)/'package.zip';path.write_bytes(package_bytes(p))
            result=u.unpack(path,Path(folder)/'candidate',p)
            self.assertEqual((Path(folder)/'candidate/PLER.exe').read_bytes(),b'invented executable')
            self.assertEqual(result['version'],p['version'])

    def test_disk_write_backup_and_cancel_failures_preserve_app_and_private_data(self):
        from pler.usage import backup
        for failure in ('disk','write','backup','cancel'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);app=root/'app';app.mkdir();(app/'keep').write_bytes(b'old app')
                data=root/'data';data.mkdir();(data/'private').write_bytes(b'private work')
                p=payload();raw=package_bytes(p);p.update(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
                envelope=self.envelope(p);closed=[]
                def transport(url,limit,destination=None,**kwargs):
                    if destination:
                        destination.write(raw)
                        if failure=='cancel':manager.cancel.set()
                        return p['sha256']
                    return envelope
                manager=u.Manager(root=app,data=data,keys=self.keys,current='0.2.31',transport=transport)
                manager.close_application=lambda:closed.append(True)
                manager.check();manager.thread.join(5)
                target={'disk':'pler.updates.shutil.disk_usage','write':'pler.updates.tempfile.mkstemp',
                        'backup':'pler.usage.backup.create','cancel':'pler.updates.shutil.disk_usage'}[failure]
                options=({'return_value':type('Space',(),{'free':0})()} if failure=='disk' else
                         {'return_value':type('Space',(),{'free':2**40})()} if failure=='cancel' else
                         {'side_effect':PermissionError('invented read-only install')} if failure=='write' else
                         {'side_effect':backup.BackupError('invalid')})
                with patch(target,**options):manager.install();manager.thread.join(10)
                self.assertEqual(manager.error,{'disk':'disk_space','write':'unsafe_path','backup':'prepare_failed','cancel':'cancelled'}[failure])
                self.assertEqual(closed,[]);self.assertEqual((app/'keep').read_bytes(),b'old app')
                self.assertEqual((data/'private').read_bytes(),b'private work')
                self.assertFalse((app/'.pler-current').exists());self.assertFalse(any(root.glob('*.lock')))
                manager.close()

    def test_traversal_case_collisions_unknown_members_and_links_cannot_escape_staging(self):
        p=payload();prefix='PLER-'+p['version']+'-windows-x64/'
        for name in ('../outside',prefix+'../outside',prefix+'app/./start.py',prefix+'APP/START.PY',prefix+'app/CON.txt',prefix+'app/test:stream',prefix+'unknown'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/'package.zip';path.write_bytes(package_bytes(p,extra=[(name,b'bad')]))
                with self.assertRaises(u.UpdateError):u.unpack(path,Path(folder)/'candidate',p)
                self.assertFalse((Path(folder)/'outside').exists())
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'package.zip';path.write_bytes(package_bytes(p))
            with zipfile.ZipFile(path,'a') as z:
                info=zipfile.ZipInfo(prefix+'link');info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(info,'../outside')
            with self.assertRaises(u.UpdateError):u.unpack(path,Path(folder)/'candidate',p)

    def test_bad_member_hash_and_declared_expansion_limit_are_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            p=payload();raw=package_bytes(p).replace(b'invented executable',b'changed! executable')
            path=Path(folder)/'package.zip';path.write_bytes(raw)
            with self.assertRaises(u.UpdateError):u.unpack(path,Path(folder)/'candidate',p)
            path.write_bytes(package_bytes(p))
            with patch.object(u,'MAX_EXPANDED',1),self.assertRaises(u.UpdateError):u.unpack(path,Path(folder)/'bounded',p)


class PortableScopeTests(unittest.TestCase):
    def test_https_body_bounds_wrong_size_encoding_and_cancellation(self):
        class Response(io.BytesIO):
            status=200
            headers={}
        class Opener:
            def __init__(self,response):self.response=response
            def open(self,*args,**kwargs):return self.response
        for case in ('oversized','short','encoded','cancelled'):
            response=Response(b'12345');response.headers={'Content-Encoding':'gzip'} if case=='encoded' else {}
            cancel=threading.Event()
            if case=='cancelled':cancel.set()
            with self.subTest(case=case),patch('urllib.request.build_opener',return_value=Opener(response)):
                with self.assertRaises(u.UpdateError) as error:
                    u.fetch(u.ORIGIN+'/fixture',4 if case=='oversized' else 8,expected=6 if case=='short' else None,cancel=cancel)
                self.assertEqual(error.exception.code,{'oversized':'package_size','short':'package_size','encoded':'network','cancelled':'cancelled'}[case])

    @unittest.skipUnless(os.name=='nt','Windows protected staging ACL')
    def test_staging_directory_has_a_protected_dacl_before_private_backup_is_written(self):
        import ctypes as c
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'staging';path.mkdir();update_crypto.private_directory(path)
            adv=c.WinDLL('advapi32.dll');size=c.c_ulong()
            adv.GetFileSecurityW.argtypes=[c.c_wchar_p,c.c_ulong,c.c_void_p,c.c_ulong,c.POINTER(c.c_ulong)]
            adv.GetFileSecurityW.restype=c.c_int
            adv.GetFileSecurityW(str(path),4,None,0,c.byref(size));buffer=c.create_string_buffer(size.value)
            self.assertTrue(adv.GetFileSecurityW(str(path),4,buffer,size.value,c.byref(size)))
            adv.GetSecurityDescriptorControl.argtypes=[c.c_void_p,c.POINTER(c.c_ushort),c.POINTER(c.c_ulong)];adv.GetSecurityDescriptorControl.restype=c.c_int
            control=c.c_ushort();revision=c.c_ulong();self.assertTrue(adv.GetSecurityDescriptorControl(buffer,c.byref(control),c.byref(revision)))
            self.assertTrue(control.value&0x1000)
            (path/'private').write_bytes(b'invented private metadata');self.assertEqual((path/'private').read_bytes(),b'invented private metadata')

    def test_pending_selection_recovers_before_launch_without_deleting_new_version_or_data(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'runtime').mkdir();(root/'runtime/python.exe').write_bytes(b'baseline runtime');(root/'app').mkdir();(root/'app/start.py').write_bytes(b'baseline app')
            newer=root/'.pler-versions/0.2.32';(newer/'runtime').mkdir(parents=True);(newer/'runtime/python.exe').write_bytes(b'new runtime');(newer/'app').mkdir();(newer/'app/start.py').write_bytes(b'new app')
            u.write_pending(root,'0.2.32',None);u.write_pointer(root,'0.2.32')
            self.assertEqual(u.selected_root(root),newer)
            self.assertTrue(u.recover_pending(root));self.assertIsNone(u.pointer(root));self.assertEqual(u.selected_root(root),root)
            self.assertEqual((newer/'app/start.py').read_bytes(),b'new app')
            u.write_pending(root,'0.2.32',None);(root/'.pler-current').write_bytes(b'../../outside')
            with self.assertRaises(u.UpdateError):u.recover_pending(root)

    @unittest.skipUnless(os.name=='nt','Windows installation leases')
    def test_shared_instances_exclude_version_switch_and_os_handle_release_allows_it(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);a=update_crypto.InstallationLease(root);b=update_crypto.InstallationLease(root)
            try:
                with self.assertRaises(ValueError):update_crypto.InstallationLease(root,True)
            finally:a.close();b.close()
            exclusive=update_crypto.InstallationLease(root,True)
            try:
                with self.assertRaises(ValueError):update_crypto.InstallationLease(root)
            finally:exclusive.close()

    @unittest.skipUnless(os.name=='nt','Windows process/guard recovery')
    def test_guard_is_not_stolen_from_live_process_and_dead_guard_can_be_reclaimed(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'app';root.mkdir();guard=Path(folder)/'owned.lock';guard.write_text(str(os.getpid()))
            with self.assertRaises(u.UpdateError):u.recover_guard(root,guard)
            self.assertEqual(guard.read_text(),str(os.getpid()))
            with patch.object(update_crypto,'process_running',return_value=False):u.recover_guard(root,guard)
            self.assertFalse(guard.exists())

    def test_source_or_wheel_status_never_discovers_data_or_queries_a_provider(self):
        with patch.object(u,'cache_folder',side_effect=AssertionError('real metadata read')),patch.object(u,'fetch',side_effect=AssertionError('network')):
            manager=u.Manager();self.assertFalse(manager.view()['supported']);self.assertEqual(manager.view()['new_model_calls'],0)

    def test_update_api_requires_token_origin_and_bounded_exact_json(self):
        with tempfile.TemporaryDirectory() as folder:
            manager=u.Manager(root=Path(folder)/'app',data=Path(folder)/'data',keys={})
            class Board:
                def close(self,*args,**kwargs):pass
            server=Server(0,Board(),manager);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def request(method,path,body=None,token=True,origin=True):
                connection=HTTPConnection(*server.server_address,timeout=3)
                headers={'Host':server.origin.split('//')[1]}
                if token:headers['X-PLER-Token']=server.token
                if origin:headers['Origin']=server.origin
                if body is not None:headers['Content-Type']='application/json'
                connection.request(method,path,body,headers);response=connection.getresponse();raw=response.read();code=response.status;connection.close();return code,raw
            try:
                self.assertEqual(request('GET','/api/updates',token=False)[0],401)
                self.assertEqual(request('POST','/api/updates/check',b'{}',origin=False)[0],403)
                for raw in (b'{"url":"https://untrusted.invalid"}',b'{"automatic":true,"automatic":false}',b'[]'):
                    self.assertEqual(request('POST','/api/updates/preferences',raw)[0],400)
                self.assertEqual(request('POST','/api/updates/preferences',b'{"automatic":true}')[0],200)
                manager.state='downloading'
                self.assertEqual(request('POST','/api/usage/work',b'{}')[0],409)
                self.assertEqual(request('GET','/api/updates')[0],200)
            finally:server.shutdown();server.server_close();thread.join(3)


if __name__=='__main__':unittest.main()
