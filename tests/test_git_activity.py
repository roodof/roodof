"""Real file formats, synthetic history only. No git process, identity or message escapes."""
from datetime import datetime, timedelta, timezone
import http.client
import json
from pathlib import Path
import stat
import subprocess
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pler.dashboard import UsageDashboard, project_view
from pler.git_activity import read_repository, session_activity
from pler.server import Server
from pler.usage.records import Session

NOW = datetime(2026, 10, 26, 12, tzinfo=timezone.utc)
SECRET = 'PRIVATE-IDENTITY-MESSAGE-AND-PATH'


def entry(seconds, action='commit', old='a' * 40, new='b' * 40):
    return ('%s %s %s <private@example.invalid> %d +0300\t%s: %s\n'
            % (old, new, SECRET, int(NOW.timestamp()) + seconds, action, SECRET)).encode()


class GitActivityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        self.log = self.root / '.git' / 'logs' / 'HEAD'
        self.log.parent.mkdir(parents=True)

    def view(self, start=-60, end=60):
        return session_activity(read_repository(str(self.root)), NOW + timedelta(seconds=start), NOW + timedelta(seconds=end))

    def test_time_window_is_inclusive_and_events_are_neither_authorship_nor_unique_commits(self):
        self.log.write_bytes(entry(-90) + entry(-60) + entry(0, 'commit (amend)') + entry(60, 'reset') + entry(90))
        view = self.view()
        self.assertEqual(view['counts'], dict(commit=1, amend=1, reset=1))
        self.assertEqual(view['matched_events'], 3)
        self.assertEqual([e['kind'] for e in view['events']], ['reset', 'amend', 'commit'])
        self.assertFalse(view['coverage_limited'])

    def test_private_identity_messages_raw_paths_and_raw_hashes_are_not_projected(self):
        self.log.write_bytes(entry(0, 'checkout'))
        value = self.view()
        encoded = json.dumps(value)
        for secret in (SECRET, 'private@example.invalid', str(self.root), 'b' * 40):
            self.assertNotIn(secret, encoded)
        self.assertEqual(value['events'][0]['commit'], 'b' * 8)
        self.assertTrue(value['coverage_limited'])

    def test_linked_worktree_gitdir_file_uses_its_own_head_log(self):
        linked = Path(self.temp.name) / 'linked'
        linked.mkdir()
        (linked / '.git').write_text('gitdir: ../project/.git\n', 'utf-8')
        self.log.write_bytes(entry(0, 'commit (initial)'))
        result = session_activity(read_repository(str(linked)), NOW, NOW)
        self.assertEqual(result['counts'], dict(commit=1))

    def test_missing_repository_and_missing_reflog_are_distinguished(self):
        self.assertEqual(read_repository(str(self.root))['state'], 'no_history')
        self.assertEqual(read_repository(str(self.root / 'gone'))['state'], 'not_repository')
        self.log.write_bytes(b'')
        self.assertEqual(read_repository(str(self.root))['state'], 'no_history')

    def test_network_relative_and_home_paths_are_skipped_before_any_file_is_opened(self):
        with patch.object(Path, 'open', side_effect=AssertionError('must not read')):
            for path in ('//server/share/project', '\\\\server\\share\\project', 'relative/project', str(Path.home())):
                with self.subTest(path=path):
                    self.assertEqual(read_repository(path)['state'], 'not_repository')

    def test_invalid_or_network_gitdir_pointer_is_unavailable_and_never_followed(self):
        linked = Path(self.temp.name) / 'linked'
        linked.mkdir()
        marker = linked / '.git'
        for content in ('gitdir: //server/share/repo', 'gitdir: \\\\server\\repo', SECRET, 'gitdir: ' + 'a' * 4100):
            marker.write_text(content, 'utf-8')
            with self.subTest(content=content[:20]):
                self.assertEqual(read_repository(str(linked)), dict(state='unavailable'))

    def test_symlink_or_windows_reparse_ancestor_is_rejected_before_reading(self):
        for info in (SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0),
                     SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)):
            with patch.object(Path, 'lstat', return_value=info), patch.object(Path, 'open', side_effect=AssertionError('must not read')):
                self.assertEqual(read_repository(str(self.root)), dict(state='not_repository'))

    def test_bad_lines_and_unreadable_files_do_not_fail_the_usage_scan(self):
        self.log.write_bytes(b'broken\n' + entry(0, 'merge') + entry(999999999999))
        value = self.view()
        self.assertEqual(value['matched_events'], 1)
        self.assertTrue(value['coverage_limited'])
        with patch.object(Path, 'open', side_effect=PermissionError(SECRET)):
            self.assertEqual(read_repository(str(self.root)), dict(state='unavailable'))

    def test_bounded_history_and_paged_events_keep_counts_honest(self):
        self.log.write_bytes(b''.join(entry(n) for n in range(35)))
        value = self.view()
        self.assertEqual((value['matched_events'], len(value['events']), value['omitted_events']), (35, 20, 15))
        with patch('pler.git_activity.MAX_BYTES', 500):
            value = self.view()
        self.assertTrue(value['coverage_limited'])
        self.assertLess(value['matched_events'], 35)

    def test_sha256_history_and_missing_times_are_supported_without_invented_dates(self):
        self.log.write_bytes(entry(0, 'rebase (finish)', old='a' * 64, new='c' * 64))
        snapshot = read_repository(str(self.root))
        self.assertEqual(session_activity(snapshot, NOW, NOW)['counts'], dict(rebase=1))
        self.assertEqual(session_activity(snapshot, None, NOW), dict(state='unknown_time'))
        self.assertEqual(session_activity(snapshot, NOW, NOW - timedelta(seconds=1)), dict(state='unknown_time'))
        self.assertEqual(session_activity(None, NOW, NOW), dict(state='not_scanned'))

    def test_one_git_read_per_project_per_refresh_and_scoped_public_projection(self):
        self.log.write_bytes(entry(0))
        rows = [Session('codex', str(i), SECRET, project=str(self.root), started=NOW, ended=NOW) for i in range(2)]
        rows.append(Session('codex', 'other', SECRET, project=str(self.root / 'other'), started=NOW, ended=NOW))
        sources = {}
        with patch('pler.dashboard.read_repository', wraps=read_repository) as read:
            dashboard = UsageDashboard(lambda: (rows, sources))
            dashboard.refresh()
            dashboard.thread.join(5)
            value = dashboard.view(days=0)
            self.assertEqual(value['state'], 'ready')
            self.assertEqual(read.call_count, 2)
            for _ in range(3):
                dashboard.view(days=0, lang='tr')
            self.assertEqual(read.call_count, 2)
        key = value['sessions'][0]['project_id']
        selected = project_view(rows, dashboard.sources, days=0, project=key)
        self.assertEqual(len(selected['sessions']), 2)
        for row in selected['sessions']:
            self.assertEqual(row['git_activity']['counts'], dict(commit=1))
        self.assertNotIn(SECRET, json.dumps(selected))
        self.assertNotIn('git_activity', sources)

    def test_http_export_keeps_git_metadata_private_read_only_and_starts_no_program(self):
        before = entry(0)
        self.log.write_bytes(before)
        rows = [Session('codex', 'test', SECRET, project=str(self.root), started=NOW, ended=NOW)]
        forbidden = {self.root / 'source.py', self.root / '.git' / 'config'}
        for path in forbidden:
            path.write_text(SECRET, 'utf-8')
        real_open = Path.open
        def guarded(path, *args, **kwargs):
            self.assertNotIn(path, forbidden, 'source and Git configuration must not be read')
            return real_open(path, *args, **kwargs)
        server = Server(0, UsageDashboard(lambda: (rows, {})))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with patch.object(subprocess, 'Popen', side_effect=AssertionError('must not start Git')), \
                    patch.object(Path, 'open', guarded):
                server.dashboard.refresh()
                server.dashboard.thread.join(5)
                connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=10)
                try:
                    connection.request('GET', '/api/usage/export?days=0&lang=en',headers={'X-PLER-Token':server.token})
                    response = connection.getresponse()
                    body = response.read()
                    self.assertEqual(response.status, 200)
                finally:
                    connection.close()
                value = json.loads(body)
                self.assertEqual(value['sessions'][0]['git_activity']['counts'], dict(commit=1))
                self.assertNotIn(SECRET, body.decode())
                self.assertNotIn('project_options', value)
        finally:
            server.shutdown()
            worker.join(5)
            server.server_close()
        self.assertEqual(self.log.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
