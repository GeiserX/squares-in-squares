from pathlib import Path
import sys,json,csv,hashlib,subprocess,time,os
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')];os.environ['K123_BASE_SECONDS32']='20'
from provenance24 import mlp,key,credit
n=790;p=W.parent/f'{n}.csv';A=mlp.load(str(p),{n})[n];want=key(n,A);c=None
for mp in sorted(W.glob('fresh*/sources-fresh*.json')):
 z=json.loads(mp.read_text()).get(str(n))
 if z and z.get('sha256_geometry')==want and Path(z.get('input_file_snapshot','')).is_file():c=z;break
assert c,'current fresh790 has no pinned source manifest'
pool='general34n790';D=W/pool;D.mkdir(exist_ok=True);snapshot=Path(c['input_file_snapshot']);assert key(n,mlp.load(str(snapshot),{n})[n])==want
(D/(pool+'.csv')).write_bytes(snapshot.read_bytes());(D/('sources-'+pool+'.json')).write_text(json.dumps({str(n):c}));(D/('bars-'+pool+'.tsv')).write_text((W/'bars.tsv').read_text())
for p in D.iterdir():subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r35-boxE',str(p),'boxE:scratch/squares-k123/'],check=True)
j=dict(kind='verify',tag='verify-generalmask34-control790',general_mask34=True,seed_n=n,pool=pool,control=True,seconds=0)
p=W/(j['tag']+'.json');p.write_text(json.dumps(j));subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r35-boxE',str(p),'boxE:scratch/squares-k123/tasks/'],check=True)
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA START complete-layout mask control on fresh790 using its exact pinned source. This removes the single-block assumption that refused367 (only4 of107 tilted cells lay on its grid). Nine upright phases plus virtual per-cell rotations/translations, frozen far cells, same controlled integer exchanges. The whole790 source must reconstruct within2e-6 before target791. Existing boxE slot, no new numerical process. cutoff16:25Z.\n')
print('fresh790 control queued')
