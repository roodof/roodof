"""User goals/outcomes stay private, survive recovery and never follow test/Git scores."""
import json
import threading
from unittest.mock import patch

from pler.dashboard import UsageDashboard
from pler.server import Server
from pler.usage import backup,work_items as work
from test_adoption_api import IsolatedMetadata,invented_sessions,join_scan
from test_work_items import A,B,row
import test_work_items_api as old_http

GOAL='PRIVATE-GOAL-CANARY'
NOTE='PRIVATE-RESULT-CANARY'


class WorkOutcomeTests(IsolatedMetadata):
    def setUp(self):
        super().setUp();self.store=work.Folder(self.cache)
        self.identity=self.store.mutate('create',title='Invented job',session=A)['id']

    def describe(self,goal=GOAL,outcome='partial',note=NOTE,revision=None):
        return self.store.mutate('describe',identity=self.identity,
            details=dict(goal=goal,outcome=outcome,result_note=note),
            expected_revision=revision or work.details_revision(self.store.read()[self.identity]))

    def test_legacy_read_and_noop_preserve_bytes_until_explicit_edit(self):
        path=self.cache/work.FILENAME
        legacy=dict(format=1,items={self.identity:dict(title='Old job',created_at=10,updated_at=10,sessions=[A])})
        raw=json.dumps(legacy).encode();path.write_bytes(raw)
        with patch.object(work.archive,'_write',side_effect=AssertionError('read migrated the file')):
            item=self.store.read()[self.identity]
            self.assertEqual((item['goal'],item['outcome'],item['result_note'],item['outcome_at']),('','not_recorded','',None))
            self.store.mutate('rename',identity=self.identity,title='Old job')
            self.describe(goal='',outcome='not_recorded',note='')
        self.assertEqual(path.read_bytes(),raw)
        self.describe()
        saved=json.loads(path.read_bytes())
        self.assertEqual(saved['format'],work.FORMAT)
        item=saved['items'][self.identity]
        self.assertEqual((item['title'],item['created_at'],item['sessions']),('Old job',10,[A]))

    def test_goals_results_and_user_status_persist_and_can_be_cleared(self):
        self.describe(goal='  İlk hedef\r\nİkinci satır 🛠  ',outcome='completed')
        item=work.Folder(self.cache).read()[self.identity]
        self.assertEqual(item['goal'],'İlk hedef\nİkinci satır 🛠')
        self.assertEqual((item['outcome'],item['result_note']),('completed',NOTE))
        self.assertIsInstance(item['outcome_at'],int)
        self.describe(goal='',outcome='not_recorded',note='')
        item=self.store.read()[self.identity]
        self.assertEqual((item['goal'],item['outcome_at'],item['result_note']),('',None,''))

    def test_same_second_stale_form_cannot_overwrite_another_window(self):
        before=self.store.read()[self.identity];revision=work.details_revision(before)
        with patch.object(work.time,'time',return_value=before['updated_at']):
            self.describe(goal='Other window',revision=revision)
            raw=(self.cache/work.FILENAME).read_bytes()
            with self.assertRaises(work.WorkError) as error: self.describe(revision=revision)
        self.assertEqual(error.exception.code,'conflict')
        self.assertEqual((self.cache/work.FILENAME).read_bytes(),raw)
        self.assertEqual(self.store.read()[self.identity]['goal'],'Other window')

    def test_title_and_links_do_not_invalidate_details_or_get_lost(self):
        revision=work.details_revision(self.store.read()[self.identity])
        self.store.mutate('rename',identity=self.identity,title='Renamed')
        self.store.mutate('link',identity=self.identity,session=B)
        self.describe(revision=revision)
        item=self.store.read()[self.identity]
        self.assertEqual((item['title'],item['sessions'],item['goal']),('Renamed',[A,B],GOAL))

    def test_goal_changes_do_not_retimestamp_the_users_outcome(self):
        self.describe(outcome='completed')
        first=self.store.read()[self.identity]['outcome_at']
        with patch.object(work.time,'time',return_value=first+100): self.describe(goal='Reworded',outcome='completed')
        self.assertEqual(self.store.read()[self.identity]['outcome_at'],first)
        with patch.object(work.time,'time',return_value=first-100): self.describe(outcome='not_completed')
        self.assertGreaterEqual(self.store.read()[self.identity]['outcome_at'],first)

    def test_invalid_fields_controls_sizes_and_future_formats_preserve_previous_data(self):
        before=(self.cache/work.FILENAME).read_bytes()
        for values in (dict(goal='x'*1001),dict(note='x\tinside'),dict(goal='a\x00b'),dict(goal='a\u2028b'),
                       dict(goal='\ud800'),dict(outcome='automatic-success'),dict(outcome=True)):
            with self.subTest(values=values),self.assertRaises(work.WorkError): self.describe(**values)
            self.assertEqual((self.cache/work.FILENAME).read_bytes(),before)
        future=json.loads(before);future['format']=work.FORMAT+1
        raw=json.dumps(future).encode();(self.cache/work.FILENAME).write_bytes(raw)
        with self.assertRaises(work.WorkError): self.describe()
        self.assertEqual((self.cache/work.FILENAME).read_bytes(),raw)

    def test_unicode_limit_html_literal_and_duplicate_save_are_safe(self):
        self.describe(goal='🛠'*1000,note='<img onerror="not executed">')
        item=self.store.read()[self.identity]
        self.assertEqual(item['goal'],'🛠'*1000)
        with patch.object(work.archive,'_write',side_effect=AssertionError('unchanged description wrote')):
            self.describe(goal=item['goal'],note=item['result_note'])

    def test_failed_atomic_save_keeps_previous_details_and_other_files(self):
        before=(self.cache/work.FILENAME).read_bytes()
        with patch.object(work.archive,'_write',side_effect=OSError('invented disk failure')):
            with self.assertRaises(OSError): self.describe()
        self.assertEqual((self.cache/work.FILENAME).read_bytes(),before)

    def test_two_concurrent_reviewers_do_not_lose_an_update(self):
        revision=work.details_revision(self.store.read()[self.identity]);results=[]
        def save(goal):
            try: self.describe(goal=goal,revision=revision);results.append('saved')
            except work.WorkError as error: results.append(error.code)
        threads=[threading.Thread(target=save,args=(text,)) for text in ('First','Second')]
        for thread in threads: thread.start()
        for thread in threads: thread.join(5)
        self.assertCountEqual(results,['saved','conflict'])

    def test_user_outcome_and_evidence_are_independent_across_filters(self):
        self.describe(outcome='partial')
        recorded=dict(row(A),checks={'test':dict(runs=3,last='passed')},
                      git_activity=dict(state='ready',matched_events=2,coverage_limited=True))
        original=self.store.read()
        for result in (work.project(original,[recorded]),work.project(original,[],{A})):
            item=result['items'][0]
            self.assertEqual((item['goal'],item['outcome'],item['result_note']),(GOAL,'partial',NOTE))
        obs=work.project(original,[recorded])['items'][0]['observations']
        self.assertEqual(obs['test'],dict(sessions=1,passed=1,failed=0,unknown=0))
        self.assertEqual(obs['git'],dict(available_sessions=1,activity_sessions=1,limited_sessions=1))
        self.describe(outcome='completed')
        recorded['checks']['test']['last']='failed'
        item=work.project(self.store.read(),[recorded])['items'][0]
        self.assertEqual(item['outcome'],'completed')
        self.assertEqual(item['observations']['test']['failed'],1)
        self.assertNotIn('quality_score',item)

    def test_private_backup_roundtrip_and_legacy_backup_remain_usable(self):
        self.describe()
        data=backup.create();info=backup.inspect(data)
        self.assertIn(GOAL.encode(),data);self.assertIn(NOTE.encode(),data)
        self.assertNotIn(GOAL,json.dumps(info));self.assertNotIn(NOTE,json.dumps(info))
        restored=self.root/'recovered';backup.restore(data,restored)
        self.assertEqual(work.Folder(restored).read(),self.store.read())
        current=json.loads((self.cache/work.FILENAME).read_bytes())
        current['format']=1
        for item in current['items'].values():
            for key in work.DETAIL_FIELDS|{'followups'}:item.pop(key,None)
        raw=json.dumps(current).encode();(self.cache/work.FILENAME).write_bytes(raw)
        old_data=backup.create();old_target=self.root/'old-recovered';backup.restore(old_data,old_target)
        self.assertEqual((old_target/work.FILENAME).read_bytes(),raw)
        self.assertEqual(work.Folder(old_target).read()[self.identity]['outcome'],'not_recorded')


class WorkOutcomeHttpTests(IsolatedMetadata):
    request=old_http.WorkHttpTests.request

    def setUp(self):
        super().setUp()
        self.board=UsageDashboard(lambda:(invented_sessions(),dict(claude_files=1,codex_files=1,skipped=[])),
                                  git_reader=lambda _:dict(state='not_repository'))
        self.board.refresh();join_scan(self.board)
        self.server=Server(0,self.board)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)
        self.identity=self.board.mutate_work_item('create',title='HTTP invented')['id']

    def body(self):
        item=self.board.view(days=0)['work_items']['items'][0]
        return dict(action='describe',id=self.identity,goal=GOAL,outcome='partial',result_note=NOTE,
                    expected_revision=item['details_revision'])

    def test_large_unicode_details_roundtrip_and_ordinary_exports_omit_every_private_field(self):
        body=self.body();body.update(goal='🛠'*1000,result_note='🛠'*1000)
        before=self.board.view(days=0)['totals']
        status,raw=self.request('/api/usage/work/details',body=body)
        self.assertEqual(status,200)
        self.assertEqual(set(json.loads(raw)),{'ok','id'})
        self.assertEqual(self.board.view(days=0)['work_items']['items'][0]['goal'],body['goal'])
        for mask in (0,1):
            code,raw=self.request('/api/usage/export?days=0&mask_projects='+str(mask),method='GET')
            self.assertEqual(code,200)
            self.assertNotIn('work_items',json.loads(raw))
            self.assertNotIn('🛠'.encode(),raw)
        self.assertEqual(self.board.view(days=0)['totals'],before)

    def test_conflict_is_a_safe_409_and_keeps_the_latest_entry(self):
        body=self.body();self.assertEqual(self.request('/api/usage/work/details',body=body)[0],200)
        body['goal']='Stale overwriter'
        status,raw=self.request('/api/usage/work/details',body=body)
        self.assertEqual((status,json.loads(raw)['code']),(409,'conflict'))
        self.assertNotIn(GOAL.encode(),raw)
        self.assertEqual(self.board.view(days=0)['work_items']['items'][0]['goal'],GOAL)

    def test_new_route_keeps_auth_framing_and_field_admission(self):
        valid=self.body()
        with patch.object(self.board,'mutate_work_item',side_effect=AssertionError('invalid request reached work store')):
            for options in (dict(auth=False),dict(headers={'Origin':'https://outside.invalid'})):
                self.assertEqual(self.request('/api/usage/work/details',body=valid,**options)[0],403)
            for altered in (dict(valid,goal=True),dict(valid,goal='x'*1001),dict(valid,outcome='auto'),
                            dict(valid,expected_revision='private-path'),dict(valid,prompt='PRIVATE'),dict(valid,action='delete')):
                self.assertEqual(self.request('/api/usage/work/details',body=altered)[0],400)
            self.assertEqual(self.request('/api/usage/work',body=valid)[0],400)
            self.assertEqual(self.request('/api/usage/work/details',raw=b'{}',
                headers={'Content-Length':str(work.MAX_DETAILS_REQUEST+1)})[0],400)
            self.assertEqual(self.request('/api/usage/work/details',raw=b'{"action":"describe","action":"describe"}')[0],400)
