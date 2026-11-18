"""Run scans, step builds and certification quenches in the third boxE slot."""
import pathlib,os,time,json,subprocess,signal,sys
R=pathlib.Path.home()/'scratch/squares-k123';os.chdir(R)
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
PY=str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python')
(R/'tasks').mkdir(exist_ok=True);(R/'taskdone').mkdir(exist_ok=True)
def run(args,log):
 with open(log,'a') as h:
  p=subprocess.Popen(args,stdout=h,stderr=h,start_new_session=True)
  try:return p.wait(timeout=max(1,min(600,float((R/'deadline').read_text())-time.time())))
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();return -2
while time.time()<float((R/'deadline').read_text()):
 jobs=sorted((R/'tasks').glob('*.json'))
 if '--cert-only' in sys.argv:jobs=[p for p in jobs if json.load(open(p)).get('kind')=='cert']
 if not jobs:
  if '--cert-only' in sys.argv:
   time.sleep(2);continue
  run([PY,'-I','qrun22.py','j22c','--once'],'out/j22c.log')
  time.sleep(1);continue
 p=jobs[0];j=json.load(open(p));tag=j['tag'];kind=j['kind']
 if kind=='scan':
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
 elif kind=='step':
  rc=run([PY,'-I','lane/k123_step.py',j.get('pool','pool0')+'.csv',str(j['n']),tag,'--rows',str(j['rows']),'--chains',str(j['chains']),'--target',str(j['target']),'--top','8'],f'out/{tag}.log')
 elif kind=='stepq':
  rc=run([PY,'-I','stepquench22.py',str(p)],f'out/{tag}-q.log')
 elif kind=='cert':
  rc=run([PY,'-I','cert_once22.py',j['in'],j['out'],str(pathlib.Path.home()/'scratch/squares-base/fq'),j['take']],f'out/{tag}.log')
 j['rc']=rc;j['ended']=time.strftime('%FT%TZ',time.gmtime());(R/'taskdone'/p.name).write_text(json.dumps(j));p.unlink()
