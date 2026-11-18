from pathlib import Path
import subprocess,json,time,os,signal
W=Path(__file__).resolve().parent
# The local health guard stays paused while its boxes deliberately restart.
gid=int((W/'guardian34.pid').read_text());os.kill(gid,signal.SIGSTOP)
try:
 for host in ['boxC','boxD','boxE']:
  cfg=json.load((W/'runtime33.json' if host=='boxE' else W/host/'runtime33.json').open())
  for name in ['box_guard34.py','stop_remote25.py']:subprocess.run(['scp','-q',str(W/name),host+':scratch/squares-k123/'],check=True,timeout=30)
  result=subprocess.run(['ssh',host,f'cd $SCRATCH/squares-k123 && {cfg["python"]} -I stop_remote25.py'],capture_output=True,text=True,check=True,timeout=45);print(host,result.stdout,flush=True)
  subprocess.run(['ssh',host,f'cd $SCRATCH/squares-k123 && nohup nice -n 5 {cfg["python"]} -I box_guard34.py > out/box-guard34-v2.log 2>&1 < /dev/null &'],check=True,timeout=20)
finally:os.kill(gid,signal.SIGCONT)
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA UPDATE all three box guards after own-tree cleanup: orphan numerical children now stop before a dead wrapper claim requeues. This closes a duplication risk after wrapper death. Completed recipes stay closed, unfinished recipes requeue. Outputs retained, logs out/box-guard34-v2.log, deadline23:45Z.\n')
