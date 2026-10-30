# Windows x64 build: python -m PyInstaller --noconfirm Kart64TV.spec
from pathlib import Path
import PySide6,os,json,hashlib

project = Path(SPECPATH)
qt = Path(PySide6.__file__).resolve().parent
android_apk=Path(os.environ.get('KART64_ANDROID_APK',str(project/'assets'/'kart64-android.apk')))
pin=json.loads((project/'assets'/'android-runtime.json').read_text())
with android_apk.open('rb') as source:
    if hashlib.file_digest(source,'sha256').hexdigest()!=pin['sha256']:raise ValueError('Rebuild the Android runtime or select the verified KART64_ANDROID_APK before packaging.')
art=[(str(p),'assets') for p in (project/'assets').iterdir() if p.is_file() and p.name != 'kart64-master.png' and p.suffix.lower() in ('.png','.ico','.json')]
a = Analysis(
    [str(project / 'studio.py')],
    pathex=[],
    binaries=[(str(qt / 'VCRUNTIME140.dll'), '.'), (str(qt / 'VCRUNTIME140_1.dll'), '.')],
    datas=[(str(project / 'src'), 'src'), (str(project / 'benchmark'), 'benchmark')]+art+[(str(android_apk),'assets')],
    hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
# Windows supplies the unversioned ICU API used by Qt. A separate application on
# the build machine may place an incompatible, versioned ICU on PATH.
a.binaries = [item for item in a.binaries if item[0].lower() != 'icuuc.dll' and not (item[0].lower().startswith('icudt') and item[0].lower().endswith('.dll'))]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='Kart64TV', debug=False,
          bootloader_ignore_signals=False, strip=False, upx=True, console=False,icon=str(project/'assets'/'kart64.ico'))
