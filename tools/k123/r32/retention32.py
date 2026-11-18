"""Recheck retained rows when the active withdrawal set changes."""
from pathlib import Path
import csv,json,hashlib,time,importlib
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent

def refresh(state):
 from policy27 import lines
 stamp=hashlib.sha256(json.dumps(lines(),sort_keys=True).encode()).hexdigest();marker=W/'retention-withdraw-stamp32'
 if marker.exists() and marker.read_text()==stamp:return
 import walker30
 code=(W/'walker30.py').stat().st_mtime_ns
 if getattr(walker30,'_retention_code32',None)!=code:walker30=importlib.reload(walker30);walker30._retention_code32=code
 from current_walk29 import configure
 walker=configure(walker30);rows=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'));kept=[];checks=[]
 for row in rows:
  n=int(row['n']);p=T/f'{n}.csv';sha=hashlib.sha256(p.read_bytes()).hexdigest();result=walker.check(str(p));checks.append({'n':n,'sha256':sha,'clean':result['clean'],'hits':result['hits']})
  if result['clean']:kept.append(row);continue
  D=W/'withdrawn';D.mkdir(exist_ok=True);(D/f'{n}-{sha}-retention-row.json').write_text(json.dumps(row,indent=2));(D/f'{n}-{sha}-retention-check.json').write_text(json.dumps(result,indent=2))
  for record in state.values():
   if record.get('n')==n and record.get('status')=='published':record.update(status='withdrawn-upstream32',withdrawal_reason=result['hits'])
  line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: WITHDRAW own n={n} exact bytes sha256 {sha}, {p}; active-withdrawal refresh refused its recorded tree: '+str(result['hits'][:2])+'; dropped from take.tsv, CSV retained for recorded descendants.\n'
  with (S/'handoff-r32.log').open('a') as f:f.write(line)
  with (T/'STATE.txt').open('a') as f:f.write(line)
 if len(kept)!=len(rows):
  with (T/'take.tsv.tmp').open('w') as f:
   wr=csv.DictWriter(f,['n','held','new','gain','source','licence'],delimiter='\t');wr.writeheader();wr.writerows(kept)
  (T/'take.tsv.tmp').replace(T/'take.tsv')
 (W/'retention-last-check32.json').write_text(json.dumps({'stamp':stamp,'time':time.strftime('%FT%TZ',time.gmtime()),'rows':checks},indent=2));marker.write_text(stamp)

if __name__=='__main__':
 import fcntl
 with (W/'collect.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);sp=W/'collect-state.json';state=json.load(sp.open()) if sp.exists() else {};before=(T/'take.tsv').read_bytes();refresh(state);tmp=sp.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2));tmp.replace(sp);print(json.dumps({'take_changed':before!=(T/'take.tsv').read_bytes()}))
