"""Light coordinate reads for queue ordering. Search and certification stay on workers."""
import csv,math,hashlib,json
from collections import defaultdict

def load(path,want=None):
 out=defaultdict(list)
 for r in csv.DictReader(open(path)):
  n=int(r['n'])
  if want is None or n in want:out[n].append((int(r['square_id']),float(r['x']),float(r['y']),float(r['angle'])))
 return {n:[(x,y,a) for _,x,y,a in sorted(v)] for n,v in out.items()}
def side(P):
 h=[.5*(abs(math.cos(a))+abs(math.sin(a))) for x,y,a in P]
 return max(max(p[0]+hh for p,hh in zip(P,h))-min(p[0]-hh for p,hh in zip(P,h)),max(p[1]+hh for p,hh in zip(P,h))-min(p[1]-hh for p,hh in zip(P,h)))
def key(P,decimals=8):
 variants=[]
 for reflect in [False,True]:
  for rot in range(4):
   Q=[]
   for x,y,a in P:
    if reflect:x=-x;a=-a
    for _ in range(rot):x,y=-y,x;a+=math.pi/2
    a=(a+math.pi/4)%(math.pi/2)-math.pi/4;Q.append((x,y,a))
   hx=[.5*(abs(math.cos(a))+abs(math.sin(a))) for x,y,a in Q];dx=min(p[0]-h for p,h in zip(Q,hx));dy=min(p[1]-h for p,h in zip(Q,hx))
   out=sorted((round(x-dx,decimals),round(y-dy,decimals),round(a,decimals)) for x,y,a in Q)
   variants.append(hashlib.sha256(json.dumps(out,separators=(',',':')).encode()).hexdigest())
 return min(variants)
