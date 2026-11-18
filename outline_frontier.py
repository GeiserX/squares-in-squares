#!/usr/bin/env python3
"""outline avenue: outline moves scored on the frontier (count, side), not at a fixed n.

A move on a tilted block (outline_search.gen_moves, plus whole end rows and columns in or out) changes how many
uprights the exact refill places, so the state after a move holds c squares with c near n, seldom n itself. Scoring at
a fixed n throws those states away (the 261 control: every move ends 1 to 9 squares short). Here every state is
quenched as it is and compared with the base side of its own count c: a win is a side below base[c]. Deleting a
square never hurts, so a state also wins c - 1 and c - 2 when its side is below those base sides.

  outline_frontier.py run OUT N [N ...] [--jobs 3] [--kinds growrow,cutrow,growcol,cutcol,row,col] [--cap 40] [--minpatch 10]
  outline_frontier.py ctl OUT [--jobs 3]     # control: a base layout with one end row cut must come back, and the null move must return the base side
SQ_BEST is the base submission. OUTLINE_DC (3): quench only states whose count is within DC of n. OUTLINE_TMO (120): seconds
per fq call. OUTLINE_LOCAL=1: regional refill, only the uprights within OUTLINE_R (4) of the change are placed again (for
layouts whose uprights are off the wall grids, where the full refill ends short). OUTLINE_NEAR (0.002): keep quenching only while the side is within this of a base side. Wins are written as OUT/<c>-from<n>-<move>.txt (fq text format), certify with
outline_seeds.py certify."""
import sys, os, math, json, time, argparse, pickle, random
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from outline_lib import *
import outline_search as OS
DC=int(os.environ.get('OUTLINE_DC','3')); TMO=float(os.environ.get('OUTLINE_TMO','120')); NEAR=float(os.environ.get('OUTLINE_NEAR','0.002')); LOCAL=os.environ.get('OUTLINE_LOCAL')=='1'; RADIUS=float(os.environ.get('OUTLINE_R','4'))
def blocks(X,minpatch=10,tilt=5.0):
    """every tilted patch of at least minpatch squares, as outline_search block dicts"""
    idx=np.where(tilted_mask(X,tilt))[0]; out=[]
    if len(idx)==0: return out
    T=X[idx]
    for g in patches(T):
        if len(g)<minpatch: continue
        gi=idx[g]; th,cells,Q=label(X[gi]); cells={c:int(gi[k]) for c,k in cells.items()}
        U=[];V=[]
        for (i,j),a in cells.items():
            b=cells.get((i+1,j)); c=cells.get((i,j+1))
            if b is not None: U.append(X[b,:2]-X[a,:2])
            if c is not None: V.append(X[c,:2]-X[a,:2])
        r=math.radians(th); U=np.mean(U,0) if U else np.array([math.cos(r),math.sin(r)]); V=np.mean(V,0) if V else np.array([-math.sin(r),math.cos(r)])
        inb=set(cells.values())
        out.append(dict(theta=th,cells=cells,U=U,V=V,other=[int(k) for k in idx if k not in inb]))
    return out
def big_moves(B,kinds):
    """whole end rows and columns in or out"""
    c=B['cells']; rows={}; cols={}; out=[]
    for (i,j) in c: rows.setdefault(j,[]).append(i); cols.setdefault(i,[]).append(j)
    J=sorted(rows); I=sorted(cols)
    if 'growrow' in kinds:
        for j,dj in ((J[-1],1),(J[0],-1)): out.append(('growrow%+d'%dj,[],[(i,j+dj) for i in sorted(rows[j])]))
    if 'cutrow' in kinds and len(J)>2:
        for j in (J[-1],J[0]): out.append(('cutrow@%d'%j,[(i,j) for i in rows[j]],[]))
    if 'growcol' in kinds:
        for i,di in ((I[-1],1),(I[0],-1)): out.append(('growcol%+d'%di,[],[(i+di,j) for j in sorted(cols[i])]))
    if 'cutcol' in kinds and len(I)>2:
        for i in (I[-1],I[0]): out.append(('cutcol@%d'%i,[(i,j) for j in cols[i]],[]))
    return out
def new_tilted(s,X,B,rem,add):
    """as outline_search.apply_move, but an added square that leaves the box or lands on a kept tilted square is skipped"""
    c=B['cells']; drop={c[r] for r in rem if r in c}; keep=[k for k in list(c.values())+B['other'] if k not in drop]
    T=[X[k] for k in keep]; ang=float(np.median([X[k,2] for k in c.values()])); h=hw(math.radians(ang))
    cells={k:v for k,v in c.items() if v not in drop}; pos={k:X[v,:2] for k,v in cells.items()}; n_add=0
    for (i,j) in add:
        p=[]
        for (di,dj,vec) in ((1,0,-B['U']),(-1,0,B['U']),(0,1,-B['V']),(0,-1,B['V'])):
            q=pos.get((i+di,j+dj))
            if q is not None: p.append(q+vec)
        if not p: continue
        p=np.mean(p,0)
        if p[0]-h<0 or p[1]-h<0 or p[0]+h>s or p[1]+h>s: continue
        if any(abs(p[0]-t[0])<0.7 and abs(p[1]-t[1])<0.7 for t in T): continue
        T.append(np.array([p[0],p[1],ang])); pos[(i,j)]=p; n_add+=1
    if add and n_add==0: return None
    return np.array(T,float).reshape(-1,3)
def local_fill(s,X,B,rem,add,R=None):
    """regional refill: every square farther than R from the change stays where it is (uprights too, also the ones off
    the wall grids). The removed block squares go, the uprights within R of the change go, and the freed room is
    filled exactly with uprights."""
    R=RADIUS if R is None else R
    c=B['cells']; drop={c[r] for r in rem if r in c}; T=new_tilted(s,X,B,rem,add)
    if T is None: return None
    nk=len(c)-len(drop)+len(B['other']); new=T[nk:]
    ch=np.array([X[k,:2] for k in drop]+[q[:2] for q in new]).reshape(-1,2); up=~tilted_mask(X)
    keep=[k for k in range(len(X)) if k not in drop and not (up[k] and (np.hypot(ch[:,0]-X[k,0],ch[:,1]-X[k,1])<R).any())]
    K=np.r_[X[keep],new] if len(new) else X[keep]
    return np.array(fillfast.fill(s,K,mode='exact'),float)
def fjob(a):
    n,s,X,bi,mv,base,out=a; name,rem,add=mv; t=time.time()
    try:
        B=blocks(X)[bi]; T=new_tilted(s,X,B,rem,add)
        if T is None: return n,bi,name,None,None,[],0.0
        F=local_fill(s,X,B,rem,add) if LOCAL else np.array(fillfast.fill(s,T,mode='exact'),float); c=len(F)
        if c not in base or abs(c-n)>DC: return n,bi,name,c,None,[],time.time()-t
        # one round first (default flags, then deep polish); more rounds only when the side is near the base side
        s2,X2=s,F
        for rnd in range(4):
            imp=False
            for fl in ((),POLISH):
                s3,X3,_=quench(s2,X2,fl,timeout=TMO)
                if s3 is not None and s3<s2-1e-9: s2,X2,imp=s3,X3,True
            if not imp or s2>min(base[cc] for cc in (c,c-1,c-2) if cc in base)+NEAR: break
        wins=[]
        for cc in (c,c-1,c-2):
            if cc in base and s2<base[cc]-1e-7:
                wins.append(cc); Y=X2 if cc==c else X2[np.argsort(-np.abs(X2[:,0]-s2/2)-np.abs(X2[:,1]-s2/2))[c-cc:]]
                write_txt(os.path.join(out,'%d-from%d-b%d-%s.txt'%(cc,n,bi,name.replace('@','_'))),s2,Y)
        return n,bi,name,c,s2,wins,time.time()-t
    except Exception as e:
        return n,bi,name,None,None,[repr(e)],time.time()-t
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('out'); ap.add_argument('ns',nargs='*',type=int); ap.add_argument('--jobs',type=int,default=3)
    ap.add_argument('--kinds',default='growrow,cutrow,growcol,cutcol'); ap.add_argument('--cap',type=int,default=40); ap.add_argument('--minpatch',type=int,default=10); ap.add_argument('--seed',type=int,default=0)
    a=ap.parse_args(); os.makedirs(a.out,exist_ok=True); kinds=tuple(a.kinds.split(',')); rng=random.Random(a.seed)
    P=load(os.environ['SQ_BEST']); base={}; N={}
    for n in P:
        if n>=50: N[n]=normalize(P[n]); base[n]=N[n][0]
    from multiprocessing import Pool
    if a.cmd=='ctl':
        ok=0; tot=0
        for n in (a.ns or [593,643,747]):
            s,X=N[n]; Bs=blocks(X)
            # null move: refill the uprights around the held tilted squares, quench: the base side must come back
            T=X[tilted_mask(X)]; F=refill(s,T,n); s0=relax(s,F,rounds=2)[0] if F is not None else None
            print('n=%d null move: refill %s, quench %s, base %.9f'%(n,'ok' if F is not None else 'short',s0,s),flush=True)
            for bi,B in enumerate(Bs[:2]):
                for name,rem,add in big_moves(B,('cutrow',))[:1]:
                    T2=new_tilted(s,X,B,rem,add); F2=np.array(fillfast.fill(s,T2,mode='exact'),float); c=len(F2); s2,X2=relax(s,F2,rounds=2)
                    # put the row back from the damaged state
                    B2=[b for b in blocks(X2)]; back=None
                    for bj,Bb in enumerate(B2):
                        for nm,r2,a2 in big_moves(Bb,('growrow',)):
                            T3=new_tilted(s2,X2,Bb,r2,a2)
                            if T3 is None: continue
                            F3=np.array(fillfast.fill(s2,T3,mode='exact'),float)
                            if len(F3)<n: continue
                            s3,_=relax(s2,trim_to(F3,n,T3),rounds=2)
                            if back is None or s3<back: back=s3
                    tot+=1; good=back is not None and back<=s+1e-6; ok+=good
                    print('  block %d %s: %d squares at %.6f (base[%d] %.6f); row put back: %s (base %.6f) %s'%(bi,name,c,s2,c,base.get(c,0),back,s,'GREEN' if good else 'RED'),flush=True)
        print('CONTROL %d of %d returns'%(ok,tot))
    else:
        jobs=[]
        for n in a.ns:
            s,X=N[n]; Bs=blocks(X,a.minpatch)
            for bi,B in enumerate(Bs[:3]):
                mv=big_moves(B,kinds)+OS.gen_moves(B,tuple(k for k in kinds if k in ('row','col','glide','add','del')))
                if a.cap and len(mv)>a.cap: mv=rng.sample(mv,a.cap)
                jobs+=[(n,s,X,bi,m,base,a.out) for m in mv]
        lp=os.path.join(a.out,'frontier.tsv'); done=set()
        if os.path.exists(lp): done={tuple(l.split('\t')[:3]) for l in open(lp)}
        jobs=[j for j in jobs if (str(j[0]),str(j[3]),j[4][0]) not in done]       # a rerun skips what is logged
        print(len(jobs),'moves on',len(a.ns),'n',flush=True); nw=0; hist={}
        with Pool(a.jobs) as pool, open(os.path.join(a.out,'frontier.tsv'),'a') as h:
            for n,bi,name,c,s2,wins,dt in pool.imap_unordered(fjob,jobs):
                h.write('%d\t%d\t%s\t%s\t%r\t%r\t%s\t%.1f\n'%(n,bi,name,c,s2,base.get(c) if c else None,wins,dt)); h.flush()
                if c is not None: hist[c-n]=hist.get(c-n,0)+1
                if wins and isinstance(wins[0],int): nw+=1; print('WIN from n=%d %s: %d squares at %.9f, base %.9f; wins %s'%(n,name,c,s2,base[c],wins),flush=True)
        print('done: %d moves, %d with a win; count change histogram %s'%(len(jobs),nw,sorted(hist.items())))
