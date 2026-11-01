"""Named work: invented titles/opaque sessions and isolated temporary metadata only."""
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from pler.usage import archive, work_items as work

A, B, C, D = (letter * 24 for letter in ('a', 'b', 'c', 'd'))


def row(identity, tokens=10, calls=1, price=0.1, **flags):
    return dict(id=identity, agent='claude-code' if identity in (A, C) else 'codex',
                total_tokens=tokens, calls=calls, api_usd=price,
                quality={name: flags.get(name, True) for name in
                         ('tokens_complete', 'calls_complete', 'attribution_complete', 'models_complete')})


class WorkItemTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.base = self.root / 'metadata'
        self.store = work.Folder(self.base)

    def create(self, title='Invented work', session=None):
        return self.store.mutate('create', title=title, session=session)['id']

    def saved(self):
        return (self.base / work.FILENAME).read_bytes()

    def test_create_rename_link_unlink_delete_and_restart_keep_only_manual_fields(self):
        self.assertEqual(self.store.read(), {})
        identity = self.create('  Ödeme hatası 🛠  ', A)
        self.assertTrue(work.CODE.fullmatch(identity))
        self.store.mutate('rename', identity=identity, title='Yeni başlık')
        self.store.mutate('link', identity=identity, session=B)
        self.store.mutate('unlink', identity=identity, session=A)
        value = work.Folder(self.base).read()[identity]
        self.assertEqual(value['title'], 'Yeni başlık')
        self.assertEqual(value['sessions'], [B])
        self.assertEqual(set(value), {'title', 'created_at', 'updated_at', 'sessions','goal','outcome','result_note','outcome_at','followups'})
        self.assertEqual(set(json.loads(self.saved())), {'format', 'items'})
        self.assertNotIn(str(self.base).encode(), self.saved())
        result = self.store.mutate('delete', identity=identity)
        self.assertEqual(result, dict(id=identity, items={}))
        self.assertEqual(work.Folder(self.base).read(), {})

    def test_repeated_link_unlink_or_same_title_does_not_rewrite_file(self):
        identity = self.create(session=A)
        before = self.saved()
        with patch.object(archive, '_write', side_effect=AssertionError('idempotent action wrote')):
            self.store.mutate('link', identity=identity, session=A)
            self.store.mutate('unlink', identity=identity, session=B)
            self.store.mutate('rename', identity=identity, title=' Invented work ')
        self.assertEqual(self.saved(), before)

    def test_invalid_actions_are_rejected_before_creating_a_folder(self):
        cases = [dict(action='create', title=''), dict(action='create', title='x' * 121),
                 dict(action='create', title='line\nbreak'), dict(action='create', title='a\x00b'),
                 dict(action='create', title='a\u2028b'), dict(action='create', title=True),
                 dict(action='create', title='x', identity=A), dict(action='create', title='x', session='../private'),
                 dict(action='link', identity=A, session=None), dict(action='link', identity=A, session=B, title='x'),
                 dict(action='delete', identity=A, session=B), dict(action='rename', identity=A, title='x', session=B),
                 dict(action='unknown', identity=A), dict(action=[], identity=A)]
        for arguments in cases:
            with self.subTest(arguments=arguments), self.assertRaises(work.WorkError):
                self.store.mutate(**arguments)
        self.assertFalse(self.base.exists())

    def test_missing_item_is_not_silently_created_or_reassigned(self):
        identity = self.create(session=A)
        before = self.saved()
        for action, extra in (('link', {'session': B}), ('unlink', {'session': A}),
                              ('rename', {'title': 'Other'}), ('delete', {})):
            with self.subTest(action=action), self.assertRaises(work.WorkError) as error:
                self.store.mutate(action, identity=D, **extra)
            self.assertEqual(error.exception.code, 'missing')
        self.assertEqual(self.saved(), before)
        self.assertIn(identity, self.store.read())

    def test_corrupt_newer_duplicate_or_extra_fields_are_preserved(self):
        self.create()
        path = self.base / work.FILENAME
        documents = [b'{broken', b'{"format":1,"format":1,"items":{}}',
                     b'{"format":4,"items":{}}', b'{"format":true,"items":{}}',
                     b'{"format":1,"items":{},"prompt":"PRIVATE"}',
                     b'{"format":1,"items":NaN}', b'[' * 300 + b']' * 300]
        for data in documents:
            with self.subTest(data=data):
                path.write_bytes(data)
                with self.assertRaises(work.WorkError): self.store.read()
                with self.assertRaises(work.WorkError): self.create('Another')
                self.assertEqual(path.read_bytes(), data)

    def test_document_validator_is_strict_and_detaches_nested_lists(self):
        identity = self.create(session=A)
        original = json.loads(self.saved())
        copied = work.validate_document(original)
        copied[identity]['sessions'].append(B)
        self.assertEqual(original['items'][identity]['sessions'], [A])
        for change in (lambda item: item.update(note='PRIVATE'), lambda item: item.update(sessions=[A, A]),
                       lambda item: item.update(created_at=True), lambda item: item.update(updated_at=-1),
                       lambda item: item.update(updated_at=1), lambda item: item.update(title=' not trimmed '),
                       lambda item: item.update(sessions=['native-provider-identity'])):
            altered = json.loads(self.saved())
            change(altered['items'][identity])
            with self.assertRaises(work.WorkError): work.validate_document(altered)

    def test_maximum_item_link_and_total_membership_limits_leave_prior_bytes(self):
        identity = self.create(session=A)
        before = self.saved()
        for setting, action in (('MAX_ITEMS', lambda: self.create('Too many')),
                                ('MAX_SESSIONS', lambda: self.store.mutate('link', identity=identity, session=B)),
                                ('MAX_MEMBERSHIPS', lambda: self.create('Too many links', B))):
            with self.subTest(setting=setting), patch.object(work, setting, 1), self.assertRaises(work.WorkError) as error:
                action()
            self.assertEqual(error.exception.code, 'limit')
            self.assertEqual(self.saved(), before)

    def test_serialized_byte_limit_is_enforced_before_write(self):
        identity = self.create(session=A)
        before = self.saved()
        with patch.object(work, 'MAX_BYTES', len(before) + 2), self.assertRaises(work.WorkError):
            self.store.mutate('rename', identity=identity, title='A much longer title')
        self.assertEqual(self.saved(), before)

    def test_oversized_file_is_rejected_before_opening_its_contents(self):
        self.base.mkdir()
        path = self.base / work.FILENAME
        path.write_bytes(b'x' * 33)
        with patch.object(work, 'MAX_BYTES', 32), patch.object(Path, 'open', side_effect=AssertionError('oversized file opened')):
            with self.assertRaises(work.WorkError) as error: self.store.read()
        self.assertEqual(error.exception.code, 'limit')

    def test_growth_after_size_observation_is_bounded_and_rejected(self):
        self.create()
        path, before = self.base / work.FILENAME, self.saved()
        opened, read_sizes = Path.open, []
        class Growing:
            def __init__(self, stream): self.stream = stream
            def __enter__(self): return self
            def __exit__(self, *args): self.stream.close()
            def fileno(self): return self.stream.fileno()
            def read(self, size):
                read_sizes.append(size)
                with opened(path, 'ab') as extra: extra.write(b' ' * 20)
                return self.stream.read(size)
        def wrapped(chosen, *args, **kwargs):
            stream = opened(chosen, *args, **kwargs)
            return Growing(stream) if chosen == path and args[:1] == ('rb',) else stream
        with patch.object(Path, 'open', wrapped), self.assertRaises(OSError): self.store.read()
        self.assertEqual(read_sizes, [len(before) + 1])

    def test_disappearance_after_observed_existence_is_not_treated_as_an_empty_file(self):
        identity = self.create(session=A)
        path, before = self.base / work.FILENAME, self.saved()
        opened = Path.open
        class Vanishing:
            def __init__(self, stream): self.stream = stream
            def __enter__(self): return self
            def __exit__(self, *args): self.stream.close();path.unlink()
            def fileno(self): return self.stream.fileno()
            def read(self, size): return self.stream.read(size)
        def wrapped(chosen, *args, **kwargs):
            stream = opened(chosen, *args, **kwargs)
            return Vanishing(stream) if chosen == path and args[:1] == ('rb',) else stream
        with patch.object(Path, 'open', wrapped), patch.object(archive, '_write', side_effect=AssertionError('missing read replaced')):
            with self.assertRaises(OSError): self.store.mutate('rename', identity=identity, title='Changed')
        self.assertFalse(path.exists())
        path.write_bytes(before)
        self.assertEqual(self.store.read()[identity]['title'], 'Invented work')

    def test_backward_clock_does_not_make_updated_older_than_created(self):
        with patch.object(work.time, 'time', return_value=100): identity = self.create()
        with patch.object(work.time, 'time', return_value=50): self.store.mutate('rename', identity=identity, title='Later')
        value = self.store.read()[identity]
        self.assertEqual((value['created_at'], value['updated_at']), (100, 100))

    def test_random_identity_collision_is_retried_without_replacing_existing_work(self):
        with patch.object(work.secrets, 'token_hex', return_value=A): self.create('First')
        with patch.object(work.secrets, 'token_hex', side_effect=[A, B]): identity = self.create('Second')
        self.assertEqual(identity, B)
        self.assertEqual(self.store.read()[A]['title'], 'First')

    def test_mutations_never_change_other_saved_metadata_or_source_files(self):
        self.base.mkdir()
        sentinels = [self.base / 'metadata-archive.json', self.base / 'claude-quota.jsonl',
                     self.base / 'session-verdicts.json', self.root / 'invented-source.jsonl']
        for path in sentinels: path.write_bytes(b'PRIVATE-SOURCE-CANARY')
        identity = self.create(session=A)
        self.store.mutate('link', identity=identity, session=B)
        self.store.mutate('delete', identity=identity)
        self.assertTrue(all(path.read_bytes() == b'PRIVATE-SOURCE-CANARY' for path in sentinels))

    def test_separate_store_instances_do_not_lose_concurrent_links(self):
        identity = self.create()
        errors = []
        def save(code):
            try: work.Folder(self.base).mutate('link', identity=identity, session=code)
            except Exception as error: errors.append(error)
        threads = [threading.Thread(target=save, args=(code,)) for code in (A, B, C, D)]
        for thread in threads: thread.start()
        for thread in threads: thread.join(5)
        self.assertFalse(errors)
        self.assertEqual(self.store.read()[identity]['sessions'], [A, B, C, D])

    def test_memory_has_the_same_behavior_without_any_filesystem_access(self):
        with patch.object(work, 'cache_file', side_effect=AssertionError('demo accessed files')), \
             patch.object(archive, '_locked', side_effect=AssertionError('demo locked files')):
            store = work.Memory()
            identity = store.mutate('create', title='Demo', session=A)['id']
            store.mutate('link', identity=identity, session=B)
            copied = store.read();copied[identity]['sessions'].append(C)
            self.assertEqual(store.read()[identity]['sessions'], [A, B])
            store.mutate('delete', identity=identity)
            self.assertEqual(store.read(), {})
        self.assertFalse(self.base.exists())


class WorkProjectionTests(unittest.TestCase):
    def store(self):
        store = work.Memory()
        first = store.mutate('create', title='API fix', session=A)['id']
        store.mutate('link', identity=first, session=B)
        second = store.mutate('create', title='Checkout', session=B)['id']
        store.mutate('link', identity=second, session=C)
        return store, first, second

    def test_multiagent_overlap_totals_use_union_not_sum_of_work_subtotals(self):
        store, first, second = self.store()
        rows = [row(A, 10, 1, .1), row(B, 20, 2, .2), row(C, 30, 3, .3), row(D, 40, 4, .4)]
        before = json.dumps(rows, sort_keys=True)
        value = work.project(store.read(), rows)
        items = {item['id']: item for item in value['items']}
        self.assertEqual((items[first]['total_tokens'], items[second]['total_tokens']), (30, 50))
        self.assertEqual((value['summary']['total_tokens'], value['summary']['calls'], value['summary']['api_usd']), (60, 6, .6))
        self.assertEqual((value['summary']['selected_sessions'], value['summary']['unassigned_sessions'],
                          value['summary']['overlapping_sessions']), (3, 1, 1))
        self.assertEqual(items[first]['overlapping_sessions'], 1)
        self.assertEqual(json.dumps(rows, sort_keys=True), before)

    def test_filter_scope_distinguishes_selected_outside_and_missing_refs(self):
        store, first, second = self.store()
        store.mutate('link', identity=first, session=D)
        value = work.project(store.read(), [row(A)], {A, B, C})
        item = next(item for item in value['items'] if item['id'] == first)
        self.assertEqual(item['session_ids'], [A, B, D])
        self.assertEqual(item['selected_session_ids'], [A])
        self.assertEqual(item['outside_session_ids'], [B])
        self.assertEqual(item['missing_session_ids'], [D])
        self.assertEqual((item['total_tokens'], item['selected_sessions'], item['outside_selection'], item['missing_sessions']), (10, 1, 1, 1))
        self.assertEqual((value['summary']['linked_sessions'], value['summary']['outside_selection'], value['summary']['missing_sessions']), (4, 2, 1))

    def test_source_moved_code_is_missing_and_never_reassigned_to_similar_new_row(self):
        store = work.Memory();identity = store.mutate('create', title='One task', session=A)['id']
        value = work.project(store.read(), [row(B, 900)], {B})
        item = value['items'][0]
        self.assertEqual(item['id'], identity)
        self.assertEqual(item['missing_session_ids'], [A])
        self.assertEqual((item['total_tokens'], item['selected_sessions']), (0, 0))
        self.assertFalse(item['tokens_complete'])
        self.assertEqual(value['summary']['unassigned_sessions'], 1)
        self.assertEqual(store.read()[identity]['sessions'], [A])

    def test_partial_usage_keeps_its_quality_flags_without_inventing_a_complete_work_total(self):
        store = work.Memory();store.mutate('create', title='Unknown usage', session=A)
        value = work.project(store.read(), [row(A, tokens_complete=False, calls_complete=False)])
        self.assertFalse(value['items'][0]['tokens_complete'])
        self.assertFalse(value['summary']['calls_complete'])
        self.assertTrue(value['summary']['models_complete'])

    def test_duplicate_selected_row_is_counted_once_but_conflicts_are_refused(self):
        store = work.Memory();store.mutate('create', title='One task', session=A)
        self.assertEqual(work.project(store.read(), [row(A), row(A)])['summary']['total_tokens'], 10)
        with self.assertRaises(work.WorkError): work.project(store.read(), [row(A), row(A, 20)])

    def test_empty_work_and_no_work_are_not_automatically_assigned(self):
        store = work.Memory();store.mutate('create', title='Empty work')
        value = work.project(store.read(), [row(A)])
        self.assertEqual((value['summary']['selected_sessions'], value['summary']['total_tokens'], value['summary']['unassigned_sessions']), (0, 0, 1))
        self.assertEqual(value['items'][0]['session_ids'], [])
        self.assertEqual(work.project({}, [row(A)])['summary']['items'], 0)

    def test_fractional_dollars_are_summed_before_rounding_and_exact_priced_tokens_are_weighted(self):
        store = work.Memory();identity = store.mutate('create', title='Partial prices', session=A)['id']
        for code in (B, C): store.mutate('link', identity=identity, session=code)
        rows = [dict(row(A, 100, price=.004), api_priced_tokens=50),
                dict(row(B, 100, price=.004), api_priced_tokens=100),
                dict(row(C, 100, price=.004), api_priced_tokens=0)]
        value = work.project(store.read(), rows)
        self.assertEqual(value['items'][0]['api_usd'], .01)
        self.assertEqual(value['summary']['api_usd'], .01)
        self.assertEqual(value['summary']['api_priced_share'], .5)
        self.assertEqual(value['items'][0]['api_priced_share'], .5)

    def test_unpriced_usage_and_no_selected_tokens_are_not_claimed_as_fully_priced(self):
        store = work.Memory();store.mutate('create', title='Unpriced', session=A)
        unpriced = work.project(store.read(), [dict(row(A, 100, price=0), api_priced_tokens=0)])
        self.assertEqual(unpriced['items'][0]['api_usd'], 0)
        self.assertEqual(unpriced['items'][0]['api_priced_share'], 0)
        self.assertIsNone(work.project(store.read(), [])['summary']['api_priced_share'])

    def test_public_share_fallback_uses_token_weight_and_exact_count_takes_precedence(self):
        store = work.Memory();identity = store.mutate('create', title='Public rows', session=A)['id']
        store.mutate('link', identity=identity, session=B)
        rows = [dict(row(A, 100), api_priced_share=.25),
                dict(row(B, 300), api_priced_share=1.0, api_priced_tokens=0)]
        self.assertEqual(work.project(store.read(), rows)['summary']['api_priced_share'], .0625)


if __name__ == '__main__':
    unittest.main()
