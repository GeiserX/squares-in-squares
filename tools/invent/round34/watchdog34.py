"""Round 34 watchdog: restart dead boxE slots (lesson 6g), stop jobs a peer passed by 1e-6 (lesson 6e)."""
import pathlib,sys,json,time,math,subprocess,traceback,os
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
import campaign34base as C
R='$SCRATCH/squares-base/venv/bin/python $SCRATCH/squares-invent-r34/wd_remote34.py '
def remote(args):return json.loads(subprocess.run(['ssh','boxE',R+args],check=True,capture_output=True,text=True,timeout=60).stdout)
stopped=set(C.load(W/'wd-stopped.json',[]))
while time.time()<C.ADMIT-60 and not(W/'STOP').exists():
 try:
  s=remote('status');jobs={j['id']:j for j in C.load(W/'jobs.json',[])};peer=C.peers()
  for slot,v in s.items():
   if not v['alive']:
    r=remote('restart '+slot);C.state('WATCHDOG restart boxE slot '+slot+' '+json.dumps(r))
    if r.get('job'):C.hand(f'RELEASE claim of job={r["job"]}: its boxE worker died and the job was re-queued.')
   job=jobs.get(v['job']or'')
   if not job or job['kind']=='control'or job['id']in stopped:continue
   n=job['n'];bar=job['bar']/math.sqrt(n)-1
   if peer[n]<bar-1e-6:
    r=remote('stop '+job['id']);stopped.add(job['id']);C.atomic(W/'wd-stopped.json',sorted(stopped))
    C.state(f'WATCHDOG stop {job["id"]}: live peer score {peer[n]:.15g} is more than 1e-6 below its dispatch bar {bar:.15g}; {json.dumps(r)}')
 except Exception:traceback.print_exc()
 time.sleep(60)
