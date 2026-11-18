"""Reuse numerical certificates only for the same count and exact CSV bytes."""
import csv,hashlib,io,os,pickle
from pathlib import Path
import fine as floatsafe
CACHE={}
CODE=Path('.')
NAMESPACE=hashlib.sha256(b'finesafe-2.2e-11-r30-v1'+b''.join(p.read_bytes()for p in[Path(__file__),CODE/'tools/border/r28/finesafe.py',CODE/'floatsafe.py',CODE/'kaggle_metric.py'])).hexdigest()
DISK=Path('$SCRATCH/bounties-squares/take-stair-c-r31/work/certificates')/NAMESPACE
DISK.mkdir(parents=True,exist_ok=True)
COUNTS=dict(memory=0,disk=0,computed=0)
def certify(path,n):
    payload=open(path,'rb').read();key=(n,hashlib.sha256(payload).hexdigest())
    if key in CACHE:COUNTS['memory']+=1;return CACHE[key]
    saved=DISK/(str(n)+'-'+key[1]+'.pkl')
    if saved.exists():
        with saved.open('rb')as h:result=pickle.load(h)
        COUNTS['disk']+=1
        if len(CACHE)>=512:CACHE.pop(next(iter(CACHE)))
        CACHE[key]=result;return result
    rows=list(csv.DictReader(io.StringIO(payload.decode())))
    if len(rows)!=n or any(int(r['n'])!=n for r in rows):result=(n,None,None,'count mismatch')
    else:result=floatsafe.work((n,rows))
    COUNTS['computed']+=1
    temp=Path(str(saved)+'.'+str(os.getpid())+'.tmp')
    with temp.open('wb')as h:pickle.dump(result,h)
    temp.replace(saved)
    if len(CACHE)>=512:CACHE.pop(next(iter(CACHE)))
    CACHE[key]=result;return result
