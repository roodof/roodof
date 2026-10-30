"""Loopback backup admission and privacy, using only invented source/cache folders."""
import http.client
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from pler.dashboard import UsageDashboard
from pler.server import Server
from pler.usage import archive, backup, scan
from test_adoption_api import join_scan
from test_archive import codex_rows
from test_logs import write_jsonl


class BackupApiTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.cache=self.root/'cache'
        self.claude=self.root/'claude/projects';self.codex=self.root/'codex/sessions'
        self.claude.mkdir(parents=True);self.codex.mkdir(parents=True)
        (self.codex.parent/'archived_sessions').mkdir()
        environment=patch.dict(os.environ,PLER_CACHE_DIR=str(self.cache),
                               CLAUDE_CONFIG_DIR=str(self.claude.parent),CODEX_HOME=str(self.codex.parent))
        environment.start();self.addCleanup(environment.stop)
        source=self.codex/'rollout-PRIVATE-INVENTED-SOURCE.jsonl';write_jsonl(source,codex_rows());scan();source.unlink()
        self.board=UsageDashboard(git_reader=lambda path:dict(state='not_repository'))
        self.board.refresh();join_scan(self.board)
        self.server=Server(0,self.board)
        thread=threading.Thread(target=self.server.serve_forever,daemon=True);thread.start()
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)

    def request(self,route,raw=b'{}',auth=True,headers=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        sent={'Host':self.server.origin.split('//')[1],'Content-Type':'application/json'}
        if auth:sent.update(Origin=self.server.origin,**{'X-PLER-Token':self.server.token})
        sent.update(headers or {})
        connection.request('POST',route,body=raw,headers=sent)
        response=connection.getresponse();result=response.status,dict(response.getheaders()),response.read()
        connection.close();return result

    def test_private_download_then_check_preserves_saved_metadata_and_only_returns_counts(self):
        before=(self.cache/archive.FILENAME).read_bytes()
        status,headers,data=self.request('/api/usage/backup')
        self.assertEqual(status,200);self.assertEqual(headers['Content-Type'],'application/zip')
        self.assertEqual(headers['Content-Disposition'],'attachment; filename="PLER-backup.zip"')
        self.assertEqual(headers['Cache-Control'],'no-store')
        self.assertIn(b'PRIVATE-INVENTED-SOURCE',data)
        names={path.name for path in self.cache.iterdir()}
        status,_,raw=self.request('/api/usage/backup/check',data,headers={'Content-Type':'application/octet-stream'})
        self.assertEqual(status,200)
        value=json.loads(raw);self.assertTrue(value['ok']);self.assertEqual(value['backup']['archive_files'],1)
        self.assertNotIn(b'PRIVATE-INVENTED-SOURCE',raw);self.assertNotIn(str(self.root).encode(),raw)
        self.assertEqual((self.cache/archive.FILENAME).read_bytes(),before)
        self.assertEqual({path.name for path in self.cache.iterdir()},names)

    def test_both_actions_require_token_and_origin_before_any_backup_access(self):
        with patch.object(backup,'create',side_effect=AssertionError('unauthorized metadata read')),\
             patch.object(backup,'inspect',side_effect=AssertionError('unauthorized upload read')):
            for route in ('/api/usage/backup','/api/usage/backup/check'):
                for auth,headers in ((False,{}),(True,{'Origin':'https://outside.invalid'}),
                                     (True,{'X-PLER-Token':'wrong'})):
                    with self.subTest(route=route,headers=headers):
                        self.assertEqual(self.request(route,auth=auth,headers=headers)[0],403)

    def test_demo_and_unread_or_closed_snapshots_never_read_real_cache(self):
        with patch.object(backup,'create',side_effect=AssertionError('demo accessed metadata')):
            for state in ('demo','unread','closed'):
                self.board.sources['demo']=state=='demo'
                self.board.scanned_at=None if state=='unread' else '2026-10-30T10:00:00Z'
                self.board._closed=state=='closed'
                self.assertEqual(self.request('/api/usage/backup')[0],409)
                self.assertEqual(self.request('/api/usage/backup/check',b'invented',
                    headers={'Content-Type':'application/octet-stream'})[0],409)

    def test_one_operation_at_a_time_admits_no_second_large_body(self):
        self.server._backup_lock.acquire()
        try:
            with patch.object(backup,'inspect',side_effect=AssertionError('concurrent inspection')):
                status,_,raw=self.request('/api/usage/backup/check',b'invented',
                                          headers={'Content-Type':'application/octet-stream'})
            self.assertEqual(status,409);self.assertEqual(json.loads(raw)['code'],'busy')
        finally:self.server._backup_lock.release()

    def test_oversized_missing_length_chunked_and_wrong_content_types_are_rejected_before_inspection(self):
        with patch.object(backup,'inspect',side_effect=AssertionError('invalid body admitted')):
            for headers in ({'Content-Length':str(backup.MAX_BUNDLE_BYTES+1),'Content-Type':'application/octet-stream'},
                            {'Transfer-Encoding':'chunked','Content-Type':'application/octet-stream'},
                            {'Content-Length':'0','Content-Type':'application/octet-stream'},
                            {'Content-Length':'-1','Content-Type':'application/octet-stream'},
                            {'Content-Type':'application/json'}):
                with self.subTest(headers=headers):
                    self.assertEqual(self.request('/api/usage/backup/check',b'invented',headers=headers)[0],400)

    def test_duplicate_lengths_and_missing_length_are_rejected(self):
        for lengths in ([],['2','2']):
            connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
            connection.putrequest('POST','/api/usage/backup',skip_host=True)
            connection.putheader('Host',self.server.origin.split('//')[1]);connection.putheader('Origin',self.server.origin)
            connection.putheader('X-PLER-Token',self.server.token);connection.putheader('Content-Type','application/json')
            for value in lengths:connection.putheader('Content-Length',value)
            connection.endheaders(b'{}')
            response=connection.getresponse();self.assertEqual(response.status,400);response.read();connection.close()

    def test_corrupt_upload_has_safe_error_and_does_not_write_files(self):
        before={path.name:path.read_bytes() for path in self.cache.iterdir() if path.is_file()}
        status,_,raw=self.request('/api/usage/backup/check',b'PRIVATE-UPLOAD-CANARY',
                                 headers={'Content-Type':'application/octet-stream'})
        self.assertEqual(status,400);self.assertNotIn(b'PRIVATE-UPLOAD-CANARY',raw)
        self.assertIn(json.loads(raw)['code'],('invalid','unsupported'))
        self.assertEqual({path.name:path.read_bytes() for path in self.cache.iterdir() if path.is_file()},before)

    def test_download_body_and_query_cannot_name_a_source_or_change_scope(self):
        with patch.object(backup,'create',side_effect=AssertionError('invalid options accepted')):
            for route,raw in (('/api/usage/backup?path=/private',b'{}'),
                              ('/api/usage/backup?lang=en&lang=tr',b'{}'),
                              ('/api/usage/backup?lang=bad',b'{}'),
                              ('/api/usage/backup',b'{"path":"/private"}'),
                              ('/api/usage/backup',b'[]')):
                self.assertEqual(self.request(route,raw)[0],400)

    def test_page_declares_the_actual_server_upload_limit_without_access_credentials(self):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        connection.request('GET','/');response=connection.getresponse();raw=response.read();connection.close()
        self.assertEqual(response.status,200)
        self.assertIn(('name="pler-backup-max" content="%d"'%backup.MAX_BUNDLE_BYTES).encode(),raw)
        self.assertNotIn(self.server.token.encode(),raw)


if __name__=='__main__':unittest.main()
