"""Expand the pinned SDK source snapshot; never use another product's build directory."""
from pathlib import Path
import hashlib, json, tarfile
ROOT = Path(__file__).resolve().parents[1]
def prepare():
    lock = json.loads((ROOT / 'tools/cymcpsdk.lock.json').read_text(encoding='utf-8'))
    archive = ROOT / lock['archive']
    if hashlib.sha256(archive.read_bytes()).hexdigest() != lock['sha256']:
        raise ValueError('CyMCPSDK source checksum mismatch')
    target = ROOT / 'third_party/cymcpsdk'
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as package:
        for member in package.getmembers():
            path = target / member.name
            if not member.isfile() or not path.resolve().is_relative_to(target.resolve()):
                raise ValueError('Invalid SDK archive member')
            data = package.extractfile(member).read()
            if not path.is_file() or path.read_bytes() != data:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
    return target
if __name__ == '__main__':
    print(prepare())
