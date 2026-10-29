"""Samsung benchmark packaging and measured-result handling."""
from pathlib import Path
import json,math,re,zipfile
from webos_core import make_icon

def make_benchmark(source,output,package):
    source,output=Path(source),Path(output)
    if not re.fullmatch(r'KB[0-9A-F]{8}',package):raise ValueError('Invalid benchmark package ID.')
    if output.exists():raise ValueError('Benchmark output already exists.')
    files=('index.html','benchmark.js','run.js')
    if not all((source/n).is_file() and not (source/n).is_symlink() for n in files):raise ValueError('Benchmark files are missing.')
    app=package+'.Check'
    xml=f'''<?xml version="1.0" encoding="UTF-8"?><widget xmlns="http://www.w3.org/ns/widgets" xmlns:tizen="http://tizen.org/ns/widgets" id="http://localhost/kart64-benchmark" version="0.1.0" viewmodes="fullscreen"><tizen:application id="{app}" package="{package}" required_version="6.5"/><content src="index.html"/><icon src="icon.png"/><name>Kart64 TV Check</name><tizen:profile name="tv"/><tizen:setting screen-orientation="landscape" context-menu="disable" background-support="disable"/></widget>'''
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED) as z:
        z.writestr('config.xml',xml);z.writestr('icon.png',make_icon(80))
        for n in files:z.write(source/n,n)
    with zipfile.ZipFile(output) as z:
        if z.testzip() is not None:raise ValueError('Benchmark package is damaged.')
    return app

def parse_debug_port(text):
    match=re.search(r'\bport:\s*(\d{1,5})\b',text)
    if not match or not 1024<=int(match.group(1))<=65535:raise ValueError('TV did not report a valid benchmark debug port.')
    return int(match.group(1))

def format_benchmark(result):
    if not isinstance(result,dict) or result.get('version')!=1:raise ValueError('Invalid benchmark result.')
    cap=result.get('capabilities');cpu=result.get('cpu');graphics=result.get('graphics')
    if not isinstance(cap,dict) or cap.get('status') not in ('features-present-untested','missing-required-features') or not isinstance(cpu,dict):raise ValueError('Invalid benchmark result.')
    lines=['TV compatibility check: '+('required features detected; real-game compatibility still untested' if cap['status']=='features-present-untested' else 'some required features are missing')]
    for key,label in [('webgl2','WebGL2'),('sharedArrayBuffer','SharedArrayBuffer'),('sharedWasm','shared WebAssembly memory'),('audioWorklet','AudioWorklet')]:
        if not isinstance(cap.get(key),bool):raise ValueError('Invalid benchmark capability.')
        lines.append(label+': '+('available' if cap[key] else 'unavailable'))
    v=cpu.get('iterationsPerSecond')
    if not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or not 0<=v<=1e12:raise ValueError('Invalid CPU benchmark result.')
    lines.append('Synthetic CPU work: '+str(round(v))+' iterations/sec')
    if graphics is not None:
        timing=graphics.get('timing') if isinstance(graphics,dict) else None
        if not isinstance(timing,dict) or timing.get('kind')!='animation_callback_rate':raise ValueError('Invalid graphics result.')
        rate=timing.get('callbackRate')
        if not isinstance(rate,(int,float)) or isinstance(rate,bool) or not math.isfinite(rate) or not 0<=rate<=1000:raise ValueError('Invalid graphics timing.')
        lines.append('Synthetic graphics callbacks: '+str(rate)+'/sec (not game FPS)')
    else:lines.append('Synthetic graphics: unavailable')
    lines.append('No FPS prediction: results require calibration against real games on multiple TVs.')
    return '\n'.join(lines)
