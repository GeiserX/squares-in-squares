from pathlib import Path
import sys,csv,json,subprocess,time,os
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp,credit
os.environ['K123_BASE_SECONDS32']='20'
P=mlp.load(str(W.parent.parent/'gather/round33-2026-11-17a.csv'),{261,367});o={n:'held' for n in P}
for n in [261,367]:
 pool=f'physical34n{n}';D=W/pool;D.mkdir(exist_ok=True)
 if not (D/(pool+'.csv')).exists():
  c=credit(n,P[n],o[n]);assert c
  with (D/(pool+'.csv')).open('w') as f:
   wr=csv.writer(f);wr.writerow(['n','square_id','x','y','angle']);wr.writerows((n,i,*r) for i,r in enumerate(P[n]))
  (D/('sources-'+pool+'.json')).write_text(json.dumps({str(n):c}));(D/('bars-'+pool+'.tsv')).write_text((W/'bars.tsv').read_text())
  for p in D.iterdir():subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r35-boxE',str(p),'boxE:scratch/squares-k123/'],check=True)
 from k123_tartan import Hole
 A=mlp.load(str(D/(pool+'.csv')),{n})[n];H=Hole(A);phi=float(H.t0*180/__import__('math').pi-45.)
 j=dict(kind='verify',tag=f'verify-maskexchange34-control{n}',mask_exchange34=True,seed_n=n,pool=pool,case=dict(control=True),seconds=0,angles=[phi-.5,phi+.5],expected_side=float(mlp.side(A)))
 p=W/(j['tag']+'.json');p.write_text(json.dumps(j));subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r35-boxE',str(p),'boxE:scratch/squares-k123/tasks/'],check=True)
 print('queued new-source control',n,'source_side',mlp.side(A),'phi',phi,flush=True)
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA START mixed-angle controls on different physical source layouts261 and367 before any target. Original368 pilots made220386 iterations and379728 mask interchanges, added no square, and all4 generation quenches returned the held368 side. Those exact profiles stay closed. Different sources change the block aspect and staircase phase; controls must rebuild source side within2e-6 before their one-minute target runs. Existing boxE slot, cutoff16:25Z.\n')
