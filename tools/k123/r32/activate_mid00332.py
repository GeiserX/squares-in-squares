"""Replace one worker at a completed-job boundary after its positive control."""
from pathlib import Path
import subprocess,json,time,os,signal
R=Path.home()/'scratch/squares-k123';os.chdir(R);end=min(time.time()+480,float((R/'search-deadline').read_text()))
def ps():
 return [line.strip().split(None,2) for line in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]]
p=R/'taskdone/verify-mid00332-control.json'
while not p.exists() and time.time()<end:time.sleep(2)
assert p.exists() and json.load(p.open())['rc']==0,'mid003 control missing or failed'
old=int((R/'j22a.pid').read_text());PY=str(Path.home()/'scratch/squares-base/venv/bin/python')
while time.time()<end:
 rows=ps();own=next((r for r in rows if int(r[0])==old),None)
 assert own and 'qrun22.py j22a' in own[2],own
 os.kill(old,signal.SIGSTOP)
 if any(int(r[1])==old for r in ps()):
  os.kill(old,signal.SIGCONT);time.sleep(3);continue
 os.kill(old,signal.SIGKILL)
 (R/'enable-mid00332').touch()
 with (R/'out/j22a-mid00332.log').open('a') as f:
  child=subprocess.Popen(['nohup','nice','-n','5',PY,'-I',str(R/'qrun22.py'),'j22a'],stdin=subprocess.DEVNULL,stdout=f,stderr=f,start_new_session=True)
 (R/'j22a.pid').write_text(str(child.pid));receipt={'old_pid':old,'new_pid':child.pid,'control':'444 at1.003','cap':80,'time':time.strftime('%FT%TZ',time.gmtime())};(R/'mid00332-started.json').write_text(json.dumps(receipt));print(json.dumps(receipt),flush=True);break
else:raise RuntimeError('no safe worker boundary before activation deadline')
