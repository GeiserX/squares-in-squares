"""Compare owned endpoints with square angles modulo90 degrees."""
import hashlib,json,math
def key(P,decimals=6):
 variants=[];period=math.pi/2
 for reflect in [False,True]:
  for rot in range(4):
   Q=[]
   for x,y,a in P:
    if reflect:x=-x;a=-a
    for _ in range(rot):x,y=-y,x;a+=period
    a=a%period;aa=round(a,decimals)
    if aa==round(period,decimals) or aa==0:aa=0.0
    Q.append((x,y,a,aa))
   h=[.5*(abs(math.cos(a))+abs(math.sin(a))) for x,y,a,aa in Q]
   dx=min(p[0]-hh for p,hh in zip(Q,h));dy=min(p[1]-hh for p,hh in zip(Q,h))
   rows=sorted((round(x-dx,decimals),round(y-dy,decimals),aa)for x,y,a,aa in Q)
   variants.append(hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest())
 return min(variants)
