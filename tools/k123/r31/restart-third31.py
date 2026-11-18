from pathlib import Path
import subprocess,os,time,signal,json
R=Path.home()/'scratch/squares-k123'
def processes():
 return [(int(a[0]),int(a[1]),a[2]) for l in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:] if len(a:=l.split(None,2))==3]
roots={p for p,pp,c in processes() if c.rstrip().endswith('python -I third22.py')}
for p in roots:os.kill(p,signal.SIGSTOP)
end=time.time()+600
while time.time()<end and any(pp in roots for p,pp,c in processes()):time.sleep(.25)
for p in roots:
 try:os.kill(p,signal.SIGKILL)
 except ProcessLookupError:pass
with (R/'out/third.log').open('a') as f:
 p=subprocess.Popen(['nohup','nice','-n','5',str(Path.home()/'scratch/squares-base/venv/bin/python'),'-I','third22.py'],cwd=R,stdout=f,stderr=f,stdin=subprocess.DEVNULL,start_new_session=True)
print(json.dumps({'replaced':list(roots),'new':p.pid,'time':time.time()}),flush=True)
