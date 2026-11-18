"""Recheck exact deferred module versions after the held-credit boundary repair."""
import datetime,hashlib,json,pickle,signal,subprocess,sys,tarfile,time
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path[:0]=[str(H),str(H.parents[2])]
import provenance as P
import public_roots as Q
from ancestors import audit as ancestors
from prepare import fingerprint
W=Q.ROOT;R=W.parents[1]
class Bounded(BaseException):pass
def timeout(*a):raise Bounded('source recovery20s')
signal.signal(signal.SIGALRM,timeout)

def main():
 wanted={r['id']for r in json.loads((W/'base-audit.json').read_text())['dropped']if not r['reason'].startswith(('changed pinned','direct withdrawn'))}
 groups={}
 for key in ['n','m','s']:
  with tarfile.open(R/f'take-stair-c-r30/work/archive/{key}/final-copy.tar.gz')as tf:
   lib=pickle.loads(tf.extractfile('libbase/library.pkl').read());tables=pickle.loads(tf.extractfile('libbase/lens.pkl').read())
   for q in lib['mods']:
    if q['id']not in wanted:continue
    group=hashlib.sha256((q['src']+'\0'+q['licence']).encode()).hexdigest();groups.setdefault(group,{})[fingerprint(q)]=(q,tables.get(q['id']))
 results=[];count=0
 for group,entries in groups.items():
  if time.time()>float((W/'box/search-deadline').read_text()):break
  q=next(iter(entries.values()))[0]
  try:
   signal.setitimer(signal.ITIMER_REAL,20)
   assert P.clean(q['src'],q['licence']),'source proof refused'
   ancestors(q['src'],q['licence'],q.get('n'));record=Q.audit(dict(source=q['src'],licence=q['licence']))
   signal.setitimer(signal.ITIMER_REAL,0)
  except (OSError,ValueError,KeyError,AssertionError,RecursionError,Bounded)as ex:
   signal.setitimer(signal.ITIMER_REAL,0);results.append(dict(group=group,admitted=False,reason=str(ex)));print('DEFER',len(results),len(groups),str(ex)[:140],flush=True);continue
  values=list(entries.values())
  for offset in range(0,len(values),3):
   pack=values[offset:offset+3];p=W/'donors'/f'r32-live-source-recovery-{group[:12]}-{offset}.pkl'
   pickle.dump(dict(mods=[q for q,t in pack],lens={q['id']:t for q,t in pack if t is not None},origin='exact r30 module after held-credit boundary repair'),p.open('wb'))
   for host in ['boxC','boxD','boxE']:subprocess.run(['rsync','-a',str(p),host+':scratch/squares-stair-c/inbox/'],capture_output=True,timeout=40,check=True)
  count+=len(entries);results.append(dict(group=group,admitted=True,states=len(entries),record=record));print('RESTORED',len(results),len(groups),len(entries),'total',count,flush=True)
 (W/'source-recovery.json').write_text(json.dumps(dict(groups=results,restored=count),indent=2))
 with(W.parent/'STATE.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA FINISH exact source retry: '+str(count)+' module states. All current direct-public and source controls retained. Log work/source-recovery.log; no old take files changed.\n')
if __name__=='__main__':main()
