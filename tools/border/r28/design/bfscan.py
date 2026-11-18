"""Vectorised search of the tilted-block plus upright-rows model (blockfill.py) for n = m*m + k.
For each angle, block a x b, right columns p and box side S = m + f, the best block centre (cx on a 0.0025 grid,
cy on a 0.005 grid) and the best bottom/top row split give the largest count. Prints, per (m, k), the smallest f on
the grid whose count reaches m*m + k, with the configuration.
usage: bfscan.py OUT.jsonl M1 M2 KMAX ANGLES(deg,comma) FMIN FMAX FSTEP [AMIN]"""
import sys, math, json, time, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from blockfill import corners, slab_x
EPS=1e-9
out=sys.argv[1]; M1,M2,KMAX=int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4])
ANG=[float(x) for x in sys.argv[5].split(',')]
FMIN,FMAX,FSTEP=float(sys.argv[6]),float(sys.argv[7]),float(sys.argv[8])
AMIN=int(sys.argv[9]) if len(sys.argv)>9 else 6
def best_count(S,a,b,t,p):
    W=S-p;H=S;R=int(math.floor(H+EPS));full=int(math.floor(W+EPS))
    c,s=math.cos(t),math.sin(t)
    hw=(a*abs(c)+b*abs(s))/2;hh=(a*abs(s)+b*abs(c))/2
    if 2*hw>W+EPS or 2*hh>H+EPS:return -1,None
    cxs=np.arange(max(hw,W/2-1.0),min(W-hw,W/2+1.0)+1e-12,0.0025)  # window of +-1 around the centre
    if len(cxs)==0:cxs=np.array([W/2])
    best=(-1,None)
    for cy in np.arange(max(hh,H/2-1.0),min(H-hh,H/2+1.0)+1e-12,0.005):
        poly=corners(0.0,cy,a,b,t)
        bot=np.empty((R,len(cxs)));top=np.empty((R,len(cxs)))
        for j in range(R):
            for arr,y0 in ((bot,j),(top,H-1-j)):
                r=slab_x(poly,y0,y0+1)
                if r is None:arr[j]=full
                else:arr[j]=np.floor(cxs+r[0]+EPS)+np.floor(W-cxs-r[1]+EPS)
        cb=np.vstack([np.zeros(len(cxs)),np.cumsum(bot,0)]);ct=np.vstack([np.zeros(len(cxs)),np.cumsum(top,0)])
        tot=cb+ct[::-1]   # J bottom rows + (R-J) top rows
        J,i=np.unravel_index(np.argmax(tot),tot.shape)
        v=int(tot[J,i])+a*b+p*R
        if v>best[0]:best=(v,dict(cx=float(cxs[i]),cy=float(cy),J=int(J)))
    return best
t0=time.time()
with open(out,'a') as fo:
  for m in range(M1,M2+1):
    for deg in ANG:
        t=math.radians(deg)
        for a in range(AMIN,m+1):
            for b in range(a if abs(deg-45)<1e-9 else AMIN,m+1):
                for p in (0,1):
                    # smallest f on the grid reaching m*m+k for each k
                    found={}
                    for f in np.arange(FMIN,FMAX+1e-12,FSTEP):
                        S=m+f;v,cfg=best_count(S,a,b,t,p)
                        if v<0:continue
                        for k in range(1,KMAX+1):
                            if k not in found and v>=m*m+k:found[k]=(round(float(f),5),v,cfg)
                        if len(found)==KMAX:break
                    for k,(f,v,cfg) in found.items():
                        fo.write(json.dumps(dict(m=m,k=k,f=f,count=v,deg=deg,a=a,b=b,p=p,**cfg))+'\n')
                    fo.flush()
        print(m,deg,'done',round(time.time()-t0),flush=True)
