"""Keep exactly four boxE numerical slots alive and record any early exit."""
from pathlib import Path
import subprocess,os,time,json,signal,re
R=Path.home()/'scratch/squares-k123';os.chdir(R);PY=str(Path.home()/'scratch/squares-base/venv/bin/python');os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
spec={'j22a':['qrun22.py','j22a'],'j22b':['qrun22.py','j22b'],'j22d':['qrun22.py','j22d'],'third':['third22.py']};workers={};reported=set()
def rows():
 out=[]
 for line in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
  a=line.strip().split(None,2)
  if len(a)==3:out.append((int(a[0]),int(a[1]),a[2]))
 return out
def live_roots(ps):
 return [(pid,slot) for pid,pp,cmd in ps for slot,args in spec.items() if cmd.endswith(' '.join(args))]
def descendants(roots,ps):
 ids=set(roots)
 while True:
  more={pid for pid,pp,cmd in ps if pp in ids}-ids
  if not more:return ids
  ids|=more
def orphan_cleanup(ps):
 active=descendants([p.pid for p in workers.values() if p.poll() is None],ps);cand={pid for pid,pp,cmd in ps if pid not in active and pp==1 and re.search(r'fq quench|lane/k123_turn.py|fq2.py|verify26.py|cert_once22.py|phase_[a-z0-9_]+.py|qrun22.py j22c --once',cmd)}
 if not cand:return []
 out=subprocess.run(['/usr/sbin/lsof','-a','-p',','.join(map(str,sorted(cand))),'-d','cwd','-Fpn'],text=True,capture_output=True,timeout=15).stdout;owned=set();pid=None
 for line in out.splitlines():
  if line.startswith('p') and line[1:].isdigit():pid=int(line[1:])
  elif line.startswith('n') and pid in cand and (line[1:]==str(R) or line[1:].startswith(str(R)+'/')):owned.add(pid)
 owned=descendants(owned,ps)
 for sig in [signal.SIGTERM,signal.SIGKILL]:
  for pid in sorted(owned,reverse=True):
   try:os.kill(pid,sig)
   except ProcessLookupError:pass
  if sig==signal.SIGTERM:time.sleep(.1)
 return sorted(owned)
assert not live_roots(rows()),'existing numerical wrappers must be adopted, not duplicated'
try:
 while time.time()<float((R/'deadline').read_text()):
  ps=rows();live=live_roots(ps);assert len(live)<=4,live;orphaned=orphan_cleanup(ps)
  for slot,args in spec.items():
   p=workers.get(slot)
   if p is not None and p.poll() is None:continue
   if p is not None and p.pid not in reported:
    event={'time':time.strftime('%FT%TZ',time.gmtime()),'slot':slot,'pid':p.pid,'returncode':p.returncode,'orphans_stopped':orphaned};reported.add(p.pid)
    with (R/'boxE-exits33.jsonl').open('a') as h:h.write(json.dumps(event)+'\n')
    print(json.dumps(event),flush=True)
   if slot!='third' and time.time()>=float((R/'search-deadline').read_text()):continue
   assert not any(s==slot for pid,s in live),'unadopted duplicate numerical wrapper'
   with (R/'out'/('supervised-'+slot+'33.log')).open('a') as h:p=subprocess.Popen(['nohup','nice','-n','5',PY,'-I',*args],stdin=subprocess.DEVNULL,stdout=h,stderr=subprocess.STDOUT,start_new_session=True)
   workers[slot]=p;(R/('third22.py.pid' if slot=='third' else slot+'.pid')).write_text(str(p.pid));live.append((p.pid,slot))
  state={'time':time.strftime('%FT%TZ',time.gmtime()),'workers':{slot:p.pid for slot,p in workers.items() if p.poll() is None},'ps_count':len(live_roots(rows())),'orphans_stopped':orphaned};assert state['ps_count']<=4;tmp=R/'boxE-guard33.tmp';tmp.write_text(json.dumps(state));tmp.replace(R/'boxE-guard33.json');time.sleep(5)
finally:
 ids=descendants([p.pid for p in workers.values() if p.poll() is None],rows())
 for sig in [signal.SIGTERM,signal.SIGKILL]:
  for pid in sorted(ids,reverse=True):
   try:os.kill(pid,sig)
   except ProcessLookupError:pass
  if sig==signal.SIGTERM:time.sleep(.2)
