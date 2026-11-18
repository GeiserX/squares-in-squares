#!/usr/bin/env python3
"""outline avenue: the outline search at the level of a gadget.

A board-class layout is a chain of gadgets along the fault between two corner lattices (Chris Deotte's fault-line
composition). A gadget is w x h cells that hold w*h + dm squares inside (w + f) x (h + f); the side of a puzzle is
K + the largest f of its chain. So the outline that matters is the outline of a gadget: which squares of a donor
packing are kept inside the w x h window. The public fault DP keeps the w*h + dm squares that stick out least and
never tries another choice. Here each gadget that binds many puzzles gets an outline search:

  donor   the same key cut from other donors (a looser cut can sit in another basin)
  swap    an edge square of the cut leaves and the next square outside the cut enters
  kick    the public squeeze loop (loosen, nudge, squeeze), as the base line

Every variant keeps the count exactly (a cut only deletes), and is scored by fq in rectangle mode: the score is f, a
length, not a count. Improved gadgets join the DP's table, the DP runs again, and every composition that beats the
base file is certified.

The fault DP, the crop and the rectangle quench are imported from alex chilton's public starter kit (dataset
alexchilton/squares-in-squares-starter-kit: fault_dp.py, skeleton.py, ensemble.py), unpacked under OUTLINE_KIT and never
copied here. fq is Evan Daniel's (MIT), from the lane's clone.

  outline_gadget.py dp    WORK BASE.csv [DONOR.csv ...]            # extract, DP, compose; writes WORK/dp0/<n>.csv
  outline_gadget.py rank  WORK [--top 60] [--delta 0.01]           # gadget keys by how much score a lower f would give
  outline_gadget.py search WORK [--top 60] [--budget 40] [--jobs 3] [--kinds kick,donor,swap]
  outline_gadget.py redp  WORK OUT                                 # DP again with the improved gadgets; OUT/<n>.csv
"""
import sys, os, math, json, time, argparse, pickle, glob
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
BOX=os.environ.get('SQ_BOX','$SCRATCH/bounties-squares')
KIT=os.environ.get('OUTLINE_KIT','$SCRATCH/outline/kit')
os.environ.setdefault('FQ_BIN',os.path.join(BOX,'ext/evand/search/packer/target/release/fq'))
sys.path.insert(0,KIT)
import numpy as np
import fault_dp as F, skeleton as S
from ensemble import side

def load_donors(paths):
    seen,donors=set(),[]
    for p in paths:
        for n,sq in F.load_csv(p).items():
            k=(n,round(side(sq),9))
            if k not in seen: seen.add(k); donors.append(sq)
    return donors
def compose_all(G,donors,cur,out,nmin=100,log=F.log,tables=None):
    """DP over the gadget table, then every composition below the base side, certified. -> {n: (L0, L)}"""
    os.makedirs(out,exist_ok=True)
    dp,PG,PM,PQ=tables if tables else F.run_dp(G)
    wins={}; tot=0.0
    for n in range(nmin,1001):
        K=math.isqrt(n); D=n-K*K
        if D==0 or D>F.DMAX or K>F.WMAX: continue
        L0=side(cur[n]) if n in cur else math.ceil(math.sqrt(n))
        f,links=F.chain(dp,PG,PM,PQ,G,K,D)
        if f is None or K+f+2*F.E>=L0-1e-7: continue
        try: sq=F.compose(K,D,f,links,G,donors)
        except AssertionError as e: log('n=%d compose failed %r'%(n,e)); continue
        r=F.certify_ladder(n,sq)
        if r is None or r[0]>=L0-1e-9: continue
        wins[n]=(L0,r[0]); tot+=(L0-r[0])/math.sqrt(n)
        with open(os.path.join(out,'%d.csv'%n),'w') as h:
            h.write('n,square_id,x,y,angle\n')
            for i,(x,y,t) in enumerate(r[1]): h.write('%d,%d,%r,%r,%r\n'%(n,i,float(x),float(y),float(t)))
        log('n=%d: %.9f -> %.9f gain %.2e, %d gadgets | total %.6f'%(n,L0,r[0],(L0-r[0])/math.sqrt(n),len(links),tot))
    return wins,(dp,PG,PM,PQ)
def rank(G,tables,cur,delta=0.01,nmin=100):
    """score a key would give if its f came down by delta, from the chains the DP picks now. The binding gadget of a
    chain is the one with the largest f; its drop is capped by the next gadget of the chain."""
    dp,PG,PM,PQ=tables; lev={}; uses={}
    for n in range(nmin,1001):
        K=math.isqrt(n); D=n-K*K
        if D==0 or D>F.DMAX or K>F.WMAX: continue
        L0=side(cur[n]) if n in cur else math.ceil(math.sqrt(n))
        f,links=F.chain(dp,PG,PM,PQ,G,K,D)
        if f is None: continue
        fs=sorted(((G[g,3],g) for g,_ in links),reverse=True)
        g=fs[0][1]; nxt=fs[1][0] if len(fs)>1 else 0.0
        gap=max(K+f-L0,0.0); gain=max(0.0,min(delta,f-nxt)-gap)/math.sqrt(n)
        key=tuple(int(v) for v in G[g,:3]); uses.setdefault(key,[]).append(n)
        if gain>0: lev[key]=lev.get(key,0.0)+gain
    return sorted(lev.items(),key=lambda kv:-kv[1]),uses
def cuts(donors,key,top=6,slack=0.04):
    """the key cut from every donor under its 8 symmetries: the `top` smallest f, one per donor. -> [(f, donor, sym)]"""
    w,h,dm=key; k=w*h+dm-1; out=[]
    for di,sq in enumerate(donors):
        if len(sq)<=k: continue
        best=None
        for si,sym in enumerate(F.SYMS):
            _,xlo,xhi,ylo,yhi=F.mapped(sq,sym)
            R=np.maximum(np.maximum(xhi-w,yhi-h),0.0); f=np.partition(R,k)[k]
            if best is None or f<best[0]: best=(float(f),di,si)
        out.append(best)
    out.sort(); 
    return [c for c in out[:top] if c[0]<=out[0][0]+slack]
def swap_variants(donor,sym,key,edge=5,outside=3):
    """cuts that differ from the least-overhang cut by one square: one of the `edge` kept squares that stick out most
    leaves, one of the `outside` nearest dropped squares enters"""
    w,h,dm=key; sq,xlo,xhi,ylo,yhi=F.mapped(donor,F.SYMS[sym]); R=np.maximum(np.maximum(xhi-w,yhi-h),0.0)
    o=np.argsort(R,kind='stable'); k=w*h+dm; keep=o[:k]; rest=o[k:k+outside]; out=[]
    for a in keep[::-1][:edge]:
        for b in rest:
            idx=[i for i in keep if i!=a]+[b]; out.append(sq[idx])
    return out
def squeeze_job(job):
    """one variant: public squeeze loop for `budget` seconds. -> (key, kind, f0, f1, squares)"""
    key,kind,sq,budget=job; w,h,dm=key; t0=time.time(); f0=S.overhang(sq,w,h)
    best,fb=S.quench(sq,w,h,loosen=1.0)
    if not (fb<f0): best,fb=sq,f0
    k=0
    while time.time()-t0<budget:
        k+=1
        cand,f=S.quench(best,w,h,loosen=1.0+0.01*(k%5),kick=0.01*(k%3),seed=k)
        if f<fb and len(cand)==w*h+dm: best,fb=cand,f
    return key,kind,f0,fb,best
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('work'); ap.add_argument('rest',nargs='*')
    ap.add_argument('--top',type=int,default=60); ap.add_argument('--delta',type=float,default=0.01); ap.add_argument('--budget',type=float,default=40)
    ap.add_argument('--jobs',type=int,default=3); ap.add_argument('--kinds',default='kick,donor,swap'); ap.add_argument('--nmin',type=int,default=100)
    ap.add_argument('--skip',type=int,default=0,help='skip the first SKIP ranked keys (already searched)')
    a=ap.parse_args(); W=a.work; os.makedirs(W,exist_ok=True); st=os.path.join(W,'state.pkl')
    if a.cmd=='dp':
        base,extra=a.rest[0],a.rest[1:]; donors=load_donors([base]+extra); F.log('%d donors'%len(donors))
        G=F.extract(donors); cur=F.load_csv(base)
        wins,tables=compose_all(G,donors,cur,os.path.join(W,'dp0'),a.nmin)
        pickle.dump(dict(base=base,donors=donors,G=G,tables=tables,cur={n:float(side(q)) for n,q in cur.items()}),open(st,'wb'))
        F.log('DONE dp: %d n below the base, total %.6f'%(len(wins),sum((x-y)/math.sqrt(n) for n,(x,y) in wins.items())))
    elif a.cmd in ('rank','search'):
        S_=pickle.load(open(st,'rb')); G,donors,tables=S_['G'],S_['donors'],S_['tables']; cur=F.load_csv(S_['base'])
        lev,uses=rank(G,tables,cur,a.delta,a.nmin)
        F.log('%d keys have leverage at delta %.3f, total %.5f'%(len(lev),a.delta,sum(v for _,v in lev)))
        for key,v in lev[:a.top]: print('%dx%d+%d\tleverage %.6f\tbinds %d n'%(key+(v,len(uses[key]))))
        if a.cmd=='search':
            kinds=a.kinds.split(','); jobs=[]
            for key,v in lev[a.skip:a.top]:
                cs=cuts(donors,key)
                if not cs: continue
                f0,di,si=cs[0]; w,h,dm=key
                if 'kick' in kinds: jobs.append((key,'kick',F.crop(donors[di],si,w,h,dm)[0],a.budget))
                if 'donor' in kinds:
                    for f,d2,s2 in cs[1:]: jobs.append((key,'donor',F.crop(donors[d2],s2,w,h,dm)[0],a.budget/2))
                if 'swap' in kinds:
                    for v_ in swap_variants(donors[di],si,key): jobs.append((key,'swap',v_,a.budget/4))
            F.log('%d variants on %d keys'%(len(jobs),len(lev[a.skip:a.top])))
            from multiprocessing import Pool
            best={}; ref={k:cuts(donors,k,top=1)[0][0] for k in {j[0] for j in jobs}}
            with Pool(a.jobs) as pool, open(os.path.join(W,'search.tsv'),'a') as h:
                for key,kind,f0,f1,sq in pool.imap_unordered(squeeze_job,jobs):
                    h.write('%dx%d+%d\t%s\t%.9f\t%.9f\t%.9f\n'%(key+(kind,ref[key],f0,f1))); h.flush()
                    if f1<ref[key]-1e-9 and (key not in best or f1<best[key][0]):
                        best[key]=(f1,sq,kind); F.log('%dx%d+%d %s: f %.6f -> %.6f'%(key+(kind,ref[key],f1)))
            old={}
            p=os.path.join(W,'improved.pkl')
            if os.path.exists(p): old=pickle.load(open(p,'rb'))
            for k,v in best.items():
                if k not in old or v[0]<old[k][0]: old[k]=v
            pickle.dump(old,open(p,'wb'))
            import collections
            F.log('DONE search: %d keys lower, by kind %s'%(len(best),dict(collections.Counter(v[2] for v in best.values()))))
    elif a.cmd=='redp':
        S_=pickle.load(open(st,'rb')); G,donors=S_['G'],S_['donors']; cur=F.load_csv(S_['base'])
        imp=pickle.load(open(os.path.join(W,'improved.pkl'),'rb')); new=[v[1] for v in imp.values()]
        Gn=F.extract(new); Gn[:,6]+=len(donors); G2=np.concatenate([G,Gn]); donors2=donors+new
        wins,_=compose_all(G2,donors2,cur,a.rest[0],a.nmin)
        F.log('DONE redp: %d n below the base, total %.6f'%(len(wins),sum((x-y)/math.sqrt(n) for n,(x,y) in wins.items())))
