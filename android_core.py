"""Explicit ADB targets and local-only game content preparation."""
import re,tarfile,io,json,shutil,subprocess
from pathlib import Path
from installer_core import validate_tv_ip,validate_archive
from webos_core import FILES

def classify_android_target(features,sdk,abis):
    names={line.strip().split(':',1)[1] for line in features.splitlines() if line.strip().startswith('feature:')}
    platform='firetv' if 'amazon.hardware.fire_tv' in names else ('androidtv' if 'android.software.leanback' in names else None)
    if platform is None:raise ValueError('The paired target does not report Android TV or Fire OS TV features. Vega OS is not covered by the APK installer.')
    try:level=int(sdk.strip())
    except (ValueError,AttributeError):raise ValueError('Could not verify the Android API level.')
    if level<26:raise ValueError('This runtime requires Android API 26 or later. Fire OS 5 and 6 are too old for this build.')
    if not {'arm64-v8a','armeabi-v7a','x86_64'}.intersection(x.strip() for x in abis.split(',')):raise ValueError('This TV CPU architecture is not included in the current Android runtime.')
    return platform

def validate_android_serial(serial):
    match=re.fullmatch(r'([0-9.]+):([0-9]{1,5})',serial)
    if not match or not 1<=int(match[2])<=65535:raise ValueError('Choose a local TV IP and ADB connection port.')
    return validate_tv_ip(match[1])+':'+str(int(match[2]))

def parse_adb_devices(text):
    result=[]
    for line in text.splitlines():
        fields=line.split()
        if len(fields)<2 or fields[1]!='device':continue
        try:serial=validate_android_serial(fields[0])
        except ValueError:continue
        result.append(serial)
    return result

def create_content_tar(runtime,archive,output):
    runtime,output=Path(runtime),Path(output);archive=validate_archive(archive)
    for name in FILES:
        src=runtime/name
        if not src.is_file() or src.is_symlink() or runtime.resolve() not in src.resolve().parents:raise ValueError('Missing or unsafe runtime file.')
    with tarfile.open(output,'x') as tar:
        for name in FILES:tar.add(runtime/name,arcname=name,recursive=False)
        tar.add(archive,arcname='mk64.o2r',recursive=False)
    return output

def discover_android():
    adb=shutil.which('adb.exe') or shutil.which('adb')
    if not adb:return []
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
    def run(args):return subprocess.run([adb]+args,capture_output=True,text=True,timeout=10,creationflags=flags)
    try:
        listing=run(['devices','-l']);found=[]
        for serial in parse_adb_devices(listing.stdout)[:16]:
            features=run(['-s',serial,'shell','pm','list','features'])
            if features.returncode:continue
            if not any(x in features.stdout.splitlines() for x in ('feature:android.software.leanback','feature:amazon.hardware.fire_tv')):continue
            sdk=run(['-s',serial,'shell','getprop','ro.build.version.sdk']).stdout.strip()
            abis=run(['-s',serial,'shell','getprop','ro.product.cpu.abilist']).stdout.strip()
            error=''
            try:platform=classify_android_target(features.stdout,sdk,abis)
            except ValueError as e:
                platform='firetv' if 'feature:amazon.hardware.fire_tv' in features.stdout.splitlines() else 'androidtv';error=str(e)
            model=run(['-s',serial,'shell','getprop','ro.product.model']).stdout.strip()[:80]
            brand=run(['-s',serial,'shell','getprop','ro.product.manufacturer']).stdout.strip()[:80]
            found.append({'ip':serial.split(':')[0],'name':model or 'TV','model':model,'brand':brand or 'Unknown','platform':platform,'adb_serial':serial,'supported':False,'api_level':sdk,'abis':abis,'android_compatible':not error,'compatibility_error':error})
        return found
    except (OSError,subprocess.TimeoutExpired):return []
