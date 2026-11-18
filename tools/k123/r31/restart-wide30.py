from pathlib import Path
import subprocess,os,signal,time,json
R=Path.home()/'scratch/squares-k123'
ps=[]
for line in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
 a=line.strip().split(None,2)
 if len(a)==3:ps.append((int(a[0]),int(a[1]),a[2]))
roots={p for p,pp,c in ps if 'python' in c.lower() and c.rstrip().endswith('qrun22.py j22d')};owned=set(roots)
while True:
 more={p for p,pp,c in ps if pp in owned}-owned
 if not more:break
 owned|=more
for sig in [signal.SIGTERM,signal.SIGKILL]:
 for p in sorted(owned,reverse=True):
  try:os.kill(p,sig)
  except ProcessLookupError:pass
 if sig==signal.SIGTERM:time.sleep(.5)
(R/'enable-wide30').touch()
with (R/'out/j22d.log').open('a') as f:p=subprocess.Popen(['nohup','nice','-n','5',str(Path.home()/'scratch/squares-base/venv/bin/python'),'-I','qrun22.py','j22d'],cwd=R,stdout=f,stderr=f,stdin=subprocess.DEVNULL,start_new_session=True)
(R/'j22d.pid').write_text(str(p.pid));out={'stopped_pids':sorted(owned),'new_pid':p.pid,'mechanism':'loosen1.005-r30'};(R/'restart-wide30.json').write_text(json.dumps(out));print(json.dumps(out),flush=True)
