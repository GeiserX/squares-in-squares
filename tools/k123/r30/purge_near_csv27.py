import pathlib,sys,json,shutil,time
sys.dont_write_bytecode=True
W=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane'),'.']
import quench_walk
from seed_rule27 import file_checks as seeds
from csv_rule27 import file_checks as layouts
D=W/'withdrawn-near-ancestor-share';D.mkdir(exist_ok=True);out=[]
for p in list((W.parent/'near').glob('*.csv')):
 checks=seeds(p,quench_walk)+layouts(p,quench_walk);bad=[r for r in checks if r['excluded']]
 if not bad:continue
 shutil.move(str(p),D/p.name)
 for q in [pathlib.Path(str(p)+'.json'),p.with_suffix('.json')]:
  if q.exists():shutil.move(str(q),D/q.name)
 out.append({'path':str(p),'excluded':bad});(D/(p.name+'.share.json')).write_text(json.dumps(bad))
 line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: WITHDRAW near {p}; complete ancestor or original-seed share >=0.4. Exact excluded proofs {D}/{p.name}.share.json. This includes the742 ancestor (share0.454177897574); do not follow this version.\n'
 for log in [W.parent/'STATE.txt',W.parent.parent/'handoff-r30.log']:
  with log.open('a') as f:f.write(line)
(W/'near-csv-purge27.json').write_text(json.dumps(out,indent=2));print('withdrawn near files',[r['path'] for r in out],flush=True)
