from pathlib import Path
import sys,json,csv,shutil,hashlib,subprocess
W=Path(__file__).resolve().parent;S=W.parent.parent;sys.path[:0]=[str(W),str(W/'lane')];sys.dont_write_bytecode=True
from provenance24 import mlp,credit
p=W/'control626.csv';q=Path(str(p)+'.json')
if not p.exists():shutil.copy(S/'take-k123-r31/work'/p.name,p)
if not q.exists():shutil.copy(S/'take-k123-r31/work'/q.name,q)
A=mlp.load(str(p),{626})[626];c=credit(626,A,str(p));assert c,'626 source admission failed'
sn=W/'input-snapshots';data=p.read_bytes();h=hashlib.sha256(data).hexdigest();rs=q.read_bytes();rh=hashlib.sha256(rs).hexdigest();a=sn/f'626-{h}.csv';a.write_bytes(data);b=sn/(rh+'.json');b.write_bytes(rs)
c={**c,'input_file_snapshot':str(a),'input_file_sha256':h,'input_file_mtime':p.stat().st_mtime,'input_record_snapshots':{str(q):{'snapshot':str(b),'sha256':rh}}}
old=json.load((W/'strippool32/sources-strippool32.json').open());pool='strippool62632';D=W/pool;D.mkdir(exist_ok=True);(D/('sources-'+pool+'.json')).write_text(json.dumps({'261':old['261'],'626':c}));(D/('bars-'+pool+'.tsv')).write_text((W/'bars.tsv').read_text());(D/(pool+'.json')).write_text(json.dumps({'kind':'strip-model-pool','tag':pool,'source':'own constructive strip model, exact held15 controls261/626'}))
P={261:mlp.load(str(W/'control261.csv'),{261})[261],626:A}
with (D/(pool+'.csv')).open('w') as f:
 wr=csv.writer(f);wr.writerow(['n','square_id','x','y','angle'])
 for n,Q in P.items():wr.writerows((n,i,*a) for i,a in enumerate(Q))
for file in [p,*[D/name for name in [pool+'.csv','sources-'+pool+'.json','bars-'+pool+'.tsv']]]:subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r34-ssh',str(file),'boxE:scratch/squares-k123/'+file.name],check=True,timeout=30)
print('626 exact calibration pool ready',flush=True)
