"""Offline local portable candidate using an existing CPython 3.12+ runtime and Windows C# compiler.

The runtime is an installed CPython folder (Lib, DLLs) or an extracted official Windows embeddable
package (pythonXY.zip). Python 3.14+ brings the standard-library zstd decoder, which makes the first
read of compressed Codex logs much faster. No download, global install, registry setting or signing is
performed. Output must not already exist. Output defaults to a private candidate; early-beta is an
explicit owner-authorized distribution channel. It does not sign the package or grant application licensing rights.
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
parser.add_argument('--desktop-runtime', type=Path, default=PRODUCT/'desktop/node_modules/electron/dist',
                    help='Installed, pinned Electron Windows x64 distribution (bundled offline).')
parser.add_argument('--channel', choices=('private-candidate', 'early-beta'), default='private-candidate',
                    help='Select early-beta only for an owner-authorized beta distribution.')
args = parser.parse_args()
desktop_source = args.desktop_runtime
if not all((desktop_source/name).is_file() for name in ('electron.exe', 'LICENSE', 'LICENSES.chromium.html', 'version')):
    parser.error('Install the pinned desktop dependency first: cd desktop; npm ci; node node_modules/electron/install.js')
desktop_version = json.loads((PRODUCT/'desktop/package.json').read_text())['devDependencies']['electron']
if (desktop_source/'version').read_text().strip().lstrip('v') != desktop_version:
    parser.error('Desktop runtime version differs from the pinned dependency.')
public_beta = args.channel == 'early-beta'
if os.name != 'nt':
    parser.error('The Windows portable candidate must be built on Windows.')
for path in (args.runtime, args.compiler, args.output):
    if not path.is_absolute() or str(path).startswith(('\\\\', '//')):
        parser.error('Use explicit local absolute paths.')
# with_suffix would turn a versioned folder such as pler-0.2.5 into pler-0.2.zip.
archive_path = args.output.with_name(args.output.name + '.zip')
if args.output.exists() or archive_path.exists():
    parser.error('Output folder or archive already exists; select a new folder. Nothing was overwritten.')
libraries = [p for p in args.runtime.glob('python3*.dll') if p.name != 'python3.dll']
if len(libraries) != 1 or not all((args.runtime/name).is_file() for name in ('python.exe', 'LICENSE.txt')):
    parser.error('The supplied runtime is not an existing CPython folder.')
tag = libraries[0].stem  # python312, python314, ...
python_version = tag[6] + '.' + tag[7:]
if int(tag[7:]) < 12:
    parser.error('CPython 3.12 or newer is required.')
embedded = (args.runtime/(tag + '.zip')).is_file()
extensions = args.runtime if embedded else args.runtime/'DLLs'
sys.path.insert(0, str(PRODUCT/'src'))
from pler import __version__

out = args.output
out.mkdir(parents=True)
(out/'.pler-running.lock').write_bytes(b'')
runtime = out/'runtime'
(runtime/'DLLs').mkdir(parents=True)
for name in ('python.exe', tag + '.dll', 'python3.dll', 'vcruntime140.dll', 'vcruntime140_1.dll', 'LICENSE.txt'):
    shutil.copy2(args.runtime/name, runtime/name)
# TLS/CNG support is used only by explicitly requested or opted-in application updates.
for name in ('_socket.pyd', 'select.pyd', 'unicodedata.pyd', '_zstd.pyd','_ssl.pyd','_hashlib.pyd','_ctypes.pyd'):
    if (extensions/name).is_file():
        shutil.copy2(extensions/name, runtime/'DLLs'/name)
    elif name != '_zstd.pyd' or int(tag[7:]) >= 14:
        parser.error('The supplied runtime lacks %s.' % name)
for name in ('libcrypto-3.dll','libssl-3.dll','libffi-8.dll'):
    if not (args.runtime/name).is_file():parser.error('The supplied runtime lacks '+name)
    shutil.copy2(args.runtime/name,runtime/name)
if embedded:
    # The official embeddable package already holds the compiled standard library.
    shutil.copy2(args.runtime/(tag + '.zip'), runtime/(tag + '.zip'))
else:
    excluded = {'site-packages', '__pycache__', 'test', 'tests', 'idlelib', 'tkinter', 'turtledemo', 'ensurepip', 'venv'}
    with zipfile.ZipFile(runtime/(tag + '.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((args.runtime/'Lib').rglob('*')):
            relative = path.relative_to(args.runtime/'Lib')
            if path.is_file() and not (set(relative.parts)&excluded) and path.suffix not in ('.pyc', '.pyo'):
                archive.write(path, relative.as_posix())
(runtime/(tag + '._pth')).write_text(tag + '.zip\nDLLs\n../app\n', 'utf-8')
app = out/'app'
shutil.copytree(PRODUCT/'src'/'pler', app/'pler', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
(app/'start.py').write_text('from pler.cli import main\nraise SystemExit(main())\n', 'utf-8')
(app/'update_worker.py').write_text('from pler.update_worker import main\nraise SystemExit(main())\n','utf-8')
(app/'update_probe.py').write_text('import sys\nfrom pler.update_worker import probe\nprobe(sys.argv[1],sys.argv[2])\n','utf-8')
(app/'bootstrap.py').write_text('from pler.update_bootstrap import main\nraise SystemExit(main())\n','utf-8')
# Bytes, not text: text mode on Windows would turn each \r\n into \r\r\n.
(out/'PLER.cmd').write_bytes(b'@echo off\r\n"%~dp0runtime\\python.exe" -I -S "%~dp0app\\bootstrap.py" %*\r\n')
# Double-click to try the page with invented data only; the window closes at once, PLER keeps running.
(out/'PLER-Demo.cmd').write_bytes(b'@echo off\r\nstart "" "%~dp0PLER.exe" demo\r\n')
desktop = out/'desktop'
shutil.copytree(desktop_source, desktop, ignore=shutil.ignore_patterns('default_app.asar'))
(desktop/'electron.exe').rename(desktop/'PLER-Desktop.exe')
desktop_app = desktop/'resources/app'
desktop_app.mkdir(parents=True)
for name in ('main.cjs', 'policy.cjs', 'window-state.cjs'):
    shutil.copy2(PRODUCT/'desktop'/name, desktop_app/name)
(desktop_app/'package.json').write_text(json.dumps(dict(name='pler-desktop', productName='PLER',
    version=__version__, main='main.cjs')), 'utf-8')
subprocess.run([str(args.compiler), '/nologo', '/target:winexe', '/platform:x64',
                '/reference:System.Windows.Forms.dll', '/out:'+str(out/'PLER.exe'),
                str(PRODUCT/'tools/windows/Launcher.cs')], check=True, capture_output=True, text=True)
(out/'README.txt').write_text(
    'PLER '+__version__+' - Windows x64 '+('early beta' if public_beta else 'local candidate')+'\n\n'
    '1. Extract the whole ZIP file into a folder.\n'
    '2. Open PLER.exe. Python is not required.\n'
    '   To try it with invented data only, open PLER-Demo.cmd instead.\n'
    '3. PLER opens in its own desktop window. Close the window to stop the application.\n'
    'Terminal report: PLER.cmd report --json\n\n'
    + ('Unsigned early beta.\n' if public_beta else 'This candidate is unsigned; public distribution has not been approved.\n') +
    'Do not bypass a SmartScreen/security warning. Clean-machine acceptance is pending.\n'
    'Uninstall: close the application and delete this extracted folder.\n'
    'Existing agent logs and Claude settings are not changed.\n'
    'The cache lives in the user cache folder and is not deleted automatically.\n'
    'This package bundles Electron '+desktop_version+'; no browser or WebView installation is required.\n'
    'It uses the Windows C Runtime and .NET Framework 4.5+ components.\n'
    '0.2.31 and older: extract this desktop package into a new folder; automatic migration is not supported.\n'
    'Support: plersolutions1st@gmail.com\n'
    'First useful result: open Help in the app for the demo-to-own-records walkthrough.\n'
    'Data: %LOCALAPPDATA%\\pler by default; a chosen data folder stays separate too.\n'
    'Removing the extracted package does not remove saved PLER history.\n'
    'Updates: use Updates in the app. Checking on launch is optional and initially off.\n'
    'Updates contact the release site; agent records and project data are not sent.\n'
    'For the first manual upgrade, extract into a new folder and close the older app.\n'
    'Private recovery backups remain beside the installation in protected .pler-update-* folders.\n'
    'Do not send recovery folders to support or remove an active update.\n'
    'Turkish: OKU.txt\n', 'utf-8')
(out/'OKU.txt').write_text(
    'PLER '+__version__+' — Windows x64 '+('erken beta' if public_beta else 'yerel aday')+'\n\n'
    '1. ZIP dosyasinin tamamini bir klasore cikarin.\n'
    '2. PLER.exe dosyasini acin. Python kurmaniz gerekmez.\n'
    '   Yalniz uydurma verilerle denemek icin PLER-Demo.cmd dosyasini acin.\n'
    '3. PLER kendi masaustu penceresinde acilir. Pencereyi kapatinca uygulama durur.\n'
    'Tarayici veya WebView kurulumu gerekmez; Electron paketle birlikte gelir.\n'
    '0.2.31 ve oncesinden gecis: masaustu paketini yeni klasore cikarin.\n'
    'Terminal raporu: PLER.cmd report --json\n\n'
    + ('Imzasiz erken beta.\n' if public_beta else 'Bu aday imzasizdir; genel dagitim onayi verilmemistir.\n') +
    'SmartScreen/guvenlik uyarisini atlatmayin. Temiz makine kabul testi bekliyor.\n'
    'Kaldirma: uygulamayi kapatip bu cikartilan klasoru silin.\n'
    'Mevcut ajan kayitlari ve Claude ayarlari degistirilmez.\n'
    'Onbellek kullanici onbellek dizinindedir; otomatik silinmez.\n'
    'Bu paket Windows sisteminin C Runtime ve .NET Framework 4.5+ bilesenlerini kullanir.\n'
    'Destek: plersolutions1st@gmail.com\n'
    'Ilk sonuc: demodan kendi kayitlarina gecis icin uygulamadaki Yardim bolumunu ac.\n'
    'Veri: varsayilan %LOCALAPPDATA%\\pler; sectigin veri klasoru de paketten ayri kalir.\n'
    'Paket klasorunu kaldirmak kayitli PLER gecmisini silmez.\n', 'utf-8')
(out/'THIRD-PARTY-NOTICES.txt').write_text(
    ('PLER early beta - bundled component notices.\n' if public_beta else 'Private local candidate; no public redistribution has been authorized.\n') +
    'CPython '+python_version+' is bundled unmodified; its complete supplied notice is runtime/LICENSE.txt.\n'
    'The Python runtime is copied from the supplied '+('official embeddable package' if embedded else 'local installation')+'.\n'
    'Microsoft runtime components accompany that runtime.\n'
    'Electron '+desktop_version+' and Chromium notices: desktop/LICENSE and desktop/LICENSES.chromium.html.\n'
    'UI component notices: app/pler/web/THIRD-PARTY.txt; font license: app/pler/web/Manrope-OFL.txt.\n'
    'These component notices grant no new license to the PLER application.\n'
    'PLER contact: plersolutions1st@gmail.com\n', 'utf-8')
files = [p for p in out.rglob('*') if p.is_file()]
manifest = dict(version=__version__,platform='windows-x64',private_candidate=not public_beta,channel=args.channel,signed=False,
                runtime='CPython '+python_version,desktop='Electron '+desktop_version,files={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                                           for p in sorted(files)})
(out/'manifest.json').write_text(json.dumps(manifest,indent=2),'utf-8')
with zipfile.ZipFile(archive_path,'w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(out.rglob('*')):
        if path.is_file(): archive.write(path,out.name+'/'+path.relative_to(out).as_posix())
print(json.dumps(dict(version=__version__,files=len(files)+1,zip_bytes=archive_path.stat().st_size,
                      zip_sha256=hashlib.sha256(archive_path.read_bytes()).hexdigest()),indent=2))
