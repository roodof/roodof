"""Invented response evidence and a controlled clock; no provider or real user logs."""
import copy
from datetime import datetime,timedelta,timezone
import json
import threading
import unittest
from unittest.mock import patch

from pler.dashboard import UsageDashboard
from pler.server import Server
from pler.usage import backup,followups as f,work_items as w
from pler.usage import claude_code,codex
from pler.usage.cache import FileCache
from pler.reporting import PARSER_VERSION
from pler.usage.records import Session,empty_tokens
from pler.usage.verdicts import session_code
from test_adoption_api import IsolatedMetadata,join_scan
import test_work_items_api as old_http
import test_period_usage as native
from test_logs import write_jsonl

NOW=datetime(2026,11,1,12,tzinfo=timezone.utc)
PRIVATE='PRIVATE-FOLLOWUP-NOTE-CANARY'


def session(n,at,tokens=100,model='invented-model',project='/invented/app',agent='codex'):
    usage=empty_tokens();usage['input']=tokens
    s=Session(agent,'invented-'+str(n),'C:/invented/source-'+str(n)+'.jsonl',project=project,
              started=at,ended=at,calls=1,tokens=usage,models={model:1},model_tokens={model:tokens})
    s._usage_events=[dict(first=at,at=at,tokens=dict(usage),usd=0)]
    return s


def samples(anchor=NOW):
    return [session(i,anchor-timedelta(days=i+1),100*(i+1)) for i in range(3)]


def measure(rows,since=None,until=NOW,observed=None,members=None,sources=None):
    return f.measure(rows,members if members is not None else [session_code(s) for s in rows],
                     since or until-f.WINDOW,until,observed or until,sources)


def record(rows=None):
    return dict(id='f'*24,method=f.METHOD,parser_version=PARSER_VERSION,created_at=int(NOW.timestamp()),
                trigger='session_pattern',observation=PRIVATE,change='Try smaller work sessions',baseline=measure(rows or samples()),
                status='open',review=None,cancelled_at=None,cancel_note='')


def reviewed(context='similar'):
    r=record();end=NOW+f.WINDOW
    after=[session(i+3,NOW+timedelta(days=i+1),50*(i+1)) for i in range(3)]
    r.update(status='reviewed',review=dict(after=measure(after,until=end),baseline_match=True,parser_match=True,context=context,note=''))
    return r


class MeasurementTests(unittest.TestCase):
    def test_equal_half_open_windows_never_copy_active_session_totals(self):
        row=samples()[0];old=row._usage_events[0]
        old['first']=NOW-f.WINDOW;old['at']=NOW-f.WINDOW
        extra=dict(first=NOW,at=NOW,tokens=dict(row.tokens),usd=0)
        row._usage_events.append(extra);row.calls=2;row.tokens['input']*=2;row.ended=NOW
        row.model_tokens={'invented-model':row.tokens['input']}
        before=measure([row]);after=measure([row],until=NOW+f.WINDOW)
        self.assertEqual((before['tokens'],before['responses'],after['tokens'],after['responses']),(100,1,100,1))

    def test_median_is_of_per_session_response_averages_and_not_pooled_totals(self):
        rows=samples();row=rows[2];event=row._usage_events[0]
        row._usage_events=[dict(event) for _ in range(20)];row.calls=20;row.tokens['input']=6000;row.model_tokens={'invented-model':6000}
        result=measure(rows)
        self.assertEqual(result['responses'],22)
        self.assertEqual(result['cohorts'][0]['median_tokens_per_response'],200)

    def test_future_events_do_not_move_frozen_baseline_fingerprint(self):
        rows=samples();before=measure(rows)
        row=rows[0];event=dict(first=NOW+timedelta(days=1),at=NOW+timedelta(days=1),tokens=dict(row.tokens),usd=0)
        row._usage_events.append(event);row.calls=2;row.tokens['input']*=2;row.ended=event['at']
        self.assertEqual(measure(rows,observed=NOW+f.WINDOW)['fingerprint'],before['fingerprint'])
        row._usage_events[0]['tokens']['input']+=1;row.tokens['input']+=1
        self.assertNotEqual(measure(rows,observed=NOW+f.WINDOW)['fingerprint'],before['fingerprint'])

    def test_boundary_undated_unreconciled_and_multi_model_evidence_are_excluded(self):
        for kind,reason in [('boundary','boundary_response'),('undated','incomplete_usage'),('mismatch','incomplete_usage'),('models','unknown_scope'),('bad_event','incomplete_usage')]:
            rows=samples();row=rows[0]
            if kind=='boundary':row._usage_events[0]['first']=NOW-f.WINDOW-timedelta(seconds=1)
            elif kind=='undated':row._usage_events[0]['at']=None
            elif kind=='mismatch':row.tokens['input']+=1
            elif kind=='models':row.models['other-model']=1
            else:row._usage_events=[None]
            with self.subTest(kind=kind):
                value=measure(rows);self.assertIn(reason,value['limitations']);self.assertEqual(value['sessions'],2)

    def test_missing_source_loss_duplicates_and_integer_bounds_block_comparison(self):
        rows=samples();members=[session_code(s) for s in rows]+['a'*24]
        value=measure(rows+[copy.deepcopy(rows[0])],members=members,sources={'archive':{'errors':1}})
        self.assertEqual(set(value['limitations']),{'missing_sessions','source_incomplete','duplicate_sessions'})
        rows[0].tokens['input']=f.MAX_NUMBER;rows[0]._usage_events[0]['tokens']['input']=f.MAX_NUMBER
        self.assertIn('measurement_limit',measure(rows)['limitations'])

    def test_numeric_difference_requires_similar_context_and_unchanged_complete_groups(self):
        r=reviewed();result=f.comparison(r)
        self.assertEqual(result['limitations'],[]);self.assertEqual(result['cohorts'][0]['change_percent'],-50)
        self.assertEqual((result['cohorts'][0]['before'],result['cohorts'][0]['after']),(200,100))
        for key,value,reason in [('context','unknown','context_unknown'),('context','different','context_different'),('baseline_match',False,'baseline_changed'),('parser_match',False,'parser_changed')]:
            changed=copy.deepcopy(r);changed['review'][key]=value
            self.assertIn(reason,f.comparison(changed)['limitations']);self.assertEqual(f.comparison(changed)['cohorts'],[])
        changed=copy.deepcopy(r);changed['review']['after']['cohorts'][0]['model']='other-model'
        self.assertIn('cohort_changed',f.comparison(changed)['limitations'])
        changed=record(samples()[:2]);changed.update(status='reviewed',review=r['review'])
        self.assertIn('small_sample',f.comparison(changed)['limitations'])

    def test_strict_private_snapshot_record_contract_rejects_bad_or_future_payloads(self):
        valid=reviewed();self.assertEqual(f.validate([valid]),[valid])
        for change in (dict(method=2),dict(change=''),dict(observation='x\t'),dict(review=dict(valid['review'],baseline_match=1)),dict(source='C:/private')):
            with self.assertRaises((ValueError,TypeError)):f.validate([dict(valid,**change)])
        bad=copy.deepcopy(valid['baseline']);bad['session_ids']=[{}]
        with self.assertRaises(ValueError):f.validate_snapshot(bad)
        bad=copy.deepcopy(valid['baseline']);bad['cohorts'][0]['median_tokens_per_response']=float('nan')
        with self.assertRaises(ValueError):f.validate_snapshot(bad)

    def test_zero_baseline_and_bounded_event_budget_remain_unresolved(self):
        rows=samples()
        with patch.object(f,'MAX_EVENTS',1):self.assertIn('measurement_limit',measure(rows)['limitations'])
        r=reviewed();r['baseline']['cohorts'][0]['median_tokens_per_response']=0
        self.assertIn('zero_baseline',f.comparison(r)['limitations']);self.assertEqual(f.comparison(r)['cohorts'],[])


class FollowupStorageTests(IsolatedMetadata):
    def setUp(self):
        super().setUp();self.store=w.Folder(self.cache);self.identity=self.store.mutate('create',title='Invented work')['id']

    def start(self,r=None,scope=None):
        return self.store.followup(self.identity,'start_followup',None,r or record(),scope or w.membership_revision(self.store.read()[self.identity]))

    def test_real_readers_and_warm_cache_preserve_two_agent_groups_without_transcripts(self):
        folders={agent:self.root/('native-'+agent) for agent in ('codex','claude')}
        for path in folders.values():path.mkdir()
        for i in range(3):
            at=NOW-timedelta(days=i+1)
            write_jsonl(folders['codex']/('rollout-'+str(i)+'.jsonl'),[native.meta('cx-'+str(i),at),
                dict(type='turn_context',timestamp=at.isoformat(),payload=dict(model='invented-model')),
                native.response('reply-'+str(i),100*(i+1),at)])
            write_jsonl(folders['claude']/(str(i)+'.jsonl'),[native.reply('reply-'+str(i),100*(i+1),at,session='cc-'+str(i))])
        cx,_=codex.read(list(folders['codex'].glob('*.jsonl')),cache=FileCache('codex','followup-fixture'))
        cache=FileCache('claude','followup-fixture');cc=claude_code.read(list(folders['claude'].glob('*.jsonl')),cache=cache);cache.save()
        before=measure(cx+cc);self.assertEqual((before['sessions'],len(before['cohorts'])),(6,2));self.assertEqual(before['limitations'],[])
        with patch.object(claude_code,'_rows',side_effect=AssertionError('warm source reopened')):
            warm=claude_code.read(list(folders['claude'].glob('*.jsonl')),cache=FileCache('claude','followup-fixture'))
        self.assertEqual(measure(cx+warm),before)
        encoded=json.dumps(before);self.assertNotIn(native.SECRET,encoded);self.assertNotIn(native.TRANSCRIPT,encoded)
        self.assertNotIn(native.TRANSCRIPT,(self.cache/'claude.json').read_text(encoding='utf-8'))

    def test_legacy_two_keeps_goal_and_noop_bytes_then_upgrades_only_on_real_write(self):
        path=self.cache/w.FILENAME;data=json.loads(path.read_bytes());data['format']=2
        item=data['items'][self.identity];item.pop('followups');item['goal']='Existing goal'
        raw=json.dumps(data).encode();path.write_bytes(raw)
        self.store.mutate('rename',identity=self.identity,title=item['title'])
        self.assertEqual(path.read_bytes(),raw);self.assertEqual(self.store.read()[self.identity]['followups'],[])
        self.start();saved=json.loads(path.read_bytes());self.assertEqual(saved['format'],3);self.assertEqual(saved['items'][self.identity]['goal'],'Existing goal')

    def test_one_open_per_work_cancel_retains_baseline_then_delete_removes_only_record(self):
        self.start();r=self.store.read()[self.identity]['followups'][0]
        with self.assertRaises(w.WorkError) as error:self.start(dict(r,id='e'*24))
        self.assertEqual(error.exception.code,'active')
        self.store.followup(self.identity,'cancel_followup',r['id'],'Changed plan',f.digest(r))
        closed=self.store.read()[self.identity]['followups'][0]
        self.assertEqual(closed['baseline'],r['baseline']);self.assertEqual(closed['status'],'cancelled')
        self.store.followup(self.identity,'delete_followup',r['id'],None,f.digest(closed))
        self.assertEqual(self.store.read()[self.identity]['followups'],[])

    def test_same_second_revision_and_membership_conflicts_cannot_overwrite(self):
        scope=w.membership_revision(self.store.read()[self.identity]);self.store.mutate('link',identity=self.identity,session='a'*24)
        with self.assertRaises(w.WorkError):self.start(scope=scope)
        self.start();r=self.store.read()[self.identity]['followups'][0]
        self.store.followup(self.identity,'review_followup',r['id'],reviewed()['review'],f.digest(r))
        raw=(self.cache/w.FILENAME).read_bytes()
        with self.assertRaises(w.WorkError):self.store.followup(self.identity,'cancel_followup',r['id'],'',f.digest(r))
        self.assertEqual((self.cache/w.FILENAME).read_bytes(),raw)

    def test_atomic_failure_preserves_prior_file_and_private_backup_roundtrips(self):
        path=self.cache/w.FILENAME;before=path.read_bytes()
        with patch.object(w.archive,'_write',side_effect=OSError('invented failure')):
            with self.assertRaises(OSError):self.start()
        self.assertEqual(path.read_bytes(),before);self.start()
        data=backup.create();info=backup.inspect(data);self.assertNotIn(PRIVATE,json.dumps(info))
        target=self.root/'recovered';backup.restore(data,target)
        self.assertEqual(w.Folder(target).read(),self.store.read())
        self.store.mutate('delete',identity=self.identity);self.assertEqual(self.store.read(),{})

    def test_bounds_and_unsafe_future_files_are_never_overwritten(self):
        for n in range(f.MAX_PER_WORK):
            r=record();r['id']=format(n,'024x');r.update(status='cancelled',cancelled_at=r['created_at'])
            # A single atomic valid document sets up a full store without unnecessary writes.
            items=self.store.read();items[self.identity]['followups'].append(r)
            (self.cache/w.FILENAME).write_text(json.dumps(dict(format=w.FORMAT,items=items)),encoding='utf-8')
        raw=(self.cache/w.FILENAME).read_bytes()
        with self.assertRaises(w.WorkError) as error:self.start()
        self.assertEqual(error.exception.code,'limit');self.assertEqual((self.cache/w.FILENAME).read_bytes(),raw)
        data=json.loads(raw);data['items'][self.identity]['followups'][0]['method']=99
        raw=json.dumps(data).encode();(self.cache/w.FILENAME).write_bytes(raw)
        with self.assertRaises(w.WorkError):self.start()
        self.assertEqual((self.cache/w.FILENAME).read_bytes(),raw)


class FollowupFixture(IsolatedMetadata):
    def setUp(self):
        super().setUp();self.rows=samples();self.clock=NOW;self.reads=0
        def reader():
            self.reads+=1
            return self.rows,dict(codex_files=len(self.rows),claude_files=0,skipped=[],observed_at=self.clock.isoformat())
        self.board=UsageDashboard(reader,git_reader=lambda _:dict(state='not_repository'));self.addCleanup(self.board.close)
        self.board.refresh();join_scan(self.board);self.identity=self.board.mutate_work_item('create',title='Invented')['id']
        for row in self.rows:self.board.mutate_work_item('link',identity=self.identity,session=session_code(row))

    def start(self):
        view=self.board.followup_view(self.identity,now=self.clock)
        result=self.board.mutate_followup('start_followup',self.identity,view['preview_revision'],change='Try smaller sessions',observation=PRIVATE,now=self.clock)
        self.assertTrue(result['ok'],result)
        return result['followup']

    def advance(self):
        self.rows+= [session(i+3,NOW+timedelta(days=i+1),50*(i+1)) for i in range(3)]
        self.clock=NOW+f.WINDOW
        self.board.refresh();join_scan(self.board)
        for row in self.rows[3:]:self.board.mutate_work_item('link',identity=self.identity,session=session_code(row))


class FollowupDashboardTests(FollowupFixture):
    def test_baseline_is_fixed_lazy_reads_do_not_rescan_and_weekly_review_is_explicit(self):
        self.start();first=self.board.followup_view(self.identity,now=self.clock)['items'][0]
        self.assertFalse(first['ready']);self.assertEqual(self.reads,1)
        self.assertEqual(self.board.mutate_followup('review_followup',self.identity,'a'*24,record_id=first['id'],now=self.clock)['reason'],'early')
        self.advance();view=self.board.followup_view(self.identity,now=self.clock);r=view['items'][0]
        self.assertTrue(r['ready']);self.assertEqual(r['baseline'],first['baseline']);self.assertEqual(r['comparison']['cohorts'],[])
        before=self.board.view(days=0)['totals']
        result=self.board.mutate_followup('review_followup',self.identity,r['review_revision'],record_id=r['id'],context='similar',note='Same test task',now=self.clock)
        self.assertTrue(result['ok'],result)
        saved=self.board.followup_view(self.identity,now=self.clock)['items'][0]
        self.assertEqual(saved['comparison']['cohorts'][0]['change_percent'],-50);self.assertEqual(saved['review']['note'],'Same test task')
        self.assertEqual(self.board.view(days=0)['totals'],before);self.assertEqual(self.reads,2)
        self.clock+=f.WINDOW;self.assertEqual(self.board.followup_view(self.identity,now=self.clock)['items'][0]['review'],saved['review'])

    def test_source_change_between_preview_and_save_rejects_without_creating_record(self):
        view=self.board.followup_view(self.identity,now=self.clock)
        self.rows[0].tokens['input']+=1;self.rows[0]._usage_events[0]['tokens']['input']+=1
        result=self.board.mutate_followup('start_followup',self.identity,view['preview_revision'],change='Try',now=self.clock)
        self.assertEqual(result['reason'],'conflict');self.assertEqual(self.board.followup_view(self.identity,now=self.clock)['items'],[])

    def test_stale_scanning_corrupt_store_and_changed_history_do_not_produce_numeric_result(self):
        view=self.board.followup_view(self.identity,now=self.clock)
        self.assertEqual(self.board.mutate_followup('start_followup',self.identity,view['preview_revision'],change='Try',now=self.clock+timedelta(minutes=6))['reason'],'stale')
        self.start();self.advance();self.rows[0].tokens['input']+=1;self.rows[0]._usage_events[0]['tokens']['input']+=1
        r=self.board.followup_view(self.identity,now=self.clock)['items'][0]
        self.assertTrue(self.board.mutate_followup('review_followup',self.identity,r['review_revision'],record_id=r['id'],context='similar',now=self.clock)['ok'])
        saved=self.board.followup_view(self.identity,now=self.clock)['items'][0]
        self.assertIn('baseline_changed',saved['comparison']['limitations']);self.assertEqual(saved['comparison']['cohorts'],[])
        self.board.state='scanning';self.assertEqual(self.board.followup_view(self.identity,now=self.clock)['reason'],'unavailable')
        self.board.state='ready';path=self.cache/w.FILENAME;path.write_bytes(b'{bad')
        self.assertEqual(self.board.followup_view(self.identity,now=self.clock)['reason'],'unreadable');self.assertEqual(path.read_bytes(),b'{bad')


class FollowupHttpTests(FollowupFixture):
    request=old_http.WorkHttpTests.request

    def setUp(self):
        super().setUp()
        view=self.board.followup_view;mutate=self.board.mutate_followup
        self.board.followup_view=lambda identity,now=None:view(identity,now=now or self.clock)
        self.board.mutate_followup=lambda *args,**kwargs:mutate(*args,now=kwargs.pop('now',self.clock),**kwargs)
        self.server=Server(0,self.board);threading.Thread(target=self.server.serve_forever,daemon=True).start()
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)

    def body(self):
        view=self.board.followup_view(self.identity)
        return dict(action='start_followup',id=self.identity,expected_revision=view['preview_revision'],trigger='other',observation=PRIVATE,change='Try one thing')

    def test_roundtrip_private_get_export_omission_and_fixed_safe_conflicts(self):
        url='/api/usage/work/followups?work='+self.identity
        body=self.body();status,raw=self.request('/api/usage/work/followup',body=body);self.assertEqual(status,200)
        self.assertEqual(set(json.loads(raw)),{'ok','id','followup'})
        status,raw=self.request(url,method='GET');self.assertEqual(status,200);self.assertIn(PRIVATE.encode(),raw)
        for mask in (0,1):
            status,raw=self.request('/api/usage/export?days=0&mask_projects='+str(mask),method='GET')
            self.assertEqual(status,200);self.assertNotIn(PRIVATE.encode(),raw);self.assertNotIn('work_items',json.loads(raw))
        self.assertNotIn(PRIVATE,json.dumps(self.board.view(days=0)['work_items']))
        status,raw=self.request('/api/usage/work/followup',body=body)
        self.assertEqual((status,json.loads(raw)['code']),(409,'active'));self.assertNotIn(PRIVATE.encode(),raw)

    def test_auth_and_strict_admission_precede_any_private_measurement(self):
        valid=self.body()
        with patch.object(self.board,'mutate_followup',side_effect=AssertionError('invalid admission reached measurement')):
            self.assertEqual(self.request('/api/usage/work/followup',body=valid,auth=False)[0],403)
            self.assertEqual(self.request('/api/usage/work/followup',body=valid,headers={'Origin':'https://outside.invalid'})[0],403)
            for altered in (dict(valid,change=''),dict(valid,change='x'*1001),dict(valid,change='\ud800'),dict(valid,trigger=[]),dict(valid,baseline={}),dict(valid,expected_revision='C:/private'),dict(valid,action='delete')):
                raw=json.dumps(altered,ensure_ascii=True).encode()
                self.assertEqual(self.request('/api/usage/work/followup',raw=raw)[0],400)
            for raw,headers in [(b'{}',{'Content-Length':'16385'}),(b'{"action":"start_followup","action":"delete"}',{}),(b'{"change":NaN}',{}),(b'{}',{'Transfer-Encoding':'chunked'}),(b'{}',{'Content-Type':'text/plain'})]:
                self.assertEqual(self.request('/api/usage/work/followup',raw=raw,headers=headers)[0],400)
        with patch.object(self.board,'followup_view',side_effect=AssertionError('unauthorized read')):
            self.assertEqual(self.request('/api/usage/work/followups?work='+self.identity,method='GET',auth=False)[0],401)
            for suffix in ('?work=C:/private','?work='+self.identity+'&work='+self.identity,'?work='+self.identity+'&extra=1'):
                self.assertEqual(self.request('/api/usage/work/followups'+suffix,method='GET')[0],400)


if __name__=='__main__':unittest.main()
