"""Real catalogue operations reused by the shared SDK registry, without model calls."""
import json
import os
from pathlib import Path
import sys
import tempfile
from .transport import Client, version
from . import catalog
from .__main__ import library_path, scan_state

def run(request):
    client=Client(request['pipe']); state=client.state(request['runtime'])
    args=request['arguments']; expected=request.get('expected',{})
    if any(state.get(k)!=v for k,v in expected.items()): raise ValueError('Instance changed before catalogue operation')
    if args.get('prompt_id') and (not state['prompt']['pending'] or state['prompt']['id']!=args['prompt_id']): raise ValueError('Request cancelled')
    method=request['method']; library=library_path(state)
    if method=='catalog_scan':return scan_state(state)
    if method=='catalog_read':return catalog.load(library/'catalog.json', {'effects':[]})
    if method=='store_effect_description':
        current=scan_state(state)
        if not current['complete']:raise ValueError('Resolve catalogue scan errors first')
        effects=[e for e in current['effects'] if e['fingerprint']==args['fingerprint']]
        if len(effects)!=1:raise ValueError('Unknown or changed effect fingerprint')
        return catalog.store_description(library,effects[0],args['text'],args.get('model','assistant'))
    with tempfile.TemporaryDirectory(prefix='cyrs-catalog-') as temp:
        path=Path(temp)/'metadata.json'
        if method=='catalog_export':
            catalog.export_library(library,path)
            return json.loads(path.read_text(encoding='utf-8'))
        if method=='catalog_import':
            path.write_text(json.dumps(args['data'],ensure_ascii=False),encoding='utf-8')
            return {'imported':catalog.import_library(library,path)}
    raise ValueError('Unknown catalogue operation')

def main():
    # Windowed PyInstaller intentionally leaves stdio unset; the owned parent supplies pipes.
    if sys.stdin is None or sys.stdout is None:
        import ctypes, msvcrt
        from ctypes import wintypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.GetStdHandle.argtypes=[wintypes.DWORD];kernel.GetStdHandle.restype=wintypes.HANDLE
        if sys.stdin is None:sys.stdin=open(msvcrt.open_osfhandle(kernel.GetStdHandle(-10),os.O_RDONLY|os.O_BINARY),'r',encoding='utf-8',closefd=False)
        if sys.stdout is None:sys.stdout=open(msvcrt.open_osfhandle(kernel.GetStdHandle(-11),os.O_WRONLY|os.O_BINARY),'w',encoding='utf-8',closefd=False)
    try:
        data=sys.stdin.readline(1024*1024+1)
        if len(data)>1024*1024:raise ValueError('Catalogue input exceeds 1 MiB')
        result=run(json.loads(data)); response={'result':result}
    except Exception as exc:
        response={'error':str(exc) if isinstance(exc,(ValueError,RuntimeError)) else 'Catalogue operation failed'}
    sys.stdout.write(json.dumps(response,ensure_ascii=False)+'\n');sys.stdout.flush()
