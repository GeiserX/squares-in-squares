from pathlib import Path
import json,subprocess,os,signal
R=Path.home()/'scratch/squares-k123';cfg=json.load(open(R/'runtime33.json'));stopped=[]
for slot,args in cfg['slots'].items():
 if args[0]!='qrun22.py':continue
 p=R/(slot+'.pid')
 if not p.exists():continue
 pid=int(p.read_text());cmd=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout.strip()
 if cmd.split()[-2:]!=args:continue
 cwd=subprocess.run(['/usr/sbin/lsof','-a','-p',str(pid),'-d','cwd','-Fn'],capture_output=True,text=True).stdout
 if '\nn'+str(R)+'\n' not in cwd:continue
 os.kill(pid,signal.SIGTERM);stopped.append(pid)
print(json.dumps({'stopped_owned_join_wrappers':stopped,'recovery':'box guard clears orphan children and requeues interrupted claims'}))
