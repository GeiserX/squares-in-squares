import ast,pathlib,time,subprocess,os,signal,sys,json
W=pathlib.Path(__file__).resolve().parent
node=next(n for n in ast.parse((W/'worker23.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='run_bounded')
ns=dict(time=time,subprocess=subprocess,os=os,signal=signal,DEADLINE=time.time()+0.5)
exec(compile(ast.Module(body=[node],type_ignores=[]),str(W/'worker23.py'),'exec'),ns)
pidfile=W/'deadline-control-pids.txt';code="import os,pathlib,subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);pathlib.Path(sys.argv[1]).write_text(str(os.getpid())+' '+str(p.pid));time.sleep(60)"
t0=time.time()
try:
 with open(W/'deadline-control.log','w')as h:ns['run_bounded']([sys.executable,'-c',code,str(pidfile)],h,30)
 raise AssertionError('deadline failed to stop child')
except subprocess.TimeoutExpired:pass
elapsed=time.time()-t0;pids=pidfile.read_text().split();left=[]
for p in pids:
 r=subprocess.run(['ps','-p',p,'-o','stat='],capture_output=True,text=True)
 if r.stdout.strip()and not r.stdout.strip().startswith('Z'):left.append(p)
assert not left,(left,elapsed)
assert elapsed<4,elapsed
out={'deadline_seconds':0.5,'elapsed':elapsed,'child_and_grandchild_stopped':True,'pids':pids}
(W/'deadline-control-result.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
