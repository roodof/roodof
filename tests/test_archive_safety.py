"""Conservative archive boundaries, using invented records and isolated cache folders only."""
import builtins
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler.usage import archive,claude_code,codex,scan
from pler.usage.records import total
from test_archive import claude_rows,codex_rows
from test_logs import write_jsonl


class ArchiveSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.claude=self.root/'claude/projects'
        self.codex=self.root/'codex/sessions'
        self.claude.mkdir(parents=True)
        self.codex.mkdir(parents=True)
        (self.codex.parent/'archived_sessions').mkdir()
        self.cache=self.root/'cache'
        env=patch.dict(os.environ,CLAUDE_CONFIG_DIR=str(self.claude.parent),CODEX_HOME=str(self.codex.parent),
                       PLER_CACHE_DIR=str(self.cache))
        env.start();self.addCleanup(env.stop)

    def read(self):
        return scan([self.claude],[self.codex],retain=True)

    def test_anonymous_claude_copied_usage_prompts_and_tools_are_withheld_with_warning(self):
        rows=claude_rows(message=None,request=None)
        rows[0]['message']['content']=[dict(type='tool_use',name='Bash',input=dict(command='NEVER-STORE'))]
        rows.append(dict(type='user',sessionId='claude',timestamp='2026-10-28T10:00:00Z',message=dict(content='NEVER-STORE')))
        source=self.claude/'old.jsonl'
        write_jsonl(source,rows)
        self.read()
        source.unlink()
        write_jsonl(self.claude/'resume.jsonl',rows)
        sessions,details=self.read()
        self.assertEqual((len(sessions),total(sessions[0].tokens),sessions[0].calls,sessions[0].prompts),(1,120,1,1))
        self.assertEqual(sessions[0].tools,{'Bash':1})
        self.assertTrue(sessions[0].archive_unverified)
        self.assertFalse(sessions[0].tokens_complete)
        self.assertEqual(details['archive']['unverified_files'],1)

    def test_anonymous_codex_copied_usage_does_not_add_a_second_path_identity(self):
        rows=codex_rows(response=None)
        source=self.codex/'rollout-old.jsonl'
        write_jsonl(source,rows)
        self.read()
        source.unlink()
        write_jsonl(self.codex/'rollout-resume.jsonl',rows)
        sessions,details=self.read()
        self.assertEqual((len(sessions),total(sessions[0].tokens),sessions[0].calls),(1,230,1))
        self.assertEqual(sessions[0].source_state,'mixed')
        self.assertTrue(sessions[0].archive_unverified)
        self.assertEqual(details['archive']['unverified_files'],1)

    def test_present_but_unreadable_source_uses_prior_metadata_without_deleted_claim(self):
        source=self.codex/'rollout-source.jsonl'
        write_jsonl(source,codex_rows())
        self.read()
        with patch.object(codex,'_rows',side_effect=PermissionError('PRIVATE-ERROR')):
            sessions,details=self.read()
        self.assertEqual(total(sessions[0].tokens),230)
        self.assertTrue(sessions[0].archive_unverified)
        self.assertFalse(sessions[0].source_deleted)
        self.assertIn('PermissionError',[reason for _,reason in details['skipped']])

    def test_clear_does_not_upgrade_deleted_sources_from_disposable_cache(self):
        source=self.codex/'rollout-source.jsonl'
        write_jsonl(source,codex_rows())
        scan()
        self.assertTrue((self.cache/'codex.json').is_file())
        source.unlink()
        archive.clear_archive()
        sessions,details=scan()
        self.assertEqual(sessions,[])
        self.assertEqual(details['archive']['stored_files'],0)

    def test_only_default_agent_persists_when_the_other_agent_has_explicit_transient_roots(self):
        a=self.claude/'transient.jsonl'
        b=self.codex/'rollout-source.jsonl'
        write_jsonl(a,claude_rows())
        write_jsonl(b,codex_rows())
        scan([self.claude],None)
        a.unlink();b.unlink()
        sessions,details=scan([self.claude],None)
        self.assertEqual([session.agent for session in sessions],['codex'])
        self.assertEqual(details['archive']['stored_files'],1)

    def test_generation_check_reads_only_the_small_marker(self):
        self.read()
        current=archive.archive_generation()
        opened=Path.open
        def guard(path,*args,**kwargs):
            self.assertNotEqual(path.name,archive.FILENAME,'generation check reopened the whole archive')
            return opened(path,*args,**kwargs)
        with patch.object(Path,'open',guard):
            self.assertEqual(archive.archive_generation(),current)
        archive.clear_archive()
        self.assertEqual(archive.archive_generation(),current+1)

    def test_new_codex_cache_and_archive_drop_nested_optional_private_metadata(self):
        source=self.codex/'rollout-source.jsonl'
        rows=codex_rows()
        rows[0]['payload']['cwd']={'command':'PRIVATE-NESTED'}
        rows[0]['payload']['cli_version']=['PRIVATE-NESTED']
        rows[1]['payload']['model']={'account_id':'PRIVATE-NESTED'}
        rows[1]['timestamp']={'tool_output':'PRIVATE-NESTED'}
        write_jsonl(source,rows)
        sessions,_=scan()
        self.assertEqual(total(sessions[0].tokens),230)
        for name in ('codex.json',archive.FILENAME):
            self.assertNotIn('PRIVATE-NESTED',(self.cache/name).read_text('utf-8'))

    def test_source_that_grows_during_read_is_not_archived_under_the_earlier_signature(self):
        source=self.codex/'rollout-source.jsonl'
        rows=codex_rows()
        write_jsonl(source,rows)
        original=codex._rows
        def growing(path,decode,*resume):
            result=original(path,decode,*resume)
            write_jsonl(path,rows+codex_rows(response='later-response')[-1:])
            return result
        with patch.object(codex,'_rows',side_effect=growing):
            sessions,details=self.read()
        self.assertEqual(total(sessions[0].tokens),230)
        self.assertEqual(details['archive']['stored_files'],0)
        source.unlink()
        sessions,_=self.read()
        self.assertEqual(sessions,[])


if __name__=='__main__': unittest.main()
