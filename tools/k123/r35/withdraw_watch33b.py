"""Recheck affected pinned sources when the live withdrawal catalogue changes."""
from pathlib import Path
import sys,os,json,hashlib,time,subprocess,traceback,signal
W=Path(__file__).resolve().parent;T=W.parent;sys.path[:0]=[str(W),str(W/'lane')]
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',K123_SOURCE_BUDGET30='1',K123_BASE_SECONDS32='45')
from policy27 import lines
from provenance24 import banned
from source25 import audit
from admission_budget30 import Deferred
push_needed=True;last=None;pending=set();oldpaths=set();denied=json.load((W/'refused-inputs26.json').open());sf=W/'withdraw-watch33.json'
if sf.exists():
 z=json.load(sf.open());last=z.get('stamp');oldpaths=set(z.get('active_paths',[]));pending=set(z.get('pending',[]))
def checked(args):
 p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,text=True)
 try:out,err=p.communicate(timeout=30)
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGKILL);p.communicate();raise
 if p.returncode:raise RuntimeError((args[0],p.returncode,err[-500:]))
def send():
 tmp=W/'refused-inputs26.tmp';tmp.write_text(json.dumps(denied));tmp.replace(W/'refused-inputs26.json')
 for host,socket,runtime in [('boxE','/tmp/squares-k123-r35-ssh','$SCRATCH/squares-base/venv/bin/python'),('boxD','/tmp/squares-k123-r35-boxD','$SCRATCH/squares-quench/venv/bin/python')]:
  if host=='boxD' and not (W/'boxCD-owned33').exists():continue
  checked(['scp','-q','-o','ControlPath='+socket,str(W/'refused-inputs26.json'),host+':scratch/squares-k123/refused-inputs26.incoming'])
  checked(['ssh','-S',socket,host,'cd $SCRATCH/squares-k123 && mv refused-inputs26.incoming refused-inputs26.json && '+runtime+' -I queue_revoke33.py'])
while time.time()<float((W/'deadline').read_text()):
 try:
  if push_needed:send();push_needed=False
  active=lines();stamp=hashlib.sha256(json.dumps(active,sort_keys=True).encode()).hexdigest();paths={p for p,line in active};changed=stamp!=last
  if last is None:last=stamp;oldpaths=paths;changed=False
  if changed or pending:
   checks=[];changedmap=False;newpending=set()
   for mp in W.glob('*/sources-*.json'):
    pool=mp.stem.removeprefix('sources-');meta=json.load(mp.open());prior=set(denied.get(pool,[]));current=set(prior)
    for n,c in meta.items():
     tag=pool+':'+n;text=json.dumps(c);affected=tag in pending or n in prior or any(p in text or any(q.endswith('/'+p) for q in c.get('checked_paths',[])) for p in paths-oldpaths)
     if not affected:continue
     try:ok=not banned(str(c.get('origin',''))) and audit(c) is not None
     except Deferred:ok=False;newpending.add(tag)
     if ok:current.discard(n)
     else:current.add(n)
     checks.append({'pool':pool,'n':int(n),'accepted':ok,'pending':tag in newpending})
    if current!=prior:changedmap=True
    if current:denied[pool]=sorted(current)
    else:denied.pop(pool,None)
   if changedmap:
    push_needed=True;send();push_needed=False
   pending=newpending;last=stamp;oldpaths=paths
   (W/'withdraw-watch-check33.json').write_text(json.dumps({'time':time.strftime('%FT%TZ',time.gmtime()),'checks':checks,'denied':denied},indent=2))
   if checks:
    with (T/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA SOURCE WATCH {len(checks)} affected pinned inputs rechecked, denied={sum(map(len,denied.values()))}, pending={len(pending)}; queue blocks sent to both owned boxes, log work/withdraw-watch33.log; hard16:25Z.\n')
  sf.write_text(json.dumps({'stamp':last,'active_paths':sorted(oldpaths),'pending':sorted(pending),'push_needed':push_needed}))
 except Exception:traceback.print_exc()
 sf.write_text(json.dumps({'stamp':last,'active_paths':sorted(oldpaths),'pending':sorted(pending),'push_needed':push_needed}))
 time.sleep(20)
