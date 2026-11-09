from datetime import datetime, timezone, timedelta
import unittest
from pler.dashboard import project_view
from pler.usage.records import Session

class FirstUseTests(unittest.TestCase):
 def test_source_summary_is_unfiltered_and_path_free(self):
  now=datetime.now(timezone.utc)
  sessions=[Session('codex','a','/invented/a',project='/secret/project-a',started=now,ended=now),
            Session('claude-code','b','/invented/b',project='/secret/project-b',started=now-timedelta(days=50),ended=now-timedelta(days=50))]
  data=project_view(sessions,dict(codex_files=3,claude_files=1),days=7,agent='codex',now=now)
  self.assertEqual(data['totals']['sessions'],1)
  self.assertEqual(data['setup'],dict(sessions=2,projects=2,agents=[dict(agent='claude-code',sessions=1,files=1),dict(agent='codex',sessions=1,files=3)]))
  self.assertNotIn('secret',str(data['setup']))
 def test_retained_history_is_not_reported_as_a_live_file(self):
  now=datetime.now(timezone.utc)
  a=Session('codex','a','/invented/a',project='/work/a',started=now,ended=now)
  a.source_state='archive'
  data=project_view([a],{},days=0)
  self.assertEqual(data['setup']['agents'][1],dict(agent='codex',sessions=1,files=0))
