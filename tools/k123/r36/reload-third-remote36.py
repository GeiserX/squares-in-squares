from pathlib import Path
import subprocess,os,signal
R=Path.home()/'scratch/squares-k123';pid=int((R/'third.pid').read_text());cmd=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True).strip();assert cmd.split()[-1]=='third22.py',cmd
cwd=subprocess.check_output(['/usr/sbin/lsof','-a','-p',str(pid),'-d','cwd','-Fn'],text=True);assert '\nn'+str(R)+'\n' in cwd,cwd
os.kill(pid,signal.SIGTERM);print('stopped owned third wrapper',pid,'guard will clean orphan and recover running job before restart')
