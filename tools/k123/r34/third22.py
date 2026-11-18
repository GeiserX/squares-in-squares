"""Run scans, step builds and certification quenches in the third boxE slot."""
import pathlib,os,time,json,subprocess,signal,sys
R=pathlib.Path.home()/'scratch/squares-k123';os.chdir(R)
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
runtime=json.load((R/'runtime33.json').open()) if (R/'runtime33.json').exists() else {}
PY=runtime.get('python',str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python'));FQ=runtime.get('fq',str(pathlib.Path.home()/'scratch/squares-base/fq'))
running=R/'running34/worker';running.mkdir(parents=True,exist_ok=True)
for previous in running.glob('*.json'):
 if (R/'taskdone'/previous.name).exists():previous.unlink()
 else:previous.replace(R/'tasks'/previous.name)
(R/'tasks').mkdir(exist_ok=True);(R/'taskdone').mkdir(exist_ok=True)
def run(args,log,cap=600):
 with open(log,'a') as h:
  p=subprocess.Popen(args,stdout=h,stderr=h,start_new_session=True)
  try:return p.wait(timeout=max(1,min(cap,float((R/'deadline').read_text())-time.time())))
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();return -2
while time.time()<float((R/'deadline').read_text()):
 jobs=sorted((R/'tasks').glob('*.json'),key=lambda p:(not p.name.startswith(('cert-','verify-')),not p.name.startswith(('licensed','rebuild')), -p.stat().st_mtime))
 if time.time()>=float((R/'search-deadline').read_text()):jobs=[p for p in jobs if json.load(open(p)).get('kind') in ('cert','verify')]
 if '--cert-only' in sys.argv:jobs=[p for p in jobs if json.load(open(p)).get('kind') in ('cert','verify')]
 if not jobs:
  if '--cert-only' in sys.argv:
   time.sleep(2);continue
  
  if time.time()<float((R/'search-deadline').read_text()):run([PY,'-I','qrun22.py',runtime.get('spare_join','j22c'),'--once'],'out/j22c.log')
  time.sleep(1);continue
 p=jobs[0]
 try:j=json.load(open(p))
 except (json.JSONDecodeError,FileNotFoundError):
  time.sleep(1);continue
 try:
  claimed=running/p.name;p.replace(claimed);p=claimed
 except FileNotFoundError:continue
 tag=j['tag'];kind=j['kind']
 gate_ok=True
 if kind=='scan':
  meta=json.load(open(R/f'sources-{tag}.json'));gate_ok=all(c.get('seed_share_gate')=='v6' for c in meta.values())
 if kind=='scan' and not gate_ok:rc=-3
 elif kind=='scan':
  pairs=(R/f'pairs-{tag}.txt').read_text().split()
  rc=run([PY,'-I','lane/k123_join.py','scan',f'{tag}.csv',f'bars-{tag}.tsv',f'scan{tag}',*pairs,'--rmax','.3','--pmax','.3','--room','-.1','--mmin','10'],f'out/scan{tag}.log')
  if rc==0:
   rc=run([PY,'-I','sel21.py',f'q{tag}.txt','4',f'out/scan{tag}.log'],f'out/sel{tag}.log')
   q=R/f'q{tag}.txt'
   if q.exists():
    rows=[]
    for l in q.read_text().splitlines():
     w=l.split('\t')
     if float(w[3])>.09 or float(w[5])>.05:continue
     w.append(tag);rows.append('\t'.join(w)+'\n')
    # Single producer appends. Workers take a snapshot on each pass.
    with open(R/'queue.tsv','a') as f:f.writelines(rows)
   import shutil
  shutil.rmtree(R/f'scan{tag}',ignore_errors=True)
 elif kind=='verify':
  rc=run([PY,'-I','verify26.py',str(p)],f'out/{tag}.log',cap=990 if j.get('held_probe31') else 600)
 elif kind=='step':
  rc=run([PY,'-I','lane/k123_step.py',j.get('pool','pool0')+'.csv',str(j['n']),tag,'--rows',str(j['rows']),'--chains',str(j['chains']),'--target',str(j['target']),'--top','8'],f'out/{tag}.log')
 elif kind=='stepq':
  rc=run([PY,'-I','stepquench22.py',str(p)],f'out/{tag}-q.log')
 elif kind=='cert':
  rc=run([PY,'-I','cert_once22.py',j['in'],j['out'],FQ,j['take']],f'out/{tag}.log')
 j['rc']=rc;j['ended']=time.strftime('%FT%TZ',time.gmtime());done=R/'taskdone'/p.name;tmp=done.with_name(done.name+'.tmp');tmp.write_text(json.dumps(j));tmp.replace(done);p.unlink()
