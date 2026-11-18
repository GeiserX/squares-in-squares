import csv, json, os, pathlib, subprocess, sys, time, traceback
D=pathlib.Path(__file__).resolve().parent
os.chdir(D)
sys.path.insert(0,str(D/'lane'))
import floatsafe
PYTHON=os.path.expanduser('$SCRATCH/squares-base/venv/bin/python')
FQ=os.path.expanduser('$SCRATCH/squares-base/fq')

def stamp(): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
def log(s):
 with open('pipe.log','a') as h: h.write(stamp()+' '+s+'\n')
def writecsv(p,rows):
 with open(p,'w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows(rows)
def post(j):
 run=D/j['id']; n=j['n']; raw=sorted((run/'raw').glob('*.csv'),key=lambda p:int(p.stem.split('-')[-1]))
 if not raw: return {'raw':0}
 p=raw[-1]
 rows=list(csv.DictReader(open(p)))
 _,fr,sc,e=floatsafe.work((n,rows))
 if fr is None: return {'raw':len(raw),'unsafe':str(p)}
 ind=run/'certin';out=run/'quench';ind.mkdir(exist_ok=True);out.mkdir(exist_ok=True)
 writecsv(ind/f'{n}.csv',fr)
 (ind/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n')
 with open(run/'fq.log','a') as h:
  subprocess.run([PYTHON,'-I','lane/midm_fqonce.py',str(ind),str(out),FQ,str(ind/'take.tsv')],stdout=h,stderr=subprocess.STDOUT,check=True,timeout=240)
 candidates=[ind/f'{n}.csv']+list(out.glob('*.csv'))
 best=(sc,fr,str(ind/f'{n}.csv'))
 for p in candidates[1:]:
  _,q,s,e=floatsafe.work((n,list(csv.DictReader(open(p)))))
  if q is not None and s<best[0]: best=(s,q,str(p))
 final=run/'final';final.mkdir(exist_ok=True);writecsv(final/f'{n}.csv',best[1])
 return {'raw':len(raw),'prequench':sc,'new':best[0],'quench_from_certified':True,'selected':best[2]}
slot=sys.argv[1]
(D/'locks').mkdir(exist_ok=True)
while time.time()<float((D/'deadline').read_text())-120 and not (D/'STOP').exists():
 try: jobs=json.load(open('queue.json'))
 except Exception: time.sleep(5);continue
 job=None
 for j in jobs:
  try: (D/'locks'/j['id']).mkdir(); job=j;break
  except FileExistsError: pass
 if job is None: time.sleep(10);continue
 j=job;run=D/j['id'];run.mkdir(exist_ok=True)
 log(f'slot={slot} START {j["id"]} n={j["n"]} kind={j["kind"]}')
 result={'id':j['id'],'started':stamp()}
 try:
  cmd=[PYTHON,'-I','lane/invent_rest.py',str(j['n']),j['start'],j['id'],'--seconds',str(j['seconds']),'--seed',str(j['seed']),'--modes','lkick','--bar',str(j['bar']),'--deadline','deadline']
  if j.get('fq'):cmd+=['--fq',FQ]
  with open(run/'run.log','a') as h:
   subprocess.run(cmd,stdout=h,stderr=subprocess.STDOUT,check=True,timeout=j['seconds']+150)
  result.update(post(j))
 except Exception as ex:
  result['error']=str(ex); traceback.print_exc()
 result['ended']=stamp()
 tmp=run/'done.json.tmp';tmp.write_text(json.dumps(result));tmp.replace(run/'done.json')
 log(f'slot={slot} END {j["id"]} {result}')
log(f'slot={slot} STOP')
