"""Three bounded boxE workers. Compare every certified candidate before fq."""
import os,sys,pathlib,json,csv,math,hashlib,time,subprocess,signal,traceback
D=pathlib.Path(__file__).resolve().parent;os.chdir(D);sys.path.insert(0,str(D/'lane'));sys.path.insert(0,str(D))
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
import scipy,numpy as np,pandas as pd
assert scipy.__version__=='1.18.1'
import floatsafe,finesafe
PYTHON=os.path.expanduser('$SCRATCH/squares-base/venv/bin/python');FQ=os.path.expanduser('$SCRATCH/squares-base/fq')
DEADLINE=float((D/'deadline').read_text());ADMIT=float((D/'search-deadline').read_text());SLOT=sys.argv[1]
def stamp():return time.strftime('%FT%TZ',time.gmtime())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def atomic(p,x):
 p=pathlib.Path(p);q=p.with_suffix(p.suffix+'.tmp'+SLOT);q.write_text(json.dumps(x));q.replace(p)
def log(s):
 with (D/'pipe.log').open('a') as h:h.write(stamp()+' '+s+'\n')
def writecsv(p,rows):
 with pathlib.Path(p).open('w',newline='')as h:
  w=csv.DictWriter(h,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows(rows)
from certify31 import certify
from early32 import export as export_early, controls as checkpoint_controls

def bounded(cmd,h,timeout,probe=None,run=None,side=None):
 p=subprocess.Popen(cmd,stdout=h,stderr=subprocess.STDOUT,start_new_session=True);begin=time.time();reason='normal'
 try:
  while p.poll()is None:
   elapsed=time.time()-begin
   if elapsed>=min(timeout,DEADLINE-begin):reason='hard-timeout';break
   if probe and elapsed>=probe:
    found=False
    for f in (run/'raw').glob('*.csv'):
     try:
      import methods_lp as mlp
      a=mlp.load(str(f),{int(f.stem.split('-')[0])});v=next(iter(a.values()));found=found or mlp.side(v)<side-1e-8
     except Exception:pass
    if not found:reason='dry-probe';break
    probe=None
   time.sleep(1)
  if p.poll()is None:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(4)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
  elif p.returncode:raise RuntimeError('child exit '+str(p.returncode))
 finally:
  if p.poll()is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
 return reason

def post(j,run):
 n=j['n'];raw=list((run/'raw').glob('*.csv'));candidates=[];certrows=[];unique=set()
 for p in [D/j['start']]+raw:
  v=certify(p,n)
  if v is None:continue
  encoded=json.dumps(v[1],sort_keys=True);digest=hashlib.sha256(encoded.encode()).hexdigest()
  certrows.append(dict(path=str(p),score=v[2],dilation=v[3],certified_rows_sha256=digest))
  if digest not in unique:candidates.append((v[2],str(p),v[1]));unique.add(digest)
 atomic(run/'certification.json',certrows)
 if not candidates:return dict(raw=len(raw),unsafe=True)
 candidates.sort(key=lambda v:v[0]);finished=[];best=None;truncated=False
 for index,(score,origin,rows)in enumerate(candidates):
  if time.time()>=DEADLINE-5:truncated=True;break
  folder=run/'candidates'/str(index);ind=folder/'certin';out=folder/'quench';ind.mkdir(parents=True,exist_ok=True);out.mkdir(exist_ok=True)
  writecsv(ind/f'{n}.csv',rows);(ind/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n')
  try:
   with (folder/'fq.log').open('a')as h:bounded([PYTHON,'-I','lane/midm_fqonce.py',str(ind),str(out),FQ,str(ind/'take.tsv')],h,240)
   assert(out/f'{n}.done').read_text().strip()==sha(ind/f'{n}.csv')
  except Exception as error:
   finished.append(dict(origin=origin,error=repr(error)))
   continue
  local=(score,rows,str(ind/f'{n}.csv'))
  for p in out.glob('*.csv'):
   v=certify(p,n)
   if v and v[2]<local[0]:local=(v[2],v[1],str(p))
  receipt=dict(origin=origin,certified_input=str(ind/f'{n}.csv'),quench_input_sha256=sha(ind/f'{n}.csv'),new=local[0],quench_from_certified=True)
  finished.append(receipt)
  if j['kind']!='control':export_early(D,j,index,local[1],ind/f'{n}.csv',out/f'{n}.done',local[2])
  if best is None or local[0]<best[0]:best=(*local,origin,score,ind,out)
  atomic(run/'candidate-quenches.json',finished)
 if best is None:raise RuntimeError('no candidate completed its certified-input quench')
 import shutil
 ind=run/'certin';out=run/'quench';ind.mkdir(exist_ok=True);out.mkdir(exist_ok=True)
 shutil.copyfile(best[5]/f'{n}.csv',ind/f'{n}.csv');shutil.copyfile(best[6]/f'{n}.done',out/f'{n}.done')
 final=run/'final';final.mkdir(exist_ok=True);f=final/f'{n}.csv';writecsv(f,best[1])
 rr=list(csv.DictReader(open(f)));sc,why=floatsafe.check(n,rr);scpd,pdwhy=floatsafe.check(n,floatsafe.via_pandas(rr));gap=min(floatsafe.clearance(rr),floatsafe.clearance(floatsafe.via_pandas(rr)))
 assert why==pdwhy=='ok'and gap>=2.2e-11 and math.isfinite(sc)
 return dict(raw=len(raw),certified_candidates=len(certrows),unique_certified_candidates=len(candidates),candidate_quenches=finished,finish_truncated=truncated,prequench=best[4],certified_origin=best[3],new=sc,pandas_score=scpd,clearance=gap,sha256=sha(f),quench_input_sha256=sha(ind/f'{n}.csv'),quench_from_certified=True,selected=best[2])

# Positive and negative metric controls before any numerical dispatch.
rows=[dict(n='2',square_id=str(i),x=str(.5+i*1.0001),y='.5',angle='0')for i in range(2)]
assert floatsafe.check(2,rows)[1]=='ok';rows[1]['x']='.5';assert floatsafe.check(2,rows)[1]!='ok'
log('slot='+SLOT+' CONTROL separated n2 accepted; duplicate overlap refused')
log('slot='+SLOT+' CHECKPOINT CONTROLS '+json.dumps(checkpoint_controls(D,SLOT)))
(D/'locks').mkdir(exist_ok=True);(D/'active').mkdir(exist_ok=True)
while time.time()<ADMIT and not(D/'STOP32FINAL').exists():
 try:queue=json.load(open(D/'queue.json'))
 except Exception:time.sleep(3);continue
 job=None
 for j in queue:
  if j['kind']!='control'and(not(D/'CONTROL_GREEN').exists()or not(D/'ALL_FINISH_GREEN').exists()):continue
  lock=D/'locks'/j['id'];active=D/'active'/str(j['n'])
  try:lock.mkdir()
  except FileExistsError:continue
  try:active.mkdir()
  except FileExistsError:lock.rmdir();continue
  job=j;break
 if job is None:time.sleep(3);continue
 j=job;run=D/j['id'];run.mkdir(exist_ok=True);result=dict(id=j['id'],n=j['n'],slot=SLOT,started=stamp(),program=j['program'],input_sha256=j['input_sha256'])
 try:
  assert sha(D/j['start'])==j['input_sha256'],'changed immutable start'
  log(f'slot={SLOT} START '+j['id'])
  seconds=min(j['seconds'],DEADLINE-time.time()-245)
  if seconds<0:raise TimeoutError('insufficient common deadline')
  if j['program']=='midm':
   cmd=[PYTHON,'-I','lane/midm_scan.py','--n',str(j['n']),'--sub',j['start'],'--out',j['id'],'--fq',FQ,'--seconds',str(seconds),'--seed',str(j['seed']),'--modes','lkick,kick','--deadline','deadline']
  else:
   cmd=[PYTHON,'-I',j['program'],str(j['n']),j['start'],j['id'],'--seconds',str(seconds),'--seed',str(j['seed']),'--modes','lkick','--bar',str(j['bar']),'--deadline','deadline','--plateau-stop','0','--try-seconds','90']+j.get('options',[])
  with (run/'run.log').open('a')as h:result['search_end']=bounded(cmd,h,seconds+95,probe=j.get('probe'),run=run,side=j['side'])
  result.update(post(j,run))
 except Exception as ex:result['error']=str(ex);traceback.print_exc()
 result['ended']=stamp();atomic(run/'done.json',result);log(f'slot={SLOT} END '+j['id']+' '+json.dumps(result));(D/'active'/str(j['n'])).rmdir()
log('slot='+SLOT+' STOP')
