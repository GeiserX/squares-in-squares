import time
from pathlib import Path
marker=Path(__file__).resolve().parent/'saved-last'
if marker.exists() and time.time()-marker.stat().st_mtime<600:raise SystemExit
marker.touch()
"""Rescan saved pairs only after a donor geometry or admitted source changed."""
import pathlib,json,csv,re,collections,time
from provenance24 import W,S,credit,key,mlp
from base25 import current
from stage24 import stage
O=S/'take-k123-r24/work';F=W/'saved-seen25.json';seen=set(json.load(open(F))) if F.exists() else set()
log=(S/'handoff-r32.log').read_text()
if any('backlog ->' in l and ('k123' in l and ('CLAIM' in l or 'claim' in l)) for l in log.splitlines()):
 print('saved queue claimed by backlog; skip');raise SystemExit
P,orig=current();pairs={};path=O/'pending-final.tsv'
if not path.exists():path=O/'queue.tsv'
for line in path.read_text().splitlines():
 f=line.split('\t')
 if len(f)<8:continue
 m=re.match(r'(\d+)r?-(\d+)r?-j',f[1])
 if not m:continue
 a,b=map(int,m.groups());pairs.setdefault((a,b,f[7]),float(f[6]))
chosen=[];proof={};refused=0;catalogs={};batch_started=time.time();considered=0
for (a,b,pool),room in sorted(pairs.items(),key=lambda z:-z[1]):
 if time.time()-batch_started>20 or considered>=64:break
 token=f'{pool}:{a}:{b}'
 if token in seen:continue
 seen.add(token);considered+=1
 mp=O/pool/f'sources-{pool}.json'
 if not mp.exists():mp=O/f'sources-{pool}.json'
 if not mp.exists() or a not in P or b not in P:continue
 try:
  if str(mp) not in catalogs:catalogs[str(mp)]=json.load(open(mp))
  old=catalogs[str(mp)];changed=any(key(nn,P[nn])!=old[str(nn)].get('sha256_geometry') for nn in (a,b))
 except (KeyError,ValueError):continue
 if not changed:continue
 for nn in (a,b):
  if nn not in proof:proof[nn]=credit(nn,P[nn],orig[nn])
 if not all(proof[nn] for nn in (a,b)):refused+=1;continue
 chosen.append((a,b))
 if len(chosen)>=12:break
F.write_text(json.dumps(sorted(seen)))
if chosen:
 seq=int((W/'saved-seq').read_text())+1 if (W/'saved-seq').exists() else 1;(W/'saved-seq').write_text(str(seq))
 stage(f'saved{seq:05d}',P,orig,list(dict.fromkeys(chosen)),'saved-changed','changed current donors of '+str(path))
print('saved considered',len(seen),'staged pairs',len(chosen),'refused',refused,flush=True)
