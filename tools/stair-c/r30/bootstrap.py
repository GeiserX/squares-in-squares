import os,pathlib,subprocess,sys,time
R=pathlib.Path('$PRIVATE_REPO');H=R/'lanes/squares/tools/stair-c/r30';W=pathlib.Path('$SCRATCH/bounties-squares/take-stair-c-r30/work')
while not (W/'base-audit.json').exists():
 if 'Traceback' in (W/'setup.log').read_text():raise RuntimeError('setup failed; inspect setup.log')
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
# A changed corner/count pairing: the cached following-stack 805 corners at748.
import pickle,shutil
lib=pickle.load(open(b/'libbase/library.pkl','rb'))
need={q['id'] for q in lib['mods'] if q.get('n')==805 and q.get('extra_stacks')==3}
assert need,'cached following-stack805 corners absent'
sp=b/'state-1.pkl';st=pickle.load(open(sp,'rb'));st['fresh'].update(need);st['rank'].insert(0,dict(need=need,ns=[748],patch='r30-priority-transfer805to748.pkl'));pickle.dump(st,open(sp,'wb'))
shutil.copy2(H/'worker.py',b/'worker.py')
print('TRANSFER805to748',sorted(need),flush=True)
subprocess.run([sys.executable,'-I',str(H/'start.py')],check=True,cwd=R)
for name,key in [('follow_driver.py','follow-driver')]:
 f=open(W/(key+'.log'),'ab');p=subprocess.Popen([sys.executable,'-I',str(H/name)],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,cwd=R);(W/(key+'.pid')).write_text(str(p.pid));print('START',key,p.pid,flush=True)
