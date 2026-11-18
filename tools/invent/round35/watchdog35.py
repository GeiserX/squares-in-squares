"""Round 35 watchdog: restart dead boxE slots (lesson 6g), stop jobs a peer passed by 1e-6 (lesson 6e)."""
import pathlib,sys,json,time,math,subprocess,traceback,os
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
import campaign35base as C
def remote(args,h=None):
 h=h or HOSTNOW[0];return json.loads(subprocess.run(['ssh',h,C.rpy(h)+' $SCRATCH/squares-invent-r35/wd_remote35.py '+args],check=True,capture_output=True,text=True,timeout=60).stdout)
HOSTNOW=[C.HOST]
stopped=set(C.load(W/'wd-stopped.json',[]))
while time.time()<C.ADMIT-60 and not(W/'STOP').exists():
 for _h in C.HOSTS:
  HOSTNOW[0]=_h
  try:
   s=remote('status');jobs={j['id']:j for j in C.load(W/'jobs.json',[])};peer=C.peers()
   for slot,v in s.items():
    if not v['alive']:
     r=remote('restart '+slot);C.state('WATCHDOG restart '+_h+' slot '+slot+' '+json.dumps(r))
     if r.get('job'):C.hand(f'RELEASE claim of job={r["job"]}: its worker died and the job was re-queued.')
    job=jobs.get(v['job']or'')
    if not job or job['kind']=='control'or job['id']in stopped:continue
    n=job['n'];bar=job['bar']/math.sqrt(n)-1
    if job['kind']=='fresh'and C.producer_certified(job.get('origin',''),n):
     r=remote('stop '+job['id']);stopped.add(job['id']);C.atomic(W/'wd-stopped.json',sorted(stopped))
     C.state(f'WATCHDOG stop {job["id"]}: its producer lane certified n={n} (lesson 6e); {json.dumps(r)}');continue
    if peer[n]<bar-1e-6:
     r=remote('stop '+job['id']);stopped.add(job['id']);C.atomic(W/'wd-stopped.json',sorted(stopped))
     C.state(f'WATCHDOG stop {job["id"]}: live peer score {peer[n]:.15g} is more than 1e-6 below its dispatch bar {bar:.15g}; {json.dumps(r)}')
  except Exception:traceback.print_exc()
 time.sleep(60)
