from pathlib import Path
import sys,json,csv,hashlib,shutil,fcntl,time
W=Path(__file__).resolve().parent;T=W.parent;sys.path[:0]=[str(W),str(W/'lane')];csv.field_size_limit(1<<28)
from bind_row30 import bind
from publication_source26 import check
rows=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'));row=next(r for r in rows if r['n']=='295');digest=hashlib.sha256((T/'295.csv').read_bytes()).hexdigest();state=json.load((W/'collect-state.json').open());key,r=next((k,r) for k,r in state.items() if r.get('status')=='published' and r['n']==295 and r.get('score')==float(row['new']));pool=r['pool'];meta=json.load((W/pool/f'sources-{pool}.json').open());new=bind(row,meta,r['donors'],pool,key+'-recursive');D=W/'recursive-control295';D.mkdir(exist_ok=True);p=D/'295.csv';shutil.copy(T/'295.csv',p);result=check(p,new);assert result['clean'],result
assert not any('take-quench-r30/584.csv' in s for s in result.get('missing',[])),result
lock=(W/'collect.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
assert hashlib.sha256((T/'295.csv').read_bytes()).hexdigest()==digest
current=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'));next(x for x in current if x['n']=='295')['source']=new['source'];states=json.load((W/'collect-state.json').open());states[key]['source']=new['source']
with (T/'take.tsv.tmp').open('w') as h:
 wr=csv.DictWriter(h,['n','held','new','gain','source','licence'],delimiter='\t');wr.writeheader();wr.writerows(current)
(T/'take.tsv.tmp').replace(T/'take.tsv');(W/'collect-state.tmp').write_text(json.dumps(states));(W/'collect-state.tmp').replace(W/'collect-state.json')
rec={'n':295,'certificate_sha256':digest,'clean':result['clean'],'files':result['files'],'missing':result.get('missing',[]),'old584_edge_replaced':True};(W/'recursive295-control30.json').write_text(json.dumps(rec,indent=2));print(json.dumps(rec),flush=True)
with (T/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA BIND recursive queue-time parent snapshots for295. Source walk passes; superseded quench584 edge replaced by exact CSV and producer-row snapshots. Certificate bytes unchanged '+digest+'. Deadline17:45Z.\n')
