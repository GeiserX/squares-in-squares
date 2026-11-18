"""Round 32 boxE worker (copied from worker31; jobs are 150 s invent_rest lkicks; STOP32 stops it): one midm_scan lkick,kick job at a time with a probe. At PROBE seconds the run is stopped
unless a find took the side more than PMIN below the start. A find is quenched once with fq from its floatsafe-certified
copy (zone_corner.py quench) when its raw score is near the bar. A leg (new seed from the find) is queued while a run
moves the side more than 1e-6; a run that gained 1e-5 of score or more gets two more seeds."""
import csv, json, os, pathlib, re, shutil, subprocess, sys, time, signal, math
R=pathlib.Path.home()/'scratch/squares-twoshort';os.chdir(R)
PY=str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python')
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',MKL_NUM_THREADS='1',SQ_FQ=str(pathlib.Path.home()/'scratch/squares-base/fq'),SQ_TMP=str(R/'tmp'),SQ_BOX=str(R),ZC_FQ_TIMEOUT='180')
fqslot=R/'ext/evand/search/packer/target/release/fq'
fqslot.parent.mkdir(parents=True,exist_ok=True)
try:
 if not fqslot.exists() and not fqslot.is_symlink():fqslot.symlink_to(pathlib.Path.home()/'scratch/squares-base/fq')
except FileExistsError:pass
W=sys.argv[1]
def atomic(p,d):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(d,indent=1));q.replace(p)
def event(s):
 with open('worker.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' '+W+' '+s+'\n')
def dl():return int((R/'deadline').read_text())
def sdl():return int((R/'search-deadline').read_text())
def killpg(proc):
 try:os.killpg(proc.pid,signal.SIGTERM)
 except ProcessLookupError:return
 try:proc.wait(timeout=3)
 except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
def scanstate(sc):
 st=sc.read_text() if sc.exists() else ''
 h=re.search(r'held=([\d.]+)',st);finds=re.findall(r'# FIND try \d+ mode (\w+) .*? side ([\d.]+)',st)
 tries=len([l for l in st.splitlines() if l and not l.startswith('#')])
 return (float(h[1]) if h else None),finds,tries
def runjob(p):
 j=json.load(open(p));n=j['n'];seed=j['seed'];tag=j['tag'];D=R/'runs'/('%s-s%d'%(tag,seed));D.mkdir(parents=True,exist_ok=True)
 if j.get('kind')=='quench':
  qd=R/'q'/('%s-s%d'%(tag,seed));qd.mkdir(parents=True,exist_ok=True);qf=qd/('%d-best.csv'%n);shutil.copy2(j['start'],qf);t0=time.time()
  with open(qd/'run.log','w') as lg:
   qp=subprocess.Popen([PY,'-I','lane/zone_corner.py','quench',str(qd),str(n)],start_new_session=True,stdout=lg,stderr=subprocess.STDOUT)
   try:qrc=qp.wait(timeout=max(5,min(900,dl()-time.time()-30)))
   except subprocess.TimeoutExpired:killpg(qp);qrc=125
  j['quench']=dict(rc=qrc,file=str(qf),log=(qd/'run.log').read_text()[-400:],seconds=round(time.time()-t0))
  atomic(R/'done'/p.name,j);event('QUENCH %s rc %s %s'%(tag,qrc,(qd/'run.log').read_text().strip().splitlines()[-1:]));return
 t0=time.time();sc=D/('scan-%d-%d.tsv'%(n,seed))
 if j.get('tool')=='lkick':return runlk(p,j,D)
 cmd=[PY,'-I','lane/midm_scan.py','--n',str(n),'--sub',j['start'],'--out',str(D),'--fq',os.environ['SQ_FQ'],'--seconds',str(j['seconds']),'--modes','lkick,kick','--deadline','search-deadline','--seed',str(seed)]
 if j.get('kicks'):cmd+=['--kicks',j['kicks']]
 event('START '+p.name+' '+' '.join(cmd[2:]))
 log=open(D/'run.log','w');proc=subprocess.Popen(cmd,start_new_session=True,stdout=log,stderr=subprocess.STDOUT)
 probed=False;why='end'
 while proc.poll() is None:
  time.sleep(5);el=time.time()-t0
  if time.time()>=min(sdl(),dl()) or (R/'STOP32').exists():killpg(proc);why='deadline';break
  if el>j['seconds']+300:killpg(proc);why='wall';break
  if not probed and el>=j.get('probe',0)>0:
   h,finds,tries=scanstate(sc)
   # round 31 19:08: the probe needs 12 tries or 300 s (936 made 4 tries in 120 s); round 32 runs no midm jobs
   if tries>=j.get('probe_tries',12) or el>=j.get('probe_max',300):
    probed=True
    if h is not None and not [f for f in finds if float(f[1])<h-j.get('pmin',1e-8)]:killpg(proc);why='probe-dry';break
 log.close();h,finds,tries=scanstate(sc)
 if h is None:j.update(error=(D/'run.log').read_text()[-1500:]);atomic(R/'done'/p.name,j);event('FAIL '+p.name);return
 raws=sorted((D/'raw').glob('%d-*.csv'%n),key=lambda q:int(q.stem.rsplit('-',1)[1])) if (D/'raw').exists() else []
 best=min([float(f[1]) for f in finds]+[h]);cur=str(raws[-1]) if finds and raws else None
 j.update(start_side=h,best=best,tries=tries,best_file=cur,why=why,seconds_used=round(time.time()-t0))
 event('DONE %s n=%d start %.12f best %.12f moved %.3e tries %d %s'%(p.name,n,h,best,h-best,tries,why))
 finish(p,j,h,best,cur,seed,tag,n)
def finish(p,j,h,best,cur,seed,tag,n):
 bar=j['bar'];sq=math.sqrt(n)
 if cur and ((h-best>1e-8 and best/sq-1<bar+3e-9) or best/sq-1<bar-1e-10) and time.time()+400<dl():
  qd=R/'q'/('%s-s%d'%(tag,seed));qd.mkdir(parents=True,exist_ok=True);qf=qd/('%d-best.csv'%n);shutil.copy2(cur,qf)
  with open(qd/'run.log','w') as lg:
   qp=subprocess.Popen([PY,'-I','lane/zone_corner.py','quench',str(qd),str(n)],start_new_session=True,stdout=lg,stderr=subprocess.STDOUT)
   try:qrc=qp.wait(timeout=max(5,min(900,dl()-time.time()-30)))
   except subprocess.TimeoutExpired:killpg(qp);qrc=125
  j['quench']=dict(rc=qrc,file=str(qf),log=(qd/'run.log').read_text()[-400:])
  event('QUENCH %s rc %s %s'%(tag,qrc,(qd/'run.log').read_text().strip().splitlines()[-1:] ))
  # round 32 11:50: a leg starts from the quenched file when the quench ran clean and went lower (992 leg 1 started
  # from the raw best, 7.6e-7 of side above its own quench, and ended above it)
  mq=re.findall(r'QUENCH ([\d.]+) -> ([\d.]+)',(qd/'run.log').read_text())
  if qrc==0 and mq and float(mq[-1][1])<best-1e-12 and qf.exists():cur=str(qf);event('LEGSTART %s quenched file %s side %s'%(tag,qf,mq[-1][1]))
 atomic(R/'done'/p.name,j)
 # legs
 gain_score=(j['root_side']-best)/sq
 if cur and h-best>(1e-8 if j.get('tool')=='lkick' else 1e-6) and j.get('legs',0)<8 and time.time()+j['leg_seconds']+120<sdl():
  extra=2 if gain_score>=1e-5 and not j.get('seeded') else 0
  for k in range(1+extra):
   jj=dict(j);[jj.pop(x,None) for x in ('start_side','best','tries','best_file','why','seconds_used','quench','error')]
   jj.update(chain=j.get('chain',[j['start']])+[cur],start=cur,seed=seed+1+k*97,legs=j.get('legs',0)+1,seconds=j['leg_seconds'],probe=j.get('leg_probe',120),priority=5,seeded=j.get('seeded') or extra>0)
   atomic(R/'jobs'/('005-%s-%d.json'%(tag,jj['seed'])),jj);event('LEG queued %s seed %d from %s'%(tag,jj['seed'],cur))
def runlk(p,j,D):
 n=j['n'];seed=j['seed'];tag=j['tag'];t0=time.time();sq=math.sqrt(n)
 cmd=[PY,'-I','lane/invent_rest.py',str(n),j['start'],str(D),'--seconds',str(j['seconds']),'--seed',str(seed),'--modes','lkick','--bar',repr((j['bar']+1)*sq),'--deadline','search-deadline']
 # round 32 14:40: a job may carry its own kick steps (wide steps --sigs 0.01,0.02,0.04 for second seeds; round 28 A/B)
 if j.get('sigs'):cmd+=['--sigs',j['sigs']]
 event('START '+p.name+' '+' '.join(cmd[2:]))
 with open(D/'run.log','w') as log:
  proc=subprocess.Popen(cmd,start_new_session=True,stdout=log,stderr=subprocess.STDOUT)
  try:proc.wait(timeout=max(5,min(j['seconds']+300,sdl()-time.time())))
  except subprocess.TimeoutExpired:killpg(proc)
 sl=D/('slide-%d-%d.tsv'%(n,seed));h=None;best=None;cur=None;tries=0
 if sl.exists():
  for line in sl.read_text().splitlines():
   m=re.search(r'start=([\d.]+)',line)
   if m and h is None:h=float(m[1]);best=h
   q=line.split('\t')
   if len(q)==7:
    tries+=1
    if q[-1]=='BEST' and (D/'raw'/('%d-sl%d-%s.csv'%(n,seed,q[0]))).exists() and float(q[3])<best:best=float(q[3]);cur=str(D/'raw'/('%d-sl%d-%s.csv'%(n,seed,q[0])))
 if h is None:j.update(error=(D/'run.log').read_text()[-1500:]);atomic(R/'done'/p.name,j);event('FAIL '+p.name);return
 j.update(start_side=h,best=best,tries=tries,best_file=cur,why='lkick',seconds_used=round(time.time()-t0))
 event('DONE %s n=%d start %.12f best %.12f moved %.3e tries %d lkick'%(p.name,n,h,best,h-best,tries))
 finish(p,j,h,best,cur,seed,tag,n)
_ME=os.stat(__file__).st_mtime
while not (R/'STOP32').exists() and time.time()+60<min(dl(),sdl()):
 if os.stat(__file__).st_mtime!=_ME:event('RELOAD');os.execv(sys.executable,[sys.executable,'-I',os.path.abspath(__file__),W])
 found=False
 def _lk(q):
  try:return json.load(open(q)).get('tool')=='lkick'
  except (ValueError,OSError):return False
 # round 32: controls (000) and legs (005) first, then by queue name
 for p in sorted((q for q in (R/'jobs').glob('*.json') if not (R/'locks'/q.name).exists()),key=lambda q:q.name):
  try:(R/'locks'/p.name).mkdir()
  except FileExistsError:continue
  found=True
  try:runjob(p)
  except Exception as ex:event('ERROR '+p.name+' '+repr(ex))
  break
 if not found:time.sleep(5)
event('EXIT')
