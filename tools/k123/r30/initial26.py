import pathlib,sys,time,json,csv,hashlib,re
W=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import S,credit,key,mlp
from base25 import current
from stage24 import stage,kj
P,o=current();classes={}
for n,A in P.items():
 if n<100:continue
 try:
  X=kj.Lay(n,*kj.norm(A),str(n))
  if len(X.G)<10:continue
  tt={(int(X.size[i-1]),int(X.size[i])) for i in range(4,len(X.G)-4)};tt|={(b,a) for a,b in list(tt)};classes[n]=tt
 except Exception:pass
for n in [735,790,968,228,365,534,581,597,907]:
 if n not in classes or not credit(n,P[n],o[n]):continue
 partners=[nn for nn in classes if classes[n]&classes[nn]]
 stage(f'licensed{n:05}',P,o,[(n,nn) for nn in partners],'licensed-changed-held',f'posted round25b n={n}; changed clean ends and follower returns')
print('initial done',flush=True)
