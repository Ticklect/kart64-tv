"""Local history of explicit compatibility checks; never uploads device data."""
from pathlib import Path
from datetime import datetime,timezone
import json,os,tempfile
from benchmark_core import format_benchmark

def load_results(path):
    try:
        p=Path(path)
        if p.stat().st_size>1024*1024:return []
        data=json.loads(p.read_text(encoding='utf-8'))
        return [x for x in data if isinstance(x,dict)][-100:] if isinstance(data,list) else []
    except (OSError,ValueError):return []

def save_result(path,device,result):
    format_benchmark(result)
    def clean(x):return ''.join(c for c in str(x or '') if c.isprintable())[:80]
    graphics=result.get('graphics')
    item={'time':datetime.now(timezone.utc).isoformat(timespec='seconds'),'brand':clean(device.get('brand','Samsung')),'model':clean(device.get('model','')) or 'Unknown model','status':result['capabilities']['status'],'cpu_iterations':round(result['cpu']['iterationsPerSecond']),'graphics_callbacks':graphics['timing']['callbackRate'] if graphics else None}
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);history=(load_results(path)+[item])[-100:]
    fd,tmp=tempfile.mkstemp(prefix='results-',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(history,f,indent=2)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return item
