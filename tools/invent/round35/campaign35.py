"""Follow changed owned geometry within three deadline-bound boxE slots (round 35)."""
import pathlib,sys,json,time,math,csv,traceback,hashlib,os
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
import campaign35base as C
from invent_shape22 import fingerprint
import numpy as np
T=C.T;S=C.S
GEOMETRY_LANES=('forensics','k123','classfill','modules','stair-c','soft')

_signature_cache={}
def source_signature(p):
 paths=[pathlib.Path(str(p)+v)for v in('.json','.origin.json','.source.json','.provenance.json')]+[p.with_suffix('.json')]
 result=[]
 for q in paths:
  if not q.is_file():continue
  st=q.stat();key=(str(q),st.st_mtime_ns,st.st_size)
  if key not in _signature_cache:_signature_cache[key]=C.sha(q)
  result.append([str(q),_signature_cache[key]])
 return result

def identity(p,n=None):
 rows=list(csv.DictReader(open(p)));n=int(rows[0]['n'])if n is None else n
 if len(rows)!=n or not all(int(r['n'])==n for r in rows):raise ValueError('packing count')
 a=np.array([[float(r['x']),float(r['y']),float(r['angle'])]for r in rows]);return n,float(C.mlp.side(a)),fingerprint(a)

def lattice(p):
 a=C.mlp.load(str(p));return C.is_lattice(next(iter(a.values())))

def init_history():
 if not(W/'held-shapes35.json').exists():
  groups=C.mlp.load(str(S/'gather/round34-2026-11-17a.csv'));C.atomic(W/'held-shapes35.json',sorted({fingerprint(v)for v in groups.values()}));del groups
 if (W/'historical-fingerprints.json').exists():return
 seen=set();files=0
 for rnd in range(21,35):
  old=S/f'take-invent-r{rnd}/work'
  for j in C.load(old/'jobs.json',[]):
   if j['kind']=='control'or not(old/'boxE-raw'/j['id']/'done.json').exists():continue
   p=pathlib.Path(j['start']);p=p if p.is_absolute()else old/p
   try:seen.add(identity(p,j['n'])[2]);files+=1
   except (OSError,ValueError,KeyError):pass
 C.atomic(W/'historical-fingerprints.json',sorted(seen));C.state(f'HISTORY {files} completed earlier starts, {len(seen)} distinct geometries. Unchanged geometry stays closed.')

def initial989(peer):
 if (W/'late989-admitted').exists():return []
 j=C.load(W/'late989-parent.json',{});p=W/'boxE-raw'/j['id']/'final/989.csv'
 if C.claimed(C.sha(p),(S/'handoff-r35.log').read_text().splitlines()):
  C.atomic(W/'late989-skipped.json',dict(reason='rebuild claimed exact late989 bytes first',sha256=C.sha(p),time=C.now()));(W/'late989-admitted').write_text('skipped exact-byte claim');C.state('SKIP late989: rebuild already claimed exact bytes; no duplicate kick.');return []
 result,why=C.produce_input(p,989,'leg',3228,peer,dict(parent_job=j))
 if result is None:raise ValueError('late989 extension refused: '+str(why))
 result['priority']=-8;result['round31_parent']=j['id'];(W/'late989-admitted').write_text(C.now());return [result]

def turn():
 jobs,done,peer=C.collect()
 wide_control=done.get('control907-wide32',{})
 if wide_control.get('quench_from_certified')and wide_control.get('clearance',0)>=2.2e-11 and (wide_control.get('new',99)+1)*math.sqrt(907)<30.6183:
  if not(W/'WIDE_GREEN').exists():(W/'WIDE_GREEN').write_text(C.now());C.state('CONTROL WIDE GREEN stopped907 side '+str((wide_control['new']+1)*math.sqrt(907))+'; certified-input fq and native/pandas clearance passed. Two fresh production starts permitted.')
 C.atomic(W/'last-handoff-read.json',dict(time=C.now(),lines=len((S/'handoff-r35.log').read_text().splitlines())))
 if time.time()>=C.ADMIT:return
 if not(W/'CONTROL_GREEN').exists()or not(W/'ALL_FINISH_GREEN').exists():return
 lines=(S/'handoff-r35.log').read_text().splitlines();locks={p.name for p in(W/'boxE-raw/locks').glob('*')}
 pending=[j for j in jobs if not done.get(j['id'])and j['id']not in locks];room=max(0,6-len(pending));new=[]
 tried=set(C.load(W/'tried-inputs.json',[]));shapes=set(C.load(W/'tried-shapes.json',[]));historical=set(C.load(W/'historical-fingerprints.json',[]))|set(C.load(W/'held-shapes35.json',[]));deferred=C.load(W/'deferred32.json',{})
 
 followed=set(C.load(W/'followed.json',[]));candidates=[]
 for j in jobs:
  d=done.get(j['id'],{});n=j['n']
  if j['kind']in('control','early')or j['id']in followed or not d.get('quench_from_certified')or 'error'in d:continue
  movement=j['side']-(d['new']+1)*math.sqrt(n)
  if movement>1e-6 and d['new']<=peer[n]+1e-6/math.sqrt(n) and C.BASE[n]-d['new']>1e-10:  # r35 lesson 6h: no legs within 1e-10 of the bar
   candidates.append((-7,-movement,W/'boxE-raw'/j['id']/'final'/f'{n}.csv',n,'leg',j['seed']+97,dict(parent_job=j),j['id']))
 cache=C.load(W/'shape-cache32.json',{})
 retried=set(C.load(W/'held-sidecar-retried.json',[]))
 for dg,v in list(deferred.items()):
  if dg not in retried and 'exceeded 120 wall seconds' in str(v.get('reason','')) and (W/'walk-cap').exists():
   del deferred[dg];retried.add(dg);C.state('SOURCE RETRY walk cap raised '+str(v.get('path')));continue
  if dg not in retried and 'missing exact source record' in str(v.get('reason','')) and C.held_sidecar(v.get('path','')):
   del deferred[dg];retried.add(dg);C.state('SOURCE RETRY held-file sidecar '+str(v.get('path')))
 C.atomic(W/'held-sidecar-retried.json',sorted(retried))
 for lane,rnd in [(lane,rnd)for rnd in (35,34)for lane in GEOMETRY_LANES]:
  root=S/f'take-{lane}-r{rnd}'
  for p in list((root/'near').glob('*.csv'))+list(root.glob('*.csv')):
   st=p.stat()
   # Backlog gets the first ten minutes on published takes.
   if (p.parent==root or lane in('classfill','soft'))and time.time()-st.st_mtime<600:continue
   prior=cache.get(str(p))
   if prior and prior['stamp']==[st.st_mtime_ns,st.st_size]:v=prior
   else:
    try:n,side,shape=identity(p);v=dict(stamp=[st.st_mtime_ns,st.st_size],n=n,side=side,shape=shape,sha256=C.sha(p));cache[str(p)]=v
    except Exception:continue
   n=v['n'];digest=v['sha256']
   if n<50:continue
   if p.parent==root and v['side']>(peer[n]+1)*math.sqrt(n)+1e-8:continue
   if lane=='classfill':
    meta=C.load(p.with_suffix('.json'),{})
    if str(meta.get('source','')).startswith('held n ='):continue
   if digest in tried or v['shape']in shapes or v['shape']in historical:continue
   try:
    if 'lattice'not in v:v['lattice']=lattice(p)
    if v['lattice']:continue
   except (OSError,ValueError):continue
   if rnd<35 and digest in deferred:continue
   if digest in deferred:
    sig=source_signature(p);old=deferred[digest]
    if 'source_signature'not in old or any(len(v)!=2 for v in old['source_signature']):old['source_signature']=sig
    if sig==old['source_signature']:continue
    del deferred[digest];C.state('SOURCE RETRY changed sidecar '+str(p))
   if C.claimed(digest,lines):continue
   if C.producer_certified(p,n):continue  # r35 lesson 6e
   delta=v['side']-(peer[n]+1)*math.sqrt(n)
   if delta>(.012 if rnd==35 else .006)or delta<-.02:continue
   candidates.append((-3 if rnd==35 else -2,delta,p,n,'fresh',3531,None,None))
 C.atomic(W/'shape-cache32.json',cache);C.atomic(W/'deferred32.json',deferred);candidates.sort(key=lambda v:(v[0],v[1]));end=time.time()+85
 for rank,order,p,n,kind,seed,proof,parent in candidates:
  if len(new)>=room or time.time()>end:break
  digest=C.sha(p)
  if C.claimed(digest,lines)or digest in tried:continue
  if any(j['n']==n and not done.get(j['id'])for j in jobs+new):continue
  wide=False and kind=='fresh'and (W/'WIDE_GREEN').exists()and sum(v['kind']=='wide'for v in jobs+new)<2 and any('/take-'+lane+'-r35/'in str(p)for lane in('forensics','k123'))
  if wide:kind='wide';seed=3299
  try:j,why=C.produce_input(p,n,kind,seed,peer,proof)
  except Exception as e:why=repr(e);j=None
  if j is None:
   deferred[digest]=dict(path=str(p),reason=why,source_signature=source_signature(p));C.atomic(W/'deferred32.json',deferred);C.state('DEFER '+str(p)+' '+str(why)[:700]);continue
  j.update(priority=rank,order=order)
  if wide:j['options']=['--rmax','8','--tfac','0.15']
  if parent:j['parent_job']=parent;followed.add(parent)
  new.append(j)
  break # Dispatch each admitted geometry before auditing the next source tree.
 for j in new:
  digest=j['input_sha256'];p=W/j['start']
  if C.claimed(digest,(S/'handoff-r35.log').read_text().splitlines()):continue
  C.hand(f'CLAIM {j["kind"]} n={j["n"]} sha256={digest}; 900s probe120 seed={j["seed"]}; options={j.get('options',[])}; pinned {p}; job={j["id"]}')
  C.state('QUEUE boxE '+j['id']+' from '+j['origin']+'; source '+j['ancestry']+'; log work/boxE-raw/'+j['id']+'/run.log; deadline16:05Z')
  tried.add(digest);shapes.add(identity(p,j['n'])[2]);jobs.append(j);C.atomic(W/'jobs.json',jobs)
 C.atomic(W/'tried-inputs.json',sorted(tried));C.atomic(W/'tried-shapes.json',sorted(shapes));C.atomic(W/'followed.json',sorted(followed))
 pending=[j for j in jobs if not done.get(j['id'])and j['id']not in locks]
 pending=[j for j in pending if j['kind']=='control'or not C.claimed(j['input_sha256'],lines)]
 for j in pending:
  if j['kind']!='control':j['bar']=(peer[j['n']]+1)*math.sqrt(j['n'])
 pending.sort(key=C.dispatch_key);C.atomic(W/'queue.json',pending)
 # Per-host queues: each pending job is bound to one host, at most one buffered job per slot of that host.
 assigned={h:[j for j in pending if j.get('host')==h]for h in C.HOSTS}
 for j in pending:
  if j.get('host')in C.HOSTSLOTS or j['kind']=='control':continue
  h=min(C.HOSTS,key=lambda h:len(assigned[h])/C.HOSTSLOTS[h])
  if len(assigned[h])>=C.HOSTSLOTS[h]:break
  j['host']=h;assigned[h].append(j)
 C.atomic(W/'jobs.json',jobs)
 for h in C.HOSTS:
  q=W/f'queue-{h}.json';C.atomic(q,assigned[h])
  try:C.cmd(['rsync','-a',str(W/'starts'),C.remote_of(h)]);C.cmd(['rsync','-a',str(q),C.remote_of(h)+'queue.json'])
  except Exception:traceback.print_exc()
 print(C.now(),'jobs',len(jobs),'done',sum(bool(v)for v in done.values()),'pending',len(pending),'deferred',len(deferred),flush=True)

if __name__=='__main__':
 init_history();last_report=0
 while time.time()<C.HARD and not(W/'STOP').exists():
  try:
   turn()
   if time.time()-last_report>300:
    from finish35 import report
    C.atomic(T/'report.json',report());last_report=time.time()
  except Exception:traceback.print_exc();C.state('CONTROLLER ERROR work/campaign35.log')
  if '--once'in sys.argv:break
  time.sleep(25)
