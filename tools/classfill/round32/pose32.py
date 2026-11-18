"""Measure pose change under square symmetries, without a source-share gate."""
import math
import numpy as np
from scipy.spatial import cKDTree

def movement(P,B):
 P=np.asarray(P);B=np.asarray(B);x=P[:,:2]-(P[:,:2].min(0)+P[:,:2].max(0))/2;y=B[:,:2]-(B[:,:2].min(0)+B[:,:2].max(0))/2;tree=cKDTree(y);best=None
 for swap in (False,True):
  for sx in (-1,1):
   for sy in (-1,1):
    Q=(x[:,::-1] if swap else x)*[sx,sy];d,idx=tree.query(Q)
    axes=np.column_stack((np.cos(P[:,2]),np.sin(P[:,2])));axes=(axes[:,::-1] if swap else axes)*[sx,sy]
    delta=(np.arctan2(axes[:,1],axes[:,0])-B[idx,2]+math.pi/4)%(math.pi/2)-math.pi/4
    c=float(d.max());a=float(np.abs(delta).max());r=dict(maximum=max(c,a),centres=c,angles=a,swap=swap,sx=sx,sy=sy)
    if best is None or r['maximum']<best['maximum']:best=r
 return best

if __name__=='__main__':
 from pathlib import Path
 from light29 import load
 P=load(Path('$SCRATCH/bounties-squares/take-classfill-r32/work/held/10.csv'),{10})[10];P=np.array(P)
 Q=P.copy();Q[:,:2]=P[:,[1,0]]+[.123,-.456];Q[:,2]=math.pi-P[:,2]
 same=movement(Q,P);assert same['maximum']<1e-10,same
 Q=P.copy();Q[0,0]+=.001;changed=movement(Q,P);assert changed['maximum']>1e-5,changed
 print('POSE_CONTROL_PASS translated/reflected/angle-wrapped copy',same,'moved point',changed)
