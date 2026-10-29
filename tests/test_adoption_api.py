"""Adoption controls keep retained history and the report access boundary intact.

Every source, setting and cache belongs to an isolated invented fixture. HTTP
uses the actual loopback server; no provider, model or external address is used.
"""
from datetime import datetime,timedelta,timezone
import http.client
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from pler.dashboard import UsageDashboard,project_view
from pler.reporting import mask_projects
from pler.server import Server
from pler.usage import archive,scan
from pler.usage.records import Session,total
from test_archive import codex_rows
from test_logs import write_jsonl

PRIVATE='PRIVATE-SOURCE-NATIVE-ID-CANARY'
NOW=datetime(2026,10,29,8,tzinfo=timezone.utc)


def invented_sessions():
    first=Session('codex',PRIVATE+'-origin','C:/'+PRIVATE+'/origin.jsonl',project='/invented/client-a/app',
        started=NOW-timedelta(days=5),ended=NOW-timedelta(days=4),calls=2,
        tokens=dict(input=100,cache_read=0,cache_write=0,output=0,reasoning=0),
        models={'invented-model-a':2},model_tokens={'invented-model-a':100})
    later=Session('claude-code',PRIVATE+'-later','C:/'+PRIVATE+'/later.jsonl',project='/invented/client-b/app',
        started=NOW-timedelta(days=2),ended=NOW-timedelta(days=1),calls=1,
        tokens=dict(input=20,cache_read=0,cache_write=0,output=0,reasoning=0),
        models={'invented-model-b':1},model_tokens={'invented-model-b':20})
    return [first,later]


def join_scan(board):
    # A stale archive result intentionally starts a replacement thread.
    for _ in range(8):
        thread=board.thread
        if thread is None:return
        thread.join(5)
        if thread.is_alive():raise AssertionError('synthetic scan did not finish')
        if board.thread is thread:return
    raise AssertionError('synthetic scan kept replacing itself')


class IsolatedMetadata(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.cache=self.root/'cache'
        self.codex=self.root/'codex/sessions'
        self.claude=self.root/'claude/projects'
        self.codex.mkdir(parents=True)
        self.claude.mkdir(parents=True)
        (self.codex.parent/'archived_sessions').mkdir()
        env=patch.dict(os.environ,PLER_CACHE_DIR=str(self.cache),CODEX_HOME=str(self.codex.parent),
                       CLAUDE_CONFIG_DIR=str(self.claude.parent))
        env.start();self.addCleanup(env.stop)

    def seed_retained(self):
        source=self.codex/'rollout-invented.jsonl'
        write_jsonl(source,codex_rows())
        rows,_=scan()
        self.assertEqual(sum(total(row.tokens) for row in rows),230)
        source.unlink()


class AdoptionServiceTests(IsolatedMetadata):
    def test_masking_is_consistent_and_pure_and_does_not_claim_anonymity(self):
        value=project_view(invented_sessions(),{},days=0,now=NOW)
        original=json.dumps(value,sort_keys=True)
        hidden=mask_projects(value,'en')
        self.assertEqual(json.dumps(value,sort_keys=True),original)
        self.assertTrue(hidden['project_names_masked'])
        self.assertNotIn('project_options',hidden)
        names={row['id']:row['name'] for row in hidden['projects']}
        self.assertEqual(set(names.values()),{'Project 1','Project 2'})
        for row in hidden['sessions']:
            self.assertEqual(row['project'],names[row['project_id']])
            self.assertIsNotNone(row['started'])
            self.assertTrue(row['models'])
            self.assertEqual(len(row['id']),24)
        for name in ('client-a/app','client-b/app',PRIVATE):
            self.assertNotIn(name,json.dumps(hidden))

    def test_retention_off_removes_archived_rows_from_snapshot_but_preserves_disk_copy(self):
        self.seed_retained()
        board=UsageDashboard()
        board.refresh();join_scan(board)
        previous=board.view(days=0)
        self.assertEqual(previous['totals']['total_tokens'],230)
        identity=previous['sessions'][0]['id']
        prior=(self.cache/archive.FILENAME).read_bytes()
        self.assertTrue(board.set_retention(False)['ok'])
        self.assertIsNone(board.session(identity))
        join_scan(board)
        self.assertEqual(board.view(days=0)['totals']['total_tokens'],0)
        self.assertEqual((self.cache/archive.FILENAME).read_bytes(),prior)
        self.assertTrue(board.set_retention(True)['ok'])
        join_scan(board)
        self.assertEqual(board.view(days=0)['totals']['total_tokens'],230)

    def test_external_reenable_invalidates_a_snapshot_which_had_retention_disabled(self):
        self.seed_retained()
        archive.set_retention(False)
        board=UsageDashboard()
        board.refresh();join_scan(board)
        self.assertFalse(board.sources['archive']['enabled'])
        self.assertTrue(board.sources['archive']['available'])
        self.assertEqual(board.view(days=0)['totals']['sessions'],0)
        archive.set_retention(True)
        board.view(days=0)
        join_scan(board)
        self.assertEqual(board.view(days=0)['totals']['total_tokens'],230)

    def test_scan_loaded_before_external_off_and_on_never_publishes_its_stale_archived_rows(self):
        self.seed_retained()
        entered,released=threading.Event(),threading.Event()
        calls=[]
        def reader():
            calls.append(True)
            if len(calls)>1:return scan()
            old=archive.Archive()
            entered.set()
            if not released.wait(5):raise AssertionError('fixture was not released')
            old_row=invented_sessions()[0]
            old_row.tokens['input']=999
            old_row.source_state='archive';old_row.source_deleted=True
            return [old_row],dict(archive=old.finish(),claude_files=0,codex_files=0,skipped=[])
        board=UsageDashboard(reader)
        board.refresh()
        self.assertTrue(entered.wait(3))
        archive.set_retention(False)
        archive.set_retention(True)
        released.set();join_scan(board)
        self.assertGreaterEqual(len(calls),2)
        self.assertEqual(board.view(days=0)['totals']['total_tokens'],230)

    def test_service_cache_reset_preserves_deleted_source_metadata(self):
        self.seed_retained()
        before=(self.cache/archive.FILENAME).read_bytes()
        board=UsageDashboard()
        result=board.reset_cache()
        self.assertTrue(result['ok'])
        join_scan(board)
        self.assertEqual(board.view(days=0)['totals']['total_tokens'],230)
        self.assertEqual((self.cache/archive.FILENAME).read_bytes(),before)


class AdoptionHttpTests(IsolatedMetadata):
    def setUp(self):
        super().setUp()
        self.rows=invented_sessions()
        self.board=UsageDashboard(lambda:(self.rows,dict(claude_files=1,codex_files=1,skipped=[])),
                                  git_reader=lambda path:dict(state='not_repository'))
        self.board.refresh();join_scan(self.board)
        self.server=Server(0,self.board)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self,path,method='GET',body=None,auth=True,headers=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=10)
        sent={'Host':self.server.origin.split('//')[1]}
        if auth:sent.update(Origin=self.server.origin,**{'X-PLER-Token':self.server.token})
        raw=None if body is None else json.dumps(body).encode('utf-8')
        if raw is not None:sent['Content-Type']='application/json'
        sent.update(headers or {})
        connection.request(method,path,body=raw,headers=sent)
        response=connection.getresponse()
        result=response.status,dict(response.getheaders()),response.read()
        connection.close()
        return result

    def test_session_read_requires_authentication_and_cannot_choose_a_file_or_source(self):
        identity=self.board.view(days=0)['sessions'][0]['id']
        path='/api/usage/session?id='+identity
        self.assertEqual(self.request(path,auth=False)[0],401)
        self.assertEqual(self.request(path,headers={'X-PLER-Token':'wrong'})[0],401)
        for query in ('id=C:/private/log.jsonl','id='+identity+'&path=C:/private',
                      'id='+identity+'&id='+identity,'id='+identity+'&root=/private','id='):
            with self.subTest(query=query):
                self.assertEqual(self.request('/api/usage/session?'+query)[0],400)

    def test_session_outside_selection_uses_only_current_snapshot_and_preserves_selection(self):
        all_rows=self.board.view(days=0)
        later=next(row for row in all_rows['sessions'] if row['agent']=='claude-code')
        first=self.board.view(days=0,agent='codex')
        query='/api/usage?days=0&agent=codex'
        self.assertEqual(json.loads(self.request(query)[2])['totals']['sessions'],1)
        with patch.object(self.board,'reader',side_effect=AssertionError('new source read')):
            code,_,raw=self.request('/api/usage/session?id='+later['id']+'&lang=tr')
        self.assertEqual(code,200)
        row=json.loads(raw)['session']
        self.assertEqual((row['id'],row['agent']),(later['id'],'claude-code'))
        self.assertNotIn(PRIVATE,raw.decode())
        after=self.board.view(days=0,agent='codex')
        self.assertEqual(first['filters'],after['filters'])
        self.assertEqual(first['totals'],after['totals'])

    def test_missing_snapshot_session_returns_404_without_private_source_details(self):
        code,_,raw=self.request('/api/usage/session?id='+'f'*24)
        self.assertEqual(code,404)
        self.assertIn('error',json.loads(raw))
        self.assertNotIn(PRIVATE,raw.decode())

    def test_new_actions_require_origin_and_token_before_any_setting_change(self):
        for route,body in (('/api/usage/retention',{'enabled':False}),('/api/usage/cache/reset',{})):
            with self.subTest(route=route):
                self.assertEqual(self.request(route,'POST',body,auth=False)[0],403)
                self.assertEqual(self.request(route,'POST',body,headers={'Origin':'http://outside.invalid'})[0],403)
                self.assertEqual(self.request(route,'POST',body,headers={'X-PLER-Token':'wrong'})[0],403)
        self.assertFalse((self.cache/archive.preferences.FILENAME).exists())

    def test_retention_accepts_only_a_boolean_and_no_extra_control_fields(self):
        for body in ({},{'enabled':0},{'enabled':'false'},{'enabled':None},
                     {'enabled':False,'path':'/invented'},[],False):
            with self.subTest(body=body):
                self.assertEqual(self.request('/api/usage/retention','POST',body)[0],400)
        self.assertEqual(self.request('/api/usage/retention','POST',{'enabled':False})[0],200)
        join_scan(self.board)
        self.assertFalse(archive.Archive().retention_enabled)
        self.assertEqual(self.request('/api/usage/retention','POST',{'enabled':True})[0],200)
        join_scan(self.board)
        self.assertTrue(archive.Archive().retention_enabled)

    def test_cache_reset_action_keeps_archive_quota_and_preferences(self):
        self.cache.mkdir(exist_ok=True)
        (self.cache/'claude.json').write_bytes(b'invented cache')
        (self.cache/'codex.json').write_bytes(b'invented damaged cache')
        for name in (archive.FILENAME,'claude-quota.jsonl',archive.preferences.FILENAME):
            (self.cache/name).write_bytes(b'invented retained bytes')
        preserved={name:(self.cache/name).read_bytes() for name in
                   (archive.FILENAME,'claude-quota.jsonl',archive.preferences.FILENAME)}
        self.assertEqual(self.request('/api/usage/cache/reset','POST',{'archive':True})[0],400)
        code,_,raw=self.request('/api/usage/cache/reset','POST',{})
        self.assertEqual(code,200)
        self.assertEqual(json.loads(raw)['cleared_files'],2)
        join_scan(self.board)
        self.assertEqual(preserved,{name:(self.cache/name).read_bytes() for name in preserved})

    def test_masked_export_uses_consistent_aliases_and_does_not_mutate_the_live_view(self):
        ordinary=json.loads(self.request('/api/usage/export?days=0')[2])
        code,headers,raw=self.request('/api/usage/export?days=0&mask_projects=1&lang=tr')
        self.assertEqual(code,200)
        self.assertIn('application/json',headers['Content-Type'])
        hidden=json.loads(raw)
        self.assertTrue(hidden['project_names_masked'])
        self.assertEqual({row['name'] for row in hidden['projects']},{'Proje 1','Proje 2'})
        names={row['id']:row['name'] for row in hidden['projects']}
        for row in hidden['sessions']:self.assertEqual(row['project'],names[row['project_id']])
        self.assertEqual(hidden['totals'],ordinary['totals'])
        self.assertNotIn('client-a/app',raw.decode());self.assertNotIn('client-b/app',raw.decode())
        again=json.loads(self.request('/api/usage/export?days=0')[2])
        self.assertFalse(again['project_names_masked'])
        self.assertEqual(again['projects'],ordinary['projects'])
        self.assertEqual(again['sessions'],ordinary['sessions'])

    def test_masking_is_an_explicit_export_only_choice_with_no_arbitrary_mode(self):
        for query in ('mask_projects=yes','mask_projects=1&mask_projects=0','mask_projects=1&path=/private'):
            self.assertEqual(self.request('/api/usage/export?days=0&'+query)[0],400)
        self.assertEqual(self.request('/api/usage?mask_projects=1')[0],400)

    def test_bundled_help_needs_no_private_report_access_and_cannot_open_an_arbitrary_path(self):
        with patch.object(self.board,'reader',side_effect=AssertionError('help scanned sources')):
            for chapter in ('guide','accounting'):
                for lang in ('en','tr'):
                    code,headers,raw=self.request('/help?lang='+lang+'&chapter='+chapter,auth=False)
                    self.assertEqual(code,200)
                    self.assertIn('text/html',headers['Content-Type'])
                    self.assertNotIn(self.server.token,raw.decode())
                    self.assertNotIn(PRIVATE,raw.decode())
        for query in ('chapter=../server.py','chapter=/private','path=/private','chapter=guide&chapter=accounting'):
            with self.subTest(query=query):
                self.assertEqual(self.request('/help?'+query,auth=False)[0],400)


if __name__=='__main__':unittest.main()
