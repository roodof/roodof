"""Inspection, collection and dry-run commands are not evidence that a test passed."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler.usage import scan
from pler.usage.checks import classify, outcome
from test_logs import codex_rows, write_jsonl


class CheckModeTests(unittest.TestCase):
    def test_explicit_non_running_modes_are_not_checks(self):
        commands = (
            'pytest --help', 'python -m pytest --version', 'pytest -h',
            'python -m pytest --collect-only', 'pytest --co', 'pytest --collectonly',
            'pytest --fixtures', 'pytest --setup-plan', 'pytest --setup-only',
            'cargo test --no-run', 'cargo test -- --list', 'cargo nextest list',
            'ctest -N', 'ctest --show-only=json-v1', 'go test -list TestCart ./...',
            'go test -list=TestCart ./...', 'go test -c ./cart', 'go test -n ./...',
            'make -n test', 'gmake -nq check', 'make --just-print', 'make --question',
            'nmake /N test', 'gradlew test -m', 'gradle test --dry-run',
            'mvn test -DskipTests', 'mvn test -DskipTests=true',
            'mvn test -Dmaven.test.skip=true', 'dotnet test --list-tests', 'dotnet test -t',
            'jest --listTests', 'npm test -- --listTests', 'vitest list',
            'rspec --dry-run', 'phpunit --list-tests', 'node --test --help',
            'gcc --version', 'javac -version', 'javac -help', 'rustc -V', 'cl /?',
            'tox -l', 'tox config', 'nox --list', 'ninja -n', 'scons -n', 'tsc --showConfig',
            'uv run pytest --help', 'env CI=1 python -m pytest --collect-only',
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNone(classify(command))

    def test_real_checks_and_option_like_paths_keep_their_outcomes(self):
        commands = (
            'pytest -q tests', 'python -m pytest tests/test_help.py',
            'cargo test --no-default-features', 'go test ./...', 'ctest --output-on-failure',
            'make -j4 test', 'mvn test -DskipTests=false', 'gradle test',
            'pytest tests/--help.txt', 'pytest tests/test--collect-only.py',
            'pytest -k help', 'npm test -- --runInBand', 'javac -h headers Main.java',
        )
        for command in commands:
            with self.subTest(command=command):
                result=classify(command)
                self.assertIsNotNone(result)
                self.assertEqual(outcome(result,False),'passed')

    def test_arguments_beyond_the_word_budget_cannot_claim_a_known_result(self):
        ordinary='pytest '+' '.join('tests/test_%d.py'%index for index in range(60))
        for command in (ordinary, ordinary+' --collect-only', ordinary+' --help'):
            with self.subTest(command=command):
                result=classify(command)
                self.assertIsNotNone(result)
                self.assertFalse(result['known'])
                self.assertEqual(outcome(result,False),'unknown')

    def test_non_running_final_step_does_not_replace_the_previous_checks_exit_code(self):
        result=classify('pytest && pytest --help')
        self.assertEqual(result,dict(kind='test',known=False))
        self.assertEqual(outcome(result,False),'unknown')
        self.assertEqual(classify('pytest --help && pytest'),dict(kind='test',known=True))

    def test_codex_exit_zero_from_non_running_modes_is_never_persisted_as_passed(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            claude=base/'claude'/'projects';claude.mkdir(parents=True)
            codex=base/'codex'/'sessions';codex.mkdir(parents=True)
            (codex.parent/'archived_sessions').mkdir()
            workspace=base/'workspace';workspace.mkdir()
            cache=base/'cache'
            rows=codex_rows('modes')
            for row in rows:
                payload=row.get('payload',{})
                if 'cwd' in payload:payload['cwd']=str(workspace)
            commands=('pytest --help', 'pytest --collect-only', 'cargo test --no-run', 'pytest -q')
            for index,command in enumerate(commands):
                rows.append(dict(type='event_msg',timestamp='2026-10-21T09:05:%02dZ'%index,
                                 payload=dict(type='item_completed',thread_id='modes',turn_id='turn',
                                              item=dict(type='CommandExecution',id='mode-%d'%index,command=command,
                                                        exit_code=0,status='completed',
                                                        aggregated_output='PRIVATE-CHECK-MODE-OUTPUT'))))
            write_jsonl(codex/'rollout-modes.jsonl',rows)
            with patch.dict(os.environ,PLER_CACHE_DIR=str(cache),CLAUDE_CONFIG_DIR=str(claude.parent),
                            CODEX_HOME=str(codex.parent)):
                sessions,_=scan()
                again,_=scan()
            self.assertEqual(sessions[0].checks,again[0].checks)
            self.assertEqual({key:sessions[0].checks['test'][key] for key in ('runs','passed','failed','last')},
                             dict(runs=1,passed=1,failed=0,last='passed'))
            persisted=''.join(path.read_text('utf-8') for path in cache.glob('*.json'))
            for private in ('PRIVATE-CHECK-MODE-OUTPUT','--help','--collect-only','--no-run','pytest'):
                self.assertNotIn(private,persisted)


if __name__=='__main__':unittest.main()
