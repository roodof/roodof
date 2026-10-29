"""Independent expected totals for the professional audit's counterexamples. Invented logs only."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler import __version__
from pler.dashboard import project_view
from pler.reporting import PARSER_VERSION,SCHEMA_VERSION
from pler.usage import claude_code,codex,main,scan
from pler.usage import discovery
from pler.usage.insights import insights
from pler.usage.records import Session,total,timestamp
from test_logs import USAGE,claude_reply,stored_zstd,write_jsonl


def row(kind,payload,at='2026-10-27T10:00:00Z'):
    return dict(type=kind,payload=payload,timestamp=at)


def numbers(value,**kwargs):
    return dict(input_tokens=value,output_tokens=0,**kwargs)


def meta(identity='s',project='/work/shop'):
    return row('session_meta',dict(id=identity,cwd=project))


def response(value,identity='r',at='2026-10-27T10:00:00Z'):
    return row('token_usage_record',dict(response_id=identity,usage=numbers(value)),at)


def cumulative(value,at='2026-10-27T10:00:00Z'):
    return row('event_msg',dict(type='token_count',info=dict(total_token_usage=numbers(value))),at)


class AccountingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.a,self.b=self.root/'rollout-a.jsonl',self.root/'rollout-b.jsonl'

    def read(self,rows):
        write_jsonl(self.a,[meta()]+rows)
        return codex.read([self.a])

    def test_same_logical_legacy_session_in_plain_and_compressed_copies_is_counted_once(self):
        rows=[meta(),cumulative(100)]
        write_jsonl(self.a,rows)
        compressed=self.b.with_suffix('.jsonl.zst')
        compressed.write_bytes(stored_zstd(''.join(json.dumps(r)+'\n' for r in rows).encode()))
        sessions,issues=codex.read([self.a,compressed])
        self.assertEqual((len(sessions),total(sessions[0].tokens),issues),(1,100,[]))
        self.assertFalse(sessions[0].calls_complete)

    def test_mixed_cumulative_and_response_records_reconcile_without_losing_legacy_usage(self):
        sessions,issues=self.read([cumulative(100),response(50),cumulative(150)])
        session,=sessions
        self.assertEqual((total(session.tokens),session.calls,issues),(150,1,[]))
        self.assertEqual(session.model_tokens,{'unknown':150})
        self.assertFalse(session.calls_complete)
        self.assertTrue(session.tokens_complete)

    def test_per_call_after_checkpoint_is_added_and_copies_of_the_response_are_not(self):
        sessions,_=self.read([cumulative(100,'2026-10-27T09:00:00Z'),response(50),response(50)])
        self.assertEqual((total(sessions[0].tokens),sessions[0].calls),(150,1))

    def test_largest_actual_response_snapshot_is_kept_independent_of_order(self):
        for values in ([100,150],[150,100]):
            with self.subTest(values=values):
                sessions,issues=self.read([response(value) for value in values])
                self.assertEqual((total(sessions[0].tokens),sessions[0].calls,issues),(150,1,[]))

    def test_crossing_snapshots_are_excluded_with_an_explicit_quality_warning(self):
        a=response(100);b=response(50);b['payload']['usage']['output_tokens']=100
        sessions,_=self.read([a,b])
        data=project_view(sessions,{},days=0)
        self.assertEqual(data['totals']['total_tokens'],0)
        self.assertFalse(data['quality']['tokens_complete'])
        self.assertIn('conflicting_usage',[x['code'] for x in data['quality']['issues']])

    def test_shared_codex_history_deduplicates_turns_tools_errors_and_work_time(self):
        common=[row('event_msg',dict(type='task_started',turn_id='turn')),
                row('response_item',dict(type='function_call',name='exec',call_id='tool')),
                row('event_msg',dict(type='task_complete',turn_id='turn',duration_ms=250,error=True)),
                row('event_msg',dict(type='turn_aborted',turn_id='turn')),response(100)]
        write_jsonl(self.a,[meta('a','/work/first')]+common)
        write_jsonl(self.b,[meta('b','/work/second')]+common)
        sessions,_=codex.read([self.a,self.b])
        self.assertEqual((sum(s.prompts for s in sessions),sum(sum(s.tools.values()) for s in sessions),
                          sum(s.errors for s in sessions),sum(s.aborted for s in sessions),
                          sum(s.active_ms or 0 for s in sessions)),(1,1,1,1,250))
        self.assertEqual(sum(total(s.tokens) for s in sessions),100)
        self.assertIsNone(sessions[0].project)
        self.assertFalse(project_view(sessions,{},days=0)['quality']['attribution_complete'])

    def test_project_attribution_is_independent_of_file_names_and_argument_order(self):
        a,b=[meta('a','/work/first'),response(100)],[meta('b','/work/second'),response(100)]
        results=[]
        for left,right,paths in ((a,b,[self.a,self.b]),(a,b,[self.b,self.a]),(b,a,[self.a,self.b])):
            write_jsonl(self.a,left);write_jsonl(self.b,right)
            sessions,_=codex.read(paths)
            results.append([(s.session_id,s.project,total(s.tokens),s.attribution_complete) for s in sessions])
        self.assertEqual(results[0],results[1]);self.assertEqual(results[0],results[2])

    def test_legacy_multi_model_totals_remain_unknown_instead_of_using_the_last_model(self):
        sessions,_=self.read([row('turn_context',dict(model='A')),cumulative(100),
                              row('turn_context',dict(model='B')),cumulative(150)])
        self.assertEqual(sessions[0].model_tokens,{'unknown':150})
        self.assertFalse(sessions[0].models_complete)

    def test_invalid_numeric_values_do_not_become_zero_calls(self):
        for invalid in (-1,'100',True,1.5,1<<54):
            with self.subTest(invalid=invalid):
                bad=response(100);bad['payload']['usage']['input_tokens']=invalid
                sessions,issues=self.read([bad])
                self.assertEqual((sessions[0].calls,total(sessions[0].tokens),len(issues)),(0,0,1))
                self.assertFalse(project_view(sessions,{},days=0)['quality']['tokens_complete'])

    def test_inconsistent_cache_and_reasoning_numbers_are_rejected(self):
        for usage in (numbers(10,cached_input_tokens=11),numbers(10,reasoning_output_tokens=1),
                      dict(output_tokens=10)):
            with self.subTest(usage=usage):
                bad=response(0);bad['payload']['usage']=usage
                sessions,issues=self.read([bad])
                self.assertEqual((sessions[0].calls,len(issues)),(0,1))

    def test_non_string_event_id_is_reported_without_crashing(self):
        sessions,issues=self.read([response(100),row('event_msg',dict(type='task_started',turn_id=[]))])
        self.assertEqual((total(sessions[0].tokens),len(issues)),(100,1))

    def test_decreasing_cumulative_or_compaction_boundaries_are_not_claimed_complete(self):
        for rows in ([cumulative(100),cumulative(10)],
                     [cumulative(100),response(50),row('compacted',dict(compaction_response_id='r')),cumulative(100)]):
            with self.subTest(rows=rows):
                sessions,_=self.read(rows)
                self.assertFalse(sessions[0].tokens_complete)
                self.assertIn('unreconciled_totals',sessions[0].issues)

    def test_ambiguous_checkpoint_coverage_is_reported_without_inventing_a_sum(self):
        write_jsonl(self.a,[meta(),cumulative(100)])
        write_jsonl(self.b,[meta(),response(50)]) # equal timestamps, no source ordering evidence
        sessions,_=codex.read([self.a,self.b])
        self.assertEqual(total(sessions[0].tokens),50)
        self.assertFalse(sessions[0].tokens_complete)

    def test_response_updated_after_checkpoint_does_not_fabricate_the_legacy_residual(self):
        sessions,_=self.read([cumulative(100),response(50),cumulative(150),response(100)])
        self.assertEqual(total(sessions[0].tokens),100)
        self.assertFalse(sessions[0].tokens_complete)

    def test_anonymous_response_usage_cannot_claim_verified_deduplication(self):
        anonymous=response(100);anonymous['payload'].pop('response_id')
        sessions,_=self.read([anonymous])
        self.assertEqual(total(sessions[0].tokens),100)
        self.assertFalse(sessions[0].tokens_complete)
        self.assertFalse(sessions[0].calls_complete)

    def test_claude_updated_copies_and_shared_projects_are_also_deterministic(self):
        original=claude_reply('b','m','r',dict(input_tokens=100,output_tokens=0),[], '2026-10-27T10:00:00Z')
        updated=copy.deepcopy(original);updated.update(sessionId='a',cwd='/work/second')
        updated['message']['usage']['input_tokens']=150
        results=[]
        for left,right in ((original,updated),(updated,original)):
            write_jsonl(self.a,[left]);write_jsonl(self.b,[right])
            sessions=claude_code.read([self.a,self.b])
            results.append([(s.session_id,s.project,total(s.tokens)) for s in sessions])
        self.assertEqual(results,[[('a',None,150)],[('a',None,150)]])

    def test_claude_invalid_usage_keeps_a_file_warning(self):
        bad=claude_reply('s','m','r',dict(input_tokens=-1,output_tokens=0),[],'2026-10-27T10:00:00Z')
        write_jsonl(self.a,[bad]);issues=[]
        self.assertEqual(claude_code.read([self.a],issues),[])
        self.assertEqual(len(issues),1)
        self.assertFalse(project_view([],dict(skipped=issues),days=0)['quality']['tokens_complete'])

    def test_cache_and_original_reads_keep_the_same_corrected_totals_and_quality(self):
        log=self.root/'codex/sessions/rollout-example.jsonl'
        write_jsonl(log,[meta(),cumulative(100),response(50),cumulative(150)])
        with patch.dict(os.environ,CODEX_HOME=str(self.root/'codex'),CLAUDE_CONFIG_DIR=str(self.root/'missing'),
                        PLER_CACHE_DIR=str(self.root/'cache')):
            first,sources=scan()
            with patch.object(codex,'_rows',side_effect=AssertionError('reopened unchanged log')):
                cached,again=scan()
        self.assertEqual([s.as_dict() for s in first],[s.as_dict() for s in cached])
        self.assertIsNotNone(timestamp(sources.pop('observed_at')))
        self.assertIsNotNone(timestamp(again.pop('observed_at')))
        self.assertEqual(sources,again)
        self.assertEqual(total(cached[0].tokens),150)

    def test_public_report_provenance_matches_cli_and_totals_conserve_unknown_buckets(self):
        sessions,_=self.read([cumulative(100),response(50),cumulative(150)])
        data=project_view(sessions,{},days=0)
        self.assertEqual(data['totals']['total_tokens'],sum(p['total_tokens'] for p in data['projects']))
        self.assertEqual(data['totals']['total_tokens'],sum(m['total_tokens'] for m in data['models']))
        shown=io.StringIO()
        with patch('pler.usage.scan',return_value=(sessions,dict(claude_files=0,codex_files=1,skipped=[],claude_quota=[]))),contextlib.redirect_stdout(shown):
            main(['--days','0','--json','--sessions','--lang','en'])
        cli=json.loads(shown.getvalue())
        for value in (data,cli):
            self.assertEqual((value['version'],value['parser_version'],value['schema_version']),(__version__,PARSER_VERSION,SCHEMA_VERSION))
        self.assertEqual(cli['quality'],data['quality'])

    def test_incomplete_usage_does_not_generate_concentration_or_session_comparisons(self):
        sessions=[Session('codex',str(i),'synthetic',calls=10,prompts=1,tokens=dict(input=1000 if i==0 else 1,cache_read=0,cache_write=0,output=0,reasoning=0)) for i in range(3)]
        sessions[0].tokens_complete=False;sessions[0].issues.add('unreconciled_totals')
        data=project_view(sessions,{},days=0)
        self.assertNotIn('concentration',[n['kind'] for n in data['insights']])

    def test_errors_and_aborts_are_events_and_never_a_percentage_of_unique_requests(self):
        session=Session('codex','s','synthetic',prompts=1,errors=2,aborted=1)
        for lang in ('en','tr'):
            item=next(n for n in insights([session],[],lang=lang) if n['kind']=='interrupted')
            self.assertNotIn('%',item['detail']);self.assertNotIn('share',item['evidence'])
            self.assertEqual(item['evidence']['prompts'],1)


class DiscoveryTests(unittest.TestCase):
    def test_configured_network_roots_are_rejected_before_filesystem_access(self):
        with patch.object(Path,'lstat',side_effect=AssertionError('network probe')),patch.object(Path,'is_dir',side_effect=AssertionError('network probe')):
            with patch.dict(os.environ,CODEX_HOME=r'\\server\logs',CLAUDE_CONFIG_DIR='//server/claude'):
                issues=[]
                self.assertEqual(codex.files(skipped=issues),[])
                self.assertEqual(claude_code.files(skipped=issues),[])
                self.assertEqual(len(issues),2)
                self.assertTrue(all(reason=='UnsafePath' for _,reason in issues))

    def test_junction_and_symlink_entries_are_not_followed(self):
        class Entry:
            path='invented-link';name='invented-link'
            def stat(self,follow_symlinks):
                self.follow=follow_symlinks
                return type('Info',(),dict(st_mode=0o040755,st_file_attributes=0x400))()
        entry=Entry()
        with tempfile.TemporaryDirectory() as folder:
            with patch('pler.usage.discovery.os.scandir') as scan_dir:
                scan_dir.return_value.__enter__.return_value=iter([entry])
                issues=[]
                self.assertEqual(discovery.files([folder],lambda _:True,issues),[])
                self.assertFalse(entry.follow)
                self.assertEqual(scan_dir.call_count,1)
                self.assertEqual(issues,[('invented-link','UnsafePath')])


if __name__=='__main__':unittest.main()
