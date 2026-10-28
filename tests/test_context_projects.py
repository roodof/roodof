"""Synthetic context evidence must not let file order choose a session's project."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler.usage import codex
from pler.usage.cache import FileCache
from pler.usage.records import total
from test_logs import write_jsonl


def record(kind, payload):
    return dict(type=kind, payload=payload, timestamp='2026-10-28T10:00:00Z')


def records(projects=(), metadata_project=None):
    meta = dict(id='synthetic-session')
    if metadata_project is not None:
        meta['cwd'] = metadata_project
    return ([record('session_meta', meta)]
            + [record('turn_context', dict(cwd=project, model='synthetic-model')) for project in projects]
            + [record('token_usage_record', dict(response_id='synthetic-response',
                                                usage=dict(input_tokens=100, output_tokens=0)))])


class ContextProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.a, self.b = (self.root / name for name in ('rollout-a.jsonl', 'rollout-b.jsonl'))

    def assert_conflict(self, sessions, issues):
        session, = sessions
        self.assertEqual((total(session.tokens), session.calls, issues), (100, 1, []))
        self.assertIsNone(session.project)
        self.assertFalse(session.attribution_complete)
        self.assertIn('shared_attribution', session.issues)

    def test_context_conflicts_do_not_depend_on_file_names_or_argument_order(self):
        for left, right in (('/synthetic/alpha', '/synthetic/beta'),
                            ('/synthetic/beta', '/synthetic/alpha')):
            write_jsonl(self.a, records([left]))
            write_jsonl(self.b, records([right]))
            for paths in ([self.a, self.b], [self.b, self.a]):
                with self.subTest(left=left, reversed_paths=paths[0] == self.b):
                    self.assert_conflict(*codex.read(paths))

    def test_conflicting_contexts_in_one_file_do_not_pick_the_first_project(self):
        for projects in (['/synthetic/alpha', '/synthetic/beta'],
                         ['/synthetic/beta', '/synthetic/alpha']):
            with self.subTest(projects=projects):
                write_jsonl(self.a, records(projects))
                self.assert_conflict(*codex.read([self.a]))

    def test_context_conflict_with_session_metadata_is_also_unknown(self):
        write_jsonl(self.a, records(['/synthetic/beta'], metadata_project='/synthetic/alpha'))
        self.assert_conflict(*codex.read([self.a]))

    def test_repeated_agreeing_contexts_and_metadata_keep_the_known_project(self):
        write_jsonl(self.a, records(['/synthetic/alpha'] * 2, metadata_project='/synthetic/alpha'))
        write_jsonl(self.b, records(['/synthetic/alpha']))
        session, = codex.read([self.b, self.a])[0]
        self.assertEqual((session.project, total(session.tokens), session.calls), ('/synthetic/alpha', 100, 1))
        self.assertTrue(session.attribution_complete)
        self.assertNotIn('shared_attribution', session.issues)

    def test_empty_and_invalid_context_cwds_do_not_mask_valid_evidence(self):
        write_jsonl(self.a, records(['', None, [], '/synthetic/alpha', ''], metadata_project=''))
        session, = codex.read([self.a])[0]
        self.assertEqual((session.project, total(session.tokens)), ('/synthetic/alpha', 100))
        self.assertTrue(session.attribution_complete)

    def test_metadata_only_project_still_works(self):
        write_jsonl(self.a, records(metadata_project='/synthetic/alpha'))
        session, = codex.read([self.a])[0]
        self.assertEqual((session.project, total(session.tokens)), ('/synthetic/alpha', 100))
        self.assertTrue(session.attribution_complete)

    def test_absent_project_evidence_remains_unknown_without_inventing_a_conflict(self):
        write_jsonl(self.a, records())
        session, = codex.read([self.a])[0]
        self.assertIsNone(session.project)
        self.assertNotIn('shared_attribution', session.issues)

    def test_cached_metadata_preserves_conflict_and_totals_without_reopening_logs(self):
        write_jsonl(self.a, records(['/synthetic/alpha']))
        write_jsonl(self.b, records(['/synthetic/beta']))
        with patch.dict(os.environ, PLER_CACHE_DIR=str(self.root / 'cache')):
            cache = FileCache('context-projects', 'synthetic-key')
            first, issues = codex.read([self.a, self.b], cache)
            cache.save()
            with patch.object(codex, '_rows', side_effect=AssertionError('reopened unchanged log')):
                cached, cached_issues = codex.read([self.b, self.a], FileCache('context-projects', 'synthetic-key'))
        self.assertEqual([s.as_dict() for s in first], [s.as_dict() for s in cached])
        self.assertEqual(issues, cached_issues)
        self.assert_conflict(cached, cached_issues)

    def test_repository_subfolders_and_local_spellings_are_equivalent(self):
        repo = self.root / 'SyntheticShop'
        (repo / '.git').mkdir(parents=True)
        (repo / 'panel').mkdir()
        (repo / 'service').mkdir()
        projects = [str(repo / 'panel'), str(repo / 'service'), str(repo) + os.sep]
        if os.name == 'nt':
            projects.append(str(repo).lower())
        write_jsonl(self.a, records(projects, metadata_project=str(repo)))
        session, = codex.read([self.a])[0]
        self.assertEqual(os.path.normcase(session.project), os.path.normcase(str(repo)))
        self.assertTrue(session.attribution_complete)
        self.assertNotIn('shared_attribution', session.issues)
        self.assertEqual(total(session.tokens), 100)

    def test_shared_response_with_same_repository_evidence_keeps_known_project(self):
        repo = self.root / 'SyntheticShop'
        (repo / '.git').mkdir(parents=True)
        (repo / 'panel').mkdir()
        (repo / 'service').mkdir()
        left = records([str(repo / 'panel')])
        right = records([str(repo / 'service')])
        left[0]['payload']['id'] = 'synthetic-a'
        right[0]['payload']['id'] = 'synthetic-b'
        write_jsonl(self.a, left); write_jsonl(self.b, right)
        sessions, issues = codex.read([self.a, self.b])
        session, = sessions
        self.assertEqual((total(session.tokens), session.calls, issues), (100, 1, []))
        self.assertEqual(session.project, str(repo / 'panel'))  # singleton spelling is retained
        self.assertFalse(session.attribution_complete)  # the original session owner remains uncertain
        self.assertEqual(session._project_evidence, frozenset([os.path.normcase(str(repo))]))

    def test_distinct_projects_in_temporary_directory_are_not_identity_evidence(self):
        alpha, beta = self.root / 'alpha', self.root / 'beta'
        alpha.mkdir(); beta.mkdir()
        write_jsonl(self.a, records([str(alpha), str(beta)]))
        self.assert_conflict(*codex.read([self.a]))
