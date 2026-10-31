"""Select and cache the pinned Android launcher without bundling it in Windows."""
import json
import os
import tempfile
import urllib.request
from pathlib import Path

from tools_core import matches


def select_android_runtime(abis, manifest):
    for abi in (item.strip() for item in abis.split(',')):
        if abi in ('arm64-v8a', 'armeabi-v7a', 'x86_64') and abi in manifest['variants']:
            return abi, manifest['variants'][abi]
    raise ValueError('No Android launcher is available for this TV CPU architecture.')


def prepare_android_runtime(abis, cache, progress=lambda message: None, manifest=None):
    if manifest is None:
        manifest = json.loads((Path(__file__).resolve().parent / 'assets/android-runtime.json').read_text())
    abi, spec = select_android_runtime(abis, manifest)
    if not spec['url'].startswith('https://'):
        raise ValueError('Android runtime downloads require HTTPS.')
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / ('Kart64TV-' + abi + '-' + spec['sha256'] + '.apk')
    if target.is_symlink():
        raise ValueError('Android runtime cache must not be a symbolic link.')
    if matches(target, spec['size'], spec['sha256']):
        progress('Using the verified cached Android launcher (' + abi + ').')
        return target
    progress('Downloading the Android launcher for ' + abi + ' (' + str(round(spec['size'] / 1048576)) + ' MiB)…')
    request = urllib.request.Request(spec['url'], headers={'User-Agent': 'Kart64-TV-Installer'})
    with tempfile.TemporaryDirectory(prefix='download-', dir=cache) as temp:
        partial = Path(temp) / 'launcher.part'
        with urllib.request.urlopen(request, timeout=90) as response, partial.open('xb') as out:
            if not response.geturl().startswith('https://'):
                raise ValueError('Android runtime downloads require HTTPS after redirects.')
            count = 0
            reported = 0
            while block := response.read(1024 * 1024):
                count += len(block)
                if count > spec['size']:
                    raise ValueError('Android runtime download exceeded its expected size.')
                out.write(block)
                if count - reported >= 8 * 1024 * 1024:
                    progress('Android launcher download: ' + str(round(100 * count / spec['size'])) + '%')
                    reported = count
        if not matches(partial, spec['size'], spec['sha256']):
            raise ValueError('Android runtime failed its size or SHA-256 integrity check. Retry the installation.')
        os.replace(partial, target)
    return target
