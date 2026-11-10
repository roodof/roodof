"""Build PLER-Setup.exe from a portable package ZIP made by build_windows_portable.py.

Usage: python tools/build_windows_setup.py --package ABS\\pler-X.Y.Z.zip --compiler ABS\\csc.exe --output ABS\\PLER-Setup-X.Y.Z.exe
The ZIP is embedded unchanged as a resource, so a later Authenticode signature covers the whole
installer. tools/windows/Setup.cs is compiled twice: once as the small uninstaller (no package),
then as the installer that carries both the package and that uninstaller.
"""
import argparse, hashlib, json, re, subprocess, tempfile, zipfile
from pathlib import Path

PRODUCT = Path(__file__).resolve().parents[1]
SOURCE = PRODUCT/'tools/windows/Setup.cs'
ICON = PRODUCT/'assets/icon/pler.ico'
REFERENCES = ('System.Windows.Forms.dll', 'System.Drawing.dll', 'System.IO.Compression.dll', 'System.Web.Extensions.dll')

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--package', type=Path, required=True)
parser.add_argument('--compiler', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
for path in (args.package, args.compiler, args.output):
    if not path.is_absolute():
        raise SystemExit('Use explicit local absolute paths.')
if args.output.exists():
    raise SystemExit('The output file already exists.')

with zipfile.ZipFile(args.package) as archive:
    names = archive.namelist()
    tops = {name.split('/')[0] for name in names}
    if len(tops) != 1:
        raise SystemExit('The package must contain one top folder.')
    manifest = json.loads(archive.read(tops.pop() + '/manifest.json'))
version = manifest['version']
if manifest.get('platform') != 'windows-x64' or not re.fullmatch(r'\d+\.\d+\.\d+', version):
    raise SystemExit('Not a Windows x64 Roodof package.')


def compile(output, resources=()):
    command = [str(args.compiler), '/nologo', '/target:winexe', '/platform:x64', '/optimize+', '/codepage:65001',
               '/win32icon:' + str(ICON), '/out:' + str(output)]
    command += ['/reference:' + name for name in REFERENCES]
    command += ['/resource:' + str(path) + ',' + name for path, name in resources]
    command += [str(SOURCE), str(info)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(result.stdout + result.stderr)


with tempfile.TemporaryDirectory() as temp:
    temp = Path(temp)
    info = temp/'VersionInfo.cs'
    info.write_text('[assembly: System.Reflection.AssemblyVersion("%s.0")]\n'
                    '[assembly: System.Reflection.AssemblyFileVersion("%s.0")]\n'
                    '[assembly: System.Reflection.AssemblyInformationalVersion("%s")]\n' % (version, version, version), 'utf-8')
    uninstaller = temp/'Uninstall PLER.exe'
    compile(uninstaller)
    compile(args.output, ((args.package, 'pler-package.zip'), (uninstaller, 'pler-uninstall.exe')))

data = args.output.read_bytes()
print(json.dumps(dict(version=version, setup=args.output.name, bytes=len(data),
                      sha256=hashlib.sha256(data).hexdigest(), signed=False), indent=2))
