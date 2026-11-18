from pathlib import Path
import sys,json,csv,subprocess,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp,credit
from base25 import current
P,o=current();pairs=[(258,259),(444,445),(733,734),(966,968),(367,368),(260,261)]
ns=sorted({n for p in pairs for n in p});meta={}
for n in ns:
 c=credit(n,P[n],o[n]);assert c,n;meta[str(n)]=c
pool='crossdistinct34';D=W/pool;D.mkdir(exist_ok=True)
with (D/(pool+'.csv')).open('w') as f:
 w=csv.writer(f);w.writerow(['n','square_id','x','y','angle'])
 for n in ns:w.writerows((n,i,*r) for i,r in enumerate(P[n]))
(D/('sources-'+pool+'.json')).write_text(json.dumps(meta));(D/('bars-'+pool+'.tsv')).write_text((W/'bars.tsv').read_text())
for p in D.iterdir():subprocess.run(['scp','-q',str(p),'boxE:scratch/squares-k123/'],check=True)
for i in range(0,len(pairs),2):
 cases=[dict(a=a,b=b,L=max(float(mlp.side(P[a])),float(mlp.side(P[b])))+1e-8) for a,b in pairs[i:i+2]]
 j=dict(kind='verify',tag=f'verify-crossdistinct34-{i}',whole_crossover34=True,pool=pool,cases=cases,seconds=90)
 p=W/(j['tag']+'.json');p.write_text(json.dumps(j));subprocess.run(['scp','-q',str(p),'boxE:scratch/squares-k123/tasks/'],check=True)
line=time.strftime('%FT%TZ',time.gmtime())+' boxA START distinct-layout spatial crossover. Changed the round33 dry self-D4 mechanism by crossing six pairs of different complete held layouts: '+str(pairs)+'. Pure512-graph and identity controls run first in each job. Three90s jobs in the existing boxE verification slot, log out/verify-crossdistinct34-*.log, deadline07:25Z.\n'
with (W.parent/'STATE.txt').open('a') as f:f.write(line)
print(line)
