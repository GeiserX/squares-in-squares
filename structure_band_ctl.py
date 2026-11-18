import sys, math, numpy as np
from structure_lib import *
from structure_band import *
P=load()
def profiles(n,flip=False):
    sq=P[n]; x0,y0,x1,y1=bbox(sq); L=max(x1-x0,y1-y0); m=int(L)
    a=[0]*m; b=[0]*m; other=0; til=[]
    for x,y,ang in sq:
        x-=x0; y-=y0
        if flip: x=L-x; ang=-ang
        if abs(norm(ang))>0.5: til.append((x,y,norm(ang))); continue
        fx=(x-0.5)%1; fy=(L-y-0.5)%1
        gx=(L-x-0.5)%1; gy=(y-0.5)%1
        e=1e-3
        tl=min(fx,1-fx)<e and min(fy,1-fy)<e
        br=min(gx,1-gx)<e and min(gy,1-gy)<e
        if tl and (not br or x<y):
            j=int(round(L-y-0.5)); a[j]+=1
        elif br:
            r=int(round(y-0.5)); b[r]+=1
        else: other+=1
    return L,m,a,b,other,til
if __name__=='__main__':
    n=int(sys.argv[1]); phi=float(sys.argv[2]); flip=len(sys.argv)>3
    L,m,a,b,other,til=profiles(n,flip)
    print('n',n,'L',L,'uprights TL',sum(a),'BR',sum(b),'other upright',other,'tilted',len(til))
    best=None
    for a0 in np.arange(0,1,0.02):
        B=Band(L,phi,a0)
        N,cnt,lo,hi=B.count(a,b,True)
        if best is None or N>best[0]: best=(N,a0,B.feasible(a,b),int(cnt.sum()))
    print('band model count',best[0],'a0',best[1],'feasible',best[2],'tilted in bands',best[3],'  (layout holds',n,')')
