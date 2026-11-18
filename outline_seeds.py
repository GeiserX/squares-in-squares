#!/usr/bin/env python3
"""outline avenue: quench every distinct public layout of an n, not only the tightest.

The lane's polish always started from the packing it held. A looser public layout of the same n can sit in another
basin and end lower after fq. `collect` walks harvest dirs and keeps, per n, the tightest layout of each distinct
structure (number of tilted squares, median tilt) within `slack` of the base side. `quench` runs fq on each (deep
polish flags, then the default flags) and keeps what ends below the base side. `certify` runs the lane's floatsafe.

  outline_seeds.py collect SEEDS.pkl BASE.csv DIR [DIR ...] [--nmin 300] [--slack 0.03] [--per 6]
  outline_seeds.py quench  SEEDS.pkl OUT [--jobs 3] [--shard i/k]
  outline_seeds.py certify OUT CERTDIR        # writes CERTDIR/<n>.csv for every certified side below the base
FQ_BIN names the fq binary (default: the lane's clone of Evan Daniel's packer, MIT)."""
import sys, os, math, csv, glob, pickle, time, argparse, subprocess, tempfile, collections
import numpy as np
FQ=os.environ.get('FQ_BIN','$SCRATCH/bounties-squares/ext/evand/search/packer/target/release/fq')
POLISH=['--no-alm','--loosen','1.0','--flip-top','64','--pit','600']
def hwv(t): return (np.abs(np.cos(t))+np.abs(np.sin(t)))/2
def norm(A):
    """rows x, y, radians -> (side, rows x, y, degrees folded to (-45, 45]) in the box [0, side]^2"""
    h=hwv(A[:,2]); x0=(A[:,0]-h).min(); y0=(A[:,1]-h).min(); s=max((A[:,0]+h).max()-x0,(A[:,1]+h).max()-y0)
    d=np.degrees(A[:,2])%90.0; d=np.where(d>45,d-90,d)
    return float(s),np.c_[A[:,0]-x0,A[:,1]-y0,d]
def read_sub(path):
    import pandas as pd
    try: df=pd.read_csv(path)
    except Exception: return {}
    df.columns=[str(c).lower() for c in df.columns]
    if not {'n','x','y','angle'}<=set(df.columns): return {}
    for c in ('x','y','angle'):
        if df[c].dtype==object: df[c]=pd.to_numeric(df[c].astype(str).str.lstrip('s'),errors='coerce')
    df=df.dropna(subset=['n','x','y','angle']); out={}
    for n,g in df.groupby('n'):
        n=int(n)
        if 1<=n<=1000 and len(g)==n: out[n]=g[['x','y','angle']].to_numpy(float)
    return out
def fingerprint(X):
    a=np.abs(X[:,2]); t=a>0.5
    return (int(t.sum()),round(float(np.median(a[t])) if t.any() else 0.0,1))
def quench(s,X,flags=(),timeout=900):
    d=tempfile.mkdtemp(prefix='fq',dir=os.environ.get('SQ_TMP')); a,b=d+'/a.txt',d+'/b.txt'
    with open(a,'w') as h:
        h.write('%d %r\n'%(len(X),float(s)))
        for x,y,dg in X: h.write('%r %r %r\n'%(float(x),float(y),float(dg)))
    out=(None,None)
    try:
        r=subprocess.run([FQ,'quench','--in',a,'--out',b]+list(flags),capture_output=True,text=True,timeout=timeout)
        if r.returncode==0 and os.path.exists(b):
            L=[l.split() for l in open(b) if l.strip()]; out=(float(L[0][1]),np.array([[float(v) for v in q[:3]] for q in L[1:len(X)+1]]))
    except subprocess.TimeoutExpired: pass
    for f in (a,b):
        if os.path.exists(f): os.remove(f)
    os.rmdir(d); return out
def qjob(a):
    n,k,s0,X,base,out=a; cur,best=s0,X; t=time.time()
    for _ in range(3):
        imp=False
        for fl in (POLISH,()):
            s2,X2=quench(cur,best,fl)
            if s2 is not None and s2<cur-1e-9: cur,best,imp=s2,X2,True
        if not imp or cur>base+0.004: break            # far above the base after a full round: give up
    if cur<base-1e-9:
        with open(os.path.join(out,'%d-%d.txt'%(n,k)),'w') as h:
            h.write('%d %r\n'%(n,cur))
            for x,y,dg in best: h.write('%r %r %r\n'%(float(x),float(y),float(dg)))
    return n,k,s0,cur,base,time.time()-t
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('args',nargs='+'); ap.add_argument('--nmin',type=int,default=300)
    ap.add_argument('--slack',type=float,default=0.03); ap.add_argument('--per',type=int,default=6); ap.add_argument('--jobs',type=int,default=3); ap.add_argument('--shard',default='0/1')
    a=ap.parse_args()
    if a.cmd=='collect':
        out,basep,dirs=a.args[0],a.args[1],a.args[2:]
        base={n:norm(X)[0] for n,X in read_sub(basep).items()}; pool=collections.defaultdict(dict); nf=0
        files=[]
        for d in dirs: files+=[p for p in glob.glob(os.path.join(d,'**','*.csv'),recursive=True)]
        for p in sorted(set(files)):
            R=read_sub(p)
            if not R: continue
            nf+=1
            for n,X in R.items():
                if n<a.nmin or n not in base: continue
                try: s,Y=norm(X)
                except Exception: continue
                if not np.isfinite(s) or s>base[n]+a.slack or s>=math.ceil(math.sqrt(n))-1e-9: continue
                fp=fingerprint(Y)
                if fp not in pool[n] or s<pool[n][fp][0]: pool[n][fp]=(s,Y,p)
            if nf%20==0: print(nf,'files,',sum(len(v) for v in pool.values()),'layouts',flush=True)
        seeds=[]
        for n in sorted(pool):
            for k,(s,Y,p) in enumerate(sorted(pool[n].values(),key=lambda v:v[0])[:a.per]): seeds.append((n,k,s,Y,base[n],p))
        pickle.dump(seeds,open(out,'wb'),protocol=4)
        print('%d files read, %d seeds on %d n; %d are not the tightest of their n'%(nf,len(seeds),len(pool),sum(1 for q in seeds if q[1]>0)))
    elif a.cmd=='quench':
        seeds=pickle.load(open(a.args[0],'rb')); out=a.args[1]; os.makedirs(out,exist_ok=True); i,k=[int(v) for v in a.shard.split('/')]
        jobs=[(n,kk,s,Y,b,out) for j,(n,kk,s,Y,b,p) in enumerate(seeds) if j%k==i]
        done=set()
        lp=os.path.join(out,'quench-%d.tsv'%i)
        if os.path.exists(lp): done={tuple(int(v) for v in l.split('\t')[:2]) for l in open(lp)}
        # a seed that is the base layout itself is the polish sweep's work, not this tool's: skip it
        jobs=[j for j in jobs if (j[0],j[1]) not in done and abs(j[2]-j[4])>1e-7]; jobs.sort(key=lambda j:j[2]-j[4])
        from multiprocessing import Pool
        w=0; tot=0.0
        with Pool(a.jobs) as pool, open(lp,'a') as h:
            for n,kk,s0,s1,b,dt in pool.imap_unordered(qjob,jobs):
                h.write('%d\t%d\t%r\t%r\t%r\t%.1f\n'%(n,kk,s0,s1,b,dt)); h.flush()
                if s1<b-1e-9: w+=1; print('BELOW n=%d seed %d: start %.6f (base %+.6f) -> %.9f, %.2e of score'%(n,kk,s0,s0-b,s1,(b-s1)/math.sqrt(n)),flush=True)
        print('done: %d seeds, %d below the base'%(len(jobs),w))
    elif a.cmd=='certify':
        sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
        from band_cert import certify
        src,dst=a.args; os.makedirs(dst,exist_ok=True); best={}
        for p in glob.glob(os.path.join(src,'*.txt')):
            L=[l.split() for l in open(p) if l.strip()]; n=int(L[0][0]); s=float(L[0][1])
            if n not in best or s<best[n][0]: best[n]=(s,np.array([[float(v) for v in q[:3]] for q in L[1:n+1]]),p)
        for n in sorted(best):
            s,X,p=best[n]; L,fr=certify(n,X)
            print(n,'fq side %.9f'%s,'certified',L,flush=True)
            if L is None: continue
            with open(os.path.join(dst,'%d.csv'%n),'w',newline='') as h:
                w=csv.writer(h); w.writerow(['n','square_id','x','y','angle'])
                for q in fr: w.writerow([q['n'],q['square_id'],q['x'],q['y'],q['angle']])
