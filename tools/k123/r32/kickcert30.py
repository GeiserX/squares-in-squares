"""Run a bounded local-kick leg from one immutable certified input."""
from pathlib import Path
import os,sys,json,subprocess,time,hashlib
R=Path.home()/'scratch/squares-k123';os.chdir(R);sys.path[:0]=[str(R/'lane')]
import methods_lp as mlp
from midm_scan import to_fq,quench
PY=str(Path.home()/'scratch/squares-base/venv/bin/python');FQ=str(Path.home()/'scratch/squares-base/fq')
j=json.load(open(sys.argv[1]));digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
if j.get('kick_control'):
 A=mlp.load(str(R/'444-control.csv'),{444})[444].copy();A[:,:2]*=1.0002;s,X=to_fq(A);D=R/'kick-control30';D.mkdir(exist_ok=True);ss,Y=quench(FQ,str(D),s,X,['--loosen','1.0'],timeout=120)
 assert ss is not None and ss<s-1e-4 and abs(ss-21.564693167754)<1e-6,(s,ss)
 result={'n':444,'before':s,'after':ss,'reference':21.564693167754,'code_sha256':digest};(R/'kickcert30-control.json').write_text(json.dumps(result));print(json.dumps(result),flush=True);raise SystemExit
control=json.load((R/'kickcert30-control.json').open());assert control['code_sha256']==digest
n=j['n'];tag=j['tag'];pool=j['pool'];D=R/'out/steps'/tag;D.mkdir(parents=True,exist_ok=True);start=R/(pool+'.csv');assert hashlib.sha256(start.read_bytes()).hexdigest()==j['input_sha256'];bar=mlp.side(mlp.load(str(start),{n})[n])
args=[PY,'-I','lane/midm_scan.py','--n',str(n),'--sub',str(start),'--out',str(D),'--fq',FQ,'--seconds','300','--seed',str(j['seed']),'--modes','lkick,kick','--deadline',str(R/'deadline')]
with (D/'scan.log').open('a') as f:p=subprocess.run(args,stdout=f,stderr=f,timeout=max(1,min(490,float((R/'deadline').read_text())-time.time())))
raw=list((D/'raw').glob('*.csv'));sides=[]
for p0 in raw:
 try:sides.append(mlp.side(mlp.load(str(p0),{n})[n]))
 except Exception:pass
r={'n':n,'tag':tag,'pool':pool,'worker':'steps','bar':bar,'raw':len(raw),'code':p.returncode,'kind':'certified-kick-leg','seconds':300,'side':min(sides) if sides else bar,'source':{'recipe_text':f'midm_scan.py 300s lkick,kick seed{j["seed"]}; one leg of the900s certified-input follow, immutable pool {R}/{pool}.csv','donors':[n]}}
with (R/'out/steps/done.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
print(json.dumps(r),flush=True)
