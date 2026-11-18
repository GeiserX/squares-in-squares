"""Shared helpers of the engine_* tools. SQ_BOX is the lane's box dir (Evan Daniel's MIT packer is imported from its
clone under ext/evand, never copied here); SQ_BEST is the submission the tools read."""
import os, sys, csv, math, collections
BOX=os.environ.get('SQ_BOX','$SCRATCH/bounties-squares')
LANE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BOX,'ext/evand/search/packer'))
import numpy as np
BEST=os.environ.get('SQ_BEST',os.path.join(BOX,'gather/assembled-2026-11-09d-safe.csv'))
def hw(t): return (abs(math.cos(t))+abs(math.sin(t)))/2
def load(path=BEST):
    P=collections.defaultdict(list)
    with open(path) as f:
        r=csv.reader(f); next(r)
        for row in r: P[int(row[1])].append((float(row[3]),float(row[4]),float(row[5])))
    return P
def normalize(sq):
    """-> (s, array (x,y,deg in (-45,45]) in box [0,s]^2)"""
    x0=min(x-hw(a) for x,y,a in sq); y0=min(y-hw(a) for x,y,a in sq)
    s=max(max(x-x0+hw(a) for x,y,a in sq), max(y-y0+hw(a) for x,y,a in sq))
    out=[]
    for x,y,a in sq:
        d=math.degrees(a)%90.0
        if d>45: d-=90
        out.append((x-x0,y-y0,d))
    return s,np.array(out)
def split(A,tol=1e-7):
    t=np.abs(A[:,2])>tol
    return A[t],A[~t]
