import pathlib,sys,json,shutil,time
sys.dont_write_bytecode=True
W=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(W),'.',str(W/'lane')]
import quench_walk
from seed_rule27 import file_checks,check_numbers
controls=check_numbers([503,811,861,983]);assert {r['n'] for r in controls if r['excluded']}=={503,983},controls
D=W/'withdrawn-seed-ancestors';D.mkdir(exist_ok=True);moved=[]
for p in list((W.parent/'near').glob('*.csv')):
 try:checks=file_checks(p,quench_walk)
 except Exception as e:
  print('cannot check',p.name,type(e).__name__,flush=True);continue
 bad=[r for r in checks if r['excluded']]
 if not bad:continue
 target=D/p.name;shutil.move(str(p),target)
 for q in [pathlib.Path(str(p)+'.json'),p.with_suffix('.json')]:
  if q.exists():shutil.move(str(q),D/q.name)
 (D/(p.name+'.seed-check.json')).write_text(json.dumps(bad));moved.append({'path':str(p),'checks':bad})
(W/'near-seed-purge27.json').write_text(json.dumps({'controls':controls,'withdrawn':moved},indent=2))
if moved:
 line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: WITHDRAW {len(moved)} own near files for original-seed ancestor share >=0.4. Original503 share1.0,983 share0.550356;811/861 controls share0.0. Complete path list and exact seed snapshot SHA256: {W}/near-seed-purge27.json. Files moved under {D}; do not follow these versions.\n'
 for log in [W.parent/'STATE.txt',W.parent.parent/'handoff-r31.log']:
  with log.open('a') as f:f.write(line)
print('near withdrawn',len(moved),'controls',controls,flush=True)
