"""Recheck final source rows with the lane's exact publication verifier."""
import csv,json,time,math,hashlib
from provenance24 import W,mlp,credit
import floatsafe
T=W.parent;out=[]
cache={r['n']:r for r in json.load(open(W/'validation25.json'))} if (W/'validation25.json').exists() else {}
for row in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
 n=int(row['n']);p=T/f'{n}.csv';sha=hashlib.sha256(p.read_bytes()).hexdigest()
 if n in cache and cache[n].get('csv_sha256')==sha:
  assert credit(n,mlp.load(str(p),{n})[n],str(p)),(n,'source proof failed')
  out.append(cache[n]);continue
 raw=list(csv.DictReader(open(p)));_,fixed,score,error=floatsafe.work((n,raw))
 assert fixed is not None,(n,error)
 assert abs(score-float(row['new']))<1e-13,(n,score,row['new'])
 # The retained file itself must already have the safe coordinates.
 for a,b in zip(raw,fixed):
  assert all(float(a[k])==float(b[k]) for k in ['x','y','angle']),(n,'verifier changed coordinates')
 assert credit(n,mlp.load(str(p),{n})[n],str(p)),(n,'source proof failed')
 out.append({'n':n,'score':score,'source_clean':True,'floatsafe':True,'rows':len(raw),'csv_sha256':sha})
(W/'validation25.json').write_text(json.dumps(out,indent=2));print(json.dumps(out),flush=True)
