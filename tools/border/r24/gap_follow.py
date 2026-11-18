from pathlib import Path
import csv,json,sys,math,subprocess,hashlib
from types import SimpleNamespace
W=Path(__file__).parent;T=W.parent
sys.path.insert(0,'.');sys.path.insert(0,str(W))
import border_sweep as b
from provenance import audit_manifest
b.lib();import floatsafe
csv.field_size_limit(16000000)
rows=list(csv.DictReader(open(W/'q/manifest.tsv'),delimiter='\t'))
r=next(r for r in rows if r['id']=='685-b1-634-d47afb30-q0-v2')
assert audit_manifest(r)
m,s,A=b.read_near(r['near']);n=int(r['n']);v=int(r['variant'])
G=b.gap_list('1,end',A,s,v%4)
assert G,'no wall tilt for gap experiment'
for g in G:
 B=b.build('b1',A,s,n,0,4*g+v%4)
 assert len(B)==n
 rr=[dict(n=str(n),square_id=str(i),x=repr(float(x)),y=repr(float(y)),angle=repr(math.radians(d))) for i,(x,y,d) in enumerate(B)]
 _,fr,sc,e=floatsafe.work((n,rr));assert fr is not None,e
 print('positive gap control',n,'variant',4*g+v%4,'legal side',(sc+1)*math.sqrt(n),flush=True)
pick=W/'gap-pick.tsv'
with pick.open('w') as f:
 wr=csv.writer(f,delimiter='\t');wr.writerow(['kind','donor','n','corner','side','margin','dropped','variant','near','near_source','donor_licence'])
 wr.writerow(['b1',m,n,0,s+1,float(r['margin_before']),0,v,r['near'],r['donor_source'],r['donor_licence']])
before={p.name for p in (W/'q').glob('*.start.txt')}
b.cmd_starts(SimpleNamespace(held=str(W/'empty.csv'),details=str(W/'details.csv'),pairs=str(pick),dir=str(W/'q'),kinds='b1',max=.03,min=-1e9,min_abs=0,no_grid=True,per_n=0,limit=10,vfrom=0,variants=4,gaps='1,end',edge_min=0))
new=[]
for p in (W/'q').glob('*.start.txt'):
 if p.name in before:continue
 ident=p.name.removesuffix('.start.txt');job=p.with_name(ident+'.job.json');job.write_text(json.dumps(dict(start=p.name,priority=-100,gap_follow=True,reason='changed free-gap placement on first promising685 donor')));new.append(job.name)
subprocess.run(['rsync','-a','--include','*.start.txt','--include','*.job.json','--exclude','*',str(W/'q')+'/', 'boxC:scratch/squares-border-r24/q/'],check=True)
print('queued changed gap starts',new,flush=True)
