"""Corner window then border (rev + b1/b2) closure scan: for each layout of N and each corner, the window of the
k squares nearest the corner has side e[k-1]; a full border gives t = k + 2*floor(e)+1 at side e+1 (b2: two borders).
Prints every (N, corner, k, t) with margin e+add-L[t] below MAX, t != N."""
import sys,csv,math,json
import numpy as np
sys.path.insert(0,'.')
import border_sweep as bs
bs.lib()
csv.field_size_limit(1<<26)
det,files,MAX=sys.argv[1],sys.argv[2:-1],float(sys.argv[-1])
L={int(r['n']):(float(r['score'])+1)*math.sqrt(int(r['n'])) for r in csv.DictReader(open(det))}
out=[]
for f in files:
  if f.endswith('.json'):continue
  try:
    if f.split('/')[-1].startswith('round') or '/gather/' in f:
      P={}
      for r in csv.DictReader(open(f)):
        n=int(r['n']);P.setdefault(n,[]).append((float(r['x']),float(r['y']),float(r['angle'])))
      items=[(n,bs.normalize(v)) for n,v in P.items()]
    else:
      m,s,A=bs.read_near(f);items=[(m,(s,A))]
  except Exception as e:
    print('skip',f,e,file=sys.stderr);continue
  for N,(s,A) in items:
    for q in range(4):
      e=np.sort(bs.extents(bs.corner(A,s,q)))
      for k in range(2,N):
        if e[k]-e[k-1]<1e-9:continue
        side=float(e[k-1]);f1=math.floor(side)
        t=k+2*f1+1
        for kind,tt,add in (('b1',t,1),('b2',t+2*math.floor(side+1)+1,2)):
          if tt>1000 or tt==N:continue
          mg=side+add-L[tt]
          if mg<MAX and side-math.floor(side)>1e-6:out.append((mg,kind,N,q,k,tt,side,f))
out.sort()
for x in out[:60]:print('%.3e'%x[0],*x[1:])
print('total',len(out),file=sys.stderr)
