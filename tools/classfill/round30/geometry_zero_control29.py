from common29 import *
import light29 as M
from collections import defaultdict
# Pure coordinate hashing, never a numerical search.
def key(P,decimals=8):
 variants=[]
 def rr(v):
  r=round(v,decimals);return 0.0 if r==0 else r
 for reflect in [False,True]:
  for rot in range(4):
   Q=[]
   for x,y,a in P:
    if reflect:x=-x;a=-a
    for _ in range(rot):x,y=-y,x;a+=math.pi/2
    a=(a+math.pi/4)%(math.pi/2)-math.pi/4;Q.append((x,y,a))
   hx=[.5*(abs(math.cos(a))+abs(math.sin(a))) for x,y,a in Q];dx=min(p[0]-h for p,h in zip(Q,hx));dy=min(p[1]-h for p,h in zip(Q,hx))
   out=sorted((rr(x-dx),rr(y-dy),rr(a)) for x,y,a in Q);variants.append(hashlib.sha256(json.dumps(out,separators=(',',':')).encode()).hexdigest())
 return 'zero-v1:'+min(variants)
if __name__=='__main__':
 P=[(.5,.5,0.),(1.5,.5,0.)];base=key(P);assert key([(.5,.5,-1e-16),(1.5,.5,0.)])==base
 assert key([(.5,.5,.1),(1.5,.5,0.)])!=base
 print('SIGNED_ZERO_CONTROL_PASS same geometry accepted, changed angle distinguished',flush=True)
 began=time.time();groups=defaultdict(list);old=set()
 for p in sorted((W/'inputs').glob('*.csv')):
  if time.time()>min(END,began+120):break
  n=int(p.name.split('-')[0]);Q=M.load(str(p),{n})[n];a=M.key(Q);b=key(Q);old.add(a);groups[b].append(dict(path=str(p),n=n,old=a))
 collapsed=[g for g in groups.values() if len({q['old'] for q in g})>1]
 result=dict(time=now(),inputs=sum(map(len,groups.values())),legacy_unique=len(old),normalized_unique=len(groups),collapsed_groups=collapsed)
 atomic(W/'geometry-zero-measurement.json',result);print(json.dumps(result,indent=1))
