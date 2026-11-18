#!/usr/bin/env python3
"""outline avenue: search over the outline of one tilted block.

The state is a whole packing. Its largest tilted patch is the block; its squares get lattice coordinates (i, j) by
following neighbours (outline_lib.label), so slips in both directions are kept. A move changes which lattice sites
the block holds: it adds, removes or shifts squares at the edge. Each new state is scored by a side, never a count:
the uprights are refilled exactly around the new tilted squares (at the present side, or the smallest inflated side
of a short ladder where the refill reaches n), and fq then quenches all squares.

  outline_search.py ctl OUT [--jobs 3] [--gens 6]       # control: quenched 8 x 13 at 16.68438 -> held 16.67878
  outline_search.py run N OUT [--jobs 3] [--gens 4] [--moves row,col,glide,add,del] [--cap 120] [--from FILE]

Moves (all keep n; the refill settles the uprights):
  row / col   shift one row (column) of the block by one site: its square at one end goes to the other end
  glide       shift every row (column) on one side of a cut by one site: a step in the outline
  add         one more tilted square at an empty site beside the block
  del         one edge square leaves the block
Tabu walk: every generation scores all moves of the present state, moves to the best outline not yet visited, and
keeps the smallest side seen. A side counts only after floatsafe certifies it.
"""
import sys, os, math, json, time, argparse, pickle, random
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from outline_lib import *
from band_cert import certify
LADDER=(0.0,0.002,0.005,0.01,0.016,0.024,0.035,0.05)

def block_of(X,tilt=5.0):
    """indices (into X) of the largest tilted patch, its angle, its outline {(i,j): index into X}, mean row and column vectors"""
    idx=np.where(tilted_mask(X,tilt))[0]
    if len(idx)==0: return None
    T=X[idx]; g=patches(T)[0]; gi=idx[g]; th,cells,Q=label(X[gi])
    cells={c:int(gi[k]) for c,k in cells.items()}
    U=[];V=[]
    for (i,j),a in cells.items():
        b=cells.get((i+1,j));  c=cells.get((i,j+1))
        if b is not None: U.append(X[b,:2]-X[a,:2])
        if c is not None: V.append(X[c,:2]-X[a,:2])
    r=math.radians(th); U=np.mean(U,0) if U else np.array([math.cos(r),math.sin(r)]); V=np.mean(V,0) if V else np.array([-math.sin(r),math.cos(r)])
    return dict(theta=th,cells=cells,U=U,V=V,other=[int(k) for k in idx if k not in set(gi.tolist())])
def site_pos(B,X,site):
    """where a new square at an empty site would stand: the mean of what its occupied neighbours say"""
    i,j=site; c=B['cells']; p=[]
    for (di,dj,vec) in ((1,0,-B['U']),(-1,0,B['U']),(0,1,-B['V']),(0,-1,B['V'])):
        a=c.get((i+di,j+dj))
        if a is not None: p.append(X[a,:2]+vec)
    return np.mean(p,0) if p else None
def gen_moves(B,kinds):
    """-> list of (name, remove sites, add sites)"""
    c=B['cells']; out=[]; rows={}; cols={}
    for (i,j) in c: rows.setdefault(j,[]).append(i); cols.setdefault(i,[]).append(j)
    J=sorted(rows); I=sorted(cols)
    if 'row' in kinds:
        for j in J:
            lo,hi=min(rows[j]),max(rows[j])
            out.append(('row%+d@%d'%(1,j),[(lo,j)],[(hi+1,j)])); out.append(('row%+d@%d'%(-1,j),[(hi,j)],[(lo-1,j)]))
    if 'col' in kinds:
        for i in I:
            lo,hi=min(cols[i]),max(cols[i])
            out.append(('col%+d@%d'%(1,i),[(i,lo)],[(i,hi+1)])); out.append(('col%+d@%d'%(-1,i),[(i,hi)],[(i,lo-1)]))
    if 'glide' in kinds:
        for j0 in J[1:]:
            for d in (1,-1):
                rem=[];add=[]
                for j in J:
                    if j<j0: continue
                    lo,hi=min(rows[j]),max(rows[j])
                    if d>0: rem.append((lo,j)); add.append((hi+1,j))
                    else: rem.append((hi,j)); add.append((lo-1,j))
                out.append(('glideR%+d@%d'%(d,j0),rem,add))
        for i0 in I[1:]:
            for d in (1,-1):
                rem=[];add=[]
                for i in I:
                    if i<i0: continue
                    lo,hi=min(cols[i]),max(cols[i])
                    if d>0: rem.append((i,lo)); add.append((i,hi+1))
                    else: rem.append((i,hi)); add.append((i,lo-1))
                out.append(('glideC%+d@%d'%(d,i0),rem,add))
    ends=set()
    for j in J: ends.add((min(rows[j]),j)); ends.add((max(rows[j]),j))
    for i in I: ends.add((i,min(cols[i]))); ends.add((i,max(cols[i])))
    if 'del' in kinds:
        for s in sorted(ends): out.append(('del@%d,%d'%s,[s],[]))
    if 'add' in kinds:
        emp=set()
        for (i,j) in ends:
            for d in ((1,0),(-1,0),(0,1),(0,-1)):
                s=(i+d[0],j+d[1])
                if s not in c: emp.add(s)
        for s in sorted(emp): out.append(('add@%d,%d'%s,[],[s]))
    return out
def sig(cells):
    I=min(c[0] for c in cells); J=min(c[1] for c in cells)
    return tuple(sorted((i-I,j-J) for i,j in cells))
def apply_move(s,X,B,rem,add):
    """new tilted set (array x,y,deg), or None when a new square leaves the box"""
    c=B['cells']; drop={c[r] for r in rem if r in c}
    keep=[k for k in list(c.values())+B['other'] if k not in drop]
    T=[X[k] for k in keep]; ang=float(np.median([X[k,2] for k in c.values()]))
    B2=dict(B); B2['cells']={k:v for k,v in c.items() if v not in drop}
    new=[]
    for a in add:
        # an added site may lean on sites added before it in the same move (a glide adds one per row)
        p=site_pos(B2,X,a)
        if p is None: return None
        h=hw(math.radians(ang))
        if p[0]-h<-1e-9 or p[1]-h<-1e-9 or p[0]+h>s+1e-9 or p[1]+h>s+1e-9: return None
        new.append([p[0],p[1],ang])
    return np.array(T+new,float).reshape(-1,3)
def score(s,T,n,ladder=LADDER,rounds=2):
    """refill at the first rung of the ladder that reaches n, then fq. -> (side or None, X, rung)"""
    for d in ladder:
        T2=T.copy(); T2[:,:2]+=d/2
        F=refill(s+d,T2,n)
        if F is None: continue
        s2,X2=relax(s+d,trim_to(F,n,T2),rounds=rounds)
        return s2,X2,d
    return None,None,None
def _job(a):
    s,X,B,mv,n=a; name,rem,add=mv; t=time.time()
    try:
        T=apply_move(s,X,B,rem,add)
        if T is None: return name,None,None,None,0.0
        s2,X2,d=score(s,T,n)
        return name,s2,X2,d,time.time()-t
    except Exception as e:
        return name,None,None,repr(e),time.time()-t
def walk(n,s0,X0,out,jobs=3,gens=6,kinds=('row','col','glide','add','del'),cap=0,target=None,seed=0,log=print):
    from multiprocessing import Pool
    os.makedirs(out,exist_ok=True); rng=random.Random(seed)
    cur_s,cur_X=s0,X0; best_s,best_X=s0,X0; seen=set(); hist=[]
    B=block_of(cur_X); seen.add(sig(B['cells']))
    log('start n=%d side %.9f block %d squares at %.3f deg'%(n,s0,len(B['cells']),B['theta']))
    with Pool(jobs) as pool, open(os.path.join(out,'moves-%d.tsv'%n),'a') as h:
        for g in range(gens):
            B=block_of(cur_X); mv=gen_moves(B,kinds)
            if cap and len(mv)>cap: mv=rng.sample(mv,cap)
            res=[]; t=time.time()
            for name,s2,X2,d,dt in pool.imap_unordered(_job,[(cur_s,cur_X,B,m,n) for m in mv]):
                h.write('%d\t%d\t%s\t%r\t%r\t%r\t%.1f\n'%(n,g,name,cur_s,s2,d,dt)); h.flush()
                if s2 is not None: res.append((s2,name,X2))
            res.sort(key=lambda r:r[0]); nxt=None
            for s2,name,X2 in res:
                B2=block_of(X2)
                if B2 is None: continue
                sg=sig(B2['cells'])
                if sg in seen: continue
                nxt=(s2,name,X2,sg); break
            nb=sum(1 for r in res if r[0]<cur_s-1e-7)
            log('gen %d: %d moves, %d scored, %d below the present side, best %s, %.0fs'%(g,len(mv),len(res),nb,('%.9f %s'%(res[0][0],res[0][1])) if res else '-',time.time()-t))
            for s2,name,X2 in res:
                if s2<best_s-1e-9: best_s,best_X=s2,X2
                break
            if nxt is None: log('no unvisited outline left'); break
            cur_s,cur_X=nxt[0],nxt[2]; seen.add(nxt[3]); hist.append((g,nxt[1],nxt[0]))
            B2=block_of(cur_X); log('  go to %s at %.9f (%d squares, %.3f deg)\n%s'%(nxt[1],cur_s,len(B2['cells']),B2['theta'],show(B2['cells'])))
            pickle.dump((best_s,best_X,hist),open(os.path.join(out,'best-%d.pkl'%n),'wb'))
            if target is not None and best_s<=target+1e-6: log('target reached'); break
    return best_s,best_X,hist
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('args',nargs='*'); ap.add_argument('--jobs',type=int,default=3); ap.add_argument('--gens',type=int,default=6)
    ap.add_argument('--moves',default='row,col,glide,add,del'); ap.add_argument('--cap',type=int,default=0); ap.add_argument('--from',dest='src'); ap.add_argument('--seed',type=int,default=0)
    a=ap.parse_args(); kinds=tuple(a.moves.split(','))
    if a.cmd=='ctl':
        import band_shear
        out=a.args[0]; r=band_shear.run(16,5,0.6925,8,13); held=normalize(load(os.environ['SQ_BEST'])[261])[0]
        print('control: quenched 8 x 13 at %.9f, held %.9f'%(r['side'],held),flush=True)
        s,X,hist=walk(261,r['side'],r['X'],out,a.jobs,a.gens,kinds,a.cap,target=held,seed=a.seed)
        print('CONTROL %s: best %.9f, held %.9f, path %s'%('GREEN' if s<=held+1e-6 else 'RED',s,held,hist))
    elif a.cmd=='run':
        n=int(a.args[0]); out=a.args[1]
        if a.src: s0,X0=read_txt(a.src)
        else: s0,X0=normalize(load(os.environ['SQ_BEST'])[n])
        s,X,hist=walk(n,s0,X0,out,a.jobs,a.gens,kinds,a.cap,seed=a.seed)
        print('n=%d start %.9f best %.9f path %s'%(n,s0,s,hist))
        if s<s0-1e-9:
            L,fr=certify(n,X)
            print('certified',L)
            if L is not None and L<s0-1e-9:
                import csv
                with open(os.path.join(out,'%d.csv'%n),'w',newline='') as hh:
                    w=csv.writer(hh); w.writerow(['n','square_id','x','y','angle'])
                    for q in fr: w.writerow([q['n'],q['square_id'],q['x'],q['y'],q['angle']])
