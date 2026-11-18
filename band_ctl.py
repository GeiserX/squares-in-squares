"""band lane: the go line. Rebuild a held layout with the four-grid band model.

  band_ctl.py N [--steps 60000] [--seeds 3] [--fams 1] [--dl 0.0] [--cells] [--events] [--h STEP] [--out FILE]

It reads the held layout of N, takes the angle families from its tilted squares (the largest clusters), reads the
four staircases off its uprights, and prints the model count with the held staircases and after annealing, at the held
side plus --dl. With --out it writes the best layout as `n s` / `x y deg` text.
"""
import sys, os, math, argparse, time, collections
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from structure_lib import load, bbox, norm
from band_model import Model, stairs_from_holes, trim, BIG
BEST=os.environ.get('SQ_BEST','$SCRATCH/bounties-squares/gather/engine-2026-11-10a.csv')
def held(n,P=None):
    P=P or load(BEST); sq=P[n]; x0,y0,x1,y1=bbox(sq); L=max(x1-x0,y1-y0)
    up=[]; til=[]
    for x,y,a in sq:
        na=norm(a)
        (til if abs(na)>0.5 else up).append((x-x0,y-y0,math.radians(na)))
    return L,up,til
def stairs_from_uprights(L,up):
    m=int(math.floor(L+1e-9)); cells=[set() for _ in range(4)]
    for x,y,_ in up:
        rl=(x-0.5)-round(x-0.5); rr=(L-x-0.5)-round(L-x-0.5); rb=(y-0.5)-round(y-0.5); rt=(L-y-0.5)-round(L-y-0.5)
        left=abs(rl)<=abs(rr); bot=abs(rb)<=abs(rt)
        i=int(round(x-0.5)) if left else int(round(L-x-0.5)); j=int(round(y-0.5)) if bot else int(round(L-y-0.5))
        cells[(2 if bot else 0)+(0 if left else 1)].add((j,i))
    st=np.zeros((4,m),int)
    for k in range(4):
        for j in range(m):
            c=0
            while (j,c) in cells[k]: c+=1
            st[k,j]=c
    return trim(st,m),len(up)-int(st.sum())
def clusters(til,nf,width=1.5):
    """largest angle clusters of the tilted squares -> list of (phi_deg, members)"""
    left=list(til); out=[]
    while left and len(out)<nf:
        d=np.array([math.degrees(t[2]) for t in left])
        best=max(d,key=lambda c:(np.abs(d-c)<width).sum())
        sel=np.abs(d-best)<width
        out.append((float(np.median(d[sel])),[t for t,s in zip(left,sel) if s]))
        left=[t for t,s in zip(left,sel) if not s]
    return out
def fam_of(phi,mem,turn,pad=0.3):
    """family whose bands fit the held squares: a0 from the circular mean of their u offsets"""
    p=phi+(90 if turn else 0); t=math.radians(p)
    u=np.array([x*math.cos(t)+y*math.sin(t) for x,y,_ in mem])-0.5
    ang=np.angle(np.exp(2j*np.pi*u).mean())/(2*np.pi)
    v=np.array([-x*math.sin(t)+y*math.cos(t) for x,y,_ in mem])
    return dict(phi=p,a0=float(ang%1.0),ulo=float(u.min())-0.5-pad,uhi=float(u.max())+1.5+pad,vlo=float(v.min())-0.5-pad,vhi=float(v.max())+0.5+pad)
def event_offsets(L,st,phi,reach=16):
    """offsets at which an edge of a band passes through the end corner of a staircase row, plus whole steps from them
    (a band can always be pushed until it meets a corner or a neighbour band)"""
    m=st.shape[1]; t=math.radians(phi); c,s=math.cos(t),math.sin(t); us=[]
    for kind in range(4):
        for j in range(m):
            n=int(st[kind,j])
            if n<=0: continue
            x=n if kind in (0,2) else L-n
            for y in ((L-j-1,L-j) if kind<2 else (j,j+1)): us.append(x*c+y*s)
    us=np.array(us); k=np.arange(-reach,reach+1)
    return np.unique(np.round((us[:,None]+k[None,:]).ravel(),12))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('n',type=int); ap.add_argument('--steps',type=int,default=60000); ap.add_argument('--seeds',type=int,default=3)
    ap.add_argument('--fams',type=int,default=1); ap.add_argument('--dl',type=float,default=0.0); ap.add_argument('--out'); ap.add_argument('--h',type=float,help='free pitch on a grid of this step'); ap.add_argument('--cells',action='store_true',help='free cells on the four grids (band_model.Cells) in place of staircases'); ap.add_argument('--events',action='store_true',help='free pitch at the offsets where a band edge meets a corner of a held staircase')
    a=ap.parse_args(); n=a.n
    L0,up,til=held(n); L=L0+a.dl; m=int(L)
    cl=clusters(til,a.fams)
    print('n',n,'held side',L0,'model side',L,'uprights',len(up),'tilted',len(til),'clusters',[(round(p,2),len(mm)) for p,mm in cl],flush=True)
    if a.cells:
        from band_model import Cells, cells_from_uprights
        best=None
        for turn in (0,1):
            f=fam_of(cl[0][0],cl[0][1],turn)
            for da in np.arange(0,1,0.05):
                C=Cells(L+1e-9,f['phi'],(f['a0']+da)%1.0); C.load(cells_from_uprights(C,up)); c=C.count()
                if best is None or c>best[0]: best=(c,f['phi'],(f['a0']+da)%1.0,int(C.occ.sum()))
        c0,phi,a0,kept=best; top=c0
        print('held cells: uprights kept',kept,'of',len(up),'| model count',c0,'of',n,'| family',(round(phi,2),round(a0,3)),flush=True)
        for seed in range(a.seeds):
            C=Cells(L+1e-9,phi,a0); C.load(cells_from_uprights(C,up)); t=time.time()
            c=C.anneal(a.steps,T0=0.25,seed=seed,stop_at=n); top=max(top,c); print('  anneal seed',seed,'->',c,'%.0fs'%(time.time()-t),flush=True)
        print('RESULT n',n,'side',L,'held cells',c0,'annealed',top,'held',n,'GO' if top>=n else 'short by %d'%(n-top))
        sys.exit()
    st0,dropped=stairs_from_uprights(L0,up)
    best=None
    for turns in range(2**len(cl)):
        fams=[fam_of(p,mm,(turns>>i)&1) for i,(p,mm) in enumerate(cl)][::-1]   # small windows first, the main family last
        for k in ('ulo','uhi','vlo','vhi'):
            if not ((a.h or a.events) and k in ('ulo','uhi')): fams[-1].pop(k)
        if a.h:
            for f in fams: f['h']=a.h; f['ulo']-=0.5; f['uhi']+=0.5
        if a.events:
            for f in fams: f['offs']=event_offsets(L,st0,f['phi']); f['ulo']-=0.5; f['uhi']+=0.5
        for da in (np.arange(0,1,0.05) if not (a.h or a.events) else (0.0,)):
            ff=[dict(f) for f in fams]; ff[-1]['a0']=(ff[-1]['a0']+da)%1.0
            M=Model(L,ff); M.load(st0)
            c=M.count()
            if best is None or c>best[0]: best=(c,ff,M.feasible())
    c0,fams,feas=best
    print('held staircases: uprights kept',int(st0.sum()),'dropped',dropped,'feasible',feas,'| model count',c0,'of',n,'| families',[(round(f['phi'],2),round(f['a0'],3)) for f in fams],flush=True)
    res=[]
    for seed in range(a.seeds):
        M=Model(L,fams); M.load(st0); t=time.time()
        c=M.anneal(a.steps,seed=seed,stop_at=n)
        res.append((c,seed,M.st.copy())); print('  anneal seed',seed,'->',c,'%.0fs'%(time.time()-t),flush=True)
    c,seed,st=max(res,key=lambda r:r[0])
    M=Model(L,fams); M.load(st); sq=M.squares()
    T=np.array([(x,y,math.degrees(t)) for x,y,t in sq if abs(t)>1e-9])
    from structure_slot import fillfast
    full=fillfast.fill(L,T,mode='exact'); cr=len(full)
    if cr>c: sq=[(x,y,math.radians(d)) for x,y,d in full]
    c2=max(c,cr)
    print('RESULT n',n,'side',L,'held staircases',c0,'annealed',c,'with the exact four-grid refill',cr,'held',n,'GO' if c2>=n else 'short by %d'%(n-c2))
    if a.out:
        with open(a.out,'w') as h:
            h.write('%d %r\n'%(len(sq),L))
            for x,y,t in sq: h.write('%r %r %r\n'%(x,y,math.degrees(t)))
