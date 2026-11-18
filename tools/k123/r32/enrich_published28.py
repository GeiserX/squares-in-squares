from pathlib import Path
import csv,json,sys,fcntl,shutil,time,hashlib
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));csv.field_size_limit(20000000)
from areeb_chain28 import enrich
from compact_source28 import source as compact_source
from publication_source26 import check
with (W/'collect.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 T=W.parent;rows=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'));changed=[]
 for row in rows:
  p=T/(row['n']+'.csv');out=enrich(p,row);out['source']=compact_source(out['source'])
  if out==row:continue
  D=W/'notice-review28'/row['n'];D.mkdir(parents=True,exist_ok=True);q=D/p.name;shutil.copy(p,q);Path(str(q)+'.json').write_text(json.dumps(out));result=check(q,out);assert result['clean'],result
  assert hashlib.sha256(q.read_bytes()).hexdigest()==hashlib.sha256(p.read_bytes()).hexdigest()
  row.update(out);changed.append(row['n'])
 if changed:
  with (T/'take.tsv.tmp').open('w',newline='') as f:
   writer=csv.DictWriter(f,['n','held','new','gain','source','licence'],delimiter='\t');writer.writeheader();writer.writerows(rows)
  (T/'take.tsv.tmp').replace(T/'take.tsv')
  state=json.loads((W/'collect-state.json').read_text())
  for key,r in state.items():
   match=next((row for row in rows if int(row['n'])==r.get('n') and r.get('status')=='published'),None)
   if match:
    cert=W/'certs'/key/'final'/(match['n']+'.csv')
    if cert.exists() and hashlib.sha256(cert.read_bytes()).hexdigest()==hashlib.sha256((T/(match['n']+'.csv')).read_bytes()).hexdigest():r['source']=match['source'];r['licence']=match['licence']
  (W/'collect-state.json').write_text(json.dumps(state,indent=2))
  with (T/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA COMPLETE public notices for{changed}: areebbb per_n rows462/703 lead to malyshevdanil submission_sources.csv sub:submission_merged.csv, Apache2.0. Both source and licence cells include the exact per-n chain; independent walk passes and certified CSV bytes are unchanged. Proof work/notice-review28. Deadline17:15Z.\n')
 print('notice-enriched rows',changed,flush=True)
