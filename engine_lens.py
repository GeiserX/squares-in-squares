#!/usr/bin/env python3
"""engine E2: rigid lattice-patch ("lens") generator + exact upright fill.

State: K patches, each a p x q block of a square lattice turned by phi, centre (cx, cy), four corner trims.
Cells that leave the box or hit an earlier patch are clipped. Uprights come from Evan Daniel's fillfast.
SA over the ~9 numbers per patch maximises the fill count at a fixed side.

  engine_lens.py N [--side S] [--secs 300] [--seed 0] [--init fit|rand]
"""
import argparse, math, random, json, time
from engine_lib import *
from engine_patch import corners, pen_matrix, cluster
import fillfast

def patch(p,q,phi,cx,cy,tr=(0,0,0,0)):
    i,j=np.meshgrid(np.arange(q)-(q-1)/2,np.arange(p)-(p-1)/2,indexing='ij')
    ii,jj=np.meshgrid(np.arange(q),np.arange(p),indexing='ij')
    keep=(ii+jj>=tr[0])&((q-1-ii)+jj>=tr[1])&(ii+(p-1-jj)>=tr[2])&((q-1-ii)+(p-1-jj)>=tr[3])
    a=math.radians(phi); c,s=math.cos(a),math.sin(a)
    x=cx+c*i-s*j; y=cy+s*i+c*j
    d=phi%90.0
    if d>45: d-=90
    return np.c_[x[keep],y[keep],np.full(keep.sum(),d)]

def build(state,s):
    T=np.zeros((0,3))
    for st in state:
        A=patch(*st[:5],st[5])
        if not len(A): continue
        P=corners(A); ok=(P.min((1,2))>=-1e-9)&(P.max((1,2))<=s+1e-9)
        A=A[ok]
        if len(T) and len(A):
            d=((A[:,None,:2]-T[None,:,:2])**2).sum(-1)
            bad=np.zeros(len(A),bool)
            for a_,t_ in zip(*np.nonzero(d<2.0)):
                if not bad[a_] and pen_matrix(A[a_:a_+1],T[t_:t_+1])[0,0]>1e-9: bad[a_]=True
            A=A[~bad]
        T=np.r_[T,A]
    return T

def fit(n,P):
    s0,A=normalize(P[n]); T=A[np.abs(A[:,2])>5]
    out=[]
    for g in cluster(T):
        if len(g)<6: continue
        X=T[g,:2]; c=X.mean(0); ang=np.median(T[g,2])
        # long axis by PCA, snapped to the lattice direction
        w,v=np.linalg.eigh(np.cov((X-c).T)); ax=v[:,1]; pa=math.degrees(math.atan2(ax[1],ax[0]))
        phi=min((ang+k*90 for k in range(-2,3)),key=lambda t:abs(((t-pa+90)%180)-90))
        a=math.radians(phi); u=np.array([math.cos(a),math.sin(a)]); vv=np.array([-u[1],u[0]])
        q=int(round(np.ptp((X-c)@u)))+1; p=int(round(np.ptp((X-c)@vv)))+1
        out.append([p,q,phi,float(c[0]),float(c[1]),(0,0,0,0)])
    return s0,out

def mutate(st,rng,s):
    st=[list(x) for x in st]; k=rng.randrange(len(st)); x=st[k]; r=rng.random()
    if r<0.3:
        sc=10**rng.uniform(-3,-0.3); x[3]+=rng.gauss(0,sc); x[4]+=rng.gauss(0,sc)
    elif r<0.5: x[2]+=rng.gauss(0,10**rng.uniform(-2,0.5))
    elif r<0.62: x[0]=max(1,x[0]+rng.choice((-1,1)))
    elif r<0.74: x[1]=max(1,x[1]+rng.choice((-1,1)))
    elif r<0.9:
        t=list(x[5]); i=rng.randrange(4); t[i]=max(0,t[i]+rng.choice((-1,1))); x[5]=tuple(t)
    else:
        sc=10**rng.uniform(-3,-0.5); x[3]+=rng.gauss(0,sc); x[4]+=rng.gauss(0,sc); x[2]+=rng.gauss(0,10**rng.uniform(-2,0))
    return st

def run(n,side,secs,seed,P,init='fit',quiet=False):
    rng=random.Random(seed)
    s0,st=fit(n,P); s=side or s0
    if init=='rand':
        st=[[rng.randint(3,8),rng.randint(5,14),rng.choice((1,-1))*rng.uniform(15,45)+rng.choice((0,90)),rng.uniform(3,s-3),rng.uniform(3,s-3),(0,0,0,0)] for _ in range(2)]
    T=build(st,s); cur=len(fillfast.fill(s,T,'greedy')); best=cur; bst=st; t0=time.time(); it=0; temp=1.0
    if not quiet: print(json.dumps(dict(n=n,s0=s0,s=s,init=[x[:5] for x in st],start=cur)),flush=True)
    while time.time()-t0<secs and best<n:
        it+=1; st2=mutate(st,rng,s); T2=build(st2,s); c2=len(fillfast.fill(s,T2,'greedy'))
        if c2>=cur or rng.random()<math.exp((c2-cur)/temp):
            st,cur=st2,c2
            if cur>best:
                best,bst=cur,st
                if not quiet: print('it %d t %.0fs best %d/%d'%(it,time.time()-t0,best,n),flush=True)
        temp=max(0.2,temp*0.999)
    T=build(bst,s); ex=len(fillfast.fill(s,T,'exact'))
    res=dict(n=n,s=s,best=best,exact=ex,iters=it,secs=round(time.time()-t0,1),state=bst,ntilt=len(T))
    print(json.dumps(res),flush=True)
    return res

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('n',type=int); ap.add_argument('--side',type=float); ap.add_argument('--secs',type=float,default=300)
    ap.add_argument('--seed',type=int,default=0); ap.add_argument('--init',default='fit')
    a=ap.parse_args(); run(a.n,a.side,a.secs,a.seed,load(),a.init)
