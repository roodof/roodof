"""Offline local portable candidate using an existing CPython 3.12 runtime and Windows C# compiler.

No download, global install, registry setting or signing is performed. Output must not already exist.
The application remains private until publisher, license and signing decisions are resolved.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

PRODUCT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--runtime', type=Path, required=True)
parser.add_argument('--compiler', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if os.name != 'nt':
    parser.error('The Windows portable candidate must be built on Windows.')
for path in (args.runtime, args.compiler, args.output):
    if not path.is_absolute() or str(path).startswith(('\\\\', '//')):
        parser.error('Use explicit local absolute paths.')
if args.output.exists():
    parser.error('Output already exists; select a new folder. Nothing was overwritten.')
for name in ('python.exe', 'python312.dll', 'LICENSE.txt'):
    if not (args.runtime/name).is_file():
        parser.error('The supplied runtime is not the expected existing CPython 3.12 folder.')
sys.path.insert(0, str(PRODUCT/'src'))
from pler import __version__

out = args.output
out.mkdir(parents=True)
runtime = out/'runtime'
(runtime/'DLLs').mkdir(parents=True)
for name in ('python.exe', 'python312.dll', 'python3.dll', 'vcruntime140.dll', 'vcruntime140_1.dll', 'LICENSE.txt'):
    shutil.copy2(args.runtime/name, runtime/name)
# These modules support the local HTTP server, select and Unicode handling. No TLS, database,
# third-party package, pip, compiler or development environment is included in the private candidate.
for name in ('_socket.pyd', 'select.pyd', 'unicodedata.pyd'):
    shutil.copy2(args.runtime/'DLLs'/name, runtime/'DLLs'/name)
excluded = {'site-packages', '__pycache__', 'test', 'tests', 'idlelib', 'tkinter', 'turtledemo', 'ensurepip', 'venv'}
with zipfile.ZipFile(runtime/'python312.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((args.runtime/'Lib').rglob('*')):
        relative = path.relative_to(args.runtime/'Lib')
        if path.is_file() and not (set(relative.parts)&excluded) and path.suffix not in ('.pyc', '.pyo'):
            archive.write(path, relative.as_posix())
(runtime/'python312._pth').write_text('python312.zip\nDLLs\n../app\n', 'utf-8')
app = out/'app'
shutil.copytree(PRODUCT/'src'/'pler', app/'pler', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
(app/'start.py').write_text('from pler.cli import main\nraise SystemExit(main())\n', 'utf-8')
(out/'PLER.cmd').write_text('@echo off\r\n"%~dp0runtime\\python.exe" -I -S "%~dp0app\\start.py" %*\r\n', 'utf-8')
subprocess.run([str(args.compiler), '/nologo', '/target:winexe', '/platform:x64',
                '/reference:System.Windows.Forms.dll', '/out:'+str(out/'PLER.exe'),
                str(PRODUCT/'tools/windows/Launcher.cs')], check=True, capture_output=True, text=True)
(out/'README.txt').write_text(
    'PLER '+__version__+' - Windows x64 local candidate\n\n'
    '1. Extract the whole ZIP file into a folder.\n'
    '2. Open PLER.exe. Python is not required.\n'
    '3. Close the application with the Close button on its page.\n'
    'Terminal report: PLER.cmd report --json\n\n'
    'This candidate is unsigned; public distribution has not been approved.\n'
    'Do not bypass a SmartScreen/security warning. Clean-machine acceptance is pending.\n'
    'Uninstall: close the application and delete this extracted folder.\n'
    'Existing agent logs and Claude settings are not changed.\n'
    'The cache lives in the user cache folder and is not deleted automatically.\n'
    'This package uses the Windows C Runtime and .NET Framework 4.5+ components.\n'
    'Turkish: OKU.txt\n', 'utf-8')
(out/'OKU.txt').write_text(
    'PLER '+__version__+' — Windows x64 yerel aday\n\n'
    '1. ZIP dosyasinin tamamini bir klasore cikarin.\n'
    '2. PLER.exe dosyasini acin. Python kurmaniz gerekmez.\n'
    '3. Uygulamayi sayfadaki Kapat dugmesiyle kapatin.\n'
    'Terminal raporu: PLER.cmd report --json\n\n'
    'Bu aday imzasizdir; genel dagitim onayi verilmemistir.\n'
    'SmartScreen/guvenlik uyarisini atlatmayin. Temiz makine kabul testi bekliyor.\n'
    'Kaldirma: uygulamayi kapatip bu cikartilan klasoru silin.\n'
    'Mevcut ajan kayitlari ve Claude ayarlari degistirilmez.\n'
    'Onbellek kullanici onbellek dizinindedir; otomatik silinmez.\n'
    'Bu paket Windows sisteminin C Runtime ve .NET Framework 4.5+ bilesenlerini kullanir.\n', 'utf-8')
(out/'THIRD-PARTY-NOTICES.txt').write_text(
    'Private local candidate; no public redistribution has been authorized.\n'
    'CPython 3.12 is bundled unmodified; its complete supplied notice is runtime/LICENSE.txt.\n'
    'The Python runtime is selected from the existing local development runtime.\n'
    'Microsoft runtime components accompany that runtime. Publisher/license/redistribution review\n'
    'and code signing remain release gates. This file grants no new license to the PLER application.\n', 'utf-8')
files = [p for p in out.rglob('*') if p.is_file()]
manifest = dict(version=__version__,platform='windows-x64',private_candidate=True,signed=False,
                runtime='CPython 3.12',files={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                                           for p in sorted(files)})
(out/'manifest.json').write_text(json.dumps(manifest,indent=2),'utf-8')
# with_suffix would turn a versioned folder such as pler-0.2.5 into pler-0.2.zip.
archive_path = out.with_name(out.name + '.zip')
if archive_path.exists():
    parser.error('Archive already exists; candidate folder preserved, no archive overwritten.')
with zipfile.ZipFile(archive_path,'w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(out.rglob('*')):
        if path.is_file(): archive.write(path,out.name+'/'+path.relative_to(out).as_posix())
print(json.dumps(dict(version=__version__,files=len(files)+1,zip_bytes=archive_path.stat().st_size,
                      zip_sha256=hashlib.sha256(archive_path.read_bytes()).hexdigest()),indent=2))
