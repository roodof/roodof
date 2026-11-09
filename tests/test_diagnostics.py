"""Synthetic observations only. Diagnostic downloads must never echo source data or errors."""
import http.client
import json
from pathlib import Path
import threading
from types import SimpleNamespace
from unittest.mock import patch

from pler import diagnostics
from pler.dashboard import UsageDashboard
from pler.reporting import without_work_items, mask_projects
from pler.server import Server
from pler.usage import session_titles
from pler.usage.records import Session
from pler.usage.verdicts import session_code
from test_adoption_api import IsolatedMetadata,join_scan
from test_archive import codex_rows
from test_logs import write_jsonl

PRIVATE='PRIVATE-PATH-PROMPT-TITLE-TOKEN-EXCEPTION-CANARY'


class DiagnosticTests(IsolatedMetadata):
    def board(self):
        write_jsonl(self.codex/'rollout-invented.jsonl',codex_rows())
        board=UsageDashboard(git_reader=lambda _:dict(state='not_repository'))
        self.addCleanup(board.close);board.refresh();join_scan(board)
        self.assertEqual(board.state,'ready')
        return board

    def test_projection_emits_only_allowlisted_messages_codes_and_counts(self):
        sources=dict(skipped=[('/'+PRIVATE,'PermissionError'),('/'+PRIVATE,PRIVATE),('/'+PRIVATE,'WSLNotRunning')],
                     title_status={PRIVATE:dict(state='fallback',reason='metadata_large',title=PRIVATE),
                                   'other':dict(state='fallback',reason=PRIVATE)},
                     git_activity={PRIVATE:dict(state='ready',changed=True,directory=PRIVATE,events=[PRIVATE])},
                     archive=dict(errors=1,evicted_files=2,unverified_files=3,path=PRIVATE),
                     verdicts_error=True,work_items_error=True,session_titles={PRIVATE:PRIVATE})
        value=diagnostics.view(sources,'ready','2026-11-08T10:00:00+00:00',lang='tr')
        encoded=json.dumps(value,ensure_ascii=False)
        self.assertNotIn(PRIVATE,encoded)
        items={item['code']:item for item in value['items']}
        self.assertEqual(items['source_access_denied']['count'],1)
        self.assertEqual(items['source_unreadable']['count'],1)
        self.assertEqual(items['source_wsl_stopped']['count'],1)
        self.assertEqual(items['title_metadata_large']['stage'],'titles')
        self.assertEqual(items['git_limited']['count'],1)
        self.assertEqual(items['saved_metadata']['count'],2)
        self.assertTrue(all(item['next'] for item in value['items']))

    def test_title_reasons_do_not_mark_usage_as_incomplete_or_enter_exports(self):
        board=self.board();value=board.view(0)
        self.assertEqual(value['sessions'][0]['title_info']['code'],'title_metadata_missing')
        self.assertTrue(value['quality']['tokens_complete'])
        self.assertTrue(any(i['stage']=='titles' for i in value['diagnostics']['items']))
        for exported in (without_work_items(value),mask_projects(value)):
            self.assertNotIn('diagnostics',exported)
            self.assertNotIn('title_info',exported['sessions'][0])
        identity=value['sessions'][0]['id']
        self.assertEqual(board.session(identity,'tr')['title_info']['code'],'title_metadata_missing')

    def test_refresh_rereads_title_metadata_without_changing_accounting(self):
        board=self.board();before=board.view(0)['totals']
        index=self.codex.parent/'session_index.jsonl'
        index.write_text(json.dumps(dict(id='codex',thread_name=PRIVATE))+'\n',encoding='utf-8')
        board.refresh();join_scan(board);value=board.view(0)
        self.assertEqual(value['sessions'][0]['title'],PRIVATE)
        self.assertEqual(value['sessions'][0]['title_info']['state'],'available')
        self.assertEqual(value['totals'],before)
        self.assertNotIn(PRIVATE,json.dumps(board.diagnostic_view()))
        self.assertNotIn(PRIVATE,json.dumps(without_work_items(value)))

    def test_failed_log_attempt_keeps_previous_snapshot_and_fixed_phase_code(self):
        board=self.board();previous=board.view(0)['totals'];at=board.scanned_at
        original=board.reader
        def fail():raise RuntimeError(PRIVATE)
        board.reader=fail;board.refresh();join_scan(board)
        value=board.view(0)
        self.assertEqual(value['totals'],previous)
        self.assertEqual(value['diagnostics']['snapshot'],'previous')
        self.assertEqual(board.scanned_at,at)
        self.assertEqual(board.failure_code,'logs_failed')
        self.assertNotIn(PRIVATE,json.dumps(value))
        board.reader=original;board.refresh();join_scan(board)
        self.assertIsNone(board.failure_code)
        self.assertEqual(board.diagnostic_view()['snapshot'],'current')

    def test_title_git_and_projection_failures_are_distinguished_without_raw_errors(self):
        board=self.board()
        cases=[('pler.usage.session_titles.inspect','titles_failed'),
               ('pler.dashboard.git_links','git_failed'),('pler.dashboard.project_view','projection_failed')]
        for target,code in cases:
            with self.subTest(code=code):
                with patch(target,side_effect=RuntimeError(PRIVATE)):
                    board.refresh();join_scan(board)
                self.assertEqual(board.failure_code,code)
                data=board.diagnostic_view()
                self.assertEqual(data['snapshot'],'previous')
                self.assertIn(code,{item['code'] for item in data['items']})
                self.assertNotIn(PRIVATE,json.dumps(data))
                board.refresh();join_scan(board);self.assertIsNone(board.failure_code)

    def test_no_snapshot_failure_still_has_downloadable_status(self):
        def fail():raise RuntimeError(PRIVATE)
        board=UsageDashboard(reader=fail);self.addCleanup(board.close)
        board.refresh();join_scan(board)
        value=board.view(0)
        self.assertFalse(value['has_snapshot'])
        self.assertEqual(value['diagnostics']['snapshot'],'none')
        self.assertEqual(value['diagnostics']['items'][0]['code'],'logs_failed')

    def test_source_and_identity_preferences_have_dedicated_codes(self):
        from pler.usage.sources import SourceError
        from pler.usage.identities import IdentityError
        from pler.usage.input_limits import ReadLimitExceeded
        for error,code in ((SourceError(),'source_preferences'),(IdentityError(),'identity_preferences'),(ReadLimitExceeded(),'scan_limit')):
            with self.subTest(code=code):
                def fail():raise error
                board=UsageDashboard(reader=fail);self.addCleanup(board.close)
                board.refresh();join_scan(board)
                self.assertEqual(board.failure_code,code)
                self.assertEqual(board.diagnostic_view()['items'][0]['code'],code)

    def test_diagnostics_are_filter_independent_and_read_only(self):
        board=self.board();before={p.name:p.read_bytes() for p in self.cache.iterdir() if p.is_file()}
        first=board.view(0,'all')['diagnostics']
        filtered=board.view(7,'claude-code')['diagnostics']
        self.assertEqual(first,filtered)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.cache.iterdir() if p.is_file()})

    def test_diagnostic_endpoint_is_authenticated_bounded_and_rejects_extra_fields(self):
        board=self.board();server=Server(0,board);self.addCleanup(server.server_close)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();self.addCleanup(server.shutdown)
        def get(query='',auth=True):
            c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
            c.request('GET','/api/usage/diagnostics'+query,headers={'X-PLER-Token':server.token} if auth else {})
            response=c.getresponse();raw=response.read();c.close();return response.status,json.loads(raw),len(raw)
        self.assertEqual(get(auth=False)[0],401)
        self.assertEqual(get('?path='+PRIVATE)[0],400)
        self.assertEqual(get('?lang=en&lang=tr')[0],400)
        status,value,size=get('?lang=tr');self.assertEqual(status,200);self.assertLess(size,65536)
        self.assertIn('Başlık',value['items'][0]['title'])
        self.assertNotIn(str(self.root),json.dumps(value))


class TitleReasonTests(IsolatedMetadata):
    def session(self,agent='codex'):
        source=(self.codex/'rollout-title.jsonl') if agent=='codex' else (self.claude/'invented/title.jsonl')
        source.parent.mkdir(parents=True,exist_ok=True);source.write_text('',encoding='utf-8')
        return Session(agent,'invented',str(source))

    def reason(self,session):
        titles,statuses=session_titles.inspect([session])
        return titles,statuses[session_code(session)]

    def test_missing_large_invalid_and_valid_indexes_have_different_reasons(self):
        s=self.session();index=self.codex.parent/'session_index.jsonl'
        self.assertEqual(self.reason(s)[1]['reason'],'metadata_missing')
        index.write_bytes(b' '*(session_titles.MAX_FILE+1))
        self.assertEqual(self.reason(s)[1]['reason'],'metadata_large')
        index.write_text('{broken}\n',encoding='utf-8')
        self.assertEqual(self.reason(s)[1]['reason'],'metadata_invalid')
        index.write_text(json.dumps(dict(id='other',thread_name='Other title'))+'\n',encoding='utf-8')
        self.assertEqual(self.reason(s)[1]['reason'],'not_recorded')
        index.write_text(json.dumps(dict(id='invented',thread_name='Exact title'))+'\n',encoding='utf-8')
        self.assertEqual(self.reason(s)[1],dict(state='available',reason='provided'))

    def test_read_budget_and_permissions_do_not_claim_title_absence(self):
        s=self.session();index=self.codex.parent/'session_index.jsonl';index.write_text('{}\n',encoding='utf-8')
        with patch.object(session_titles,'MAX_TOTAL',0):self.assertEqual(self.reason(s)[1]['reason'],'read_budget')
        with patch('builtins.open',side_effect=PermissionError(PRIVATE)):
            result=self.reason(s)[1];self.assertEqual(result['reason'],'access_denied');self.assertNotIn(PRIVATE,json.dumps(result))

    def test_claude_window_is_explicit_even_when_a_title_was_found(self):
        s=self.session('claude-code');source=Path(s.source)
        first=json.dumps(dict(type='custom-title',sessionId='invented',customTitle='Early title'))+'\n'
        filler=json.dumps(dict(type='other',metadata='x'*4000))+'\n'
        source.write_text(first+filler*40,encoding='utf-8')
        names,status=self.reason(s)
        self.assertEqual(names[session_code(s)],'Early title')
        self.assertEqual(status,dict(state='limited',reason='window_limited'))
        # A middle-only rename is not falsely described as never recorded.
        source.write_text(filler*20+first+filler*20,encoding='utf-8')
        names,status=self.reason(s);self.assertEqual(names,{})
        self.assertEqual(status,dict(state='fallback',reason='window_limited'))

    def test_archive_never_reads_live_title_files_and_relative_layout_is_explicit(self):
        s=self.session();s.source_state='archive'
        with patch.object(session_titles.Reader,'read',side_effect=AssertionError('archive title read')):
            self.assertEqual(self.reason(s)[1]['reason'],'archive_only')
        s.source_state='live';s.source='relative.jsonl'
        self.assertEqual(self.reason(s)[1]['reason'],'location_unknown')

    def test_changed_metadata_is_not_published_as_a_current_title(self):
        s=self.session();index=self.codex.parent/'session_index.jsonl';index.write_text('{}\n',encoding='utf-8')
        original=session_titles.os.fstat;calls=[]
        def changing(fd):
            value=original(fd);calls.append(1)
            return value if len(calls)==1 else SimpleNamespace(st_size=value.st_size+1,st_mtime_ns=value.st_mtime_ns,
                                                              st_ino=value.st_ino,st_dev=value.st_dev)
        with patch.object(session_titles.os,'fstat',side_effect=changing):
            _,status=self.reason(s)
        self.assertEqual(status['reason'],'read_changed')

    def test_restricted_network_title_never_probes_a_share(self):
        s=Session('codex','invented','//example.invalid/share/sessions/rollout.jsonl')
        with patch.object(Path,'lstat',side_effect=AssertionError('UNC probe')):
            self.assertEqual(self.reason(s)[1]['reason'],'source_restricted')

    def test_valid_index_does_not_hide_a_missing_claude_transcript(self):
        s=self.session('claude-code');source=Path(s.source)
        (source.parent/'sessions-index.json').write_text(json.dumps(dict(entries=[dict(sessionId='invented',summary='Older index title')])),encoding='utf-8')
        source.unlink();names,status=self.reason(s)
        self.assertEqual(names[session_code(s)],'Older index title')
        self.assertEqual(status,dict(state='limited',reason='metadata_missing'))
