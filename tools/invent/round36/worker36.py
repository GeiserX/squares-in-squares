"""Round 36 invent boxE worker: one slot. Takes jobs from queue.json (lock per job id and per n), runs the
search (invent_barretain_budget30.py lkick, or midm_scan.py), certifies every raw find with finesafe (2.2e-11),
runs the full fq loop (midm_fqonce.py: default flags then polish, up to three rounds) on each certified candidate,
certifies the quench output and writes done.json plus final/<n>.csv. Load guard 16."""
import os,sys,pathlib,json,csv,math,hashlib,time,subprocess,signal,traceback,shutil
D=pathlib.Path(__file__).resolve().parent;os.chdir(D);sys.path.insert(0,str(D/'lane'));sys.path.insert(0,str(D))
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
import scipy,numpy as np
assert scipy.__version__=='1.18.1'
import floatsafe,finesafe
from certify31 import certify
import methods_lp as mlp
PYTHON=os.path.expanduser('$SCRATCH/squares-base/venv/bin/python');FQ=os.path.expanduser('$SCRATCH/squares-base/fq')
DEADLINE=float((D/'deadline').read_text());ADMIT=float((D/'search-deadline').read_text());SLOT=sys.argv[1]
def stamp():return time.strftime('%FT%TZ',time.gmtime())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def atomic(p,x):
 p=pathlib.Path(p);q=p.with_suffix(p.suffix+'.tmp'+SLOT);q.write_text(json.dumps(x));q.replace(p)
def log(s):
 with (D/'pipe.log').open('a') as h:h.write(stamp()+' slot='+SLOT+' '+s+'\n')
def writecsv(p,rows):
 with pathlib.Path(p).open('w',newline='')as h:
  w=csv.DictWriter(h,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows([{k:r[k] for k in ('n','square_id','x','y','angle')} for r in rows])

def bounded(cmd,h,timeout):
 p=subprocess.Popen(cmd,stdout=h,stderr=subprocess.STDOUT,start_new_session=True);begin=time.time();reason='normal'
 try:
  while p.poll()is None:
   if time.time()-begin>=timeout or time.time()>=DEADLINE or (D/'STOP').exists():reason='hard-timeout';break
   if (D/'kill'/CUR).exists():reason='killed';break
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
 n=j['n'];raw=sorted((run/'raw').glob('*.csv'));cands=[];seen=set()
 for p in [D/j['start']]+raw:
  try:v=certify(p,n)
  except Exception as e:log('certify error '+str(p)+' '+repr(e));v=None
  if v is None:continue
  dg=hashlib.sha256(json.dumps(v[1],sort_keys=True).encode()).hexdigest()
  if dg in seen:continue
  seen.add(dg);cands.append((v[2],str(p),v[1]))
 if not cands:return dict(raw=len(raw),unsafe=True)
 cands.sort(key=lambda v:v[0]);cands=cands[:4];best=None;fin=[]
 for i,(score,origin,rows) in enumerate(cands):
  if time.time()>=DEADLINE-30:break
  f=run/'cand'/str(i);ind=f/'certin';out=f/'quench';ind.mkdir(parents=True,exist_ok=True);out.mkdir(exist_ok=True)
  writecsv(ind/f'{n}.csv',rows);(ind/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n')
  try:
   with (f/'fq.log').open('a')as h:bounded([PYTHON,'-I','lane/midm_fqonce.py',str(ind),str(out),FQ,str(ind/'take.tsv')],h,600)
   assert (out/f'{n}.done').exists()
  except Exception as e:fin.append(dict(origin=origin,error=repr(e)));continue
  local=(score,rows,str(ind/f'{n}.csv'))
  for p in out.glob('*.csv'):
   v=certify(p,n)
   if v and v[2]<local[0]:local=(v[2],v[1],str(p))
  fin.append(dict(origin=origin,certified=score,quenched=local[0]))
  if best is None or local[0]<best[0]:best=(*local,origin)
 if best is None:return dict(raw=len(raw),error='no quench completed',cands=fin)
 final=run/'final';final.mkdir(exist_ok=True);f=final/f'{n}.csv';writecsv(f,best[1])
 rr=list(csv.DictReader(open(f)));sc,why=floatsafe.check(n,rr);pd_,pw=floatsafe.check(n,floatsafe.via_pandas(rr))
 gap=min(floatsafe.clearance(rr),floatsafe.clearance(floatsafe.via_pandas(rr)))
 ok=why==pw=='ok' and gap>=2.2e-11 and math.isfinite(sc)
 return dict(raw=len(raw),cands=fin,new=sc,pandas_score=pd_,clearance=gap,certified_ok=ok,sha256=sha(f),selected=best[2],origin=best[3])

CUR='none'
rows=[dict(n='2',square_id=str(i),x=str(.5+i*1.0001),y='.5',angle='0')for i in range(2)]
assert floatsafe.check(2,rows)[1]=='ok';rows[1]['x']='.5';assert floatsafe.check(2,rows)[1]!='ok'
log('CONTROL separated n2 accepted; overlap refused')
(D/'locks').mkdir(exist_ok=True);(D/'active').mkdir(exist_ok=True);(D/'kill').mkdir(exist_ok=True)
while time.time()<ADMIT and not(D/'STOP').exists():
 try:queue=json.load(open(D/'queue.json'))
 except Exception:time.sleep(5);continue
 if os.getloadavg()[0]>16:log('LOADGUARD '+str(os.getloadavg()[0]));time.sleep(30);continue
 job=None
 for j in sorted(queue,key=lambda j:j.get('priority',0)):
  if (D/'runs'/j['id']/'done.json').exists() or not (D/j['start']).exists():continue
  lock=D/'locks'/j['id'];active=D/'active'/str(j['n'])
  try:lock.mkdir()
  except FileExistsError:continue
  try:active.mkdir()
  except FileExistsError:lock.rmdir();continue
  job=j;break
 if job is None:time.sleep(5);continue
 j=job;CUR=j['id'];run=D/'runs'/j['id'];run.mkdir(parents=True,exist_ok=True);res=dict(id=j['id'],n=j['n'],slot=SLOT,started=stamp(),program=j['program'],input_sha256=j['input_sha256'])
 try:
  assert sha(D/j['start'])==j['input_sha256'],'changed start'
  log('START '+j['id'])
  seconds=min(j['seconds'],DEADLINE-time.time()-700)
  if seconds<60:raise TimeoutError('insufficient deadline')
  if j['program']=='midm':
   cmd=[PYTHON,'-I','lane/midm_scan.py','--n',str(j['n']),'--sub',j['start'],'--out',str(run),'--fq',FQ,'--seconds',str(int(seconds)),'--seed',str(j['seed']),'--modes','lkick,kick','--deadline','deadline']
  else:
   cmd=[PYTHON,'-I','invent_barretain_budget30.py',str(j['n']),j['start'],str(run),'--seconds',str(int(seconds)),'--seed',str(j['seed']),'--modes',j.get('modes','lkick'),'--bar',str(j['bar']),'--deadline','deadline','--plateau-stop','0','--try-seconds','90']+j.get('options',[])
  with (run/'run.log').open('a')as h:res['search_end']=bounded(cmd,h,seconds+95)
  res.update(post(j,run))
 except Exception as ex:res['error']=repr(ex);traceback.print_exc()
 res['ended']=stamp();atomic(run/'done.json',res);log('END '+json.dumps(res)[:600])
 try:(D/'active'/str(j['n'])).rmdir()
 except OSError:pass
log('STOP')
