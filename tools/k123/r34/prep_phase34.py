from pathlib import Path
import sys,json,csv,subprocess,time,math
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp,credit
from base25 import current
P,o=current()
for n in [368,261]:
 c=credit(n,P[n],o[n]);assert c,n
 pool=f'physical34n{n}';D=W/pool;D.mkdir(exist_ok=True)
 with (D/(pool+'.csv')).open('w') as f:
  w=csv.writer(f);w.writerow(['n','square_id','x','y','angle']);w.writerows((n,i,*r) for i,r in enumerate(P[n]))
 (D/('sources-'+pool+'.json')).write_text(json.dumps({str(n):c}));(D/('bars-'+pool+'.tsv')).write_text((W/'bars.tsv').read_text())
 for p in D.iterdir():subprocess.run(['scp','-q',str(p),'boxE:scratch/squares-k123/'],check=True)
 sides={int(l.split('\t')[0]):float(l.split('\t')[1]) for l in (W/'bars.tsv').read_text().splitlines()};cases=[dict(control=True,phi=0.)]
 for target in [n,n+1]:
  for phi in ([0.,.5,1.,2.,3.,-1.] if n==368 else [1.,2.,3.118,4.,-1.,-3.118]):cases.append(dict(n=target,phi=phi,side=sides[target]-1e-6))
 j=dict(kind='verify',tag=f'verify-physical34n{n}',phase_physical34=True,pool=pool,seed_n=n,cases=cases,seconds=120)
 p=W/(j['tag']+'.json');p.write_text(json.dumps(j));subprocess.run(['scp','-q',str(p),'boxE:scratch/squares-k123/tasks/'],check=True)
line=time.strftime('%FT%TZ',time.gmtime())+' boxA START physical upright-phase model: interior quarter-slack phases, opening seams and shifted parent uprights replace the round33 fixed four wall lattices. 512 graph controls and held368/261 reconstruction run before target searches. Two120s jobs in existing boxE verification slot; log out/verify-physical34n*.log; deadline07:25Z.\n'
with (W.parent/'STATE.txt').open('a') as f:f.write(line)
print(line)
