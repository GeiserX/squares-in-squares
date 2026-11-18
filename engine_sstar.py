#!/usr/bin/env python3
"""engine E1b: same group moves as engine_patch, but the objective is s*(T), the smallest side at which the exact
upright refill reaches n (patches stay anchored to their nearest corner while the side changes). A graded objective
instead of a flat count.

  engine_sstar.py N [--secs 300] [--seed 0] [--tilt 0.5]
"""
import argparse, math, random, json, time
from engine_lib import *
from engine_patch import corners, pen_matrix, cluster, rigid, feasible
import fillfast

def place(T,groups,far,s0,s):
    T2=T.copy()
    for g,f in zip(groups,far):
        for k in (0,1):
            if f[k]: T2[g,k]-=(s0-s)
    return T2

def sstar(T,groups,far,s0,n,lo,hi,tol=2e-7):
    """bisect the smallest s in [lo,hi] with fill count >= n; inf-like value if hi fails"""
    def ok(s):
        T2=place(T,groups,far,s0,s)
        if not feasible(T2,s,groups): return False,-1
        c=len(fillfast.fill(s,T2,'greedy')); return c>=n,c
    o,c=ok(hi)
    if not o: return hi+0.05*(n-c if c>=0 else 50)
    o,c=ok(lo)
    if o: return lo
    while hi-lo>tol:
        mid=(lo+hi)/2
        if ok(mid)[0]: hi=mid
        else: lo=mid
    return hi

def run(n,secs,seed,tilt,P):
    rng=random.Random(seed)
    s0,A=normalize(P[n]); T=A[np.abs(A[:,2])>tilt]; groups=cluster(T)
    far=[tuple(T[g,k].mean()>s0/2 for k in (0,1)) for g in groups]
    f=lambda T_: sstar(T_,groups,far,s0,n,s0-0.05,s0+0.01)
    cur=f(T); print(json.dumps(dict(n=n,s0=s0,ntilt=len(T),patches=[len(g) for g in groups],sstar0=cur)),flush=True)
    best=cur; t0=time.time(); it=0; imp=0
    big=[g for g in groups if len(g)>=4] or groups
    while time.time()-t0<secs:
        it+=1; r=rng.random(); g=big[rng.randrange(len(big))]
        if r<0.35:
            sc=10**rng.uniform(-5,-1); T2=rigid(T,g,rng.gauss(0,sc),rng.gauss(0,sc),0.0)
        elif r<0.6:
            T2=rigid(T,g,0,0,rng.gauss(0,10**rng.uniform(-4,-0.5)))
        elif r<0.75:
            sc=10**rng.uniform(-5,-1); T2=rigid(T,g,rng.gauss(0,sc),rng.gauss(0,sc),rng.gauss(0,10**rng.uniform(-4,-0.5)))
        else:
            i=g[rng.randrange(len(g))]; th=math.radians(T[i,2])
            if rng.random()<0.5: th+=math.pi/2
            u=np.array([math.cos(th),math.sin(th)]); nrm=np.array([-u[1],u[0]])
            row=[j for j in g if abs((T[j,:2]-T[i,:2])@nrm)<0.3]
            d=rng.gauss(0,10**rng.uniform(-5,-1)); T2=T.copy(); T2[row,0]+=d*u[0]; T2[row,1]+=d*u[1]
        c2=f(T2)
        if c2<cur-1e-9:
            imp+=1; T,cur=T2,c2; best=cur
            print('it %d t %.0fs s* %.7f (d %.2e)'%(it,time.time()-t0,cur,cur-s0),flush=True)
    print(json.dumps(dict(n=n,s0=s0,best=best,gain=s0-best,iters=it,improvements=imp,secs=round(time.time()-t0,1))),flush=True)
    return T,best

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('n',type=int); ap.add_argument('--secs',type=float,default=300); ap.add_argument('--seed',type=int,default=0); ap.add_argument('--tilt',type=float,default=0.5)
    a=ap.parse_args(); run(a.n,a.secs,a.seed,a.tilt,load())
