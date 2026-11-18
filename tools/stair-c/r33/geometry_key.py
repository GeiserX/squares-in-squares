"""Identify unchanged whole-layout geometry before repeating a matched pair."""
import hashlib,numpy as np

def key(points):
 a=np.asarray(points,float);xy=a[:,:2]-(a[:,:2].min(0)+a[:,:2].max(0))/2
 axes=np.column_stack((np.cos(a[:,2]),np.sin(a[:,2])));keys=[]
 for swap in (False,True):
  for sx in (-1,1):
   for sy in (-1,1):
    q=(xy[:,::-1]if swap else xy)*[sx,sy]
    v=(axes[:,::-1]if swap else axes)*[sx,sy]
    t=np.arctan2(v[:,1],v[:,0])
    z=np.round(np.column_stack((q,np.cos(4*t),np.sin(4*t))),8);z[z==0]=0.
    z=z[np.lexsort(tuple(z[:,i]for i in (3,2,1,0)))]
    keys.append(hashlib.sha256(z.tobytes()).hexdigest())
 return min(keys)

def control():
 a=np.array([[.1,.2,.3],[1.3,2.7,.71],[3.8,1.4,.12]])
 b=a[::-1].copy();b[:,0]*=-1;b[:,2]=np.pi-b[:,2];b[:,:2]+=[19,-7]
 assert key(a)==key(b)
 changed=a.copy();changed[1,0]+=.0001
 assert key(changed)!=key(a)
 print('CONTROL whole geometry: reordered mirrored translated copy matches; changed centre differs',flush=True)
