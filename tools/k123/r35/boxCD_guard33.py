"""Run at most four fresh-join workers and release their CPU above load nine."""
from pathlib import Path
import os,subprocess,signal,time,json,sys
R=Path.home()/'scratch/squares-k123';os.chdir(R);runtime=json.load((R/'runtime33.json').open());PY=runtime['python'];slots=['j22e','j22f','j22g','j22h'];workers={};paused=False;low=0
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
def rows():
 out=[]
 for line in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
  a=line.strip().split(None,2)
  if len(a)==3:out.append((int(a[0]),int(a[1]),a[2]))
 return out
def tree():
 ps=rows();ids={p.pid for p in workers.values() if p.poll() is None}
 while True:
  extra={pid for pid,pp,cmd in ps if pp in ids}-ids
  if not extra:return sorted(ids,reverse=True)
  ids|=extra
def signals(sig):
 for pid in tree():
  try:os.kill(pid,sig)
  except ProcessLookupError:pass
try:
 while time.time()<float((R/'search-deadline').read_text()) and not (R/'STOP33').exists():
  load=os.getloadavg()[0];size=1024*int(subprocess.check_output(['du','-sk',str(R)],text=True).split()[0])
  if load>9 or size>2_650_000_000:
   signals(signal.SIGSTOP);paused=True
   low=0
  elif paused:
   low=low+1 if load<8 and size<2_650_000_000 else 0
   if low>=2:signals(signal.SIGCONT);paused=False;low=0
  if not paused:
   ps=rows();owned=[(pid,cmd) for pid,pp,cmd in ps if cmd.endswith(tuple('qrun22.py '+s for s in slots))]
   assert len(owned)<=4,owned
   for slot in slots:
    p=workers.get(slot)
    if p is not None and p.poll() is None:continue
    assert not any(cmd.endswith('qrun22.py '+slot) for _,cmd in owned),'unadopted duplicate worker'
    with (R/'out'/(slot+'.log')).open('a') as f:p=subprocess.Popen(['nohup','nice','-n','5',PY,'-I','qrun22.py',slot],stdout=f,stderr=f,stdin=subprocess.DEVNULL,start_new_session=True)
    workers[slot]=p;(R/(slot+'.pid')).write_text(str(p.pid))
  state={'time':time.strftime('%FT%TZ',time.gmtime()),'load1':load,'bytes':size,'paused':paused,'workers':{s:p.pid for s,p in workers.items() if p.poll() is None},'ps_count':len([1 for pid,pp,cmd in rows() if cmd.endswith(tuple('qrun22.py '+s for s in slots))])}
  (R/'boxCD-guard33.json.tmp').write_text(json.dumps(state));(R/'boxCD-guard33.json.tmp').replace(R/'boxCD-guard33.json');print(json.dumps(state),flush=True);time.sleep(15)
finally:
 ids33=tree()
 for sig33 in [signal.SIGCONT,signal.SIGTERM,signal.SIGKILL]:
  for pid33 in sorted(set(ids33+tree()),reverse=True):
   try:os.kill(pid33,sig33)
   except ProcessLookupError:pass
  if sig33==signal.SIGTERM:time.sleep(.5)
