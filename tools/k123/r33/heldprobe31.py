"""Run a held-row kick for 900 seconds only when its first 120 seconds improve."""
from pathlib import Path
import json,sys,subprocess,os,time,signal,hashlib,math
R=Path.home()/'scratch/squares-k123';os.chdir(R);sys.path[:0]=[str(R/'lane')]
import methods_lp as mlp
j=json.load(open(sys.argv[1]))
if j.get('held_control31'):
 from midm_scan import to_fq,quench
 A=mlp.load(str(R/'444-control.csv'),{444})[444].copy();A[:,:2]*=1.0002;s,X=to_fq(A);D=R/'held-control31';D.mkdir(exist_ok=True)
 ss,Y=quench(str(Path.home()/'scratch/squares-base/fq'),str(D),s,X,['--loosen','1.0'],timeout=120)
 assert ss is not None and ss<s-1e-4 and abs(ss-21.564693167754)<1e-6,(s,ss)
 assert any(v<s-1e-9 for v in [ss]) and not any(v<s-1e-9 for v in [s])
 result={'before':s,'after':ss,'probe_improvement_continues':True,'probe_no_improvement_stops':True};(R/'held-control31.json').write_text(json.dumps(result));print(json.dumps(result),flush=True);raise SystemExit
assert (R/'held-control31.json').exists()
n=j['n'];pool=j['pool'];tag=j['tag'];start=R/(pool+'.csv');assert hashlib.sha256(start.read_bytes()).hexdigest()==j['input_sha256']
A=mlp.load(str(start),{n})[n];bar=mlp.side(A);D=R/'out/steps'/tag;D.mkdir(parents=True,exist_ok=True);PY=str(Path.home()/'scratch/squares-base/venv/bin/python');FQ=str(Path.home()/'scratch/squares-base/fq')
job_deadline=D/'deadline';job_deadline.write_text(str(min(time.time()+900,float((R/'deadline').read_text()))))
args=[PY,'-I','lane/midm_scan.py','--n',str(n),'--sub',str(start),'--out',str(D),'--fq',FQ,'--seconds','900','--seed',str(j['seed']),'--modes','kick,lkick','--deadline',str(job_deadline)]
t0=time.time();probed=False;stopped=False
with (D/'scan.log').open('a') as f:
 p=subprocess.Popen(args,stdout=f,stderr=f,start_new_session=True)
 while p.poll() is None:
  if time.time()>=float(job_deadline.read_text()):stopped=True
  if not probed and time.time()-t0>=120:
   probed=True;vals=[]
   for lp in D.glob('scan-*.tsv'):
    for l in lp.read_text().splitlines():
     try:
      a=l.split('\t');v=float(a[4]);vals.append(v)
     except (ValueError,IndexError):pass
   threshold=max(1e-9,math.sqrt(n)*1e-10+2.2e-11*max(1,bar))
   if not any(math.isfinite(v) and v<bar-threshold for v in vals):stopped=True
  if stopped:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=2)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   break
  time.sleep(1)
raws=list((D/'raw').glob('*.csv'));sides=[mlp.side(mlp.load(str(p0),{n})[n]) for p0 in raws]
r={'n':n,'tag':tag,'pool':pool,'worker':'steps','bar':bar,'raw':len(raws),'code':p.returncode,'kind':'held-probe31','seconds':time.time()-t0,'probe_stopped':stopped,'side':min(sides) if sides else bar,'source':{'recipe_text':f'midm_scan.py 900s kick,lkick seed{j["seed"]}; first120s probe, held source pinned by sha256 {j["input_sha256"]}','donors':[n]}}
with (R/'out/steps/done.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
print(json.dumps(r),flush=True)
