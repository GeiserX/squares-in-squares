import hashlib,math,numpy as np

def key(P,decimals=6):
 P=np.array(P,float);variants=[]
 for reflected in [False,True]:
  Q=P.copy()
  if reflected:Q[:,0]*=-1;Q[:,2]*=-1
  for r in range(4):
   if r:
    Q[:,[0,1]]=Q[:,[1,0]];Q[:,0]*=-1;Q[:,2]+=math.pi/2
   A=Q.copy();A[:,2]=(A[:,2]+math.pi/4)%(math.pi/2)-math.pi/4
   half=(np.abs(np.cos(A[:,2]))+np.abs(np.sin(A[:,2])))/2
   A[:,0]-=np.min(A[:,0]-half);A[:,1]-=np.min(A[:,1]-half)
   A=np.round(A,decimals);A[np.abs(A)<.5*10**-decimals]=0
   order=np.lexsort((A[:,2],A[:,1],A[:,0]));variants.append(hashlib.sha256(A[order].tobytes()).hexdigest())
 return min(variants)
