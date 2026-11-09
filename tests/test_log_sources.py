"""Invented local folders only; WSL status and UNC I/O are mocked, no distro is started."""
import http.client
import io
import json
from pathlib import Path
import threading
import zipfile
from contextlib import contextmanager
import stat
from types import SimpleNamespace
from unittest.mock import patch

from pler import wsl
from pler.dashboard import UsageDashboard
from pler.server import Server
from pler.usage import Rescan, archive, scan, sources
from pler.usage.records import total
from test_adoption_api import IsolatedMetadata, join_scan
from test_archive import codex_rows, claude_rows
from test_logs import write_jsonl


class LogSourceTests(IsolatedMetadata):
    def extra(self, agent='codex'):
        root = self.root/'extra'/('sessions' if agent == 'codex' else 'projects')
        root.mkdir(parents=True, exist_ok=True)
        write_jsonl(root/('rollout-extra.jsonl' if agent == 'codex' else 'extra.jsonl'),
                    codex_rows() if agent == 'codex' else claude_rows())
        return root

    def add(self, root, agent='codex'):
        sources.Store().change(sources.revision(sources.Store().read()), agent, [str(root)])

    def test_extra_folder_is_additive_deduplicated_and_survives_new_reader(self):
        extra = self.extra()
        self.add(extra)
        self.add(extra)
        self.add(self.codex)  # automatic plus manual root must be read once
        write_jsonl(self.claude/'native.jsonl', claude_rows())
        first, details = Rescan()()
        again, current = Rescan()()
        self.assertEqual((details['claude_files'], details['codex_files']), (1, 1))
        self.assertEqual(len(first), 2)
        self.assertEqual(sum(total(s.tokens) for s in first), sum(total(s.tokens) for s in again))
        self.assertEqual(len(sources.Store().read()), 2)
        self.assertTrue(current['archive']['available'])

    def test_config_home_expands_only_log_subfolders_for_both_agents(self):
        for agent in sources.AGENTS:
            root = self.extra(agent)
            checked = sources.check(agent, str(root.parent))
            self.assertEqual(checked['roots'], [str(root)])
        (self.root/'extra/archived_sessions').mkdir()
        self.assertEqual(set(sources.check('codex', str(self.root/'extra'))['roots']),
                         {str(self.root/'extra/sessions'), str(self.root/'extra/archived_sessions')})

    def test_removal_keeps_original_logs_and_retained_metadata(self):
        extra = self.extra(); self.add(extra); scan()
        before = (self.cache/archive.FILENAME).read_bytes()
        sources.Store().change(sources.revision(sources.Store().read()), remove=sources.code('codex', str(extra)))
        rows, details = scan()
        self.assertTrue((extra/'rollout-extra.jsonl').is_file())
        self.assertEqual(details['codex_files'], 0)
        self.assertEqual(len(rows), 0)  # no longer selected; private retained metadata stays on disk
        self.assertTrue((self.cache/archive.FILENAME).is_file())
        self.assertEqual((self.cache/archive.FILENAME).read_bytes(), before)

    def test_revision_conflict_does_not_overwrite_another_window(self):
        old = sources.revision([]); extra = self.extra(); self.add(extra)
        before = (self.cache/sources.FILENAME).read_bytes()
        with self.assertRaisesRegex(sources.SourceError, 'conflict'):
            sources.Store().change(old, remove=sources.code('codex', str(extra)))
        self.assertEqual((self.cache/sources.FILENAME).read_bytes(), before)

    def test_limits_and_corrupt_preferences_are_preserved(self):
        for n in range(sources.MAX_ENTRIES): self.add(self.root/('invented-'+str(n)))
        before = (self.cache/sources.FILENAME).read_bytes()
        with self.assertRaisesRegex(sources.SourceError, 'limit'): self.add(self.root/'extra-limit')
        self.assertEqual((self.cache/sources.FILENAME).read_bytes(), before)
        for raw in (b'{broken', b'{"format":1,"format":1,"entries":[]}', b'x'*(sources.MAX_BYTES+1)):
            (self.cache/sources.FILENAME).write_bytes(raw)
            self.assertFalse(sources.view()['readable'])
            with self.assertRaises(sources.SourceError): self.add(self.root/'should-not-save')
            self.assertEqual((self.cache/sources.FILENAME).read_bytes(), raw)

    def test_corrupt_source_preference_keeps_previous_dashboard(self):
        write_jsonl(self.codex/'rollout-standard.jsonl', codex_rows())
        board=UsageDashboard(); self.addCleanup(board.close); board.refresh(); join_scan(board)
        old = board.view(0)['totals']
        (self.cache/sources.FILENAME).write_bytes(b'{invalid')
        board.refresh(); join_scan(board)
        self.assertEqual(board.state, 'error')
        self.assertEqual(board.error, 'error.log_sources')
        self.assertEqual(board.view(0)['totals'], old)

    def test_explicit_fixture_scan_and_demo_never_read_or_write_real_preferences(self):
        extra=self.extra(); self.add(extra)
        with patch.object(sources.Store, 'read', side_effect=AssertionError('real preferences')):
            rows, _=scan([], [])
            self.assertEqual(rows, [])
            board=UsageDashboard(manage_sources=False); self.addCleanup(board.close)
            self.assertTrue(board.source_view()['demo'])
            self.assertEqual(board.source_action(dict(action='check',agent='codex',path=str(extra)))['reason'], 'demo')

    def test_unsafe_network_and_relative_roots_fail_before_any_probe(self):
        for value in (r'\\example.invalid\share', r'\\?\C:\logs', r'\\.\pipe\bad',
                      r'\\wsl.localhost\Ubuntu\..\logs', r'\\wsl.localhost\Ubuntu',
                      'relative', str(Path(self.root.anchor)), 'bad\npath'):
            with self.subTest(value=value), patch.object(Path, 'lstat', side_effect=AssertionError('probe')), \
                    patch.object(wsl, 'running', side_effect=AssertionError('status')):
                with self.assertRaises(sources.SourceError): sources.check('codex', value)

    def test_stopped_or_unavailable_wsl_never_touches_unc(self):
        for status, reason in (({}, 'wsl_not_running'), (None, 'wsl_unavailable')):
            with patch.object(wsl, 'WINDOWS', True), patch.object(wsl, 'running', return_value=status), \
                    patch.object(Path, 'lstat', side_effect=AssertionError('UNC probe')):
                with self.assertRaisesRegex(sources.SourceError, reason):
                    sources.check('codex', r'\\wsl.localhost\Ubuntu\home\invented\.codex\sessions')

    def test_reports_omit_source_paths_and_backup_omits_selection_but_keeps_history_paths(self):
        from pler.usage import backup
        extra=self.extra(); self.add(extra); scan()
        board=UsageDashboard(); self.addCleanup(board.close); board.refresh(); join_scan(board)
        self.assertNotIn(str(extra), json.dumps(board.view(0)))
        self.assertNotIn(sources.FILENAME, backup.LIMITS)
        self.assertEqual(sources.view()['entries'][0]['path'], str(extra))
        with zipfile.ZipFile(io.BytesIO(backup.create())) as bundle:
            self.assertNotIn(sources.FILENAME, bundle.namelist())
            retained=json.loads(bundle.read(archive.FILENAME))
            self.assertTrue(any(str(extra) in row['source'] for row in retained['files'].values()))

    def test_running_wsl_check_uses_status_before_mocked_directory_access(self):
        events=[]
        root=r'\\wsl.localhost\Ubuntu\home\invented\.codex\sessions'
        def status(): events.append('status'); return {'ubuntu':'Ubuntu'}
        def directory(*_):
            self.assertIn('status',events);events.append('directory')
            return SimpleNamespace(st_mode=stat.S_IFDIR)
        @contextmanager
        def entries(_):
            self.assertIn('status',events);yield iter(())
        with patch.object(wsl,'WINDOWS',True),patch.object(wsl,'running',side_effect=status), \
                patch.object(wsl.WslRoots,'_checked',side_effect=lambda value:Path(value)), \
                patch.object(Path,'stat',side_effect=directory),patch.object(Path,'is_dir',return_value=False), \
                patch.object(sources.os,'scandir',side_effect=entries):
            result=sources.check('codex',root)
        self.assertEqual(result,dict(ok=True,roots=[root],kind='wsl'))

    def test_saved_wsl_root_registers_existing_capability_for_extra_discovery(self):
        from pler.usage import codex,discovery
        root=r'\\wsl.localhost\Ubuntu\home\invented\.codex\sessions'
        self.add(root)
        entry=SimpleNamespace(name='rollout-invented.jsonl',path=root+r'\rollout-invented.jsonl',
                              stat=lambda **_:SimpleNamespace(st_mode=stat.S_IFREG))
        @contextmanager
        def entries(_): yield iter([entry])
        manifest=discovery.Manifest()
        with patch.object(wsl,'WINDOWS',True),patch.object(wsl,'running',return_value={'ubuntu':'Ubuntu'}), \
                patch.object(wsl.WslRoots,'_checked',side_effect=lambda value:Path(value)), \
                patch.object(codex,'roots',return_value=[]),patch.object(discovery.os,'scandir',side_effect=entries):
            found=codex.files(extra=[sources.Store().read()[0]['path']],manifest=manifest)
        self.assertEqual([str(p) for p in found],[entry.path])
        self.assertEqual(manifest.scope(found[0]),root)

    def test_missing_and_file_paths_have_distinct_check_reasons(self):
        with self.assertRaisesRegex(sources.SourceError, 'missing'): sources.check('codex', str(self.root/'missing'))
        path=self.root/'file'; path.write_text('invented',encoding='utf-8')
        with self.assertRaisesRegex(sources.SourceError, 'not_folder'): sources.check('codex', str(path))


class SourceApiTests(IsolatedMetadata):
    def test_authentication_fields_add_remove_and_refresh(self):
        board=UsageDashboard(); self.addCleanup(board.close)
        server=Server(0, board)
        self.addCleanup(server.server_close)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(server.shutdown)
        origin=server.origin
        def request(method, path, body=None, authorized=True):
            connection=http.client.HTTPConnection('127.0.0.1',server.server_address[1],timeout=5)
            headers={'Origin':origin,'Content-Type':'application/json'}
            if authorized: headers['X-PLER-Token']=server.token
            connection.request(method,path,json.dumps(body) if body is not None else None,headers)
            response=connection.getresponse(); result=(response.status,json.loads(response.read()))
            connection.close();return result
        self.assertEqual(request('GET','/api/usage/sources',authorized=False)[0],401)
        self.assertEqual(request('POST','/api/usage/sources',{},False)[0],403)
        status, data=request('GET','/api/usage/sources');self.assertEqual(status,200)
        self.assertEqual(request('POST','/api/usage/sources',{'action':'add','shell':'forbidden'})[0],400)
        root=self.root/'extra';root.mkdir()
        checked=request('POST','/api/usage/sources',dict(action='check',agent='codex',path=str(root)))
        self.assertEqual(checked[0],200)
        status, data=request('POST','/api/usage/sources',dict(action='add',agent='codex',path=str(root),expected=data['revision']))
        self.assertEqual(status,200);self.assertEqual(len(data['entries']),1);join_scan(board)
        status, data=request('POST','/api/usage/sources',dict(action='remove',id=data['entries'][0]['id'],expected=data['revision']))
        self.assertEqual(status,200);self.assertEqual(data['entries'],[]);join_scan(board)
