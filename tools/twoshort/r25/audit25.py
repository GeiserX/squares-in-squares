from pathlib import Path
import csv,json,sys,math,hashlib
csv.field_size_limit(16000000)
W=Path(__file__).parent;B=W.parent.parent;T=W.parent;R=W/'boxE25';sys.path.insert(0,str(W));sys.path.insert(0,str(W/'lane'));from shape974 import load;import floatsafe
from bar25 import bars as policy_bars,policy,reference
held,held22,sam_bar,free_bar=policy_bars();bar=free_bar
pending=[];summ=[];cachepath=W/'q-checks.json';cache=json.load(open(cachepath)) if cachepath.exists() else {}
for p in R.glob('q/*/meta.json'):
 j=json.load(open(p))
 if j.get('quench_rc')!=0:continue
 n=j['n'];q=p.parent/Path(j['quenched_file']).name
 if not q.exists():continue
 digest=hashlib.sha256(q.read_bytes()).hexdigest()
 if digest not in cache:
  rows=[{k:r[k] for k in ['n','square_id','x','y','angle']} for r in csv.DictReader(open(q))];_,fr,s,e=floatsafe.work((n,rows));cache[digest]=dict(file=str(q),n=n,score=s,valid=fr is not None,dilation=e)
 if not cache[digest]['valid']:print('INVALID QUENCH',q,flush=True);continue
 pol=policy(j['source'],j['licence']);livebar=free_bar[n] if pol['status']=='none' else sam_bar[n]
 _,side=load(q);rawscore=side/math.sqrt(n)-1
 if rawscore>=livebar-1e-10:continue
 s=cache[digest]['score'];record=dict(n=n,meta=str(p),file=str(q),score=s,gain=held[n]-s,beyond_live=livebar-s,valid=cache[digest]['valid'],source=j['source'],licence=j['licence'])
 pending.append(record)
cachepath.write_text(json.dumps(cache,indent=2));print('completed quench checks',len(cache),'invalid',sum(not c['valid'] for c in cache.values()))
(W/'pending-proofs.json').write_text(json.dumps(pending,indent=2));print('qualifying completed quenches needing proof',[(d['n'],d['gain'],d['beyond_live']) for d in pending])
