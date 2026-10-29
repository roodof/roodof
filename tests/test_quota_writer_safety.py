"""Bounded quota input and shared-writer exclusion using only invented local numbers."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from pler import statusline


class QuotaWriterSafetyTests(unittest.TestCase):
    def test_another_process_cannot_append_during_a_prune_transaction(self):
        # A writer owns the same OS lock across reading old samples and replacing the journal.
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            first = {'300': [10, 2000]}
            second = {'300': [20, 2000]}
            self.assertTrue(statusline.record(first, base, now=1000))
            program = (
                "import json,sys;sys.path.insert(0,sys.argv[1]);"
                "from pler import statusline;statusline.LOCK_WAIT=.05;"
                "print(json.dumps(statusline.record({'300':[20,2000]},sys.argv[2],now=1001)))"
            )
            with statusline._quota_locked(base):
                child = subprocess.run([sys.executable, '-I', '-c', program,
                                        str(Path(statusline.__file__).resolve().parent.parent), str(base)],
                                       capture_output=True, timeout=10)
                self.assertEqual(child.returncode, 0, child.stderr)
                self.assertIs(json.loads(child.stdout), False)
                self.assertEqual([row[2] for row in statusline.samples(base)], [10])
            with (base / statusline.FILE).open('ab') as stream:
                stream.write(b' ' * 200 + b'\n')
            with patch.object(statusline, 'PRUNE_BYTES', 120):
                self.assertTrue(statusline.record(second, base, now=1001))
            self.assertEqual([row[2] for row in statusline.samples(base)], [10, 20])

    def test_concurrent_completed_writers_survive_repeated_pruning(self):
        with tempfile.TemporaryDirectory() as folder:
            barrier = threading.Barrier(3)
            completed = []
            def worker(used):
                barrier.wait()
                completed.append(statusline.record({'300': [used, 2000]}, folder, now=1000 + used))
            with patch.object(statusline, 'PRUNE_BYTES', 120), patch.object(statusline, 'LOCK_WAIT', 3):
                workers = [threading.Thread(target=worker, args=(used,)) for used in (10, 20)]
                for worker in workers:
                    worker.start()
                barrier.wait()
                for worker in workers:
                    worker.join(5)
                    self.assertFalse(worker.is_alive())
            self.assertEqual(completed, [True, True])
            self.assertEqual({row[2] for row in statusline.samples(folder)}, {10, 20})

    def test_unterminated_broken_tail_cannot_swallow_a_new_sample(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / statusline.FILE
            path.write_bytes(b'{"partial":')
            self.assertTrue(statusline.record({'300': [30, 2000]}, folder, now=1000))
            self.assertEqual([row[2] for row in statusline.samples(folder)], [30])

    def test_long_and_deep_rows_do_not_hide_later_valid_samples(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / statusline.FILE
            good = json.dumps(dict(at=1000, windows={'300': [30, 2000]})).encode() + b'\n'
            path.write_bytes(b'x' * (statusline.MAX_LINE_BYTES * 4) + b'\n' +
                             b'[' * 1000 + b'0' + b']' * 1000 + b'\n' + good)
            self.assertEqual([row[2] for row in statusline.samples(folder)], [30])

    def test_tail_read_and_retained_samples_have_hard_bounds(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / statusline.FILE
            path.write_bytes(b'not-json\n' * 100 + b''.join(
                json.dumps(dict(at=1000 + i, windows={'300': [i, 2000]})).encode() + b'\n'
                for i in range(20)))
            real_open = Path.open
            consumed, requested = [], []
            class CheckedStream:
                def __init__(self, stream): self.stream = stream
                def __enter__(self): self.stream.__enter__(); return self
                def __exit__(self, *args): return self.stream.__exit__(*args)
                def seek(self, *args): return self.stream.seek(*args)
                def readline(self, size):
                    requested.append(size)
                    value = self.stream.readline(size); consumed.append(len(value)); return value
            def checked_open(target, *args, **kwargs):
                stream = real_open(target, *args, **kwargs)
                return CheckedStream(stream) if target == path else stream
            with patch.object(statusline, 'MAX_JOURNAL_BYTES', 600), \
                    patch.object(statusline, 'MAX_KEPT_ROWS', 3), patch.object(Path, 'open', checked_open):
                found = statusline.samples(folder)
            self.assertLessEqual(sum(consumed), 600)
            self.assertLessEqual(max(requested), statusline.MAX_LINE_BYTES + 1)
            self.assertLessEqual(len(found), 6)
            self.assertEqual(found[-1][2], 19)

    def test_prune_caps_recent_history_by_count_and_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / statusline.FILE
            path.write_text(''.join(json.dumps(dict(at=1000 + i, windows={'300': [i, 2000]})) + '\n'
                                    for i in range(20)), 'utf-8')
            with patch.object(statusline, 'PRUNE_BYTES', 200), patch.object(statusline, 'MAX_KEPT_ROWS', 2):
                self.assertTrue(statusline.record({'300': [90, 2000]}, folder, now=1100))
                self.assertLessEqual(path.stat().st_size, 200)
                rows = statusline.samples(folder)
            self.assertLessEqual(len(rows), 2)
            self.assertEqual(rows[-1][2], 90)

    def test_unsafe_or_busy_lock_never_appends(self):
        with tempfile.TemporaryDirectory() as folder:
            original = statusline.cache_file
            def safe_file(name, base=None):
                return None if name == statusline.LOCKFILE else original(name, base)
            with patch.object(statusline, 'cache_file', safe_file):
                self.assertFalse(statusline.record({'300': [10, 2000]}, folder, now=1000))
            self.assertFalse((Path(folder) / statusline.FILE).exists())

    def test_status_input_is_read_with_an_explicit_bound_and_never_persisted(self):
        class Input:
            def __init__(self): self.requested = []; self.buffer = self
            def read(self, size): self.requested.append(size); return b'x' * size
        class Output:
            def __init__(self): self.buffer = io.BytesIO()
            def flush(self): pass
        source, output = Input(), Output()
        with patch.object(statusline, 'MAX_INPUT_BYTES', 64), patch.object(sys, 'stdin', source), \
                patch.object(sys, 'stdout', output), patch.object(statusline, 'record') as record:
            self.assertEqual(statusline.main([]), 0)
        self.assertEqual(source.requested, [65])
        self.assertEqual(output.buffer.getvalue(), b'PLER')
        record.assert_called_once_with({})

    def test_invalid_times_remain_best_effort(self):
        with tempfile.TemporaryDirectory() as folder:
            for invalid in (True, float('nan'), float('inf'), -1, 10**1000, 'invalid'):
                self.assertFalse(statusline.record({'300': [10, 2000]}, folder, now=invalid))

