"""structure lane: classify a held layout. Prints the angle histogram, the tilted clusters (blocks) and, per block,
whether its squares form rows or columns in the block's own frame (count, slide and spacing per row).

  structure_classify.py N [N ...] [--png DIR]
"""
import sys, os, math, collections
import numpy as np
from structure_lib import *
def clusters(T,r=1.25):
    n=len(T); par=list(range(n))
    def f(i):
        while par[i]!=i: par[i]=par[par[i]]; i=par[i]
        return i
    for i in range(n):
        for j in range(i):
            if math.hypot(T[i][0]-T[j][0],T[i][1]-T[j][1])<r: par[f(i)]=f(j)
    C=collections.defaultdict(list)
    for i in range(n): C[f(i)].append(T[i])
    return list(C.values())

def rows_report(sq):
    x0,y0,x1,y1=bbox(sq); L=max(x1-x0,y1-y0)
    T=[(x-x0,y-y0,norm(a)) for x,y,a in sq if abs(norm(a))>0.5]
    for c in sorted(clusters(T),key=len,reverse=True)[:3]:
        A=np.array(c); th=math.radians(np.median(A[:,2]))
        u=np.array([math.cos(th),math.sin(th)]); v=np.array([-math.sin(th),math.cos(th)])
        a=A[:,:2]@u; b=A[:,:2]@v
        print('cluster',len(c),'theta %.4f'%math.degrees(th))
        for name,p,q in (('rows(b const)',b,a),('cols(a const)',a,b)):
            o=np.argsort(p); ps=p[o]; qs=q[o]
            groups=[[0]]
            for i in range(1,len(ps)):
                if ps[i]-ps[groups[-1][-1]]<0.3: groups[-1].append(i)
                else: groups.append([i])
            print(' ',name,'n groups',len(groups))
            if len(groups)<3: continue
            for g in groups:
                qq=np.sort(qs[g])
                print('    pos %.3f (sd %.3f) count %d  start frac %.3f  max gap %.3f'%(ps[g].mean(),ps[g].std(),len(g),qq[0]%1,(np.diff(qq).max() if len(qq)>1 else 0)))
if __name__=="__main__":
    args=sys.argv[1:]; png=None
    if '--png' in args:
        i=args.index('--png'); png=args[i+1]; args=args[:i]+args[i+2:]
    P=load()
    for n in map(int,args):
        sq=P[n]; L=side(sq); m=int(L)
        angs=collections.Counter(round(abs(norm(a)),1) for x,y,a in sq)
        print('n',n,'L=%.6f'%L,'k=',n-m*m,'tilted',sum(v for k,v in angs.items() if k>0),sorted(angs.items(),key=lambda t:-t[1])[:8])
        rows_report(sq)
        if png: draw(sq,os.path.join(png,'structure_%d.png'%n),'n=%d L=%.5f'%(n,L))
