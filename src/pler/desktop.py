"""Own the bundled window; credentials stay out of command arguments and files."""
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time


def executable_path():
    return Path(__file__).resolve().parents[2] / 'desktop' / 'PLER-Desktop.exe'


class Window:
    def __init__(self, server):
        executable = executable_path()
        if not executable.is_file():
            raise OSError('The desktop window is missing. Extract the complete desktop package.')
        self.session = tempfile.TemporaryDirectory(prefix='pler-desktop-')
        self.control = Path(self.session.name)
        (self.control / 'running').write_text('1', encoding='ascii')
        env = os.environ.copy()
        for name in ('ELECTRON_RUN_AS_NODE', 'NODE_OPTIONS', 'NODE_PATH'):
            env.pop(name, None)
        # Windows GUI Electron does not inherit stdin reliably. A process-private environment
        # carries the credential; the temporary directory holds only nonsecret lifetime markers.
        env.update(PLER_DESKTOP_URL=server.access_url, PLER_DESKTOP_SESSION=str(self.control),
                   PLER_DESKTOP_PARENT=str(os.getpid()))
        server.desktop_ready = threading.Event()
        try:
            self.process = subprocess.Popen(
                [str(executable)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, env=env,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except OSError:
            self.session.cleanup()
            raise
        threading.Thread(target=self._watch, args=(server,), daemon=True).start()
        threading.Thread(target=self._ready, args=(server,), daemon=True).start()

    def _ready(self, server):
        deadline = time.monotonic() + 30
        while self.process.poll() is None and time.monotonic() < deadline:
            if (self.control / 'ready').is_file():
                server.desktop_ready.set()
                return
            time.sleep(.1)

    def _watch(self, server):
        self.process.wait()
        server.shutdown()

    def close(self):
        (self.control / 'running').unlink(missing_ok=True)
        try:
            self.process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=5)
        finally:
            self.session.cleanup()
