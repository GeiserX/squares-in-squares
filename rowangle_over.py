#!/usr/bin/env python3
"""rowangle: overcount scan. The exact upright refill with an overlap tolerance sometimes places n + 1 or n + 2
squares around the tilted squares of our n, at our side for n (791 gives 792 at a tolerance of 0.02). Such a start
goes to Evan Daniel's fq (MIT, imported from his clone); the quenched side counts when it is below our side for the
larger n and floatsafe certifies it.

  rowangle_over.py OUTDIR [--jobs 3] [--ns a,b] [--taus 0.02,0.05,0.1,0.15]
"""
import argparse, csv, json, math, os, sys, time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from engine_lib import *
from engine_patch import pen_matrix
from engine_fq import quench, POLISH
import fillfast
P=None; LS={}
def init():
    global P
    P=load()
    for n in P: LS[n]=normalize(P[n])[0]
def job(a):
    n,out,taus=a; s,A=normalize(P[n]); T=A[np.abs(A[:,2])>0.5]; res=[]; seen=set(); wins=[]
    for tau in taus:
        F=fillfast.fill(s,T,'exact',tau=tau); c=len(F)
        for t in range(n+1,min(c,n+2,1000)+1):
            if (t,c) in seen: continue
            seen.add((t,c))
            U=F[len(T):]; pen=pen_matrix(U,T).max(1) if len(T) else np.zeros(len(U))
            X=np.r_[T,U[np.argsort(pen)[:t-len(T)]]]
            s2,X2,dt=quench(s,X,())
            if s2 is not None and s2<LS[t]+2e-4:
                s3,X3,_=quench(s2,X2,POLISH)
                if s3 is not None and s3<s2: s2,X2=s3,X3
            res.append((tau,c,t,None if s2 is None else s2-LS[t]))
            if s2 is not None and s2<LS[t]-1e-9:
                from engine_polish import certify
                L,fr=certify(t,X2)
                if L is not None and L<LS[t]-1e-9:
                    with open(os.path.join(out,'%d-from-%d.csv'%(t,n)),'w',newline='') as h:
                        w=csv.writer(h); w.writerow(['n','square_id','x','y','angle'])
                        for r in fr: w.writerow([r['n'],r['square_id'],r['x'],r['y'],r['angle']])
                    wins.append((t,LS[t],L))
    return n,res,wins
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--jobs',type=int,default=3); ap.add_argument('--ns'); ap.add_argument('--taus',default='0.02,0.05,0.1,0.15')
    a=ap.parse_args(); os.makedirs(a.out,exist_ok=True); init(); taus=[float(x) for x in a.taus.split(',')]
    ns=[int(x) for x in a.ns.split(',')] if a.ns else range(30,1000)
    from multiprocessing import Pool
    t0=time.time(); starts=0; nw=0
    with Pool(a.jobs,initializer=init) as pool, open(os.path.join(a.out,'over.tsv'),'w') as h:
        h.write('n\ttau\tcount\ttarget\tquench_minus_ours\n')
        for n,res,wins in pool.imap_unordered(job,[(n,a.out,taus) for n in ns]):
            for tau,c,t,d in res:
                starts+=1; h.write('%d\t%g\t%d\t%d\t%s\n'%(n,tau,c,t,'' if d is None else repr(d))); h.flush()
            for t,l0,l1 in wins:
                nw+=1; print('WIN n=%d from %d: %.9f -> %.9f gain %.3e'%(t,n,l0,l1,(l0-l1)/math.sqrt(t)),flush=True)
    print(json.dumps(dict(n_tried=len(ns),starts=starts,wins=nw,secs=round(time.time()-t0))))
