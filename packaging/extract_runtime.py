"""Recover the pinned, game-free Android launcher for a desktop rebuild."""
import hashlib, json, sys
from pathlib import Path
from PyInstaller.archive.readers import CArchiveReader

root = Path(__file__).resolve().parents[1]
pin = json.loads((root / 'assets/android-runtime.json').read_text())
data = CArchiveReader(sys.argv[1]).extract('assets\\kart64-android.apk')
if len(data) != pin['size'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
    raise ValueError('Android runtime failed verification')
target = Path(sys.argv[2])
target.parent.mkdir(parents=True, exist_ok=True)
with target.open('xb') as stream:
    stream.write(data)
print('Extracted verified Android runtime:', target)
