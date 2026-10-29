"""Comparable cohorts describe recorded use without mixing projects or models.

Synthetic in-memory metadata only. No private log, provider or filesystem read.
"""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from pler.usage.insights import _long_sessions
from pler.usage.records import Session

PRIVATE='PRIVATE-PROJECT-AND-NATIVE-ID'


def session(index,calls,per_call,project='/invented/'+PRIVATE,model='invented-model',agent='codex'):
    return Session(agent,PRIVATE+str(index),'/invented/'+PRIVATE+'/source',project=project,calls=calls,
                   tokens=dict(input=calls*per_call,cache_read=0,cache_write=0,output=0,reasoning=0),
                   models={model:calls},model_tokens={model:calls*per_call})


def cohort(project='/invented/'+PRIVATE,model='invented-model',agent='codex',ratio=4):
    return ([session(i,calls,100,project,model,agent) for i,calls in enumerate((5,20,49))]
            +[session(i+3,calls,100*ratio,project,model,agent) for i,calls in enumerate((100,150,200))])


class ComparableInsightTests(unittest.TestCase):
    def test_same_agent_project_and_model_supplies_three_sessions_per_side_and_safe_evidence(self):
        rows=cohort()
        before=[row.as_dict() for row in rows]
        note,=_long_sessions(rows,'en')
        self.assertEqual(note['level'],'info')
        self.assertEqual(note['evidence'],dict(agent='codex',model='invented-model',same_project=True,
            median_tokens_per_call_short=100,median_tokens_per_call_long=400,
            short_sessions=3,long_sessions=3,ratio=4.0))
        self.assertNotIn(PRIVATE,json.dumps(note))
        self.assertEqual([row.as_dict() for row in rows],before)

    def test_one_or_two_long_sessions_are_not_enough(self):
        for size in (4,5):
            self.assertEqual(_long_sessions(cohort()[:size],'en'),[])

    def test_fewer_than_three_short_sessions_are_not_enough(self):
        self.assertEqual(_long_sessions(cohort()[1:],'en'),[])

    def test_different_models_do_not_create_a_cross_model_ratio(self):
        rows=cohort()
        for row in rows[3:]:
            row.models={'another-model':row.calls};row.model_tokens={'another-model':sum(row.tokens.values())}
        self.assertEqual(_long_sessions(rows,'en'),[])

    def test_different_projects_do_not_create_a_cross_project_ratio(self):
        rows=cohort()
        for row in rows[3:]:row.project='/another/project'
        self.assertEqual(_long_sessions(rows,'en'),[])

    def test_different_agents_do_not_create_a_cross_agent_ratio(self):
        rows=cohort()
        for row in rows[3:]:row.agent='claude-code'
        self.assertEqual(_long_sessions(rows,'en'),[])

    def test_all_four_completeness_requirements_apply_to_each_session(self):
        for field in ('tokens_complete','calls_complete','attribution_complete','models_complete'):
            with self.subTest(field=field):
                rows=cohort();setattr(rows[-1],field,False)
                self.assertEqual(_long_sessions(rows,'en'),[])

    def test_unknown_project_does_not_supply_a_comparable_cohort(self):
        for project in (None,'',' ','unknown'):
            with self.subTest(project=project):
                self.assertEqual(_long_sessions(cohort(project=project),'en'),[])

    def test_unknown_missing_or_multiple_models_do_not_supply_a_comparable_cohort(self):
        for model in ('unknown','<synthetic>',' '):
            with self.subTest(model=model):
                self.assertEqual(_long_sessions(cohort(model=model),'en'),[])
        rows=cohort()
        for row in rows:row.models={};row.model_tokens={}
        self.assertEqual(_long_sessions(rows,'en'),[])
        rows=cohort()
        for row in rows:row.model_tokens['another-model']=1
        self.assertEqual(_long_sessions(rows,'en'),[])

    def test_middle_length_and_very_short_sessions_cannot_fill_the_cohort_minimum(self):
        rows=cohort()
        rows[0].calls=4
        rows.extend(session(20+i,calls,100) for i,calls in enumerate((50,75,99)))
        self.assertEqual(_long_sessions(rows,'en'),[])

    def test_ratio_two_is_inclusive_but_smaller_ratios_are_not_an_observation(self):
        self.assertEqual(_long_sessions(cohort(ratio=2),'en')[0]['evidence']['ratio'],2.0)
        self.assertEqual(_long_sessions(cohort(ratio=1),'en'),[])

    def test_zero_short_baseline_is_not_a_division_or_a_claim(self):
        rows=cohort()
        for row in rows[:3]:row.tokens={name:0 for name in row.tokens}
        self.assertEqual(_long_sessions(rows,'en'),[])

    def test_strongest_cohort_is_deterministic_without_disclosing_project_identity(self):
        rows=cohort(project='/first/'+PRIVATE,model='model-a')+cohort(project='/second/'+PRIVATE,model='model-b',ratio=6)
        before=_long_sessions(rows,'en')
        self.assertEqual(before[0]['evidence']['model'],'model-b')
        self.assertEqual(before,_long_sessions(list(reversed(rows)),'en'))
        self.assertNotIn(PRIVATE,json.dumps(before))

    def test_calculation_reads_no_files_or_processes(self):
        with patch('builtins.open',side_effect=AssertionError('file read')), \
                patch.object(Path,'stat',side_effect=AssertionError('stat')), \
                patch('subprocess.run',side_effect=AssertionError('process')):
            self.assertEqual(_long_sessions(cohort(),'en')[0]['evidence']['ratio'],4.0)


if __name__=='__main__':unittest.main()
