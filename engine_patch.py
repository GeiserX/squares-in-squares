#!/usr/bin/env python3
"""engine E1: rigid patch moves + exact upright refill at a reduced side.

A layout = tilted squares T (grouped into rigid patches) + uprights U. U is never searched: Evan Daniel's
fillfast (MIT, imported from his clone, not copied) recomputes the best upright set for any T. The search
moves whole patches (translate, rotate about the centroid), slips single patch rows, or drops/re-adds one
tilted square, at a fixed side below ours, and maximises the fill count.

  engine_patch.py N [--delta 0.002 | --side S] [--secs 120] [--seed 0] [--tilt 5]
"""
import argparse, math, random, sys, time, json
from engine_lib import *
import fillfast

def corners(A):
    th=np.radians(A[:,2]); c,s=np.cos(th),np.sin(th)
    off=np.array([[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5]])
    return A[:,None,:2]+np.stack([off[:,0]*c[:,None]-off[:,1]*s[:,None], off[:,0]*s[:,None]+off[:,1]*c[:,None]],-1)

def pen_matrix(A,B):
    """SAT penetration depth (>0 = overlap) for every pair A[i], B[j]"""
    PA=corners(A); PB=corners(B)
    best=np.full((len(A),len(B)),np.inf)
    for S,(X,Y) in ((A,(PA,PB)),(B,(PA,PB))):
        th=np.radians(S[:,2])
        for ax in (np.c_[np.cos(th),np.sin(th)], np.c_[-np.sin(th),np.cos(th)]):
            if S is A:
                pa=np.einsum('ikd,id->ik',PA,ax)            # (a,4)
                pb=np.einsum('jkd,id->ijk',PB,ax)           # (a,b,4)
                d=np.minimum(pa.max(1)[:,None]-pb.min(2), pb.max(2)-pa.min(1)[:,None])
            else:
                pa=np.einsum('ikd,jd->ijk',PA,ax)
                pb=np.einsum('jkd,jd->jk',PB,ax)
                d=np.minimum(pa.max(2)-pb.min(1)[None,:], pb.max(1)[None,:]-pa.min(2))
            best=np.minimum(best,d)
    return best

def feasible(T,s,groups,tol=1e-9):
    P=corners(T)
    if P.min()< -tol or P.max()>s+tol: return False
    # only pairs within distance sqrt2 can overlap
    d=T[:,None,:2]-T[None,:,:2]
    near=(d**2).sum(-1)<2.0
    np.fill_diagonal(near,False)
    I,J=np.nonzero(np.triu(near))
    if len(I)==0: return True
    for i,j in zip(I,J):
        if pen_matrix(T[i:i+1],T[j:j+1])[0,0]>tol: return False
    return True

def cluster(T,r=1.75):
    n=len(T); par=list(range(n))
    def f(a):
        while par[a]!=a: par[a]=par[par[a]]; a=par[a]
        return a
    d=((T[:,None,:2]-T[None,:,:2])**2).sum(-1)
    for i,j in zip(*np.nonzero(np.triu(d<r*r,1))): par[f(i)]=f(j)
    lab=np.array([f(i) for i in range(n)])
    return [np.nonzero(lab==l)[0] for l in np.unique(lab)]

def count(s,T,mode='greedy'):
    return len(fillfast.fill(s,T,mode))

def rigid(T,idx,dx,dy,dth):
    T2=T.copy(); c=T[idx,:2].mean(0); a=math.radians(dth); ca,sa=math.cos(a),math.sin(a)
    v=T[idx,:2]-c
    T2[idx,0]=c[0]+ca*v[:,0]-sa*v[:,1]+dx; T2[idx,1]=c[1]+sa*v[:,0]+ca*v[:,1]+dy; T2[idx,2]=T[idx,2]+dth
    return T2

def anchor_shrink(T,s0,s1):
    """keep every tilted square's offset to its nearest wall in x and in y"""
    T2=T.copy()
    for k in (0,1):
        far=T[:,k]>s0/2
        T2[far,k]-= (s0-s1)
    return T2

def run(n,side=None,delta=0.002,secs=120,seed=0,tilt=5.0,log=None,P=None):
    rng=random.Random(seed)
    P=P or load()
    s0,A=normalize(P[n]); T0=A[np.abs(A[:,2])>tilt]
    base=count(s0,T0,'exact')
    s=side if side else s0-delta
    groups=cluster(T0)
    # shrink: each patch keeps its offset to the nearest corner (by centroid)
    T=T0.copy()
    for g in groups:
        c=T0[g,:2].mean(0)
        for k in (0,1):
            if c[k]>s0/2: T[g,k]-=(s0-s)
    ok=feasible(T,s,groups)
    cur=count(s,T) if ok else -1
    best=cur; bestT=T.copy(); t0=time.time(); it=0; acc=0
    info=dict(n=n,s0=s0,s=s,ntilt=len(T0),patches=[len(g) for g in groups],base_at_s0=base,start=cur)
    print(json.dumps(info),flush=True)
    temp=0.6
    while time.time()-t0<secs and best<n:
        it+=1
        r=rng.random(); T2=T.copy(); groups2=groups
        g=groups[rng.randrange(len(groups))]
        if r<0.45:
            sc=10**rng.uniform(-3.5,-0.7)
            T2=rigid(T,g,rng.gauss(0,sc),rng.gauss(0,sc),0.0)
        elif r<0.65:
            T2=rigid(T,g,0,0,rng.gauss(0,10**rng.uniform(-2.5,0)))
        elif r<0.8:
            sc=10**rng.uniform(-3.5,-0.7)
            T2=rigid(T,g,rng.gauss(0,sc),rng.gauss(0,sc),rng.gauss(0,10**rng.uniform(-2.5,0)))
        elif r<0.93:
            # slip one lattice row of the patch along its own direction
            i=g[rng.randrange(len(g))]; th=math.radians(T[i,2])
            if rng.random()<0.5: th+=math.pi/2
            u=np.array([math.cos(th),math.sin(th)]); nrm=np.array([-u[1],u[0]])
            row=[j for j in g if abs((T[j,:2]-T[i,:2])@nrm)<0.3]
            d=rng.gauss(0,10**rng.uniform(-3,-0.7))
            T2[row,0]+=d*u[0]; T2[row,1]+=d*u[1]
        else:
            # single tilted square jiggle
            i=g[rng.randrange(len(g))]; sc=10**rng.uniform(-3.5,-1)
            T2[i,0]+=rng.gauss(0,sc); T2[i,1]+=rng.gauss(0,sc); T2[i,2]+=rng.gauss(0,0.5)
        if not feasible(T2,s,groups): continue
        c2=count(s,T2)
        if c2>=cur or rng.random()<math.exp((c2-cur)/temp):
            T,cur=T2,c2; acc+=1
            if cur>best:
                best=cur; bestT=T.copy()
                print('it %d t %.0fs best %d/%d'%(it,time.time()-t0,best,n),flush=True)
        temp=max(0.15,temp*0.9995)
    ex=count(s,bestT,'exact') if best>0 else -1
    res=dict(info,best=best,exact=ex,iters=it,acc=acc,secs=round(time.time()-t0,1),win=bool(ex>=n))
    print(json.dumps(res),flush=True)
    return res,bestT,s

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('n',type=int); ap.add_argument('--side',type=float); ap.add_argument('--delta',type=float,default=0.002)
    ap.add_argument('--secs',type=float,default=120); ap.add_argument('--seed',type=int,default=0); ap.add_argument('--tilt',type=float,default=5.0); ap.add_argument('--out')
    a=ap.parse_args()
    res,T,s=run(a.n,a.side,a.delta,a.secs,a.seed,a.tilt)
    if a.out and res['win']:
        R=fillfast.fill(s,T,'exact')
        with open(a.out,'w') as h:
            h.write('%d %r\n'%(len(R),s))
            for x,y,d in R[:a.n]: h.write('%r %r %r\n'%(x,y,d))
