"""Contributing source roots are local namespaces, never provider account IDs."""
from datetime import datetime,timedelta,timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler.dashboard import project_view
from pler.usage import scan
from pler.usage.discovery import Manifest
from pler.usage.forecast import outlook
from pler.usage.quota_scope import _namespace,source_groups
from pler.usage.records import Session
from test_archive import codex_rows
from test_logs import write_jsonl

NOW=datetime(2026,10,29,12,tzinfo=timezone.utc)


class QuotaSourceScopes(unittest.TestCase):
    def test_standard_active_and_archived_folders_share_one_local_namespace(self):
        for home in ('/invented/one','C:/Invented/One'):
            self.assertEqual(_namespace('codex',home+'/sessions'),_namespace('codex',home+'/archived_sessions'))
        self.assertEqual(_namespace('claude-code','C:/Invented/One/projects'),'c:/invented/one')
        self.assertNotEqual(_namespace('codex','/invented/a/sessions'),_namespace('codex','/invented/b/sessions'))

    def test_wsl_host_aliases_preserve_linux_path_case(self):
        a=_namespace('codex',r'\\wsl$\Ubuntu\home\A\sessions')
        b=_namespace('codex',r'\\wsl.localhost\ubuntu\home\A\archived_sessions')
        self.assertEqual(a,b)
        self.assertNotEqual(a,_namespace('codex',r'\\wsl$\Ubuntu\home\a\sessions'))

    def test_only_contributing_roots_count_without_filesystem_queries(self):
        a,b=Manifest(),Manifest()
        a.select('/invented/personal/projects');a.select('/invented/empty/projects')
        b.select('/invented/work/sessions');b.select('/invented/work/archived_sessions')
        with patch.object(Path,'stat',side_effect=AssertionError('source namespace queried filesystem')):
            found=source_groups(a,b,['/invented/personal/projects/a.jsonl'],
                                ['/invented/work/sessions/a.jsonl','/invented/work/archived_sessions/b.jsonl'])
        self.assertEqual(found,{'claude-code':1,'codex':1})
        self.assertNotIn('invented',json.dumps(found))

    def test_compatible_histories_from_two_source_groups_do_not_imply_one_meter(self):
        start,reset=NOW-timedelta(minutes=30),NOW+timedelta(hours=3)
        session=Session('codex','invented','invented',quota=[(start,300,10,reset),(NOW,300,30,reset)])
        ordinary=outlook([session],NOW,scopes={'codex':1})[0]
        self.assertEqual(ordinary['state'],'fills_before_reset')
        self.assertEqual(ordinary['percent_per_hour'],40)
        blocked=outlook([session],NOW,scopes={'codex':2})[0]
        self.assertEqual(blocked['reason'],'multiple_source_groups')
        self.assertIsNone(blocked['used_percent']);self.assertIsNone(blocked['resets_at'])
        self.assertNotIn('full_at',blocked);self.assertNotIn('percent_per_hour',blocked)
        data=project_view([session],{'quota_source_groups':{'codex':2}},days=0,now=NOW)
        self.assertEqual(data['outlook'][0]['state'],'ambiguous')
        self.assertIsNone(data['quota']['latest'][0]['used_percent'])
        self.assertEqual(data['quota']['latest'][0]['reason'],'multiple_source_groups')

    def test_legacy_samples_without_reset_dates_do_not_bypass_source_scope_guard(self):
        session=Session('codex','invented','invented',quota=[(NOW,300,50,None)])
        data=project_view([session],{'quota_source_groups':{'codex':2}},days=0,now=NOW)
        self.assertEqual(data['outlook'],[])
        self.assertEqual(data['quota']['latest'][0]['state'],'ambiguous')
        self.assertIsNone(data['quota']['latest'][0]['used_percent'])

    def test_a_deleted_but_retained_root_still_counts_in_the_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);a=root/'personal/sessions';b=root/'work/sessions';claude=root/'empty'
            a.mkdir(parents=True);b.mkdir(parents=True);claude.mkdir()
            first=a/'rollout-a.jsonl';second=b/'rollout-b.jsonl'
            write_jsonl(first,codex_rows('a',response='a'));write_jsonl(second,codex_rows('b',response='b'))
            with patch.dict(os.environ,PLER_CACHE_DIR=str(root/'cache')):
                _,before=scan([claude],[a,b],retain=True)
                second.unlink()
                _,after=scan([claude],[a,b],retain=True)
            self.assertEqual(before['quota_source_groups']['codex'],2)
            self.assertEqual(after['quota_source_groups']['codex'],2)
