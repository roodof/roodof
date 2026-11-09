import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime,timezone

from pler.usage import reconnections as rules,work_items,verdicts,budgets,archive
from pler.usage.records import Session
from pler.dashboard import UsageDashboard

OLD='a'*24
NEW='b'*24
OTHER='c'*24


class ReconnectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.work=work_items.Folder(self.base);self.verdicts=verdicts.Folder(self.base);self.budgets=budgets.Store(self.base)
        self.store=rules.Store(self.base)
        self.item=self.work.mutate('create',title='Private work',session=OLD)['id']
        self.work.mutate('link',identity=self.item,session=NEW)
        self.verdicts.save(OLD,'useful');self.verdicts.save(NEW,'wasted')
        self.budgets.change(lambda entries:entries.update({OLD:dict(metric='tokens',limit=100,revision='d'*24,notified=[80]),NEW:dict(metric='usd',limit=2,revision='e'*24,notified=[])}))

    def transfer(self):
        self.store.change(self.store.state()['revision'],OLD,NEW,'source','source')

    def files(self):return {name:(self.base/name).read_bytes() if (self.base/name).exists() else None for name in (*rules.NAMES,rules.FILENAME)}

    def test_transfer_merges_links_and_explicitly_resolves_both_conflicts(self):
        self.transfer()
        self.assertEqual(self.work.read()[self.item]['sessions'],[NEW])
        self.assertEqual(self.verdicts.read(),{NEW:'useful'})
        values=self.budgets.read();self.assertNotIn(OLD,values)
        self.assertEqual((values[NEW]['metric'],values[NEW]['limit'],values[NEW]['notified']),('tokens',100,[80]))
        self.assertNotEqual(values[NEW]['revision'],'d'*24)
        self.assertEqual(self.store.state()['record']['phase'],'complete')

    def test_missing_choice_or_stale_preview_cannot_write(self):
        before=self.files();revision=self.store.state()['revision']
        with self.assertRaises(rules.ReconnectError):self.store.change(revision,OLD,NEW)
        self.assertEqual(before,self.files())
        self.verdicts.save(OTHER,'useful');before=self.files()
        with self.assertRaisesRegex(rules.ReconnectError,'could not'):self.store.change(revision,OLD,NEW,'source','source')
        self.assertEqual(before,self.files())

    def test_target_choices_keep_target_settings_and_remove_old_refs(self):
        self.store.change(self.store.state()['revision'],OLD,NEW,'target','target')
        self.assertEqual(self.verdicts.read(),{NEW:'wasted'})
        self.assertEqual(self.budgets.read()[NEW]['metric'],'usd')

    def test_interrupted_transfer_rolls_forward_before_an_annotation_read(self):
        install=rules._install
        def failing(base,name,data):
            if name==verdicts.FILENAME:raise OSError('invented disk interruption')
            return install(base,name,data)
        with patch.object(rules,'_install',side_effect=failing):
            with self.assertRaises(OSError):self.transfer()
        self.assertEqual(json.loads((self.base/rules.FILENAME).read_text())['phase'],'pending')
        # This is an ordinary old read API, not an explicit recovery call.
        self.assertEqual(self.verdicts.read(),{NEW:'useful'})
        self.assertEqual(self.work.read()[self.item]['sessions'],[NEW])
        self.assertNotIn(OLD,self.budgets.read())
        self.assertEqual(self.store.state()['record']['phase'],'complete')

    def test_unexpected_edit_during_pending_recovery_is_preserved(self):
        install=rules._install
        def failing(base,name,data):
            if name in rules.NAMES:raise OSError('invented interruption')
            return install(base,name,data)
        with patch.object(rules,'_install',side_effect=failing):
            with self.assertRaises(OSError):self.transfer()
        path=self.base/verdicts.FILENAME
        modified=dict(format=1,verdicts={OTHER:dict(verdict='wasted',at=1)})
        path.write_text(json.dumps(modified),encoding='utf-8');before=self.files()
        with self.assertRaises(rules.ReconnectError):self.work.read()
        self.assertEqual(before,self.files())

    def test_undo_preserves_unrelated_notes_entries_and_automatic_acknowledgements(self):
        self.transfer();item=self.work.read()[self.item]
        self.work.mutate('describe',identity=self.item,details=dict(goal='New note after transfer',outcome='not_recorded',result_note=''),expected_revision=work_items.details_revision(item))
        self.verdicts.save(OTHER,'wasted')
        def changed(entries):
            entries[NEW]['notified']=[80,100]
            entries[OTHER]=dict(metric='tokens',limit=42,revision='f'*24,notified=[])
        self.budgets.change(changed)
        state=self.store.state();self.assertTrue(state['can_undo'])
        self.store.change(state['revision'],action='undo')
        item=self.work.read()[self.item]
        self.assertEqual(set(item['sessions']),{OLD,NEW});self.assertEqual(item['goal'],'New note after transfer')
        self.assertEqual(self.verdicts.read(),{OLD:'useful',NEW:'wasted',OTHER:'wasted'})
        self.assertEqual(self.budgets.read()[OLD]['revision'],'d'*24)
        self.assertEqual(self.budgets.read()[OTHER]['limit'],42)
        self.assertFalse(self.store.state()['can_undo'])

    def test_changed_target_budget_blocks_undo_without_overwriting(self):
        self.transfer()
        self.budgets.change(lambda entries:entries[NEW].update(limit=300,revision='f'*24))
        state=self.store.state();self.assertFalse(state['can_undo']);before=self.files()
        with self.assertRaises(rules.ReconnectError):self.store.change(state['revision'],action='undo')
        self.assertEqual(before,self.files())

    def test_corrupt_journal_blocks_all_writes_and_is_never_cleared(self):
        (self.base/rules.FILENAME).write_bytes(b'{broken');before=self.files()
        for action in [lambda:self.work.mutate('rename',identity=self.item,title='changed'),lambda:self.verdicts.save(OTHER,'useful'),lambda:self.budgets.change(lambda entries:entries.clear()),lambda:self.store.change('0'*64,action='clear')]:
            with self.assertRaises(ValueError):action()
            self.assertEqual(before,self.files())

    def test_clear_removes_only_the_private_undo_copy(self):
        self.transfer();before=self.files()
        self.store.change(self.store.state()['revision'],action='clear')
        self.assertFalse((self.base/rules.FILENAME).exists())
        self.assertEqual({k:v for k,v in before.items() if k in rules.NAMES},{k:v for k,v in self.files().items() if k in rules.NAMES})

    def test_journal_rejects_unknown_files_and_duplicate_keys(self):
        self.transfer();record=json.loads((self.base/rules.FILENAME).read_text())
        record['files']['../outside.json']=record['files'][work_items.FILENAME]
        with self.assertRaises(rules.ReconnectError):rules.validate(json.dumps(record).encode())
        with self.assertRaises(rules.ReconnectError):rules.validate(b'{"format":1,"format":1}')

    def test_backup_finishes_a_pending_transfer_and_omits_the_undo_copy(self):
        from pler.usage import backup
        import io,zipfile
        install=rules._install
        def failing(base,name,data):
            if name==verdicts.FILENAME:raise OSError('invented interruption')
            return install(base,name,data)
        with patch.object(rules,'_install',side_effect=failing):
            with self.assertRaises(OSError):self.transfer()
        with zipfile.ZipFile(io.BytesIO(backup.create(self.base))) as bundle:
            self.assertFalse(any(name.endswith(rules.FILENAME) for name in bundle.namelist()))
        self.assertEqual(self.verdicts.read(),{NEW:'useful'})
        self.assertEqual(self.store.state()['record']['phase'],'complete')

    def test_authenticated_http_preview_and_strict_write_admission(self):
        from pler.server import Server
        from http.client import HTTPConnection
        import threading
        dashboard=self.dashboard();server=Server(dashboard=dashboard)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def close():server.shutdown();server.server_close();thread.join(3)
        self.addCleanup(close)
        def request(method,route,body=None,auth=True,origin=True):
            connection=HTTPConnection(*server.server_address,timeout=3)
            headers={'Content-Type':'application/json'}
            if auth:headers['X-PLER-Token']=server.token
            if origin:headers['Origin']=server.origin
            connection.request(method,route,None if body is None else json.dumps(body),headers)
            response=connection.getresponse();result=json.loads(response.read());status=response.status;connection.close();return status,result
        route='/api/usage/reconnections'
        self.assertEqual(request('GET',route,auth=False)[0],401)
        self.assertEqual(request('GET',route+'?offset=-1')[0],400)
        self.assertEqual(request('GET',route+'?q=a&q=b')[0],400)
        payload=dict(action='preview',source=OLD,target=NEW)
        self.assertEqual(request('POST',route,payload,origin=False)[0],403)
        before=self.files();status,preview=request('POST',route,payload)
        self.assertEqual(status,200);self.assertEqual(before,self.files())
        transfer=dict(action='transfer',source=OLD,target=NEW,expected=preview['expected'],confirmed=True,verdict_choice='target',budget_choice='target')
        self.assertEqual(request('POST',route,dict(transfer,extra='rejected'))[0],400)
        self.assertEqual(request('POST',route,dict(transfer,confirmed=1))[0],400)
        status,result=request('POST',route,transfer)
        self.assertEqual(status,200,result);self.assertTrue(result['can_undo'])
        self.assertEqual(self.work.read()[self.item]['sessions'],[NEW])

    def dashboard(self):
        dashboard=UsageDashboard(reader=lambda:([],{}),verdicts=self.verdicts,work_items=self.work,budgets=self.budgets,manage_sources=False)
        self.addCleanup(dashboard.close)
        dashboard.budgets.autostart=False
        rows=[]
        for code,state,amount in [(OLD,'archive',11),(NEW,'live',22)]:
            row=Session('codex',code,'/invented/'+code,started=datetime(2026,1,1,tzinfo=timezone.utc),ended=datetime(2026,1,1,tzinfo=timezone.utc),tokens=dict(input=amount,cache_read=0,cache_write=0,output=0,reasoning=0))
            row._pler_identity=code;row.source_state=state;rows.append(row)
        dashboard.sessions=rows;dashboard.sources={};dashboard.state='ready';dashboard.scanned_at=datetime.now(timezone.utc).isoformat()
        dashboard.budgets.bind(rows)
        return dashboard

    def test_preview_is_read_only_and_transfer_keeps_session_usage_and_ids(self):
        dashboard=self.dashboard();before=self.files()
        preview=dashboard.reconnect_action(dict(action='preview',source=OLD,target=NEW))
        self.assertTrue(preview['ok']);self.assertTrue(preview['budget_conflict']);self.assertTrue(preview['verdict_conflict'])
        self.assertEqual(before,self.files())
        totals=[(verdicts.session_code(row),dict(row.tokens)) for row in dashboard.sessions]
        result=dashboard.reconnect_action(dict(action='transfer',source=OLD,target=NEW,expected=preview['expected'],confirmed=True,verdict_choice='source',budget_choice='source'))
        self.assertTrue(result['ok'],result)
        self.assertEqual(totals,[(verdicts.session_code(row),dict(row.tokens)) for row in dashboard.sessions])
        self.assertEqual(dashboard.session(NEW)['verdict'],'useful')
        self.assertEqual(dashboard.session(OLD)['verdict'],None)

    def test_active_source_and_changed_scan_refuse_transfer(self):
        dashboard=self.dashboard();dashboard.sessions[0].source_state='live'
        self.assertEqual(dashboard.reconnect_action(dict(action='preview',source=OLD,target=NEW))['reason'],'source_live')
        dashboard.sessions[0].source_state='archive'
        preview=dashboard.reconnect_action(dict(action='preview',source=OLD,target=NEW))
        dashboard.generation+=1
        result=dashboard.reconnect_action(dict(action='transfer',source=OLD,target=NEW,expected=preview['expected'],confirmed=True,verdict_choice='source',budget_choice='source'))
        self.assertEqual(result['reason'],'conflict')

    def test_search_paginates_targets_beyond_the_frozen_400_picker(self):
        dashboard=self.dashboard()
        for index in range(450):
            row=Session('codex',str(index),'/invented/'+str(index),tokens=dict(input=0,cache_read=0,cache_write=0,output=0,reasoning=0))
            row._pler_identity=('%024x'%(index+100));dashboard.sessions.append(row)
        value=dashboard.reconnect_view('targets',query='%024x'%549)
        self.assertEqual(value['total'],1);self.assertEqual(value['items'][0]['id'],'%024x'%549)
        self.assertEqual(len(dashboard.reconnect_view('targets')['items']),20)
