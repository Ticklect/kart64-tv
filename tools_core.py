"""Download pinned Windows tools without modifying system-wide installations."""
from pathlib import Path
import hashlib, os, platform, tempfile, urllib.request, zipfile

TOOLS={
 'sdb':{'url':'https://download.tizen.org/sdk/tizenstudio/official/binary/sdb_4.2.36_windows-64.zip','zipSize':1899533,'zipSha256':'829c504db12ce3e9a598a457762a030d606836cec916c45438623618fc94333c','entry':'data/tools/sdb.exe','exeSize':4956936,'exeSha256':'adeaabc381fedc9d7ba536d2f272e4ad1a24584673c2bc33ee51f70edb908169','filename':'sdb.exe'},
 'node':{'url':'https://nodejs.org/dist/v22.21.1/node-v22.21.1-win-x64.zip','zipSize':35556042,'zipSha256':'3c624e9fbe07e3217552ec52a0f84e2bdc2e6ffa7348f3fdfb9fbf8f42e23fcf','entry':'node-v22.21.1-win-x64/node.exe','exeSize':85800448,'exeSha256':'471961cb355311c9a9dd8ba417eca8269ead32a2231653084112554cda52e8b3','filename':'node.exe'},
 'apps2samsung':{'url':'https://github.com/Apps2Samsung/Apps2Samsung/releases/download/v3.1.0/Apps2Samsung-cli-v3.1.0-win-x64.zip','zipSize':34492438,'zipSha256':'02e9228c81f6b519879036a7041b40233ddca0e908a46952ebbcd1e1ed8e5a42','entry':'apps2samsung-cli.exe','exeSize':79738754,'exeSha256':'29b64e7791b83ebfe95d1ff3f697e0bc4f856f070ad0fbf27e433e4cdfb58a55','filename':'apps2samsung-cli.exe'}}

def matches(file,size,digest):
    f=Path(file)
    if not f.is_file() or f.is_symlink() or f.stat().st_size!=size:return False
    with f.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()==digest

def unpack_verified_tool(archive,target,spec):
    archive,target=Path(archive),Path(target)
    if not matches(archive,spec['zipSize'],spec['zipSha256']):raise ValueError('Tool archive failed its integrity check.')
    if target.exists():
        if not matches(target,spec['exeSize'],spec['exeSha256']):raise ValueError('Existing tool failed its integrity check.')
        return target
    created=False
    try:
        with zipfile.ZipFile(archive) as z:
            info=z.getinfo(spec['entry'])
            if info.file_size!=spec['exeSize'] or info.is_dir():raise ValueError('Unexpected tool size.')
            with z.open(info) as source,target.open('xb') as out:
                created=True;count=0
                while True:
                    data=source.read(1024*1024)
                    if not data:break
                    count+=len(data)
                    if count>spec['exeSize']:raise ValueError('Unexpected tool size.')
                    out.write(data)
        if not matches(target,spec['exeSize'],spec['exeSha256']):raise ValueError('Tool executable failed its integrity check.')
    except Exception:
        if created and target.is_file() and not target.is_symlink():target.unlink()
        raise
    return target

def prepare_tool(name,folder,progress=lambda message:None):
    if name not in TOOLS:raise ValueError('Unknown tool.')
    if os.name!='nt' or platform.machine().lower() not in ('amd64','x86_64'):raise ValueError('Automatic tools currently support Windows x64 only.')
    spec=TOOLS[name];folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);target=folder/spec['filename']
    if target.exists():
        if not matches(target,spec['exeSize'],spec['exeSha256']):raise ValueError('Existing tool failed its integrity check.')
        return target
    progress('Downloading and verifying '+({'node':'Node.js','apps2samsung':'Apps2Samsung','sdb':'Samsung debugging tools'}[name])+'…')
    with tempfile.TemporaryDirectory(prefix='download-',dir=folder) as temp:
        archive=Path(temp)/'tool.zip'
        request=urllib.request.Request(spec['url'],headers={'User-Agent':'Kart64-TV-Installer'})
        with urllib.request.urlopen(request,timeout=90) as response,archive.open('xb') as out:
            if not response.geturl().startswith('https://'):raise ValueError('Tool download requires HTTPS.')
            total=0
            while True:
                b=response.read(1024*1024)
                if not b:break
                total+=len(b)
                if total>spec['zipSize']:raise ValueError('Tool download exceeded its expected size.')
                out.write(b)
        return unpack_verified_tool(archive,target,spec)

def resolve_cli(override,folder,preparer=prepare_tool,progress=lambda message:None):
    if override:
        cli=Path(override).resolve()
        if not cli.is_file() or cli.name.lower()!='apps2samsung-cli.exe':raise ValueError('Choose apps2samsung-cli.exe.')
        return cli
    return preparer('apps2samsung',folder,progress)
