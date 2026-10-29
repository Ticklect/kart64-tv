"""Presentation helpers; no performance prediction or compatibility inference."""
def device_status(device,ip):
    if not ip:return ('No TV selected','Find a TV or enter a Samsung TV address.')
    if not device:return ('Manual TV address','Samsung-only setup; the device is not verified.')
    brand=device.get('brand','TV')
    if not device.get('supported',False):return (brand+' TV found','Installation and testing are not supported for this device yet.')
    return ('Samsung TV selected',(device.get('model') or device.get('name') or 'Unknown model')+' · experimental installation')

def latest_for_device(rows,device):
    if not device or not device.get('model'):return None
    return next((r for r in reversed(rows) if r.get('model')==device['model'] and r.get('brand')==device.get('brand')),None)

def game_status(path):
    return 'Game file selected — checked when installation starts' if path else 'No game file selected'
