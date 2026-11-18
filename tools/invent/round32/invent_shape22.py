import hashlib, math
import numpy as np

def fingerprint(a):
 a=np.asarray(a,dtype=float)
 variants=[]
 for reflect in (False,True):
  b=a.copy()
  if reflect:b[:,0]*=-1;b[:,2]*=-1
  for k in range(4):
   if k:b[:,:2]=np.column_stack((-b[:,1],b[:,0]))
   c=b.copy();c[:,:2]-=c[:,:2].min(0)
   c[:,2]%=math.pi/2
   c[:,2][np.minimum(c[:,2],math.pi/2-c[:,2])<5e-6]=0
   c=np.round(c,7);c[c==0]=0
   c=c[np.lexsort((c[:,2],c[:,1],c[:,0]))]
   variants.append(hashlib.sha256(c.tobytes()).hexdigest())
 return min(variants)

if __name__=='__main__':
 a=np.array([[0.,0.,0.],[2.,0.,.2],[1.,2.,.4]])
 b=a.copy();b[:,:2]=np.column_stack((-a[:,1],a[:,0]))+7;b[:,2]+=math.pi/2
 c=a.copy();c[:,0]*=-1;c[:,2]*=-1
 d=a.copy();d[0,0]+=.001
 assert fingerprint(a)==fingerprint(b)==fingerprint(c)
 assert fingerprint(a)!=fingerprint(d)
 print('PASS: translation, quarter turn and reflection give one key; a 0.001 centre move gives another')
