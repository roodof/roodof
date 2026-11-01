"""Reviewed compatibility is a release guard, not a live account or price lookup."""
import copy
from datetime import date
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import pler
from pler.dashboard import project_view
from pler.usage import scan,claude_code,codex,pricing,plans
from pler.usage.records import total

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pler_compatibility_gate',ROOT/'tools/check_compatibility.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
REVIEW=date(2026,11,1)


class CompatibilityGateTests(unittest.TestCase):
    def setUp(self):self.data=gate.read_registry()

    def test_reviewed_package_and_price_facts_pass_without_source_or_network_reads(self):
        with patch.object(codex,'files',side_effect=AssertionError('user roots discovered')),patch.object(claude_code,'files',side_effect=AssertionError('user roots discovered')):
            result=gate.check(self.data,as_of=REVIEW)
        self.assertTrue(result['ok'],result);self.assertEqual(result['model_count'],26);self.assertEqual(result['network_requests'],0)

    def test_price_changes_new_models_and_plan_changes_require_review(self):
        changed=copy.deepcopy(pricing.PRICES);changed['codex']['gpt-6.1-sol'][0][1]['input']=999
        with patch.object(pricing,'PRICES',changed):self.assertIn('api_rate_review_required',gate.check(self.data,as_of=REVIEW)['errors'])
        changed['codex']['unreviewed-model']=copy.deepcopy(changed['codex']['gpt-6.1-sol'])
        with patch.object(pricing,'PRICES',changed):self.assertIn('model_coverage_review_required',gate.check(self.data,as_of=REVIEW)['errors'])
        changed=copy.deepcopy(plans.PLANS);changed['claude-code']['max']['usd']=99
        with patch.object(plans,'PLANS',changed):self.assertIn('plan_rate_review_required',gate.check(self.data,as_of=REVIEW)['errors'])

    def test_nonfinite_boolean_or_negative_prices_cannot_be_approved(self):
        for value in (float('nan'),float('inf'),True,-1):
            changed=copy.deepcopy(pricing.PRICES);changed['codex']['gpt-6.1-sol'][0][1]['input']=value
            with self.subTest(value=value),patch.object(pricing,'PRICES',changed):self.assertFalse(gate.check(self.data,as_of=REVIEW)['ok'])

    def test_expired_future_and_untrusted_reviews_block_the_release(self):
        self.assertIn('price_review_expired',gate.check(self.data,as_of=date(2026,12,2))['errors'])
        self.assertIn('price_review_expired',gate.check(self.data,as_of=date(2026,10,31))['errors'])
        changed=copy.deepcopy(self.data);changed['price_review']['sources'].append('https://untrusted.invalid/prices')
        self.assertIn('untrusted_price_source',gate.check(changed,as_of=REVIEW)['errors'])
        changed=copy.deepcopy(self.data);changed['price_review']['sources'].append('https://name:secret@developers.openai.com/prices')
        self.assertIn('untrusted_price_source',gate.check(changed,as_of=REVIEW)['errors'])

    def test_unreviewed_reader_code_and_fixture_changes_cannot_pass_a_same_version(self):
        with tempfile.TemporaryDirectory() as folder:
            package=Path(folder)/'package'
            for name in gate.CORE:
                target=package/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(Path(pler.__file__).parent/name,target)
            before=gate.code_digest(package);path=package/'usage/accounting.py'
            source=path.read_text(encoding='utf-8');path.write_text(source+'\n# A comment does not change interpretation.\n',encoding='utf-8')
            self.assertEqual(gate.code_digest(package),before)
            path.write_text(source+'\n_UNREVIEWED_INTERPRETATION = 1\n',encoding='utf-8')
            self.assertIn('reader_code_review_required',gate.check(self.data,as_of=REVIEW,package=package)['errors'])
            path.write_text(source,encoding='utf-8')
            # Unchanged tables do not excuse changes to how amounts are interpreted.
            path=package/'usage/pricing.py'
            source=path.read_text(encoding='utf-8')
            path.write_text(source+'\nresponse_cost = lambda *args: 0\n',encoding='utf-8')
            self.assertIn('reader_code_review_required',gate.check(self.data,as_of=REVIEW,package=package)['errors'])
        changed=copy.deepcopy(self.data);changed['record_cases_sha256']='0'*64
        self.assertIn('record_fixture_review_required',gate.check(changed,as_of=REVIEW)['errors'])
        changed=copy.deepcopy(self.data);changed['regressions'][0]='test_accounting.AccountingTests.test_missing_example'
        self.assertIn('missing_named_regression',gate.check(changed,as_of=REVIEW)['errors'])

    def test_duplicate_and_nonfinite_registry_json_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'review.json'
            for raw in ('{"format":1,"format":1}','{"format":NaN}'):
                path.write_text(raw,encoding='utf-8')
                with self.assertRaises(ValueError):gate.read_registry(path)


class CompatibilityRecordTests(unittest.TestCase):
    def test_independent_cases_match_cold_warm_and_verified_archive_with_private_text_removed(self):
        data=json.loads((ROOT/'tests/fixtures/compatibility/cases.json').read_text(encoding='utf-8'))
        for case in data['cases']:
            with self.subTest(case=case['id']),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);cc=root/'claude/projects';cx=root/'codex/sessions';cc.mkdir(parents=True);cx.mkdir(parents=True)
                cache=root/'cache';path=(cc if case['agent']=='claude-code' else cx)/('invented.jsonl' if case['agent']=='claude-code' else 'rollout-invented.jsonl')
                path.write_text(''.join(json.dumps(row)+'\n' for row in case['rows']),encoding='utf-8')
                expected=case['expected']
                with patch.dict(os.environ,PLER_CACHE_DIR=str(cache),CLAUDE_CONFIG_DIR=str(cc.parent),CODEX_HOME=str(cx.parent)):
                    for phase in ('cold','warm','verified_archive'):
                        if phase=='verified_archive':path.unlink()
                        sessions,sources=scan();self.assertEqual(len(sessions),1,(case['id'],phase))
                        s=sessions[0]
                        self.assertEqual((total(s.tokens),s.calls,s.tokens_complete,s.calls_complete),
                                         tuple(expected[k] for k in ('total_tokens','calls','tokens_complete','calls_complete')),(case['id'],phase))
                        self.assertAlmostEqual(s.api_usd,expected['api_usd'],places=12,msg=(case['id'],phase))
                        self.assertEqual(s.api_priced_tokens,expected['api_priced_tokens'],(case['id'],phase))
                        self.assertEqual(any(reason=='MalformedRows' for _,reason in sources['skipped']),expected['malformed'])
                        view=project_view(sessions,sources,days=0)
                        if expected['malformed']:self.assertFalse(view['quality']['tokens_complete'])
                        if expected['total_tokens'] and not expected['api_priced_tokens']:self.assertEqual(view['totals']['api_priced_share'],0)
                        self.assertNotIn(data['canary'],json.dumps(view))
                        if phase=='verified_archive':self.assertTrue(s.source_deleted);self.assertFalse(s.archive_old_parser)
                    for artifact in cache.iterdir():
                        if artifact.is_file():
                            saved=artifact.read_bytes()
                            for text in (data['canary'],'private/path','invalid word!'):self.assertNotIn(text.encode(),saved)


if __name__=='__main__':unittest.main()
