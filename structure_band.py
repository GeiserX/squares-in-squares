"""structure lane: band model of a tilted channel between two corner grids.

Class: uprights are rows of the top-left grid (row j from the top holds a[j] cells from the left wall) and rows of the
bottom-right grid (row r from the bottom holds b[r] cells from the right wall). Every tilted square has one angle phi
and sits in a band: in the frame u=(cos phi, sin phi), v=(-sin phi, cos phi) band k is u in [a0+k, a0+k+1]. Bands tile
the plane, so tilted squares in different bands never overlap, and inside a band they only need distance 1 along v.
Given the two staircases the best tilted fill is therefore exact and separable: band k holds floor(hi_k - lo_k)
squares, hi_k = lowest v of the top-left rows inside the band, lo_k = highest v of the bottom-right rows (walls too).
The search is over the integer staircases only (simulated annealing), which moves whole rows of tilted squares at once.
"""
import math, sys, time, json, random
import numpy as np
BIG=1e18
def strip_ext(P, lo, hi):
    """P (q,4,2) convex quads in (u,v); strips u in [lo_k,hi_k] (K,). Returns vmin, vmax (q,K) of quad∩strip (nan if empty)."""
    a=P[:,:,0][:,None,:]; o=P[:,:,1][:,None,:]
    lo_=lo[None,:,None]; hi_=hi[None,:,None]
    inside=(a>=lo_-1e-12)&(a<=hi_+1e-12)
    mn=np.where(inside,o,BIG).min(-1); mx=np.where(inside,o,-BIG).max(-1)
    a2=np.roll(a,-1,axis=-1); o2=np.roll(o,-1,axis=-1)
    for b in (lo_,hi_):
        cr=(a-b)*(a2-b)<0
        t=np.where(cr,(b-a)/np.where(a2!=a,a2-a,1.0),0.0)
        val=o+t*(o2-o)
        mn=np.minimum(mn,np.where(cr,val,BIG).min(-1)); mx=np.maximum(mx,np.where(cr,val,-BIG).max(-1))
    return mn,mx
class Band:
    def __init__(self,L,phi_deg,a0):
        self.L=L; self.m=int(math.floor(L+1e-9)); self.phi=math.radians(phi_deg); self.phi_deg=phi_deg
        c,s=math.cos(self.phi),math.sin(self.phi)
        self.R=np.array([[c,s],[-s,c]])            # (x,y)->(u,v)
        corners=np.array([[0,0],[L,0],[L,L],[0,L]],float)@self.R.T
        umin,umax=corners[:,0].min(),corners[:,0].max()
        k0=math.floor(umin-a0)-1; k1=math.ceil(umax-a0)+1
        self.lo=a0+np.arange(k0,k1,dtype=float); self.hi=self.lo+1
        # wall limits: the tilted cell [lo,hi]x[t,t+1] must be inside the container: v-range of container at u=lo and u=hi
        def vr(uv):
            mn,mx=strip_ext(corners[None],uv-1e-9,uv+1e-9)
            return mn[0],mx[0]
        g1,h1=vr(self.lo); g2,h2=vr(self.hi)
        bad=(g1>=BIG/2)|(g2>=BIG/2)
        self.wlo=np.where(bad,BIG,np.maximum(g1,g2)); self.whi=np.where(bad,-BIG,np.minimum(h1,h2))
        self.m_rows=self.m
        self.memo={}
    def row_ext(self,kind,j,n):
        """v extent in every band of an upright row. kind 0: top-left grid row j from the top with n cells from x=0;
        kind 1: bottom-right grid row j from the bottom with n cells from x=L. returns (K,) vmin (kind 0) or vmax (kind 1)"""
        key=(kind,j,n)
        r=self.memo.get(key)
        if r is None:
            L=self.L
            if n<=0: r=np.full(len(self.lo), BIG if kind==0 else -BIG)
            else:
                if kind==0: q=np.array([[0,L-j-1],[n,L-j-1],[n,L-j],[0,L-j]],float)
                else: q=np.array([[L-n,j],[L,j],[L,j+1],[L-n,j+1]],float)
                mn,mx=strip_ext((q@self.R.T)[None],self.lo,self.hi)
                r=mn[0] if kind==0 else mx[0]
            self.memo[key]=r
        return r
    def count(self,a,b,detail=False):
        m=self.m
        hi=self.whi.copy(); lo=self.wlo.copy()
        for j in range(m):
            if a[j]>0: hi=np.minimum(hi,self.row_ext(0,j,a[j]))
            if b[j]>0: lo=np.maximum(lo,self.row_ext(1,j,b[j]))
        gap=hi-lo
        cnt=np.where(gap>0,np.floor(gap+1e-9),0).astype(int)
        cnt=np.maximum(cnt,0)
        if detail: return int(sum(a)+sum(b)+cnt.sum()),cnt,lo,hi
        return int(sum(a)+sum(b)+cnt.sum())
    def feasible(self,a,b):
        m=self.m; L=self.L; f=L-m
        # top-left row j: y in [L-j-1, L-j]; bottom-right row r: y in [r, r+1]; they overlap in y when r < L-j and r+1 > L-j-1
        for j in range(m):
            if a[j]==0: continue
            ylo=L-j-1; yhi=L-j
            for r in (int(math.floor(ylo+1e-12)), int(math.floor(ylo+1e-12))+1, int(math.floor(ylo+1e-12))-1):
                if 0<=r<m and b[r]>0 and r<yhi-1e-12 and r+1>ylo+1e-12:
                    if a[j]>L-b[r]+1e-12: return False
        return True
    def squares(self,a,b):
        """explicit layout (x,y,angle_rad)"""
        m=self.m; L=self.L; out=[]
        for j in range(m):
            for i in range(a[j]): out.append((i+0.5,L-j-0.5,0.0))
            for i in range(b[j]): out.append((L-i-0.5,j+0.5,0.0))
        N,cnt,lo,hi=self.count(a,b,True)
        Ri=self.R.T
        for k in range(len(cnt)):
            c=int(cnt[k])
            if c<=0: continue
            slack=(hi[k]-lo[k]-c)
            for i in range(c):
                uv=np.array([self.lo[k]+0.5, lo[k]+slack/2+i+0.5])
                x,y=Ri@uv
                out.append((float(x),float(y),self.phi))
        return out
def init_profiles(m,L,w1,w2,anti=False):
    """straight diagonal channel: top-left rows end at the main diagonal minus w1, bottom-right rows start w2 past it"""
    a=[0]*m; b=[0]*m
    for j in range(m):
        ytop=L-j        # top-left row j spans y in [L-j-1, L-j]; keep cells with x <= y_bottom - w1
        a[j]=max(0,min(m,int(math.floor(L-j-1-w1+1e-9))))
        b[j]=max(0,min(m,int(math.floor(L-(j+1)-w2+1e-9))))   # cells with x >= y_top + w2 -> count from right = L - (j+1) - w2
    return a,b
def anneal(B,a,b,steps,T0=0.6,T1=0.05,seed=0):
    rng=random.Random(seed); m=B.m
    a=list(a); b=list(b)
    cur=B.count(a,b); best=(cur,list(a),list(b))
    for it in range(steps):
        T=T0*(T1/T0)**(it/max(1,steps-1))
        arr=a if rng.random()<0.5 else b
        j=rng.randrange(m); d=rng.choice((-1,1))
        span=1 if rng.random()<0.7 else rng.randint(2,4)
        idx=[i for i in range(j,min(m,j+span))]
        old=[arr[i] for i in idx]
        ok=True
        for i in idx:
            nv=arr[i]+d
            if nv<0 or nv>m: ok=False; break
            arr[i]=nv
        if not ok or not B.feasible(a,b):
            for i,o in zip(idx,old): arr[i]=o
            continue
        new=B.count(a,b)
        if new>=cur or rng.random()<math.exp((new-cur)/T):
            cur=new
            if cur>best[0]: best=(cur,list(a),list(b))
        else:
            for i,o in zip(idx,old): arr[i]=o
    return best
if __name__=='__main__':
    m=int(sys.argv[1]); f=float(sys.argv[2]); phi=float(sys.argv[3]); steps=int(sys.argv[4]) if len(sys.argv)>4 else 20000
    L=m+f
    for a0 in (0.0,0.25,0.5,0.75):
        B=Band(L,phi,a0)
        best=None
        for w in (0.5,1.0,1.5,2.0,2.5,3.0,3.5):
            a,b=init_profiles(m,L,w,w)
            if not B.feasible(a,b): continue
            n=B.count(a,b)
            if best is None or n>best[0]: best=(n,a,b,w)
        t=time.time()
        res=anneal(B,best[1],best[2],steps)
        print(json.dumps({'m':m,'f':f,'phi':phi,'a0':a0,'init_gain':best[0]-m*m,'w':best[3],'sa_gain':res[0]-m*m,'secs':round(time.time()-t,1)}),flush=True)
