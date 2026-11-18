"""Model start plus fq: for n = M*M+K and one angle, find the smallest f (to 1e-3) where the mixed model reaches n
over blocks a x b, write that layout as an fq start and run fq chains (default then polish rounds, border_sweep
quench_one, up to ROUNDS) from it. Prints the start and end sides.
usage: mixfq.py M K DEG FHI ROUNDS TAG [AMIN]"""
import sys, os, math, json, time
D=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,D);sys.path.insert(0,os.path.dirname(D))
import bfmix as B, border_sweep as bs
M,K,deg,FHI,ROUNDS,TAG=int(sys.argv[1]),int(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),int(sys.argv[5]),sys.argv[6]
AMIN=int(sys.argv[7]) if len(sys.argv)>7 else 6
n=M*M+K;t=math.radians(deg);c,s=abs(math.cos(t)),abs(math.sin(t))
END=float(open(os.path.join(os.path.dirname(D),'deadline')).read())
best=None
for a in range(AMIN,M+1):
  for b in range(AMIN,M+1):
    S=M+FHI;w=a*c+b*s;h=a*s+b*c
    if w>S or h>S or a*b<0.2*n:continue
    free=S-w;K1=sorted({max(0,int(free/2)+d) for d in (-1,0,1)})
    v,cfg=B.best_count(S,a,b,t,K1,K1,0.03)
    if v<n:continue
    lo,hi=0.0,FHI;bc=(FHI,cfg)
    while hi-lo>1e-3:
      mid=(lo+hi)/2;v,cg=B.best_count(M+mid,a,b,t,K1,K1,0.03)
      if v>=n:hi=mid;bc=(mid,cg)
      else:lo=mid
    if best is None or bc[0]<best[0]:best=(bc[0],a,b,bc[1]);print('model',M,K,deg,a,b,round(bc[0],4),flush=True)
f,a,b,cfg=best;S=M+f
L=B.layout(S,a,b,t,cfg['cx'],cfg['cy'],cfg['k1'],cfg['k2'])
L=L[:n] if len(L)>=n else L
start=os.path.join(D,f'{TAG}.start.txt');bs.write_txt(start,S,[(x,y,math.degrees(an)) for x,y,an in L])
print('start',TAG,'n',len(L),'S',S,'block',a,b,deg,flush=True)
res=bs.quench_one((start,os.path.join(os.path.dirname(D),'fq'),600,ROUNDS,.001,0,END))
print('fq chain',TAG,res['s_start'],'->',res['s_final'],'rounds',res['round'],'best',res['best'],'f',res['s_final']-M,flush=True)
