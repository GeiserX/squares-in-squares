"""heldshare.py FILE [FILE...]: fraction of a layout's square centres within 1e-3 and 1e-2 of a centre of the held
round35a row of the same n (bounding-box corner aligned, best of 8 square symmetries). A start that shares most of
its squares with the held row is the held optimum plus a perturbation."""
import sys,csv,math,numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0,'.');import methods_lp as mlp
S='$SCRATCH/bounties-squares/'
_h={}
def held(n):
 if not _h:
  for r in csv.DictReader(open(S+'gather/round35-2026-11-17a.csv')):_h.setdefault(int(r['n']),[]).append((float(r['x'].lstrip('s')),float(r['y'].lstrip('s'))))
 return np.array(_h[n])
def norm(c):return c-c.min(0)
def share(p,n=None):
 if n is None:n=int(next(csv.DictReader(open(p)))['n'])
 A=norm(np.array([[float(r['x'].lstrip('s')),float(r['y'].lstrip('s'))] for r in csv.DictReader(open(p))]));B=norm(held(n))
 L=max(A.max(),B.max());t=cKDTree(B);best=(0,0)
 for k in range(8):
  X=A.copy()
  if k&1:X[:,0]=A[:,0].max()-X[:,0]
  if k&2:X[:,1]=A[:,1].max()-X[:,1]
  if k&4:X=X[:,::-1]
  d,_=t.query(X);best=max(best,(float((d<1e-3).mean()),float((d<1e-2).mean())))
 return n,best
if __name__=='__main__':
 for p in sys.argv[1:]:
  n,b=share(p);print('%d share1e-3 %.3f share1e-2 %.3f %s'%(n,b[0],b[1],p.replace(S,'')))
