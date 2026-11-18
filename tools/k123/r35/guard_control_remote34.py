from pathlib import Path
import subprocess,os,json,time,tempfile
R=Path.home()/'scratch/squares-k123';text=(R/'box_guard34.py').read_text();prefix=text.split('assert not any(cmd.endswith')[0];ns={};exec(compile(prefix,'box_guard34.py','exec'),ns)
with tempfile.TemporaryDirectory(dir=R) as tmp:
 root=Path(tmp);(root/'claims').mkdir();(root/'out/test').mkdir(parents=True);ns['R']=root;ns['rows']=lambda:[]
 p=root/'claims/stale';p.mkdir();(p/'owner.json').write_text(json.dumps(dict(pid=-123,worker='test',jobkey='pool-2-tag')));requeued=ns['recover_claims']();assert len(requeued)==1 and not p.exists()
 p=root/'claims/completed';p.mkdir();(p/'owner.json').write_text(json.dumps(dict(pid=-123,worker='test',jobkey='pool-2-tag')));(root/'out/test/done.jsonl').write_text(json.dumps(dict(pool='pool',n=2,tag='tag'))+'\n');assert not ns['recover_claims']() and p.exists()
print(json.dumps({'stale_claim_requeued':True,'completed_claim_retained':True}),flush=True)
p=subprocess.Popen([__import__('sys').executable,'-c','import time;time.sleep(45)'],cwd=R,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
print(json.dumps({'orphan_pid':p.pid}),flush=True)
