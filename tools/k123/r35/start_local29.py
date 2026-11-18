from pathlib import Path
import subprocess,json,time
W=Path(__file__).resolve().parent;PY=str(W.parent.parent/'venv/bin/python')
ps=subprocess.check_output(['ps','-axo','pid,command'],text=True);started=[]
for name,args in [('collect',['resident25.py','collect']),('stage',['resident25.py','stage']),('third',['background29.py','third']),('storage',['background29.py','storage']),('finalizer',['finish26.py'])]:
 if str(W/args[0])+' '+(' '.join(args[1:])) in ps:continue
 with open(W/(name+'-resident29.log'),'a') as f:
  p=subprocess.Popen(['nohup','nice','-n','5',PY,str(W/args[0]),*args[1:]],stdout=f,stderr=f,stdin=subprocess.DEVNULL,start_new_session=True)
 (W/(name+'.pid')).write_text(str(p.pid));started.append(dict(name=name,pid=p.pid,args=args))
with open(W.parent/'STATE.txt','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA START restartable controllers '+json.dumps(started)+'; logs work/*-resident29.log; common cutoff16:25Z, report after16:35Z.\n')
print(json.dumps(started))
