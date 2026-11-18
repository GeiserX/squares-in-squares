"""Drain current join jobs, then switch boxE to disjoint fresh recipe hashes."""
from pathlib import Path
import subprocess,time,os,signal,json,fcntl
R=Path.home()/'scratch/squares-k123';os.chdir(R);PY=str(Path.home()/'scratch/squares-base/venv/bin/python')
lock=(R/'update-boxE33.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
def rows():
 out=[]
 for line in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
  a=line.strip().split(None,2)
  if len(a)==3:out.append((int(a[0]),int(a[1]),a[2]))
 return out
slots=['j22a','j22b','j22d'];old=[pid for pid,pp,cmd in rows() if any(cmd.endswith('python -I qrun22.py '+s) or cmd.endswith('python -I qrun22.py '+s+' --once') for s in slots+['j22c'])];deadline=(R/'search-deadline').read_text();(R/'search-deadline').write_text(str(time.time()-1));end=time.time()+220
try:
 while time.time()<end:
  live={pid for pid,pp,cmd in rows()}
  remaining=sorted(set(old)&live)
  if not remaining:break
  print('draining current join workers',remaining,flush=True);time.sleep(2)
 assert not (set(old)&{pid for pid,pp,cmd in rows()}),'join drain exceeded cap'
finally:
 (R/'search-deadline.tmp').write_text(deadline);(R/'search-deadline.tmp').replace(R/'search-deadline')
started={}
for slot in slots:
 assert not [pid for pid,pp,cmd in rows() if cmd.endswith('python -I qrun22.py '+slot)]
 with (R/'out'/(slot+'.log')).open('a') as f:p=subprocess.Popen(['nohup','nice','-n','5',PY,'-I','qrun22.py',slot],stdout=f,stderr=f,stdin=subprocess.DEVNULL,start_new_session=True)
 (R/(slot+'.pid')).write_text(str(p.pid));started[slot]=p.pid
(R/'partition-ready33.json').write_text(json.dumps({'time':time.strftime('%FT%TZ',time.gmtime()),'drained':old,'started':started}));print('partition-ready',started,flush=True)
