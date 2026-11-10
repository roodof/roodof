"""Stable terminal bootstrap; active versions and private data never replace this entry point."""
import os
from pathlib import Path
import subprocess
import sys
from . import update_crypto
from .updates import local,recover_pending,selected_root


def main():
    root=local(Path(__file__).absolute().parents[2]);lease=None
    try:
        if (root/'.pler-pending').exists():
            lease=update_crypto.InstallationLease(root,exclusive=True)
            recover_pending(root);lease.close();lease=None
        lease=update_crypto.InstallationLease(root)
        run=selected_root(root);env=os.environ.copy()
        env.update(PLER_INSTALL_ROOT=str(root),PLER_LAUNCHER_PID=str(os.getpid()))
        return subprocess.call([str(run/'runtime/python.exe'),'-I','-S',str(run/'app/start.py'),*sys.argv[1:]],env=env)
    except Exception:
        print('Roodof could not select a safe installed version. Retry after any update finishes.',file=sys.stderr);return 1
    finally:
        if lease:lease.close()
