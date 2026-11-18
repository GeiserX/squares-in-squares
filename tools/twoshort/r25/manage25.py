"""Collect this lane, refresh references, and adopt fresh layouts in its slice."""
import csv,hashlib,json,math,os,pathlib,re,shutil,subprocess,sys,time,signal
csv.field_size_limit(16000000)
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
B=pathlib.Path('$SCRATCH/bounties-squares');T=B/'take-twoshort-r25';W=T/'work';R=W/'boxE25';R.mkdir(exist_ok=True)
OLD=B/'take-twoshort-r25/work/empty-old';PY=str(B/'venv/bin/python');remote='boxE:scratch/squares-twoshort/'
sys.path.insert(0,str(W));from shape974 import load,distance
seenfile=W/'seen.json';seen=set(json.load(open(seenfile))) if seenfile.exists() else set()
recheck_path=W/'recheck-source-keys-v2.json';recheck=set(json.load(open(recheck_path))) if recheck_path.exists() else set()
def atom(p,d):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2));t.replace(p)
def state(s):
 with open(T/'STATE.txt','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA '+s+'\n')
def hand(s):
 with open(B/'handoff-r25.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> all: '+s+'\n')
def rs(src,dst,*opts):subprocess.run(['rsync','-az',*opts,str(src),str(dst)],check=True,timeout=90)
from source25 import allowed as safe_source
from admit25 import module_allowed as allowed_module,trace_input
from bar25 import bars as policy_bars,label as policy_label
_metadata_cache={};_table_cache={}
def table_rows(p):
 st=p.stat();key=(str(p),st.st_mtime_ns,st.st_size)
 if key not in _table_cache:_table_cache[key]=list(csv.DictReader(open(p),delimiter='\t'))
 return _table_cache[key]
def metadata(p,n,fallback=None,depth=0):
 st=p.stat();key=(str(p),n,st.st_mtime_ns,st.st_size)
 if fallback is None and key in _metadata_cache:return _metadata_cache[key]
 result=metadata_uncached(p,n,fallback,depth)
 if fallback is None:_metadata_cache[key]=result
 return result
def approved_job(j):
 if not safe_source(j['source'],j['licence']):return False
 pp=j.get('input_ancestry_proof')
 if not pp or not pathlib.Path(pp).exists():
  from admit25 import store
  return store(dict(source=j['source'],licence=j['licence']),n=j.get('n'))[0]
 proof=json.load(open(pp));snap=pathlib.Path(proof.get('snapshot',''))
 if not (proof.get('admitted') is True and snap.is_file() and hashlib.sha256(snap.read_bytes()).hexdigest()==proof.get('sha256')):return False
 from admit25 import store
 return store(dict(source=j['source'],licence=j['licence']),n=j.get('n'))[0]
def metadata_uncached(p,n,fallback=None,depth=0):
 from admit25 import plain_credit
 plain=plain_credit(p,n)
 if plain:return plain['source'],plain['licence']
 source=str(p);lic='unresolved: '+str(p)
 for tp in [p.parent/'take.tsv',p.parent.parent/'take.tsv']:
  if tp.exists():
   for r in table_rows(tp):
    if r['n']==str(n) and p.parent==tp.parent:
     source+='; '+str(tp)+'; '+r['source']
     if not r.get('licence','').startswith(('see ','unresolved')):return source,r.get('licence',lic)
 for jp in [p.with_suffix('.json'),pathlib.Path(str(p)+'.json')]:
  if jp.exists():
   try:
    md=json.load(open(jp));mods=md.get('modules')
    if md.get('parent_path') and depth<8:
     parent=pathlib.Path(md['parent_path'])
     if parent.exists():
      digest=hashlib.sha256(parent.read_bytes()).hexdigest()
      if md.get('parent_sha256') and md['parent_sha256']!=digest:
       snap=p.parent.parent/'work/box/donors'/(md.get('parent_donor','')+'.csv')
       if not snap.exists() or hashlib.sha256(snap.read_bytes()).hexdigest()!=md['parent_sha256']:return source+'; refused changed parent', 'unresolved: parent hash mismatch'
       def notices(obj):
        if isinstance(obj,dict):
         for k,v in obj.items():
          if k=='licence' and isinstance(v,str) and not v.startswith(('see ','unresolved')):yield v
          elif isinstance(v,(dict,list)):yield from notices(v)
        elif isinstance(obj,list):
         for v in obj:yield from notices(v)
       admission=md.get('admission',{});notices_found=sorted(set(notices(admission)))
       if not notices_found:return source+'; immutable parent missing notices', 'unresolved: parent licence'
       source+='; immutable parent '+str(snap)+' sha256 '+md['parent_sha256']+'; frozen admission '+json.dumps(admission)
       lic='; '.join(notices_found);parent=None
      if parent is None:continue
      pn=int(next(csv.DictReader(open(parent)))['n']);ps,pl=metadata(parent,pn,depth=depth+1)
      if not pl.startswith(('unresolved','see ')):source+='; parent '+ps;lic=pl
    if md.get('parts'):
     source+='; rectangle composition '+json.dumps(md['parts']);lic='our composition; '+'; '.join(sorted({v['licence'] for v in md['parts'].values() if isinstance(v,dict) and 'licence' in v}))
    if mods:source+='; modules '+json.dumps(mods);lic='; '.join(sorted({m['licence'] for m in mods}))
    elif md.get('source') and md.get('licence'):
     source+='; '+md['source']
     if not md['licence'].startswith(('see ','unresolved')) or lic.startswith(('unresolved','see ')):lic=md['licence']
   except (ValueError,KeyError,TypeError):pass
 for parent in [p.parent,p.parent.parent,p.parent.parent.parent]:
  for name in ['sources.tsv','sources-all.tsv','work/sources.tsv','work/sources-all.tsv']:
   sp=parent/name
   if not sp.exists():continue
   for row in table_rows(sp):
    donor=row.get('donor','')
    if donor and (p.stem==donor or p.stem.endswith('from'+donor)):
     source+='; '+str(sp)+'; '+row['source']
     if not row['licence'].startswith(('see ','unresolved')) or lic.startswith(('unresolved','see ')):lic=row['licence']
 if lic.startswith(('unresolved','see ')) and depth<2 and fallback:
  original=re.search(r'$DATA/[^\s,;]+\.csv',fallback.get('source',''))
  if original and pathlib.Path(original[0]).exists() and pathlib.Path(original[0])!=p:
   src2,lic2=metadata(pathlib.Path(original[0]),n,depth=depth+1)
   if not lic2.startswith(('unresolved','see ')):return source+'; '+src2,lic2
 if fallback and not fallback.get('licence','').startswith(('unresolved','see ')):source+='; '+fallback['source'];lic=fallback['licence']
 return source,lic

def once(intake=True):
 intake_started=time.time()
 rs(remote,R,'--exclude=lane','--exclude=tmp','--exclude=lib','--exclude=lib-z4','--exclude=reference')
 held=list(csv.DictReader(open(B/'gate/cand-round23-1113b/details.csv')));_,_,_,scores=policy_bars()
 bar={n:(1+s)*math.sqrt(n) for n,s in scores.items()}
 atom(W/'bar.json',{str(n):s for n,s in bar.items()})
 with open(W/'details-bar.csv','w',newline='') as f:
  cw=csv.writer(f);cw.writerow(['n','L','score','min_gap']);cw.writerows([int(r['n']),bar[int(r['n'])],scores[int(r['n'])],r['min_gap']] for r in held)
 rs(W/'bar.json',remote+'bar.json');rs(W/'details-bar.csv',remote+'details-bar.csv')
 if (R/'worker.log').exists():
  for line in (R/'worker.log').read_text().splitlines():
   key='event:'+line
   if key not in seen:state('boxE '+line+'; log work/boxE25; deadline02:45UTC');seen.add(key)
 # Export raw changes while scans are still running.
 jobs={}
 for jp in (R/'jobs').glob('*.json'):
  try:
   j=json.load(open(jp));jobs[(j.get('tag'),j.get('seed'))]=j
  except ValueError:pass
 for log in R.glob('runs/*/slide-*.tsv'):
  try:tag,seed=log.parent.name.rsplit('-s',1);seed=int(seed);j=jobs[(tag,seed)]
  except (ValueError,KeyError):continue
  if tag.startswith('control') or not approved_job(j):continue
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
   atom(dst.with_suffix('.json'),dict(n=n,built=side,bar=bar[n],source=j['source'],licence=j['licence'],certified=False,input_ancestry_proof=j.get('input_ancestry_proof'),raw=str(raw)))
   hand('raw kick n=%d side=%.12f gap=%+.9g, %s'%(n,side,side-bar[n],dst))
 new_stages=[]
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
  atom(dst.with_suffix('.json'),dict(source=source+'; local kick seed '+str(j['seed'])+'; raw '+j['best_file']+'; boxE fq from certified input; '+str(mp),licence=lic,ancestry_checked=approved_job(j), source_proof=j.get('input_ancestry_proof')))
  new_stages.append(dst)
  seen.add(key)
 if new_stages:
  with open(W/'certify.log','a') as out:subprocess.run([PY,str(W/'certify25.py'),str(W/'stage'),'--paths']+list(map(str,new_stages)),stdout=out,stderr=subprocess.STDOUT,check=True)
 with open(W/'prune-take.log','a') as out:subprocess.run([PY,str(W/'prune_take25.py')],stdout=out,stderr=subprocess.STDOUT,check=True)
 for p in R.glob('designs/*/base.pkl'):
  if p.parent.name.startswith(('library-','import-')):continue
  key='base:'+str(p)+':'+str(p.stat().st_mtime_ns)
  if key in seen:continue
  seen.add(key);hand('fresh corner base (partial versions allowed), '+str(p))
 for p in R.glob('designs/*/builds/*.json'):
  key='build:'+str(p)
  if key in seen:continue
  try:d=json.load(open(p));n=d['n']
  except (ValueError,KeyError):continue
  seen.add(key)
  if p.parent.parent.name.startswith('control'):continue
  if not (bool(d.get('modules')) and all(allowed_module(m) for m in d['modules'])):continue
  if d.get('built') is None or d['built']>bar[n]+.001:continue
  dst=T/'near'/(str(n)+'-'+p.parent.parent.name+'-'+p.stem+'-family.csv');shutil.copy2(p.with_suffix('.csv'),dst);shutil.copy2(p,dst.with_suffix('.json'));hand('fresh family build n='+str(n)+' side='+str(d['built'])+', '+str(dst))
 if intake and time.time()<int((W/'search-deadline').read_text()):
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
  for td in B.glob('take-*-r25'):
   if td==T:continue
   for pat in ['*.csv','near/*.csv','work/unread/*.csv']:
    live.extend((p,td.name.split('-')[1],None) for p in td.glob(pat))
  # Read the handoff log as well, including raw files below work/.
  hp=B/'handoff-r25.log'
  if hp.exists():
   for line in hp.read_text().splitlines():
    if 'twoshort ->' in line:continue
    key='handoff-v2:'+line
    if key in seen:continue
    seen.add(key)
    lane=line.split(' -> ')[0].split()[-1]
    for path in re.findall(r'$DATA/[^\s,;]+',line):
     library=pathlib.Path(path)/'library.pkl';lens=pathlib.Path(path)/'lens.pkl'
     if not library.exists() or not lens.exists():continue
     digest=hashlib.sha256(library.read_bytes()).hexdigest();lens_digest=hashlib.sha256(lens.read_bytes()).hexdigest()
     ids=[]
     for needpath in re.findall(r'$DATA/[^\s,;]+\.txt',line):
      np=pathlib.Path(needpath)
      if np.exists():ids.extend(np.read_text().split())
     if not ids:state('LIBRARY has no named new IDs, defer '+path);continue
     ids=sorted(set(ids));id_digest=hashlib.sha256('\n'.join(ids).encode()).hexdigest();lk='library-v2:'+digest+':'+lens_digest+':'+id_digest
     if lk in seen:continue
     seen.add(lk);tag='library-'+lane+'-'+hashlib.sha256((digest+lens_digest).encode()).hexdigest()[:8]+'-'+id_digest[:8];dd=W/'designs'/tag;dd.mkdir(parents=True,exist_ok=True)
     import pickle
     shared_key=hashlib.sha256((digest+lens_digest).encode()).hexdigest()[:20];shared=W/'libraries'/shared_key
     if not (shared/'library.pkl').exists():
      shared.mkdir(parents=True,exist_ok=True);lib=pickle.load(open(library,'rb'));lib['mods']=[m for m in lib['mods'] if m['id'] in ids and allowed_module(m)];lib['layouts']=[]
      for m in lib['mods']:
       if m['tag']=='z' and m['licence']=='our own':m['ours']=True
      pickle.dump(lib,open(shared/'library.pkl','wb'));lt=pickle.load(open(lens,'rb'));keep={m['id'] for m in lib['mods']};pickle.dump({k:v for k,v in lt.items() if k in keep},open(shared/'lens.pkl','wb'));named=shared/'named';named.mkdir(exist_ok=True);shutil.copy2(shared/'library.pkl',named/'library.pkl');shutil.copy2(shared/'lens.pkl',named/'lens.pkl');from union25 import merge as merge_pairs;merge_pairs([named,W/'designs/library-original-union25/lib'],shared);subprocess.run(['ssh','boxE','mkdir -p $SCRATCH/squares-twoshort/libraries'],check=True,timeout=30);rs(shared,remote+'libraries/')
     lib=pickle.load(open(shared/'library.pkl','rb'));allowed={m['id'] for m in lib['mods']};ids=[i for i in ids if i in allowed]
     if not ids:continue
     ld=dd/'lib'
     if not ld.exists():ld.symlink_to(pathlib.Path('../../libraries')/shared_key,target_is_directory=True)
     (dd/'need.txt').write_text('\n'.join(ids)+'\n')
     rs(dd,remote+'designs/');atom(W/'jobs'/('001-01-'+tag+'.json'),dict(kind='design',f=.69,tag=tag))
     state('QUEUE fresh module library '+path+' IDs='+str(len(ids))+' as '+tag+'; boxE design25.py slice screen; deadline02:45UTC')
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
       base=[q for q in base if safe_source(q.get('source',''),q.get('licence','our own'))]
       if not base:continue
       digest=hashlib.sha256(p.read_bytes()).hexdigest();pk='pkl:'+digest
       if pk in seen:continue
       seen.add(pk);tag='import-'+lane+'-'+digest[-8:];dd=W/'designs'/tag;dd.mkdir(exist_ok=True);pickle.dump(base,open(dd/'base.pkl','wb'))
       jj=dict(kind='design',f=float(base[0]['f']),tag=tag);atom(W/'jobs'/('001-01-'+tag+'.json'),jj)
       rs(dd,remote+'designs/');state('QUEUE imported corner '+str(p)+' as '+tag+'; boxE design25.py screen; deadline02:45UTC')
      except (ValueError,TypeError,KeyError,pickle.UnpicklingError):continue
  # New live versions first. The pending queue then runs in measured proximity order.
  candidates=[]
  for p,lane,j in live:
   try:
    key='file:'+hashlib.sha256(p.read_bytes()).hexdigest()
    if key in seen and key not in recheck:continue
    row=next(csv.DictReader(open(p)));n=int(row['n']);m=math.isqrt(n-1)
    outside=m not in range(28,32) or n-m*m not in range(5,17)
    a,side=load(p);gap=side-bar[n]
    if outside and (gap>.001 or lane not in ['modules','corners','readers','family','forensics','k123','rebuild','gap','stair','stair-c']):continue
    if gap>.02:seen.add(key);continue
    candidates.append((lane=='pending22',gap,-p.stat().st_mtime,n,p,lane,j,key,a,side))
   except (ValueError,KeyError,StopIteration,OSError):continue
  intake_started=time.time()
  def admission_order(t):
   rank=0 if t[5] in ['forensics','k123'] or '/public/' in str(t[4]) else 1 if t[5] in ['modules','corners'] else 2 if t[5] in ['family','readers','classfill','stair-c'] else 3
   return (t[0],rank,t[1],t[2],t[3])
  for isold,gap,mt,n,p,lane,j,key,a,side in sorted(candidates,key=admission_order):
   if time.time()-intake_started>150:state('INTAKE checkpoint, transfer fresh jobs before next cycle');break
   if key in seen and key not in recheck:continue
   duplicate=None
   # Already winning inputs keep their own run even when geometrically equal.
   if side>=bar[n]-1e-10*math.sqrt(n):
    for ref in pool.get(n,[]):
     if ref not in cache:cache[ref]=load(ref)
     q,qs=cache[ref]
     if len(q)==len(a) and abs(side-qs)<2e-8 and distance(a,side,q)<2e-8:duplicate=ref;break
   seen.add(key)
   if duplicate:state('DROP geometry copy n=%d %s matches %s'%(n,p,duplicate));continue
   tag=lane+'-'+str(n)+'-'+key[-8:];dst=W/'starts'/(tag+'.csv')
   try:shutil.copy2(p,dst)
   except FileNotFoundError:seen.discard(key);state('DEFER vanished input '+str(p));continue
   if 'file:'+hashlib.sha256(dst.read_bytes()).hexdigest()!=key:
    seen.discard(key);state('DEFER input changed during intake '+str(p));continue
   try:source,lic=metadata(p,n,j);lic=policy_label(source,lic)
   except (csv.Error,ValueError,KeyError,OSError,RecursionError) as ex:
    state('DEFER malformed source '+str(p)+' '+repr(ex));recheck.discard(key);continue
   recheck.discard(key)
   input_proof=None
   if True:
    try:admitted,ancestry=trace_input(p,n)
    except (OSError,ValueError,KeyError,RecursionError):admitted=False
    if not admitted or lic.startswith(('see ','unresolved')):
     state('DEFER ancestry '+str(p));recheck.add(key);continue
    if hashlib.sha256(p.read_bytes()).hexdigest()!=key.removeprefix('file:'):
     seen.discard(key);state('DEFER source changed during ancestry walk '+str(p));continue
    input_proof=W/'intake'/(tag+'-ancestry.json');atom(input_proof,dict(admitted=True,snapshot=str(dst),sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),ancestry=ancestry))
    source+='; verified input ancestry '+str(input_proof)
   proof=W/'intake'/(tag+'.json');atom(proof,dict(origin=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source=source,licence=lic))
   source+='; immutable intake '+str(proof)
   priority=60 if isold else 0 if side<bar[n]-1e-10*math.sqrt(n) else 1 if lane in ['forensics','k123','rebuild','gap'] else 2 if lane in ['modules','corners','readers','family'] else 3
   if gap>.001:priority+=3
   job=dict(tag=tag,n=n,start='starts/'+dst.name,seed=625,remaining=2 if gap<.001 else 1,seconds=180,miss=0,priority=priority,source=source,licence=lic,force_quench=side<bar[n]-1e-10*math.sqrt(n))
   if input_proof:job['input_ancestry_proof']=str(input_proof)
   jp=W/'jobs'/('%03d-%s-625.json'%(priority,tag));atom(jp,job)
   # Batch input transfers after intake.
   pool.setdefault(n,set()).add(dst);state('QUEUE '+tag+' from '+str(p)+' sidegap=%+.9g'%gap+'; command worker25.py invent_rest lkick180s; log runs/'+tag+'-s625; deadline02:45UTC')
 if intake and time.time()<int((W/'search-deadline').read_text()):
  import pickle
  for line in (B/'handoff-r25.log').read_text().splitlines():
   if 'twoshort ->' in line:continue
   for path in re.findall(r'$DATA/[^\s,;]+',line):
    folder=pathlib.Path(path);zp=folder/'corners.pkl'
    if not zp.exists():continue
    digest=hashlib.sha256(zp.read_bytes()).hexdigest();key='zone:'+digest
    if key in seen:continue
    seen.add(key)
    mods=pickle.load(open(zp,'rb'));mods=[m for m in mods if isinstance(m,dict) and allowed_module(m)]
    if not mods:state('DEFER zone ancestry '+str(zp));continue
    tag='library-zones-'+digest[:12];dd=W/'designs'/tag;(dd/'zones').mkdir(parents=True,exist_ok=True)
    pickle.dump(mods,open(dd/'zones/corners.pkl','wb'));(dd/'need.txt').write_text('\n'.join(m['id'] for m in mods)+'\n')
    atom(dd/'intake.json',dict(path=str(zp),sha256=digest,source_records=[dict(id=m['id'],source=m['src'],licence=m['licence']) for m in mods]))
    rs(dd,remote+'designs/');atom(W/'jobs'/('001-'+tag+'.json'),dict(kind='design',f=.69,tag=tag));state('QUEUE new zones '+str(zp)+' as '+tag+'; log designs/'+tag+'; deadline02:45UTC')
 auditstamp=W/'last-audit'
 if False:
  with open(W/'audit.log','a') as out:subprocess.run([PY,str(W/'audit25.py')],stdout=out,stderr=subprocess.STDOUT,check=True)
  auditstamp.write_text(str(time.time()))
 rs(str(W/'starts')+'/',remote+'starts/');rs(str(W/'jobs')+'/',remote+'jobs/');subprocess.run(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python -I $SCRATCH/squares-twoshort/prioritize25.py'],check=True,timeout=30);atom(seenfile,sorted(seen));atom(recheck_path,sorted(recheck));print(time.strftime('%FT%TZ',time.gmtime()),'done',len(list(R.glob('done/*.json'))),'jobs',len(list(R.glob('jobs/*.json'))),flush=True)
if __name__=='__main__':
 if '--loop' in sys.argv:
  while time.time()<int((W/'deadline').read_text())+300 and not (W/'STOP-COLLECT').exists():
   try:subprocess.run([PY,__file__,'--once'],check=True)
   except Exception as e:state('COLLECT ERROR '+repr(e));print(repr(e),flush=True)
   time.sleep(40)
 else:
  once('--no-intake' not in sys.argv)
  sys.stdout.flush();sys.stderr.flush();os._exit(0)
