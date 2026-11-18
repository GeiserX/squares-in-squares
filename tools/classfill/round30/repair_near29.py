"""Rewalk changed numerical endpoints after the source-reader corrections."""
from common29 import *
from history29 import trace
from ancestor_share29 import inspect
import signal
class AuditTimeout(BaseException):pass
def timeout(a,b):raise AuditTimeout()
signal.signal(signal.SIGALRM,timeout)
base,live,_=bar();repairs=read(W/'source-repairs.json',{});closed=read(W/'continued-near.json',{});seen=set();candidates=[]
for host in ['boxE','boxD']:
 for p in (W/host/'out').glob('near-*/*.json'):
  if not p.stem.isdigit():continue
  n=int(p.stem);j=read(p,{});tag=p.parent.name.removeprefix('near-');job=read(W/'jobs'/f'{tag}.json',{})
  if n<100 or tag in read(W/'prohibited-tags.json',[]) or '; leg ' in job.get('source',''):continue
  side=(1+j['finish_score'])*math.sqrt(n);move=j['finish_start_side']-side;excess=side-(1+live[n])*math.sqrt(n)
  if not (excess < -1e-10*math.sqrt(n) or (move>1e-5 and excess<0.0005 and job.get('seconds',0)<=300)):continue
  proof=next((W/'ancestry').glob(tag[1:13]+'*.json'),None)
  if proof:candidates.append((excess,tag,n,proof))
for _,tag,n,proof in sorted(candidates):
 if time.time()>=SEARCH_END:break
 if tag in repairs:continue
 a=read(proof);start=time.time();signal.alarm(45)
 try:h=trace(a['source'],a['licence'],dict(producer=a.get('metadata',{}),expanded_records=a['expanded'].get('records',[]),unresolved_csv=a['expanded'].get('unresolved_csv',[])),n)
 except AuditTimeout:note('SOURCE_REPAIR_TIMEOUT '+tag);continue
 finally:signal.alarm(0)
 if h['issues'] or h['excluded']:note(f'SOURCE_REPAIR_STILL_OPEN {tag} issues{len(set(h["issues"]))} excluded{h["excluded"]}');continue
 updated=dict(a);updated['expanded']=dict(a['expanded'],history=h);updated['repaired_from']=blob(proof)
 data=json.dumps(updated,sort_keys=True).encode();digest=hashlib.sha256(data).hexdigest();p=W/'repaired-proofs'/f'{digest}.json';atomic(p,updated)
 guard=inspect(p)
 if guard['excluded'] or guard['errors']:note('SOURCE_REPAIR_PUBLIC_REFUSAL '+tag);continue
 repairs[tag]=str(p);atomic(W/'source-repairs.json',repairs)
 note(f'SOURCE_REPAIR_COMPLETE {tag} n{n} seconds{time.time()-start:.3f} pins{len(h["snapshots"])} {p}')
print('REPAIRED',len(repairs),flush=True)
