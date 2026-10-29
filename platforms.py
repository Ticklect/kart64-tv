"""Installation routes are distinct from confirmed game compatibility."""
import re
from installer_core import validate_tv_ip

def platform_for(device):
    if device.get('platform') in ('androidtv','firetv') and device.get('adb_serial'):return device['platform']
    return {'Samsung':'tizen','LG':'webos'}.get(device.get('brand'),'unknown')

def verify_webos_target(rows,name,ip):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',name):raise ValueError('Enter a valid registered LG device name.')
    ip=validate_tv_ip(ip)
    if not isinstance(rows,list):raise ValueError('Could not read registered webOS devices.')
    for row in rows:
        if isinstance(row,dict) and row.get('name')==name and row.get('profile')=='tv' and row.get('deviceinfo',{}).get('ip')==ip:return name
    raise ValueError('The registered LG device does not match the selected TV IP. Check webOS CLI setup.')
