"""Check owned controller pids and keep detached drivers adoptable."""
from pathlib import Path
import subprocess,time,os,signal,json
W=Path(__file__).resolve().parent;PY=str(W.parent.parent/'venv/bin/python')
spec={'collect':['resident25.py','collect'],'stage':['resident25.py','stage'],'third':['background29.py','third'],'storage':['background29.py','storage'],'bridge34':['bridge34.py'],'finalize36':['finalize36.py']}
while time.time()<float((W/'search-deadline').read_text()):
 ps=subprocess.check_output(['ps','-axo','pid,command'],text=True);live={int(l.split(None,1)[0]):l.split(None,1)[1] for l in ps.splitlines()[1:] if l.split(None,1)[0].isdigit() and len(l.split(None,1))==2}
 for name,args in spec.items():
  if (W/('stop-'+name+'36')).exists():continue
  p=W/(name+'.pid');pid=int(p.read_text()) if p.exists() else -1
  if pid in live and str(W/args[0]) in live[pid]:continue
  with open(W/(name+'-r36.log'),'a') as f:q=subprocess.Popen(['nohup','nice','-n','5',PY,str(W/args[0]),*args[1:]],stdout=f,stderr=f,stdin=subprocess.DEVNULL,start_new_session=True)
  p.write_text(str(q.pid))
  with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA RESTART '+name+' pid'+str(q.pid)+' log work/'+name+'-r36.log deadline23:45Z\n')
 (W/'guardian36.json').write_text(json.dumps({'time':time.strftime('%FT%TZ',time.gmtime()),'pids':{name:int((W/(name+'.pid')).read_text()) for name in spec}}));time.sleep(30)
