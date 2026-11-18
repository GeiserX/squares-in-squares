"""Resolve the measured n805 historical pin from its exact archived copy."""
import hashlib
import json
from pathlib import Path
import re
from common import S,W
from policy import snapshot

OLD=str(S/'take-forensics-r28/near/805-rect.csv')
HASH='3905b3f6064dcafa0db6bda9c7d3c8a76d5d1ccf7ee24a47ddaf8d86a0f50686'
ARCHIVE=S/'take-stair-c-r28/work/donors/r28-805-3905b3f6064d.csv'
EXTRA_PINS={}


def resolve():
    import walk as Q
    if hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()!=HASH:
        raise ValueError('historical805 archive bytes differ from requested pin')
    for name,line in Q.WITHDRAWN_LINES:
        if Q.Q.norm(name)!=OLD or Q.samanyu_only(line):continue
        hashes=re.findall(r'sha256[ =:]+([0-9a-f]{8,64})',line,re.I)
        if not hashes or any(HASH.startswith(h) for h in hashes):
            raise ValueError('historical805 bytes have a hard withdrawal: '+line[:200])
    dst,sha=snapshot(ARCHIVE,W/'ancestry-inputs')
    sidecar=Path(str(ARCHIVE)+'.json');target=Path(str(dst)+'.json')
    raw=sidecar.read_bytes()
    if target.exists() and target.read_bytes()!=raw:
        raise ValueError('historical805 source sidecar changed')
    if not target.exists():target.write_bytes(raw)
    EXTRA_PINS[OLD]=dict(original=OLD,snapshot=str(dst),sha256=sha)
    return str(dst)


def transform(value,bound=False):
    if isinstance(value,dict):
        bound=bound or (value.get('path')==OLD and value.get('snapshot_sha256')==HASH) or (value.get('original')==OLD and value.get('sha256')==HASH)
        return {k:transform(v,bound) for k,v in value.items()}
    if isinstance(value,list):return [transform(v,bound) for v in value]
    if isinstance(value,str) and OLD in value:
        pinned=re.search(re.escape(OLD)+r'\s*\(sha256 '+HASH[:16],value)
        if bound or pinned:
            return value.replace(OLD,resolve())
    return value
