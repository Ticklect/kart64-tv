"""Best-effort local SSDP discovery. Discovery is not proof of compatibility."""
import ipaddress, socket, time, urllib.parse, urllib.request, urllib.error
import xml.etree.ElementTree as ET
from installer_core import validate_tv_ip

def parse_description(data, ip):
    if len(data)>262144 or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper(): return None
    try:
        ip=validate_tv_ip(ip);root=ET.fromstring(data)
    except (ValueError,ET.ParseError):return None
    device=next((x for x in root.iter() if x.tag.split('}')[-1]=='device'),None)
    if device is None:return None
    fields={x.tag.split('}')[-1]:(x.text or '') for x in device}
    def clean(key):return ''.join(c for c in fields.get(key,'') if c.isprintable())[:80]
    name,model,maker,kind=map(clean,('friendlyName','modelName','manufacturer','deviceType'))
    if model.strip().lower() in ('renderer','media renderer','smarttv'):model=''
    combined=(name+' '+model+' '+maker+' '+kind).lower()
    brands=(('samsung','Samsung'),('lg electronics','LG'),('lge','LG'),('roku','Roku'),('sony','Sony'),('hisense','Hisense'),('tcl','TCL'),('philips','Philips'),('panasonic','Panasonic'))
    brand=next((label for needle,label in brands if needle in combined),'Other')
    description=fields.get('modelDescription','')
    if brand=='Other' and any(line.strip().lower()=='brand=his' for line in description.splitlines()):brand='Hisense (likely)'
    if not (any(x in combined for x in ('television','smart tv','smarttv','android tv','google tv','webos','roku tv','tvdevice','tv device')) or (brand!='Other' and ('mediarenderer' in combined or 'tv' in combined))):return None
    return {'ip':ip,'name':name,'model':model,'brand':brand,'supported':False}

def merge_devices(samsung, others):
    results={d['ip']:{**d,'brand':'Samsung','supported':True} for d in samsung}
    for d in others:
        if d['ip'] not in results:results[d['ip']]=d
    return list(results.values())

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def discover_other_tvs(seconds=3):
    message=('M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nMX: 2\r\nST: ssdp:all\r\n\r\n').encode('ascii')
    locations={};end=time.monotonic()+seconds
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        sock.settimeout(.3);sock.sendto(message,('239.255.255.250',1900))
        while time.monotonic()<end and len(locations)<32:
            try:data,peer=sock.recvfrom(8192)
            except socket.timeout:continue
            try:
                ip=validate_tv_ip(peer[0]);headers=data.decode('iso-8859-1').splitlines()
                location=next((x.split(':',1)[1].strip() for x in headers if x.lower().startswith('location:')),None)
                u=urllib.parse.urlsplit(location or '')
                if u.scheme!='http' or u.username or u.password or u.hostname!=ip:continue
                locations[ip]=location
            except (ValueError,IndexError):continue
    found=[];opener=urllib.request.build_opener(NoRedirect,urllib.request.ProxyHandler({}))
    for ip,url in locations.items():
        try:
            with opener.open(url,timeout=1) as response:data=response.read(262145)
            item=parse_description(data,ip)
            if item:found.append(item)
        except (OSError,ValueError,urllib.error.URLError):continue
    return found
