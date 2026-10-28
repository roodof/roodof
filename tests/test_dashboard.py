"""Synthetic metadata only: privacy, honest session periods, cache lifecycle and local HTTP."""
from datetime import datetime, timedelta, timezone
import http.client
import json
import threading
import unittest
from unittest.mock import patch

from pler.usage.records import Session
from pler.dashboard import UsageDashboard, project_view
from pler.server import Server

SECRET='PRIVATE-PROMPT-AND-COMMAND'
NOW=datetime(2026,10,26,10,tzinfo=timezone.utc)


def sessions():
    a=Session('codex','session-one','C:/'+SECRET+'/rollout.jsonl',project='C:/Users/'+SECRET+'/Projects/shop',
              started=NOW-timedelta(days=40),ended=NOW-timedelta(days=1),calls=2,prompts=1,
              tokens=dict(input=10,cache_read=80,cache_write=0,output=10,reasoning=5),
              models={'model-a':2},model_tokens={'model-a':100},files_edited={SECRET},notes=[SECRET],
              reported_cost_usd=999,quota_plan='plus',quota=[(NOW-timedelta(hours=2),300,10),(NOW,300,20)])
    b=Session('claude-code','session-two',SECRET,project='/work/other',started=NOW-timedelta(days=2),ended=NOW,
              calls=1,prompts=1,tokens=dict(input=5,cache_read=0,cache_write=10,output=5,reasoning=0),
              model_tokens={'model-b':20},models={'model-b':1})
    return [a,b]


class ProjectionTests(unittest.TestCase):
    def test_period_selects_active_sessions_but_does_not_invent_daily_spending(self):
        data=project_view(sessions(),{},days=7,now=NOW)
        self.assertEqual(data['totals']['total_tokens'],120)
        self.assertEqual(data['period']['mode'],'active_sessions_full_totals')
        self.assertEqual(data['period']['cross_period_sessions'],1)
        self.assertNotIn('days',data)
        self.assertEqual(sum(data['totals']['tokens'][k] for k in ('input','cache_read','cache_write','output')),120)

    def test_explicit_projection_drops_transcript_paths_costs_notes_and_source_ids(self):
        data=project_view(sessions(),dict(skipped=[(SECRET,'PermissionError')]),days=0,now=NOW)
        encoded=json.dumps(data)
        for private in (SECRET,'session-one','reported_cost_usd','C:/Users','rollout.jsonl'):
            self.assertNotIn(private,encoded)
        self.assertEqual(data['sources']['unreadable'],1)
        self.assertEqual(data['sessions'][0]['edited_files'],1)
        self.assertEqual(data['sessions'][0]['project'],'Projects/shop')

    def test_agent_and_opaque_project_filters_keep_totals_consistent(self):
        data=project_view(sessions(),{},days=0,agent='codex',now=NOW)
        self.assertEqual((data['totals']['sessions'],data['totals']['total_tokens']),(1,100))
        key=data['sessions'][0]['project_id']
        self.assertEqual(project_view(sessions(),{},days=0,project=key,now=NOW)['totals']['total_tokens'],100)
        for kw in (dict(days=True),dict(days=-1),dict(days=31),dict(agent='other'),dict(project='../outside')):
            with self.subTest(kw=kw),self.assertRaises(ValueError):project_view(sessions(),{},**kw)

    def test_empty_and_unknown_dates_are_valid_without_fabricating_a_visible_date(self):
        self.assertEqual(project_view([],{},days=0)['totals']['total_tokens'],0)
        rows=sessions()+[Session('codex','unknown','ignored')]
        result=project_view(rows,{},days=0,now=NOW)
        self.assertIsNone(result['sessions'][-1]['started'])
        self.assertEqual(result['totals']['sessions'],3)

    def test_quota_is_a_dated_account_snapshot_and_unknown_call_split_is_explained(self):
        rows=sessions();rows[0].notes=['Older Codex log: session total from cumulative token_count; per-call split unknown.']
        value=project_view(rows,{},days=0,now=NOW,lang='tr')
        self.assertEqual(value['quota']['latest'][0]['used_percent'],20)
        self.assertEqual(value['sessions'][0]['quota_burn'][0]['percentage_points'],10)
        self.assertIn('bilinmiyor',value['sessions'][0]['notes'][0])
        self.assertFalse(value['sessions'][0]['calls_complete'])
        self.assertEqual(value['unknown_call_sessions'],1)

    def test_record_span_and_reported_work_time_are_separate_and_missing_stays_unknown(self):
        rows=sessions()
        rows[0].active_ms=90000
        value=project_view(rows,{},days=0,now=NOW)['sessions']
        self.assertEqual(value[0]['span_seconds'],39*86400)
        self.assertEqual(value[0]['active_ms'],90000)
        self.assertIsNone(value[1]['active_ms'])
        rows[0].started=None
        rows[0].active_ms=-1
        value=project_view(rows,{},days=0,now=NOW)['sessions'][0]
        self.assertIsNone(value['span_seconds'])
        self.assertIsNone(value['active_ms'])
        rows[0].started=rows[0].ended+timedelta(seconds=1)
        rows[0].active_ms=True
        value=project_view(rows,{},days=0,now=NOW)['sessions'][0]
        self.assertIsNone(value['span_seconds'])
        self.assertIsNone(value['active_ms'])
        rows[0].started=rows[0].ended
        rows[0].active_ms=0
        value=project_view(rows,{},days=0,now=NOW)['sessions'][0]
        self.assertEqual((value['span_seconds'],value['active_ms']),(0,0))

    def test_legacy_account_meter_does_not_change_with_project_agent_or_period_filters(self):
        rows=sessions()
        rows[1].quota=[(NOW+timedelta(minutes=1),300,35)]
        all_data=project_view(rows,{},days=0,now=NOW)
        project=all_data['sessions'][0]['project_id']
        for filters in (dict(agent='codex'),dict(project=project),dict(days=7)):
            with self.subTest(filters=filters):
                data=project_view(rows,{},now=NOW,**filters)
                self.assertEqual(data['quota'],all_data['quota'])
                self.assertEqual(data['quota']['latest'][0]['used_percent'],35)


class SnapshotTests(unittest.TestCase):
    def test_refresh_is_single_flight_and_does_not_block_snapshot_reads(self):
        release=threading.Event()
        def reader():release.wait(3);return sessions(),dict(claude_files=1,codex_files=1,skipped=[])
        service=UsageDashboard(reader)
        first=service.refresh();second=service.refresh()
        self.assertTrue(first['started']);self.assertFalse(second['started'])
        self.assertEqual(service.view()['state'],'scanning')
        release.set();service.thread.join(5)
        result=service.view(days=0)
        self.assertEqual(result['state'],'ready');self.assertTrue(result['has_snapshot'])
        self.assertEqual(result['new_model_calls'],0)

    def test_reader_failure_keeps_prior_snapshot_and_never_leaks_exception_content(self):
        service=UsageDashboard(lambda:(sessions(),{}));service.refresh();service.thread.join(5)
        def failed():raise OSError(SECRET)
        service.reader=failed;service.refresh();service.thread.join(5)
        value=service.view(days=0)
        self.assertEqual(value['state'],'error');self.assertEqual(value['totals']['total_tokens'],120)
        self.assertNotIn(SECRET,json.dumps(value))


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = Server(0, UsageDashboard(lambda: (sessions(), dict(claude_files=1, codex_files=1, skipped=[]))))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, path, method='GET', body=None, headers=None, authenticated=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        sent = {'Host': self.server.origin.split('//')[1]}
        if authenticated or authenticated is None and method=='GET':
            sent.update({'Origin': self.server.origin, 'X-PLER-Token': self.server.token})
        data = None if body is None else json.dumps(body).encode('utf-8')
        if data is not None:
            sent['Content-Type'] = 'application/json'
        sent.update(headers or {})
        connection.request(method, path, body=data, headers=sent)
        response = connection.getresponse()
        value = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return value

    def test_it_listens_on_this_computer_only_and_serves_three_fixed_files(self):
        self.assertEqual(self.server.server_address[0], '127.0.0.1')
        code, headers, page = self.request('/')
        self.assertEqual(code, 200)
        self.assertIn('PLER · My usage', page.decode())
        self.assertNotIn(self.server.token, page.decode())
        self.assertIn("default-src 'self'", headers['Content-Security-Policy'])
        for path in ('/app.js', '/app.css'):
            self.assertEqual(self.request(path)[0], 200)
        for path in ('/usage.js', '/index.html', '/web/app.js', '/../server.py', '/api/runs', '/api/live'):
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)
        self.assertEqual(json.loads(self.request('/api/health')[2])['app'], 'pler')

    def test_report_reads_and_exports_require_the_private_startup_link(self):
        self.assertEqual(self.server.access_url,self.server.origin+'/#access='+self.server.token)
        for path in ('/api/usage','/api/usage/export'):
            self.assertEqual(self.request(path,authenticated=False)[0],401)
            self.assertEqual(self.request(path,headers={'X-PLER-Token':'wrong'})[0],401)
        self.assertEqual(self.request('/api/usage')[0],200)

    def test_opening_the_page_reads_nothing_until_the_page_asks(self):
        with patch.object(self.server.dashboard, 'reader', side_effect=AssertionError('no implicit scan')):
            code, _, body = self.request('/api/usage')
        self.assertEqual((code, json.loads(body)['state']), (200, 'idle'))
        self.assertEqual(self.request('/api/usage/export')[0], 400)

    def test_reading_again_needs_the_page_token_and_an_empty_request(self):
        self.assertEqual(self.request('/api/usage/refresh', 'POST', {})[0], 403)
        self.assertEqual(self.request('/api/usage/refresh', 'POST', {'path': 'C:/logs'}, authenticated=True)[0], 400)
        self.assertEqual(self.request('/api/usage/refresh', 'POST', {}, authenticated=True)[0], 202)
        self.server.dashboard.thread.join(5)
        data = json.loads(self.request('/api/usage?days=0')[2])
        self.assertEqual(data['totals']['total_tokens'], 120)
        self.assertNotIn(SECRET, json.dumps(data))
        self.assertIn('pler-kullanim-ozeti.json', self.request('/api/usage/export?days=0&lang=tr')[1]['Content-Disposition'])
        code, headers, body = self.request('/api/usage/export?days=0&agent=codex')
        self.assertEqual(code, 200)
        self.assertIn('pler-usage-summary.json', headers['Content-Disposition'])
        self.assertNotIn('project_options', json.loads(body))
        self.assertNotIn('work/other', body.decode())

    def test_other_sites_and_unknown_questions_are_refused(self):
        self.assertEqual(self.request('/', headers={'Host': 'evil.example:80'})[0], 403)
        self.assertEqual(self.request('/api/usage', headers={'Origin': 'http://evil.example'})[0], 403)
        self.assertEqual(self.request('/api/usage', headers={'Sec-Fetch-Site': 'cross-site'})[0], 403)
        self.assertEqual(self.request('/api/usage/refresh', 'POST', {}, headers={'X-PLER-Token': self.server.token,
                                                                             'Origin': 'http://evil.example'})[0], 403)
        for query in ('days=3', 'days=7&days=30', 'root=C:/logs', 'agent=other', 'project=../outside', 'days='):
            with self.subTest(query=query):
                self.assertEqual(self.request('/api/usage?' + query)[0], 400)
        self.assertEqual(self.request('/api/shutdown', 'POST', {}, authenticated=True)[0], 404)

    def test_missing_project_is_distinct_from_other_read_errors(self):
        code,_,body=self.request('/api/usage?project=removed')
        self.assertEqual(code,400)
        self.assertEqual(json.loads(body)['code'],'unknown_project')
        self.assertNotIn('code',json.loads(self.request('/api/usage?days=3')[2]))

    def test_close_stops_the_server(self):
        self.assertEqual(self.request('/api/quit', 'POST', {'now': True}, authenticated=True)[0], 400)
        self.assertEqual(self.request('/api/quit', 'POST', {}, authenticated=True)[0], 200)
        self.thread.join(5)
        self.assertFalse(self.thread.is_alive())


if __name__ == '__main__':
    unittest.main()
