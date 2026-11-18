"""Compare whole layouts under every square-box symmetry."""
import csv,json,math,pathlib
import numpy as np
from scipy.spatial import cKDTree
W=pathlib.Path(__file__).resolve().parent

def load(p):return np.array([[float(r[k])for k in ('x','y','angle')]for r in csv.DictReader(open(p))])
def normal(a):
 a=a.copy();h=.5*(abs(np.cos(a[:,2]))+abs(np.sin(a[:,2])));a[:,:2]-=(a[:,:2]-h[:,None]).min(0);return a

def compare(a,b):
 a=normal(a);tree=cKDTree(a[:,:2]);best=None
 for k in range(4):
  t=k*math.pi/2;rot=np.array([[math.cos(t),-math.sin(t)],[math.sin(t),math.cos(t)]])
  for flip in (1,-1):
   M=rot@np.diag([flip,1]);q=b.copy();q[:,:2]=q[:,:2]@M.T
   v=np.column_stack((np.cos(q[:,2]),np.sin(q[:,2])))@M.T;q[:,2]=np.arctan2(v[:,1],v[:,0]);q=normal(q)
   dist,idx=tree.query(q[:,:2])
   if len(set(idx))!=len(a):continue
   angle=abs((q[:,2]-a[idx,2]+math.pi/4)%(math.pi/2)-math.pi/4)
   r=dict(max_position=float(dist.max()),rms_position=float(np.sqrt(np.mean(dist**2))),max_angle=float(angle.max()),rotation=k,reflection=flip)
   if best is None or r['max_position']+r['max_angle']<best['max_position']+best['max_angle']:best=r
 return best
if __name__=='__main__':
 jobs=json.load(open(W/'jobs.json'));ids=['l001332x921x438','l002438x921x518'];a,b=[load(W/next(j for j in jobs if j['id']==key)['start'])for key in ids]
 shifted=a.copy();shifted[:,:2]+=np.array([3.,-2.]);pos=compare(a,shifted);assert pos['max_position']<1e-11 and pos['max_angle']<1e-11
 altered=a.copy();altered[100,0]+=.001;neg=compare(a,altered);assert neg['max_position']>.0009
 result=dict(control_translation=pos,control_changed_square=neg,legs=ids,comparison=compare(a,b));(W/'leg-comparison.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
