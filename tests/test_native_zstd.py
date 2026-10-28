"""Run the real installed native decoder against independent checked-in reference bytes.

These are skipped when only the plain-Python reader is available. Mocked API tests cannot establish that
an actual native library rejects a truncated frame or consumes every concatenated frame.
"""
from pathlib import Path
import tempfile
import unittest

from pler.usage import codex, zstd
from pler.usage.records import total
from test_logs import ZSTD_FILES, ZSTD_SAMPLES, codex_rows, stored_zstd, write_jsonl


class NativeZstdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        decoder, cls.decoder_name = zstd.decoder()
        if cls.decoder_name == 'plain python':
            raise unittest.SkipTest('No native zstd decoder is installed; fallback tests run separately')
        cls.decode = staticmethod(decoder)

    def test_reference_corpus_matches_independently_generated_original_bytes(self):
        files = sorted(ZSTD_FILES.glob('*.zst'))
        self.assertGreaterEqual(len(files), 13)
        for path in files:
            with self.subTest(decoder=self.decoder_name, fixture=path.name):
                self.assertEqual(self.decode(path.read_bytes()), ZSTD_SAMPLES[path.name.split('-')[0]]())

    def test_concatenated_and_skippable_frames_are_fully_consumed(self):
        skip = (0x184D2A53).to_bytes(4, 'little') + (5).to_bytes(4, 'little') + b'xxxxx'
        tiny = (ZSTD_FILES / 'tiny-3.zst').read_bytes()
        log = (ZSTD_FILES / 'log-19.zst').read_bytes()
        expected = ZSTD_SAMPLES['tiny']() + ZSTD_SAMPLES['log']()
        self.assertEqual(self.decode(skip + tiny + skip + log + skip), expected)
        self.assertEqual(self.decode(skip), b'')
        self.assertEqual(self.decode(stored_zstd(b'')), b'')

    def test_every_truncation_of_a_raw_frame_is_rejected(self):
        frame = stored_zstd(b'not a transcript')
        for end in range(len(frame)):
            with self.subTest(decoder=self.decoder_name, end=end), self.assertRaises(ValueError):
                self.decode(frame[:end])
        self.assertEqual(self.decode(frame), b'not a transcript')

    def test_missing_or_wrong_checksums_are_rejected(self):
        checked = 0
        for path in sorted(ZSTD_FILES.glob('*.zst')):
            data = path.read_bytes()
            if not data[4] & 4:
                continue
            checked += 1
            for broken in (data[:-1], data[:-4], data[:-1] + bytes([data[-1] ^ 1])):
                with self.subTest(fixture=path.name, bytes=len(broken)), self.assertRaises(ValueError):
                    self.decode(broken)
        self.assertGreaterEqual(checked, 5)

    def test_wrong_declared_content_size_is_rejected(self):
        frame = stored_zstd(b'abc')
        for size in (0, 2, 4, 10**9):
            damaged = frame[:5] + size.to_bytes(8, 'little') + frame[13:]
            with self.subTest(size=size), self.assertRaises(ValueError):
                self.decode(damaged)

    def test_truncated_skippable_frame_is_rejected(self):
        frame = (0x184D2A53).to_bytes(4, 'little') + (5).to_bytes(4, 'little') + b'abcde'
        for end in range(len(frame)):
            with self.subTest(end=end), self.assertRaises(ValueError):
                self.decode(frame[:end])

    def test_incomplete_second_frame_or_trailing_garbage_is_rejected(self):
        one = (ZSTD_FILES / 'tiny-3.zst').read_bytes()
        two = (ZSTD_FILES / 'log-3.zst').read_bytes()
        for tail in (two[:-1], two[:5], b'garbage', b'\x00'):
            with self.subTest(tail_length=len(tail)), self.assertRaises(ValueError):
                self.decode(one + tail)

    def test_reserved_frame_header_is_rejected(self):
        frame = stored_zstd(b'abc')
        with self.assertRaises(ValueError):
            self.decode(frame[:4] + bytes([frame[4] | 8]) + frame[5:])

    def test_damaged_compressed_log_warns_while_other_usage_survives(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            write_jsonl(root / 'rollout-good.jsonl', codex_rows())
            (root / 'rollout-bad.jsonl.zst').write_bytes((ZSTD_FILES / 'log-3.zst').read_bytes()[:-1])
            rows, issues = codex.read(codex.files([root]))
        self.assertEqual((len(rows), total(rows[0].tokens), len(issues)), (1, 2100, 1))
