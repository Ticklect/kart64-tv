"""Experimental webOS staging only; not verified on an LG TV."""
from pathlib import Path
import json,shutil,struct,zlib
from installer_core import validate_archive

FILES=('index.html','Spaghettify.js','Spaghettify.wasm','spaghetti.o2r','courses.json','courses/silverstone/silverstone-v1.9.o2r','diagnostics.js','packaged-boot.js')

def make_icon(size):
    rows=[]
    for y in range(size):
        row=bytearray()
        for x in range(size):
            # A simple original geometric K, with no game artwork.
            on=(size*.22<x<size*.32 and size*.18<y<size*.82) or (size*.3<x<size*.73 and abs(y-(size*.5-(x-size*.3)*.7))<size*.055) or (size*.3<x<size*.73 and abs(y-(size*.5+(x-size*.3)*.7))<size*.055)
            row.extend((255,255,255,255) if on else (30,56,135,255))
        rows.append(b'\x00'+bytes(row))
    def chunk(name,data):return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b'')

def prepare_webos_stage(runtime,archive,output):
    runtime,output=Path(runtime),Path(output)
    if not output.is_dir() or output.is_symlink() or any(output.iterdir()):raise ValueError('Choose a new empty output directory.')
    if not runtime.is_dir() or runtime.is_symlink():raise ValueError('Runtime directory is missing.')
    if output.resolve()==runtime.resolve() or runtime.resolve() in output.resolve().parents:raise ValueError('Output must be separate from the runtime.')
    archive=validate_archive(archive)
    if output.resolve() in archive.resolve().parents:raise ValueError('Game archive must be outside the output.')
    for name in FILES:
        src=runtime.joinpath(*name.split('/'))
        if not src.is_file() or src.is_symlink() or runtime.resolve() not in src.resolve().parents:raise ValueError('Runtime is incomplete or unsafe.')
    for name in FILES:
        src=runtime.joinpath(*name.split('/'));dest=output.joinpath(*name.split('/'));dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
    shutil.copyfile(archive,output/'mk64.o2r')
    assets=Path(__file__).resolve().parent/'assets'
    shutil.copyfile(assets/'kart64-80.png',output/'icon.png');shutil.copyfile(assets/'kart64-130.png',output/'largeIcon.png')
    info={'id':'com.ticklect.kart64','version':'1.0.0','vendor':'Ticklect','type':'web','main':'index.html','title':'Kart64 TV','icon':'icon.png','largeIcon':'largeIcon.png','iconColor':'#1e3887','requiredACG':[]}
    (output/'appinfo.json').write_text(json.dumps(info,indent=2)+'\n',encoding='utf-8')
    return output
