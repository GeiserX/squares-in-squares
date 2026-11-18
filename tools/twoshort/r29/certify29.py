"""Publish a proved, quenched improvement after floatsafe certification."""
from pathlib import Path
import sys,json,csv,math,time,fcntl,argparse
csv.field_size_limit(16000000)
W=Path(__file__).parent;T=W.parent;B=T.parent
sys.path.insert(0,str(W));sys.path.insert(0,str(W/'lane'))
import finesafe as floatsafe  # round 29: border's bisected dilation (pinned copy, finesafe.sha256)
from bar29 import bars,label
from admit29 import store
from shape974 import load as geometry_load
from source29 import credited_cells
ap=argparse.ArgumentParser();ap.add_argument('stage');ap.add_argument('--paths',nargs='*');a=ap.parse_args()
lock=open(W/'locks/certify.lock','a');fcntl.flock(lock,fcntl.LOCK_EX)
base,_,_,live=bars(T)
cur={int(r['n']):r for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')}
for p in map(Path,a.paths if a.paths is not None else sorted(Path(a.stage).glob('*.csv'))):
 md=json.load(open(p.with_suffix('.json')))
 if not md.get('ancestry_checked'):print('DROP unproved',p);continue
 # Round 27: n whose start tree was withdrawn by its producer for a still-valid reason stay out (work/withdrawn-n.txt).
 if (W/'withdrawn-n.txt').exists() and p.stem.split('-')[0] in {l.split()[0] for l in (W/'withdrawn-n.txt').read_text().splitlines() if l.strip()}:print('DROP withdrawn n',p);continue
 if not credited_cells(md['source'],md['licence']):print('DEFER public upstream credit in both cells',p);continue
 n=int(p.stem.split('-')[0]);_,raw_side=geometry_load(p)
 if raw_side/math.sqrt(n)-1>=min(base[n],live[n])-1e-11:print('DROP raw bar',n);continue
 from admit29 import store_lenient
 ok,proof=store_lenient(dict(source=md['source'],licence=md['licence']),n=n)
 if not ok:print('DROP source closure',p,(proof.get('fresh_closure') or proof['closure'])['errors'][:2]);continue
 import qgate29
 qres=qgate29.check(p)
 if not qres.get('clean'):print('DROP quench_walk',p,qres.get('hits',[])[:2]);continue
 n=int(p.stem.split('-')[0]);rows=[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(p))]
 _,fr,s,e=floatsafe.work((n,rows))
 base,_,_,live=bars(T)
 if len(rows)!=n or fr is None or s>=base[n]-1e-10 or s>=live[n]-1e-10:print('DROP',n,s,live[n],e);continue
 if n in cur and s>=float(cur[n]['new']):continue
 dst=T/(str(n)+'.csv');tmp=dst.with_suffix('.csv.tmp')
 with tmp.open('w',newline='') as f:
  cw=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(fr)
 tmp.replace(dst)
 cur[n]=dict(n=n,held=base[n],new=s,gain=base[n]-s,source=md['source'],licence=label(md['source'],md['licence']))
 with open(B/'handoff-r29.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> all: certified n='+str(n)+' gain='+str(base[n]-s)+' from proved raw kick and certified-input boxE fq, '+str(dst)+'\n')
 print('KEEP',n,base[n]-s,live[n]-s)
with open(T/'take.tsv.tmp','w',newline='') as f:
 cw=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');cw.writeheader();cw.writerows(cur[n] for n in sorted(cur))
(T/'take.tsv.tmp').replace(T/'take.tsv')

import os
sys.stdout.flush();sys.stderr.flush();os._exit(0)
