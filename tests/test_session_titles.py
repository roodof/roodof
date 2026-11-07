"""Invented titles only; accounting/cache and export boundaries stay unchanged."""
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from pler.dashboard import project_view
from pler.reporting import without_work_items, mask_projects
from pler.usage.records import Session
from pler.usage.session_titles import load, clean, MAX_FILE, TAIL
from pler.usage.verdicts import session_code


class TitleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('\n'.join(json.dumps(r) for r in rows) + '\n', encoding='utf-8')

    def test_codex_exact_id_latest_rename_and_refresh(self):
        source = self.root / 'codex/sessions/2026/11/07/rollout.jsonl'
        source.parent.mkdir(parents=True)
        source.write_text('', encoding='utf-8')
        index = self.root / 'codex/session_index.jsonl'
        a = Session('codex', 'one', str(source))
        b = Session('codex', 'two', str(source))
        self.write(index, [dict(id='one', thread_name='Old name'), dict(id='two', thread_name='Other work'),
                           dict(id='one', thread_name='Ödeme ekranını düzelt')])
        titles = load([a, b])
        self.assertEqual(titles[session_code(a)], 'Ödeme ekranını düzelt')
        self.assertEqual(titles[session_code(b)], 'Other work')
        self.write(index, [dict(id='one', thread_name='Renamed')])
        self.assertEqual(load([a])[session_code(a)], 'Renamed')

    def test_claude_custom_title_over_index_summary_never_uses_prompt(self):
        source = self.root / 'claude/projects/demo/one.jsonl'
        a = Session('claude-code', 'one', str(source))
        self.write(source, [dict(type='user', sessionId='one', message=dict(content='PRIVATE PROMPT')),
                            dict(type='custom-title', sessionId='other', customTitle='Wrong session'),
                            dict(type='custom-title', sessionId='one', customTitle='Checkout fix')])
        (source.parent / 'sessions-index.json').write_text(json.dumps(dict(entries=[dict(sessionId='one', summary='Old summary')])), encoding='utf-8')
        self.assertEqual(load([a])[session_code(a)], 'Checkout fix')
        self.write(source, [dict(type='user', sessionId='one', message=dict(content='PRIVATE PROMPT'))])
        self.assertEqual(load([a])[session_code(a)], 'Old summary')
        (source.parent / 'sessions-index.json').unlink()
        self.assertEqual(load([a]), {})

    def test_long_claude_transcript_head_and_tail_and_broken_rows(self):
        source = self.root / 'claude/projects/demo/one.jsonl'
        a = Session('claude-code', 'one', str(source))
        self.write(source, [dict(type='custom-title', sessionId='one', customTitle='Early title')])
        with source.open('a', encoding='utf-8') as stream:
            stream.write('x' * (TAIL * 3) + '\n{broken}\n')
        self.assertEqual(load([a])[session_code(a)], 'Early title')
        with source.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(dict(type='custom-title', sessionId='one', customTitle='Latest title')) + '\n')
        self.assertEqual(load([a])[session_code(a)], 'Latest title')

    def test_missing_corrupt_oversized_and_archive_fall_back(self):
        source = self.root / 'codex/archived_sessions/one.jsonl'
        source.parent.mkdir(parents=True)
        source.write_text('', encoding='utf-8')
        a = Session('codex', 'one', str(source))
        index = self.root / 'codex/session_index.jsonl'
        self.assertEqual(load([a]), {})
        index.write_text('{broken}\n', encoding='utf-8')
        self.assertEqual(load([a]), {})
        index.write_bytes(b' ' * (MAX_FILE + 1))
        self.assertEqual(load([a]), {})
        self.write(index, [dict(id='one', thread_name='Do not expose archived title')])
        a.source_state = 'archive'
        self.assertEqual(load([a]), {})

    def test_titles_are_ui_only_and_do_not_enter_exports_or_session_records(self):
        now = datetime.now(timezone.utc)
        a = Session('codex', 'one', '/invented/sessions/one.jsonl', project='/work/demo', started=now, ended=now)
        before = dict(vars(a))
        data = project_view([a], dict(session_titles={session_code(a): 'PRIVATE DISPLAY TITLE'}), days=0)
        self.assertEqual(data['sessions'][0]['title'], 'PRIVATE DISPLAY TITLE')
        self.assertNotIn('PRIVATE DISPLAY TITLE', json.dumps(without_work_items(data)))
        self.assertNotIn('PRIVATE DISPLAY TITLE', json.dumps(mask_projects(data)))
        self.assertEqual(vars(a), before)

    def test_bounded_text_and_control_characters(self):
        self.assertEqual(clean('  Fix\n checkout\u202e\x00  '), 'Fix checkout')
        self.assertEqual(len(clean('a' * 400)), 160)
        self.assertIsNone(clean('a' * 5000))
        self.assertIsNone(clean(42))
