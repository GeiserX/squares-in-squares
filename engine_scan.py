#!/usr/bin/env python3
"""engine: graft scan. For each target n that trails the board, place the tilted patches of nearby donors (each patch
anchored to its nearest corner) in a box a little smaller than our held side and count the exact upright refill.
A count >= n is a start for fq + certify.   engine_scan.py OUT.tsv [--back 8] [--fwd 3] [--eps 2e-5]"""
import argparse, csv, os, sys, json, time
from engine_lib import *
from engine_patch import corners, cluster
from engine_graft import anchor
import fillfast
ap=argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--back',type=int,default=8); ap.add_argument('--fwd',type=int,default=3); ap.add_argument('--eps',type=float,default=2e-5)
a=ap.parse_args(); P=load()
rows=list(csv.DictReader(open(os.path.join(LANE,'tools/targets-2026-11-09.tsv')),delimiter='\t'))
tg=[int(r['n']) for r in rows if int(r['short'])>0]
N={}
def norm(n):
    if n not in N:
        s,A=normalize(P[n]); T=A[np.abs(A[:,2])>0.5]; N[n]=(s,T,cluster(T) if len(T) else [])
    return N[n]
t0=time.time(); hits=0; tried=0
with open(a.out,'w') as h:
    for n in tg:
        s=norm(n)[0]-a.eps; best=(0,None)
        for d in list(range(max(1,n-a.back),n))+list(range(n+1,min(1000,n+a.fwd)+1)):
            sd,T,groups=norm(d)
            if not len(T): continue
            T2=anchor(T,groups,sd,s); Pc=corners(T2)
            if Pc.min()<-1e-9 or Pc.max()>s+1e-9: continue
            # patches anchored to different corners must not collide after the shift: fill's own test is upright-only
            from engine_patch import feasible
            if not feasible(T2,s,groups): continue
            tried+=1; c=len(fillfast.fill(s,T2,'greedy'))
            if c>best[0]: best=(c,d)
            if c>=n:
                hits+=1; print('HIT n=%d donor=%d count=%d side=%.6f'%(n,d,c,s),flush=True)
        h.write('%d\t%r\t%s\t%s\n'%(n,s,best[0],best[1])); h.flush()
print(json.dumps(dict(targets=len(tg),fills=tried,hits=hits,secs=round(time.time()-t0))))
