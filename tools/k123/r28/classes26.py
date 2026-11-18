"""Cache chain readings of unchanged layouts between light admission passes."""
import numpy as np
from provenance24 import key
_cache={}
def read(n,A,kj):
 token=(n,key(n,A))
 if token not in _cache:
  try:
   X=kj.Lay(n,*kj.norm(A),str(n))
   if len(X.G)<10:out=None
   else:
    out={(int(X.size[i-1]),int(X.size[i])) for i in range(4,len(X.G)-4)};out|={(b,a) for a,b in list(out)}
  except Exception:out=None
  _cache[token]=out
 return _cache[token]
