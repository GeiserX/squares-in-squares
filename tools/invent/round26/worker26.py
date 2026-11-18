import csv,json,os,pathlib,subprocess,sys,time,traceback,signal
D=pathlib.Path(__file__).resolve().parent;os.chdir(D);sys.path.insert(0,str(D/'lane'))
sys.path.insert(0,str(D))
from claim26 import claim,release
import floatsafe,hashlib,io
import pandas as pd
import scipy
assert scipy.__version__=="1.18.1"
PYTHON=os.path.expanduser('$SCRATCH/squares-base/venv/bin/python');FQ=os.path.expanduser('$SCRATCH/squares-base/fq')
DEADLINE=float((D/'deadline').read_text());slot=sys.argv[1]
def stamp():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def log(s):
 with open('pipe.log','a')as h:h.write(stamp()+' '+s+'\n')
def writecsv(p,rows):
 with open(p,'w',newline='')as h:
  w=csv.DictWriter(h,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows(rows)
def run_bounded(cmd,h,seconds):
 timeout=min(seconds,DEADLINE-time.time())
 if timeout<=0:raise TimeoutError('common deadline reached')
 p=subprocess.Popen(cmd,stdout=h,stderr=subprocess.STDOUT,start_new_session=True)
 try:
  p.wait(timeout=timeout)
  if p.returncode:raise RuntimeError('child return code '+str(p.returncode))
 except BaseException:
  try:os.killpg(p.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:p.wait(timeout=3)
  except subprocess.TimeoutExpired:
   os.killpg(p.pid,signal.SIGKILL);p.wait()
  raise

def post(j):
 run=D/j['id'];n=j['n'];raw=sorted((run/'raw').glob('*.csv'),key=lambda p:int(p.stem.split('-')[-1]))
 if not raw:return {'raw':0}
 _,fr,sc,e=floatsafe.work((n,list(csv.DictReader(open(raw[-1])))))
 if fr is None:return {'raw':len(raw),'unsafe':str(raw[-1])}
 ind=run/'certin';out=run/'quench';ind.mkdir(exist_ok=True);out.mkdir(exist_ok=True)
 writecsv(ind/f'{n}.csv',fr);(ind/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n')
 with open(run/'fq.log','a')as h:run_bounded([PYTHON,'-I','lane/midm_fqonce.py',str(ind),str(out),FQ,str(ind/'take.tsv')],h,240)
 best=(sc,fr,str(ind/f'{n}.csv'))
 for p in out.glob('*.csv'):
  _,q,s,e=floatsafe.work((n,list(csv.DictReader(open(p)))))
  if q is not None and s<best[0]:best=(s,q,str(p))
 final=run/'final';final.mkdir(exist_ok=True);writecsv(final/f'{n}.csv',best[1])
 f=final/f'{n}.csv'
 assert (out/f'{n}.done').read_text().strip()==hashlib.sha256((ind/f'{n}.csv').read_bytes()).hexdigest()
 rows=list(csv.DictReader(open(f)));score,why=floatsafe.check(n,rows)
 pandas_rows=floatsafe.via_pandas(rows);pds,pdwhy=floatsafe.check(n,pandas_rows)
 gap=min(floatsafe.clearance(rows),floatsafe.clearance(pandas_rows))
 assert why==pdwhy=='ok' and gap>=2.2e-11 and len(rows)==n
 return {'raw':len(raw),'prequench':sc,'new':score,'pandas_score':pds,'clearance':gap,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'quench_input_sha256':hashlib.sha256((ind/f'{n}.csv').read_bytes()).hexdigest(),'quench_from_certified':True,'selected':best[2]}
valid=[dict(n='2',square_id='0',x='.5',y='.5',angle='0'),dict(n='2',square_id='1',x='1.5001',y='.5',angle='0')]
assert floatsafe.check(2,valid)[1]=='ok'
valid[1]['x']='.5';assert floatsafe.check(2,valid)[1]!='ok'
print('CONTROL metric accepted separated n2 and rejected duplicate overlap',flush=True)
(D/'locks').mkdir(exist_ok=True)
while time.time()<float((D/'search-deadline').read_text()) and not(D/'STOP26').exists():
 try:jobs=json.load(open('queue'+slot+'.json'))
 except Exception:time.sleep(5);continue
 job=None
 for j in jobs:
  if j['kind']!='control'and not(D/'CONTROL_GREEN').exists():continue
  if claim(D,j):job=j;break
 if job is None:time.sleep(5);continue
 j=job;run=D/j['id'];run.mkdir(exist_ok=True);result={'id':j['id'],'slot':slot,'started':stamp()}
 log(f'slot={slot} START {j["id"]} n={j["n"]} kind={j["kind"]}')
 try:
  seconds=min(j['seconds'],DEADLINE-time.time()-245)
  cmd=[PYTHON,'-I','lane/invent_rest.py',str(j['n']),j['start'],j['id'],'--seconds',str(seconds),'--seed',str(j['seed']),'--modes','lkick','--bar',str(j['bar']),'--deadline','deadline']
  if j.get('fq'):cmd+=['--fq',FQ]
  with open(run/'run.log','a')as h:run_bounded(cmd,h,seconds+100)
  result.update(post(j))
 except Exception as ex:result['error']=str(ex);traceback.print_exc()
 result['ended']=stamp();p=run/'done.json.tmp';p.write_text(json.dumps(result));p.replace(run/'done.json')
 log(f'slot={slot} END {j["id"]} {result}');release(D,j)
log(f'slot={slot} STOP')
