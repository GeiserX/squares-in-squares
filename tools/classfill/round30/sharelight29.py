import math

def share(a,b):
 ax=(min(x for x,y in a)+max(x for x,y in a))/2;ay=(min(y for x,y in a)+max(y for x,y in a))/2
 bx=(min(x for x,y in b)+max(x for x,y in b))/2;by=(min(y for x,y in b)+max(y for x,y in b))/2
 a=[(x-ax,y-ay) for x,y in a];b=[(x-bx,y-by) for x,y in b];bins={}
 for x,y in b:bins.setdefault((math.floor(x*1000),math.floor(y*1000)),[]).append((x,y))
 best=0
 for swap in [False,True]:
  for sx in [1,-1]:
   for sy in [1,-1]:
    count=0
    for x,y in a:
     if swap:x,y=y,x
     x*=sx;y*=sy;ix=math.floor(x*1000);iy=math.floor(y*1000)
     if any((x-u)**2+(y-v)**2<1e-6 for dx in [-1,0,1] for dy in [-1,0,1] for u,v in bins.get((ix+dx,iy+dy),[])):count+=1
    best=max(best,count/len(a))
 return best
