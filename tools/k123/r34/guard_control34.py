from pathlib import Path
import subprocess,json,time
W=Path(__file__).resolve().parent;host='boxC';cfg=json.load((W/host/'runtime33.json').open());py=cfg['python']
script="""from pathlib import Path
import subprocess,os,json,time,tempfile
R=Path.home()/'scratch/squares-k123';text=(R/'box_guard34.py').read_text();prefix=text.split('assert not any(cmd.endswith')[0];ns={};exec(compile(prefix,'box_guard34.py','exec'),ns)
with tempfile.TemporaryDirectory(dir=R) as tmp:
 root=Path(tmp);(root/'claims').mkdir();(root/'out/test').mkdir(parents=True);ns['R']=root;ns['rows']=lambda:[]
 p=root/'claims/stale';p.mkdir();(p/'owner.json').write_text(json.dumps(dict(pid=-123,worker='test',jobkey='pool-2-tag')));requeued=ns['recover_claims']();assert len(requeued)==1 and not p.exists()
 p=root/'claims/completed';p.mkdir();(p/'owner.json').write_text(json.dumps(dict(pid=-123,worker='test',jobkey='pool-2-tag')));(root/'out/test/done.jsonl').write_text(json.dumps(dict(pool='pool',n=2,tag='tag'))+'\\n');assert not ns['recover_claims']() and p.exists()
print(json.dumps({'stale_claim_requeued':True,'completed_claim_retained':True}),flush=True)
p=subprocess.Popen([__import__('sys').executable,'-c','import time;time.sleep(45)'],cwd=R,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
print(json.dumps({'orphan_pid':p.pid}),flush=True)
"""
p=W/'guard_control_remote34.py';p.write_text(script);subprocess.run(['scp','-q',str(p),host+':scratch/squares-k123/'],check=True)
r=subprocess.run(['ssh',host,f'cd $SCRATCH/squares-k123 && {py} -I guard_control_remote34.py'],capture_output=True,text=True,check=True,timeout=30);lines=r.stdout.splitlines();assert json.loads(lines[0])['stale_claim_requeued'];pid=json.loads(lines[1])['orphan_pid'];print(r.stdout,flush=True)
removed=False
for i in range(12):
 time.sleep(2)
 p=subprocess.run(['ssh',host,f'ps -p {pid} -o pid='],capture_output=True,text=True,timeout=10)
 if not p.stdout.strip():removed=True;break
assert removed,'orphan cleanup failed'
result={'stale_claim_requeued':True,'completed_claim_retained':True,'live_orphan_removed':True,'orphan_pid':pid,'box':host};(W/'guard-control34.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA FINISH guard control: stale claim requeued, completed claim retained, live orphan process stopped by the box guard. work/guard-control34.json; deadline07:25Z.\n')
