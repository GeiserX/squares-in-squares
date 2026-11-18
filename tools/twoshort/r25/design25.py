"""Build fresh staircase corners at one side fraction, then screen and kick their layouts."""
import csv, hashlib,json,os,pathlib,pickle,shutil,subprocess,sys,time
csv.field_size_limit(16000000)
R=pathlib.Path.home()/'scratch/squares-twoshort';os.chdir(R);PY=str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python')
sys.path.insert(0,str(R/'lane'));sys.path.insert(0,str(R));import zone_corner as Z
from shape974 import load as shape_load,distance as shape_distance,guard as shape_guard
f=float(sys.argv[1]);tag=sys.argv[2];D=R/'designs'/tag;D.mkdir(parents=True,exist_ok=True);end=int(open('deadline').read())
def call(args,log):
 if time.time()+80>end:raise RuntimeError('deadline')
 with open(D/log,'w') as out:
  timeout=min(max(1,end-time.time()-65),600 if str(args[0]).endswith('twoshort_corner.py') else 120 if str(args[0]).endswith('modules.py') and str(args[1])=='job' else 300 if str(args[0]).endswith('modules.py') and str(args[1])=='queue' else 1800)
  if 'batch_start' in globals():timeout=max(.01,min(timeout,360-(time.time()-batch_start)))
  try:subprocess.run([PY,'-I']+list(map(str,args)),stdout=out,stderr=subprocess.STDOUT,check=True,timeout=timeout)
  except subprocess.TimeoutExpired:
   if str(args[0]).endswith('modules.py') and str(args[1])=='job':
    with open(D/'timeouts.log','a') as f:f.write(str(args)+'\n')
    return False
   if str(args[0]).endswith('twoshort_corner.py') and (D/'base.pkl').exists():print('stair timed out, using saved base',flush=True)
   else:raise
def atom(p,d):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2));t.replace(p)
if tag.startswith('library-'):
 if tag.startswith('library-zones-') and not (D/'lib/library.pkl').exists():
  call(['lane/zone_corner.py','merge','lib-z4',D/'zones',D/'lib','--max-loss',6],'merge.log')
else:
 p=D/'base.pkl'
 if tag.startswith('joint') and not p.exists():
  call(['joint23.py',f,tag],'joint.log')
 elif tag.endswith('-hot'):
  shutil.copy2(R/'designs'/tag[:-4]/'base.pkl',p)
 elif tag.endswith('-96'):
  shutil.copy2(R/'designs'/tag[:-3]/'base.pkl',p)
 elif not p.exists():
  call(['lane/twoshort_corner.py','stair',9,9,f,p,'--top',0,'--per',4,'--walls','--keep',40,'--seconds',480,'--tag',tag],'stair.log')
 base=pickle.load(open(p,'rb')); selected=[]
 if tag.endswith('-96'):
  cand=[b for b in base if b['count']==96]
  if not cand:raise RuntimeError('96-square corner not retained')
  b=min(cand,key=lambda q:Z.loss_of(Z.cmod(9,9),f,q['count'],q['y0'],q['x0']))
  cheapest=min((q for q in base if q['count']%9==6),key=lambda q:Z.loss_of(Z.cmod(9,9),f,q['count'],q['y0'],q['x0']))
  if b['id']==cheapest['id'] and tag[:-3]!='s673':
   atom(D/'summary.json',dict(f=f,tag=tag,skipped='same 96-square start already tested in primary pipeline'));sys.exit(0)
  base=[b];pickle.dump(base,open(p,'wb'))
 for cl in ([] if tag.startswith(('import-','joint')) else [6] if tag.endswith('-96') else [6,4,1,3]):
  b=min((q for q in base if q['count']%9==cl),key=lambda q:Z.loss_of(Z.cmod(9,9),f,q['count'],q['y0'],q['x0']),default=None)
  if b:selected.append(b)
 # Make the un-hopped staircase library, and each new hop state, available without waiting for the whole pipeline.
 if not list((D/'runs').glob('corner-*.pkl')):
  call(['lane/zone_corner.py','adopt',p,D/'runs'],'adopt.log')
 for b in selected:
  call(['cornerhot22.py' if tag.endswith('-hot') else 'lane/zone_corner.py','search',p,D/'runs','--id',b['id'],'--moves','self,hop','--seed',22,'--minutes',4,'--deadline','deadline'],b['id']+'.hop.log')
 # Compare small local kicks with the standard hops on the same class-6 staircase start.
 for b in selected:
  if b['count']%9==6 and not tag.endswith('-hot'):
   wr=D/'runs-weak';wr.mkdir(exist_ok=True)
   for pp in (D/'runs').glob('corner-'+b['id']+'-*-s22.pkl'):shutil.copy2(pp,wr/pp.name)
   call(['cornerlk22.py',p,wr,'--id',b['id'],'--moves','self,resume,hop','--seed',22,'--minutes',4,'--deadline','deadline'],b['id']+'.weak.log')
   weakdir=D/'runs'/'weak';weakdir.mkdir(exist_ok=True)
   for pp in (D/'runs-weak').glob('corner-*.pkl'):shutil.copy2(pp,weakdir/pp.name)
 call(['lane/zone_corner.py','table',D/'runs',D/'zones',D/'zones.tsv','--all','--tag',tag],'table.log')
 expected={pickle.load(open(pp,'rb'))['count'] for pp in (D/'runs').glob('corner-*.pkl')}
 actual={q['count'] for q in pickle.load(open(D/'zones/corners.pkl','rb'))}
 atom(D/'count-control.json',dict(expected=sorted(expected),actual=sorted(actual),missing=sorted(expected-actual)))
 assert expected<=actual,('table lost standard-hop counts',expected-actual)
 call(['lane/zone_corner.py','merge','lib-z4',D/'zones',D/'lib','--max-loss',6],'merge.log')
lib=pickle.load(open(D/'lib/library.pkl','rb'))
changed=False
for q in lib['mods']:
 if q['tag']=='z' and q['licence']=='our own' and not q.get('ours'):q['ours']=True;changed=True
if changed:
 tmp=D/'lib'/('library.pkl.tmp.'+str(os.getpid()));pickle.dump(lib,open(tmp,'wb'));tmp.replace(D/'lib/library.pkl')
if not tag.startswith('library-'):
 zs=pickle.load(open(D/'zones/corners.pkl','rb'));have={q['id'] for q in lib['mods']}
 (D/'need.txt').write_text('\n'.join(q['id'] for q in zs if q['id'] in have)+'\n')
# Geometry deduplication runs in the collector.
skipped_kicks=[]
from family_targets25 import targets
(D/'ns.txt').write_text(' '.join(map(str,targets(lib['mods'],set((D/'need.txt').read_text().split()),json.load(open('bar.json'))))))
call(['lane/modules.py','queue',D/'lib','details-bar.csv',D/'queue.tsv','--top',4,'--slack',.012 if tag.startswith(('import-','library-')) else .006,'--need',D/'need.txt','--depth',.08,'--ns',D/'ns.txt'],'queue.log')
rows=sorted(csv.DictReader(open(D/'queue.tsv'),delimiter='\t'),key=lambda r:float(r['predicted_minus_held']))
seen=set();built=0;batch_start=time.time();attempted=[]
for ri,r in enumerate(rows):
 if time.time()-batch_start>360:
  atom(D/'unstarted.json',rows[ri:]);break
 n=int(r['n']);key=tuple(r[k] for k in ('n','corner','far1','far2','stacks1','stacks2'))
 if key in seen:continue
 seen.add(key);attempted.append(key); name=str(n)+'-'+hashlib.md5(str(r).encode()).hexdigest()[:8]
 md=D/'builds'/(name+'.json')
 prior=D/(name+'.build.log')
 if not md.exists():
  if prior.exists() and 'no start' in prior.read_text():continue
  call(['lane/modules.py','job',D/'lib',D/'builds','details-bar.csv',name,n,r['corner'],r['far1'],r['far2'],r['stacks1'],r['stacks2'],r['f'],'--squeeze','family'],name+'.build.log')
 if not md.exists():continue
 d=json.load(open(md));built+=1;bar=json.load(open('bar.json'))[str(n)]
 if d.get('built') is not None and d['built']<bar+.001:
  candidate=D/'builds'/(name+'.csv');arr,side=shape_load(candidate);duplicate=None
  for jp in (R/'jobs').glob('*.json'):
   jj=json.load(open(jp))
   if jj.get('n')!=n or 'start' not in jj or jj.get('tag','').startswith('control'):continue
   ref=pathlib.Path(jj['start']);ref=ref if ref.is_absolute() else R/ref
   if not ref.exists() or ref==candidate:continue
   rr,ss=shape_load(ref)
   if len(rr)==len(arr) and abs(side-ss)<2e-8 and shape_distance(arr,side,rr)<2e-8:duplicate=str(ref);break
  if duplicate and side>=bar-1e-10*(n**.5):
   skipped_kicks.append(dict(n=n,build=name,duplicate=duplicate))
   if built>=18:
    atom(D/'unstarted.json',rows[ri+1:]);break
   continue
  j=dict(tag=tag+'-'+name,n=n,start=str(D/'builds'/(name+'.csv')),seed=625,remaining=2,seconds=180,miss=0,priority=0,force_quench=True,source='twoshort round25 corner pipeline '+tag+' family build '+name+'; '+json.dumps(d['modules']),licence='; '.join(sorted({x['licence'] for x in d['modules']})))
  atom(R/'jobs'/('000-'+j['tag']+'-625.json'),j)
 if built>=18:
  atom(D/'unstarted.json',rows[ri+1:]);break
atom(D/'summary.json',dict(f=f,tag=tag,settled=0 if tag.startswith('library-') else len(base),selected=[] if tag.startswith('library-') else [b['id'] for b in selected],queue_rows=len(rows),built=built,attempted=len(attempted),build_batch_seconds=time.time()-batch_start,skipped_kicks=skipped_kicks))
