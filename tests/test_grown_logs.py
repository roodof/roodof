"""A log that has only grown since the last read is read on from where that read ended, with exactly the result
of a full read; a rewritten, shortened or half-written log is read from the start."""
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from pler.usage import claude_code, codex, scan
from pler.usage.cache import FileCache
from test_logs import USAGE, claude_reply, stored_zstd, write_jsonl


def append(path, rows, tail=''):
    with path.open('a', encoding='utf-8', newline='') as stream:
        stream.write(''.join(json.dumps(row) + '\n' for row in rows) + tail)


def claude_parts():
    def call(n, command, at):
        return claude_reply('s1', 'm%d' % n, 'r%d' % n, USAGE,
                            [dict(type='tool_use', name='Bash', id='t%d' % n, input=dict(command=command))], at)

    def answer(n, error, at):
        return dict(type='user', sessionId='s1', timestamp=at, cwd='/work/shop', message=dict(role='user', content=[
            dict(type='tool_result', tool_use_id='t%d' % n, content='invented output', is_error=error)]))
    prompt = dict(type='user', sessionId='s1', uuid='u1', timestamp='2026-10-20T10:00:00Z', cwd='/work/shop',
                  message=dict(role='user', content='invented request'))
    first = [prompt, call(1, 'python -m pytest', '2026-10-20T10:00:05Z')]
    # The answer to the test started in the first part only arrives in the second.
    second = [answer(1, True, '2026-10-20T10:00:30Z'), call(2, 'python -m pytest', '2026-10-20T10:01:00Z'),
              answer(2, False, '2026-10-20T10:01:30Z')]
    return first, second


def codex_parts():
    usage = dict(input_tokens=100, cached_input_tokens=0, cache_write_input_tokens=0, output_tokens=10, reasoning_output_tokens=0)
    def item(n, code, at):
        return dict(timestamp=at, type='event_msg', payload=dict(type='item_completed', item=dict(
            type='CommandExecution', id='item-%d' % n, command=['bash', '-lc', 'cargo test'], exit_code=code)))
    first = [dict(timestamp='2026-10-21T09:00:00Z', type='session_meta', payload=dict(id='c1', cwd='/work/engine')),
             dict(timestamp='2026-10-21T08:59:00Z', type='response_item', payload=dict(type='message', content='invented')),
             dict(timestamp='2026-10-21T09:00:01Z', type='turn_context', payload=dict(model='gpt-6.1-sol', cwd='/work/engine')),
             dict(timestamp='2026-10-21T09:00:02Z', type='token_usage_record', payload=dict(response_id='a', usage=usage)),
             item(1, 101, '2026-10-21T09:00:03Z')]
    # Rows that only move the session's last time and close its tests come later.
    second = [dict(timestamp='2026-10-21T09:00:04Z', type='token_usage_record', payload=dict(response_id='b', usage=usage)),
              item(2, 0, '2026-10-21T09:00:05Z'),
              dict(timestamp='2026-10-21T09:30:00Z', type='response_item', payload=dict(type='message', content='invented'))]
    return first, second


class GrownLogTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.temp), True)
        self.claude = self.temp / 'claude' / 'projects'
        self.codex = self.temp / 'codex' / 'sessions'
        (self.codex.parent / 'archived_sessions').mkdir(parents=True)
        self.claude.mkdir(parents=True)
        self.codex.mkdir(parents=True)
        self.env(self.temp / 'cache')

    def env(self, cache):
        values = patch.dict(os.environ, PLER_CACHE_DIR=str(cache), CLAUDE_CONFIG_DIR=str(self.claude.parent),
                            CODEX_HOME=str(self.codex.parent))
        values.start(); self.addCleanup(values.stop)

    def full(self):
        """The same logs read by a computer without any cache."""
        self.env(self.temp / ('fresh-%d' % len(os.listdir(str(self.temp)))))
        return scan()[0]

    def parsed(self, module):
        return patch.object(module, 'json_row', wraps=module.json_row)

    def test_a_grown_transcript_is_read_from_where_the_last_read_ended(self):
        source = self.claude / 'shop' / 's1.jsonl'
        first, second = claude_parts()
        write_jsonl(source, first)
        scan()
        append(source, second)
        with self.parsed(claude_code) as rows:
            sessions, _ = scan()
        self.assertEqual(rows.call_count, len(second))
        self.assertEqual(sessions, self.full())
        test = sessions[0].checks['test']
        self.assertEqual((test['runs'], test['failed'], test['passed'], test['last']), (2, 1, 1, 'passed'))

    def test_a_grown_rollout_keeps_its_first_and_last_times_and_flags(self):
        source = self.codex / '2026' / '10' / '21' / 'rollout-c1.jsonl'
        first, second = codex_parts()
        write_jsonl(source, first)
        append(source, [], tail='{not json\n')  # a malformed line before the resume point stays counted
        scan()
        append(source, second)
        with self.parsed(codex) as rows:
            sessions, _ = scan()
        self.assertEqual(rows.call_count, len(second))
        self.assertEqual(sessions, self.full())
        self.assertEqual((sessions[0].started.minute, sessions[0].ended.minute), (59, 30))
        self.assertIn('invalid_records', sessions[0].issues)
        self.assertEqual(sessions[0].checks['test']['last'], 'passed')

    def test_a_half_written_last_line_leaves_no_resume_point(self):
        source = self.claude / 'shop' / 's1.jsonl'
        first, second = claude_parts()
        line = json.dumps(second[0]) + '\n'
        write_jsonl(source, first)
        append(source, [], tail=line[:40])
        scan()
        append(source, second[1:], tail='')
        with source.open('r+', encoding='utf-8', newline='') as stream:
            text = stream.read()
            stream.seek(0); stream.write(text.replace(line[:40], line, 1)); stream.truncate()
        with self.parsed(claude_code) as rows:
            sessions, _ = scan()
        self.assertEqual(rows.call_count, len(first) + len(second))
        self.assertEqual(sessions, self.full())

    def resumed(self, source, change):
        """Read `source`, apply `change`, read again; True when the second read continued the first."""
        cache = FileCache('grown-check', 'v1')
        self.assertIsNone(cache.get(source))
        point = {}
        cache.put(source, claude_code._rows(source, cache.grown(source), point), point)
        cache.save()
        self.assertIn('resume', cache.new[str(source)])
        change()
        cache = FileCache('grown-check', 'v1')
        self.assertIsNone(cache.get(source))
        return cache.grown(source) is not None

    def test_only_an_append_to_the_same_file_is_continued(self):
        first, second = claude_parts()
        source = self.claude / 'shop' / 's1.jsonl'
        write_jsonl(source, first)
        original, more = source.read_bytes(), json.dumps(second[0]).encode() + b'\n'
        self.assertTrue(self.resumed(source, lambda: append(source, second)))

        def rewrite_start():
            source.write_bytes(original.replace(b'"s1"', b'"s2"', 1) + more)
        def rewrite_before_end():
            self.assertIn(b'50', original[-30:])
            source.write_bytes(original[:-30] + original[-30:].replace(b'50', b'51') + more)
        def shorten():
            source.write_bytes(original[:len(original) // 2])
        def replace_file():
            copy = source.with_name('copy.jsonl')
            copy.write_bytes(original + more)
            os.replace(str(copy), str(source))
        for change in (rewrite_start, rewrite_before_end, shorten) + ((replace_file,) if os.stat(source).st_ino else ()):
            with self.subTest(change=change.__name__):
                write_jsonl(source, first)
                self.assertFalse(self.resumed(source, change))

    def test_a_stored_point_that_does_not_fit_the_rows_is_ignored(self):
        first, second = claude_parts()
        source = self.claude / 'shop' / 's1.jsonl'
        write_jsonl(source, first)
        scan()
        stored = self.temp / 'cache' / 'claude.json'
        value = json.loads(stored.read_text('utf-8'))
        entry = value['files'][str(source)]
        for broken in (dict(entry['resume'], state=dict(malformed='no', asked=[])),
                       dict(entry['resume'], state=dict(malformed=True, asked=[])),
                       dict(entry['resume'], size='large')):
            with self.subTest(resume=broken):
                entry['resume'] = broken
                stored.write_text(json.dumps(value), 'utf-8')
                append(source, second[:1])
                with self.parsed(claude_code) as rows:
                    sessions, _ = scan()
                self.assertEqual(rows.call_count, len(source.read_text('utf-8').splitlines()))
                self.assertEqual(sessions, self.full())
                self.env(self.temp / 'cache')
                value = json.loads(stored.read_text('utf-8'))
                entry = value['files'][str(source)]

    def test_compressed_rollouts_are_never_continued(self):
        first, _ = codex_parts()
        source = self.codex / '2026' / '10' / '21' / 'rollout-c1.jsonl.zst'
        source.parent.mkdir(parents=True)
        source.write_bytes(stored_zstd(''.join(json.dumps(row) + '\n' for row in first).encode('utf-8')))
        point = {}
        rows = codex._rows(source, codex.decoder()[0], None, point)
        self.assertTrue(rows)
        self.assertEqual(point, {})
        plain = source.with_name('rollout-c1.jsonl')
        write_jsonl(plain, first)
        codex._rows(plain, codex.decoder()[0], None, point)
        self.assertEqual(point['offset'], plain.stat().st_size)
