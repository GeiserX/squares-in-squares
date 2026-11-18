"""Certify a near donor and quench from the certified bytes in the shared boxE slot."""
from pathlib import Path
import sys,json,csv,hashlib,subprocess,shutil,math
R=Path.home()/'scratch/squares-k123';sys.path.insert(0,str(R/'lane'))
import finesafe,floatsafe
job=json.load(open(sys.argv[1]));n=int(job['n']);D=R/job['out'];D.mkdir(parents=True,exist_ok=True);rows=list(csv.DictReader(open(R/job['raw'])))
a=finesafe.work((n,rows));assert a[1] is not None,a
C=D/'certified';C.mkdir(exist_ok=True)
def write(p,rs):
 with p.open('w') as f:
  w=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows(rs)
p=C/f'{n}.csv';write(p,a[1]);cfg=json.load(open(R/'runtime33.json'))
subprocess.run([cfg['python'],'-I',str(R/'cert_once22.py'),str(C),str(D/'fq'),cfg['fq'],''],check=True,timeout=1110)
receipt=json.load(open(D/'fq'/f'{n}-quench.json'));assert receipt['completed'] and receipt['full_fq_loop']
b=finesafe.work((n,list(csv.DictReader(open(D/'fq'/f'{n}-fq-tight.csv')))));assert b[1] is not None
best=min([a,b],key=lambda z:z[2]);out=D/f'{n}.csv';write(out,best[1]);written=list(csv.DictReader(open(out)));assert floatsafe.clearance(written)>=2.2e-11
assert floatsafe.check(n,written)[1]=='ok';assert floatsafe.check(n,floatsafe.via_pandas(written))[1]=='ok'
result={'n':n,'score':best[2],'side':(best[2]+1)*math.sqrt(n),'clearance':floatsafe.clearance(written),'csv_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'full_fq_loop':True,'fq':receipt}
(D/'result36.json').write_text(json.dumps(result));print(json.dumps(result),flush=True)
