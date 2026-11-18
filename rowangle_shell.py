#!/usr/bin/env python3
"""rowangle: cross-shell graft scan. A donor d held at side m_d + f gives a start for a target n in a neighbouring
shell at side m + f: its tilted squares keep their offset to the nearest corner (per patch, or per square), and the
uprights are refilled exactly (Evan Daniel's fillfast, MIT, imported from his clone). Removing a shell (m_d = m + 1)
is the "collapse" step, adding one (m_d = m - 1) the "expand" step. A count >= n at a side below ours is a hit: the
extra squares are dropped, fq quenches it and floatsafe certifies it.

  rowangle_shell.py OUTDIR [--jobs 3] [--ns a,b] [--slack 3] [--shells 1]
"""
import argparse, csv, json, math, os, sys, time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from engine_lib import *
from engine_patch import corners, cluster, feasible, anchor_shrink
from engine_graft import anchor
import fillfast
P=None; LS={}; N={}
def init():
    global P
    P=load()
    for n in P: LS[n]=normalize(P[n])[0]
def norm(n):
    if n not in N:
        s,A=normalize(P[n]); T=A[np.abs(A[:,2])>0.5]; N[n]=(s,T,cluster(T) if len(T) else [])
    return N[n]
def starts(d,s):
    """every patch keeps its place, or moves by the change of side, in x and in y: 4 choices per patch (the 3 largest
    patches; smaller ones follow their nearest corner)"""
    import itertools
    sd,T,groups=norm(d)
    if not len(T): return
    base=anchor(T,groups,sd,s); big=sorted(groups,key=len,reverse=True)[:3]
    for combo in itertools.product(((0,0),(1,0),(0,1),(1,1)),repeat=len(big)):
        T2=base.copy()
        for g,(mx,my) in zip(big,combo):
            T2[g,0]=T[g,0]+mx*(s-sd); T2[g,1]=T[g,1]+my*(s-sd)
        yield ''.join('%d%d'%c for c in combo),T2
def job(a):
    n,ds,out=a; Ln=LS[n]; best=(0,None,None,None); hit=None; fills=0
    for d in ds:
        s=LS[d]+(int(Ln)-int(LS[d]))
        for how,T2 in starts(d,s):
            if not feasible(T2,s,None): continue
            fills+=1; F=fillfast.fill(s,T2,'greedy'); c=len(F)
            if c>=n-1:
                F=fillfast.fill(s,T2,'exact'); c=len(F)
            if c>best[0]: best=(c,d,how,s)
            if c>=n and (hit is None or s<hit[0]): hit=(s,d,how,F)
    res=None
    if hit:
        from engine_polish import certify
        from engine_fq import quench, POLISH
        s,d,how,F=hit
        up=np.nonzero(np.abs(F[:,2])<=0.5)[0]; F=np.delete(F,up[:len(F)-n],axis=0)   # drop the extra uprights
        X=F; cur=s
        for fl in ((),POLISH):
            s2,X2,dt=quench(cur,X,fl)
            if s2 is not None and s2<cur: cur,X=s2,X2
        L,fr=certify(n,X)
        if L is None: L,fr=certify(n,F)
        if L is not None and L<Ln-1e-9:
            with open(os.path.join(out,'%d.csv'%n),'w',newline='') as h:
                w=csv.writer(h); w.writerow(['n','square_id','x','y','angle'])
                for r in fr: w.writerow([r['n'],r['square_id'],r['x'],r['y'],r['angle']])
            res=(L,d,how)
    return n,Ln,best,fills,res
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--jobs',type=int,default=3); ap.add_argument('--ns'); ap.add_argument('--slack',type=int,default=3); ap.add_argument('--shells',type=int,default=1)
    a=ap.parse_args(); os.makedirs(a.out,exist_ok=True); init()
    ns=[int(x) for x in a.ns.split(',')] if a.ns else range(30,1001)
    jobs=[]
    for n in ns:
        m=int(LS[n]); ds=[]
        for d in P:
            md=int(LS[d]); k=m-md
            if k==0 or abs(k)>a.shells: continue
            if LS[d]+k>=LS[n]-1e-7: continue
            est=d+sum((2*(md+i)+1) for i in range(k)) if k>0 else d-sum((2*(md-i)-1) for i in range(-k))
            if est+a.slack>=n and est-3*a.slack<=n: ds.append(d)
        if ds: jobs.append((n,ds,a.out))
    print('targets',len(jobs),'fills <=',2*sum(len(j[1]) for j in jobs),flush=True)
    from multiprocessing import Pool
    t0=time.time(); wins=0; tot=0.0; nf=0
    with Pool(a.jobs,initializer=init) as pool, open(os.path.join(a.out,'shell.tsv'),'w') as h:
        h.write('n\tours\tbest_count\tdonor\tanchor\tside\tcertified\n')
        for n,Ln,best,fills,res in pool.imap_unordered(job,jobs):
            nf+=fills
            h.write('%d\t%r\t%s\t%s\t%s\t%s\t%s\n'%(n,Ln,best[0],best[1],best[2],best[3],res[0] if res else '')); h.flush()
            if res:
                g=(Ln-res[0])/math.sqrt(n); tot+=g; wins+=1
                print('WIN n=%d %.9f -> %.9f donor %d (%s) gain %.3e total %.3e'%(n,Ln,res[0],res[1],res[2],g,tot),flush=True)
    print(json.dumps(dict(targets=len(jobs),fills=nf,wins=wins,total_gain=tot,secs=round(time.time()-t0))))
