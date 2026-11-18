"""structure lane: sheared 45-degree block. `a` chains of `b` unit squares; each chain runs along the exact diagonal with step
sec(eps) and the squares are turned by eps off 45 degrees, so the block keeps 45-degree outlines but its two extents become
a*cos(eps) (across) and about b*sec(eps) (along). eps = 0 is the rigid block of structure_rigid45.py. Uprights by exact fill.

  structure_shear.py M F A B EPS[,EPS...]      # best gain over a small scan of the block position
"""
import sys, os, math, json, time
import numpy as np
from structure_slot import count
S2=math.sqrt(2)
def block(a,b,eps_deg,cx,cy,anti=False):
    eps=math.radians(eps_deg); phi=math.pi/4-eps
    u=np.array([math.cos(phi),math.sin(phi)]); v=np.array([-math.sin(phi),math.cos(phi)])
    d=np.array([1,1])/S2; step=d/math.cos(eps)
    out=[]
    for k in range(b):
        for j in range(a):
            c=np.array([cx,cy])+(k-(b-1)/2)*step+(j-(a-1)/2)*v
            out.append((float(c[0]),float(c[1]),math.degrees(phi)) if not anti else (float(c[0]),float(2*cy-c[1]),-math.degrees(phi)))
    return out
def inside(T,L):
    for x,y,dg in T:
        h=(abs(math.cos(math.radians(dg)))+abs(math.sin(math.radians(dg))))/2
        if x-h<-1e-9 or y-h<-1e-9 or x+h>L+1e-9 or y+h>L+1e-9: return False
    return True
def best_gain(m,f,a,b,eps,offs=(0.0,-0.03,-0.06,-0.09,0.03),anti=False):
    """block centre from the rigid phase rule (lower-left edge on an integer line, upper-left edge on an f line), then small offsets"""
    L=m+f; e=math.radians(eps)
    En=a*math.cos(e)+math.sin(e); Ed=(b-1)/math.cos(e)+math.cos(e)+math.sin(e)   # envelope extents across / along
    best=None
    i0=int(round(L-Ed/S2)); j0=int(round(En/S2-f))
    for di,dj in ((0,0),(1,0),(-1,0),(0,1),(0,-1)):
        for o1 in offs:
            for o2 in offs:
                i=i0+di
                # lower-left edge: x+y = cx+cy - Ed/sqrt2 = i + o1 ; upper-left edge: y-x = cy-cx + En/sqrt2 = f + o2 + integer
                s=i+o1+Ed/S2; t=f+o2+j0+dj-En/S2
                cx=(s-t)/2; cy=(s+t)/2
                T=block(a,b,eps,cx,cy,anti)
                if not inside(T,L): continue
                n=count(L,T)
                if best is None or n>best[0]: best=(n,cx,cy,o1,o2)
    return best
if __name__=='__main__':
    m=int(sys.argv[1]); f=float(sys.argv[2]); a=int(sys.argv[3]); b=int(sys.argv[4])
    for eps in [float(x) for x in sys.argv[5].split(',')]:
        t=time.time(); r=best_gain(m,f,a,b,eps)
        print(json.dumps({'m':m,'f':f,'a':a,'b':b,'eps':eps,'gain':None if r is None else r[0]-m*m,'pos':None if r is None else [round(x,4) for x in r[1:]],'secs':round(time.time()-t,1)}),flush=True)
