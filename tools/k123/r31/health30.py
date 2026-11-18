"""Keep the four declared numerical slots alive until intake closes."""
from pathlib import Path
import subprocess,time,os,json
W=Path(__file__).resolve().parent;SSH=['ssh','-o','ControlPath=/tmp/squares-k123-r31-ssh','-o','ConnectTimeout=10','boxE']
while time.time()<float((W/'search-deadline').read_text()):
 try:
  control=W/'taskdone/verify-variant31-control.json'
  if control.exists() and json.load(control.open()).get('rc')==0 and not (W/'wide31-enabled').exists():
   subprocess.run(SSH+['cd $SCRATCH/squares-k123 && $SCRATCH/squares-base/venv/bin/python -I restart-wide30.py'],timeout=40,check=True)
   (W/'wide31-enabled').touch()
   with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxE ADOPT one controlled1.005 finish in existing j22d slot after numerical444 control passed. Deadline00:15Z.\n')
  ps=subprocess.check_output(SSH+['ps -axo pid,ppid,command'],text=True,timeout=30)
  for worker in ['j22a','j22b','j22d','third']:
   needle='third22.py' if worker=='third' else 'qrun22.py '+worker
   # Restrict matching to a Python process and exact script arguments.
   matches=[l for l in ps.splitlines() if 'python' in l.lower() and l.rstrip().endswith(needle)]
   if matches:continue
   args='third22.py' if worker=='third' else 'qrun22.py '+worker
   cmd=f'cd $SCRATCH/squares-k123 && nohup nice -n 5 $SCRATCH/squares-base/venv/bin/python -I {args} >> out/{worker}.log 2>&1 < /dev/null &'
   subprocess.run(SSH+[cmd],timeout=30,check=True)
   with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' boxE RESTART missing numerical slot {worker}; no live root matched. Log out/{worker}.log; deadline00:15Z.\n')
 except Exception as e:print(time.strftime('%FT%TZ',time.gmtime()),repr(e),flush=True)
 for _ in range(3):
  if time.time()>=float((W/'search-deadline').read_text()):break
  time.sleep(50)
