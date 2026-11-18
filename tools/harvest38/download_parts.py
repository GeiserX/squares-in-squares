"""Resume immutable notebook output files across interrupted fetch passes."""
import hashlib
import json
import os
from pathlib import Path
from common import W
ROOT=W/'download-parts'


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):digest.update(block)
    return digest.hexdigest()


def fetch(url,path,ref,signature,download):
    path=Path(path)
    identity=hashlib.sha256(json.dumps([ref,signature,path.name]).encode()).hexdigest()
    folder=ROOT/identity[:2];folder.mkdir(parents=True,exist_ok=True)
    payload=folder/(identity+'.blob');receipt=folder/(identity+'.json')
    if receipt.exists():
        data=json.loads(receipt.read_text())
        if (data['ref']!=ref or data['signature']!=signature or data['name']!=path.name
                or not payload.is_file() or sha(payload)!=data['sha256']):
            raise ValueError('completed download checkpoint bytes changed')
        os.link(payload,path)
        return True
    download(url,path)
    digest=sha(path)
    if payload.exists():
        if sha(payload)!=digest:raise ValueError('unfinished download checkpoint differs from fetched bytes')
    else:os.link(path,payload)
    data=dict(ref=ref,signature=signature,name=path.name,sha256=digest,size=path.stat().st_size)
    temporary=receipt.with_suffix('.json.tmp');temporary.write_text(json.dumps(data)+'\n');temporary.replace(receipt)
    return False


def control():
    import tempfile
    from unittest.mock import patch
    with tempfile.TemporaryDirectory(dir=W) as name:
        root=Path(name);calls=[]
        def download(url,path):calls.append(url);Path(path).write_bytes(b'complete packing bytes')
        with patch.dict(globals(),ROOT=root/'parts'):
            for sub in ['first','second','changed','tampered']:(root/sub).mkdir()
            assert not fetch('https://data.invalid/one',root/'first/submission.csv','example/source','v1',download)
            assert fetch('https://data.invalid/new-signed-url',root/'second/submission.csv','example/source','v1',download)
            assert len(calls)==1 and (root/'first/submission.csv').read_bytes()==(root/'second/submission.csv').read_bytes()
            assert not fetch('https://data.invalid/two',root/'changed/submission.csv','example/source','v2',download)
            assert len(calls)==2
            (root/'first/submission.csv').write_bytes(b'changed cache bytes')
            try:fetch('https://data.invalid/one',root/'tampered/submission.csv','example/source','v1',download)
            except ValueError:pass
            else:raise AssertionError('changed completed bytes were reused')
            assert len(calls)==2
    print('CONTROL completed download reused across a changed signed URL; changed version downloads; tampered completed bytes refused',flush=True)

if __name__=='__main__':control()
