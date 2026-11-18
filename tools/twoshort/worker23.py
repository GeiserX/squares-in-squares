"""Run one local-kick job at a time, with an atomic claim and a fixed deadline."""
import csv, json, os, pathlib, re, shutil, subprocess, sys, time
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
def runjob(p):
 j=json.load(open(p))
 if j.get('kind')=='requench':
  d=R/'q'/j['tag'];meta=d/'meta.json';md=json.load(open(meta))
  with open(d/'run.log','w') as log:rc=subprocess.call([PY,'-I','lane/zone_corner.py','quench',str(d),str(md['n'])],stdout=log,stderr=subprocess.STDOUT)
  md['quench_rc']=rc;atomic(meta,md);atomic(R/'done'/p.name,dict(j,rc=rc));event('REQUENCH '+j['tag']+' rc='+str(rc));return
 if j.get('kind')=='control':
  event('STAIR CONTROL START')
  rc=subprocess.call([PY,'-I','control22.py']);atomic(R/'done'/p.name,dict(j,rc=rc));event('STAIR CONTROL DONE rc='+str(rc));return
 if j.get('kind')=='design':
  event('DESIGN START '+p.name)
  rc=subprocess.call([PY,'-I','design23.py',str(j['f']),j['tag']])
  atomic(R/'done'/p.name,dict(j,rc=rc));event('DESIGN DONE '+p.name+' rc='+str(rc));return
 n=j['n'];seed=j['seed'];tag=j['tag']; D=R/'runs'/('%s-s%d'%(tag,seed));D.mkdir(exist_ok=True)
 bar=json.load(open('bar.json'))[str(n)]; t0=time.time()
 cmd=[PY,'-I','lane/invent_rest.py',str(n),j['start'],str(D),'--seconds',str(j['seconds']),'--seed',str(seed),'--modes','lkick','--bar',str(bar),'--deadline','deadline']+j.get('extra',[])
 event('START '+p.name+' '+repr(cmd))
 with open(D/'run.log','w') as log:rc=subprocess.call(cmd,stdout=log,stderr=subprocess.STDOUT)
 text=(D/'run.log').read_text();m=re.search(r'n=\d+ start ([\d.]+) best ([\d.]+) tries (\d+)',text)
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
 if (cur!=j['start'] or j.get('force_quench')) and best<bar+0.0007 and time.time()+240<int(open('deadline').read()):
  qdir=R/'q'/('%s-s%d'%(tag,seed));qdir.mkdir(exist_ok=True);qfile=qdir/('%d-best.csv'%n);shutil.copy2(cur,qfile)
  sys.path.insert(0,str(R/'lane'));import floatsafe
  fr=floatsafe.work((n,[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(qfile))]))[1]
  if fr is None:raise RuntimeError('cannot certify quench input')
  with open(qfile,'w',newline='') as f:
   cw=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(fr)
  with open(qdir/'run.log','w') as log:qrc=subprocess.call([PY,'-I','lane/zone_corner.py','quench',str(qdir),str(n)],stdout=log,stderr=subprocess.STDOUT)
  atomic(qdir/'meta.json',dict(j,quench_rc=qrc,quenched_file=str(qfile)))
 if j['remaining']>1 and miss<2 and time.time()+j['seconds']+75<int(open('deadline').read()):
  jj={k:v for k,v in j.items() if k not in ['start_side','best','tries','best_file','bar','seconds_used']}
  jj.update(start=cur,seed=seed+1,remaining=j['remaining']-1,miss=miss,priority=2 if start-best>1e-7 else 8)
  atomic(R/'jobs'/('%03d-%s-%d.json'%(jj['priority'],tag,seed+1)),jj)
while not (R/'STOP23').exists() and time.time()+75<int(open('deadline').read()):
 found=False
 for p in sorted((R/'jobs').glob('*.json')):
  try:(R/'locks'/p.name).mkdir()
  except FileExistsError:continue
  found=True
  try:runjob(p)
  except Exception as ex:event('ERROR '+p.name+' '+repr(ex))
  break
 if not found:time.sleep(5)
event('EXIT')
