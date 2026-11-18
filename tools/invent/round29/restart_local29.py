import os,pathlib,signal,subprocess,time
W=pathlib.Path(__file__).parent
for name in ('controller','finish'):
 p=W/(name+'.pid')
 if p.exists():
  pid=int(p.read_text())
  try:
   command=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True)
   if str(W) in command:
    if os.getpgid(pid)==pid:os.killpg(pid,signal.SIGTERM)
    else:os.kill(pid,signal.SIGTERM)
  except (ProcessLookupError,subprocess.CalledProcessError):pass
import json
progress=json.load(open(W/'finish-progress.json'))if(W/'finish-progress.json').exists()else{}
launch=[('finish','finish28.py')]if progress.get('controller_stopped')else [('controller','controller28.py'),('finish','finish28.py')]
for name,script in launch:
 h=(W/(name+'.log')).open('a');env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
 p=subprocess.Popen(['nohup','nice','-n','5','$SCRATCH/bounties-squares/venv/bin/python','-I',str(W/script)],cwd=W,env=env,stdin=subprocess.DEVNULL,stdout=h,stderr=subprocess.STDOUT,start_new_session=True);(W/(name+'.pid')).write_text(str(p.pid));print(name,p.pid)
with (W.parent/'STATE.txt').open('a')as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' RESTART '+('finalizer from saved progress, controller stays stopped'if progress.get('controller_stopped')else 'local collector/finalizer')+', no boxE numerical process touched. Logs work/controller.log work/finish.log; common11:45Z.\n')
