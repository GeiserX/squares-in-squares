"""Resume saved full module specifications, using a common wall deadline."""
import os,pathlib,sys,json,subprocess,time,csv,hashlib
csv.field_size_limit(16000000)
sys.path.insert(0,str(pathlib.Path.home()/'scratch/squares-twoshort'));from shape974 import load,distance
R=pathlib.Path.home()/'scratch/squares-twoshort';os.chdir(R);D=R/'designs'/sys.argv[1];PY=str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python');end=int((R/'deadline').read_text());start=time.time()
rows=json.load(open(D/('unstarted.json' if (D/'unstarted.json').exists() else 'specifications.json')));done=[]
bar_now=json.load(open(R/'bar.json'));rows.sort(key=lambda r:float(r.get('predicted_side',float(r.get('held_side',bar_now[r['n']]))+float(r['predicted_minus_held'])))-bar_now[r['n']])
for i,r in enumerate(rows):
 if time.time()+150>end or time.time()-start>360:
  (D/'unstarted.json').write_text(json.dumps(rows[i:],indent=2));break
 n=int(r['n']);name=str(n)+'-'+hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()[:10];md=D/'builds'/(name+'.json');(D/'builds').mkdir(exist_ok=True)
 if not md.exists():
  cmd=[PY,'-I','lane/modules.py','job',str(D/'lib'),str(D/'builds'),'details-bar.csv',name,str(n),r['corner'],r['far1'],r['far2'],r['stacks1'],r['stacks2'],r['f'],'--squeeze','family']
  try:
   with open(D/(name+'.build.log'),'w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=max(.01,min(120,end-time.time()-30,360-(time.time()-start))),check=True)
  except subprocess.TimeoutExpired:done.append(dict(n=n,name=name,timeout=True));continue
  except subprocess.CalledProcessError:done.append(dict(n=n,name=name,error=True));continue
 if not md.exists():continue
 d=json.load(open(md));done.append(dict(n=n,name=name,built=d.get('built')))
 if not D.name.startswith('control') and d.get('built') is not None and d['built']<json.load(open('bar.json'))[str(n)]+.001:
  candidate=md.with_suffix('.csv');a,side=load(candidate);duplicate=None
  refs=json.load(open(R/'reference/index.json')) if (R/'reference/index.json').exists() else []
  for old in refs:
   if old['n']!=n:continue
   ref=R/old['file'];b,bs=load(ref)
   if abs(side-bs)<2e-8 and distance(a,side,b)<2e-8:duplicate=str(ref);break
  if duplicate:
   done[-1]['duplicate']=duplicate;continue
  for jp in (R/'jobs').glob('*.json'):
   jj=json.load(open(jp))
   if jj.get('n')!=n or not jj.get('start') or jj.get('tag','').startswith('control'):continue
   ref=pathlib.Path(jj['start']);ref=ref if ref.is_absolute() else R/ref
   if not ref.exists() or ref==candidate:continue
   b,bs=load(ref)
   if abs(side-bs)<2e-8 and distance(a,side,b)<2e-8:duplicate=str(ref);break
  if duplicate:
   done[-1]['duplicate']=duplicate;continue
  j=dict(tag=D.name+'-'+name,n=n,start=str(md.with_suffix('.csv')),seed=625,remaining=2,seconds=180,miss=0,priority=1,force_quench=True,source='twoshort round25 original module family build from saved r24 specification '+str(md)+'; '+json.dumps(d['modules']),licence='; '.join(sorted({m['licence'] for m in d['modules']})),ancestry_checked=True)
  p=R/'jobs'/('001-'+j['tag']+'-625.json');tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(j,indent=2));tmp.replace(p)
else:(D/'unstarted.json').write_text('[]')
batch=list(D.glob('batch-*.json'));(D/('batch-%03d.json'%len(batch))).write_text(json.dumps(dict(results=done,seconds=time.time()-start),indent=2))
if (D/'unstarted.json').exists() and json.load(open(D/'unstarted.json')) and time.time()+200<end:
 j=dict(kind='specs',tag=D.name,priority=50);p=R/'jobs'/('050-'+D.name+'-b%03d.json'%len(batch));p.write_text(json.dumps(j))
(D/'summary.json').write_text(json.dumps(dict(attempted=len(done),seconds=time.time()-start,results=done),indent=2))
