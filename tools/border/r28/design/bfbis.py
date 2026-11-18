"""Bisection version of bfscan.py: for n = m*m + k, each angle, block a x b (a <= b, bounding box inside the box) and
p in (0, 1), the smallest f in [FLO, FHI] (to 1e-4) whose best count reaches n. One line per configuration.
usage: bfbis.py OUT.jsonl M K ANGLES(deg,comma) FLO FHI AMIN AMAX"""
import sys, os, math, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
__file__=os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),'bfscan.py')
src=open(__file__).read().split('t0=time.time()')[0]
argv=sys.argv;sys.argv=['x','/dev/null','1','1','1','45','0.5','0.5','0.01']
exec(src)
sys.argv=argv
out,M,K=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
ANG=[float(x) for x in sys.argv[4].split(',')];FLO,FHI=float(sys.argv[5]),float(sys.argv[6]);AMIN,AMAX=int(sys.argv[7]),int(sys.argv[8])
n=M*M+K;t0=time.time()
with open(out,'a') as fo:
  for deg in ANG:
    t=math.radians(deg)
    for a in range(AMIN,AMAX+1):
      for b in range(a,M+1):
        c,s=abs(math.cos(t)),abs(math.sin(t))
        if a*c+b*s>M+FHI or a*s+b*c>M+FHI:continue
        for p in (0,1):
          v,cfg=best_count(M+FHI,a,b,t,p)
          if v<n:continue
          lo,hi=FLO,FHI;best=(FHI,v,cfg)
          while hi-lo>1e-4:
            mid=(lo+hi)/2;v,cfg=best_count(M+mid,a,b,t,p)
            if v>=n:hi=mid;best=(mid,v,cfg)
            else:lo=mid
          fo.write(json.dumps(dict(m=M,k=K,f=round(best[0],5),count=best[1],deg=deg,a=a,b=b,p=p,**(best[2] or {})))+'\n');fo.flush()
    print('deg',deg,'done',round(time.time()-t0),flush=True)
