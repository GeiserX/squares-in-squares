"""Tilted block with a mixed upright fill (border r28 design). Rows from the left wall in x < k1 and from the right
wall in x > W-k2 (bottom rows 0..J-1 on the bottom wall, the rest from the top wall, J chosen per side); unit
columns between, aligned on x = k1, each with a stack from the bottom wall and one from the top wall up to the block.
For n = M*M+K: per angle, block a x b and (k1, k2), the smallest f (bisection to 1e-4) whose best count reaches n.
usage: bfmix.py OUT.jsonl M K ANGLES FLO FHI AMIN"""
import sys, os, math, json, time, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blockfill import corners, slab_x
EPS=1e-9
def slab_y(poly,x0,x1):
    return slab_x([(y,x) for x,y in poly],x0,x1)
def slab_y_vec(poly,u):
    """y-range of the convex polygon over the vertical slabs [u, u+1] (u an array): (ymin, ymax) with +-inf when empty."""
    lo=np.full(len(u),np.inf);hi=np.full(len(u),-np.inf)
    n=len(poly)
    for i in range(n):
        (xa,ya),(xb,yb)=poly[i],poly[(i+1)%n]
        m=(u<=xa)&(xa<=u+1);lo=np.where(m,np.minimum(lo,ya),lo);hi=np.where(m,np.maximum(hi,ya),hi)
        if xa!=xb:
            for xx in (u,u+1):
                tt=(xx-xa)/(xb-xa);m=(tt>0)&(tt<1);yy=ya+(yb-ya)*tt
                lo=np.where(m,np.minimum(lo,yy),lo);hi=np.where(m,np.maximum(hi,yy),hi)
    return lo,hi
def best_count(S,a,b,t,K1,K2,step=0.01):
    W=S;H=S;R=int(math.floor(H+EPS))
    c,s=math.cos(t),math.sin(t);hw=(a*abs(c)+b*abs(s))/2;hh=(a*abs(s)+b*abs(c))/2
    if 2*hw>W+EPS or 2*hh>H+EPS:return -1,None
    best=(-1,None)
    for k1 in K1:
      for k2 in K2:
        mid=W-k1-k2
        if mid<0:continue
        ncol=int(math.floor(mid+EPS))
        cxs=np.arange(max(hw,W/2-0.6),min(W-hw,W/2+0.6)+1e-12,step)
        if len(cxs)==0:continue
        for cy in np.arange(max(hh,H/2-0.6),min(H-hh,H/2+0.6)+1e-12,step):
            poly=corners(0.0,cy,a,b,t)
            # left and right rows, per cx
            Lb=np.empty((R,len(cxs)));Lt=np.empty((R,len(cxs)));Rb=np.empty((R,len(cxs)));Rt=np.empty((R,len(cxs)))
            for j in range(R):
                for (Lx,Rx,y0) in ((Lb,Rb,j),(Lt,Rt,H-1-j)):
                    r=slab_x(poly,y0,y0+1)
                    if r is None:Lx[j]=k1;Rx[j]=k2
                    else:
                        Lx[j]=np.minimum(k1,np.floor(np.maximum(cxs+r[0],0)+EPS))
                        Rx[j]=np.minimum(k2,np.floor(np.maximum(W-cxs-r[1],0)+EPS))
            def split(B,T):
                cb=np.vstack([np.zeros(len(cxs)),np.cumsum(B,0)]);ct=np.vstack([np.zeros(len(cxs)),np.cumsum(T,0)])
                return (cb+ct[::-1]).max(0)
            tot=split(Lb,Lt)+split(Rb,Rt)
            # columns of the middle
            col=np.zeros(len(cxs))
            for i in range(ncol):
                x0=k1+i
                lo,hi=slab_y_vec(poly,x0-cxs)
                empty=~np.isfinite(lo)
                col+=np.where(empty,R,np.floor(np.maximum(np.where(empty,0,lo),0)+EPS)+np.floor(np.maximum(H-np.where(empty,H,hi),0)+EPS))
            tot=tot+col
            q=int(np.argmax(tot));v=int(tot[q])+a*b
            if v>best[0]:best=(v,dict(cx=float(cxs[q]),cy=float(cy),k1=k1,k2=k2))
    return best
if __name__=='__main__':
    out,M,K=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]);ANG=[float(x) for x in sys.argv[4].split(',')]
    FLO,FHI=float(sys.argv[5]),float(sys.argv[6]);AMIN=int(sys.argv[7]);n=M*M+K;t0=time.time()
    with open(out,'a') as fo:
      for deg in ANG:
        t=math.radians(deg);c,s=abs(math.cos(t)),abs(math.sin(t))
        for a in range(AMIN,M+1):
          for b in range(AMIN,M+1):
            w=a*c+b*s;h=a*s+b*c
            if w>M+FHI or h>M+FHI or a*b<0.25*n:continue
            # the side regions: k1, k2 around the block's free width
            free=M+FHI-w;K1=sorted({max(0,int(free/2)+d) for d in (-1,0,1)});K2=K1
            v,cfg=best_count(M+FHI,a,b,t,K1,K2,0.02)
            if v<n:continue
            lo,hi=FLO,FHI;best=(FHI,v,cfg)
            while hi-lo>2e-4:
                mid=(lo+hi)/2;v,cfg=best_count(M+mid,a,b,t,K1,K2,0.02)
                if v>=n:hi=mid;best=(mid,v,cfg)
                else:lo=mid
            fo.write(json.dumps(dict(m=M,k=K,f=round(best[0],5),count=best[1],deg=deg,a=a,b=b,**(best[2] or {})))+'\n');fo.flush()
        print('deg',deg,'done',round(time.time()-t0),flush=True)

def screen(out,M,K,ANG,FT,AMIN,step=0.03):
    """one count per configuration at f = FT (coarse centre grid); a line for every configuration within 3 of n."""
    n=M*M+K;S=M+FT;t0=time.time()
    with open(out,'a') as fo:
      for deg in ANG:
        t=math.radians(deg);c,s=abs(math.cos(t)),abs(math.sin(t));best=-1
        for a in range(AMIN,M+1):
          for b in range(AMIN,M+1):
            w=a*c+b*s;h=a*s+b*c
            if w>S or h>S or a*b<0.2*n:continue
            free=S-w;K1=sorted({max(0,int(free/2)+d) for d in (-1,0,1)})
            v,cfg=best_count(S,a,b,t,K1,K1,step)
            best=max(best,v)
            if v>=n-3:fo.write(json.dumps(dict(m=M,k=K,f=FT,count=v,deg=deg,a=a,b=b,**(cfg or {})))+'\n');fo.flush()
        print('deg',deg,'best',best,'of',n,'at f',FT,round(time.time()-t0),flush=True)

def layout(S,a,b,t,cx,cy,k1,k2):
    """the squares (x, y, angle rad) of one mixed configuration (the J split per side is the best one)."""
    W=S;H=S;R=int(math.floor(H+EPS));out=[]
    c,s=math.cos(t),math.sin(t)
    for i in range(a):
        for j in range(b):
            u=i-(a-1)/2;v=j-(b-1)/2;out.append((cx+c*u-s*v,cy+s*u+c*v,t))
    poly=corners(cx,cy,a,b,t)
    def runs(side):
        bot=[];top=[]
        for j in range(R):
            for arr,y0 in ((bot,j),(top,H-1-j)):
                r=slab_x(poly,y0,y0+1)
                if r is None:arr.append(k1 if side=='L' else k2)
                elif side=='L':arr.append(min(k1,math.floor(max(r[0],0)+EPS)))
                else:arr.append(min(k2,math.floor(max(W-r[1],0)+EPS)))
        J=max(range(R+1),key=lambda J:sum(bot[:J])+sum(top[:R-J]))
        return [(j,bot[j]) for j in range(J)]+[(H-1-q,top[q]) for q in range(R-J)]
    for y0,k in runs('L'):
        for q in range(int(k)):out.append((0.5+q,y0+0.5,0.0))
    for y0,k in runs('R'):
        for q in range(int(k)):out.append((W-0.5-q,y0+0.5,0.0))
    ncol=int(math.floor(W-k1-k2+EPS))
    for i in range(ncol):
        x0=k1+i;r=slab_y(poly,x0,x0+1)
        if r is None:
            for q in range(R):out.append((x0+0.5,0.5+q,0.0))
            continue
        for q in range(int(math.floor(max(r[0],0)+EPS))):out.append((x0+0.5,0.5+q,0.0))
        for q in range(int(math.floor(max(H-r[1],0)+EPS))):out.append((x0+0.5,H-0.5-q,0.0))
    return out
