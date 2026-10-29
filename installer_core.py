"""Private, local packaging helpers for the experimental Samsung installer."""
from pathlib import Path
import ipaddress
import zipfile
import hashlib
import stat
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import PurePosixPath

def validate_tv_ip(value):
    try: address = ipaddress.IPv4Address(value.strip())
    except (ValueError, AttributeError) as exc: raise ValueError('Enter a valid local IPv4 address.') from exc
    networks = ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')
    if not any(address in ipaddress.IPv4Network(n) for n in networks): raise ValueError('Enter a private LAN address for your TV.')
    return str(address)

def validate_archive(file):
    file = Path(file)
    if not file.is_file() or file.is_symlink(): raise ValueError('Select a local game-data archive.')
    if file.stat().st_size > 1024 * 1024 * 1024: raise ValueError('Game archive is too large.')
    try:
        with zipfile.ZipFile(file) as z:
            entries = z.infolist()
            if not entries or len(entries)>100000 or sum(x.file_size for x in entries)>2*1024*1024*1024: raise ValueError('Invalid game archive size.')
            if z.testzip() is not None: raise ValueError('Game archive is damaged.')
    except (zipfile.BadZipFile, OSError) as exc: raise ValueError('Select a valid SpaghettiKart game-data archive (.o2r).') from exc
    return file

def make_package(stage,archive,output):
    stage,output=Path(stage),Path(output);archive=validate_archive(archive)
    required=('config.xml','index.html','Spaghettify.js','Spaghettify.wasm','diagnostics.js')
    if not all((stage/n).is_file() for n in required): raise ValueError('Incomplete runtime package.')
    if output.exists(): raise ValueError('Package output already exists.')
    files=sorted(stage.rglob('*'))
    if any(p.is_symlink() for p in files): raise ValueError('Runtime contains a symbolic link.')
    if any(p.name in ('mk64.o2r','author-signature.xml','signature1.xml') for p in files): raise ValueError('Unexpected game data or signature in runtime.')
    with zipfile.ZipFile(output,'x',allowZip64=True) as z:
        for p in files:
            if p.is_file():
                compression=zipfile.ZIP_STORED if p.suffix in ('.wasm','.o2r') else zipfile.ZIP_DEFLATED
                z.write(p,p.relative_to(stage).as_posix(),compress_type=compression)
        z.write(archive,'mk64.o2r',compress_type=zipfile.ZIP_STORED)
    with zipfile.ZipFile(output) as z:
        if z.testzip() is not None: raise ValueError('Package verification failed.')
    return output

def parse_discovery(data):
    if not isinstance(data,dict) or data.get('ok') is not True or not isinstance(data.get('tvs'),list):
        raise ValueError('TV discovery did not complete successfully.')
    found=[];seen=set()
    for item in data['tvs']:
        if not isinstance(item,dict):continue
        try: ip=validate_tv_ip(item.get('ip',''))
        except ValueError: continue
        if ip in seen: continue
        seen.add(ip)
        def clean(key):
            v=item.get(key,'');return ''.join(c for c in v if c.isprintable())[:80] if isinstance(v,str) else ''
        found.append({'ip':ip,'name':clean('name'),'model':clean('model')})
    return found

US_ROM_SHA1='579c48e211ae952530ffc8738709f078d5dd215e'

def identify_game(file):
    file=Path(file)
    if not file.is_file() or file.is_symlink():raise ValueError('Select a local game file.')
    if zipfile.is_zipfile(file):
        validate_archive(file);return 'archive'
    if file.stat().st_size!=12582912:raise ValueError('Please select the supported US Mario Kart 64 .z64 ROM or a compatible .o2r archive.')
    with file.open('rb') as stream:digest=hashlib.file_digest(stream,'sha1').hexdigest()
    if digest!=US_ROM_SHA1:raise ValueError('Please select the supported US Mario Kart 64 .z64 ROM or a compatible .o2r archive.')
    return 'rom'

def safe_extract_release(archive,target):
    target=Path(target)
    with zipfile.ZipFile(archive) as z:
        infos=z.infolist()
        if not infos or len(infos)>2000 or sum(i.file_size for i in infos)>100*1024*1024:raise ValueError('Unexpected extractor archive size.')
        for i in infos:
            name=i.filename; p=PurePosixPath(name)
            if not name or chr(92) in name or p.is_absolute() or any(part in ('.','..') or ':' in part for part in p.parts) or stat.S_ISLNK(i.external_attr>>16):raise ValueError('Unsafe extractor archive path.')
        for i in infos:
            dest=target.joinpath(*PurePosixPath(i.filename).parts)
            if i.is_dir():dest.mkdir(parents=True,exist_ok=True)
            else:
                dest.parent.mkdir(parents=True,exist_ok=True)
                with z.open(i) as source,dest.open('xb') as output:
                    while True:
                        block=source.read(1024*1024)
                        if not block:break
                        output.write(block)
    if not (target/'Spaghettify.exe').is_file():raise ValueError('Extractor executable is missing.')


def verify_extractor(file,size,digest):
    file=Path(file)
    if not file.is_file() or file.is_symlink() or file.stat().st_size!=size:raise ValueError('Extractor download failed its integrity check.')
    with file.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if actual!=digest:raise ValueError('Extractor download failed its integrity check.')
    return True

EXTRACTOR_URL='https://github.com/HarbourMasters/SpaghettiKart/releases/download/1.0.0/spaghetti-windows.zip'
EXTRACTOR_SIZE=7806456
EXTRACTOR_SHA256='bf7bd7cdb5f412c7b370af92949b9431ce7503968631f8cacd607933fb32aff3'

def prepare_rom(rom,workdir,progress=lambda message:None):
    if identify_game(rom)!='rom':raise ValueError('Choose a supported US ROM for conversion.')
    if os.name!='nt':raise ValueError('Automatic ROM preparation currently requires Windows.')
    workdir=Path(workdir);release=workdir/'extractor.zip';target=workdir/'extractor';target.mkdir()
    progress('Downloading the official SpaghettiKart extractor…')
    request=urllib.request.Request(EXTRACTOR_URL,headers={'User-Agent':'Kart64-TV-Installer'})
    with urllib.request.urlopen(request,timeout=60) as response,release.open('xb') as out:
        if not response.geturl().startswith('https://'):raise ValueError('Extractor download requires HTTPS.')
        total=0
        while True:
            chunk=response.read(256*1024)
            if not chunk:break
            total+=len(chunk)
            if total>EXTRACTOR_SIZE:raise ValueError('Extractor download exceeded the expected size.')
            out.write(chunk)
    verify_extractor(release,EXTRACTOR_SIZE,EXTRACTOR_SHA256);safe_extract_release(release,target)
    shutil.copyfile(rom,target/'baserom.us.z64')
    progress('Preparing your game data locally; this may take a few minutes…')
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=subprocess.SW_HIDE
    process=subprocess.Popen([str(target/'Spaghettify.exe')],cwd=target,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW)
    archive=target/'mk64.o2r';deadline=time.monotonic()+300;last_size=None
    try:
        while time.monotonic()<deadline:
            if archive.is_file():
                size=archive.stat().st_size
                if size>0 and size==last_size:
                    try:validate_archive(archive);return archive
                    except ValueError:pass
                last_size=size
            if process.poll() is not None:raise ValueError('The SpaghettiKart preparation tool exited before generating game data.')
            time.sleep(2)
        raise ValueError('Game-data preparation timed out.')
    finally:
        if process.poll() is None:
            process.terminate()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10)
