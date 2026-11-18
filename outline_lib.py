"""outline avenue: shared helpers. A block is a set of tilted squares at one angle. Each square gets whole lattice
coordinates (i, j) by following neighbours, so slips in both lattice directions are allowed: a neighbour along a row
is 1 away along the row and up to 0.5 off it. The outline is the set of occupied (i, j).

Evan Daniel's MIT packer (fillfast, the fq binary) is imported from its clone under SQ_BOX/ext/evand, never copied."""
import os, sys, math, collections
os.environ.setdefault('SQ_BEST','$SCRATCH/bounties-squares/gather/rowangle-2026-11-10b.csv')
os.environ.setdefault('SQ_TMP','$SCRATCH/outline/tmp')
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from engine_lib import BOX, load, normalize, hw
from engine_fq import quench, POLISH, write_txt, read_txt
import numpy as np, fillfast

def fold(d): return (np.asarray(d,float)+45.0)%90.0-45.0
def tilted_mask(X,tilt=5.0): return np.abs(fold(X[:,2]))>tilt
def patches(T,link=1.6):
    """connected groups of tilted squares (centres closer than `link`), largest first"""
    n=len(T); lab=-np.ones(n,int); out=[]
    for s in range(n):
        if lab[s]>=0: continue
        lab[s]=len(out); st=[s]; g=[s]
        while st:
            a=st.pop(); d=np.hypot(T[:,0]-T[a,0],T[:,1]-T[a,1])
            for b in np.where((d<link)&(lab<0))[0]: lab[b]=lab[a]; st.append(b); g.append(b)
        out.append(sorted(g))
    out.sort(key=len,reverse=True); return out
def frame(T):
    """block angle (degrees, median of the folded angles made positive) and the centres turned into the block frame"""
    a=fold(T[:,2]); th=float(np.median(np.where(a<0,a+90,a))); r=math.radians(th); c,s=math.cos(r),math.sin(r)
    return th,np.stack([T[:,0]*c+T[:,1]*s,-T[:,0]*s+T[:,1]*c],1)
def label(T,tol=0.2,slip=0.55):
    """(theta, {(i,j): index}) by following neighbours from the square nearest the centre. tol: allowed error of the
    1.0 spacing; slip: allowed sideways slip between neighbours"""
    th,Q=frame(T); n=len(T); c=Q.mean(0); s=int(np.argmin(np.hypot(Q[:,0]-c[0],Q[:,1]-c[1])))
    ij={s:(0,0)}; st=[s]
    while st:
        a=st.pop(); d=Q-Q[a]
        for b in range(n):
            if b in ij: continue
            du,dv=d[b]
            if abs(abs(du)-1)<tol and abs(dv)<slip: ij[b]=(ij[a][0]+int(np.sign(du)),ij[a][1]); st.append(b)
            elif abs(abs(dv)-1)<tol and abs(du)<slip: ij[b]=(ij[a][0],ij[a][1]+int(np.sign(dv))); st.append(b)
    return th,{v:k for k,v in ij.items()},Q
def show(cells):
    """text map of an outline: one line per j (top first), '#' occupied"""
    I=[c[0] for c in cells]; J=[c[1] for c in cells]; out=[]
    for j in range(max(J),min(J)-1,-1):
        out.append(''.join('#' if (i,j) in cells else '.' for i in range(min(I),max(I)+1)))
    return '\n'.join(out)
def refill(L,T,n,tau=0.0):
    """exact upright refill around the tilted squares T at side L; None when it holds fewer than n"""
    X=np.array(fillfast.fill(L,np.asarray(T,float).reshape(-1,3),mode='exact',tau=tau),float)
    return X if len(X)>=n else None
def trim_to(X,n,T):
    """drop surplus uprights: the ones nearest the block (they give it room)"""
    if len(X)<=n: return X
    t=tilted_mask(X,1e-9); c=T[:,:2].mean(0); d=np.hypot(X[:,0]-c[0],X[:,1]-c[1]); d[t]=1e9
    keep=np.ones(len(X),bool); keep[np.argsort(d)[:len(X)-n]]=False
    return X[keep]
def relax(s,X,rounds=3,eps=1e-9):
    """fq with the default flags and the deep polish flags in turn, until neither gains"""
    cur,best=s,X
    for _ in range(rounds):
        imp=False
        for fl in ((),POLISH):
            s2,X2,_=quench(cur,best,fl)
            if s2 is not None and s2<cur-eps: cur,best,imp=s2,X2,True
        if not imp: break
    return cur,best
