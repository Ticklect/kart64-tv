"""Remove only this project's fixed app ID from an explicitly selected TV."""
from pathlib import Path
import json,os,shutil,subprocess,urllib.request,urllib.error,re,time
from installer_core import validate_tv_ip
from platforms import platform_for,verify_webos_target
from android_core import validate_android_serial
from tools_core import resolve_cli
from discovery import NoRedirect

APP_ID='com.ticklect.kart64'
SAMSUNG_APP_ID='KART64TV01.Kart64'

def samsung_installed(ip):
    ip=validate_tv_ip(ip)
    opener=urllib.request.build_opener(NoRedirect,urllib.request.ProxyHandler({}))
    try:
        with opener.open('http://'+ip+':8001/api/v2/applications/'+SAMSUNG_APP_ID,timeout=5) as response:
            if response.status!=200:raise ValueError('Could not verify Samsung app state.')
            return True
    except urllib.error.HTTPError as e:
        if e.code==404:return False
        raise ValueError('Could not verify Samsung app state.') from e

def remove_app(device,cli,tool_dir,lg_cli,lg_target,command,progress):
    ip=validate_tv_ip(device.get('ip',''));platform=platform_for(device)
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
    def query(args):
        p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30,creationflags=flags)
        if p.returncode:raise ValueError('Could not verify the selected TV or app state.')
        return p.stdout
    if platform in ('androidtv','firetv'):
        serial=validate_android_serial(device['adb_serial'])
        if serial.split(':')[0]!=ip:raise ValueError('ADB target does not match the selected TV.')
        adb=shutil.which('adb.exe') or shutil.which('adb')
        if not adb:raise ValueError('Android platform-tools are required to uninstall this app.')
        features=query([adb,'-s',serial,'shell','pm','list','features'])
        names={x.strip() for x in features.splitlines()}
        if not names.intersection({'feature:android.software.leanback','feature:amazon.hardware.fire_tv'}):raise ValueError('The authorised target does not report TV features.')
        command([adb,'-s',serial,'uninstall',APP_ID])
        listing=query([adb,'-s',serial,'shell','pm','list','packages',APP_ID])
        if 'package:'+APP_ID in {x.strip() for x in listing.splitlines()}:raise ValueError('The TV still reports Kart64 TV installed.')
    elif platform=='webos':
        folder=Path(lg_cli);install=folder/'ares-install.cmd';setup=folder/'ares-setup-device.cmd'
        if not install.is_file() or not setup.is_file():raise ValueError('Select the official webOS CLI folder under Devices.')
        verify_webos_target(json.loads(query([str(setup),'--listfull'])),lg_target,ip)
        command([str(install),'--device',lg_target,'--remove',APP_ID])
        listing=query([str(install),'--device',lg_target,'--list'])
        if re.search(r'(?m)^\s*'+re.escape(APP_ID)+r'(?:\s|$)',listing):raise ValueError('The LG TV still reports Kart64 TV installed.')
    elif platform=='tizen':
        if not samsung_installed(ip):progress('Kart64 TV is already absent from this Samsung TV.');return
        tool=resolve_cli(cli,tool_dir,progress=progress)
        command([str(tool),'uninstall',SAMSUNG_APP_ID,'--tv',ip])
        for attempt in range(4):
            if not samsung_installed(ip):break
            if attempt==3:raise ValueError('The Samsung TV still reports Kart64 TV installed.')
            time.sleep(.5)
    else:raise ValueError('Uninstall is not available for this TV platform.')
    progress('Kart64 TV removal verified on the selected TV.')
