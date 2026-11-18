"""Screen the original slice, fresh hosts, their shells and matching side fractions."""
import math

def targets(modules,needed,bar):
 out={m*m+k for m in range(28,32) for k in range(5,17)};fresh=[m for m in modules if m['id'] in needed]
 for mod in fresh:
  n=int(mod.get('n',0))
  if 1<=n<=1000:
   m=math.isqrt(n-1);out.update(x for x in [n,n-2*m-1,n+2*m+3] if 1<=x<=1000)
 fractions=[float(m['f0']) for m in fresh if m.get('f0') is not None]
 for text,side in bar.items():
  n=int(text);m=math.isqrt(n-1)
  if n>=300 and any(abs(float(side)-m-f)<.06 for f in fractions):out.add(n)
 return sorted(out)
