"""List fresh r26 layouts (take csv and near csv of other lanes) whose side is within 2e-6 above the live bar (border r26, light)."""
import csv,json,math,glob,os,time,sys
from pathlib import Path
W=Path(__file__).resolve().parent.parent;S=W.parent.parent
L={int(k):v for k,v in json.load(open(W/'bars.json')).items()}
out=[]
for p in glob.glob(str(S/'take-*-r26/near/*.csv'))+glob.glob(str(S/'take-*-r26/[0-9]*.csv')):
 if 'take-border-r26' in p:continue
 try:
  st=os.stat(p)
  if st.st_size>1500000 or time.time()-st.st_mtime>4*3600:continue
  xs=[];n=None
  with open(p) as f:
   for r in csv.DictReader(f):
    n=int(r['n']);a=float(r['angle']);h=.5*(abs(math.cos(a))+abs(math.sin(a)));xs.append((float(r['x']),float(r['y']),h))
  if n is None or len(xs)!=n or n not in L:continue
  side=max(max(x+h for x,y,h in xs)-min(x-h for x,y,h in xs),max(y+h for x,y,h in xs)-min(y-h for x,y,h in xs))
  gap=side-L[n]
  if -1e-9<gap<2e-6:out.append((gap,n,p,side))
 except Exception:continue
out.sort()
with open(W/'lpnear/pick.tsv','w') as f:
 for g,n,p,s in out:f.write(f'{n}\t{g:.3e}\t{s!r}\t{p}\n')
print(len(out));[print(n,f'{g:.3e}',p.split('bounties-squares/')[1]) for g,n,p,s in out[:40]]
