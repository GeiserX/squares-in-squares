"""Cache only geometry measurements, keyed by every pose and reference byte."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import W,S
sys.modules.setdefault('geometry_cache',sys.modules[__name__])
_CACHE=None
_DIRTY=False
_REVISION=hashlib.sha256(Path(__file__).read_bytes()+Path(__file__).with_name('policy.py').read_bytes()+(S/'take-assemble-r31/scripts/share31.py').read_bytes()).digest()
PATH=W/'geometry-share-cache.json'


def key(n,centres,targets):
    digest=hashlib.sha256(_REVISION+str(n).encode()+b'\0'+centres.tobytes())
    for label,target in targets:
        digest.update(label.encode()+b'\0'+str(target.shape).encode()+b'\0'+target.tobytes())
    return digest.hexdigest()


def lookup(identity):
    global _CACHE
    if _CACHE is None:
        _CACHE=json.loads(PATH.read_text()) if PATH.exists() else {}
    return _CACHE.get(identity)


def put(identity,result):
    global _DIRTY
    _CACHE[identity]=result;_DIRTY=True


def flush():
    global _DIRTY,_CACHE
    if not _DIRTY:return
    if len(_CACHE)>10000:_CACHE=dict(list(_CACHE.items())[-10000:])
    temp=PATH.with_suffix('.json.tmp');temp.write_text(json.dumps(_CACHE,separators=(',',':'))+'\n');temp.replace(PATH)
    _DIRTY=False


def control():
    import csv,time
    from unittest.mock import patch
    import policy
    path=S/'take-harvest-r31/work/direct-source-held/851-public31-985c28a4e8027701.csv'
    if not path.exists():path=S/'take-harvest-r31/near/851-public31-985c28a4e8027701.csv'
    rows=list(csv.DictReader(path.open()))
    policy.excluded(851)
    with patch.dict(globals(),_CACHE={},_DIRTY=False):
        with patch.object(policy,'share',wraps=policy.share) as measured:
            start=time.monotonic();first=policy.audit(rows);cold=time.monotonic()-start
            assert not first[0] and abs(max(r['share1e2'] for r in first[1])-.46415981198589895)<1e-12
            calls=measured.call_count;assert calls>0
            start=time.monotonic();second=policy.audit(rows);warm=time.monotonic()-start
            assert first==second and measured.call_count==calls
            changed=[dict(r) for r in rows];changed[0]['x']=str(float(changed[0]['x'])+.001)
            policy.audit(changed);assert measured.call_count>calls;calls=measured.call_count
            targets=policy.excluded(851);label,target=targets[0];target=target.copy();target[0,0]+=.001
            with patch.object(policy,'excluded',return_value=[(label,target)]+targets[1:]):policy.audit(rows)
            assert measured.call_count>calls
    print(f'CONTROL exact public851 refusal preserved at0.464159811986; second audit uses zero share calls; changed input/reference bytes recompute; cold={cold:.6f}s warm={warm:.6f}s',flush=True)

if __name__=='__main__':control()
