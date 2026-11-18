"""Kick at the bar side, with a fixed-square compression of the initial centres."""
import pathlib,sys
D=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(D/'lane'))
import invent_rest as I
import family_step as F
import methods_lp as M
import numpy as np

def compressed(p,target):
 s,p=F.canon(np.asarray(p,dtype=float))
 if target>=s:return p
 low,high=0.,1.
 for unused in range(60):
  scale=(low+high)/2
  q=p.copy();q[:,:2]*=scale
  if M.side(q)>target:high=scale
  else:low=scale
 q=p.copy();q[:,:2]*=low
 q=M.normal(q)
 assert abs(M.side(q)-target)<1e-10
 assert np.array_equal(q[:,2],p[:,2])
 return q

def controls():
 p=np.array([[.5,.5,0.],[1.7,.5,0.]])
 q=compressed(p,2.0)
 assert abs(M.side(q)-2.)<1e-12 and M.min_gap(q)>-1e-12
 assert np.allclose(compressed(p,2.3),F.canon(p)[1])
 tilted=np.array([[.8,.8,.2],[2.3,1.2,.3]])
 q=compressed(tilted,2.1)
 assert abs(M.side(q)-2.1)<1e-12 and np.array_equal(q[:,2],tilted[:,2])
 print('CONTROL bar compression reaches target side, preserves angles and retains smaller inputs',flush=True)

if __name__=='__main__':
 controls()
 if '--controls' in sys.argv:raise SystemExit(0)
 target=float(sys.argv[sys.argv.index('--bar')+1])
 original=F.load
 def load(*args,**kwargs):
  packings=original(*args,**kwargs)
  return {n:compressed(p,target) for n,p in packings.items()}
 F.load=load
 I.main()
