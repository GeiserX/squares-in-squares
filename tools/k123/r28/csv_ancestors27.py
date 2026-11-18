"""Measure complete per-n CSV ancestors of the retained take, skipping module fragments."""
import pathlib,sys,csv,json,re,time,hashlib
sys.dont_write_bytecode=True
W=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(W),'.',str(W/'lane')]
import quench_walk,policy27,numpy as np
rows=list(csv.DictReader(open(W.parent/'take.tsv'),delimiter='\t'));cache={};out=[]
for r in rows:
 n=int(r['n']);texts,missing,seen,helds,refused=quench_walk.walk(str(W.parent/f'{n}.csv'),n);checks=[]
 for name in sorted(seen):
  p=pathlib.Path(name)
  if not p.is_file() or p.suffix!='.csv':continue
  if '/lib' in str(p) or '/parts/' in str(p) or '/cuts/' in str(p):continue
  if name not in cache:
   try:
    rr=[];nn=None;multiple=False
    for row in csv.DictReader(open(p)):
     if 'n' not in row or not all(k in row for k in ['x','y','angle']):multiple=True;break
     k=int(row['n'])
     if nn is None:nn=k
     elif nn!=k:multiple=True;break
     rr.append(row)
    if multiple or nn is None or len(rr)!=nn:cache[name]=None;continue
    A=np.array([[float(row[k]) for k in ['x','y','angle']] for row in rr]);share=policy27.share(nn,A)
    cache[name]={'n':nn,'path':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'share':share,'excluded':share>=.4}
   except (ValueError,KeyError,OSError):cache[name]=None;continue
  if cache[name]:checks.append(cache[name])
 out.append({'n':n,'checked':len(checks),'excluded':[x for x in checks if x['excluded']],'checks':checks})
(W/'csv-ancestor-checks27.json').write_text(json.dumps({'time':time.strftime('%FT%TZ',time.gmtime()),'rows':out},indent=2))
print(json.dumps([{'n':x['n'],'checked':x['checked'],'excluded':x['excluded']} for x in out]),flush=True)
