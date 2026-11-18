"""Collect this lane, refresh references, and adopt fresh layouts in its slice."""
import csv,hashlib,json,math,os,pathlib,re,shutil,subprocess,sys,time
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
B=pathlib.Path('$SCRATCH/bounties-squares');T=B/'take-twoshort-r23';W=T/'work';R=W/'boxE23';R.mkdir(exist_ok=True)
OLD=B/'take-twoshort-r22/work/boxE22';PY=str(B/'venv/bin/python');remote='boxE:scratch/squares-twoshort/'
sys.path.insert(0,str(W));from shape974 import load,distance
seenfile=W/'seen.json';seen=set(json.load(open(seenfile))) if seenfile.exists() else set()
def atom(p,d):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2));t.replace(p)
def state(s):
 with open(T/'STATE.txt','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA '+s+'\n')
def hand(s):
 with open(B/'handoff-r23.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> all: '+s+'\n')
def rs(src,dst,*opts):subprocess.run(['rsync','-az',*opts,str(src),str(dst)],check=True,timeout=90)
def metadata(p,n,fallback=None,depth=0):
 source=str(p)+'; held source register results/round21-best-2026-11-13.tsv';lic='unresolved: '+str(p)
 for tp in [p.parent/'take.tsv',p.parent.parent/'take.tsv']:
  if tp.exists():
   for r in csv.DictReader(open(tp),delimiter='\t'):
    if r['n']==str(n) and p.parent==tp.parent:
     return source+'; '+str(tp)+'; '+r['source'],r.get('licence',lic)
 for jp in [p.with_suffix('.json'),pathlib.Path(str(p)+'.json')]:
  if jp.exists():
   try:
    md=json.load(open(jp));mods=md.get('modules')
    if md.get('parts'):
     source+='; rectangle composition '+json.dumps(md['parts']);lic='our composition; '+'; '.join(sorted({v['licence'] for v in md['parts'].values() if isinstance(v,dict) and 'licence' in v}))
    if mods:source+='; modules '+json.dumps(mods);lic='; '.join(sorted({m['licence'] for m in mods}))
    elif md.get('source') and md.get('licence'):source+='; '+md['source'];lic=md['licence']
   except (ValueError,KeyError,TypeError):pass
 for parent in [p.parent,p.parent.parent,p.parent.parent.parent]:
  for name in ['sources.tsv','sources-all.tsv','work/sources.tsv','work/sources-all.tsv']:
   sp=parent/name
   if not sp.exists():continue
   for row in csv.DictReader(open(sp),delimiter='\t'):
    donor=row.get('donor','')
    if donor and (p.stem==donor or p.stem.endswith('from'+donor)):
     source+='; '+str(sp)+'; '+row['source'];lic=row['licence']
 if lic.startswith(('unresolved','see ')) and depth<2 and fallback:
  original=re.search(r'$DATA/[^\s,;]+\.csv',fallback.get('source',''))
  if original and pathlib.Path(original[0]).exists() and pathlib.Path(original[0])!=p:
   src2,lic2=metadata(pathlib.Path(original[0]),n,depth=depth+1)
   if not lic2.startswith(('unresolved','see ')):return source+'; '+src2,lic2
 if fallback and not fallback.get('licence','').startswith(('unresolved','see ')):source+='; '+fallback['source'];lic=fallback['licence']
 return source,lic

def once(intake=True):
 rs(remote,R,'--exclude=lane','--exclude=tmp','--exclude=lib','--exclude=lib-z4','--exclude=reference')
 held=list(csv.DictReader(open(B/'gate/cand-round21-1113a/details.csv')));scores={int(r['n']):float(r['score']) for r in held}
 for p in list(B.glob('take-*-r22/take.tsv'))+list(B.glob('take-*-r23/take.tsv')):
  for rr in csv.DictReader(open(p),delimiter='\t'):
   n=int(rr['n']);scores[n]=min(scores[n],float(rr['new']))
 bar={n:(1+s)*math.sqrt(n) for n,s in scores.items()}
 atom(W/'bar.json',{str(n):s for n,s in bar.items()})
 with open(W/'details-bar.csv','w',newline='') as f:
  cw=csv.writer(f);cw.writerow(['n','L','score','min_gap']);cw.writerows([int(r['n']),bar[int(r['n'])],scores[int(r['n'])],r['min_gap']] for r in held)
 rs(W/'bar.json',remote+'bar.json');rs(W/'details-bar.csv',remote+'details-bar.csv')
 if (R/'worker.log').exists():
  for line in (R/'worker.log').read_text().splitlines():
   key='event:'+line
   if key not in seen:state('boxE '+line+'; log work/boxE23; deadline18:30UTC');seen.add(key)
 # Export raw changes while scans are still running.
 jobs={}
 for jp in (R/'jobs').glob('*.json'):
  try:
   j=json.load(open(jp));jobs[(j.get('tag'),j.get('seed'))]=j
  except ValueError:pass
 for log in R.glob('runs/*/slide-*.tsv'):
  try:tag,seed=log.parent.name.rsplit('-s',1);seed=int(seed);j=jobs[(tag,seed)]
  except (ValueError,KeyError):continue
  if tag.startswith('control'):continue
  for line in log.read_text().splitlines():
   parts=line.split('\t')
   if len(parts)!=7 or parts[-1]!='BEST':continue
   key='raw:'+str(log)+':'+parts[0]
   if key in seen:continue
   seen.add(key);side=float(parts[3]);n=j['n']
   if side>bar[n]+.015:continue
   raw=log.parent/'raw'/('%d-sl%d-%s.csv'%(n,seed,parts[0]))
   if not raw.exists():seen.discard(key);continue
   dst=T/'near'/('%d-%s-s%d-t%s-raw.csv'%(n,tag,seed,parts[0]));shutil.copy2(raw,dst)
   atom(dst.with_suffix('.json'),dict(n=n,built=side,bar=bar[n],source=j['source'],licence=j['licence'],certified=False,raw=str(raw)))
   hand('raw kick n=%d side=%.12f gap=%+.9g, %s'%(n,side,side-bar[n],dst))
 for mp in R.glob('q/*/meta.json'):
  key='cert:'+str(mp)
  if key in seen:continue
  try:j=json.load(open(mp))
  except ValueError:continue
  if j.get('quench_rc')!=0:continue
  n=j['n'];src=mp.parent/pathlib.Path(j['quenched_file']).name
  if not src.exists():continue
  source=j['source'];lic=j['licence']
  if n==799 and j['tag'].startswith(('forensics-799-9a406de6','branch799-')) and (W/'799-provenance.json').exists():
   proof=json.load(open(W/'799-provenance.json'));source=proof['source'];lic=proof['licence']
  if lic.startswith(('unresolved','see ')):
   original=re.search(r'$DATA/[^\s,;]+\.csv',source)
   if original and pathlib.Path(original[0]).exists():source,lic=metadata(pathlib.Path(original[0]),n,j)
  if lic.startswith(('unresolved','see ')):
   key2='need-source:'+str(mp)
   if key2 not in seen:state('SOURCE TRACE needed '+str(src));seen.add(key2)
   continue
  dst=W/'stage'/('%d-%s.csv'%(n,mp.parent.name));shutil.copy2(src,dst)
  atom(dst.with_suffix('.json'),dict(source=source+'; local kick seed '+str(j['seed'])+'; raw '+j['best_file']+'; boxE fq from certified input; '+str(mp),licence=lic))
  with open(W/'certify.log','a') as out:subprocess.run([PY,str(W/'certify23.py'),str(W/'stage')],stdout=out,stderr=subprocess.STDOUT,check=True)
  seen.add(key)
 for p in R.glob('designs/*/base.pkl'):
  if p.parent.name.startswith(('library-','import-')):continue
  key='base:'+str(p)+':'+str(p.stat().st_mtime_ns)
  if key in seen:continue
  seen.add(key);hand('joint-offset corner base (partial versions allowed), '+str(p))
 for p in R.glob('designs/*/builds/*.json'):
  key='build:'+str(p)
  if key in seen:continue
  try:d=json.load(open(p));n=d['n']
  except (ValueError,KeyError):continue
  seen.add(key)
  if d.get('built') is None or d['built']>bar[n]+.001:continue
  dst=T/'near'/(str(n)+'-'+p.parent.parent.name+'-'+p.stem+'-family.csv');shutil.copy2(p.with_suffix('.csv'),dst);shutil.copy2(p,dst.with_suffix('.json'));hand('fresh family build n='+str(n)+' side='+str(d['built'])+', '+str(dst))
 if intake and time.time()<int((W/'deadline').read_text())-600:
  # Build geometry references from every already-run round22 start and this round's intake.
  pool={};cache={}
  for root in [OLD,R]:
   for jp in (root/'jobs').glob('*.json'):
    try:
     j=json.load(open(jp));st=j.get('start','');pp=root/st.split('/scratch/squares-twoshort/')[-1]
     if not st or not pp.exists():continue
     if root==OLD and not (root/'locks'/jp.name).exists():continue
     pool.setdefault(j['n'],set()).add(pp)
    except (ValueError,KeyError):continue
  pending=[]
  for jp in (OLD/'jobs').glob('*.json'):
   if (OLD/'locks'/jp.name).exists():continue
   j=json.load(open(jp));st=j.get('start','')
   if not st:continue
   p=OLD/st.split('/scratch/squares-twoshort/')[-1]
   if p.exists():pending.append((p,'pending22',j))
  live=[]
  for td in B.glob('take-*-r23'):
   if td==T:continue
   for pat in ['*.csv','near/*.csv','work/unread/*.csv']:
    live.extend((p,td.name.split('-')[1],None) for p in td.glob(pat))
  # Read the handoff log as well, including raw files below work/.
  hp=B/'handoff-r23.log'
  if hp.exists():
   for line in hp.read_text().splitlines():
    if 'twoshort ->' in line:continue
    key='handoff:'+line
    if key in seen:continue
    seen.add(key)
    lane=line.split(' -> ')[0].split()[-1]
    for path in re.findall(r'$DATA/[^\s,;]+',line):
     library=pathlib.Path(path)/'library.pkl';lens=pathlib.Path(path)/'lens.pkl'
     if not library.exists() or not lens.exists():continue
     digest=hashlib.sha256(library.read_bytes()).hexdigest();lk='library:'+digest
     if lk in seen:continue
     ids=[]
     for needpath in re.findall(r'$DATA/[^\s,;]+\.txt',line):
      np=pathlib.Path(needpath)
      if np.exists():ids.extend(np.read_text().split())
     if not ids:state('LIBRARY has no named new IDs, defer '+path);continue
     seen.add(lk);tag='library-'+lane+'-'+digest[-8:];dd=W/'designs'/tag;ld=dd/'lib';ld.mkdir(parents=True,exist_ok=True)
     shutil.copy2(library,ld/'library.pkl');shutil.copy2(lens,ld/'lens.pkl');(dd/'need.txt').write_text('\n'.join(ids)+'\n')
     rs(dd,remote+'designs/');atom(W/'jobs'/('000-01-'+tag+'.json'),dict(kind='design',f=.69,tag=tag))
     state('QUEUE fresh module library '+path+' IDs='+str(len(ids))+' as '+tag+'; boxE design23.py slice screen; deadline18:30UTC')
    for path in re.findall(r'$DATA/[^\s,;]+\.csv',line):
     p=pathlib.Path(path)
     if p.exists():live.append((p,lane,None))
    for path in re.findall(r'$DATA/[^\s,;]+\.pkl',line):
     p=pathlib.Path(path)
     if p.exists():
      try:
       import pickle
       base=pickle.load(open(p,'rb'))
       if not isinstance(base,list):continue
       base=[q for q in base if isinstance(q,dict) and q.get('c1') in [8,9,10] and q.get('c2') in [8,9,10] and 'f' in q]
       if not base:continue
       digest=hashlib.sha256(p.read_bytes()).hexdigest();pk='pkl:'+digest
       if pk in seen:continue
       seen.add(pk);tag='import-'+lane+'-'+digest[-8:];dd=W/'designs'/tag;dd.mkdir(exist_ok=True);pickle.dump(base,open(dd/'base.pkl','wb'))
       jj=dict(kind='design',f=float(base[0]['f']),tag=tag);atom(W/'jobs'/('000-01-'+tag+'.json'),jj)
       rs(dd,remote+'designs/');state('QUEUE imported corner '+str(p)+' as '+tag+'; boxE design23.py screen; deadline18:30UTC')
      except (ValueError,TypeError,KeyError,pickle.UnpicklingError):continue
  # New live versions first. The pending queue then runs in measured proximity order.
  candidates=[]
  for p,lane,j in live+pending:
   try:
    key='file:'+hashlib.sha256(p.read_bytes()).hexdigest()
    if key in seen:continue
    row=next(csv.DictReader(open(p)));n=int(row['n']);m=math.isqrt(n-1)
    if m not in range(28,32) or n-m*m not in range(5,17):continue
    a,side=load(p);gap=side-bar[n]
    if gap>.02:seen.add(key);continue
    candidates.append((lane=='pending22',gap,-p.stat().st_mtime,n,p,lane,j,key,a,side))
   except (ValueError,KeyError,StopIteration,OSError):continue
  for isold,gap,mt,n,p,lane,j,key,a,side in sorted(candidates,key=lambda t:t[:4]):
   if key in seen:continue
   duplicate=None
   # Already winning inputs keep their own run even when geometrically equal.
   if side>=bar[n]-1e-10*math.sqrt(n):
    for ref in pool.get(n,[]):
     if ref not in cache:cache[ref]=load(ref)
     q,qs=cache[ref]
     if len(q)==len(a) and abs(side-qs)<2e-8 and distance(a,side,q)<2e-8:duplicate=ref;break
   seen.add(key)
   if duplicate:state('DROP geometry copy n=%d %s matches %s'%(n,p,duplicate));continue
   tag=lane+'-'+str(n)+'-'+key[-8:];dst=W/'starts'/(tag+'.csv');shutil.copy2(p,dst)
   source,lic=metadata(p,n,j)
   priority=4 if isold else 0
   if gap>.001:priority+=3
   job=dict(tag=tag,n=n,start='starts/'+dst.name,seed=423,remaining=3 if gap<.001 else 1,seconds=240,miss=0,priority=priority,source=source,licence=lic,force_quench=side<bar[n]-1e-10*math.sqrt(n))
   jp=W/'jobs'/('%03d-%s-423.json'%(priority,tag));atom(jp,job)
   # Batch input transfers after intake.
   pool.setdefault(n,set()).add(dst);state('QUEUE '+tag+' from '+str(p)+' sidegap=%+.9g'%gap+'; command worker23.py invent_rest lkick240s; log runs/'+tag+'-s423; deadline18:30UTC')
 # Copy completed libraries and verify their hashes before removing the remote copies.
 for summary in R.glob('designs/*/summary.json'):
  tag=summary.parent.name;key='archive:'+tag
  if key in seen or not re.fullmatch('[A-Za-z0-9_-]+',tag):continue
  dest=summary.parent/'lib';dest.mkdir(exist_ok=True)
  try:
   rs(remote+'designs/'+tag+'/lib/',str(dest)+'/')
   want={name:hashlib.sha256((dest/name).read_bytes()).hexdigest() for name in ['library.pkl','lens.pkl']}
   import shlex
   code='import pathlib,hashlib,json,shutil;r=pathlib.Path.home()/"scratch/squares-twoshort/designs"/'+repr(tag)+'/"lib";want='+repr(want)+';got={n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in want};assert got==want,(got,want);shutil.rmtree(r);print(json.dumps(got))'
   reply=subprocess.run(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python -c '+shlex.quote(code)],check=True,capture_output=True,text=True,timeout=60)
   (dest/'copy-check.json').write_text(reply.stdout);seen.add(key);state('ARCHIVE verified '+tag+' '+str(dest)+' then removed remote lib; deadline18:30UTC')
   break
  except (subprocess.CalledProcessError,FileNotFoundError) as e:state('ARCHIVE retry '+tag+' '+repr(e))
 rs(str(W/'starts')+'/',remote+'starts/');rs(str(W/'jobs')+'/',remote+'jobs/');atom(seenfile,sorted(seen));print(time.strftime('%FT%TZ',time.gmtime()),'done',len(list(R.glob('done/*.json'))),'jobs',len(list(R.glob('jobs/*.json'))),flush=True)
if __name__=='__main__':
 if '--loop' in sys.argv:
  while time.time()<1794594900 and not (W/'STOP-COLLECT').exists():
   try:subprocess.run([PY,__file__,'--once'],check=True)
   except Exception as e:state('COLLECT ERROR '+repr(e));print(repr(e),flush=True)
   time.sleep(40)
 else:once('--no-intake' not in sys.argv)
