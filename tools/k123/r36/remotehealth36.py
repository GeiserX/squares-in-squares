"""Adopt an owned box guard or recover it after a crash, before each queue transfer."""
from pathlib import Path
import subprocess,os,json,time,signal
R=Path.home()/'scratch/squares-k123';os.chdir(R)
if (R/'STOP34').exists() or time.time()>=float((R/'deadline').read_text()):print(json.dumps({'stopped_by_deadline':True}));raise SystemExit
cfg=json.load(open(R/'runtime33.json'));ps=[]
for l in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
 a=l.strip().split(None,2)
 if len(a)==3 and a[0].isdigit() and a[1].isdigit():ps.append((int(a[0]),int(a[1]),a[2]))
candidates=[pid for pid,pp,cmd in ps if Path(cmd.split()[0]).name in ['python','python3','Python','fq'] and pid!=os.getpid()]
owned=set();pid=None
if candidates:
 out=subprocess.run(['/usr/sbin/lsof','-a','-p',','.join(map(str,candidates)),'-d','cwd','-Fpn'],capture_output=True,text=True,timeout=15).stdout
 for l in out.splitlines():
  if l.startswith('p') and l[1:].isdigit():pid=int(l[1:])
  elif l.startswith('n') and (l[1:]==str(R) or l[1:].startswith(str(R)+'/')):owned.add(pid)
guards=[pid for pid,pp,cmd in ps if pid in owned and cmd.split()[-1]=='box_guard34.py']
assert len(guards)<=1,guards
if guards:
 (R/'box_guard36.pid').write_text(str(guards[0]));print(json.dumps({'guard_pid':guards[0],'restarted':False}));raise SystemExit
# The guard is gone. Stop only this lane's orphan process tree before it requeues interrupted claims.
while True:
 more={pid for pid,pp,cmd in ps if pp in owned}-owned
 if not more:break
 owned|=more
for sig in [signal.SIGCONT,signal.SIGTERM,signal.SIGKILL]:
 for pid in sorted(owned,reverse=True):
  try:os.kill(pid,sig)
  except ProcessLookupError:pass
 if sig==signal.SIGTERM:time.sleep(.2)
with open(R/'out/box-guard34.log','a') as f:p=subprocess.Popen(['nohup','nice','-n','5',cfg['python'],'-I','box_guard34.py'],stdout=f,stderr=f,stdin=subprocess.DEVNULL,start_new_session=True)
(R/'box_guard36.pid').write_text(str(p.pid));j={'time':time.strftime('%FT%TZ',time.gmtime()),'guard_pid':p.pid,'restarted':True,'orphan_pids_stopped':sorted(owned)}
with open(R/'health-restarts36.jsonl','a') as f:f.write(json.dumps(j)+'\n')
print(json.dumps(j))
