"""Bound Git traversal before materializing paths; accept only bounded, coherent saved counts."""
from collections import Counter
import io
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pler import git_survival as rules
from pler.runtime import ScanCancelled, cancellation


def tree_body(entries):
    return b''.join((b'40000' if folder else b'100644') + b' ' + name + b'\0' + bytes.fromhex(key)
                    for name, folder, key in entries)


def reader_for(trees, on_read=None):
    reader = rules._Reader.__new__(rules._Reader)
    reader.size = 20
    reader.trees, reader.files, reader.spent = {}, {}, 0
    reader.entries = reader.visits = 0
    reader.limited = False
    reads = []
    def get(key):
        reads.append(key.hex())
        if on_read is not None:
            on_read()
        return (2, trees[key.hex()]) if key.hex() in trees else None
    reader.store = SimpleNamespace(_object=get)
    return reader, reads


class SavedCountSafetyTests(unittest.TestCase):
    def test_a_file_growing_after_stat_is_read_only_through_the_observed_size(self):
        requested = []
        class Stream(io.BytesIO):
            def read(self, size=-1):
                requested.append(size)
                return super().read(size)
        class Growing:
            def stat(self):return SimpleNamespace(st_size=2)
            def open(self, mode):return Stream(b' '*200 + b'{}')
        with patch.object(rules.Saved, '_path', return_value=Growing()), \
                patch.object(rules.json, 'loads', side_effect=AssertionError('changing file parsed')):
            self.assertEqual(rules.Saved().load(), {})
        self.assertEqual(requested, [3])

    def test_known_oversized_file_is_not_opened(self):
        class Oversized:
            def stat(self):return SimpleNamespace(st_size=rules.Saved.MAX_SIZE + 1)
            def open(self, mode):raise AssertionError('oversize file opened')
        with patch.object(rules.Saved, '_path', return_value=Oversized()):
            self.assertEqual(rules.Saved().load(), {})

    def test_saved_counts_reject_impossible_relations_and_invalid_roots(self):
        key, other = 'a'*64, 'b'*64
        good = dict(format=1, version=rules._version(), counts={key: [3, 2, 1, 0]})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/rules.Saved.FILENAME
            for bad in ([1, 2, 1, 0], [0, 1, 0, 0], [1, True, 1, 0], [1, -1, 1, 0],
                        [1, 1, 1 << 53, 0], [1, 1, 1]):
                value = dict(good, counts={key: good['counts'][key], other: bad})
                path.write_text(json.dumps(value), 'utf-8')
                self.assertEqual(rules.Saved(folder).load(), {key: dict(added=3, kept=2, files=1, skipped=0)})
            for value in ([], None, 1, {'format': True, 'version': rules._version(), 'counts': {}},
                          dict(good, counts=[]), dict(good, format=2)):
                path.write_text(json.dumps(value), 'utf-8')
                self.assertEqual(rules.Saved(folder).load(), {})

    def test_save_never_writes_a_body_beyond_its_read_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            saved = rules.Saved(folder)
            value = {'a'*64: dict(added=3, kept=2, files=1, skipped=0)}
            with patch.object(rules.Saved, 'MAX_SIZE', 32):
                saved.save(value)
            self.assertFalse((Path(folder)/rules.Saved.FILENAME).exists())


class TraversalSafetyTests(unittest.TestCase):
    def test_flat_tree_entry_budget_stops_parsing_early(self):
        tip, blob = '1'*40, 'f'*40
        reader, reads = reader_for({tip: tree_body([(str(n).encode(), False, blob) for n in range(10)])})
        with patch.object(rules, 'MAX_ENTRIES', 2), self.assertRaises(rules._LimitExceeded):
            list(reader.changed(None, tip))
        self.assertEqual((reader.entries, len(reads)), (2, 1))

    def test_deep_trees_are_iterative_and_stop_before_the_depth_budget(self):
        keys = [str(n)*40 for n in range(1, 7)]
        trees = {key: tree_body([(b'child', True, keys[n+1])]) for n, key in enumerate(keys[:-1])}
        trees[keys[-1]] = tree_body([(b'file.py', False, 'f'*40)])
        reader, reads = reader_for(trees)
        with patch.object(rules, 'MAX_TREE_DEPTH', 2), self.assertRaises(rules._LimitExceeded):
            list(reader.changed(None, keys[0]))
        self.assertEqual(len(reads), 3)

    def test_distinct_tree_budget_is_enforced_before_loading_another_object(self):
        keys = [str(n)*40 for n in range(1, 5)]
        trees = {key: tree_body([(b'child', True, keys[n+1])]) for n, key in enumerate(keys[:-1])}
        trees[keys[-1]] = tree_body([(b'file.py', False, 'f'*40)])
        reader, reads = reader_for(trees)
        with patch.object(rules, 'MAX_TREES', 2), self.assertRaises(rules._LimitExceeded):
            list(reader.changed(None, keys[0]))
        self.assertEqual(len(reads), 2)

    def test_repeated_cached_subtrees_still_spend_a_traversal_visit_budget(self):
        root, child, blob = '1'*40, '2'*40, 'f'*40
        trees = {root: tree_body([(str(n).encode(), True, child) for n in range(4)]),
                 child: tree_body([(b'file.py', False, blob)])}
        reader, reads = reader_for(trees)
        with patch.object(rules, 'MAX_ENTRIES', 6), self.assertRaises(rules._LimitExceeded):
            list(reader.changed(None, root))
        self.assertEqual(reader.visits, 6)
        self.assertEqual(len(reads), 2)

    def test_cancel_during_an_object_read_propagates_without_becoming_a_count(self):
        event = threading.Event()
        key = '1'*40
        reader, _ = reader_for({key: tree_body([(b'a.py', False, 'f'*40)])}, event.set)
        with cancellation(event), self.assertRaises(ScanCancelled):
            list(reader.changed(None, key))

    def test_blob_admission_never_overshoots_the_total_byte_budget(self):
        reader, _ = reader_for({})
        reader.store = SimpleNamespace(_object=lambda key: (3, b'VALUE = 1\n'))
        with patch.object(rules, 'MAX_BYTES', 4):
            self.assertIsNone(reader.lines('1'*40))
        self.assertEqual(reader.spent, 0)
        self.assertTrue(reader.limited)

    def test_file_budget_reads_one_sentinel_instead_of_materializing_the_tail(self):
        consumed = []
        instance = None
        class Reader:
            def __init__(self, directory, size):
                nonlocal instance
                instance = self
                self.store = SimpleNamespace(base='invented')
                self.limited, self.spent = False, 0
            def close(self):pass
            def commit(self, key):return ('tree', ['parent'])
            def changed(self, old, new):
                for n in range(10000):
                    consumed.append(n)
                    yield (b'file.py',), None, 'blob'
            def lines(self, key):return Counter({'VALUE = 1': 1})
            def find(self, tree, parts):return 'blob'
            def limit(self):
                self.limited = True
                raise rules._LimitExceeded('limit')
        rules._MEMO.clear()
        commit = '1'*40
        with patch.object(rules, '_Reader', Reader), patch.object(rules, 'head', return_value='2'*40), \
                patch.object(rules, 'on_branch', return_value={commit: True}), patch.object(rules, 'MAX_FILES', 2):
            self.assertEqual(rules.survival('invented', [commit]), {commit: None})
        self.assertEqual(consumed, [0, 1, 2])
        self.assertTrue(instance.limited)
        self.assertEqual(rules._MEMO, {})


if __name__ == '__main__':unittest.main()
