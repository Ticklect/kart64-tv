# Windows x64 build: python -m PyInstaller --noconfirm Kart64TV.spec
from pathlib import Path
import PySide6,os

project = Path(SPECPATH)
qt = Path(PySide6.__file__).resolve().parent
art=[(str(p),'assets') for p in (project/'assets').iterdir() if p.is_file() and p.name != 'kart64-master.png' and p.suffix.lower() in ('.png','.ico','.json')]
legal=Path(os.environ.get('KART64_RELEASE_LEGAL',str(project/'build'/'release'/'legal')))
notices=[(str(legal),'legal')] if legal.is_dir() else []
a = Analysis(
    [str(project / 'studio.py')],
    pathex=[],
    binaries=[(str(qt / 'VCRUNTIME140.dll'), '.'), (str(qt / 'VCRUNTIME140_1.dll'), '.')],
    datas=[(str(project / 'src'), 'src'), (str(project / 'benchmark'), 'benchmark')]+art+notices,
    hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
# Windows supplies the unversioned ICU API used by Qt. A separate application on
# the build machine may place an incompatible, versioned ICU on PATH.
a.binaries = [item for item in a.binaries if item[0].lower().replace('\\','/').split('/')[-1] not in ('icuuc.dll','opengl32sw.dll') and not (item[0].lower().startswith('icudt') and item[0].lower().endswith('.dll'))]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='Kart64TV', debug=False,
          bootloader_ignore_signals=False, strip=False, upx=True, console=False,icon=str(project/'assets'/'kart64.ico'))
