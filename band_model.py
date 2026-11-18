"""band lane: the band model on four corner grids, with several angle families.

It extends structure_band.py (two grids, one angle). The state is four whole-number staircases, one per corner grid:

  st[0][j]  TL grid, row j from the top,    cells from the left wall
  st[1][j]  TR grid, row j from the top,    cells from the right wall
  st[2][r]  BL grid, row r from the bottom, cells from the left wall
  st[3][r]  BR grid, row r from the bottom, cells from the right wall

A family is (phi, a0, u range, justify). Its squares stand at angle phi and sit in bands: in the frame
u = (cos phi, sin phi), v = (-sin phi, cos phi), band k is u in [a0+k, a0+k+1]. Squares in different bands of one
family never overlap, and inside a band they only need distance 1 along v, so every band has its own free slide.
With `h` or `offs` set the family has a free pitch: its bands may start at any candidate offset, at least 1 apart,
and the best set of offsets is found exactly by a one-dimensional dynamic programme.
Every upright row blocks one v interval of a band (a convex shape cut by a strip), so with the staircases fixed the
tilted fill of a family is exact: each free interval of each band holds floor(length) squares. Families are filled in
order; a later family sees the squares of the earlier ones as blocked intervals (they are placed at `just` of the slack).
"""
import math, random
import numpy as np
from structure_band import strip_ext, BIG
EPS=1e-9
TOUCH=1e-9   # a corner that only touches the edge of a band does not block it
class Fam:
    def __init__(self,L,phi_deg,a0,ulo=-BIG,uhi=BIG,just=0.5,vlo=-BIG,vhi=BIG,h=None,offs=None):
        self.L=L; self.m=int(math.floor(L+1e-9)); self.phi_deg=phi_deg; self.phi=math.radians(phi_deg); self.a0=a0; self.just=just
        c,s=math.cos(self.phi),math.sin(self.phi)
        self.R=np.array([[c,s],[-s,c]])
        corners=np.array([[0,0],[L,0],[L,L],[0,L]],float)@self.R.T
        umin,umax=corners[:,0].min(),corners[:,0].max()
        k0=math.floor(umin-a0)-1; k1=math.ceil(umax-a0)+1
        self.free=h is not None or offs is not None
        if not self.free: self.lo=a0+np.arange(k0,k1,dtype=float)
        else:
            # free pitch: candidate strips at the offsets `offs` (or on a grid of step h); fill() picks strips >= 1 apart
            u0=max(umin,ulo); u1=min(umax,uhi)-1
            if offs is None: offs=u0+np.arange(0,max(1,int(math.floor((u1-u0)/h+1e-9))+1))*h
            offs=np.unique(np.asarray(offs,float)); self.lo=offs[(offs>=u0-1e-9)&(offs<=u1+1e-9)]
            self.prev=np.searchsorted(self.lo,self.lo-1+1e-10,side='right').tolist()   # strips 0..prev[t]-1 end before strip t starts
        self.hi=self.lo+1; self.K=len(self.lo)
        def vr(uv):
            mn,mx=strip_ext(corners[None],uv-1e-9,uv+1e-9); return mn[0],mx[0]
        g1,h1=vr(self.lo); g2,h2=vr(self.hi)
        bad=(g1>=BIG/2)|(g2>=BIG/2)
        self.wlo=np.where(bad,BIG,np.maximum(g1,g2)); self.whi=np.where(bad,-BIG,np.minimum(h1,h2))
        ok=self.wlo<BIG/2
        self.wlo=np.where(ok,np.maximum(self.wlo,vlo),self.wlo); self.whi=np.where(ok,np.minimum(self.whi,vhi),self.whi)
        self.active=(self.lo>=ulo-1e-9)&(self.hi<=uhi+1e-9)
        self.memo={}
        m=self.m
        self.S=np.full((4*m+2,self.K),BIG); self.E=np.full((4*m+2,self.K),BIG)
        self.S[4*m]=-BIG; self.E[4*m]=self.wlo; self.S[4*m+1]=self.whi; self.E[4*m+1]=BIG
    def rect(self,kind,j,n):
        L=self.L
        y0=L-j-1 if kind<2 else j
        x0=0.0 if kind in (0,2) else L-n
        return np.array([[x0,y0],[x0+n,y0],[x0+n,y0+1],[x0,y0+1]],float)
    def row(self,kind,j,n):
        key=(kind,j,n); r=self.memo.get(key)
        if r is None:
            if n<=0: r=(np.full(self.K,BIG),np.full(self.K,BIG))
            else:
                mn,mx=strip_ext((self.rect(kind,j,n)@self.R.T)[None],self.lo+TOUCH,self.hi-TOUCH)
                e=mn[0]>=BIG/2
                r=(np.where(e,BIG,mn[0]),np.where(e,BIG,mx[0]))
            self.memo[key]=r
        return r
    def set_row(self,kind,j,n):
        s,e=self.row(kind,j,n); i=kind*self.m+j
        self.S[i]=s; self.E[i]=e
    def fill(self,extra=None,detail=False):
        """extra: (q,4,2) quads in (x,y) of squares placed by earlier families. returns count [, squares (x,y,rad)]"""
        S,E=self.S,self.E
        if extra is not None and len(extra):
            mn,mx=strip_ext(extra@self.R.T,self.lo+TOUCH,self.hi-TOUCH)
            e=mn>=BIG/2
            S=np.vstack([S,np.where(e,BIG,mn)]); E=np.vstack([E,np.where(e,BIG,mx)])
        o=np.argsort(S,axis=0,kind='stable')
        Ss=np.take_along_axis(S,o,0); Es=np.take_along_axis(E,o,0)
        C=np.maximum.accumulate(Es,0)
        gap=Ss[1:]-C[:-1]
        cnt=np.where((gap>0)&self.active[None,:],np.floor(gap+EPS),0.0)
        if self.free:
            # exact choice of strips at pitch >= 1: dp[t+1] = best total over strips 0..t
            wl=cnt.sum(0).tolist(); K=self.K; dp=[0.0]*(K+1); pv=self.prev
            for t in range(K):
                x=dp[t]; y=dp[pv[t]]+wl[t]
                dp[t+1]=x if x>=y else y
            tot=int(dp[K])
            if not detail: return tot
            keep=np.zeros(K,bool); t=K-1
            while t>=0:
                if dp[t+1]==dp[t]: t-=1
                else: keep[t]=True; t=pv[t]-1
            cnt=cnt*keep[None,:]
        else: tot=int(cnt.sum())
        if not detail: return tot
        out=[]; Ri=self.R.T
        for i,k in zip(*np.nonzero(cnt)):
            c=int(cnt[i,k]); slack=max(0.0,gap[i,k]-c)
            for t in range(c):
                uv=np.array([self.lo[k]+0.5, C[i,k]+self.just*slack+t+0.5])
                x,y=Ri@uv; out.append((float(x),float(y),self.phi))
        return tot,out
def quads(sq):
    """(q,4,2) corner arrays of unit squares (x,y,rad)"""
    if not len(sq): return np.zeros((0,4,2))
    A=np.array(sq,float); c=np.cos(A[:,2])/2; s=np.sin(A[:,2])/2
    dx=np.stack([c-s,-c-s,-c+s,c+s],1); dy=np.stack([s+c,-s+c,-s-c,s-c],1)
    return np.stack([A[:,0:1]+dx,A[:,1:2]+dy],2)
class Model:
    def __init__(self,L,fams):
        """fams: list of dicts phi,a0[,ulo,uhi,vlo,vhi,just,h,offs]; h or offs sets a free pitch (see Fam); a u or v range keeps the family inside a window of its own frame"""
        self.L=L; self.m=int(math.floor(L+1e-9))
        self.fams=[Fam(L,f['phi'],f['a0'],f.get('ulo',-BIG),f.get('uhi',BIG),f.get('just',0.5),f.get('vlo',-BIG),f.get('vhi',BIG),f.get('h'),f.get('offs')) for f in fams]
        self.st=np.zeros((4,self.m),int)
    def load(self,st):
        st=np.array(st,int)
        for kind in range(4):
            for j in range(self.m):
                self.st[kind,j]=st[kind,j]
                for F in self.fams: F.set_row(kind,j,int(st[kind,j]))
    def set(self,kind,j,n):
        self.st[kind,j]=n
        for F in self.fams: F.set_row(kind,j,int(n))
    def feasible(self,st=None):
        st=self.st if st is None else st
        m=self.m; a,c,d,e=st
        if ((a+c)>m).any() or ((d+e)>m).any(): return False
        dr=d[::-1]; er=e[::-1]
        if ((a>0)&(dr>0)).any() or ((c>0)&(er>0)).any() or ((a+er)>m).any() or ((c+dr)>m).any(): return False
        a2=a[1:]; c2=c[1:]; dr=dr[:-1]; er=er[:-1]
        if ((a2>0)&(dr>0)).any() or ((c2>0)&(er>0)).any() or ((a2+er)>m).any() or ((c2+dr)>m).any(): return False
        return True
    def count(self,detail=False):
        tot=int(self.st.sum())
        if len(self.fams)==1 and not detail: return tot+self.fams[0].fill()
        placed=[]; ntil=[]
        for F in self.fams:
            c,sq=F.fill(quads(placed) if placed else None,True)
            placed+=sq; tot+=c; ntil.append(c)
        return (tot,placed,ntil) if detail else tot
    def squares(self):
        """explicit layout (x,y,rad)"""
        L=self.L; out=[]
        a,c,d,e=self.st
        for j in range(self.m):
            out+=[(i+0.5,L-j-0.5,0.0) for i in range(a[j])]+[(L-i-0.5,L-j-0.5,0.0) for i in range(c[j])]
            out+=[(i+0.5,j+0.5,0.0) for i in range(d[j])]+[(L-i-0.5,j+0.5,0.0) for i in range(e[j])]
        tot,placed,_=self.count(True)
        return out+placed
    def anneal(self,steps,T0=0.6,T1=0.05,seed=0,stop_at=None):
        rng=random.Random(seed); m=self.m
        cur=self.count(); best=(cur,self.st.copy())
        for it in range(steps):
            T=T0*(T1/T0)**(it/max(1,steps-1))
            kind=rng.randrange(4); j=rng.randrange(m); d=rng.choice((-1,1))
            span=1 if rng.random()<0.7 else rng.randint(2,4)
            idx=range(j,min(m,j+span))
            old=[int(self.st[kind,i]) for i in idx]
            if any(o+d<0 or o+d>m for o in old): continue
            for i,o in zip(idx,old): self.st[kind,i]=o+d
            if not self.feasible():
                for i,o in zip(idx,old): self.st[kind,i]=o
                continue
            for i,o in zip(idx,old): self.set(kind,i,o+d)
            new=self.count()
            if new>=cur or rng.random()<math.exp((new-cur)/T):
                cur=new
                if cur>best[0]:
                    best=(cur,self.st.copy())
                    if stop_at is not None and cur>=stop_at: break
            else:
                for i,o in zip(idx,old): self.set(kind,i,o)
        self.load(best[1])
        return best[0]
def clip_x(Q,y0,y1):
    """x extent (min,max) of the convex quads Q (q,4,2) inside the row y in (y0,y1); None when no quad enters it"""
    if not len(Q): return None
    P=Q[:,:,::-1]   # (y,x) so strip_ext cuts along y
    mn,mx=strip_ext(P,np.array([y0+1e-7]),np.array([y1-1e-7]))
    mn=mn[:,0]; mx=mx[:,0]; ok=(mn<BIG/2)&(mx-mn>1e-7)
    if not ok.any(): return None
    return float(mn[ok].min()),float(mx[ok].max())
def stairs_from_holes(L,sq,JL,JR,shrink=0.0):
    """staircases around the tilted squares sq (x,y,rad): top rows above the switches JL (left) and JR (right),
    bottom rows below them; every row runs from its wall to the first tilted square. Trimmed to a feasible state."""
    m=int(math.floor(L+1e-9)); st=np.zeros((4,m),int)
    Q=quads(sq)
    if shrink and len(Q):
        ctr=Q.mean(1,keepdims=True); Q=ctr+(Q-ctr)*(1-shrink)
    for j in range(m):
        ex=clip_x(Q,L-j-1,L-j)
        if j<JL: st[0,j]=m if ex is None else max(0,min(m,int(math.floor(ex[0]+1e-9))))
        if j<JR and not (ex is None and j<JL): st[1,j]=m if ex is None else max(0,min(m,int(math.floor(L-ex[1]+1e-9))))
        ex=clip_x(Q,j,j+1)
        if j<m-JL: st[2,j]=m if ex is None else max(0,min(m,int(math.floor(ex[0]+1e-9))))
        if j<m-JR and not (ex is None and j<m-JL): st[3,j]=m if ex is None else max(0,min(m,int(math.floor(L-ex[1]+1e-9))))
    return trim(st,m)
def trim(st,m):
    a,c,d,e=st
    for j in range(m):
        if a[j]+c[j]>m: c[j]=m-a[j]
        if d[j]+e[j]>m: e[j]=m-d[j]
    for j in range(m):
        for r in (m-j-1,m-j):
            if not 0<=r<m: continue
            if a[j]>0 and d[r]>0: d[r]=0
            if c[j]>0 and e[r]>0: e[r]=0
            if a[j]+e[r]>m: e[r]=m-a[j]
            if c[j]+d[r]>m: c[j]=m-d[r]
    return st
class Cells:
    """The same exact count with free uprights: any set of cells of the four corner grids (grid g = 0 TL, 1 TR, 2 BL,
    3 BR; cell (g, j, i) is row j from the grid's own wall, cell i along the row), not only rows that start at a wall.
    One family at a fixed pitch. A move adds or removes one cell; only the bands that the cell crosses are recounted."""
    def __init__(self,L,phi,a0):
        self.L=L; m=self.m=int(math.floor(L+1e-9)); self.F=F=Fam(L,phi,a0)
        g,j,i=np.meshgrid(np.arange(4),np.arange(m),np.arange(m),indexing='ij'); g=g.ravel(); j=j.ravel(); i=i.ravel()
        y0=np.where(g<2,L-j-1,j).astype(float); x0=np.where((g==0)|(g==2),i,L-i-1).astype(float)
        self.x0=x0; self.y0=y0; self.N=len(g)
        Q=np.stack([np.stack([x0,y0],1),np.stack([x0+1,y0],1),np.stack([x0+1,y0+1],1),np.stack([x0,y0+1],1)],1)
        mn,mx=strip_ext(Q@F.R.T,F.lo+TOUCH,F.hi-TOUCH)
        self.cb=[[(int(k),float(mn[c,k]),float(mx[c,k])) for k in np.nonzero(mn[c]<BIG/2)[0]] for c in range(self.N)]
        # cells of other grids that overlap a cell
        self.conf=[[] for _ in range(self.N)]
        order=np.argsort(x0); xs=x0[order]
        for c in range(self.N):
            a=np.searchsorted(xs,x0[c]-1+1e-9); b=np.searchsorted(xs,x0[c]+1-1e-9)
            for d in order[a:b]:
                if d!=c and abs(y0[d]-y0[c])<1-1e-9: self.conf[c].append(int(d))
        self.occ=np.zeros(self.N,bool); self.blk=[dict() for _ in range(F.K)]
        self.wlo=F.wlo.tolist(); self.whi=F.whi.tolist(); self.bc=[self.band(k) for k in range(F.K)]
    def cid(self,g,j,i): return (g*self.m+j)*self.m+i
    def band(self,k,detail=False):
        lo=self.wlo[k]; hi=self.whi[k]
        if lo>=hi: return (0,[]) if detail else 0
        iv=sorted(self.blk[k].values()); tot=0; cur=lo; out=[]
        for s,e in iv:
            if s>cur:
                g=min(s,hi)-cur
                if g>=1-EPS:
                    c=int(g+EPS); tot+=c
                    if detail: out.append((cur,g,c))
            if e>cur: cur=e
            if cur>=hi: break
        if cur<hi:
            g=hi-cur
            if g>=1-EPS:
                c=int(g+EPS); tot+=c
                if detail: out.append((cur,g,c))
        return (tot,out) if detail else tot
    def toggle(self,c):
        """flip cell c and return the change of the total count"""
        on=not self.occ[c]; self.occ[c]=on; d=1 if on else -1
        for k,s,e in self.cb[c]:
            if on: self.blk[k][c]=(s,e)
            else: del self.blk[k][c]
            n=self.band(k); d+=n-self.bc[k]; self.bc[k]=n
        return d
    def load(self,cells):
        for c in np.nonzero(self.occ)[0]: self.toggle(int(c))
        for c in cells:
            if not self.occ[c] and not any(self.occ[d] for d in self.conf[c]): self.toggle(int(c))
    def count(self): return int(self.occ.sum())+sum(self.bc)
    def squares(self,just=0.5):
        out=[(float(self.x0[c]+0.5),float(self.y0[c]+0.5),0.0) for c in np.nonzero(self.occ)[0]]
        F=self.F; Ri=F.R.T
        for k in range(F.K):
            for cur,g,c in self.band(k,True)[1]:
                for t in range(c):
                    x,y=Ri@np.array([F.lo[k]+0.5,cur+just*max(0.0,g-c)+t+0.5]); out.append((float(x),float(y),F.phi))
        return out
    def frontier(self,reach=2.5):
        """cells within `reach` of a tilted square or of an empty place: the only cells worth a move"""
        sq=self.squares(); T=np.array([(x,y) for x,y,t in sq if t!=0.0]).reshape(-1,2)
        cx=self.x0+0.5; cy=self.y0+0.5; near=np.zeros(self.N,bool)
        for x,y in T: near|=(np.abs(cx-x)<reach)&(np.abs(cy-y)<reach)
        return np.nonzero(near)[0]
    def anneal(self,steps,T0=0.6,T1=0.05,seed=0,stop_at=None,refresh=4000):
        rng=random.Random(seed); cur=self.count(); best=(cur,self.occ.copy()); pool=None
        for it in range(steps):
            if it%refresh==0:
                pool=self.frontier().tolist()
                if not pool: pool=list(range(self.N))
            T=T0*(T1/T0)**(it/max(1,steps-1))
            c=pool[rng.randrange(len(pool))]
            if self.occ[c]: flips=[c]
            else:
                ev=[d for d in self.conf[c] if self.occ[d]]
                if ev and rng.random()<0.5: continue
                flips=ev+[c]
            d=0
            for x in flips: d+=self.toggle(x)
            if d>=0 or rng.random()<math.exp(d/T):
                cur+=d
                if cur>best[0]:
                    best=(cur,self.occ.copy())
                    if stop_at is not None and cur>=stop_at: break
            else:
                for x in reversed(flips): self.toggle(x)
        self.load(np.nonzero(best[1])[0])
        return best[0]
def cells_from_uprights(C,up,tol=0.3):
    """nearest cell of the nearest corner grid for every upright square (x,y,_) of a held layout"""
    L=C.L; out=[]
    for x,y,_ in up:
        rl=(x-0.5)-round(x-0.5); rr=(L-x-0.5)-round(L-x-0.5); rb=(y-0.5)-round(y-0.5); rt=(L-y-0.5)-round(L-y-0.5)
        left=abs(rl)<=abs(rr); bot=abs(rb)<=abs(rt)
        i=int(round(x-0.5)) if left else int(round(L-x-0.5)); j=int(round(y-0.5)) if bot else int(round(L-y-0.5))
        if 0<=i<C.m and 0<=j<C.m and min(abs(rl),abs(rr))<tol and min(abs(rb),abs(rt))<tol: out.append(C.cid((2 if bot else 0)+(0 if left else 1),j,i))
    return out
