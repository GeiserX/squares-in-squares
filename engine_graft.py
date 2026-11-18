#!/usr/bin/env python3
"""engine E4: graft + grow. Take the tilted patches of a donor n0, anchor each to its nearest corner in the target
n's box (side = our held side for n), then climb the tolerant fill count with lattice hops (engine_hop moves) until
it reaches n, quench with fq, certify. Also probes plain placement first.

  engine_graft.py N DONOR OUTDIR [--secs 300] [--seed 0] [--side S]
"""
import argparse, math, random, json, time, os, csv, sys
from engine_lib import *
from engine_patch import corners, cluster
from engine_hop import relattice, clip
from engine_fq import quench
import fillfast

def anchor(T,groups,s0,s):
    T2=T.copy()
    for g in groups:
        c=T[g,:2].mean(0)
        for k in (0,1):
            if c[k]>s0/2: T2[g,k]+=(s-s0)
    return T2

def cnt(s,T,tau): return len(fillfast.fill(s,T,'greedy',tau=tau))

def run(n,donor,out,secs,seed,side,P,tau=0.05):
    from engine_polish import certify
    rng=random.Random(seed); os.makedirs(out,exist_ok=True)
    s_t,At=normalize(P[n]); s=side or s_t
    s_d,Ad=normalize(P[donor]); T=Ad[np.abs(Ad[:,2])>5]; groups=cluster(T)
    T=anchor(T,groups,s_d,s); P_=corners(T)
    if P_.min()<-1e-9 or P_.max()>s+1e-9: print(json.dumps(dict(n=n,donor=donor,err='donor patches leave the box'))); return
    cur=cnt(s,T,tau); start=cur; t0=time.time(); it=0; nq=0; best=None; sides=[]; top=cur
    while time.time()-t0<secs:
        it+=1; groups=cluster(T); big=[g for g in groups if len(g)>=6]
        if not big: break
        g=rng.choice(big); rest=np.delete(T,g,axis=0); r=rng.random(); dth=dx=dy=0.0; edit=None
        if r<0.5: edit=rng.choice(('addline','addline','addcell','delcell','delline'))
        elif r<0.7: dth=rng.gauss(0,0.5)
        else: dx,dy=rng.gauss(0,0.15),rng.gauss(0,0.15)
        Tg=relattice(T[g],dth,dx,dy,edit,rng)
        if Tg is None: continue
        Tn=clip(Tg,rest,s,1e-9); T2=np.r_[rest,Tn]; c2=cnt(s,T2,tau)
        if c2>=cur or rng.random()<math.exp((c2-cur)/0.5):
            T,cur=T2,c2; top=max(top,cur)
        if cur>=n:
            R=fillfast.fill(s,T,'greedy',tau=tau); X=R[:len(T)]; U=R[len(T):]
            X=np.r_[X,U[:n-len(T)]] if len(T)<n else R[:n]
            s2,X2,dt=quench(s,X,()); nq+=1
            if s2 is not None:
                sides.append(s2)
                if s2<s_t-1e-9 and (best is None or s2<best-1e-9):
                    L,fr=certify(n,X2)
                    if L is not None and L<s_t-1e-9:
                        best=L
                        with open(os.path.join(out,'%d.csv'%n),'w',newline='') as h:
                            w=csv.writer(h); w.writerow(['n','square_id','x','y','angle'])
                            for r_ in fr: w.writerow([r_['n'],r_['square_id'],r_['x'],r_['y'],r_['angle']])
                        print('WIN n=%d donor=%d %.9f -> %.9f'%(n,donor,s_t,L),flush=True)
            # step back so the walk keeps exploring
            cur=cur
    print(json.dumps(dict(n=n,donor=donor,s_target=s_t,s=s,start=start,top=top,iters=it,quenches=nq,best=best,
                          sides_min_med=[min(sides),float(np.median(sides))] if sides else [],secs=round(time.time()-t0))),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('n',type=int); ap.add_argument('donor',type=int); ap.add_argument('out')
    ap.add_argument('--secs',type=float,default=300); ap.add_argument('--seed',type=int,default=0); ap.add_argument('--side',type=float); ap.add_argument('--sub',default=BEST)
    a=ap.parse_args(); run(a.n,a.donor,a.out,a.secs,a.seed,a.side,load(a.sub))
