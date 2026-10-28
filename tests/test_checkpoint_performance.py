"""Snapshot selection stays exact while long checkpoint histories require only linear comparisons."""
import itertools
import random
import unittest

from pler.usage.accounting import largest
from pler.usage.records import TOKEN_FIELDS, empty_tokens


def snapshot(incoming=0, output=0, **extra):
    return dict(empty_tokens(), input=incoming, output=output, **extra)


def brute_force(values):
    """Independent all-pairs specification: return a real record dominating all retained records."""
    records = {}
    for value in values:
        records[tuple(value[key] for key in TOKEN_FIELDS)] = value
    for candidate in records.values():
        if all(all(candidate[key] >= other[key] for key in TOKEN_FIELDS) for other in records.values()):
            return candidate
    return None


class CountedInt(int):
    """Count field comparisons, including those inside tuple ordering; no timing assertion is needed."""
    comparisons = 0
    __hash__ = int.__hash__

    def __eq__(self, other):
        CountedInt.comparisons += 1
        return int.__eq__(self, other)

    def __gt__(self, other):
        CountedInt.comparisons += 1
        return int.__gt__(self, other)

    def __ge__(self, other):
        CountedInt.comparisons += 1
        return int.__ge__(self, other)


class CheckpointSelectionTests(unittest.TestCase):
    def test_empty_and_one_pass_iterables(self):
        self.assertIsNone(largest([]))
        self.assertIsNone(largest(iter(())))
        record = snapshot(10, 5)
        self.assertIs(largest(value for value in [record]), record)

    def test_duplicate_vectors_keep_the_last_original_record(self):
        first, last = snapshot(10, 5, marker='first'), snapshot(10, 5, marker='last')
        self.assertIs(largest([first, snapshot(1, 1), last]), last)

    def test_crossing_vectors_cannot_manufacture_a_snapshot(self):
        left, right = snapshot(100, 1), snapshot(1, 100)
        self.assertIsNone(largest([left, right]))
        actual = snapshot(100, 100)
        self.assertIs(largest([left, right, actual]), actual)
        self.assertIs(largest([actual, right, left]), actual)

    def test_small_vector_sequences_match_the_all_pairs_specification(self):
        vectors = [(0, 0), (1, 0), (0, 1), (1, 1)]
        for length in range(5):
            for coordinates in itertools.product(vectors, repeat=length):
                records = [snapshot(a, b, marker=index) for index, (a, b) in enumerate(coordinates)]
                self.assertIs(largest(iter(records)), brute_force(records))

    def test_deterministic_five_field_samples_match_the_all_pairs_specification(self):
        rng = random.Random(20261028)
        for trial in range(150):
            records = [{key: rng.randrange(30) for key in TOKEN_FIELDS} for _ in range(rng.randrange(1, 13))]
            if trial % 2:
                records.append({key: max(record[key] for record in records) + rng.randrange(2) for key in TOKEN_FIELDS})
            records.append(dict(records[rng.randrange(len(records))]))
            rng.shuffle(records)
            self.assertIs(largest(value for value in records), brute_force(records))

    def test_iterable_mutation_keeps_selection_based_on_actual_record_values(self):
        first, second = snapshot(1, 1), snapshot(2, 2)
        def changing():
            yield first
            first.update(input=5, output=5)
            yield second
        self.assertIs(largest(changing()), first)

    def test_monotone_histories_do_not_return_to_pairwise_field_comparisons(self):
        for size in (64, 128):
            with self.subTest(size=size):
                records = [{key: CountedInt(index if key == 'output' else 0) for key in TOKEN_FIELDS}
                           for index in range(size)]
                CountedInt.comparisons = 0
                self.assertIs(largest(iter(records)), records[-1])
                # Allows several linear passes; the previous all-pairs implementation exceeds this bound.
                self.assertLessEqual(CountedInt.comparisons, 24 * size)


if __name__ == '__main__':
    unittest.main()
