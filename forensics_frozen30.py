"""Retain each frozen source graph once instead of expanding repeated parents."""
from pathlib import Path
import hashlib,json,os,re
from functools import lru_cache

CACHE={}


def atomic(path,payload):
    temporary=path.with_name(path.name+'.'+str(os.getpid())+'.tmp');temporary.write_bytes(payload);temporary.replace(path)


def eligible(path):
    return any(re.fullmatch(r'take-[a-z0-9-]+-r(?:[1-9]|1\d|2\d)',part) for part in path.parts)


def trace(path,n,scratch,active,original,compact,work,policy):
    path=Path(path)
    if not path.is_absolute() and str(path).startswith(('take-','gather/')):path=Path(scratch)/path
    if not eligible(path) or not path.is_file():return original(path,n,scratch,active)
    active=set(active or ())
    if (str(path),n) in active:return False,dict(path=str(path),n=n,reason='frozen source cycle')
    from forensics_public30 import file_sha
    st=path.stat();packing=file_sha(str(path),st.st_size,st.st_mtime_ns);token=(str(path),n,packing,policy)
    if token in CACHE:return True,CACHE[token]
    key=hashlib.sha256(json.dumps(token).encode()).hexdigest();directory=Path(work)/'frozen-graphs30';directory.mkdir(exist_ok=True);index=directory/(key+'.index.json')
    if index.exists():
        try:
            saved=json.loads(index.read_text())
            if saved.get('path')==str(path) and saved.get('n')==n and saved.get('snapshot_sha256')==packing and saved.get('policy_sha256')==policy and Path(saved['source_proof']).is_file():
                CACHE[token]=saved;return True,saved
        except (OSError,ValueError,KeyError):pass
    ok,proof=original(path,n,scratch,active)
    if not ok:return ok,proof
    blob=json.dumps(dict(path=str(path),n=n,packing_sha256=packing,evidence=proof),sort_keys=True,separators=(',',':')).encode();digest=hashlib.sha256(blob).hexdigest();target=directory/(digest+'.json')
    if not target.exists():atomic(target,blob)
    value=dict(path=str(path),n=n,reason='verified immutable donor group',source_proof=str(target),sha256=digest,snapshot_sha256=packing,policy_sha256=policy,origins=compact(proof,str(target)))
    atomic(index,json.dumps(value,sort_keys=True).encode());CACHE[token]=value
    return True,value
