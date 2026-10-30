"""Tests and builds the agents ran, and whether their exit code is visible. Invented logs only.

The command text is classified while a log is read; it must never reach the cache, the archive or a view.
"""
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from pler.dashboard import project_view, session_view
from pler.usage import archive, scan
from pler.usage.checks import classify, outcome, summary
from pler.usage.records import Session
from test_logs import USAGE, claude_reply, write_jsonl

SECRET = 'SECRET-COMMAND-TEXT'


def kind(command):
    value = classify(command)
    return (value['kind'], value['known']) if value else None


class ClassifierTests(unittest.TestCase):
    def test_test_and_build_tools_of_many_languages(self):
        for command, expected in (
                ('python -m pytest -q', ('test', True)), ('PYTHONPATH=src pytest tests', ('test', True)),
                ('npm test', ('test', True)), ('pnpm run test:unit', ('test', True)), ('npm run build', ('build', True)),
                ('go test ./...', ('test', True)), ('cargo build --release', ('build', True)),
                ('dotnet test', ('test', True)), ('./gradlew :app:test', ('test', True)), ('mvn -q package', ('build', True)),
                ('make', ('build', True)), ('make check', ('test', True)), ('cmake --build build', ('build', True)),
                ('ctest --output-on-failure', ('test', True)), ('gcc -O2 main.c -o main', ('build', True)),
                ('bundle exec rspec', ('test', True)), ('uv run pytest -x', ('test', True)), ('npx vitest run', ('test', True)),
                ('node --test tests/a.cjs', ('test', True)), ('python tests/test_cart.py', ('test', True)),
                ('Invoke-Pester -Path tests', ('test', True)), ('timeout 60 python -m pytest', ('test', True))):
            with self.subTest(command=command):
                self.assertEqual(kind(command), expected)

    def test_ordinary_commands_and_quoted_text_are_not_checks(self):
        for command in ('git status', 'ls -la', 'make clean', 'npm run lint', 'node build.js', 'python run.py',
                        'python -c "import pytest"', 'echo "pytest && make"', "grep -r 'go test' .", '', None, 42, ['ls']):
            with self.subTest(command=command):
                self.assertIsNone(classify(command))

    def test_exit_code_is_the_checks_own_only_when_it_is_the_last_step(self):
        for command, known in (
                ('cd "C:/x y" && python -m pytest -q', True), ('npm run build && npm test', True), ('pytest 2>&1', True),
                ('pytest -q 2>&1 | tail -3', False), ('pytest || true', False), ('pytest; echo done', False),
                ('pytest &', False), ('gcc main.c && ./main', False), ('pytest | Select-Object -Last 3', False)):
            with self.subTest(command=command):
                self.assertEqual(classify(command)['known'], known)

    def test_shell_wrappers_lists_and_here_documents(self):
        self.assertEqual(kind(['bash', '-lc', 'go build ./... && go test ./...']), ('test', True))
        self.assertEqual(kind(['bash', '-lc', 'cargo test 2>&1 | tail']), ('test', False))
        self.assertEqual(kind('"C:/Program Files/PowerShell/7/pwsh.exe" -Command "python -m pytest -q"'), ('test', True))
        self.assertEqual(kind('& "C:/Python/python.exe" -m pytest -q'), ('test', True))
        self.assertEqual(kind('"C:/Program Files/Python312/python.exe" -m pytest -q'), ('test', True))
        self.assertEqual(kind(['powershell.exe', '-Command', "$env:CI='1'; & 'C:/Program Files/Go/bin/go.exe' build ./..."]),
                         ('build', True))
        body = "x = 'pytest; don''t'\n" * 3000
        self.assertEqual(kind("cat > f.py <<'EOF'\n" + body + "EOF\npython -m pytest -q"), ('test', True))
        self.assertIsNone(classify("python - <<'EOF'\npytest\nEOF"))
        self.assertIsNone(classify("@'\npytest\n'@ | Set-Content f.txt"))
        self.assertIsNone(classify('pytest ' + 'x' * 30000))  # too long to be a command line worth reading

    def test_outcome_needs_a_visible_exit_code(self):
        self.assertEqual(outcome(dict(kind='test', known=True), False), 'passed')
        self.assertEqual(outcome(dict(kind='test', known=True), True), 'failed')
        self.assertEqual(outcome(dict(kind='test', known=False), True), 'unknown')
        self.assertEqual(outcome(dict(kind='test', known=True), None), 'unknown')


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, str(self.temp), True)
        self.cache = self.temp / 'cache'
        self.claude = self.temp / 'claude' / 'projects'
        self.codex = self.temp / 'codex' / 'sessions'
        self.claude.mkdir(parents=True)
        self.codex.mkdir(parents=True)
        (self.codex.parent / 'archived_sessions').mkdir()
        env = patch.dict(os.environ, PLER_CACHE_DIR=str(self.cache), CLAUDE_CONFIG_DIR=str(self.claude.parent),
                         CODEX_HOME=str(self.codex.parent))
        env.start(); self.addCleanup(env.stop)

    def claude_session(self):
        def call(n, command, at, **extra):
            return claude_reply('s1', 'm%d' % n, 'r%d' % n, USAGE, [dict(type='tool_use', name='Bash', id='t%d' % n,
                                                                          input=dict(command=command, **extra))], at)

        def answer(n, error, at):
            return dict(type='user', sessionId='s1', timestamp=at, message=dict(role='user', content=[
                dict(type='tool_result', tool_use_id='t%d' % n, content='Exit code 1 ' + SECRET if error else SECRET,
                     is_error=error)]))
        return [
            call(1, 'python -m pytest -k ' + SECRET, '2026-10-20T10:00:00Z'), answer(1, True, '2026-10-20T10:00:05Z'),
            call(2, 'ls ' + SECRET, '2026-10-20T10:01:00Z'), answer(2, True, '2026-10-20T10:01:01Z'),
            call(3, 'make && echo ' + SECRET, '2026-10-20T10:02:00Z'), answer(3, False, '2026-10-20T10:02:05Z'),
            call(4, 'pytest -q 2>&1 | tail -3 # ' + SECRET, '2026-10-20T10:03:00Z'), answer(4, False, '2026-10-20T10:03:05Z'),
            call(5, 'python -m pytest -q', '2026-10-20T10:04:00Z', run_in_background=True), answer(5, False, '2026-10-20T10:04:01Z'),
            call(6, 'python -m pytest', '2026-10-20T10:05:00Z'), answer(6, False, '2026-10-20T10:05:30Z'),
        ]

    def codex_session(self, session_id):
        def item(n, command, code, at):
            return dict(timestamp=at, type='event_msg', payload=dict(type='item_completed', thread_id=session_id, turn_id='u1',
                        item=dict(type='CommandExecution', id='item-%d' % n, command=command, exit_code=code,
                                  status='completed' if code == 0 else 'failed', aggregated_output=SECRET, cwd='/work/engine')))
        usage = dict(input_tokens=100, cached_input_tokens=0, cache_write_input_tokens=0, output_tokens=10, reasoning_output_tokens=0)
        return [
            dict(timestamp='2026-10-21T09:00:00Z', type='session_meta', payload=dict(id=session_id, cwd='/work/engine')),
            dict(timestamp='2026-10-21T09:00:01Z', type='turn_context', payload=dict(model='gpt-6.1-sol', cwd='/work/engine')),
            dict(timestamp='2026-10-21T09:00:02Z', type='token_usage_record', payload=dict(response_id='a', usage=usage)),
            item(1, ['bash', '-lc', 'cargo test ' + SECRET], 101, '2026-10-21T09:00:03Z'),
            item(2, 'git status ' + SECRET, 0, '2026-10-21T09:00:04Z'),
            item(3, ['bash', '-lc', 'cargo build && cargo test'], 0, '2026-10-21T09:00:05Z'),
            item(4, ['bash', '-lc', 'cargo test | tail'], 0, '2026-10-21T09:00:06Z'),
        ]

    def stored_text(self):
        return ''.join(path.read_text('utf-8') for path in self.cache.glob('*.json'))

    def test_claude_checks_use_the_tool_answer_and_never_keep_the_command(self):
        write_jsonl(self.claude / 'shop' / 's1.jsonl', self.claude_session())
        sessions, _ = scan()
        checks = sessions[0].checks
        self.assertEqual({key: checks['test'][key] for key in ('runs', 'passed', 'failed', 'last')},
                         dict(runs=4, passed=1, failed=1, last='passed'))
        self.assertEqual({key: checks['build'][key] for key in ('runs', 'passed', 'failed', 'last')},
                         dict(runs=1, passed=0, failed=0, last=None))
        self.assertNotIn(SECRET, self.stored_text())
        self.assertNotIn('pytest', self.stored_text())
        # Only answers to check commands are kept; the plain `ls` answer is not.
        rows = json.loads((self.cache / 'claude.json').read_text('utf-8'))['files']
        answers = [result['id'] for value in rows.values() for row in value['rows'] for result in row.get('results', ())]
        self.assertEqual(sorted(answers), ['t1', 't3', 't4', 't5', 't6'])
        sessions_again, _ = scan()  # from the cache
        self.assertEqual(sessions_again[0].checks, checks)

    def test_codex_checks_use_exit_codes_count_copies_once_and_never_keep_the_command(self):
        rows = self.codex_session('c1')
        write_jsonl(self.codex / '2026' / '10' / '21' / 'rollout-c1.jsonl', rows)
        write_jsonl(self.codex / '2026' / '10' / '21' / 'rollout-c1-copy.jsonl', rows)  # a copied history
        sessions, _ = scan()
        self.assertEqual(len(sessions), 1)
        checks = sessions[0].checks
        self.assertEqual({key: checks['test'][key] for key in ('runs', 'passed', 'failed', 'last')},
                         dict(runs=3, passed=1, failed=1, last='passed'))
        self.assertNotIn('build', checks)  # `cargo build && cargo test` is one test run
        self.assertNotIn(SECRET, self.stored_text())
        self.assertNotIn('cargo', self.stored_text())

    def test_archived_rows_keep_only_kind_flag_and_answer(self):
        claude = archive.sanitize('claude-code', [
            dict(type='assistant', sessionId='s', message=dict(id='m', content=[
                dict(type='tool_use', name='Bash', id='t', input=dict(command=SECRET), check='test', known=True)])),
            dict(type='user', sessionId='s', results=[dict(id='t', error=True, text=SECRET)]),
            dict(type='assistant', sessionId='s', message=dict(id='n', content=[
                dict(type='tool_use', name='Bash', id='u', check='lint', known='yes')]))])
        self.assertNotIn(SECRET, json.dumps(claude))
        self.assertEqual(claude[0]['message']['content'][0]['check'], 'test')
        self.assertEqual(claude[1]['results'], [dict(id='t', error=True)])
        self.assertNotIn('check', claude[2]['message']['content'][0])
        codex = archive.sanitize('codex', [
            dict(type='event_msg', payload=dict(type='item_completed', item_id='i', check='build', outcome='failed', command=SECRET)),
            dict(type='event_msg', payload=dict(type='item_completed', item_id='j', check='deploy', outcome='passed'))])
        self.assertEqual(codex, [dict(type='event_msg', timestamp=None,
                                      payload=dict(type='item_completed', item_id='i', check='build', outcome='failed'))])


class ViewTests(unittest.TestCase):
    def sessions(self):
        from datetime import datetime, timezone
        rows = []
        for n, results in enumerate((('passed', 'failed'), ('failed', 'passed', 'failed'), ('unknown',), ())):
            session = Session('codex', 's%d' % n, '/logs/s%d.jsonl' % n, project='/work/app',
                              started=datetime(2026, 10, 20, n, tzinfo=timezone.utc), ended=datetime(2026, 10, 20, n, 30, tzinfo=timezone.utc),
                              calls=1, tokens=dict(input=100 * (n + 1), cache_read=0, cache_write=0, output=0, reasoning=0))
            for minute, result in enumerate(results):
                session.record_check('test', result, datetime(2026, 10, 20, n, minute, tzinfo=timezone.utc))
            rows.append(session)
        return rows

    def test_summary_session_rows_and_observation(self):
        rows = self.sessions()
        value = summary(rows)['test']
        self.assertEqual(value, dict(sessions=3, runs=6, passed=2, failed=3, ended_passed=0, ended_failed=2, ended_unknown=1,
                                     ended_failed_tokens=300))
        view = project_view(rows, {}, days=0, lang='tr')
        self.assertEqual(view['checks']['test']['ended_failed'], 2)
        note = next(item for item in view['insights'] if item['kind'] == 'tests')
        self.assertEqual(note['level'], 'warn')
        self.assertIn('3 oturum test çalıştırdı', note['detail'])
        row = session_view(rows[1])
        self.assertEqual(row['checks'], dict(test=dict(runs=3, passed=1, failed=2, last='failed')))
        self.assertEqual(session_view(rows[3])['checks'], {})

    def test_last_result_follows_time_not_reading_order(self):
        from datetime import datetime, timezone
        session = Session('codex', 's', '/logs/s.jsonl')
        session.record_check('test', 'passed', datetime(2026, 10, 20, 10, tzinfo=timezone.utc))
        session.record_check('test', 'failed', datetime(2026, 10, 20, 9, tzinfo=timezone.utc))
        session.record_check('test', 'unknown', datetime(2026, 10, 20, 11, tzinfo=timezone.utc))
        self.assertEqual((session.checks['test']['last'], session.checks['test']['runs']), ('passed', 3))


if __name__ == '__main__':
    unittest.main()
