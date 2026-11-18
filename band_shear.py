"""band lane: sheared blocks from the rigid 45-degree rule.

A rigid a x b block at 45 degrees needs both of its extents to match the grids: f >= fa = (a*sqrt2 - A)/2 and
f >= fb = (b*sqrt2 - B)/2. When fa and fb differ, the block is tight in one direction and loose in the other at the
side where it first fits. An all-free quench (Evan Daniel's fq) can then turn the squares a little and trade the loose
extent for the tight one, as the held n = 261 does (8 x 13, rigid at 0.6924, held at 0.6788).

  band_shear.py ctl                      # positive control: 8 x 13 at m = 16 must come down to the held 0.67878
  band_shear.py scan OUTDIR [--jobs 3] [--mmin 10] [--kmax 12] [--per 6] [--above 0.012]
        for every n = m*m + k where a rigid block ties or beats our side with room left in one direction, build it
        at our side, quench it, and keep what floatsafe certifies below our side.
"""
import sys, os, csv, math, json, time, argparse
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from structure_slot import fillfast
from structure_rigid45 import block, pred, S2
from engine_fq import quench, POLISH
from band_cert import certify
HERE=os.path.dirname(os.path.abspath(__file__))
def build(m,f,a,b,want):
    """rigid a x b block near the centre of the box of side m+f, exact upright fill. returns (count, layout x,y,deg)"""
    L=m+f; best=None; ext=(a+b)/(2*S2); cands=[]
    for i in range(0,2*m+2):
        for j in range(-m,m+1):
            cx=(i+b/S2-f-j+a/S2)/2; cy=(i+b/S2+f+j-a/S2)/2
            if cx-ext<-1e-9 or cy-ext<-1e-9 or cx+ext>L+1e-9 or cy+ext>L+1e-9: continue
            cands.append((abs(cx-L/2)+abs(cy-L/2),cx,cy))
    cands.sort()
    for _,cx,cy in cands[:12]:
        X=fillfast.fill(L,np.array(block(a,b,cx,cy),float),mode='exact')
        if best is None or len(X)>len(best): best=X
        if len(X)>=want: break
    return (0,None) if best is None else (len(best),np.array(best,float))
def fold(d): return (np.asarray(d,float)+45.0)%90.0-45.0     # fq writes an upright square as 0 or 90
def trim_to(X,n,L):
    """drop surplus uprights: the ones nearest the block, which gives it room"""
    if len(X)<=n: return X
    t=np.abs(fold(X[:,2]))>1e-9; c=X[t,:2].mean(0); d=np.hypot(X[:,0]-c[0],X[:,1]-c[1]); d[t]=1e9
    keep=np.ones(len(X),bool); keep[np.argsort(d)[:len(X)-n]]=False
    return X[keep]
def run(m,k,f,a,b,flags=((),POLISH)):
    n=m*m+k; cnt,X=build(m,f,a,b,n)
    if cnt<n: return dict(m=m,k=k,a=a,b=b,f=f,built=cnt,side=None)
    X=trim_to(X,n,m+f); s=m+f; cur=s; best=X
    for _ in range(3):
        imp=False
        for fl in flags:
            s2,X2,dt=quench(cur,best,fl)
            if s2 is not None and s2<cur-1e-9: cur,best,imp=s2,X2,True
        if not imp: break
    return dict(m=m,k=k,a=a,b=b,f=f,built=cnt,side=cur,X=best)
def squeeze(n,s,X,deltas=(0.006,0.003,0.0015,0.0007),tilt=0.5,log=None):
    """refill and quench in turn: shrink the side by a step, keep the tilted squares, refill the uprights exactly on
    the four grids, quench again. A quench cannot change which upright cells exist; the refill can."""
    cur,best=s,X
    for d in deltas:
        for _ in range(40):
            s2=cur-d; T=best[np.abs(fold(best[:,2]))>tilt].copy(); T[:,:2]-=d/2
            if T[:,:2].min()<0.4 or T[:,:2].max()>s2-0.4: break
            F=np.array(fillfast.fill(s2,T,mode='exact'),float)
            if len(F)<n: break
            got=None
            for fl in ((),POLISH):
                s3,X3,_=quench(s2,trim_to(F,n,s2),fl)
                if s3 is not None and s3<cur-1e-8 and (got is None or s3<got[0]): got=(s3,X3)
            if got is None: break
            cur,best=got
            if log: log('   step %g -> %.9f'%(d,cur))
    return cur,best
def candidates(m,k,f0,per):
    """blocks whose rigid gain at our side f0 is at least k, with the most room left in one direction first"""
    out=[]
    for a in range(1,45):
        for b in range(a,45):
            g,A,B=pred(a,b,f0+1e-9)
            if g<k or (A+B)/2+2>m: continue
            ra=A-(a*S2-2*f0); rb=B-(b*S2-2*f0)        # room in each direction, in grid units
            out.append((-(max(ra,rb)-min(ra,rb)),g,a,b))
    out.sort()
    return [(a,b,f0) for _,g,a,b in out[:per]]
def candidates_above(m,k,f0,per,above):
    """blocks that first reach gain k at a side up to `above` over ours: built there, a quench may bring them under"""
    out=[]
    for a in range(1,45):
        for b in range(a,45):
            ts=set()
            for s_ in (a,b):
                for A in range(max(0,int(s_*S2)-2),int(s_*S2)+1):
                    t=(s_*S2-A)/2
                    if f0+1e-7<t<=f0+above: ts.add(round(t,12))
            for t in sorted(ts):
                g,A,B=pred(a,b,t+1e-9)
                if g>=k and (A+B)/2+2<=m: out.append((t,a,b)); break
    out.sort()
    return [(a,b,t+1e-9) for t,a,b in out[:per]]
def job(arg):
    m,k,f0,a,b,out,fb=arg; n=m*m+k; t=time.time()
    try: r=run(m,k,fb,a,b); r['f']=f0; r['f_build']=fb
    except Exception as e: return dict(m=m,k=k,a=a,b=b,err=repr(e))
    X=r.pop('X',None); r['secs']=round(time.time()-t,1); r['n']=n; r['cert']=None
    if r['side'] is not None and r['side']<m+f0-1e-7:
        L,fr=certify(n,X)
        if L is not None and L<m+f0-1e-9:
            r['cert']=L
            with open(os.path.join(out,'%d-%dx%d.csv'%(n,a,b)),'w',newline='') as h:
                w=csv.writer(h); w.writerow(['n','square_id','x','y','angle'])
                for q in fr: w.writerow([q['n'],q['square_id'],q['x'],q['y'],q['angle']])
    return r
if __name__=='__main__':
    if sys.argv[1]=='ctl':
        r=run(16,5,0.6925,8,13); print('8 x 13 at m=16, built',r['built'],'of 261 at 16.6925; quenched side',r['side'],'(held 16.678779876)',flush=True)
        s,X=squeeze(261,r['side'],r['X'],log=print); print('after refill and quench in turn:',s)
        sys.exit()
    ap=argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('out'); ap.add_argument('--jobs',type=int,default=3); ap.add_argument('--mmin',type=int,default=10)
    ap.add_argument('--kmax',type=int,default=12); ap.add_argument('--per',type=int,default=6); ap.add_argument('--above',type=float,default=0.0,help='also blocks whose rigid side is up to this much over ours'); ap.add_argument('--targets',default=os.path.join(HERE,'tools','targets-2026-11-09.tsv'))
    ap.add_argument('--sub',default=os.environ.get('SQ_BEST'))
    a=ap.parse_args(); os.makedirs(a.out,exist_ok=True)
    if a.sub:
        from structure_lib import load, side
        P=load(a.sub); ours={n:side(P[n]) for n in P}
    else: ours={int(r['n']):float(r['ours_L']) for r in csv.DictReader(open(a.targets),delimiter='\t')}
    jobs=[]
    for n in sorted(ours):
        m=int(math.floor(ours[n]+1e-9)); k=n-m*m; f0=ours[n]-m
        if m<a.mmin or k<1 or k>a.kmax or f0<1e-6: continue
        cs=candidates_above(m,k,f0,a.per,a.above) if a.above else candidates(m,k,f0,a.per)
        for (aa,bb,fb) in cs: jobs.append((m,k,f0,aa,bb,a.out,fb))
    print(len(jobs),'jobs',flush=True)
    from multiprocessing import Pool
    wins={}
    with Pool(a.jobs) as pool, open(os.path.join(a.out,'shear.tsv'),'a') as h:
        for r in pool.imap_unordered(job,jobs):
            h.write(json.dumps(r)+'\n'); h.flush()
            if r.get('cert'):
                n=r['n']; g=(r['m']+r['f']-r['cert'])/math.sqrt(n); wins[n]=max(wins.get(n,0),g)
                print('WIN n=%d block %dx%d: %.9f -> %.9f (gain %.2e; %d n, total %.3e)'%(n,r['a'],r['b'],r['m']+r['f'],r['cert'],g,len(wins),sum(wins.values())),flush=True)
    print(json.dumps(dict(jobs=len(jobs),wins=len(wins),total=sum(wins.values()))))
