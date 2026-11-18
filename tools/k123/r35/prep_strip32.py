from pathlib import Path
import sys,json,csv,shutil,hashlib,subprocess,time
W=Path(__file__).resolve().parent;S=W.parent.parent;T=W.parent;sys.path[:0]=[str(W),str(W/'lane')];sys.dont_write_bytecode=True
from provenance24 import mlp,credit
SSH=['ssh','-S','/tmp/squares-k123-r35-ssh','boxE'];SCP=['scp','-q','-o','ControlPath=/tmp/squares-k123-r35-ssh']
pool='strippool32';D=W/pool;D.mkdir(exist_ok=True);manifest={};pack={};sn=W/'input-snapshots';sn.mkdir(exist_ok=True)
for n in [261,367]:
 p=W/f'control{n}.csv';q=Path(str(p)+'.json')
 if not p.exists():shutil.copy(S/'take-k123-r31/work'/p.name,p)
 if not q.exists():shutil.copy(S/'take-k123-r31/work'/q.name,q)
 A=mlp.load(str(p),{n})[n];c=credit(n,A,str(p));assert c,(n,'source failed')
 raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();rs=q.read_bytes();rh=hashlib.sha256(rs).hexdigest();csvsnap=sn/f'{n}-{h}.csv';csvsnap.write_bytes(raw);jsnap=sn/(rh+'.json');jsnap.write_bytes(rs)
 manifest[str(n)]={**c,'input_file_snapshot':str(csvsnap),'input_file_sha256':h,'input_file_mtime':p.stat().st_mtime,'input_record_snapshots':{str(q):{'snapshot':str(jsnap),'sha256':rh}}};pack[n]=A
for n in [261,367]:subprocess.run(SCP+[str(W/f'control{n}.csv'),'boxE:scratch/squares-k123/'],check=True,timeout=30)
with (D/(pool+'.csv')).open('w') as f:
 wr=csv.writer(f);wr.writerow(['n','square_id','x','y','angle'])
 for n,A in pack.items():wr.writerows((n,i,*a) for i,a in enumerate(A))
(D/('sources-'+pool+'.json')).write_text(json.dumps(manifest));(D/('bars-'+pool+'.tsv')).write_text((W/'bars.tsv').read_text());(D/(pool+'.json')).write_text(json.dumps({'kind':'strip-model-pool','source':'own constructive strip model, exact held15 calibration files261/367','tag':pool}))
for name in [pool+'.csv','sources-'+pool+'.json','bars-'+pool+'.tsv']:subprocess.run(SCP+[str(D/name),'boxE:scratch/squares-k123/'+name],check=True,timeout=30)
for name in ['slide_strip32.py','verify26.py']:
 subprocess.run(SCP+[str(W/name),'boxE:scratch/squares-k123/'+name+'.pending32'],check=True,timeout=30)
 subprocess.run(SSH+[f'cd $SCRATCH/squares-k123 && mv {name}.pending32 {name}'],check=True,timeout=30)
controls=[dict(kind='verify',tag='verify-strip32-engine-control',slide_strip32=True,slide_control31=True),dict(kind='verify',tag='verify-strip32-bounds-control',slide_strip32=True,strip_bound_control32=True)]
for j in controls:
 p=W/(j['tag']+'.json');p.write_text(json.dumps(j));subprocess.run(SCP+[str(p),'boxE:scratch/squares-k123/tasks/'+p.name+'.tmp'],check=True,timeout=30);subprocess.run(SSH+[f'cd $SCRATCH/squares-k123 && mv tasks/{p.name}.tmp tasks/{p.name}'],check=True,timeout=30)
with (T/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA START strip32 controls in existing fourth boxE slot: engine261 and fixed-row positive/negative toy. Poolstrippool32 pins exact held15 controls261/367 and complete sources. New model fixes parents/cells outside one strip and omits inactive-parent collision states. This changes r31 missing-incumbent failure. No target queued before controls pass. Logs out/verify-strip32*.log; cutoff16:25Z.\n')
print('strip source pool and two controls ready',flush=True)
