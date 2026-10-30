"""A verdict update uses one bounded document snapshot; invalid history is never replaced."""
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pler.usage import verdicts


FIRST='a'*24
SECOND='b'*24


class VerdictReadSafetyTests(unittest.TestCase):
    def make(self,folder,entries=None,**extra):
        path=Path(folder)/verdicts.FILENAME
        value=dict(format=1,verdicts=entries or {FIRST:dict(verdict='useful',at=123)})
        value.update(extra)
        path.write_text(json.dumps(value),'utf-8')
        return path

    def test_save_reads_one_bounded_snapshot_and_preserves_existing_timestamps(self):
        with tempfile.TemporaryDirectory() as folder:
            path=self.make(folder)
            original_open=Path.open
            reads=[];opens=[]
            class Counted:
                def __init__(self,stream):self.stream=stream
                def __enter__(self):return self
                def __exit__(self,*args):self.stream.close()
                def read(self,size=-1):
                    reads.append(size)
                    return self.stream.read(size)
            def opened(candidate,*args,**kwargs):
                stream=original_open(candidate,*args,**kwargs)
                if candidate==path and args==('rb',):
                    opens.append(candidate)
                    return Counted(stream)
                return stream
            size=path.stat().st_size
            with patch.object(Path,'open',opened),patch.object(Path,'read_bytes',side_effect=AssertionError('unbounded reread')),patch.object(verdicts.time,'time',return_value=456):
                result=verdicts.save(SECOND,'wasted',folder)
            self.assertEqual(result,{FIRST:'useful',SECOND:'wasted'})
            self.assertEqual(reads,[size+1])
            self.assertEqual(len(opens),1)
            stored=json.loads(path.read_text('utf-8'))['verdicts']
            self.assertEqual(stored[FIRST],dict(verdict='useful',at=123))
            self.assertEqual(stored[SECOND],dict(verdict='wasted',at=456))

    def test_growth_after_stat_is_bounded_and_cannot_reach_the_writer(self):
        reads=[]
        class Stream(io.BytesIO):
            def read(self,size=-1):
                reads.append(size)
                return super().read(size)
        class Growing:
            parent=Path('invented')
            def stat(self):return SimpleNamespace(st_size=2)
            def open(self,mode):return Stream(b' '*1000+b'{}')
        from contextlib import nullcontext
        with patch.object(verdicts,'cache_file',return_value=Growing()), \
                patch('pler.usage.archive._locked',return_value=nullcontext()), \
                patch('pler.usage.archive._write',side_effect=AssertionError('invalid document overwritten')):
            with self.assertRaises(ValueError):verdicts.save(SECOND,'wasted')
        self.assertEqual(reads,[3])

    def test_same_size_replacement_before_open_is_validated_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            path=self.make(folder)
            prior=path.read_bytes()
            replaced=prior.replace(b'"format": 1',b'"format": 2')
            self.assertEqual(len(prior),len(replaced))
            original_open=Path.open
            def opened(candidate,*args,**kwargs):
                if candidate==path and args==('rb',):return io.BytesIO(replaced)
                return original_open(candidate,*args,**kwargs)
            with patch.object(Path,'open',opened),patch('pler.usage.archive._write',side_effect=AssertionError('newer snapshot overwritten')):
                with self.assertRaises(ValueError):verdicts.save(SECOND,'wasted',folder)
            self.assertEqual(path.read_bytes(),prior)

    def test_known_oversize_is_refused_before_open_or_write(self):
        class Oversize:
            parent=Path('invented')
            def stat(self):return SimpleNamespace(st_size=verdicts.MAX_BYTES+1)
            def open(self,*args):raise AssertionError('oversized file opened')
        from contextlib import nullcontext
        with patch.object(verdicts,'cache_file',return_value=Oversize()), \
                patch('pler.usage.archive._locked',return_value=nullcontext()), \
                patch('pler.usage.archive._write',side_effect=AssertionError('oversized file overwritten')):
            with self.assertRaises(ValueError):verdicts.save(SECOND,'wasted')

    def test_invalid_shapes_and_deep_json_never_replace_existing_bytes(self):
        invalid=[b'['*1500+b'0'+b']'*1500,
                 json.dumps(dict(format=True,verdicts={})).encode(),
                 json.dumps(dict(format=1,verdicts={FIRST:dict(verdict='useful',at=True)})).encode(),
                 json.dumps(dict(format=1,verdicts={FIRST:dict(verdict='useful',at=-1)})).encode(),
                 json.dumps(dict(format=1,verdicts={FIRST:dict(verdict='other',at=1)})).encode()]
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/verdicts.FILENAME
            for raw in invalid:
                with self.subTest(bytes=len(raw)):
                    path.write_bytes(raw)
                    with self.assertRaises(ValueError):verdicts.save(SECOND,'wasted',folder)
                    self.assertEqual(path.read_bytes(),raw)
