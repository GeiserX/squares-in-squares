"""Use small local kicks in the imported corner search without changing its solver."""
import math,pathlib,pickle,sys
import numpy as np
R=pathlib.Path.home()/'scratch/squares-twoshort';sys.path.insert(0,str(R/'lane'));import zone_corner as Z

def weak(P,mod,f,y0,x0,rng):
 Q=P.copy();i=int(rng.integers(len(Q)));radius=rng.uniform(1.2,3.0);sigma=float(rng.choice([.003,.006,.01,.02]));near=np.linalg.norm(Q[:,:2]-Q[i,:2],axis=1)<radius
 Q[near,:2]+=rng.normal(0,sigma,(int(near.sum()),2));Q[near,2]+=rng.normal(0,math.degrees(.5*sigma),int(near.sum()))
 return Q,y0+.04,x0+.04,'local-small'
Z.hop=weak
# Recover the known 8x8 control from stack faces opened by 0.04 on each arm.
base=pickle.load(open(R/'design-control/base.pkl','rb'));b=min(base,key=lambda b:Z.loss_of(Z.cmod(8,8),b['f'],b['count'],b['y0'],b['x0']));mod=Z.cmod(8,8)
loss0=Z.loss_of(mod,b['f'],b['count'],b['y0']+.04,b['x0']+.04)
r=Z.hops(b['P'],mod,b['f'],b['y0']+.04,b['x0']+.04,20,np.random.default_rng(22))
loss=Z.loss_of(mod,b['f'],b['count'],r[0],r[1]);print('CONTROL opened loss %.9f recovered %.9f tries %d'%(loss0,loss,r[3]),flush=True)
assert r[3]>0 and loss<2.49,(loss0,loss,r[3])
Z.cmd_search(sys.argv[1:])
