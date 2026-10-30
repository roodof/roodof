"""Manual work annotations: invented sessions, isolated local state and real loopback admission."""
from contextlib import redirect_stdout
from dataclasses import replace
import http.client
import io
import json
import threading
from unittest.mock import patch

from pler.dashboard import UsageDashboard,project_view
from pler.reporting import mask_projects
from pler.server import Server
from pler.usage import main as report_main,work_items
from pler.usage.verdicts import session_code
from test_adoption_api import IsolatedMetadata,invented_sessions,join_scan

TITLE='PRIVATE-MANUAL-WORK-CANARY'


class WorkDashboardTests(IsolatedMetadata):
    def board(self,rows=None,store=None,demo=False):
        rows=invented_sessions() if rows is None else rows
        self.reads=0
        def reader():
            self.reads+=1
            return rows,dict(claude_files=1,codex_files=1,skipped=[],demo=demo)
        board=UsageDashboard(reader,git_reader=lambda path:dict(state='not_repository'),work_items=store)
        board.refresh();join_scan(board);self.addCleanup(board.close)
        return board

    def test_two_agents_and_overlapping_work_leave_original_totals_unchanged(self):
        board=self.board();before=board.view(days=0)
        first,second=[row['id'] for row in before['sessions']]
        one=board.mutate_work_item('create',title=TITLE,session=first)['id']
        two=board.mutate_work_item('create',title='Another work',session=first)['id']
        self.assertTrue(board.mutate_work_item('link',identity=one,session=second)['ok'])
        self.assertTrue(board.mutate_work_item('link',identity=one,session=second)['ok'])
        after=board.view(days=0);work=after['work_items'];by_id={row['id']:row for row in work['items']}
        self.assertEqual(after['totals'],before['totals'])
        self.assertEqual(work['summary']['total_tokens'],120)
        self.assertEqual(work['summary']['selected_sessions'],2)
        self.assertEqual(work['summary']['overlapping_sessions'],1)
        self.assertEqual((by_id[one]['total_tokens'],by_id[two]['total_tokens']),(120,100))
        self.assertEqual(self.reads,1,'annotations must never force another source read')

    def test_filtered_view_distinguishes_outside_selection_from_missing(self):
        board=self.board();all_rows=board.view(days=0)['sessions']
        made=board.mutate_work_item('create',title=TITLE)['id']
        for row in all_rows:board.mutate_work_item('link',identity=made,session=row['id'])
        selected=board.view(days=0,agent='codex')
        work=selected['work_items']['items'][0]
        self.assertEqual((work['selected_sessions'],work['outside_selection'],work['missing_sessions']),(1,1,0))
        self.assertEqual(work['total_tokens'],100)
        self.assertEqual(selected['totals']['sessions'],1)

    def test_prices_sum_unrounded_session_values_before_final_rounding(self):
        rows=invented_sessions()
        rows.append(replace(rows[0],session_id='third-invented',source='C:/invented/third.jsonl'))
        for row in rows:row.api_usd=.004
        board=self.board(rows);made=board.mutate_work_item('create',title=TITLE)['id']
        for row in rows:board.mutate_work_item('link',identity=made,session=session_code(row))
        work=board.view(days=0)['work_items']
        self.assertEqual(work['summary']['api_usd'],.01)
        self.assertEqual(work['items'][0]['api_usd'],.01)

    def test_external_window_updates_are_visible_without_rescanning_sources(self):
        board=self.board();made=board.mutate_work_item('create',title='First')['id']
        second=self.board();self.assertEqual(second.view(days=0)['work_items']['items'][0]['title'],'First')
        self.assertTrue(second.mutate_work_item('rename',identity=made,title=TITLE)['ok'])
        self.assertEqual(board.view(days=0)['work_items']['items'][0]['title'],TITLE)

    def test_moved_source_keeps_an_orphan_instead_of_rebinding_the_same_provider_id(self):
        rows=invented_sessions();board=self.board(rows)
        original=board.view(days=0)['sessions'][0]['id']
        made=board.mutate_work_item('create',title=TITLE,session=original)['id']
        moved=[replace(row,source=row.source+'.moved') for row in rows]
        board.reader=lambda:(moved,dict(claude_files=1,codex_files=1,skipped=[]))
        board.refresh();join_scan(board)
        work=board.view(days=0)['work_items']['items'][0]
        self.assertEqual((work['missing_sessions'],work['selected_sessions']),(1,0))
        self.assertEqual(work['session_ids'],[original])
        self.assertFalse(work['tokens_complete'])
        self.assertTrue(board.mutate_work_item('unlink',identity=made,session=original)['ok'])
        self.assertEqual(board.view(days=0)['work_items']['items'][0]['missing_sessions'],0)

    def test_create_and_link_accept_only_known_sessions_but_empty_work_is_allowed(self):
        board=self.board()
        self.assertEqual(board.mutate_work_item('create',title=TITLE,session='f'*24),dict(ok=False,reason='missing_session'))
        made=board.mutate_work_item('create',title=TITLE)['id']
        self.assertEqual(board.mutate_work_item('link',identity=made,session='f'*24),dict(ok=False,reason='missing_session'))
        self.assertEqual(board.view(days=0)['work_items']['items'][0]['linked_sessions'],0)

    def test_corrupt_or_newer_work_file_is_reported_and_never_overwritten(self):
        board=self.board();self.cache.mkdir(exist_ok=True)
        path=self.cache/work_items.FILENAME
        for raw in (b'{damaged',b'{"format":99,"items":{}}'):
            path.write_bytes(raw)
            self.assertFalse(board.view(days=0)['work_items']['readable'])
            self.assertEqual(board.mutate_work_item('create',title=TITLE),dict(ok=False,reason='unreadable'))
            self.assertEqual(path.read_bytes(),raw)

    def test_demo_never_uses_the_supplied_disk_store(self):
        store=work_items.Folder(self.cache)
        with patch.object(store,'read',side_effect=AssertionError('demo read disk work')), \
             patch.object(store,'mutate',side_effect=AssertionError('demo wrote disk work')):
            board=self.board(store=store,demo=True)
            made=board.mutate_work_item('create',title=TITLE)
            self.assertTrue(made['ok'])
            self.assertEqual(board.view(days=0)['work_items']['items'][0]['title'],TITLE)
        self.assertFalse((self.cache/work_items.FILENAME).exists())

    def test_unread_and_closed_boards_reject_mutations(self):
        board=UsageDashboard(work_items=work_items.Memory())
        self.assertEqual(board.mutate_work_item('create',title=TITLE),dict(ok=False,reason='unavailable'))
        board=self.board();board.close()
        self.assertEqual(board.mutate_work_item('create',title=TITLE),dict(ok=False,reason='unavailable'))

    def test_masked_export_helper_omits_private_titles_without_mutating_view(self):
        board=self.board();made=board.mutate_work_item('create',title=TITLE)['id']
        value=board.view(days=0);exported=mask_projects(value)
        self.assertIn(TITLE,json.dumps(value))
        self.assertNotIn('work_items',exported)
        self.assertNotIn(TITLE,json.dumps(exported));self.assertNotIn(made,json.dumps(exported))

    def test_terminal_json_does_not_read_or_export_work_store(self):
        work_items.Folder(self.cache).mutate('create',title=TITLE)
        output=io.StringIO()
        with patch.object(work_items.Folder,'read',side_effect=AssertionError('ordinary terminal report read work labels')), \
             redirect_stdout(output):report_main(['--days','0','--json'])
        self.assertNotIn(TITLE,output.getvalue())
        self.assertNotIn('work_items',json.loads(output.getvalue()))


class WorkHttpTests(IsolatedMetadata):
    def setUp(self):
        super().setUp();rows=invented_sessions()
        self.board=UsageDashboard(lambda:(rows,dict(claude_files=1,codex_files=1,skipped=[])),
                                  git_reader=lambda path:dict(state='not_repository'))
        self.board.refresh();join_scan(self.board)
        self.server=Server(0,self.board)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)

    def request(self,path='/api/usage/work',body=None,raw=None,auth=True,headers=None,method='POST'):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=10)
        sent={'Host':self.server.origin.split('//')[1],'Content-Type':'application/json'}
        if auth:sent.update(Origin=self.server.origin,**{'X-PLER-Token':self.server.token})
        sent.update(headers or {})
        if raw is None and body is not None:raw=json.dumps(body,ensure_ascii=False).encode('utf-8')
        connection.request(method,path,body=raw,headers=sent)
        response=connection.getresponse();value=response.status,response.read();connection.close();return value

    def test_create_rename_link_unlink_delete_roundtrip_changes_only_manual_store(self):
        session=self.board.view(days=0)['sessions'][0]['id']
        before=self.board.view(days=0)['totals']
        code,raw=self.request(body=dict(action='create',title=TITLE,session=session));self.assertEqual(code,200)
        made=json.loads(raw)['id'];self.assertEqual(set(json.loads(raw)),{'ok','id'})
        for body in (dict(action='rename',id=made,title='Revised'),dict(action='unlink',id=made,session=session),
                     dict(action='link',id=made,session=session),dict(action='delete',id=made)):
            self.assertEqual(self.request(body=body)[0],200)
        self.assertEqual(self.board.view(days=0)['work_items']['items'],[])
        self.assertEqual(self.board.view(days=0)['totals'],before)

    def test_authentication_and_origin_are_checked_before_store_access(self):
        with patch.object(self.board,'mutate_work_item',side_effect=AssertionError('unauthorized work access')):
            for auth,headers in ((False,{}),(True,{'Origin':'https://outside.invalid'}),(True,{'X-PLER-Token':'wrong'})):
                self.assertEqual(self.request(body=dict(action='create',title=TITLE),auth=auth,headers=headers)[0],403)
        self.assertFalse((self.cache/work_items.FILENAME).exists())

    def test_unknown_fields_bad_types_duplicate_fields_and_oversize_are_refused(self):
        bad=[b'{"action":"create","action":"delete","title":"x"}',b'[]',b'{"action":"delete","id":true}',
             json.dumps(dict(action='create',title=TITLE,path='/private')).encode(),
             json.dumps(dict(action='link',id='a'*24,session='PRIVATE-PATH')).encode(),b'{"action":"create","title":NaN}',
             json.dumps(dict(action='create',title=TITLE)).encode('utf-16'),
             b'{"action":"create","title":"'+b'x'*1024+b'"}']
        with patch.object(self.board,'mutate_work_item',side_effect=AssertionError('invalid request reached store')):
            for raw in bad:
                with self.subTest(raw=raw[:40]):
                    code,value=self.request(raw=raw);self.assertEqual(code,400)
                    self.assertEqual(json.loads(value)['code'],'invalid');self.assertNotIn(TITLE.encode(),value)

    def test_unicode_titles_respect_character_limit_and_invalid_titles_are_not_saved(self):
        for title in ('','   ','x'*121,'private\nline','\ud800'):
            code,value=self.request(body=dict(action='create',title=title),
                                    raw=json.dumps(dict(action='create',title=title)).encode())
            self.assertEqual(code,400);self.assertEqual(json.loads(value)['code'],'invalid')
        self.assertFalse((self.cache/work_items.FILENAME).exists())
        title='\U0001f600'*120
        self.assertEqual(self.request(body=dict(action='create',title=title))[0],200)
        self.assertEqual(self.board.view(days=0)['work_items']['items'][0]['title'],title)

    def test_header_admission_refuses_transfer_encoding_duplicate_or_missing_length(self):
        with patch.object(self.board,'mutate_work_item',side_effect=AssertionError('bad framing reached store')):
            for headers in ({'Transfer-Encoding':'chunked'},{'Content-Length':'1025'},
                            {'Content-Type':'application/octet-stream'}):
                self.assertEqual(self.request(raw=b'{}',headers=headers)[0],400)
            for lengths in ([],['2','2']):
                connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=10)
                connection.putrequest('POST','/api/usage/work',skip_host=True)
                connection.putheader('Host',self.server.origin.split('//')[1]);connection.putheader('Origin',self.server.origin)
                connection.putheader('X-PLER-Token',self.server.token);connection.putheader('Content-Type','application/json')
                for length in lengths:connection.putheader('Content-Length',length)
                connection.endheaders(b'{}');response=connection.getresponse();self.assertEqual(response.status,400)
                response.read();connection.close()

    def test_errors_are_fixed_safe_codes_and_existing_files_stay_unchanged(self):
        before=self.board.view(days=0)['totals']
        code,raw=self.request(body=dict(action='create',title=TITLE,session='f'*24))
        self.assertEqual(code,404);self.assertEqual(json.loads(raw)['code'],'missing_session')
        code,raw=self.request(body=dict(action='rename',id='f'*24,title=TITLE))
        self.assertEqual(code,404);self.assertEqual(json.loads(raw)['code'],'missing')
        self.assertNotIn(TITLE.encode(),raw);self.assertEqual(self.board.view(days=0)['totals'],before)

    def test_normal_usage_exports_omit_titles_and_memberships_in_both_mask_modes(self):
        made=self.board.mutate_work_item('create',title=TITLE)['id']
        code,raw=self.request('/api/usage?days=0',method='GET')
        self.assertEqual(code,200);self.assertIn(TITLE.encode(),raw)
        for mask in ('0','1'):
            code,raw=self.request('/api/usage/export?days=0&mask_projects='+mask,method='GET')
            self.assertEqual(code,200);self.assertNotIn(TITLE.encode(),raw)
            self.assertNotIn(made.encode(),raw);self.assertNotIn('work_items',json.loads(raw))

    def test_invalid_query_options_and_closed_state_are_refused(self):
        for query in ('?path=/private','?lang=en&lang=tr','?lang=bad'):
            self.assertEqual(self.request('/api/usage/work'+query,dict(action='create',title=TITLE))[0],400)
        self.board.close()
        code,raw=self.request(body=dict(action='create',title=TITLE))
        self.assertEqual(code,409);self.assertEqual(json.loads(raw)['code'],'unavailable')
