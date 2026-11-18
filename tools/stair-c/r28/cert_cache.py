"""Reuse numerical certificates only for the same count and exact CSV bytes."""
import csv,hashlib,io
import floatsafe
CACHE={}
def certify(path,n):
    payload=open(path,'rb').read();key=(n,hashlib.sha256(payload).hexdigest())
    if key in CACHE:return CACHE[key]
    rows=list(csv.DictReader(io.StringIO(payload.decode())))
    if len(rows)!=n or any(int(r['n'])!=n for r in rows):result=(n,None,None,'count mismatch')
    else:result=floatsafe.work((n,rows))
    if len(CACHE)>=32:CACHE.pop(next(iter(CACHE)))
    CACHE[key]=result;return result
