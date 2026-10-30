"""Collect notices and corresponding Qt sources for the Windows release."""
import argparse, hashlib, importlib.metadata, io, json, re, shutil, sys, tarfile, urllib.request, zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def prepare(cache, output, apk):
    cache.mkdir(parents=True, exist_ok=True)
    legal = output / 'legal'
    legal.mkdir(parents=True, exist_ok=True)
    pins = json.loads((ROOT / 'packaging/dependency-sources.json').read_text())
    for pin in pins:
        archive = cache / pin['file']
        if not archive.exists():
            with urllib.request.urlopen(pin['url'], timeout=90) as response, archive.open('xb') as target:
                count = 0
                while block := response.read(1024 * 1024):
                    count += len(block)
                    if count > pin['size']:
                        raise ValueError('Source download exceeded its pinned size')
                    target.write(block)
        with archive.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if archive.stat().st_size != pin['size'] or digest != pin['sha256']:
            raise ValueError('Source archive failed verification: ' + pin['file'])
        with tarfile.open(archive) as source:
            for member in source:
                path = PurePosixPath(member.name)
                if not member.isfile() or member.size > 2 * 1024 * 1024:
                    continue
                if not (re.match(r'(?i)^(license|licence|copying|copyright|notice)([._-].*)?$', path.name) or 'LICENSES' in path.parts):
                    continue
                if path.is_absolute() or any(part in ('.', '..') or ':' in part or '\\' in part for part in path.parts):
                    raise ValueError('Unsafe license path')
                dest = legal.joinpath(*path.parts)
                dest.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as stream, dest.open('wb') as target:
                    shutil.copyfileobj(stream, target)
        print('Verified sources and collected notices:', pin['file'], flush=True)
    for name in ('LICENSE', 'NOTICE.md'):
        shutil.copyfile(ROOT / name, legal / name)
    shutil.copyfile(Path(sys.base_prefix) / 'LICENSE.txt', legal / 'Python-LICENSE.txt')
    distribution = importlib.metadata.distribution('pyinstaller')
    for file in distribution.files:
        if str(file).endswith('licenses/COPYING.txt'):
            shutil.copyfile(distribution.locate_file(file), legal / 'PyInstaller-COPYING.txt')
    for component in ('tcl8.6', 'tk8.6'):
        file = Path(sys.base_prefix) / 'tcl' / component / 'license.terms'
        if file.exists():
            shutil.copyfile(file, legal / (component + '-license.txt'))
    with zipfile.ZipFile(apk) as android:
        if any(n.lower().endswith(('.o2r', '.z64', '.n64', '.v64', '.xcz', '.p12', '.pfx', '.key', '.keystore')) for n in android.namelist()):
            raise ValueError('Private content in Android runtime')
        with zipfile.ZipFile(io.BytesIO(android.read('assets/omni.ja'))) as gecko:
            (legal / 'GeckoView-LICENSES.html').write_bytes(gecko.read('chrome/toolkit/content/global/license.html'))
        for name in android.namelist():
            if name.startswith('META-INF/androidx/') and name.endswith('/LICENSE.txt'):
                dest = legal / 'androidx' / name.removeprefix('META-INF/androidx/')
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(android.read(name))
    nano = urllib.request.urlopen('https://raw.githubusercontent.com/NanoHttpd/nanohttpd/nanohttpd-project-2.3.1/LICENSE.md', timeout=30).read()
    (legal / 'NanoHTTPD-LICENSE.md').write_bytes(nano)
    shutil.copyfile(ROOT / 'packaging/SOURCES.md', legal / 'SOURCES.md')
    shutil.copyfile(ROOT / 'packaging/dependency-sources.json', legal / 'dependency-sources.json')
    bundle = output / 'Kart64TV-1.0-DependencySources.zip'
    with zipfile.ZipFile(bundle, 'w', allowZip64=True) as target:
        for pin in pins:
            target.write(cache / pin['file'], 'sources/' + pin['file'], compress_type=zipfile.ZIP_STORED)
        for file in legal.rglob('*'):
            if file.is_file():
                target.write(file, 'legal/' + file.relative_to(legal).as_posix(), compress_type=zipfile.ZIP_DEFLATED)
    print('Prepared:', bundle, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--apk', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.cache, args.output, args.apk)
