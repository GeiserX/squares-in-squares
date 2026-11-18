#!/usr/bin/env python3
"""probe.py HELD.csv N [N ...]: how far above the held side does the layout of n + 2m + 1 with one shell cut out
(the jog cuts of midm_soft.py) become soft-free? For each n it settles the best cuts in boxes at the held side
plus 0, 0.01, 0.02, 0.04, 0.08, 0.16 and 0.32 and prints the lowest energy of each box. Run from the lane dir."""
import sys, math, numpy as np
sys.path.insert(0, '.')
import methods_lp as mlp, methods_soft as ms, midm_soft as mz
ms.load_kernel()
sub=sys.argv[1]
for n in [int(v) for v in sys.argv[2:]]:
    held=mlp.normal(mlp.load(sub,{n})[n]); Lh=mlp.side(held); m=int(Lh); nu=n+2*m+1
    D=mlp.load(sub,{nu})[nu]; rng=np.random.default_rng(1)
    res=[]
    for off in (0.0, 0.01, 0.02, 0.04, 0.08, 0.16, 0.32):
        box=Lh-2e-4+off; got=[]
        for P,tag in mz.jog_seeds(D,n,box,rng=rng,cap=1500):
            Q,E=ms.relax(P,box,200); got.append((E,Q,tag))
        got.sort(key=lambda z:z[0]); best=None
        for E,Q,tag in got[:12]:
            Q,E=mz.settle(Q,box)
            if best is None or E<best[0]: best=(E,Q,tag)
        res.append((off,best[0],best[2],len(got)))
        if best[0]<1e-10*n: break
    print('n=%d held %.6f donor %d side %.6f (peeled %.6f)'%(n,Lh,nu,mlp.side(D),mlp.side(D)-1), ' '.join('+%.2f:%.1e'%(r[0],r[1]) for r in res), '| cuts',res[-1][3],'|',res[-1][2], flush=True)
