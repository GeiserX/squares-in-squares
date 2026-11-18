from pathlib import Path
import sys,json,time
R=Path.home()/'scratch/squares-k123';cfg=json.load(open(R/'runtime33.json'));slot=next(s for s,a in cfg['slots'].items() if a[0]=='qrun22.py');s=(R/'qrun-preview36.py').read_text();prefix=s.split("while time.time()<float((R/'search-deadline').read_text()):")[0]
sys.argv=[str(R/'qrun22.py'),slot];ns={};exec(compile(prefix,'qrun-preview36.py','exec'),ns)
closed=json.load(open(R/'closed-families36.json'));key=next(iter(closed));assert ns['family_closed36'](key);assert not ns['family_closed36']('changed-family')
start=time.time();ns['active_family36']='changed-family';assert ns['run']([cfg['python'],'-c','print("open family")'],str(R/'control-family36.log'))==0;elapsed=time.time()-start;assert elapsed<1.5,elapsed
ns['active_family36']=key;assert ns['run']([cfg['python'],'-c','import time;time.sleep(5)'],str(R/'control-family36.log'))==-3
ns['active_family36']='changed-family';ns['jobdeadline']=time.time()+.1;assert ns['run']([cfg['python'],'-c','import time;time.sleep(5)'],str(R/'control-family36.log'))==-2
r={'isolated_import':True,'open_family_completes':True,'closed_family_stops':True,'deadline_stops':True,'fast_job_seconds':elapsed,'box':(R/'box33').read_text().strip()};(R/'isolated-family-control36.json').write_text(json.dumps(r));print(json.dumps(r))
