"""Feed both extra boxes and return their receipts to boxE certification queue."""
from pathlib import Path
import subprocess,json,time,sys,hashlib,fcntl,traceback
W=Path(__file__).resolve().parent;T=W.parent
boxes={'boxC':['j22i','j22j'],'boxD':['j22e','j22f','j22g','j22h','j22k']}
def prepare(args):
 args=list(args)
 if args[0]=='ssh':args[1:1]=['-S','/tmp/squares-k123-r35-'+args[1]]
 elif args[0] in ['scp','rsync']:
  host=next((a.split(':',1)[0] for a in args if a.startswith(('boxC:','boxD:','boxE:'))),None)
  if host:
   sock='/tmp/squares-k123-r35-'+host
   args[1:1]=['-o','ControlPath='+sock] if args[0]=='scp' else ['-e','ssh -S '+sock]
 return args
def run(args,**kw):return subprocess.run(prepare(args),check=True,timeout=90,**kw)
def once(export=True):
 if export:
  r=run(['ssh','boxE','cd $SCRATCH/squares-k123 && $SCRATCH/squares-base/venv/bin/python -I boxCD_export33.py'],capture_output=True,text=True);receipt=json.loads(r.stdout.strip())
  run(['scp','-q','boxE:scratch/squares-k123/boxCD-export33.tgz',str(W/'boxCD-export33.tgz')]);assert hashlib.sha256((W/'boxCD-export33.tgz').read_bytes()).hexdigest()==receipt['sha256']
 for host,slots in boxes.items():
  cfg=json.load((W/host/'runtime33.json').open());D=W/(host+'-bridge34');D.mkdir(exist_ok=True)
  if export:
   run(['scp','-q',str(W/'boxCD-export33.tgz'),host+':scratch/squares-k123/'])
   run(['ssh',host,f'cd $SCRATCH/squares-k123 && {cfg["python"]} -I boxCD_import33.py '+receipt['sha256']],stdout=subprocess.DEVNULL)
  for slot in slots:
   out=D/'out'/slot;out.mkdir(parents=True,exist_ok=True)
   # Freeze the completion list before copying its already-closed output files.
   pinned=D/(slot+'-done-pinned34.jsonl')
   cp=subprocess.run(prepare(['scp','-q',host+':scratch/squares-k123/out/'+slot+'/done.jsonl',str(pinned)+'.tmp']),timeout=30,capture_output=True,text=True)
   if cp.returncode:
    if 'No such file' in cp.stderr:continue
    raise RuntimeError(cp.stderr)
   Path(str(pinned)+'.tmp').replace(pinned)
   r=subprocess.run(prepare(['rsync','-az','--exclude=done.jsonl',host+':scratch/squares-k123/out/'+slot+'/',str(out)+'/']),timeout=90,capture_output=True,text=True)
   if r.returncode:raise RuntimeError(r.stderr)
   run(['ssh','boxE','mkdir -p $SCRATCH/squares-k123/out/'+slot])
   run(['rsync','-az','--exclude=done.jsonl',str(out)+'/','boxE:scratch/squares-k123/out/'+slot+'/'])
   # A collector can see a completion only after every associated file arrives.
   run(['scp','-q',str(pinned),'boxE:scratch/squares-k123/out/'+slot+'/done.jsonl.incoming34'])
   run(['ssh','boxE','cd $SCRATCH/squares-k123/out/'+slot+' && mv done.jsonl.incoming34 done.jsonl'])
  run(['scp','-q',host+':scratch/squares-k123/guard34.json',str(D/'guard34.json')])
  print(time.strftime('%FT%TZ',time.gmtime()),host,'bridge complete',json.load((D/'guard34.json').open()),flush=True)
if __name__=='__main__':
 for host in ['boxC','boxD','boxE']:
  sock='/tmp/squares-k123-r35-'+host
  probe=subprocess.run(['ssh','-S',sock,'-O','check',host],capture_output=True,timeout=10)
  if probe.returncode:subprocess.run(['ssh','-MNf','-o','ControlPath='+sock,'-o','ControlMaster=auto','-o','ControlPersist=600',host],check=True,timeout=20)
 with (W/'bridge34.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if '--once' in sys.argv:once('--no-export' not in sys.argv)
  else:
   while time.time()<float((W/'deadline').read_text()) and not (W/'bridge-stop34').exists():
    try:once(time.time()<float((W/'search-deadline').read_text()))
    except Exception:traceback.print_exc()
    time.sleep(30)
