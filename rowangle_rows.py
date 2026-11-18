#!/usr/bin/env python3
"""rowangle: the patch model with one angle per row. Each tilted patch of a held packing is read as a stack of rows;
every row keeps its own tilt, direction and slide (a few dozen numbers per packing). A move changes one row only:
one more square at an end, one fewer, a turn of the row, or a slide along itself. All other tilted squares stay
where the relaxed packing has them, uprights included. Evan Daniel's fq quench (MIT, run from his clone) relaxes
the result, and floatsafe certifies a smaller side.

  rowangle_rows.py report N [N ...]          rows of each patch: count, tilt, direction, slide, fit residuals
  rowangle_rows.py search OUTDIR [--ns a,b | --trail] [--jobs 3] [--max-moves 400]
  rowangle_rows.py control N                 damage one row end, quench, then ask the search to find the way back
"""
import argparse, csv, json, math, os, sys, time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from engine_lib import *
from engine_patch import corners, pen_matrix, cluster
from engine_fq import quench, POLISH
import fillfast

def rows_of(Tg):
    """-> list of rows; a row = indices into Tg ordered along the row. The row axis is the square axis along which
    neighbours line up best (smaller residual of the two choices)."""
    th0=float(np.median(Tg[:,2])); best=None
    for th in (th0,th0+90.0):
        a=math.radians(th); u=np.array([math.cos(a),math.sin(a)]); v=np.array([-u[1],u[0]])
        A=Tg[:,:2]@u; B=Tg[:,:2]@v; o=np.argsort(B); rows=[[o[0]]]
        for i in o[1:]:
            if B[i]-B[rows[-1][-1]]<0.45 and abs(B[i]-B[rows[-1][0]])<0.8: rows[-1].append(i)
            else: rows.append([i])
        rows=[sorted(r,key=lambda i:A[i]) for r in rows]
        gaps=np.concatenate([np.diff(A[r]) for r in rows if len(r)>1] or [np.array([9.0])])
        res=float(np.sqrt(((gaps-1)**2).mean()))
        if best is None or res<best[0]: best=(res,rows)
    return best[1]
def row_fit(Tg,r):
    """own tilt (mean square angle, deg), own direction (deg, of the line through the centres), rms off that line"""
    X=Tg[r,:2]; th=float(Tg[r,2].mean())
    if len(r)<2: return th,th,0.0,0.0
    c=X.mean(0); w,V=np.linalg.eigh(np.cov((X-c).T)); d=V[:,1]
    if d@(X[-1]-X[0])<0: d=-d
    return th,math.degrees(math.atan2(d[1],d[0])),float(np.sqrt(max(w[0],0))),float(Tg[r,2].std())
def patches(A,minsize=6):
    T=np.nonzero(np.abs(A[:,2])>0.5)[0]
    return [T[g] for g in cluster(A[T]) if len(g)>=minsize] if len(T) else []
def report(n,A,s):
    out=[]
    for pi,g in enumerate(patches(A)):
        Tg=A[g]; rows=rows_of(Tg); ths=[]; one=float(np.median(Tg[:,2]))
        print('n=%d patch %d: %d squares, %d rows, median tilt %.3f, tilt spread (sd) %.3f'%(n,pi,len(g),len(rows),one,Tg[:,2].std()))
        for r in rows:
            th,ph,off,sd=row_fit(Tg,r); ths.append((th,len(r),sd))
            print('   row of %d  tilt %.3f  direction %.3f  tilt sd inside the row %.3f  off-line rms %.4f'%(len(r),th,ph,sd,off))
        within=math.sqrt(sum(l*sd*sd for _,l,sd in ths)/len(g)); between=float(np.sqrt(sum(l*(t-Tg[:,2].mean())**2 for t,l,_ in ths)/len(g)))
        print('   tilt spread: %.3f between rows, %.3f inside rows'%(between,within))
        out.append((len(g),len(rows),between,within))
    return out

def moves(A,max_moves=400,rng=None):
    """yield (name, packing) for one-row changes that keep n. A: whole packing (x, y, deg). Every square that the move
    does not name stays where the relaxed packing has it, uprights included (a refill of the uprights loses their
    relaxed places: the quench then ends 0.003 above the held side of 498).
      ext: the upright next to a row end becomes one more square of that row
      del: the square at a row end becomes an upright at the same centre
      turn, slide: the row turns about its centre, or slides along itself"""
    ti=np.nonzero(np.abs(A[:,2])>0.5)[0]; up=np.nonzero(np.abs(A[:,2])<=0.5)[0]; out=[]
    if not len(ti): return out
    T=A[ti]
    for pi,g in enumerate([g for g in cluster(T) if len(g)>=6]):
        Tg=T[g]; rows=rows_of(Tg)
        for ri,r in enumerate(rows):
            idx=ti[g[r]]; th,ph,_,_=row_fit(Tg,r); d=np.array([math.cos(math.radians(ph)),math.sin(math.radians(ph))])
            if len(r)<2:
                a=math.radians(th); d=np.array([math.cos(a),math.sin(a)])
            for e,i in (('lo',idx[0]),('hi',idx[-1])):
                sg=-1.0 if e=='lo' else 1.0; p=A[i,:2]+sg*d
                if len(up):
                    dd=((A[up,:2]-p)**2).sum(1); j=up[int(np.argmin(dd))]
                    if dd.min()<1.0:
                        A2=A.copy(); A2[j]=(p[0],p[1],A[i,2]); out.append(('ext p%d r%d %s'%(pi,ri,e),A2))
                if len(r)>1:
                    A2=A.copy(); A2[i,2]=0.0; out.append(('del p%d r%d %s'%(pi,ri,e),A2))
            c=A[idx,:2].mean(0)
            for dth in (-1.0,-0.4,0.4,1.0):
                a=math.radians(dth); R=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]]); A2=A.copy()
                A2[idx,:2]=c+(A[idx,:2]-c)@R.T; A2[idx,2]=A[idx,2]+dth; out.append(('turn p%d r%d %+.1f'%(pi,ri,dth),A2))
            for sl in (-0.5,-0.2,0.2,0.5):
                A2=A.copy(); A2[idx,:2]=A[idx,:2]+sl*d; out.append(('slide p%d r%d %+.1f'%(pi,ri,sl),A2))
    if len(out)>max_moves:
        import random
        (rng or random.Random(0)).shuffle(out); out=out[:max_moves]
    return out
def run_move(s,A2,deep=True):
    s2,X2,dt=quench(s,A2,())
    if s2 is None: return None,None,dt
    if deep and s2<s+2e-4:
        s3,X3,_=quench(s2,X2,POLISH)
        if s3 is not None and s3<s2: s2,X2=s3,X3
    return s2,X2,dt
def search_one(n,A,s,max_moves=400,log=None,deep=True,only=None):
    """-> (best side, packing, move) over all one-row moves, each relaxed by fq"""
    best=(s,None,None); tried=0; sides=[]
    for name,A2 in moves(A,max_moves):
        if only and not name.startswith(only): continue
        tried+=1; s2,X2,dt=run_move(s,A2,deep)
        if s2 is None: continue
        sides.append(s2)
        if log: log.write('%d\t%s\t%r\t%.1f\n'%(n,name,s2-s,dt)); log.flush()
        if s2<best[0]-1e-9: best=(s2,X2,name)
    return best,tried,sides
def job(a):
    n,sq,out,mm=a
    s,A=normalize(sq); t0=time.time()
    with open(os.path.join(out,'moves-%d.tsv'%n),'w') as log:
        best,tried,sides=search_one(n,A,s,mm,log); reach=tried
    res=None
    if best[1] is not None:
        from engine_polish import certify
        L,fr=certify(n,best[1])
        if L is not None and L<s-1e-9:
            with open(os.path.join(out,'%d.csv'%n),'w',newline='') as h:
                w=csv.writer(h); w.writerow(['n','square_id','x','y','angle'])
                for r in fr: w.writerow([r['n'],r['square_id'],r['x'],r['y'],r['angle']])
            res=(L,best[2])
    return n,s,tried,reach,(min(sides)-s if sides else None),res,time.time()-t0
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('args',nargs='*'); ap.add_argument('--ns'); ap.add_argument('--trail',action='store_true')
    ap.add_argument('--jobs',type=int,default=3); ap.add_argument('--max-moves',type=int,default=400)
    a=ap.parse_args(); P=load()
    if a.cmd=='report':
        for n in map(int,a.args):
            s,A=normalize(P[n]); report(n,A,s)
    elif a.cmd=='control':
        n=int(a.args[0]); s,A=normalize(P[n])
        s0,_,_=run_move(s,A); print('null move: held %.9f, quench %+.3e'%(s,s0-s),flush=True)
        dels=[(nm,A2) for nm,A2 in moves(A,10**6) if nm.startswith('del')]
        for nm,A2 in dels[::max(1,len(dels)//5)][:5]:
            s1,X1,_=run_move(s,A2)
            if s1 is None: print('damage %s: quench failed'%nm); continue
            best,tried,sides=search_one(n,X1,s1,10**6,only='ext')
            print('damage %s: quench %+.6f above held; %d ext moves from it, best %+.3e against held (%s)'%(nm,s1-s,tried,best[0]-s,best[2]),flush=True)
    else:
        out=a.args[0]; os.makedirs(out,exist_ok=True)
        if a.ns: ns=[int(x) for x in a.ns.split(',')]
        elif a.trail: ns=[int(r['n']) for r in csv.DictReader(open(os.path.join(LANE,'tools/targets-2026-11-09.tsv')),delimiter='\t') if int(r['short'])>0]
        else: ns=sorted(P)
        from multiprocessing import Pool
        tot=0.0; wins=0; t0=time.time()
        with Pool(a.jobs) as pool, open(os.path.join(out,'rows.tsv'),'a') as h:
            for n,s,tried,reach,bd,res,sec in pool.imap_unordered(job,[(n,P[n],out,a.max_moves) for n in ns]):
                h.write('%d\t%r\t%d\t%d\t%s\t%s\t%s\t%.0f\n'%(n,s,tried,reach,'' if bd is None else repr(bd),res[0] if res else '',res[1] if res else '',sec)); h.flush()
                if res:
                    g=(s-res[0])/math.sqrt(n); tot+=g; wins+=1
                    print('WIN n=%d %.9f -> %.9f (%s) gain %.3e (total %.3e, %d wins, %.0fs)'%(n,s,res[0],res[1],g,tot,wins,time.time()-t0),flush=True)
        print(json.dumps(dict(n_tried=len(ns),wins=wins,total_gain=tot,secs=round(time.time()-t0))))
