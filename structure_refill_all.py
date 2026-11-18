"""structure lane: exact upright refill of every held layout at its own side; reports n where the refill holds more than n squares."""
import sys, math, time, json
import numpy as np
from structure_lib import *
from structure_slot import count
import fillfast
P=load()
lo=int(sys.argv[1]); hi=int(sys.argv[2]); thr=float(sys.argv[3]) if len(sys.argv)>3 else 0.5
for n in range(lo,hi+1):
    sq=P[n]; x0,y0,x1,y1=bbox(sq); L=max(x1-x0,y1-y0)
    T=[(x-x0,y-y0,math.degrees(a)) for x,y,a in sq if abs(norm(a))>thr]
    try:
        out=fillfast.fill(L,np.array(T,float).reshape(-1,3),mode='exact')
        N=len(out)
    except Exception as e:
        print(json.dumps({'n':n,'err':str(e)[:80]}),flush=True); continue
    if N!=n: print(json.dumps({'n':n,'L':L,'tilted':len(T),'refill':N,'delta':N-n}),flush=True)
print('done',lo,hi,flush=True)
