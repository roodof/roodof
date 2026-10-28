"""Retained metadata survives deleted logs without becoming a second accounting source.

Only invented records and isolated temporary roots/caches are used. WSL failure cases have filesystem
guards and mocked status: this module never touches a real UNC share or starts a distro.
"""
from contextlib import ExitStack
import builtins
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pler import paths, wsl
from pler.usage import scan
from pler.usage import archive, discovery
from pler.usage.cache import _checksum
from pler.usage.records import total
from test_logs import claude_reply, write_jsonl

AT = '2026-10-28T10:00:00Z'
LATER = '2026-10-28T10:01:00Z'
PRIVATE = ('PROMPT-CANARY', 'REPLY-CANARY', 'COMMAND-CANARY', 'OUTPUT-CANARY', 'ACCOUNT-CANARY')


def codex_rows(identity='codex', amount=200, output=30, response='reply-1'):
    return [dict(type='session_meta', timestamp=AT, payload=dict(id=identity)),
            dict(type='turn_context', timestamp=AT, payload=dict(model='invented-model')),
            dict(type='token_usage_record', timestamp=AT, payload=dict(response_id=response,
                 usage=dict(input_tokens=amount, output_tokens=output, cached_input_tokens=0,
                            cache_write_input_tokens=0, reasoning_output_tokens=0)))]


def claude_rows(identity='claude', amount=100, output=20, message='message-1', request='request-1'):
    row = claude_reply(identity, message, request, dict(input_tokens=amount, output_tokens=output),
                       [dict(type='text', text='REPLY-CANARY')], AT)
    row.pop('cwd', None)  # no filesystem project evidence outside this test's own selected roots
    return [row]


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.claude = self.root / 'claude' / 'projects'
        self.codex = self.root / 'codex' / 'sessions'
        self.claude.mkdir(parents=True)
        self.codex.mkdir(parents=True)
        (self.codex.parent / 'archived_sessions').mkdir()
        self.cache = self.root / 'cache'
        self.environment = patch.dict(os.environ, CLAUDE_CONFIG_DIR=str(self.claude.parent),
                                      CODEX_HOME=str(self.codex.parent), PLER_CACHE_DIR=str(self.cache))
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def both(self):
        claude = self.claude / 'invented' / 'session.jsonl'
        codex = self.codex / 'rollout-invented.jsonl'
        write_jsonl(claude, claude_rows())
        write_jsonl(codex, codex_rows())
        return claude, codex

    def explicit(self, retain=True, claude=None, codex=None):
        return scan([self.claude if claude is None else claude],
                    [self.codex if codex is None else codex], retain=retain)

    def numbers(self, sessions):
        return len(sessions), sum(total(session.tokens) for session in sessions), sum(session.calls for session in sessions)

    def test_default_environment_sources_replay_after_deletion_with_explicit_provenance(self):
        sources = self.both()
        live, initial = scan()
        self.assertEqual(self.numbers(live), (2, 350, 2))
        self.assertTrue(initial['archive']['enabled'])
        self.assertTrue(all(session.source_state == 'live' and not session.source_deleted for session in live))
        for path in sources:
            path.unlink()
        retained, missing = scan()
        self.assertEqual(self.numbers(retained), (2, 350, 2))
        self.assertTrue(all(session.source_state == 'archive' and session.source_deleted for session in retained))
        self.assertTrue(all(session.archive_files == 1 and not session.archive_unverified for session in retained))
        self.assertEqual((missing['archive']['stored_files'], missing['archive']['archive_files'],
                          missing['archive']['unverified_files']), (2, 2, 0))
        self.assertEqual(missing['skipped'], [])

    def test_explicit_sources_are_not_persisted_without_opt_in(self):
        sources = self.both()
        live, details = self.explicit(retain=False)
        self.assertEqual(self.numbers(live), (2, 350, 2))
        self.assertFalse(details['archive']['enabled'])
        for path in sources:
            path.unlink()
        missing, _ = self.explicit(retain=False)
        self.assertEqual(missing, [])
        self.assertEqual(archive.archive_info()['stored_files'], 0)

    def test_explicit_opt_in_retains_only_its_selected_roots(self):
        first = self.codex / 'rollout-first.jsonl'
        other_root = self.root / 'other-codex' / 'sessions'
        second = other_root / 'rollout-second.jsonl'
        write_jsonl(first, codex_rows('first', response='first-response'))
        write_jsonl(second, codex_rows('second', amount=500, output=0, response='second-response'))
        self.explicit()
        self.explicit(codex=other_root)
        first.unlink()
        second.unlink()
        selected, _ = self.explicit()
        self.assertEqual(self.numbers(selected), (1, 230, 1))
        self.assertEqual(selected[0].session_id, 'first')
        other, _ = self.explicit(codex=other_root)
        self.assertEqual(self.numbers(other), (1, 500, 1))
        self.assertEqual(other[0].session_id, 'second')
        transient, _ = self.explicit(retain=False)
        self.assertEqual(transient, [])

    def test_archived_claude_reply_and_live_resume_are_counted_once(self):
        original = self.claude / 'invented' / 'old.jsonl'
        base = claude_rows()
        write_jsonl(original, base)
        self.explicit()
        original.unlink()
        resumed = self.claude / 'invented' / 'resume.jsonl'
        write_jsonl(resumed, base + claude_rows(amount=5, output=7, message='message-2', request='request-2'))
        sessions, details = self.explicit()
        self.assertEqual(self.numbers(sessions), (1, 132, 2))
        self.assertEqual((sessions[0].source_state, sessions[0].source_deleted, sessions[0].archive_files),
                         ('mixed', True, 1))
        self.assertEqual(details['archive']['archive_files'], 1)
        # A second scan must not add another archive layer or another copy of either reply.
        again, _ = self.explicit()
        self.assertEqual(self.numbers(again), (1, 132, 2))

    def test_archived_codex_response_and_live_resume_are_counted_once(self):
        original = self.codex / 'rollout-old.jsonl'
        base = codex_rows()
        write_jsonl(original, base)
        self.explicit()
        original.unlink()
        resumed = self.codex / 'rollout-resume.jsonl'
        next_response = codex_rows(amount=50, output=10, response='reply-2')[-1]
        next_response['timestamp'] = LATER
        write_jsonl(resumed, base + [next_response])
        sessions, _ = self.explicit()
        self.assertEqual(self.numbers(sessions), (1, 290, 2))
        self.assertEqual((sessions[0].source_state, sessions[0].source_deleted, sessions[0].archive_files),
                         ('mixed', True, 1))

    def test_codex_shared_response_retains_archive_provenance_on_either_ownership_anchor(self):
        for archived_id, live_id in (('B','A'), ('A','B')):
            with self.subTest(archived=archived_id, live=live_id):
                selected = self.codex / ('archive-' + archived_id)
                original = selected / 'rollout-archive.jsonl'
                live = selected / 'rollout-live.jsonl'
                write_jsonl(original, codex_rows(archived_id, amount=150, output=0, response='shared-response'))
                self.explicit(codex=selected)
                original.unlink()
                write_jsonl(live, codex_rows(live_id, amount=100, output=0, response='shared-response'))
                sessions, _ = self.explicit(codex=selected)
                self.assertEqual(sum(total(session.tokens) for session in sessions), 150)
                anchors = [session for session in sessions if total(session.tokens)]
                self.assertEqual(len(anchors), 1)
                self.assertIn(anchors[0].source_state, ('mixed','archive'))
                self.assertTrue(anchors[0].source_deleted)
                self.assertGreaterEqual(anchors[0].archive_files, 1)

    def test_claude_shared_reply_retains_archive_provenance_on_either_ownership_anchor(self):
        for archived_id, live_id in (('B','A'), ('A','B')):
            with self.subTest(archived=archived_id, live=live_id):
                selected = self.claude / ('archive-' + archived_id)
                original = selected / 'archive.jsonl'
                live = selected / 'live.jsonl'
                write_jsonl(original, claude_rows(archived_id, amount=150, output=0,
                                                  message='shared-message', request='shared-request'))
                self.explicit(claude=selected)
                original.unlink()
                write_jsonl(live, claude_rows(live_id, amount=100, output=0,
                                              message='shared-message', request='shared-request'))
                sessions, _ = self.explicit(claude=selected)
                self.assertEqual(sum(total(session.tokens) for session in sessions), 150)
                anchors = [session for session in sessions if total(session.tokens)]
                self.assertEqual(len(anchors), 1)
                self.assertIn(anchors[0].source_state, ('mixed','archive'))
                self.assertTrue(anchors[0].source_deleted)
                self.assertGreaterEqual(anchors[0].archive_files, 1)

    def test_cumulative_checkpoint_copy_and_later_response_keep_existing_reconciliation(self):
        original = self.codex / 'rollout-checkpoint.jsonl'
        checkpoint = dict(type='event_msg', timestamp=AT, payload=dict(type='token_count',
                          info=dict(total_token_usage=dict(input_tokens=100, output_tokens=0))))
        base = codex_rows('checkpoint')[:1] + [checkpoint]
        write_jsonl(original, base)
        self.explicit()
        original.unlink()
        resumed = self.codex / 'rollout-resume.jsonl'
        later = codex_rows('checkpoint', amount=20, output=0, response='later')[-1]
        later['timestamp'] = LATER
        write_jsonl(resumed, base + [later])
        sessions, _ = self.explicit()
        self.assertEqual(self.numbers(sessions), (1, 120, 1))
        self.assertFalse(sessions[0].calls_complete)
        self.assertEqual(sessions[0].source_state, 'mixed')

    def test_reappearing_source_replaces_archive_status_instead_of_adding_usage(self):
        source = self.codex / 'rollout-invented.jsonl'
        rows = codex_rows()
        write_jsonl(source, rows)
        self.explicit()
        source.unlink()
        self.explicit()
        write_jsonl(source, rows)
        sessions, details = self.explicit()
        self.assertEqual(self.numbers(sessions), (1, 230, 1))
        self.assertEqual(sessions[0].source_state, 'live')
        self.assertFalse(sessions[0].source_deleted)
        self.assertEqual(details['archive']['archive_files'], 0)

    def test_partial_discovery_uses_unverified_metadata_without_claiming_deletion(self):
        readable = self.codex / 'readable' / 'rollout-one.jsonl'
        blocked = self.codex / 'blocked' / 'rollout-two.jsonl'
        write_jsonl(readable, codex_rows('readable', response='readable-response'))
        write_jsonl(blocked, codex_rows('blocked', amount=500, output=0, response='blocked-response'))
        self.explicit()
        original_scandir = os.scandir
        def partial(value):
            if Path(value) == blocked.parent:
                raise PermissionError('synthetic unreadable folder')
            return original_scandir(value)
        with patch.object(os, 'scandir', side_effect=partial):
            sessions, details = self.explicit()
        self.assertEqual(self.numbers(sessions), (2, 730, 2))
        by_id = {session.session_id: session for session in sessions}
        self.assertEqual(by_id['readable'].source_state, 'live')
        self.assertTrue(by_id['blocked'].archive_unverified)
        self.assertFalse(by_id['blocked'].source_deleted)
        self.assertEqual(details['archive']['unverified_files'], 1)
        self.assertIn('PermissionError', [reason for _, reason in details['skipped']])
        # Restored access makes the source live again; the archive never marks it deleted.
        restored, _ = self.explicit()
        self.assertTrue(all(session.source_state == 'live' and not session.source_deleted for session in restored))

    def test_closed_wsl_selection_never_probes_unc_or_imports_an_unselected_local_archive(self):
        source = self.codex / 'rollout-invented.jsonl'
        write_jsonl(source, codex_rows())
        self.explicit()
        before = archive.archive_info()['stored_files']
        def guard(original):
            def checked(value, *args, **kwargs):
                if paths.network(value):
                    raise AssertionError('UNC filesystem probe')
                return original(value, *args, **kwargs)
            return checked
        with ExitStack() as stack:
            stack.enter_context(patch.object(wsl, 'WINDOWS', True))
            stack.enter_context(patch.object(wsl, 'running', return_value={}))
            for owner, name in ((Path,'lstat'), (Path,'stat'), (Path,'open'), (Path,'is_dir'),
                                (Path,'is_file'), (Path,'exists'), (Path,'resolve'),
                                (os,'stat'), (os,'lstat'), (os,'open'), (os,'scandir'),
                                (builtins,'open'), (io,'open')):
                stack.enter_context(patch.object(owner, name, guard(getattr(owner,name))))
            selected, details = scan([r'\\wsl.localhost\InventedStopped\tmp\claude\projects'],
                                     [r'\\wsl.localhost\InventedStopped\tmp\codex\sessions'], retain=True)
        self.assertEqual(selected, [])
        self.assertEqual([reason for _, reason in details['skipped']], ['WSLNotRunning', 'WSLNotRunning'])
        self.assertEqual(archive.archive_info()['stored_files'], before)
        restored, _ = self.explicit()
        self.assertEqual(self.numbers(restored), (1, 230, 1))
        self.assertFalse(restored[0].source_deleted)

    def test_previously_retained_wsl_rows_replay_as_unverified_when_the_selected_distro_is_closed(self):
        selected_root = r'\\wsl.localhost\InventedStopped\tmp\codex\sessions'
        source = selected_root + r'\rollout-invented.jsonl'
        manifest = discovery.Manifest()
        manifest.select(selected_root)
        seeded = archive.Archive()
        seeded.prepare('codex', [], manifest, 'invented-reader')
        seeded.observe('codex', Path(source), codex_rows())
        seeded.finish()
        def guard(original):
            def checked(value, *args, **kwargs):
                if paths.network(value):
                    raise AssertionError('UNC filesystem probe')
                return original(value, *args, **kwargs)
            return checked
        with ExitStack() as stack:
            stack.enter_context(patch.object(wsl, 'WINDOWS', True))
            stack.enter_context(patch.object(wsl, 'running', return_value={}))
            stack.enter_context(patch('pler.usage.version', return_value='invented-reader'))
            for owner, name in ((Path,'lstat'), (Path,'stat'), (Path,'open'), (Path,'is_dir'),
                                (Path,'is_file'), (Path,'exists'), (Path,'resolve'),
                                (os,'stat'), (os,'lstat'), (os,'open'), (os,'scandir'),
                                (builtins,'open'), (io,'open')):
                stack.enter_context(patch.object(owner, name, guard(getattr(owner,name))))
            retained, details = scan([self.claude], [selected_root.replace('wsl.localhost','wsl$')], retain=True)
        self.assertEqual(self.numbers(retained), (1, 230, 1))
        self.assertEqual(retained[0].source_state, 'archive')
        self.assertTrue(retained[0].archive_unverified)
        self.assertFalse(retained[0].source_deleted)
        self.assertFalse(retained[0].archive_old_parser)
        self.assertEqual((details['archive']['archive_files'], details['archive']['unverified_files']), (1,1))
        self.assertEqual([reason for _, reason in details['skipped']], ['WSLNotRunning'])

    def test_archive_contains_only_projected_metadata_never_prompt_reply_command_output_or_account(self):
        claude, codex = self.both()
        rows = claude_rows()
        rows[0]['account_id'] = 'ACCOUNT-CANARY'
        rows[0]['message']['content'].append(dict(type='tool_use', id='tool-1', name='Bash',
                                                input=dict(command='COMMAND-CANARY')))
        rows += [dict(type='user', sessionId='claude', timestamp=AT,
                      message=dict(role='user', content='PROMPT-CANARY')),
                 dict(type='user', sessionId='claude', timestamp=AT, message=dict(role='user',
                      content=[dict(type='tool_result', tool_use_id='tool-1', content='OUTPUT-CANARY')]))]
        write_jsonl(claude, rows)
        rows = codex_rows()
        rows[0]['payload'].update(base_instructions='PROMPT-CANARY', account_id='ACCOUNT-CANARY')
        rows += [dict(type='response_item', timestamp=AT, payload=dict(type='function_call', name='exec',
                      call_id='tool-1', arguments=json.dumps(dict(cmd='COMMAND-CANARY')))),
                 dict(type='response_item', timestamp=AT, payload=dict(type='function_call_output',
                      call_id='tool-1', output='OUTPUT-CANARY')),
                 dict(type='response_item', timestamp=AT, payload=dict(type='message',
                      content=[dict(type='output_text', text='REPLY-CANARY')]))]
        write_jsonl(codex, rows)
        self.explicit()
        text = (self.cache / 'metadata-archive.json').read_text(encoding='utf-8')
        for secret in PRIVATE:
            self.assertNotIn(secret, text)
        self.assertGreater(archive.archive_info()['stored_files'], 0)

    def test_clear_removes_retained_metadata_keeps_sources_and_quota_then_rebuilds_only_live_logs(self):
        sources = self.both()
        self.explicit()
        quota = self.cache / 'quota-sentinel.json'
        quota.write_text('{"invented": true}\n', encoding='utf-8')
        original = quota.read_bytes()
        generation = archive.archive_info()['clear_generation']
        cleared = archive.clear_archive()
        self.assertTrue(cleared['ok'])
        self.assertGreaterEqual(cleared['cleared_files'], 2)
        self.assertGreater(cleared['clear_generation'], generation)
        self.assertTrue(all(path.is_file() for path in sources))
        self.assertEqual(quota.read_bytes(), original)
        live, _ = self.explicit()
        self.assertEqual(self.numbers(live), (2, 350, 2))
        self.assertTrue(all(session.source_state == 'live' for session in live))
        for path in sources:
            path.unlink()
        archive.clear_archive()
        absent, details = self.explicit()
        self.assertEqual(absent, [])
        self.assertEqual(details['archive']['archive_files'], 0)
        self.assertEqual(quota.read_bytes(), original)

    def test_corrupt_archive_is_excluded_with_an_error_instead_of_inventing_a_total(self):
        source = self.codex / 'rollout-invented.jsonl'
        write_jsonl(source, codex_rows())
        self.explicit()
        source.unlink()
        (self.cache / 'metadata-archive.json').write_text('{invalid archive', encoding='utf-8')
        sessions, details = self.explicit()
        self.assertEqual(sessions, [])
        self.assertTrue(details['archive']['errors'])

    def test_old_reader_metadata_remains_visible_with_a_warning_until_the_live_source_is_reparsed(self):
        source = self.codex / 'rollout-invented.jsonl'
        rows = codex_rows()
        write_jsonl(source, rows)
        self.explicit()
        source.unlink()
        with patch('pler.usage.version', return_value='invented-updated-reader'):
            retained, details = self.explicit()
            self.assertEqual(self.numbers(retained), (1, 230, 1))
            self.assertTrue(retained[0].archive_old_parser)
            self.assertFalse(retained[0].tokens_complete)
            self.assertEqual(details['archive']['old_parser_files'], 1)
            write_jsonl(source, rows)
            refreshed, fresh_details = self.explicit()
        self.assertEqual(self.numbers(refreshed), (1, 230, 1))
        self.assertEqual(refreshed[0].source_state, 'live')
        self.assertFalse(refreshed[0].archive_old_parser)
        self.assertEqual(fresh_details['archive']['old_parser_files'], 0)

    def test_file_count_limit_evicts_whole_entries_and_reports_coverage_loss(self):
        sources = self.both()
        self.explicit()
        for source in sources:
            source.unlink()
        with patch.object(archive, 'MAX_FILES', 1):
            sessions, details = self.explicit()
            stored = archive.archive_info()
        self.assertEqual(len(sessions), 1)
        self.assertIn(total(sessions[0].tokens), (120, 230))
        self.assertEqual((details['archive']['stored_files'], details['archive']['evicted_files']), (1, 1))
        self.assertEqual(stored['stored_files'], 1)

    def test_byte_limit_bounds_the_saved_envelope_and_reports_eviction(self):
        sources = self.both()
        self.explicit()
        target = self.cache / 'metadata-archive.json'
        budget = target.stat().st_size - 1
        for source in sources:
            source.unlink()
        with patch.object(archive, 'MAX_BYTES', budget):
            sessions, details = self.explicit()
        self.assertLessEqual(target.stat().st_size, budget)
        self.assertGreaterEqual(details['archive']['evicted_files'], 1)
        self.assertLessEqual(len(sessions), 1)
        self.assertIn(sum(total(session.tokens) for session in sessions), (0, 120, 230))

    def test_age_limit_uses_last_observation_and_removes_expired_metadata(self):
        self.both()
        self.explicit()
        previous = archive.Archive()
        future = archive.Archive(now=previous.now + (archive.MAX_DAYS + 1) * 86400)
        self.assertEqual((future.info()['stored_files'], future.info()['evicted_files']), (0, 2))
        future.finish()
        self.assertEqual(archive.archive_info()['stored_files'], 0)

    def test_malformed_legacy_cache_optional_metadata_cannot_smuggle_nested_private_payloads(self):
        source = self.codex / 'rollout-removed.jsonl'
        rows = codex_rows()
        rows[0]['payload'].update(cwd=dict(text='PROMPT-CANARY'),
                                  cli_version=dict(account='ACCOUNT-CANARY'))
        rows[1]['payload'].update(model=dict(command='COMMAND-CANARY'), effort=['OUTPUT-CANARY'])
        self.cache.mkdir(parents=True)
        legacy = dict(key='invented-legacy-reader', files={str(source):dict(signature=[1,1], rows=rows,
                                                                         checksum=_checksum(rows))})
        (self.cache / 'codex.json').write_text(json.dumps(legacy), encoding='utf-8')
        original_open = Path.open
        def guard(value, *args, **kwargs):
            if value == source:
                raise AssertionError('removed source was opened')
            return original_open(value, *args, **kwargs)
        with patch.object(Path, 'open', guard):
            sessions, details = scan()
        self.assertEqual(self.numbers(sessions), (1, 230, 1))
        self.assertTrue(sessions[0].archive_old_parser)
        self.assertEqual(details['archive']['old_parser_files'], 1)
        text = (self.cache / 'metadata-archive.json').read_text(encoding='utf-8')
        for secret in PRIVATE:
            self.assertNotIn(secret, text)

    def test_unchanged_logs_neither_rebuild_nor_rewrite_the_archive(self):
        # On real logs (24 MB archive) rebuilding and rewriting it on every read took 21 s instead of 2.4 s.
        self.both()
        scan()
        target = self.cache / 'metadata-archive.json'
        before = (target.read_bytes(), target.stat().st_mtime_ns)
        with patch.object(archive, 'sanitize', side_effect=AssertionError('unchanged rows rebuilt')), \
                patch.object(archive, '_write', side_effect=AssertionError('unchanged archive rewritten')):
            sessions, details = scan()
        self.assertEqual(self.numbers(sessions), (2, 350, 2))
        self.assertEqual(details['archive']['errors'], 0)
        self.assertEqual((target.read_bytes(), target.stat().st_mtime_ns), before)
        # A changed log is still stored at once.
        write_jsonl(self.codex / 'rollout-invented.jsonl', codex_rows(amount=300))
        scan()
        self.assertNotEqual(target.read_bytes(), before[0])

    def test_folders_named_on_the_command_line_are_read_but_never_archived(self):
        from pler.usage import main
        self.both()
        with patch('sys.stdout', io.StringIO()):
            main(['--days', '0', '--json', '--claude-dir', str(self.claude), '--codex-dir', str(self.codex)])
        self.assertFalse((self.cache / 'metadata-archive.json').exists())

    def test_a_scan_loaded_before_clear_cannot_restore_the_cleared_archive_on_save(self):
        self.both()
        self.explicit()
        inflight = archive.Archive()
        self.assertEqual(inflight.info()['stored_files'], 2)
        cleared = archive.clear_archive()
        self.assertTrue(cleared['ok'])
        stale_result = inflight.finish()
        self.assertEqual(stale_result['stored_files'], 0)
        self.assertEqual(stale_result['clear_generation'], cleared['clear_generation'])
        self.assertEqual(archive.archive_info()['stored_files'], 0)


if __name__ == '__main__':
    unittest.main()
