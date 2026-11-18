"""Run the imported corner hops with temperature 0.05 instead of 0.01."""
import pathlib,pickle,sys
import numpy as np
R=pathlib.Path.home()/'scratch/squares-twoshort';sys.path.insert(0,str(R/'lane'));import zone_corner as Z
original=Z.hops
def hotter(*args,**kwargs):
 kwargs['temp']=.05
 return original(*args,**kwargs)
Z.hops=hotter
base=pickle.load(open(R/'design-control/base.pkl','rb'));mod=Z.cmod(8,8)
b=min(base,key=lambda q:Z.loss_of(mod,q['f'],q['count'],q['y0'],q['x0']))
r=Z.hops(b['P'],mod,b['f'],b['y0']+.04,b['x0']+.04,30,np.random.default_rng(22))
loss=Z.loss_of(mod,b['f'],b['count'],r[0],r[1]);print('CONTROL hot temp .05 opened loss 3.051973224 recovered %.12f tries %d'%(loss,r[3]),flush=True)
assert r[3]>0 and loss<2.49,loss
print('EXPERIMENT temp .05',flush=True)
args=sys.argv[1:]
if args and args[0]=='search':args=args[1:]
assert args and pathlib.Path(args[0]).exists(),args
Z.cmd_search(args)
