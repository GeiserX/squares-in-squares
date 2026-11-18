from pathlib import Path
import os,subprocess,signal,time,json
R=Path.home()/'scratch/squares-k123';os.chdir(R);pid=int((R/'box_guard36.pid').read_text());cmd=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True).strip();assert cmd.split()[-1]=='box_guard34.py',cmd
cwd=subprocess.check_output(['/usr/sbin/lsof','-a','-p',str(pid),'-d','cwd','-Fn'],text=True);assert '\nn'+str(R)+'\n' in cwd,cwd
os.kill(pid,signal.SIGTERM);time.sleep(1);py=json.load(open(R/'runtime33.json'))['python'];os.execv(py,[py,'-I',str(R/'remotehealth36.py')])
