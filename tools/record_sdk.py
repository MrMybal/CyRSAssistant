"""Record the SDK executable and its pinned source provenance (no build paths)."""
from pathlib import Path
import hashlib, json, re, sys
root=Path(__file__).resolve().parents[1]
exe=Path(sys.argv[1])
lock=json.loads((root/'tools/cymcpsdk.lock.json').read_text(encoding='utf-8'))
version=re.search(r'project\(CyRSAssistant VERSION ([0-9.]+)',(root/'CMakeLists.txt').read_text()).group(1)
assert hashlib.sha256((root/lock['archive']).read_bytes()).hexdigest()==lock['sha256']
exe.with_suffix('.build.json').write_text(json.dumps({'application_version':version,'sdk':lock,'sha256':hashlib.sha256(exe.read_bytes()).hexdigest()},indent=2)+'\n',encoding='utf-8')
