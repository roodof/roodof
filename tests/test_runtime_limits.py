"""One scan worker and finite local HTTP work; synthetic metadata and loopback peers only."""
import http.client
import socket
import threading
import unittest
from unittest.mock import patch

from pler.dashboard import UsageDashboard
from pler.runtime import ScanCancelled, cancellation, checkpoint
from pler.server import Server
from pler.usage.records import Session


class ScanLifecycleTests(unittest.TestCase):
    def test_cancellation_is_scoped_and_restores_an_outer_scan(self):
        outer,inner=threading.Event(),threading.Event()
        outer.set()
        with cancellation(inner):
            checkpoint()
            with self.assertRaises(ScanCancelled):
                with cancellation(outer):pass
            checkpoint()
        checkpoint()

    def test_forced_refreshes_coalesce_and_stale_reader_never_enters_git_phase(self):
        entered,release=threading.Event(),threading.Event()
        calls=[]
        def reader():
            calls.append(len(calls)+1)
            if len(calls)==1:
                entered.set()
                if not release.wait(5):raise AssertionError('unreleased synthetic reader')
            row=Session('codex','invented','invented',calls=len(calls))
            return [row],{}
        board=UsageDashboard(reader)
        self.addCleanup(lambda:board.close(timeout=0))
        self.addCleanup(release.set)
        with patch('pler.dashboard.git_links',return_value={('codex','invented','invented'): {}}) as links:
            board.refresh()
            self.assertTrue(entered.wait(3))
            worker=board.thread
            for _ in range(20):
                board.refresh(force=True)
                self.assertIs(board.thread,worker)
            release.set();worker.join(5)
            self.assertFalse(worker.is_alive())
            self.assertEqual(calls,[1,2])
            self.assertEqual(links.call_count,1)
        self.assertEqual(board.state,'ready')
        self.assertEqual(board.sessions[0].calls,2)

    def test_reader_checkpoint_stops_before_the_next_file_and_runs_latest_request(self):
        entered,release=threading.Event(),threading.Event()
        calls=[];after_checkpoint=[]
        def reader():
            calls.append(True)
            if len(calls)==1:
                entered.set()
                if not release.wait(5):raise AssertionError('unreleased synthetic file')
                checkpoint()
                after_checkpoint.append('old scan advanced')
            return [],{}
        board=UsageDashboard(reader)
        self.addCleanup(lambda:board.close(timeout=0))
        self.addCleanup(release.set)
        board.refresh();self.assertTrue(entered.wait(3))
        board.refresh(force=True)
        release.set();board.thread.join(5)
        self.assertEqual((len(calls),after_checkpoint,board.state),(2,[],'ready'))

    def test_close_does_not_wait_for_an_uncooperative_reader_or_start_more_work(self):
        entered,release=threading.Event(),threading.Event()
        def reader():
            entered.set()
            if not release.wait(5):raise AssertionError('unreleased synthetic OS read')
            return [Session('codex','old','old')],{}
        board=UsageDashboard(reader)
        self.addCleanup(lambda:board.close(timeout=0))
        self.addCleanup(release.set)
        board.refresh();self.assertTrue(entered.wait(3))
        self.assertFalse(board.close(timeout=0))
        self.assertFalse(board.refresh(force=True)['started'])
        release.set();board.thread.join(5)
        self.assertTrue(board.close(timeout=0))
        self.assertEqual(board.sessions,[])
        self.assertIsNone(board.scanned_at)

    def test_close_budget_also_applies_when_another_thread_holds_the_snapshot_lock(self):
        board=UsageDashboard(lambda:([],{}))
        entered,release=threading.Event(),threading.Event()
        def slow_projection():
            with board.lock:
                entered.set();release.wait(5)
        worker=threading.Thread(target=slow_projection,daemon=True)
        self.addCleanup(lambda:worker.join(3))
        self.addCleanup(release.set)
        worker.start();self.assertTrue(entered.wait(3))
        self.assertFalse(board.close(timeout=0))
        self.assertTrue(board._closed)
        release.set();worker.join(3)
        self.assertFalse(board.refresh(force=True)['started'])


class FiniteLocalHttpTests(unittest.TestCase):
    def setUp(self):
        class SmallServer(Server):
            max_workers=2
            idle_timeout=5
            request_timeout=30
            def process_request(inner,request,address):
                super().process_request(request,address)
                with inner._requests_lock:
                    if len(inner._requests)==2:inner.two_accepted.set()
        self.server=SmallServer(0,UsageDashboard(lambda:([],{})))
        self.server.two_accepted=threading.Event()
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.peers=[]
        self.addCleanup(self.finish)

    def finish(self):
        for peer in self.peers:peer.close()
        self.server.shutdown();self.server.server_close();self.thread.join(3)

    def peer(self,data):
        peer=socket.create_connection(self.server.server_address,timeout=3)
        self.peers.append(peer);peer.sendall(data)
        return peer

    def health(self):
        client=http.client.HTTPConnection(*self.server.server_address,timeout=3)
        client.request('GET','/api/health')
        result=client.getresponse();status=result.status;result.read();client.close()
        return status

    def test_unfinished_headers_are_capped_and_capacity_recovers(self):
        first=self.peer(b'GET /')
        second=self.peer(b'GET /')
        self.assertTrue(self.server.two_accepted.wait(3))
        third=self.peer(b'GET /api/health HTTP/1.0\r\n\r\n')
        # Refused without a response: an orderly close, or an abortive one (reset on POSIX, WinError 10053 on Windows).
        try:self.assertEqual(third.recv(100),b'')
        except (ConnectionResetError,ConnectionAbortedError):pass
        with self.server._requests_lock:self.assertEqual(len(self.server._requests),2)
        # Wake the existing handlers, then use their worker-slot completion as the barrier.
        first.shutdown(socket.SHUT_RDWR);second.shutdown(socket.SHUT_RDWR)
        acquired=[]
        try:
            for _ in range(2):
                self.assertTrue(self.server._slots.acquire(timeout=3));acquired.append(True)
        finally:
            for _ in acquired:self.server._slots.release()
        self.assertEqual(self.health(),200)

    def test_total_deadline_interrupts_a_partial_header_independent_of_idle_timeout(self):
        first=self.peer(b'GET /')
        second=self.peer(b'GET /')
        self.assertTrue(self.server.two_accepted.wait(3))
        # Advance only the server's deadline comparison; sockets keep their normal idle timeout.
        with self.server._requests_lock:
            end=max(self.server._requests.values())+1
        with patch('pler.server.time.monotonic',return_value=end):self.server.service_actions()
        for peer in (first,second):
            try:self.assertEqual(peer.recv(100),b'')
            except ConnectionResetError:pass

    def test_partial_authenticated_body_cannot_trigger_an_action_and_is_closed_on_deadline(self):
        head=('POST /api/usage/refresh HTTP/1.0\r\nHost: '+self.server.origin.split('//')[1]+
              '\r\nOrigin: '+self.server.origin+'\r\nX-PLER-Token: '+self.server.token+
              '\r\nContent-Type: application/json\r\nContent-Length: 2\r\n\r\n{').encode('ascii')
        with patch.object(self.server.dashboard,'refresh',side_effect=AssertionError('incomplete action ran')):
            first=self.peer(head);second=self.peer(head)
            self.assertTrue(self.server.two_accepted.wait(3))
            with self.server._requests_lock:end=max(self.server._requests.values())+1
            with patch('pler.server.time.monotonic',return_value=end):self.server.service_actions()
            for peer in (first,second):
                # An EOF after a partial JSON document can produce an ordinary 400 or close directly.
                try:received=peer.recv(4096)
                except ConnectionResetError:received=b''
                self.assertTrue(not received or received.startswith(b'HTTP/1.0 400'))

    def test_closing_server_also_closes_its_dashboard(self):
        self.server.shutdown();self.thread.join(3)
        self.server.server_close()
        self.assertFalse(self.server.dashboard.refresh(force=True)['started'])


if __name__=='__main__':unittest.main()
