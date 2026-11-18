import pathlib,csv,json,sys,subprocess
from provenance24 import W,S,mlp,credit
from base25 import current
from stage24 import stage
P,o=current()
# Changed clean licensed geometry first; historical numerical dead ends stay closed.
for tag,n,p in [
 ('licensed20001',228,S/'take-k123-r24/228.csv'),
 ('licensed20002',581,S/'take-k123-r24/581.csv'),
 ('licensed20003',847,S/'take-soft-r24/847.csv'),
 ('licensed20004',365,S/'take-k123-r24/near/365-cc0-rebuilt.csv'),
 ('licensed20005',790,S/'take-k123-r24/near/790-cc0-rebuilt.csv')]:
 if not p.exists():continue
 A=mlp.load(str(p),{n})[n]
 if not credit(n,A,str(p)):print('REFUSED',p,flush=True);continue
 from stage24 import kj
 try:
  X=kj.Lay(n,*kj.norm(A),str(n));types={(int(X.size[i-1]),int(X.size[i])) for i in range(4,len(X.G)-4)};types|={(b,a) for a,b in list(types)}
 except Exception:continue
 pairs=[]
 for nn,B in P.items():
  if nn<100 or not credit(nn,B,o[nn]):continue
  try:
   Y=kj.Lay(nn,*kj.norm(B),str(nn));tt={(int(Y.size[i-1]),int(Y.size[i])) for i in range(4,len(Y.G)-4)};tt|={(b,a) for a,b in list(tt)}
   if types&tt:pairs.append((n,nn))
  except Exception:pass
 if not pairs:continue
 stage(tag,{**P,n:A},{**o,n:str(p)},pairs,'licensed',str(p))
