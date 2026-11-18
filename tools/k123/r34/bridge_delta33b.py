"""Copy the extra box's numerical data through the collector into the existing certification pipeline."""
from pathlib import Path
import subprocess,json,os,time,sys,fcntl,signal
W=Path(__file__).resolve().parent;T=W.parent;D=W/'boxD-bridge33';D.mkdir(exist_ok=True)
SSH0=['ssh','-S','/tmp/squares-k123-r34-ssh','boxE'];SSH1=['ssh','-S','/tmp/squares-k123-r34-boxD','boxD'];SCP0=['scp','-q','-o','ControlPath=/tmp/squares-k123-r34-ssh'];SCP1=['scp','-q','-o','ControlPath=/tmp/squares-k123-r34-boxD']
def run(args,**kw):
 timeout=kw.pop('timeout',90);check=kw.pop('check',True)
 if kw.pop('capture_output',False):kw['stdout']=kw['stderr']=subprocess.PIPE
 p=subprocess.Popen(args,start_new_session=True,**kw)
 try:out,err=p.communicate(timeout=timeout)
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGKILL);p.communicate();raise
 result=subprocess.CompletedProcess(args,p.returncode,out,err)
 if check:result.check_returncode()
 return result
def once(export=True):
 if export:
  ack=run(SSH1+['cd $SCRATCH/squares-k123 && $SCRATCH/squares-quench/venv/bin/python -I boxCD_inventory33.py'],capture_output=True,text=True)
  confirmed=json.loads(ack.stdout);assert isinstance(confirmed,list) and all(isinstance(p,str) for p in confirmed)
  (D/'boxD-received33.json').write_text(json.dumps(confirmed))
  run(SCP0+[str(D/'boxD-received33.json'),'boxE:scratch/squares-k123/boxD-received33.json.incoming'])
  r=run(SSH0+['cd $SCRATCH/squares-k123 && mv boxD-received33.json.incoming boxD-received33.json && $SCRATCH/squares-base/venv/bin/python -I boxCD_export_delta33.py'],capture_output=True,text=True);receipt=json.loads(r.stdout.strip());(D/'export33.json').write_text(json.dumps(receipt))
  run(SCP0+['boxE:scratch/squares-k123/boxCD-export33.tgz',str(D/'boxCD-export33.tgz')])
  import hashlib
  assert hashlib.sha256((D/'boxCD-export33.tgz').read_bytes()).hexdigest()==receipt['sha256']
  run(SCP1+[str(D/'boxCD-export33.tgz'),'boxD:scratch/squares-k123/'])
  run(SSH1+['cd $SCRATCH/squares-k123 && $SCRATCH/squares-quench/venv/bin/python -I boxCD_import33.py '+receipt['sha256']],stdout=subprocess.DEVNULL)
 for slot in ['j22e','j22f','j22g','j22h']:
  out=D/'out'/slot;out.mkdir(parents=True,exist_ok=True)
  r=run(['rsync','-az','-e','ssh -S /tmp/squares-k123-r34-boxD','boxD:scratch/squares-k123/out/'+slot+'/',str(out)+'/'],timeout=90,capture_output=True,text=True,check=False)
  if r.returncode and 'No such file' not in r.stderr:raise RuntimeError(r.stderr)
  if not list(out.iterdir()):continue
  run(SSH0+['mkdir -p $SCRATCH/squares-k123/out/'+slot])
  run(['rsync','-az','-e','ssh -S /tmp/squares-k123-r34-ssh',str(out)+'/','boxE:scratch/squares-k123/out/'+slot+'/'])
 run(SCP1+['boxD:scratch/squares-k123/boxCD-guard33.json',str(D/'boxCD-guard33.json')],timeout=30,capture_output=True,check=False)
 if (D/'boxCD-guard33.json').exists():
  g=json.load((D/'boxCD-guard33.json').open());old=json.load((W/'boxCD-load-last33.json').open()) if (W/'boxCD-load-last33.json').exists() else {}
  if g.get('paused')!=old.get('paused'):
   line=time.strftime('%FT%TZ',time.gmtime())+f' boxD load guard paused={g["paused"]}, load1={g["load1"]:.3f}, ownworkers={g["ps_count"]}; bridge log work/bridge-boxCD33.log, hard07:25Z.\n'
   with (T/'STATE.txt').open('a') as f:f.write(line)
  (W/'boxCD-load-last33.json').write_text(json.dumps(g))
 print(time.strftime('%FT%TZ',time.gmtime()),'boxD bridge copied',('pools='+str(receipt['pools'])+', new='+str(receipt.get('new_pools','?'))+', bytes='+str(receipt['bytes']) if export else 'final outputs'),flush=True)
if __name__=='__main__':
 with (W/'bridge-boxCD33.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  if '--once' in sys.argv:once('--no-export' not in sys.argv)
  else:
   while time.time()<float((W/'deadline').read_text()):
    try:once(time.time()<float((W/'search-deadline').read_text()))
    except Exception as e:print(time.strftime('%FT%TZ',time.gmtime()),'BRIDGE ERROR',repr(e),flush=True)
    time.sleep(30)
