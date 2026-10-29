"""Bounded source/output chunks and strict frames, with invented inputs only."""
import io
import threading
import unittest
from unittest.mock import patch

from pler.runtime import cancellation, ScanCancelled
from pler.usage import zstd, unzstd
from pler.usage.input_limits import ReadLimitExceeded
from test_logs import ZSTD_FILES, ZSTD_SAMPLES, stored_zstd


class LimitedReads(io.BytesIO):
    def __init__(self,data,maximum):
        super().__init__(data)
        self.maximum,self.requests=maximum,[]

    def read(self,size=-1):
        if not 0<size<=self.maximum:raise AssertionError('unbounded compressed read')
        self.requests.append(size)
        return super().read(size)


def unpack(data,maximum=1024*1024,chunk=37):
    source=LimitedReads(data,chunk)
    output=list(zstd.iter_chunks(source,max_output=maximum,max_input=len(data),chunk_size=chunk))
    assert all(len(part)<=chunk for part in output)
    assert not source.closed
    return b''.join(output)


class ZstdBoundsTests(unittest.TestCase):
    def test_corpus_is_exact_on_bounded_streaming_api(self):
        for path in sorted(ZSTD_FILES.glob('*.zst')):
            with self.subTest(fixture=path.name):
                self.assertEqual(unpack(path.read_bytes(),chunk=4096),ZSTD_SAMPLES[path.name.split('-')[0]]())

    def test_every_truncation_and_concatenation_is_strict(self):
        one=stored_zstd(b'abc');two=stored_zstd(b'def')
        skip=(0x184D2A53).to_bytes(4,'little')+(3).to_bytes(4,'little')+b'xyz'
        self.assertEqual(unpack(skip+one+skip+two+skip,chunk=1),b'abcdef')
        self.assertEqual(unpack(skip,maximum=0,chunk=1),b'')
        self.assertEqual(unpack(stored_zstd(b''),maximum=0),b'')
        for frame in (one,skip):
            for end in range(len(frame)):
                with self.subTest(end=end,bytes=len(frame)),self.assertRaises(ValueError):
                    unpack(frame[:end],chunk=1)
        for bad in (one+two[:-1],one+b'junk',one+b'\x00'):
            with self.assertRaises(ValueError):unpack(bad)

    def test_declared_and_unknown_size_frames_share_output_budget(self):
        # One RLE block: small compressed bytes with no declared content size.
        frame=unzstd.MAGIC.to_bytes(4,'little')+b'\x00\x38'+((100000<<3)|3).to_bytes(3,'little')+b'x'
        self.assertEqual(unpack(frame,maximum=100000,chunk=4096),b'x'*100000)
        for source in (frame,stored_zstd(b'x'*100)):
            with self.assertRaises(ValueError):unpack(source,maximum=99)
        with self.assertRaises(ValueError):
            unpack(stored_zstd(b'abc')+stored_zstd(b'def'),maximum=5)

    def test_input_limit_is_enforced_during_read(self):
        frame=stored_zstd(b'abc')
        source=LimitedReads(frame,5)
        with self.assertRaises(ValueError):
            list(zstd.iter_chunks(source,max_output=10,max_input=len(frame)-1,chunk_size=5))
        self.assertLessEqual(source.tell(),len(frame))

    def test_oversized_window_is_rejected_before_decoder_allocation(self):
        # A resource limit, not a damaged file: reported as incomplete coverage at a limit.
        frame=unzstd.MAGIC.to_bytes(4,'little')+b'\x00\xff'+b'\x01\x00\x00'
        with self.assertRaises(ReadLimitExceeded):
            unpack(frame)

    def test_fallback_checks_unknown_size_and_total_budget_before_growth(self):
        frame=unzstd.MAGIC.to_bytes(4,'little')+b'\x00\x38'+((100000<<3)|3).to_bytes(3,'little')+b'x'
        with patch.dict('sys.modules',{'compression':None,'zstandard':None}):
            self.assertEqual(unpack(stored_zstd(b'abc'),maximum=3),b'abc')
            with self.assertRaises(ValueError):unpack(frame,maximum=99999)
            with self.assertRaises(ValueError):unpack(stored_zstd(b'abc')*2,maximum=5)
        with self.assertRaises(ValueError):unzstd.decompress(frame,max_output=99999)

    def test_compressed_sequences_without_declared_size_obey_budget(self):
        original=(ZSTD_FILES/'log-3.zst').read_bytes();flags=original[4]
        single=bool(flags&32);dictionary=(0,1,2,4)[flags&3]
        count=((1 if single else 0),2,4,8)[flags>>6]
        start=5+(not single)
        # Keep all encoded blocks/checksum but use an explicit bounded window
        # and omit the optional content size; sequence growth must be checked.
        unknown=original[:4]+bytes([flags&31,136])+original[start:start+dictionary]+original[start+dictionary+count:]
        expected=ZSTD_SAMPLES['log']()
        self.assertEqual(unpack(unknown,maximum=len(expected)),expected)
        with self.assertRaises(ValueError):unpack(unknown,maximum=len(expected)-1)
        with patch.dict('sys.modules',{'compression':None,'zstandard':None}):
            with self.assertRaises(ValueError):unpack(unknown,maximum=len(expected)-1)

    def test_corrupt_checksums_and_sizes_are_never_accepted(self):
        checked=next(path.read_bytes() for path in sorted(ZSTD_FILES.glob('*.zst')) if path.read_bytes()[4]&4)
        with self.assertRaises(ValueError):unpack(checked[:-1]+bytes([checked[-1]^1]))
        original=stored_zstd(b'abc')
        with self.assertRaises(ValueError):unpack(original[:5]+(2).to_bytes(8,'little')+original[13:])

    def test_cancellation_is_not_reported_as_compression_corruption(self):
        stop=threading.Event();stop.set()
        with self.assertRaises(ScanCancelled),cancellation(stop):
            unpack(stored_zstd(b'abc'))
        def stopped(data):raise ScanCancelled()
        with self.assertRaises(ScanCancelled):zstd._checked(stopped)(b'')

    def test_cancellation_after_a_compressed_read_is_observed(self):
        stop=threading.Event()
        class Stopping(io.BytesIO):
            def read(self,size):
                output=super().read(size);stop.set();return output
        with cancellation(stop),self.assertRaises(ScanCancelled):
            list(zstd.iter_chunks(Stopping(stored_zstd(b'abc')),max_input=100,max_output=100))

    def test_decoder_factory_exposes_bounded_streaming(self):
        decode,_=zstd.decoder()
        self.assertIs(decode.iter_chunks,zstd.iter_chunks)

