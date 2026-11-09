"""Physical log moves and annotation safety. Invented sources and isolated metadata only."""
import json
import os
from pathlib import Path
import shutil
from unittest.mock import patch

from pler.dashboard import UsageDashboard
from pler.usage import Rescan, scan, archive, identities, budgets, backup, verdicts, work_items
from pler.usage.records import Session, total
from test_adoption_api import IsolatedMetadata, join_scan
from test_archive import codex_rows, claude_rows
from test_logs import write_jsonl


class SessionIdentityTests(IsolatedMetadata):
    def seed(self, agent='codex', name='a', retain=False, amount=80):
        self.assertTrue(archive.set_retention(retain)['ok'])
        folder = self.codex if agent == 'codex' else self.claude
        path = folder / (('rollout-' if agent == 'codex' else '')+name+'.jsonl')
        rows = codex_rows('identity-invented', amount, 0) if agent == 'codex' else claude_rows('identity-invented', amount, 0)
        write_jsonl(path, rows)
        if not identities.sample([path]):
            self.skipTest('This filesystem does not expose the required local file birth/identity proof')
        return path

    def move(self, source, target, replace=False):
        root = self.root.resolve()
        for path in (source.resolve(), target.resolve()):
            self.assertIn(root, path.parents, 'move must stay inside this invented fixture')
        target.parent.mkdir(parents=True, exist_ok=True)
        (os.replace if replace else os.rename)(str(source), str(target))
        return target

    def board(self):
        board = UsageDashboard(git_reader=lambda _: dict(state='not_repository'))
        board.budgets.autostart = False
        self.addCleanup(board.close)
        board.refresh(); join_scan(board)
        self.assertEqual(board.state, 'ready')
        return board

    def refresh(self, board):
        board.refresh(); join_scan(board)
        self.assertEqual(board.state, 'ready')
        return board.view(days=0)

    def test_real_rename_keeps_original_code_for_both_agents_and_reload(self):
        for agent in ('codex', 'claude-code'):
            with self.subTest(agent=agent):
                path = self.seed(agent)
                sessions, _ = scan(); row = next(s for s in sessions if s.agent == agent)
                original = verdicts.session_code(row)
                moved = self.move(path, path.parent / ('rollout-z.jsonl' if agent == 'codex' else 'z.jsonl'))
                after, sources = scan()
                row = next(s for s in after if s.agent == agent)
                self.assertNotEqual(verdicts.source_code(row), original)
                self.assertEqual(verdicts.session_code(row), original)
                self.assertEqual(row._pler_identity_state, 'preserved')
                again, _ = scan(memo=Rescan())
                self.assertEqual(verdicts.session_code(next(s for s in again if s.agent == agent)), original)
                registry = (self.cache/identities.FILENAME).read_text(encoding='utf-8')
                self.assertNotIn(str(path), registry)
                self.assertNotIn('identity-invented', registry)

    def test_work_review_and_notified_budget_survive_move_with_retained_old_name(self):
        path = self.seed(retain=True)
        board = self.board(); row = board.sessions[0]; code = verdicts.session_code(row)
        work = board.mutate_work_item('create', title='Invented work', session=code)['id']
        self.assertTrue(board.set_verdict(code, 'useful')['ok'])
        self.assertTrue(board.set_budget(code, 'tokens', 100, None)['ok'])
        board.budgets.tick(); budget = board.budget_view()['items'][0]
        self.assertEqual(budget['level'], 80)
        self.assertTrue(board.ack_budget(code, budget['revision'], 80)['ok'])
        before = {name:(self.cache/name).read_bytes() for name in (work_items.FILENAME, verdicts.FILENAME, budgets.FILENAME)}
        moved = self.move(path, path.parent/'rollout-z.jsonl')
        value = self.refresh(board)
        self.assertEqual(value['sessions'][0]['id'], code)
        self.assertEqual(value['sessions'][0]['verdict'], 'useful')
        self.assertEqual(value['work_items']['items'][0]['id'], work)
        self.assertEqual(value['work_items']['items'][0]['missing_sessions'], 0)
        self.assertTrue(getattr(board.sessions[0], '_pler_live_sources', None))
        board.budgets.tick(); current = board.budget_view()['items'][0]
        self.assertEqual(current['state'], 'watching')
        self.assertEqual(current['notified'], [80]); self.assertEqual(current['pending_level'], 0)
        for name, content in before.items(): self.assertEqual((self.cache/name).read_bytes(), content)
        reopened = self.board(); reopened.budgets.tick()
        self.assertEqual(reopened.budget_view()['items'][0]['pending_level'], 0)
        write_jsonl(moved, codex_rows('identity-invented', 110, 0))
        reopened.budgets.tick()
        self.assertEqual(reopened.budget_view()['items'][0]['pending_level'], 100)
        self.assertEqual(total(reopened.sessions[0].tokens), 80)  # monitor is independent of the old UI snapshot

    def test_a_copy_seen_beside_the_original_does_not_inherit_after_original_disappears(self):
        path = self.seed()
        first, _ = scan(); original = verdicts.session_code(first[0])
        verdicts.save(original, 'useful')
        copy = path.parent/'rollout-z.jsonl'; shutil.copy2(path, copy)
        together, _ = scan(); self.assertEqual(verdicts.session_code(together[0]), original)
        parked = self.move(path, self.root/'parked.jsonl')
        rows, _ = scan()
        self.assertNotEqual(verdicts.session_code(rows[0]), original)
        self.assertEqual(rows[0]._pler_identity_state, 'unverified')
        self.assertEqual(verdicts.read(), {original:'useful'})
        self.assertEqual(total(rows[0].tokens), 80)

    def test_replacing_same_path_and_native_id_cannot_take_previous_annotation(self):
        path = self.seed(); first, _ = scan(); original = verdicts.session_code(first[0])
        replacement = self.root/'replacement.jsonl'
        write_jsonl(replacement, codex_rows('identity-invented', 80, 0))
        self.move(replacement, path, replace=True)
        rows, _ = scan(); new = verdicts.session_code(rows[0])
        self.assertNotEqual(new, original)
        again, _ = scan(); self.assertEqual(verdicts.session_code(again[0]), new)

    def test_two_previously_distinct_physical_owners_cannot_share_annotations(self):
        path = self.seed(); first, _ = scan(); old = verdicts.session_code(first[0])
        copy = path.parent/'rollout-z.jsonl'; shutil.copy2(path, copy)
        parked = self.move(path, self.root/'parked.jsonl')
        second, _ = scan(); other = verdicts.session_code(second[0]); self.assertNotEqual(other, old)
        self.move(parked, path)
        both, details = scan()
        self.assertEqual(len(both), 1)  # existing accounting reconciliation; no new session merge here
        self.assertNotIn(verdicts.session_code(both[0]), (old, other))
        self.assertEqual(both[0]._pler_identity_state, 'conflict')
        self.assertEqual(details['identity']['conflicts'], 1)

    def test_corrupt_registry_keeps_previous_dashboard_and_annotation_files(self):
        self.seed(); board = self.board(); before = board.view(days=0)
        registry = self.cache/identities.FILENAME; registry.write_bytes(b'{private-invalid-canary')
        board.refresh(); join_scan(board)
        self.assertEqual(board.state, 'error'); self.assertEqual(board.error, 'error.session_identity')
        after = board.view(days=0)
        self.assertEqual(after['sessions'], before['sessions'])
        self.assertNotIn('canary', after['error'])
        self.assertEqual(registry.read_bytes(), b'{private-invalid-canary')

    def test_backup_restores_registry_and_budget_for_the_same_local_source(self):
        path = self.seed(); board = self.board(); code = verdicts.session_code(board.sessions[0])
        board.mutate_work_item('create', title='Invented backup work', session=code)
        board.set_verdict(code, 'useful'); board.set_budget(code, 'tokens', 100, None)
        board.budgets.tick(); row = board.budget_view()['items'][0]; board.ack_budget(code, row['revision'], 80)
        data = backup.create(); restored = self.root/'restored'
        backup.restore(data, restored)
        self.assertTrue((restored/identities.FILENAME).is_file()); self.assertTrue((restored/budgets.FILENAME).is_file())
        self.move(path, path.parent/'rollout-z.jsonl')
        with patch.dict(os.environ, PLER_CACHE_DIR=str(restored)):
            second = self.board(); value = second.view(days=0); second.budgets.tick()
            self.assertEqual(value['sessions'][0]['id'], code); self.assertEqual(value['sessions'][0]['verdict'], 'useful')
            self.assertEqual(value['work_items']['summary']['missing_sessions'], 0)
            self.assertEqual(second.budget_view()['items'][0]['pending_level'], 0)

    def test_changed_native_identity_on_the_same_file_is_distinct(self):
        path = self.seed(); first, _ = scan(); original = verdicts.session_code(first[0])
        write_jsonl(path, codex_rows('different-invented-provider', 80, 0))
        rows, _ = scan(); self.assertNotEqual(verdicts.session_code(rows[0]), original)

    def test_network_sampling_never_probes_a_remote_or_wsl_path(self):
        with patch.object(identities.discovery, 'local', side_effect=AssertionError('network probe')):
            self.assertEqual(identities.sample(['//server/log.jsonl', r'\\wsl.localhost\Invented\log.jsonl']), {})

    def test_growth_during_read_keeps_known_identity_without_enrolling_new_proofs(self):
        path = self.seed(); before = identities.sample([path]); sessions, _ = scan()
        code = verdicts.session_code(sessions[0]); changed = dict(before)
        changed[str(path)] = (*before[str(path)][:3], before[str(path)][3]+10, before[str(path)][4]+1)
        status = identities.bind(sessions, before, changed)
        self.assertEqual(verdicts.session_code(sessions[0]), code)
        fresh = self.root/'fresh-identity-cache'
        identities.bind(sessions, before, changed, fresh)
        self.assertFalse((fresh/identities.FILENAME).exists())

    def test_registry_limit_does_not_drop_existing_proofs_or_claim_new_move_support(self):
        path = self.seed(); first, _ = scan(); original = verdicts.session_code(first[0])
        other = path.parent/'rollout-new.jsonl'; write_jsonl(other, codex_rows('new-provider', 80, 0, response='new-response'))
        with patch.object(identities, 'MAX_ENTRIES', 1):
            rows, details = scan()
        self.assertTrue(details['identity']['limit_reached'])
        self.assertEqual(verdicts.session_code(next(s for s in rows if s.session_id == 'identity-invented')), original)
        self.assertEqual(len(identities.validate((self.cache/identities.FILENAME).read_bytes())), 1)

    def test_explicit_non_retained_scan_does_not_create_identity_preferences(self):
        path = self.codex/'rollout-a.jsonl'; write_jsonl(path, codex_rows())
        scan([self.claude], [self.codex])
        self.assertFalse((self.cache/identities.FILENAME).exists())

    def test_retained_copy_coverage_requires_every_usage_record_in_the_live_original(self):
        for agent in ('codex', 'claude-code'):
            with self.subTest(agent=agent):
                path = self.seed(agent, retain=True)
                board = self.board(); original = next(s for s in board.sessions if s.agent == agent)
                code = verdicts.session_code(original)
                board.set_budget(code, 'tokens', 100000, None)
                copy = path.parent/('rollout-copy.jsonl' if agent == 'codex' else 'copy.jsonl')
                extra = (codex_rows('identity-invented', 20, 0, response='extra-response')[-1:]
                         if agent == 'codex' else claude_rows('identity-invented', 20, 0, message='extra-message', request='extra-request'))
                base = (codex_rows('identity-invented', 80, 0) if agent == 'codex' else claude_rows('identity-invented', 80, 0))
                write_jsonl(copy, base+extra); self.refresh(board)
                copy.unlink(); self.refresh(board); board.budgets.tick()
                watched = next(r for r in board.budget_view()['items'] if r['id'] == code)
                self.assertEqual(watched['state'], 'archive')  # one reply exists only in retained metadata
                write_jsonl(path, base+extra); self.refresh(board); board.budgets.tick()
                watched = next(r for r in board.budget_view()['items'] if r['id'] == code)
                self.assertEqual(watched['state'], 'watching')
                self.assertEqual(watched['amount'], 100)

    def test_archive_copy_with_different_model_is_not_alert_coverage(self):
        path = self.seed(retain=True)
        rows = codex_rows('identity-invented', 80, 0); rows[1]['payload']['model'] = 'gpt-6.1-sol'
        write_jsonl(path, rows); board = self.board(); code = verdicts.session_code(board.sessions[0])
        board.set_budget(code, 'tokens', 100000, None)
        copy = path.parent/'rollout-copy.jsonl'
        rows[1]['payload']['model'] = 'gpt-6-astra'; write_jsonl(copy, rows)
        self.refresh(board); copy.unlink(); self.refresh(board); board.budgets.tick()
        self.assertEqual(board.budget_view()['items'][0]['state'], 'archive')

    def test_registry_disappearing_mid_read_is_not_an_empty_new_registry(self):
        self.seed(); scan(); registry = self.cache/identities.FILENAME
        before = registry.read_bytes(); original = Path.stat; calls = []
        def changing(path, *args, **kwargs):
            if path == registry:
                calls.append(path)
                if len(calls) > 1: raise FileNotFoundError('invented race')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'stat', changing), self.assertRaises(identities.IdentityError):
            identities._read(registry)
        self.assertEqual(registry.read_bytes(), before)

    def test_uncertain_retained_snapshot_cannot_be_complete_from_live_totals_alone(self):
        path = self.seed(retain=True)
        rows = codex_rows('identity-invented', 80, 0); rows[1]['payload']['model'] = 'gpt-6.1-sol'
        write_jsonl(path, rows); board = self.board(); code = verdicts.session_code(board.sessions[0])
        self.move(path, path.parent/'rollout-z.jsonl'); self.refresh(board)
        session = board.sessions[0]; self.assertTrue(session._pler_live_sources)
        session.tokens_complete = False
        board.set_budget(code, 'tokens', 100, None); board.budgets.tick()
        row = board.budget_view()['items'][0]
        self.assertEqual(row['state'], 'partial'); self.assertEqual(row['pending_level'], 0)
        session.tokens_complete = True; session.models_complete = False; session.api_priced_tokens = 0
        board.set_budget(code, 'usd', .0001, row['revision']); board.budgets.tick()
        row = board.budget_view()['items'][0]
        self.assertEqual(row['state'], 'partial'); self.assertEqual(row['pending_level'], 0)

    def test_budget_cannot_follow_a_replaced_file_before_the_next_full_refresh(self):
        path = self.seed(); board = self.board(); code = verdicts.session_code(board.sessions[0])
        board.set_budget(code, 'tokens', 100, None); board.budgets.tick()
        replacement = self.root/'replacement.jsonl'
        write_jsonl(replacement, codex_rows('identity-invented', 1000, 0))
        self.move(replacement, path, replace=True)
        board.budgets.tick(); row = board.budget_view()['items'][0]
        self.assertEqual(row['state'], 'read_error'); self.assertEqual(row['pending_level'], 0)
