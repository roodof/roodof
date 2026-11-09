"""Invented backups only: no current history replacement or source reads."""
from http.client import HTTPConnection
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch, Mock

from pler import cli, desktop_profiles
from pler.recovery import Manager
from pler.usage import backup, verdicts
from pler.server import Server
from pler.dashboard import UsageDashboard


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.current=self.root/'current';self.current.mkdir()
        self.source=self.root/'source';self.source.mkdir()
        verdicts.Folder(self.source).save('a'*24,'useful')
        self.data=backup.create(self.source)
        self.manager=Manager(self.current,install=self.root/'application',anchor=self.current)
        self.addCleanup(self.manager.close)

    def plan(self,manager=None):
        manager=manager or self.manager
        state=manager.inspect(self.data);p=state['preview']
        return manager.act(dict(action='destination',ticket=p['ticket'],expected=p['expected'],parent=str(self.root)))['preview']

    def recover(self):
        p=self.plan()
        return self.manager.act(dict(action='restore',ticket=p['ticket'],expected=p['expected'],confirmed=True))['restored']

    def test_preview_and_destination_are_read_only_and_never_expose_bytes(self):
        before=list(self.root.rglob('*'));p=self.plan()
        self.assertEqual(before,list(self.root.rglob('*')))
        self.assertNotIn('data',p);self.assertEqual(p['summary']['verdicts'],1)
        self.assertFalse(Path(p['target']).exists())

    def test_restore_keeps_current_and_preserves_exact_annotation_bytes(self):
        (self.current/'keep.txt').write_text('untouched')
        restored=self.recover();target=Path(restored['target'])
        self.assertEqual((target/verdicts.FILENAME).read_bytes(),(self.source/verdicts.FILENAME).read_bytes())
        self.assertEqual((self.current/'keep.txt').read_text(),'untouched')
        self.assertIsNone(self.manager.state()['preview'])
        self.assertFalse((self.current/desktop_profiles.FILENAME).exists())

    def test_current_and_install_subtrees_and_network_destinations_refused(self):
        (self.root/'application').mkdir()
        for parent in (str(self.current),str(self.root/'application'),r'\\server\share'):
            p=self.manager.inspect(self.data)['preview']
            with self.assertRaises(backup.BackupError):
                self.manager.act(dict(action='destination',ticket=p['ticket'],expected=p['expected'],parent=parent))

    def test_changed_preview_expiry_confirmation_and_existing_target_never_write(self):
        p=self.plan();self.manager.inspect(self.data)
        with self.assertRaisesRegex(backup.BackupError,'conflict'):
            self.manager.act(dict(action='restore',ticket=p['ticket'],expected=p['expected'],confirmed=True))
        p=self.plan()
        with self.assertRaisesRegex(backup.BackupError,'invalid'):
            self.manager.act(dict(action='restore',ticket=p['ticket'],expected=p['expected'],confirmed=1))
        target=Path(p['target']);target.mkdir();(target/'keep').write_text('keep')
        with self.assertRaisesRegex(backup.BackupError,'exists'):
            self.manager.act(dict(action='restore',ticket=p['ticket'],expected=p['expected'],confirmed=True))
        self.assertEqual((target/'keep').read_text(),'keep')
        self.manager.preview['expires']=time.monotonic()-1
        with self.assertRaisesRegex(backup.BackupError,'conflict'):
            self.manager.act(dict(action='discard',ticket=p['ticket'],expected=p['expected']))

    def test_corrupt_backup_is_rejected_without_replacing_valid_preview(self):
        p=self.plan()
        with self.assertRaises(backup.BackupError):self.manager.inspect(b'not a ZIP')
        self.assertEqual(self.manager.state()['preview']['ticket'],p['ticket'])

    def test_open_persists_choice_and_previous_without_changing_environment(self):
        restored=self.recover();old=os.environ.get('PLER_CACHE_DIR')
        target=self.manager.select(dict(action='open',token=restored['token'],confirmed=True))
        self.assertEqual(os.environ.get('PLER_CACHE_DIR'),old)
        choice=desktop_profiles.read(self.current)
        self.assertEqual(choice,dict(selected=target,previous=self.current))
        other=Manager(target,anchor=self.current,previous=self.current);self.addCleanup(other.close)
        self.assertEqual(other.select(dict(action='previous',confirmed=True)),self.current)
        self.assertEqual(desktop_profiles.read(self.current)['previous'],target)

    def test_open_refuses_replaced_or_corrupt_restored_directory(self):
        restored=self.recover();target=Path(restored['target'])
        (target/verdicts.FILENAME).write_text('broken')
        with self.assertRaises(backup.BackupError):
            self.manager.select(dict(action='open',token=restored['token'],confirmed=True))
        self.assertFalse((self.current/desktop_profiles.FILENAME).exists())

    def test_unwritable_selection_leaves_recovery_and_current_intact(self):
        restored=self.recover()
        with patch('pler.desktop_profiles.os.replace',side_effect=PermissionError()):
            with self.assertRaises(backup.BackupError):
                self.manager.select(dict(action='open',token=restored['token'],confirmed=True))
        self.assertFalse(self.manager.switching)
        self.assertTrue(Path(restored['target']).is_dir())

    def test_partial_write_is_not_advertised_as_success(self):
        p=self.plan()
        with patch('pler.usage.backup._write_new',side_effect=OSError()):
            with self.assertRaises(backup.BackupError):
                self.manager.act(dict(action='restore',ticket=p['ticket'],expected=p['expected'],confirmed=True))
        self.assertIsNone(self.manager.restored);self.assertFalse(Path(p['target']).exists())

    def test_post_publish_sync_error_keeps_verified_complete_result_accessible(self):
        p=self.plan();sync=backup._sync_directory
        def interrupted(path):
            if path==self.root:raise OSError('invented after publish')
            sync(path)
        with patch('pler.usage.backup._sync_directory',side_effect=interrupted):
            value=self.manager.act(dict(action='restore',ticket=p['ticket'],expected=p['expected'],confirmed=True))
        self.assertTrue(value['restored']['summary']['durability_uncertain'])
        self.assertTrue(Path(value['restored']['target']).is_dir())

    def test_malformed_selector_is_preserved_and_not_followed(self):
        file=self.current/desktop_profiles.FILENAME;file.write_text('{broken')
        with self.assertRaises(backup.BackupError):desktop_profiles.read(self.current)
        with self.assertRaises(backup.BackupError):desktop_profiles.save(self.current,self.source,self.current)
        self.assertEqual(file.read_text(),'{broken')

    def test_normal_desktop_remembers_but_explicit_folder_bypasses_choice(self):
        desktop_profiles.save(self.current,self.source,self.current)
        observed=[]
        def once(*args):
            observed.append((os.environ.get('PLER_CACHE_DIR'),args[-1]));return None,None
        with patch.dict(os.environ,{},clear=False):
            os.environ.pop('PLER_CACHE_DIR',None)
            with patch('pler.paths.cache_folder',return_value=self.current),patch('pler.cli._serve_once',side_effect=once):
                self.assertIsNone(cli.serve(desktop=True))
            self.assertNotIn('PLER_CACHE_DIR',os.environ)
        self.assertEqual(observed[-1][0],str(self.source))
        with patch.dict(os.environ,PLER_CACHE_DIR=str(self.current)),patch('pler.cli._serve_once',side_effect=once):
            cli.serve(desktop=True)
        self.assertEqual(observed[-1][0],str(self.current));self.assertIsNone(observed[-1][1][0])

    def test_http_auth_admission_no_snapshot_restore_and_browser_open_refusal(self):
        with patch.dict(os.environ,PLER_CACHE_DIR=str(self.current)):
            board=UsageDashboard(reader=lambda:([],{}),manage_sources=False)
            server=Server(0,dashboard=board)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(lambda:(server.shutdown(),thread.join(3),server.server_close()))
        def request(method,route,body=None,kind='application/json',auth=True,origin=True):
            connection=HTTPConnection('127.0.0.1',server.server_port,timeout=8)
            headers={'Content-Type':kind}
            if auth:headers['X-PLER-Token']=server.token
            if origin:headers['Origin']=server.origin
            if isinstance(body,dict):body=json.dumps(body)
            connection.request(method,route,body,headers)
            response=connection.getresponse();result=json.loads(response.read());code=response.status;connection.close()
            return code,result
        route='/api/usage/recovery'
        self.assertEqual(request('GET',route,auth=False)[0],401)
        self.assertEqual(request('POST',route+'/preview',self.data,'application/octet-stream',origin=False)[0],403)
        self.assertEqual(request('POST',route,'{"action":"previous","confirmed":true,"confirmed":true}')[0],400)
        status,state=request('POST',route+'/preview',self.data,'application/octet-stream');self.assertEqual(status,200,state)
        p=state['preview'];status,state=request('POST',route,dict(action='destination',ticket=p['ticket'],expected=p['expected'],parent=str(self.root)))
        self.assertEqual(status,200,state);p=state['preview']
        status,state=request('POST',route,dict(action='restore',ticket=p['ticket'],expected=p['expected'],confirmed=True))
        self.assertEqual(status,200,state)
        self.assertEqual(request('POST',route,dict(action='open',token=state['restored']['token'],confirmed=True))[1]['reason'],'desktop_required')
        self.assertFalse(server.recovery.switching)

