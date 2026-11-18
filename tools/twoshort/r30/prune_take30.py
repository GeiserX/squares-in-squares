"""Remove take rows superseded during collection and preserve their source records."""
from pathlib import Path
import csv,json,fcntl,time,sys,shutil
csv.field_size_limit(16000000)
W=Path(__file__).parent;T=W.parent;sys.path.insert(0,str(W));from bar30 import bars
lock=open(W/'locks/certify.lock','a');fcntl.flock(lock,fcntl.LOCK_EX)
base,_,_,live=bars(T);keep=[];dropped=[]
for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
 n=int(r['n']);s=float(r['new'])
 if s<base[n]-1e-10 and s<live[n]-1e-10:
  r.update(held=base[n],gain=base[n]-s);keep.append(r);continue
 p=T/(str(n)+'.csv');q=T/'near'/(str(n)+'-superseded.csv')
 if p.exists():shutil.copy2(p,q);p.unlink()
 q.with_suffix('.json').write_text(json.dumps(dict(source=r['source'],licence=r['licence'],certified=True,counted=False,score=s,base=base[n],live=live[n])))
 dropped.append(n)
 with open(T.parent/'handoff-r30.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> all: DROP superseded n='+str(n)+' from take; base='+str(base[n])+' live='+str(live[n])+'; source-preserved near '+str(q)+'\n')
with open(T/'take.tsv.tmp','w',newline='') as f:
 cw=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');cw.writeheader();cw.writerows(keep)
(T/'take.tsv.tmp').replace(T/'take.tsv');print('prune take kept',len(keep),'dropped',dropped)

import os
sys.stdout.flush();sys.stderr.flush();os._exit(0)
