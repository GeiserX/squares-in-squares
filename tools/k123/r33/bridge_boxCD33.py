"""Copy the extra box's numerical data through the collector into the existing certification pipeline."""
from pathlib import Path
import subprocess,json,os,time,sys,fcntl
W=Path(__file__).resolve().parent;T=W.parent;D=W/'boxD-bridge33';D.mkdir(exist_ok=True)
SSH0=['ssh','-S','/tmp/squares-k123-r33-ssh','boxE'];SSH1=['ssh','-S','/tmp/squares-k123-r33-boxD','boxD'];SCP0=['scp','-q','-o','ControlPath=/tmp/squares-k123-r33-ssh'];SCP1=['scp','-q','-o','ControlPath=/tmp/squares-k123-r33-boxD']
def run(args,**kw):return subprocess.run(args,check=True,timeout=90,**kw)
def once(export=True):
 if export:
  r=run(SSH0+['cd $SCRATCH/squares-k123 && $SCRATCH/squares-base/venv/bin/python -I boxCD_export33.py'],capture_output=True,text=True);receipt=json.loads(r.stdout.strip());(D/'export33.json').write_text(json.dumps(receipt))
  run(SCP0+['boxE:scratch/squares-k123/boxCD-export33.tgz',str(D/'boxCD-export33.tgz')])
  import hashlib
  assert hashlib.sha256((D/'boxCD-export33.tgz').read_bytes()).hexdigest()==receipt['sha256']
  run(SCP1+[str(D/'boxCD-export33.tgz'),'boxD:scratch/squares-k123/'])
  run(SSH1+['cd $SCRATCH/squares-k123 && $SCRATCH/squares-quench/venv/bin/python -I boxCD_import33.py '+receipt['sha256']],stdout=subprocess.DEVNULL)
 for slot in ['j22e','j22f','j22g','j22h']:
  out=D/'out'/slot;out.mkdir(parents=True,exist_ok=True)
  r=subprocess.run(['rsync','-az','-e','ssh -S /tmp/squares-k123-r33-boxD','boxD:scratch/squares-k123/out/'+slot+'/',str(out)+'/'],timeout=90,capture_output=True,text=True)
  if r.returncode and 'No such file' not in r.stderr:raise RuntimeError(r.stderr)
  if not list(out.iterdir()):continue
  run(SSH0+['mkdir -p $SCRATCH/squares-k123/out/'+slot])
  run(['rsync','-az','-e','ssh -S /tmp/squares-k123-r33-ssh',str(out)+'/','boxE:scratch/squares-k123/out/'+slot+'/'])
 subprocess.run(SCP1+['boxD:scratch/squares-k123/boxCD-guard33.json',str(D/'boxCD-guard33.json')],timeout=30,capture_output=True)
 if (D/'boxCD-guard33.json').exists():
  g=json.load((D/'boxCD-guard33.json').open());old=json.load((W/'boxCD-load-last33.json').open()) if (W/'boxCD-load-last33.json').exists() else {}
  if g.get('paused')!=old.get('paused'):
   line=time.strftime('%FT%TZ',time.gmtime())+f' boxD load guard paused={g["paused"]}, load1={g["load1"]:.3f}, ownworkers={g["ps_count"]}; bridge log work/bridge-boxCD33.log, hard00:15Z.\n'
   with (T/'STATE.txt').open('a') as f:f.write(line)
  (W/'boxCD-load-last33.json').write_text(json.dumps(g))
 print(time.strftime('%FT%TZ',time.gmtime()),'boxD bridge copied',('pools='+str(receipt['pools']) if export else 'final outputs'),flush=True)
if __name__=='__main__':
 with (W/'bridge-boxCD33.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  if '--once' in sys.argv:once('--no-export' not in sys.argv)
  else:
   while time.time()<float((W/'deadline').read_text()):
    try:once(time.time()<float((W/'search-deadline').read_text()))
    except Exception as e:print(time.strftime('%FT%TZ',time.gmtime()),'BRIDGE ERROR',repr(e),flush=True)
    time.sleep(30)
