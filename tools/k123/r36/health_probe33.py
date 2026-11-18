"""Report and, only with zero surviving wrappers, recover the owned boxE pool."""
from pathlib import Path
import subprocess,json,time,sys,fcntl
R=Path.home()/'scratch/squares-k123'
def status():
 rows=[]
 for l in subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines()[1:]:
  a=l.strip().split(None,1)
  if len(a)==2:rows.append((int(a[0]),a[1]))
 guard=[pid for pid,c in rows if c.endswith('boxE_guard33.py')];roots=[pid for pid,c in rows if c.endswith(('qrun22.py j22a','qrun22.py j22b','qrun22.py j22d','third22.py'))]
 return {'time':time.strftime('%FT%TZ',time.gmtime()),'guard':guard,'roots':roots,'recovered':False}
s=status()
if '--recover' in sys.argv and not s['guard'] and not s['roots'] and time.time()<float((R/'deadline').read_text()):
 with (R/'health-recovery33.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);s=status()
  if not s['guard'] and not s['roots']:
   with (R/'out/boxE-guard33.log').open('a') as h:p=subprocess.Popen(['nohup','nice','-n','5',str(Path.home()/'scratch/squares-base/venv/bin/python'),'-I','boxE_guard33.py'],cwd=R,stdin=subprocess.DEVNULL,stdout=h,stderr=subprocess.STDOUT,start_new_session=True)
   (R/'boxE_guard33.py.pid').write_text(str(p.pid));s['recovered']=True;s['new_guard']=p.pid
print(json.dumps(s))
