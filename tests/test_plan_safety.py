"""Known recorded usage must never turn missing evidence into savings or plan fit."""
from datetime import timedelta
import io
import json
import unittest
from unittest.mock import patch

from pler.dashboard import project_view
from pler.usage import _plan_lines, main, plans
from test_adoption_api import IsolatedMetadata
from test_plans import NOW, dense_meter, meter, row, session, tokens

CLAUDE='claude-code'


def advice(value=None, samples=(), **kwargs):
    return row(plans.advise([value or session(usd=[3])],samples,NOW,'max',**kwargs),CLAUDE)


def no_conclusion(test, result):
    test.assertNotIn('api_below_list_price',result['findings'])
    test.assertNotIn('lower_plan_comparison',result)
    test.assertNotIn('api_cheaper',result['findings'])
    test.assertNotIn('smaller_fits',result['findings'])


class PlanSafetyTests(unittest.TestCase):
    def test_unpriced_usage_cannot_be_treated_as_zero_cost_even_when_rounded_share_is_one(self):
        for prices in ([None],[3,None]):
            result=advice(session(usd=prices))
            no_conclusion(self,result)
            self.assertIn('unpriced_usage',result['limitations'])
        value=session(usd=[3])
        value._usage_events[0]['tokens']['input']=1_000_000
        value.tokens['input']=1_000_000
        at=NOW-timedelta(days=2)
        value._usage_events.append(dict(first=at,at=at,tokens=tokens(1),usd=None))
        value.calls+=1;value.tokens['input']+=1
        result=advice(value)
        self.assertEqual(result['api_priced_share'],1.0)
        no_conclusion(self,result)

    def test_read_failures_or_archive_loss_block_both_kinds_of_comparison(self):
        samples=dense_meter(300,10)+dense_meter(10080,10)
        for sources in ({'skipped':[('PRIVATE-PATH','PermissionError')]},
                        {'archive':{'errors':1}}, {'archive':{'evicted_files':1}}):
            result=advice(samples=samples,sources=sources)
            no_conclusion(self,result)
            self.assertIn('source_incomplete',result['limitations'])
            self.assertNotIn('PRIVATE-PATH',json.dumps(result))

    def test_multi_source_or_changed_plan_is_not_compared_to_one_subscription(self):
        value=session('codex',usd=[3],plan='plus')
        result=row(plans.advise([value],(),NOW,scopes={'codex':2}),'codex')
        no_conclusion(self,result)
        self.assertIn('multiple_source_groups',result['limitations'])
        other=session('codex',usd=[1],plan='pro');other.ended=NOW-timedelta(days=2)
        other.session_id='invented-other';other.source='/invented/other-codex.jsonl'
        result=row(plans.advise([value,other],(),NOW),'codex')
        self.assertIn('plan_changed',result['limitations']);no_conclusion(self,result)

    def test_unknown_project_does_not_drop_known_priced_responses(self):
        value=session(usd=[3],attribution_complete=False)
        result=advice(value)
        self.assertEqual(result['api_usd'],3)
        self.assertIn('api_below_list_price',result['findings'])
        self.assertEqual(result['scope'],'retained_agent_records_all_projects')

    def test_unallocated_residual_and_future_or_reversed_dates_are_incomplete(self):
        value=session(usd=[3]);value.tokens['input']+=500
        result=advice(value)
        self.assertTrue(result['usage_partial']);no_conclusion(self,result)
        for first,at in ((NOW+timedelta(days=1),NOW+timedelta(days=1)),
                         (NOW,NOW-timedelta(hours=1)),(None,NOW)):
            value=session(usd=[3]);value._usage_events[0].update(first=first,at=at)
            result=advice(value)
            self.assertEqual(result['api_usd'],0)
            self.assertTrue(result['usage_partial']);no_conclusion(self,result)

    def test_old_or_unchecked_archives_remain_unverified_despite_dated_events(self):
        for fields in ({'archive_old_parser':True},{'archive_unverified':True},
                       {'calls_complete':False},{'models_complete':False}):
            result=advice(session(usd=[3],**fields))
            self.assertTrue(result['usage_partial']);no_conclusion(self,result)

    def test_two_distant_samples_are_not_fourteen_observed_days(self):
        result=advice(session(usd=[150]),meter(300,[5,10])+meter(10080,[5,10]))
        self.assertIn('meter_sparse',result['limitations'])
        self.assertNotIn('lower_plan_comparison',result)

    def test_dense_but_old_or_elapsed_samples_do_not_support_a_current_comparison(self):
        old=[(at-timedelta(days=2),minutes,used,reset-timedelta(days=2))
             for at,minutes,used,reset in dense_meter(300,10)+dense_meter(10080,10)]
        result=advice(session(usd=[150]),old)
        self.assertIn('meter_stale',result['limitations'])
        self.assertNotIn('lower_plan_comparison',result)
        expired=dense_meter(300,10,now=NOW-timedelta(hours=6))+dense_meter(10080,10)
        self.assertIn('meter_stale',advice(samples=expired)['limitations'])

    def test_gaps_are_not_hidden_by_many_same_day_samples(self):
        samples=dense_meter(300,10)+dense_meter(10080,10)
        samples=[s for s in samples if not NOW-timedelta(days=12)<s[0]<NOW-timedelta(days=8)]
        # Many distinct days remain, but the four-day gap still matters.
        result=advice(session(usd=[150]),samples)
        self.assertIn('meter_sparse',result['limitations'])
        self.assertNotIn('lower_plan_comparison',result)

    def test_conflicting_history_is_not_silently_treated_as_low_pressure(self):
        samples=dense_meter(300,10)+dense_meter(10080,10)
        at,minutes,used,reset=samples[20]
        result=advice(session(usd=[150]),samples+[(at,minutes,11,reset)])
        self.assertTrue(result['meter_ambiguous'])
        self.assertIn('meter_conflicting',result['limitations'])
        self.assertNotIn('lower_plan_comparison',result)
        # Only the contradicted period leaves the counts; the clean periods still count.
        self.assertEqual([(m['samples'],m['periods']) for m in result['meter'] if m['window_minutes']==300],[(20,20)])

    def test_an_old_contradiction_leaves_clean_periods_on_both_sides_counted(self):
        def period(days,used):
            at=NOW-timedelta(days=days)
            return [(at,300,used-5,at+timedelta(hours=4)),(at+timedelta(hours=1),300,used,at+timedelta(hours=4))]
        samples=period(9,100)+period(6,95)+period(3,100)
        at,_,_,reset=samples[2]
        samples.append((at,300,40,reset))  # a different reading at the same instant: that period is uncertain
        result=advice(session(usd=[150]),samples)
        five=[m for m in result['meter'] if m['window_minutes']==300]
        self.assertEqual([(m['samples'],m['periods'],m['full']) for m in five],[(4,2,2)])
        self.assertIn('meter_conflicting',result['limitations'])
        self.assertNotIn('lower_plan_comparison',result)

    def test_bad_reset_or_naive_time_is_explained_and_never_qualifies(self):
        for bad in ((NOW,300,5,NOW-timedelta(hours=1)),(NOW.replace(tzinfo=None),300,5,NOW),
                    (NOW,300,5,NOW+timedelta(days=9)),(NOW,300,5,None),('bad',300,5,NOW)):
            result=advice(session(usd=[150]),dense_meter(300,10)+dense_meter(10080,10)+[bad])
            self.assertIn('meter_incomplete',result['limitations'])
            self.assertNotIn('lower_plan_comparison',result)

    def test_valid_dense_comparison_is_conditional_and_expires_with_the_short_meter(self):
        result=advice(session(usd=[150]),dense_meter(300,10)+dense_meter(10080,10))
        lower=result['lower_plan_comparison']
        self.assertTrue(lower['observed_only'])
        self.assertEqual(lower['assumed_plan'],'max')
        self.assertEqual(lower['expires_at'],(NOW+timedelta(minutes=30)).isoformat())
        self.assertIsNone(result['actual_payment_usd'])
        self.assertFalse(result['history_complete'])
        self.assertEqual(result['since'],(NOW-timedelta(days=30)).isoformat())

    def test_terminal_preserves_unknown_prices_and_distinguishes_agents(self):
        for lang in ('en','tr'):
            lines='\n'.join(_plan_lines([advice(session(usd=[None]))],lang))
            self.assertNotIn('$0.00',lines)
            self.assertNotIn('$0,00',lines)
            value=row(plans.advise([session('codex',usd=[3],plan='plus')],(),NOW),'codex')
            lines='\n'.join(_plan_lines([value],lang))
            self.assertIn('Codex',lines)
            self.assertNotIn('statusline',lines)


class PlanProjectionSafetyTests(IsolatedMetadata):
    def test_page_filters_do_not_hide_source_failures_from_the_plan_check(self):
        value=session(usd=[3])
        result=project_view([value],dict(skipped=[('PRIVATE','PermissionError')],claude_plan='max'),
                            days=7,agent='codex',now=NOW)
        self.assertEqual(result['totals']['sessions'],0)
        no_conclusion(self,result['plans']['rows'][0])
        self.assertIn('source_incomplete',result['plans']['rows'][0]['limitations'])

    def test_terminal_json_receives_the_same_source_limit(self):
        value=session(usd=[3])
        sources=dict(claude_files=1,codex_files=0,claude_quota=[],skipped=[('PRIVATE','PermissionError')],claude_plan='max')
        plans.Choice().save('max')
        output=io.StringIO()
        with patch('pler.usage.scan',return_value=([value],sources)),patch('sys.stdout',output):
            main(['--json','--lang','en','--days','0'])
        result=json.loads(output.getvalue())['plans']['rows'][0]
        no_conclusion(self,result)
        self.assertIn('source_incomplete',result['limitations'])


if __name__=='__main__': unittest.main()
