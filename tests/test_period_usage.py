"""Dated usage is proven response metadata, never a split of a session total."""
import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler.usage import claude_code, codex, scan
from pler.usage.cache import FileCache
from pler.usage.period_usage import analyze, event_time
from pler.usage.records import Session, total
from test_logs import write_jsonl


NOW=datetime(2026,10,29,12,tzinfo=timezone.utc)
SINCE=NOW-timedelta(days=7)
OLD=NOW-timedelta(days=90)
SECRET='PRIVATE-PERIOD-PROMPT-PATH-IDENTITY'
TRANSCRIPT='PRIVATE-TRANSCRIPT-TEXT-CANARY'


def iso(at): return at.isoformat() if isinstance(at,datetime) else at


def meta(identity='one',at=OLD,parent=None):
    payload=dict(id=identity,cwd='/invented/'+SECRET)
    if parent is not None: payload['parent_thread_id']=parent
    return dict(type='session_meta',timestamp=iso(at),payload=payload)


def response(identity,value,at):
    payload=dict(usage=dict(input_tokens=value,output_tokens=0))
    if identity is not None: payload['response_id']=identity
    return dict(type='token_usage_record',timestamp=iso(at),payload=payload)


def cumulative(value,at):
    return dict(type='event_msg',timestamp=iso(at),payload=dict(type='token_count',
                info=dict(total_token_usage=dict(input_tokens=value,output_tokens=0))))


def reply(identity,value,at,session='one'):
    return dict(type='assistant',timestamp=iso(at),sessionId=session,cwd='/invented/'+SECRET,
                requestId='request-'+identity if identity is not None else None,
                message=dict(id=identity,model='invented-model',usage=dict(input_tokens=value,output_tokens=0),
                             content=[dict(type='text',text=TRANSCRIPT)]))


class PeriodUsageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.path=self.root/'rollout-test.jsonl'

    def codex(self,rows):
        write_jsonl(self.path,[meta()]+rows)
        sessions,issues=codex.read([self.path])
        self.assertEqual(issues,[])
        return sessions

    def claude(self,rows):
        write_jsonl(self.path,rows)
        issues=[]
        sessions=claude_code.read([self.path],issues)
        self.assertEqual(issues,[])
        return sessions

    def check(self,sessions,tokens,calls,unallocated=0):
        before=[copy.deepcopy(s.as_dict()) for s in sessions]
        value=analyze(sessions,SINCE,NOW)
        self.assertEqual((value['total_tokens'],value['response_calls'],value['unallocated_sessions']),
                         (tokens,calls,unallocated))
        self.assertEqual(value['retained_usage_fully_dated'],unallocated==0)
        self.assertEqual(value['selected_sessions'],value['eligible_sessions']+sum(value['excluded'].values()))
        self.assertEqual(value['dated_response_calls'],value['response_calls']+value['outside_period_calls'])
        self.assertEqual(before,[s.as_dict() for s in sessions])
        self.assertNotIn(SECRET,json.dumps(value,allow_nan=False))
        self.assertNotIn('_usage_events',json.dumps(before))
        return value

    def test_old_session_only_contributes_its_new_codex_response(self):
        sessions=self.codex([response('old',1000000,OLD),response('new',40,NOW-timedelta(hours=1))])
        self.assertEqual((sessions[0].calls,total(sessions[0].tokens)),(2,1000040))
        value=self.check(sessions,40,1)
        self.assertEqual((value['dated_response_calls'],value['outside_period_calls'],value['contributing_sessions']),(2,1,1))

    def test_old_session_only_contributes_its_new_claude_response(self):
        sessions=self.claude([reply('old',1000000,OLD),reply('new',50,NOW-timedelta(hours=1))])
        self.assertEqual((sessions[0].calls,total(sessions[0].tokens)),(2,1000050))
        self.check(sessions,50,1)

    def test_interval_boundaries_are_inclusive_and_none_means_all_dated_records(self):
        sessions=self.codex([response('before',1,SINCE-timedelta(microseconds=1)),
                             response('start',2,SINCE),response('end',3,NOW),
                             response('future',4,NOW+timedelta(microseconds=1))])
        value=self.check(sessions,5,2,1)
        self.assertEqual((value['outside_period_calls'],value['future_response_calls']),(1,1))
        self.assertEqual(analyze(sessions,None,NOW)['total_tokens'],6)

    def test_cumulative_only_total_is_not_allocated_to_its_checkpoint_date(self):
        sessions=self.codex([cumulative(1000000,NOW-timedelta(hours=1))])
        self.assertEqual(total(sessions[0].tokens),1000000)
        value=self.check(sessions,0,0,1)
        self.assertEqual(value['excluded']['missing_event_evidence'],1)

    def test_dated_responses_can_be_shown_with_a_cumulative_residual_unallocated(self):
        sessions=self.codex([cumulative(100,OLD),response('new',50,NOW-timedelta(hours=1))])
        self.assertEqual((total(sessions[0].tokens),sessions[0].calls),(150,1))
        self.check(sessions,50,1,1)

    def test_same_selected_response_copies_are_once_and_repeated_session_references_are_once(self):
        rows=[response('same',100,NOW-timedelta(hours=1))]*3
        sessions=self.codex(rows)
        self.assertEqual((total(sessions[0].tokens),sessions[0].calls),(100,1))
        value=self.check(sessions+sessions,100,1)
        self.assertEqual(value['selected_sessions'],1)

    def test_only_the_actual_selected_larger_snapshot_supplies_the_timestamp(self):
        for reader,rows in ((self.codex,[response('same',10,OLD),response('same',100,NOW-timedelta(hours=1))]),
                            (self.claude,[reply('same',10,OLD),reply('same',100,NOW-timedelta(hours=1))])):
            with self.subTest(reader=reader.__name__):
                self.check(reader(rows),100,1)

    def test_timestamp_on_smaller_snapshot_cannot_date_an_undated_selected_snapshot(self):
        for reader,rows in ((self.codex,[response('same',10,NOW),response('same',100,None)]),
                            (self.claude,[reply('same',10,NOW),reply('same',100,None)])):
            with self.subTest(reader=reader.__name__):
                value=self.check(reader(rows),0,0,1)
                self.assertEqual(value['undated_response_calls'],1)

    def test_conflicting_selected_snapshot_times_are_undated_instead_of_choosing_first(self):
        for reader,rows in ((self.codex,[response('same',100,OLD),response('same',100,NOW)]),
                            (self.claude,[reply('same',100,OLD),reply('same',100,NOW)])):
            for order in (rows,list(reversed(rows))):
                with self.subTest(reader=reader.__name__,order=order[0]['timestamp']):
                    value=self.check(reader(order),0,0,1)
                    self.assertEqual(value['undated_response_calls'],1)

    def test_content_block_copies_of_one_response_are_dated_by_their_span(self):
        # Claude Code writes each content block of a response as its own row, seconds apart, with the same usage.
        inside=[reply('same',100,NOW-timedelta(seconds=9)),reply('same',100,NOW-timedelta(seconds=2))]
        self.check(self.claude(inside),100,1)
        before=[reply('same',100,SINCE-timedelta(seconds=9)),reply('same',100,SINCE-timedelta(seconds=2))]
        value=self.check(self.claude(before),0,0)
        self.assertEqual(value['outside_period_calls'],1)
        straddling=[reply('same',100,SINCE-timedelta(seconds=2)),reply('same',100,SINCE+timedelta(seconds=2))]
        self.assertEqual(self.check(self.claude(straddling),0,0,1)['undated_response_calls'],1)

    def test_missing_time_in_one_selected_copy_does_not_inherit_the_other_copy_time(self):
        sessions=self.codex([response('same',100,NOW),response('same',100,None)])
        self.assertEqual(self.check(sessions,0,0,1)['undated_response_calls'],1)

    def test_reconciled_zeroed_claude_copy_cannot_change_the_valid_usage_snapshot_time(self):
        valid=reply('same',100,NOW)
        valid['message']['usage'].update(output_tokens=20,output_tokens_details=dict(thinking_tokens=10))
        zeroed=copy.deepcopy(valid);zeroed['timestamp']=iso(OLD)
        zeroed['message']['usage'].update(input_tokens=0,output_tokens=0,cache_read_input_tokens=0,
                                          cache_creation_input_tokens=0)
        sessions=self.claude([zeroed,valid])
        self.assertIn('reconciled_copies',sessions[0].issues)
        self.assertTrue(sessions[0].tokens_complete)
        self.check(sessions,120,1)

    def test_naive_log_timestamps_are_not_silently_assumed_utc_for_period_usage(self):
        for reader,rows in ((self.codex,[response('one',100,'2026-10-29T11:00:00')]),
                            (self.claude,[reply('one',100,'2026-10-29T11:00:00')])):
            with self.subTest(reader=reader.__name__):
                self.assertEqual(self.check(reader(rows),0,0,1)['undated_response_calls'],1)

    def test_equivalent_aware_offsets_prove_one_instant_and_epoch_times_are_accepted(self):
        sessions=self.codex([response('same',100,'2026-10-29T11:00:00Z'),
                             response('same',100,'2026-10-29T13:00:00+02:00'),
                             response('epoch',50,int(NOW.timestamp()))])
        self.check(sessions,150,2)
        self.assertEqual(event_time(int(NOW.timestamp())*1000),NOW)

    def test_anonymous_usage_is_excluded_without_changing_the_whole_session_total(self):
        for reader,rows in ((self.codex,[response(None,100,NOW)]),
                            (self.claude,[reply(None,100,NOW)])):
            with self.subTest(reader=reader.__name__):
                sessions=reader(rows)
                self.assertEqual(total(sessions[0].tokens),100)
                self.assertEqual(self.check(sessions,0,0,1)['excluded']['incomplete_usage'],1)

    def test_bad_record_makes_the_session_excluded_even_if_one_response_has_a_good_time(self):
        write_jsonl(self.path,[meta(),response('good',100,NOW)])
        with self.path.open('a',encoding='utf-8') as stream:stream.write('{broken\n')
        sessions,issues=codex.read([self.path])
        self.assertEqual(len(issues),1)
        self.assertEqual(self.check(sessions,0,0,1)['excluded']['incomplete_usage'],1)

    def test_missing_parent_and_conflicting_attribution_are_not_placed_in_a_period(self):
        write_jsonl(self.path,[meta(parent='missing'),response('good',100,NOW)])
        sessions,issues=codex.read([self.path])
        self.assertEqual(issues,[])
        self.assertEqual(self.check(sessions,0,0,1)['excluded']['uncertain_history'],1)
        sessions=self.claude([reply('same',100,NOW,session='a'),reply('same',100,NOW,session='b')])
        self.assertEqual(self.check(sessions,0,0,1)['excluded']['unverified_attribution'],1)

    def test_known_parent_child_response_ids_can_be_dated_without_allocating_inherited_counters(self):
        parent=self.root/'rollout-parent.jsonl';child=self.root/'rollout-child.jsonl'
        write_jsonl(parent,[meta('parent'),response('parent-response',100,NOW-timedelta(hours=2))])
        write_jsonl(child,[meta('child',parent='parent'),response('child-response',50,NOW-timedelta(hours=1))])
        sessions,issues=codex.read([parent,child])
        self.assertEqual(issues,[])
        self.assertEqual(sum(total(s.tokens) for s in sessions),150)
        self.check(sessions,150,2)

    def test_other_agent_aggregates_remain_separate_and_share_no_native_identifiers(self):
        codex_rows=self.codex([response('new',40,NOW)])
        claude_rows=self.claude([reply('new',50,NOW)])
        value=self.check(codex_rows+claude_rows,90,2)
        self.assertEqual([(item['agent'],item['total_tokens'],item['response_calls']) for item in value['agents']],
                         [('claude-code',50,1),('codex',40,1)])

    def test_reader_cache_rebuilds_identical_private_events_without_storing_them(self):
        for agent,reader,rows in (('codex',codex.read,[meta(),response('same',100,NOW)]),
                                  ('claude',claude_code.read,[reply('same',100,NOW)])):
            with self.subTest(agent=agent),patch.dict(os.environ,PLER_CACHE_DIR=str(self.root/'cache')):
                write_jsonl(self.path,rows)
                cache=FileCache(agent,'invented-period-key')
                first=reader([self.path],cache=cache)
                first=first[0] if agent=='codex' else first
                cache.save()
                module=codex if agent=='codex' else claude_code
                with patch.object(module,'_rows',side_effect=AssertionError('unchanged source reopened')):
                    cached=reader([self.path],cache=FileCache(agent,'invented-period-key'))
                    cached=cached[0] if agent=='codex' else cached
                self.assertEqual(analyze(first,SINCE,NOW),analyze(cached,SINCE,NOW))
                encoded=(self.root/'cache'/(agent+'.json')).read_text('utf-8')
                self.assertNotIn('_usage_events',encoded)
                self.assertNotIn(TRANSCRIPT,encoded)

    def test_verified_archive_replays_events_but_old_or_unverified_archive_is_excluded(self):
        claude=self.root/'claude';cx=self.root/'codex';claude.mkdir();cx.mkdir()
        log=claude/'invented.jsonl';write_jsonl(log,[reply('one',100,NOW)])
        with patch.dict(os.environ,PLER_CACHE_DIR=str(self.root/'archive-cache')):
            first,_=scan([claude],[cx],retain=True)
            log.unlink()
            archived,_=scan([claude],[cx],retain=True)
        self.assertEqual(analyze(first,SINCE,NOW),analyze(archived,SINCE,NOW))
        self.assertTrue(archived[0].source_deleted)
        for attribute,reason in (('archive_old_parser','archive_old_parser'),('archive_unverified','archive_unverified')):
            value=copy.deepcopy(archived[0]);setattr(value,attribute,True)
            self.assertEqual(self.check([value],0,0,1)['excluded'][reason],1)
        value=copy.deepcopy(archived[0]);value.source_deleted=False
        self.assertEqual(self.check([value],0,0,1)['excluded']['archive_unverified'],1)

    def test_empty_input_and_quota_only_sessions_have_no_invented_usage(self):
        self.check([],0,0)
        self.check([Session('codex','only-quota','invented')],0,0)

    def test_calculation_does_not_query_files_processes_or_clock(self):
        sessions=self.codex([response('one',100,NOW)])
        with patch('builtins.open',side_effect=AssertionError('file access')),\
                patch.object(os,'stat',side_effect=AssertionError('filesystem access')),\
                patch.object(Path,'resolve',side_effect=AssertionError('filesystem resolution')):
            self.check(sessions,100,1)

    def test_invalid_interval_is_rejected_instead_of_broadening_the_selection(self):
        for since,cutoff in ((SINCE,NOW.replace(tzinfo=None)),(SINCE.replace(tzinfo=None),NOW),
                              (NOW+timedelta(seconds=1),NOW)):
            with self.subTest(since=since,cutoff=cutoff),self.assertRaises(ValueError):
                analyze([],since,cutoff)



class SessionAttributionTests(unittest.TestCase):
    """E01: an unknown project alone does not hide a session's own dated responses; shared records still do."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def reply(self,session,message,cwd,at):
        return dict(type='assistant',sessionId=session,requestId='request-'+message,timestamp=iso(at),cwd=cwd,
                    message=dict(id=message,model='claude-opus-5-5',usage=dict(input_tokens=100,output_tokens=10),
                                 content=[dict(type='text',text=TRANSCRIPT)]))

    def test_a_session_in_several_folders_keeps_its_dated_responses_but_shared_records_do_not(self):
        at=NOW-timedelta(days=1)
        write_jsonl(self.root/'a.jsonl',[self.reply('wide','m1','/invented/one',at),self.reply('wide','m2','/invented/two',at)])
        wide,=claude_code.read([self.root/'a.jsonl'])
        self.assertIsNone(wide.project)
        self.assertFalse(wide.attribution_complete)
        result=analyze([wide],SINCE,NOW)
        self.assertEqual((result['total_tokens'],result['response_calls'],result['unallocated_sessions']),(220,2,0))
        # The same response copied into a second session: its owner is a stable anchor, not proven.
        write_jsonl(self.root/'b.jsonl',[self.reply('copy','m1','/invented/one',at),self.reply('copy','m3','/invented/one',at)])
        sessions=claude_code.read([self.root/'a.jsonl',self.root/'b.jsonl'])
        result=analyze(sessions,SINCE,NOW)
        self.assertEqual(result['excluded']['unverified_attribution'],2)
        self.assertNotIn(TRANSCRIPT,json.dumps(result))


if __name__=='__main__':unittest.main()
