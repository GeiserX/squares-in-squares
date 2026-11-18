"""Recover dead controllers and box supervisors while the search window is open."""
from pathlib import Path
import subprocess,time,json,os,traceback,datetime,signal
W=Path(__file__).resolve().parent;T=W.parent;PY=str(T.parent/'venv/bin/python');spec={'collect':['resident25.py','collect'],'stage':['resident25.py','stage'],'third':['background29.py','third'],'storage':['background29.py','storage'],'bridge34':['bridge34.py']}
end=datetime.datetime(2026,11,17,15,55,tzinfo=datetime.timezone.utc).timestamp()
def note(s):
 with (T/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA GUARD34 '+s+'\n')
while time.time()<end:
 try:
  ps=subprocess.check_output(['ps','-axo','pid,command'],text=True)
  for name,args in spec.items():
   suffix=str(W/args[0])+(' '+' '.join(args[1:]) if len(args)>1 else '')
   matches=[int(l.strip().split(None,1)[0]) for l in ps.splitlines() if l.rstrip().endswith(suffix)]
   assert len(matches)<=1,(name,matches)
   if matches:continue
   with (W/(name+'-recovery34.log')).open('a') as f:p=subprocess.Popen([PY,str(W/args[0]),*args[1:]],stdin=subprocess.DEVNULL,stdout=f,stderr=f,start_new_session=True)
   (W/(name+'.pid')).write_text(str(p.pid));note('RESTART '+name+' pid='+str(p.pid)+' after dead controller. Deadline16:25Z.')
  for host in ['boxE','boxC','boxD']:
   # One process list per box detects a dead supervisor even if its last JSON remains.
   psr=subprocess.run(['ssh',host,'ps -axo pid,command'],capture_output=True,text=True,timeout=15);psr.check_returncode()
   guards=[l for l in psr.stdout.splitlines() if l.rstrip().endswith('box_guard34.py')]
   if guards:continue
   cfg=json.load((W/'runtime33.json' if host=='boxE' else W/host/'runtime33.json').open())
   subprocess.run(['ssh',host,f'cd $SCRATCH/squares-k123 && {cfg["python"]} -I stop_remote25.py'],check=True,timeout=30)
   subprocess.run(['ssh',host,f'cd $SCRATCH/squares-k123 && nohup nice -n 5 {cfg["python"]} -I box_guard34.py > out/box-guard34-restart.log 2>&1 < /dev/null &'],check=True,timeout=15)
   note('RESTART '+host+' supervisor after own-tree cleanup; interrupted claims requeue. Deadline16:25Z.')
  (W/'guardian34-status.json').write_text(json.dumps({'time':time.strftime('%FT%TZ',time.gmtime()),'controllers':'live','boxes':'supervisors live'}))
 except Exception:traceback.print_exc()
 time.sleep(30)
