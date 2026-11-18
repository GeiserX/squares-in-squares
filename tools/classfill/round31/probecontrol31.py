import os,sys,json,subprocess,shutil
from pathlib import Path
sys.path.insert(0,str(Path('lane').resolve()))
import classfill_finish as F
root=Path('out/probe-control31');root.mkdir(exist_ok=True)
for label,x,expected in [('loose',1.5004,True),('tight',1.500000000022,False)]:
 p=root/('2-'+label+'.csv');F.write(p,[dict(n='2',square_id='0',x='0.5',y='0.5',angle='0'),dict(n='2',square_id='1',x=str(x),y='0.5',angle='0')]);out=root/label
 subprocess.run([sys.executable,'-I','probe31.py','--n','2','--sub',str(p),'--out',str(out),'--fq',str(Path('fq').resolve()),'--seconds','8','--seed','31','--modes','lkick,kick','--kicks','0.02','--deadline','deadline','--probe-seconds','3'],check=True)
 r=json.loads((out/'probe.json').read_text());assert bool(r['certified_review'].get('productive'))==expected,(label,r)
 assert r['stopped_no_find'] != expected,(label,r)
 print('PROBE_CERT_CONTROL_PASS',label,r,flush=True)
