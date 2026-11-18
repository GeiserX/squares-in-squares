"""Run one local-kick job at a time, with an atomic claim and a fixed deadline."""
import csv, json, os, pathlib, re, shutil, subprocess, sys, time, signal
csv.field_size_limit(16000000)
R=pathlib.Path.home()/'scratch/squares-twoshort';os.chdir(R)
PY=str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python')
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',MKL_NUM_THREADS='1',SQ_FQ=str(pathlib.Path.home()/'scratch/squares-base/fq'),SQ_TMP=str(R/'tmp'),SQ_BOX=str(R),ZC_FQ_TIMEOUT='180')
fqslot=R/'ext/evand/search/packer/target/release/fq'
fqslot.parent.mkdir(parents=True,exist_ok=True)
if not fqslot.exists() and not fqslot.is_symlink():fqslot.symlink_to(pathlib.Path.home()/'scratch/squares-base/fq')
def atomic(p,d):
 q=p.with_suffix('.tmp');q.write_text(json.dumps(d,indent=2));q.replace(p)
def event(s):
 with open('worker.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' '+sys.argv[1]+' '+s+'\n')
def bounded(cmd,limit=None,**kw):
 end=int((R/'deadline').read_text())
 if limit:end=min(end,time.time()+limit)
 if time.time()>=end:return 125
 proc=subprocess.Popen(cmd,start_new_session=True,**kw)
 try:return proc.wait(timeout=max(1,end-time.time()))
 except subprocess.TimeoutExpired:
  os.killpg(proc.pid,signal.SIGTERM)
  try:proc.wait(timeout=2)
  except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
  return 125
def lp_polish(n,qfile,qdir,j):
 if time.time()+480>=int(open('deadline').read()):return
 sys.path.insert(0,str(R/'lane'));import floatsafe
 try:
  with open(qdir/'lp.log','w') as log:lrc=bounded([PY,'-I','lane/methods_lp.py',str(qfile),str(qdir/'lp'),'--ns',str(n),'--jobs','1'],limit=420,stdout=log,stderr=subprocess.STDOUT)
  lpf=qdir/'lp'/'raw'/('%d.csv'%n)
  if not lpf.exists():j['lp_polish']=dict(rc=lrc,moved=False);return
  rd=lambda q:[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(q))]
  a0=floatsafe.work((n,rd(qfile)));a1=floatsafe.work((n,rd(lpf)))
  j['lp_polish']=dict(rc=lrc,before=a0[2],after=a1[2],kept=False)
  if a1[1] is not None and (a0[1] is None or a1[2]<a0[2]-1e-13):
   with open(qfile,'w',newline='') as f:
    cw=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(a1[1])
   j['lp_polish']['kept']=True
  event('LP '+str(n)+' '+json.dumps(j['lp_polish']))
 except Exception as ex:event('LP ERROR '+str(n)+' '+repr(ex))
def runjob(p):
 j=json.load(open(p))
 if j.get('kind')=='requench':
  d=R/'q'/j['tag'];meta=d/'meta.json';md=json.load(open(meta))
  with open(d/'run.log','w') as log:rc=bounded([PY,'-I','lane/zone_corner.py','quench',str(d),str(md['n'])],stdout=log,stderr=subprocess.STDOUT)
  md['quench_rc']=rc;atomic(meta,md);atomic(R/'done'/p.name,dict(j,rc=rc));event('REQUENCH '+j['tag']+' rc='+str(rc));return
 if j.get('kind')=='control':
  event('STAIR CONTROL START')
  rc=bounded([PY,'-I','control22.py']);atomic(R/'done'/p.name,dict(j,rc=rc));event('STAIR CONTROL DONE rc='+str(rc));return
 if j.get('kind')=='specs':
  event('SPECS START '+p.name)
  rc=bounded([PY,'-I','specs30.py',j['tag']])
  atomic(R/'done'/p.name,dict(j,rc=rc));event('SPECS DONE '+p.name+' rc='+str(rc));return
 if j.get('kind')=='design':
  event('DESIGN START '+p.name)
  rc=bounded([PY,'-I','design30.py',str(j['f']),j['tag']])
  atomic(R/'done'/p.name,dict(j,rc=rc));event('DESIGN DONE '+p.name+' rc='+str(rc));return
 n=j['n'];seed=j['seed'];tag=j['tag']; D=R/'runs'/('%s-s%d'%(tag,seed));D.mkdir(exist_ok=True)
 bar=json.load(open('bar.json'))[str(n)]; t0=time.time()
 if j.get('tool')=='midm':
  cmd=[PY,'-I','lane/midm_scan.py','--n',str(n),'--sub',j['start'],'--out',str(D),'--fq',os.environ['SQ_FQ'],'--seconds',str(j['seconds']),'--modes','lkick,kick','--deadline','deadline','--seed',str(seed)]
  event('START '+p.name+' '+repr(cmd))
  with open(D/'run.log','w') as log:rc=bounded(cmd,limit=j['seconds']+600,stdout=log,stderr=subprocess.STDOUT)
  sc=D/('scan-%d-%d.tsv'%(n,seed));st=sc.read_text() if sc.exists() else '';h=re.search(r'held=([\d.]+)',st)
  if not h:
   j.update(error=(D/'run.log').read_text()[-1500:],rc=rc);atomic(R/'done'/p.name,j);event('FAIL '+p.name);return
  start=float(h[1]);finds=re.findall(r'# FIND try \d+ mode (\w+) .*? side ([\d.]+)',st)
  tries=len([l for l in st.splitlines() if l and not l.startswith('#')])
  raws=list((D/'raw').glob('%d-*.csv'%n)) if (D/'raw').exists() else []
  best=min([float(f[1]) for f in finds]+[start]);cur=str(max(raws,key=lambda q:int(q.stem.rsplit('-',1)[1]))) if finds and raws else j['start']
  extra=''
  if finds and best<start-1e-9 and time.time()+480<int(open('deadline').read()):
   D2=D/'lk';D2.mkdir(exist_ok=True)
   cmd2=[PY,'-I','lane/invent_rest.py',str(n),cur,str(D2),'--seconds','180','--seed',str(seed),'--modes','lkick','--bar',str(bar),'--deadline','deadline']
   with open(D2/'run.log','w') as log:rc2=bounded(cmd2,limit=780,stdout=log,stderr=subprocess.STDOUT)
   sl=D2/('slide-%d-%d.tsv'%(n,seed));lk_best=best;lk_cur=None;lk_tries=0
   if sl.exists():
    for line in sl.read_text().splitlines():
     q=line.split('\t')
     if len(q)==7:lk_tries+=1
     if len(q)==7 and q[-1]=='BEST' and float(q[3])<lk_best and (D2/'raw'/('%d-sl%d-%s.csv'%(n,seed,q[0]))).exists():lk_best=float(q[3]);lk_cur=str(D2/'raw'/('%d-sl%d-%s.csv'%(n,seed,q[0])))
   event('LKICK AFTER MIDM %d %.12f -> %.12f tries %d rc %s'%(n,best,lk_best,lk_tries,rc2))
   j['lkick_after']=dict(before=best,after=lk_best,tries=lk_tries,rc=rc2)
   if lk_cur:best=lk_best;cur=lk_cur;extra=' + lkick 180 s'
  m=['n=%d start %.12f best %.12f tries %d (midm lkick,kick%s)'%(n,start,best,tries,extra)]
  if tag.startswith('control793'):j['control_pass']=abs(start-28.672864930769137)<2e-10 and best<=start and tries>0;event('CONTROL '+str(j['control_pass'])+' '+m[0])
 else:
  cmd=[PY,'-I','lane/invent_rest.py',str(n),j['start'],str(D),'--seconds',str(j['seconds']),'--seed',str(seed),'--modes','lkick','--bar',str(bar),'--deadline','deadline']+j.get('extra',[])
  event('START '+p.name+' '+repr(cmd))
  with open(D/'run.log','w') as log:rc=bounded(cmd,limit=j['seconds']+600,stdout=log,stderr=subprocess.STDOUT)
  text=(D/'run.log').read_text();m=re.search(r'n=\d+ start ([\d.]+) best ([\d.]+) tries (\d+)',text)
  if not m and rc==125 and (D/('slide-%d-%d.tsv'%(n,seed))).exists():
   sl=(D/('slide-%d-%d.tsv'%(n,seed))).read_text();h=re.search(r'start=([\d.]+)',sl)
   data=[l.split('\t') for l in sl.splitlines() if l and not l.startswith('#')]
   bs=[float(q[3]) for q in data if len(q)==7 and q[-1]=='BEST']
   if h:m=['n=%d start %s best %.12f tries %d (wall limit)'%(n,h[1],min(bs+[float(h[1])]),len(data)),h[1],repr(min(bs+[float(h[1])])),str(len(data))];event('WALL LIMIT '+p.name)
  if not m:
   j.update(error=text[-1500:],rc=rc);atomic(R/'done'/p.name,j);event('FAIL '+p.name);return
  start,best=float(m[1]),float(m[2]);tries=int(m[3]);cur=j['start']
  for line in (D/('slide-%d-%d.tsv'%(n,seed))).read_text().splitlines():
   parts=line.split('\t')
   if len(parts)==7 and parts[-1]=='BEST':cur=str(D/'raw'/('%d-sl%d-%s.csv'%(n,seed,parts[0])))
 improved=start-best>1e-8;miss=0 if improved else j['miss']+1
 j.update(start_side=start,best=best,tries=tries,best_file=cur,bar=bar,seconds_used=time.time()-t0)
 if tag=='control793':
  j['control_pass']=abs(start-28.672864930769137)<2e-10 and best<start-1e-5 and tries>0
  event('CONTROL '+str(j['control_pass'])+' '+m[0])
 atomic(R/'done'/p.name,j);event('DONE '+p.name+' '+m[0])
 if tag=='control793':return
 # Keep raw finds as chain starts. Quench a separate copy only when near the bar.
 if (cur!=j['start'] or j.get('force_quench')) and best<bar+0.0007 and time.time()+250<int(open('deadline').read()):
  qdir=R/'q'/('%s-s%d'%(tag,seed));qdir.mkdir(exist_ok=True);qfile=qdir/('%d-best.csv'%n);shutil.copy2(cur,qfile)
  sys.path.insert(0,str(R/'lane'));import floatsafe
  fr=floatsafe.work((n,[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(qfile))]))[1]
  if fr is None:raise RuntimeError('cannot certify quench input')
  with open(qfile,'w',newline='') as f:
   cw=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(fr)
  with open(qdir/'run.log','w') as log:qrc=bounded([PY,'-I','lane/zone_corner.py','quench',str(qdir),str(n)],stdout=log,stderr=subprocess.STDOUT)
  if qrc==0:lp_polish(n,qfile,qdir,j)
  atomic(qdir/'meta.json',dict(j,quench_rc=qrc,quenched_file=str(qfile)))
 if j['remaining']>1 and start-best>1e-7 and miss<2 and time.time()+j['seconds']+75<int(open('deadline').read()):
  jj={k:v for k,v in j.items() if k not in ['start_side','best','tries','best_file','bar','seconds_used']}
  jj.update(start=cur,seed=seed+1,remaining=j['remaining']-1,miss=miss,priority=5 if start-best>1e-7 else 80)
  atomic(R/'jobs'/('%03d-%s-%d.json'%(jj['priority'],tag,seed+1)),jj)
_ME=os.stat(__file__).st_mtime
def _midm(p):
 try:return json.load(open(p)).get('tool')=='midm'
 except (ValueError,OSError):return False
def _order(ps):
 return sorted(ps,key=lambda p:(not p.name.startswith('000-00-leg'),(not p.name[:3].isdigit()) or int(p.name[:3])>=50,_midm(p)!=(sys.argv[1]=='1'),p.name))
while not (R/'STOP30b').exists() and time.time()+75<int(open('deadline').read()) and time.time()<int((R/'search-deadline').read_text()):
 found=False
 if os.stat(__file__).st_mtime!=_ME:event('RELOAD');os.execv(sys.executable,[sys.executable,'-I',os.path.abspath(__file__),sys.argv[1]])
 for p in _order([q for q in (R/'jobs').glob('*.json') if not (R/'locks'/q.name).exists()]):
  # Worker one reserves capacity for fresh designs and first passes.
  if sys.argv[1]=='1' and p.name.startswith(('080-',)):continue
  try:(R/'locks'/p.name).mkdir()
  except FileExistsError:continue
  found=True
  try:runjob(p)
  except Exception as ex:event('ERROR '+p.name+' '+repr(ex))
  break
 if not found:time.sleep(5)
event('EXIT')
