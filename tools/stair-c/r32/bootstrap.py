import os,pathlib,subprocess,sys,time
R=pathlib.Path('$PRIVATE_REPO');H=R/'lanes/squares/tools/stair-c/r32';W=pathlib.Path('$SCRATCH/bounties-squares/take-stair-c-r32/work')
while not (W/'base-audit.json').exists():
 if 'Traceback' in (W/'setup.log').read_text().split('CONTROL r27 source gate:')[-1]:raise RuntimeError('setup failed; inspect setup.log')
 time.sleep(5)
for name,args in [('control_fresh.py',[]),('control_live.py',[str(H/'worker.py')]),('control_novel.py',[str(H/'worker.py')]),('queue_bar.py',[]),('saved.py',[]),('whole.py',[])]:
 subprocess.run([sys.executable,'-I',str(H/name),*args],check=True,cwd=R)
# Certify the real fq control before placing it in the worker queue.
sys.path[:0]=[str(H),str(R/'lanes/squares')]
import csv,json
import fine
b=W/'box';a=list(csv.DictReader(open(b/'control975.csv')));n,rr,sc,eps=fine.work((975,a));assert rr is not None
broken=[dict(r)for r in rr];broken[1]=dict(broken[0]);assert fine.work((975,broken))[1]is None
(b/'cert-in').mkdir(exist_ok=True)
with open(b/'cert-in/975-control-real.csv','w')as f:w=csv.DictWriter(f,['n','square_id','x','y','angle']);w.writeheader();w.writerows(rr)
(b/'cert-in/975-control-real.json').write_text(json.dumps(dict(n=975,control_only=True,modules=[],built=(1+sc)*975**.5)))
print('CONTROL finesafe975 certified; duplicate-square copy rejected; clearance',fine.module.fs.clearance(rr),flush=True)
# A real inflated-start kick control precedes production kicks on the worker.
scaled=[dict(r,x=repr(float(r['x'])*1.0003),y=repr(float(r['y'])*1.0003))for r in rr]
_,safe,score,_=fine.work((975,scaled));assert safe is not None
with open(b/'cert-in/975-inflated-kick-control.csv','w')as f:
 writer=csv.DictWriter(f,['n','square_id','x','y','angle']);writer.writeheader();writer.writerows(safe)
(b/'cert-in/975-inflated-kick-control.json').write_text(json.dumps(dict(n=975,control_only=True,whole_layout_follow=True,whole_kick=True,kick_control=True,kick_seconds=60,kick_seed=31111,modules=[],built=(1+score)*975**.5)))

import shutil
for tool in H.glob('*.py'):shutil.copy2(tool,b/tool.name)
shutil.copy2(R/'lanes/squares/tools/border/r28/finesafe.py',b/'lane/stair_finesafe.py')
subprocess.run([sys.executable,'-I',str(H/'start.py')],check=True,cwd=R)
for name,key in [('follow_driver.py','follow-driver'),('held_driver.py','held-driver')]:
 f=open(W/(key+'.log'),'ab');p=subprocess.Popen([sys.executable,'-I',str(H/name)],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,cwd=R);(W/(key+'.pid')).write_text(str(p.pid));print('START',key,p.pid,flush=True)
