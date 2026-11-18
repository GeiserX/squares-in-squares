"""Supervise the assigned slots, clear interrupted claims, and pause above the box load limit."""
from pathlib import Path
import os,subprocess,signal,time,json
R=Path.home()/'scratch/squares-k123';os.chdir(R);cfg=json.load((R/'runtime33.json').open());PY=cfg['python'];spec=cfg['slots'];workers={};paused=False;low=0
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
def rows():
 out=[]
 for line in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
  a=line.strip().split(None,2)
  # Another process can put a newline in its command; skip lines that are not pid rows.
  if len(a)==3 and a[0].isdigit() and a[1].isdigit():out.append((int(a[0]),int(a[1]),a[2]))
 return out
def tree():
 ps=rows();ids={p.pid for p in workers.values() if p.poll() is None}
 while True:
  extra={pid for pid,pp,cmd in ps if pp in ids}-ids
  if not extra:return ids
  ids|=extra
def signals(sig):
 for pid in sorted(tree(),reverse=True):
  try:os.kill(pid,sig)
  except ProcessLookupError:pass

def cancel_for_load():
 roots={p.pid for p in workers.values() if p.poll() is None};ids=tree()
 # Stop wrappers first so a killed child cannot become a completed trial.
 for pid in sorted(roots,reverse=True):
  try:os.kill(pid,signal.SIGKILL)
  except ProcessLookupError:pass
 for sig in [signal.SIGCONT,signal.SIGTERM,signal.SIGKILL]:
  for pid in sorted(ids-roots,reverse=True):
   try:os.kill(pid,sig)
   except ProcessLookupError:pass
  if sig==signal.SIGTERM:time.sleep(.1)
 for p in workers.values():p.poll()
 if ids:
  with (R/'load-cancels34.jsonl').open('a') as f:f.write(json.dumps({'time':time.strftime('%FT%TZ',time.gmtime()),'roots':sorted(roots),'stopped':sorted(ids)})+'\n')
 return sorted(ids)

def cleanup_orphans():
 active=tree();ps=rows()
 candidates={pid for pid,pp,cmd in ps if pp==1 and pid!=os.getpid() and pid not in active and Path(cmd.split()[0]).name in ['python','python3','Python','fq']}
 if not candidates:return []
 out=subprocess.run(['/usr/sbin/lsof','-a','-p',','.join(map(str,sorted(candidates))),'-d','cwd','-Fpn'],capture_output=True,text=True,timeout=15).stdout
 owned=set();pid=None
 for line in out.splitlines():
  if line.startswith('p') and line[1:].isdigit():pid=int(line[1:])
  elif line.startswith('n') and pid in candidates and (line[1:]==str(R) or line[1:].startswith(str(R)+'/')):owned.add(pid)
 while True:
  more={pid for pid,pp,cmd in ps if pp in owned}-owned
  if not more:break
  owned|=more
 for sig in [signal.SIGCONT,signal.SIGTERM,signal.SIGKILL]:
  for pid in sorted(owned,reverse=True):
   try:os.kill(pid,sig)
   except ProcessLookupError:pass
  if sig==signal.SIGTERM:time.sleep(.1)
 if owned:
  with (R/'orphans34.jsonl').open('a') as f:f.write(json.dumps({'time':time.time(),'stopped':sorted(owned)})+'\n')
 return sorted(owned)

def recover_claims():
 live={pid for pid,pp,cmd in rows()};requeued=[]
 for p in (R/'claims').glob('*/owner.json'):
  try:
   j=json.load(p.open())
   if j['pid'] in live:continue
   done=R/'out'/j['worker']/'done.jsonl'
   complete=False
   for line in done.read_text().splitlines() if done.exists() else []:
    r=json.loads(line)
    if j['jobkey']==f'{r["pool"]}-{r["n"]}-{r["tag"]}' and not (not r.get('raw') and (r.get('code') in [-15,-9] or r.get('fq2code') in [-15,-9])):complete=True;break
   if not complete:p.unlink();p.parent.rmdir();requeued.append(j)
  except (OSError,ValueError,KeyError):continue
 if requeued:
  with (R/'requeued34.jsonl').open('a') as f:
   for j in requeued:f.write(json.dumps(j)+'\n')
 return requeued
assert not any(cmd.endswith(' '.join(args)) for _,_,cmd in rows() for args in spec.values()),'existing slot must be adopted'
try:
 while time.time()<float((R/'deadline').read_text()) and not (R/'STOP34').exists():
  load=os.getloadavg()[0];size=1024*int(subprocess.check_output(['du','-sk',str(R)],text=True).split()[0]);orphans=cleanup_orphans();requeued=recover_claims()
  if load>cfg['load_limit'] or size>2_650_000_000:
   cancelled=cancel_for_load();paused=True;low=0
  elif paused:
   low=low+1 if load<cfg['load_limit']-1 and size<2_650_000_000 else 0
   if low>=2:paused=False;low=0
  if not paused:
   ps=rows();owned=[(pid,cmd) for pid,pp,cmd in ps if any(cmd.endswith(' '.join(a)) for a in spec.values())]
   assert len(owned)<=len(spec),owned
   for slot,args in spec.items():
    p=workers.get(slot)
    if p is not None and p.poll() is None:continue
    if slot!='third' and time.time()>=float((R/'search-deadline').read_text()):continue
    assert not any(cmd.endswith(' '.join(args)) for _,cmd in owned),'unadopted duplicate worker'
    with (R/'out'/(slot+'-guard34.log')).open('a') as f:p=subprocess.Popen(['nohup','nice','-n','5',PY,'-I',*args],stdout=f,stderr=f,stdin=subprocess.DEVNULL,start_new_session=True)
    workers[slot]=p;(R/(slot+'.pid')).write_text(str(p.pid));owned.append((p.pid,' '.join(args)))
  state={'time':time.strftime('%FT%TZ',time.gmtime()),'load1':load,'bytes':size,'paused':paused,'workers':{s:p.pid for s,p in workers.items() if p.poll() is None},'requeued':requeued,'orphans_stopped':orphans}
  (R/'guard34.json.tmp').write_text(json.dumps(state));(R/'guard34.json.tmp').replace(R/'guard34.json');print(json.dumps(state),flush=True);time.sleep(10)
finally:
 ids=tree()
 for sig in [signal.SIGCONT,signal.SIGTERM,signal.SIGKILL]:
  for pid in sorted(ids|tree(),reverse=True):
   try:os.kill(pid,sig)
   except ProcessLookupError:pass
  if sig==signal.SIGTERM:time.sleep(.3)
