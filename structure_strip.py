"""structure lane: sheared diagonal strip. Rows of `a` unit squares (row axis v, squares at angle phi=45-eps deg), stacked along the exact
45-degree diagonal with step sec(eps); clipped to the container; uprights by exact fill (Evan Daniel's fillfast, MIT, imported)."""
import sys, math, time, json
import numpy as np
from structure_slot import count
S2=math.sqrt(2)
def strip_rows(L, a, eps_deg, perp=0.0, phase=0.0, anti=False, kmin=None, kmax=None, gap=None):
    eps=math.radians(eps_deg); phi=math.pi/4-eps
    u=np.array([math.cos(phi),math.sin(phi)]); v=np.array([-math.sin(phi),math.cos(phi)])
    d=np.array([1,1])/S2; nrm=np.array([-1,1])/S2
    step=d/math.cos(eps)
    out=[]
    K=int(L*S2*math.cos(eps))+6
    for k in range(-3,K):
        if kmin is not None and k<kmin: continue
        if kmax is not None and k>kmax: continue
        if gap is not None and gap[0]<=k<=gap[1]: continue
        base=(phase+k)*step+perp*nrm
        for j in range(a):
            c=base+(j-(a-1)/2)*v
            h=(abs(u[0])+abs(u[1]))/2
            if c[0]-h<-1e-12 or c[0]+h>L+1e-12 or c[1]-h<-1e-12 or c[1]+h>L+1e-12: continue
            if anti: out.append((L-c[0],c[1],-math.degrees(phi)))
            else: out.append((c[0],c[1],math.degrees(phi)))
    return out
def best_count(L,a,eps,perps,phases):
    best=(-1,)
    for p in perps:
        for ph in phases:
            T=strip_rows(L,a,eps,p,ph)
            n=count(L,T)
            if n>best[0]: best=(n,p,ph,len(T))
    return best
if __name__=='__main__':
    m=int(sys.argv[1]); f=float(sys.argv[2]); a=int(sys.argv[3]); epss=[float(x) for x in sys.argv[4].split(',')]
    L=m+f
    for eps in epss:
        t=time.time()
        b=best_count(L,a,eps,[0.0,0.1,0.2,0.3,0.4],[0.0,0.25,0.5,0.75])
        A=math.ceil(S2*a*math.cos(math.radians(eps))-2*f)
        print(json.dumps({'m':m,'f':f,'a':a,'eps':eps,'gain':b[0]-m*m,'perp':b[1],'phase':b[2],'tilted':b[3],'rate_pred':round(S2*a*math.cos(math.radians(eps))-(A+1),3),'secs':round(time.time()-t)}),flush=True)
