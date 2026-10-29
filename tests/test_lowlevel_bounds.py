"""Malformed local requests and growing metadata have bounded, ordinary failures."""
import http.client
import io
import json
import os
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pler.dashboard import UsageDashboard
from pler.server import Server
from pler.usage import archive
from pler.usage.cache import FileCache
from pler.usage import preferences


class MetadataReadBounds(unittest.TestCase):
    def test_a_file_that_grows_after_stat_is_read_only_through_the_bound(self):
        sizes=[]
        class Stream(io.BytesIO):
            def read(self,size=-1):
                sizes.append(size)
                return super().read(size)
        class Growing:
            def stat(self):return SimpleNamespace(st_size=2)
            def open(self,mode):
                self.mode=mode
                return Stream(b' '*200+b'{}')
        path=Growing()
        with patch.object(archive.json,'loads',side_effect=AssertionError('oversized input reached JSON')):
            with self.assertRaises(ValueError):archive._read(path,32)
        self.assertEqual(sizes,[3])
        self.assertEqual(path.mode,'rb')

    def test_a_known_oversized_file_is_rejected_before_open(self):
        class Oversized:
            def stat(self):return SimpleNamespace(st_size=33)
            def open(self,*args):raise AssertionError('oversized file opened')
        with self.assertRaises(ValueError):archive._read(Oversized(),32)

    def test_the_generation_marker_has_a_small_separate_limit(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,PLER_CACHE_DIR=folder):
            (Path(folder)/archive.GENERATION).write_bytes(b' '*4097)
            with patch.object(Path,'open',side_effect=AssertionError('oversized generation opened')):
                with self.assertRaises(ValueError):archive._generation(Path(folder))

    def test_utf8_and_invalid_constants_keep_the_existing_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'invented.json'
            path.write_text(json.dumps({'text':'\u03bb'}),'utf-8')
            self.assertEqual(archive._read(path,64),{'text':'\u03bb'})
            path.write_text('{"n":NaN}','utf-8')
            with self.assertRaises(ValueError):archive._read(path,64)

    def test_over_nested_archive_is_an_invalid_file_instead_of_a_scan_crash(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/archive.FILENAME
            path.write_bytes(b'['*1500+b'0'+b']'*1500)
            with self.assertRaises(ValueError):archive._load(Path(folder))

    def test_a_growing_retention_preference_is_bounded_and_invalid(self):
        sizes=[]
        class Stream(io.BytesIO):
            def read(self,size=-1):
                sizes.append(size)
                return super().read(size)
        class Growing:
            def stat(self):return SimpleNamespace(st_size=2)
            def open(self,mode):return Stream(b' '*5000)
        with patch.object(preferences,'cache_file',return_value=Growing()):
            with self.assertRaises(ValueError):preferences.read(Path('invented'))
        self.assertEqual(sizes,[3])

    def test_over_nested_disposable_cache_becomes_a_cache_miss(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,PLER_CACHE_DIR=folder):
            (Path(folder)/'codex.json').write_bytes(b'['*1500+b'0'+b']'*1500)
            cache=FileCache('codex','invented-key')
            self.assertEqual(cache.old,{})
            self.assertFalse(cache.intact)

    def test_over_nested_preference_is_closed_and_can_be_repaired_by_an_explicit_choice(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,PLER_CACHE_DIR=folder):
            base=Path(folder)
            (base/preferences.FILENAME).write_bytes(b'['*1500+b'0'+b']'*1500)
            view=archive.Archive()
            self.assertFalse(view.retention_enabled)
            self.assertGreater(view.errors,0)
            result=archive.set_retention(False)
            self.assertTrue(result['ok'])
            self.assertIs(preferences.read(base),False)


class MalformedLocalRequests(unittest.TestCase):
    def setUp(self):
        self.server=Server(0,UsageDashboard(lambda:([],{})))
        thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self,path,token,method='GET'):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        headers={'X-PLER-Token':token,'Origin':self.server.origin}
        body=None
        if method=='POST':headers['Content-Type']='application/json';body=b'{}'
        conn.request(method,path,body=body,headers=headers)
        response=conn.getresponse();status=response.status;response.read();conn.close()
        return status

    def test_non_ascii_tokens_are_denied_without_breaking_the_connection_handler(self):
        for invalid in ('\u00e9','a'*63,'a'*65,'!',' '):
            with self.subTest(token=repr(invalid)):
                self.assertEqual(self.request('/api/usage',invalid),401)
                self.assertEqual(self.request('/api/usage/refresh',invalid,'POST'),403)
        self.assertEqual(self.request('/api/usage',self.server.token),200)

    def test_session_query_uses_the_same_strict_language_rules_as_report_queries(self):
        for query in ('id='+'a'*24+'&lang=xx','id='+'a'*24+'&lang=en&lang=tr'):
            self.assertEqual(self.request('/api/usage/session?'+query,self.server.token),400)
