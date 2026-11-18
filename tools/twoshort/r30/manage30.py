"""Collect this lane, refresh references, and adopt fresh layouts in its slice."""
import csv,hashlib,json,math,os,pathlib,re,shutil,subprocess,sys,time,signal
csv.field_size_limit(16000000)
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
B=pathlib.Path('$SCRATCH/bounties-squares');T=B/'take-twoshort-r30';W=T/'work';R=W/'boxE30';R.mkdir(exist_ok=True)
OLD=B/'take-twoshort-r29/work/boxE29';PY=str(B/'venv/bin/python');remote='boxE:scratch/squares-twoshort/'
sys.path.insert(0,str(W));from shape974 import load,distance
seenfile=W/'seen.json';seen=set(json.load(open(seenfile))) if seenfile.exists() else set()
recheck_path=W/'recheck-source-keys-v2.json';recheck=set(json.load(open(recheck_path))) if recheck_path.exists() else set()
def atom(p,d):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2));t.replace(p)
def state(s):
 with open(T/'STATE.txt','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA '+s+'\n')
def hand(s):
 with open(B/'handoff-r30.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> all: '+s+'\n')
def rs(src,dst,*opts):subprocess.run(['rsync','-az',*opts,str(src),str(dst)],check=True,timeout=90)
from source30 import allowed as safe_source
from admit30 import module_allowed as allowed_module,trace_input_lenient as trace_input
from bar30 import bars as policy_bars,label as policy_label
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
_approved={}
BOXE='$SCRATCH/squares-twoshort/'
def approved_job(j):
 k=(j.get('tag'),str(j.get('seed')),j.get('source'),j.get('licence'),j.get('input_ancestry_proof'))
 if k not in _approved:_approved[k]=approved_job_uncached(j)
 return _approved[k]
def prv_copy(text):
 # Round 27: the prvsiyan rule is the share test on the layout itself (0.4 within 1e-3), run by qwalk30.py on every
 # start at intake and on every result at certification. A recorded distance no longer refuses.
 return False
def approved_job_uncached(j):
 if not safe_source(j['source'],j['licence']):return False
 pp0=j.get('input_ancestry_proof')
 if prv_copy(j['source']+' '+j['licence']+' '+(open(pp0).read() if pp0 and pathlib.Path(pp0).exists() else '')):return False
 pp=j.get('input_ancestry_proof')
 if not pp or not pathlib.Path(pp).exists():
  from admit30 import store_lenient
  return store_lenient(dict(source=j['source'],licence=j['licence']),n=j.get('n'))[0]
 proof=json.load(open(pp));snap=pathlib.Path(proof.get('snapshot',''))
 if not (proof.get('admitted') is True and snap.is_file() and hashlib.sha256(snap.read_bytes()).hexdigest()==proof.get('sha256')):return False
 from admit30 import store_lenient
 return store_lenient(dict(source=j['source'],licence=j['licence']),n=j.get('n'))[0]
def _sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def snapshot_sidecar(tag):
 """Round 28: a sidecar beside our byte snapshot of an input: the origin, its record as read at intake (the origin's
 own sidecar copied when the origin is still the same bytes), and the source text of our intake without proof paths."""
 snap=W/'starts'/(tag+'.csv');ip=W/'intake'/(tag+'.json')
 if not snap.exists() or not ip.exists():return None
 side=snap.with_name(snap.name+'.json')
 if side.exists():return snap
 intake=json.load(open(ip));origin=intake.get('origin','')
 src0=re.sub(r';\s*verified input ancestry \S+','',intake.get('source',''))
 rec=None
 if origin and pathlib.Path(origin).is_file() and _sha(origin)==intake.get('sha256')==_sha(snap):
  for cand in [origin+'.json',origin[:-4]+'.json',origin[:-4]+'.origin.json',origin[:-4]+'.source.json']:
   if pathlib.Path(cand).is_file():
    try:rec=json.load(open(cand));break
    except ValueError:pass
 d=dict(source='byte snapshot of '+origin+'; '+src0,licence=intake.get('licence',''),origin=origin,origin_sha256_at_intake=intake.get('sha256'))
 if isinstance(rec,dict):d=dict(rec,**{k:v for k,v in d.items() if k not in rec or k in ('origin',)},snapshot_of=origin,twoshort_intake_source=d['source'])
 atom(side,d);return snap
def _upstream(snap):
 txt=''
 for q in (pathlib.Path(str(snap)+'.json'),W/'intake'/(pathlib.Path(str(snap)).stem+'.json')):
  if q.is_file():txt+=q.read_text()
 refs=sorted({(r[0] or r[1]) if isinstance(r,tuple) else r for r in re.findall(r'(?:notebooks/|datasets/|upstream\s+|->\s*)([A-Za-z0-9_-]+/[A-Za-z0-9_-]+)|([A-Za-z0-9_-]+/[A-Za-z0-9_-]+)\s*::',txt)} - {''})
 refs=[r for r in refs if not r.startswith('areebbb/')]
 return ('; upstream credits named by the input record: '+', '.join('upstream '+r for r in refs)) if refs else ''
def clean_record(j,lic):
 snap=snapshot_sidecar(j['tag'])
 if snap is None:return None
 raw=pathlib.Path(j['best_file'].replace(BOXE,str(R)+'/'))
 if not raw.is_file():return None
 return dict(source='twoshort round 30: '+('midm_scan.py --modes lkick,kick (%d s, seed %d)'%(j.get('seconds',900),j['seed']) if j.get('tool')=='midm' else 'invent_rest.py lkick (180 s legs, seed '+str(j['seed'])+')')+' of '+str(snap)+' (sha256 '+_sha(snap)+'), a byte snapshot of '+json.load(open(W/'intake'/(j['tag']+'.json'))).get('origin','')+' with its record beside it; raw best '+str(raw)+' (sha256 '+_sha(raw)+'); one fq quench of the floatsafe-certified raw best on boxE'+_upstream(snap),licence=lic,parent_path=str(snap),parent_sha256=_sha(snap))
def metadata_uncached(p,n,fallback=None,depth=0):
 from admit30 import plain_credit
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

_claims=[None,set()]
def backlog_claims():
 hp=B/'handoff-r30.log'
 try:st=hp.stat().st_size
 except OSError:return set()
 if _claims[0]!=st:
  c=set()
  for line in hp.read_text().splitlines():
   if re.search(r'\bclaims?\b',line) and ' twoshort -> ' not in line:c.update(re.findall(r'$DATA/[^\s,;]+\.csv',line))
  _claims[:]=[st,c]
 return _claims[1]
_wd=[None,set()]
def withdrawn_shas():
 hp=B/'handoff-r30.log'
 try:st=hp.stat().st_size
 except OSError:return set()
 if _wd[0]!=st:
  c=set()
  for line in hp.read_text().splitlines():
   if 'WITHDRAW' in line:c.update(re.findall(r'sha256 ([0-9a-f]{64})',line))
  _wd[:]=[st,c]
 return _wd[1]
def once(intake=True):
 intake_started=time.time()
 rs(remote,R,'--exclude=lane','--exclude=tmp','--exclude=lib','--exclude=lib-z4','--exclude=reference')
 held=list(csv.DictReader(open(B/'gate/cand-round28-1115b/details.csv')));_,_,_,scores=policy_bars()
 bar={n:(1+s)*math.sqrt(n) for n,s in scores.items()}
 atom(W/'bar.json',{str(n):s for n,s in bar.items()})
 with open(W/'details-bar.csv','w',newline='') as f:
  cw=csv.writer(f);cw.writerow(['n','L','score','min_gap']);cw.writerows([int(r['n']),bar[int(r['n'])],scores[int(r['n'])],r['min_gap']] for r in held)
 rs(W/'bar.json',remote+'bar.json');rs(W/'details-bar.csv',remote+'details-bar.csv')
 if (R/'worker.log').exists():
  for line in (R/'worker.log').read_text().splitlines():
   key='event:'+line
   if key not in seen:state('boxE '+line+'; log work/boxE30; deadline17:45UTC');seen.add(key)
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
  ok=None
  for line in log.read_text().splitlines():
   parts=line.split('\t')
   if len(parts)!=7 or parts[-1]!='BEST':continue
   key='raw:'+str(log)+':'+parts[0]
   if key in seen:continue
   side=float(parts[3]);n=j['n']
   if side>bar[n]+.015:seen.add(key);continue
   if ok is None:ok=approved_job(j)
   if not ok:break
   seen.add(key)
   raw=log.parent/'raw'/('%d-sl%d-%s.csv'%(n,seed,parts[0]))
   if not raw.exists():seen.discard(key);continue
   dst=T/'near'/('%d-%s-s%d-t%s-raw.csv'%(n,tag,seed,parts[0]));shutil.copy2(raw,dst)
   atom(dst.with_suffix('.json'),dict(n=n,built=side,bar=bar[n],source=j['source'],licence=j['licence'],certified=False,input_ancestry_proof=j.get('input_ancestry_proof'),raw=str(raw)))
   if side<bar[n]:hand('raw kick below bar n=%d side=%.12f gap=%+.9g, %s'%(n,side,side-bar[n],dst))
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
  # Round 26: name the local mirror copies, not boxE paths. quench_walk reads a boxE path whose run tag
  # starts with harvest- as a scratch file that is gone, and refused 459, 499, 646, 818 and 850 for that.
  qm=W/'qmeta'/(mp.parent.name+'.json');qm.parent.mkdir(exist_ok=True)
  # Round 27: rewrite only this job's own boxE paths; inherited records keep theirs (the walk reads $DATA paths only).
  def own(t):
   for pre in ('runs/','q/'):t=t.replace(BOXE+pre+j['tag']+'-s',str(R)+'/'+pre+j['tag']+'-s')
   return t.replace(BOXE+'starts/'+j['tag'],str(R)+'/starts/'+j['tag'])
  atom(qm,json.loads(own(json.dumps(j))))
  # Round 28: a clean stage record. The old record named our intake ancestry proof and qmeta, whose admit closure
  # (2632 files for forensics 697) reaches take-readers-r22/work/follow.json, its gone files and the r22 745/858 join
  # text: quench_walk refused 697 (2.3e-3 of side below the bar) and every r27 812 stair kick for that alone.
  clean=clean_record(j,lic)
  if clean is None:
   key3='clean-record:'+str(mp)
   if key3 not in seen:state('SOURCE TRACE no clean record for '+str(src));seen.add(key3)
   continue
  atom(dst.with_suffix('.json'),dict(clean,ancestry_checked=approved_job(j)))
  new_stages.append(dst)
  seen.add(key)
 if new_stages:
  with open(W/'certify.log','a') as out:subprocess.run([PY,str(W/'certify30.py'),str(W/'stage'),'--paths']+list(map(str,new_stages)),stdout=out,stderr=subprocess.STDOUT,check=True)
 with open(W/'prune-take.log','a') as out:subprocess.run([PY,str(W/'prune_take30.py')],stdout=out,stderr=subprocess.STDOUT,check=True)
 with open(W/'qgate.log','a') as out:subprocess.run([PY,str(W/'qgate30.py')],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=1800)
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
  for td in B.glob('take-*-r30'):
   if td==T:continue
   for pat in ['*.csv','near/*.csv','work/unread/*.csv']:
    live.extend((p,td.name.split('-')[1],None) for p in td.glob(pat))
  # Round 27: inputs refused or withdrawn only for the Samanyu-dev seed in earlier rounds (work/reopen.txt, path<TAB>lane).
  rp=W/'reopen.txt'
  if rp.exists():
   for line in rp.read_text().splitlines():
    if not line.strip() or line.startswith('#'):continue
    path,_,lane=line.partition('\t');q=pathlib.Path(path.strip())
    if q.is_file():live.append((q,(lane.strip() or 'reopen'),None))
  # Read the handoff log as well, including raw files below work/.
  hp=B/'handoff-r30.log'
  if hp.exists():
   for line in hp.read_text().splitlines():
    if 'twoshort ->' in line:continue
    key='handoff-v2:'+line
    if key in seen:continue
    seen.add(key)
    lane=line.split(' -> ')[0].split()[-1]
    for path in re.findall(r'$DATA/[^\s,;]+',line):
     library=pathlib.Path(path)/'library.pkl';lens=pathlib.Path(path)/'lens.pkl'
     # Round 27: module family screens stay out of the queue (round 26 next item 5); a union library with no lib crashed the cycle.
     continue
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
      pickle.dump(lib,open(shared/'library.pkl','wb'));lt=pickle.load(open(lens,'rb'));keep={m['id'] for m in lib['mods']};pickle.dump({k:v for k,v in lt.items() if k in keep},open(shared/'lens.pkl','wb'));named=shared/'named';named.mkdir(exist_ok=True);shutil.copy2(shared/'library.pkl',named/'library.pkl');shutil.copy2(shared/'lens.pkl',named/'lens.pkl');from union30 import merge as merge_pairs;merge_pairs([named,W/'designs/library-original-union30/lib'],shared);subprocess.run(['ssh','boxE','mkdir -p $SCRATCH/squares-twoshort/libraries'],check=True,timeout=30);rs(shared,remote+'libraries/')
     lib=pickle.load(open(shared/'library.pkl','rb'));allowed={m['id'] for m in lib['mods']};ids=[i for i in ids if i in allowed]
     if not ids:continue
     ld=dd/'lib'
     if not ld.exists():ld.symlink_to(pathlib.Path('../../libraries')/shared_key,target_is_directory=True)
     (dd/'need.txt').write_text('\n'.join(ids)+'\n')
     rs(dd,remote+'designs/');atom(W/'jobs'/('001-01-'+tag+'.json'),dict(kind='design',f=.69,tag=tag))
     state('QUEUE fresh module library '+path+' IDs='+str(len(ids))+' as '+tag+'; boxE design30.py slice screen; deadline17:45UTC')
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
       rs(dd,remote+'designs/');state('QUEUE imported corner '+str(p)+' as '+tag+'; boxE design30.py screen; deadline17:45UTC')
      except (ValueError,TypeError,KeyError,pickle.UnpicklingError):continue
  # New live versions first. The pending queue then runs in measured proximity order.
  # Round 26: a deferred file is walked again at most every 15 minutes, so refusals do not stall the cycle.
  rtp=W/'recheck-times.json';rtimes=json.load(open(rtp)) if rtp.exists() else {}
  candidates=[]
  for p,lane,j in live:
   try:
    key='file:'+hashlib.sha256(p.read_bytes()).hexdigest()
    if key in seen and key not in recheck:continue
    if key in recheck and time.time()-rtimes.get(key,0)<900:
     # Round 28: an input that waited only for the walker is taken up as soon as its walk is cached.
     import qgate30
     if not ('qwalk-wait:'+key in seen and qgate30.lookup(p) is not None):continue
    if key in recheck:rtimes[key]=time.time()
    row=next(csv.DictReader(open(p)));n=int(row['n']);m=math.isqrt(n-1)
    outside=m not in range(28,32) or n-m*m not in range(5,17)
    a,side=load(p);gap=side-bar[n]
    if outside and gap>.001:continue
    if gap>.02:seen.add(key);continue
    candidates.append((lane=='pending22',gap,-p.stat().st_mtime,n,p,lane,j,key,a,side))
   except (ValueError,KeyError,StopIteration,OSError):continue
  intake_started=time.time()
  # Round 26: starts at the same side as two earlier dry kicks of the same n are copies of a settled floor.
  dry={}
  for dp in R.glob('done/*.json'):
   try:dd=json.load(open(dp))
   except ValueError:continue
   if 'start_side' in dd and dd['start_side']-dd['best']<1e-12:dry.setdefault(dd['n'],[]).append(dd['start_side'])
  def dry_copy(n,side):return sum(abs(side-s0)<1e-11 for s0 in dry.get(n,[]))>=2
  def admission_order(t):
   # Round 26: a certified row of another lane below the base bar is a new design that already counts; walk it first.
   rank=-1 if re.search(r'/take-[a-z0-9-]+-r30/\d+\.csv$',str(t[4])) else 0 if t[1]<0 or t[5] in ['forensics','k123'] or t[5].startswith('reopen') or '/public/' in str(t[4]) else 1 if t[5] in ['modules','corners'] else 2 if t[5] in ['family','readers','classfill','stair-c'] else 3
   return (t[0],rank,t[1],t[2],t[3])
  for isold,gap,mt,n,p,lane,j,key,a,side in sorted(candidates,key=admission_order):
   if time.time()-intake_started>150:state('INTAKE checkpoint, transfer fresh jobs before next cycle');break
   if key in seen and key not in recheck:continue
   duplicate=None
   if dry_copy(n,side):seen.add(key);recheck.discard(key);state('DROP same-side dry copy n=%d side=%.12f %s'%(n,side,p));continue
   # Already winning inputs keep their own run even when geometrically equal.
   if side>=bar[n]-1e-10*math.sqrt(n):
    for ref in pool.get(n,[]):
     if ref not in cache:cache[ref]=load(ref)
     q,qs=cache[ref]
     if len(q)==len(a) and abs(side-qs)<2e-8 and distance(a,side,q)<2e-8:duplicate=ref;break
   seen.add(key)
   if duplicate:recheck.discard(key);state('DROP geometry copy n=%d %s matches %s'%(n,p,duplicate));continue
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
    import qgate30
    qres=qgate30.lookup(p)
    if qres is None:
     # Round 28: at most two unwalked files of one lane dir and one n wait for the walker (stair-c writes many variants).
     _qq=set(qgate30.queue_path.read_text().splitlines()) if qgate30.queue_path.exists() else set()
     _same=[x for x in _qq if pathlib.Path(x).parent==p.parent and pathlib.Path(x).name.split('-')[0]==p.name.split('-')[0] and pathlib.Path(x).is_file() and qgate30.lookup(pathlib.Path(x)) is None]
     if len(_same)>=2 and str(p) not in _qq:recheck.add(key);seen.discard(key);continue
     qgate30.enqueue(p);recheck.add(key);seen.discard(key)
     if 'qwalk-wait:'+key not in seen:state('DEFER quench_walk pending (walker queue) '+str(p));seen.add('qwalk-wait:'+key)
     continue
    if not qres.get('clean'):
     if 'qwalk-no:'+key not in seen:state('DEFER quench_walk '+str(p)+' '+' | '.join(h[:120] for h in qres.get('hits',[])[:2]));seen.add('qwalk-no:'+key)
     recheck.add(key);continue
    if hashlib.sha256(p.read_bytes()).hexdigest()!=key.removeprefix('file:'):
     seen.discard(key);state('DEFER source changed during ancestry walk '+str(p));continue
    input_proof=W/'intake'/(tag+'-ancestry.json');atom(input_proof,dict(admitted=True,snapshot=str(dst),sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),ancestry=ancestry))
    source+='; verified input ancestry '+str(input_proof)
   proof=W/'intake'/(tag+'.json');atom(proof,dict(origin=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source=source,licence=lic))
   source+='; immutable intake '+str(proof)
   priority=60 if isold else 0 if side<bar[n]-1e-10*math.sqrt(n) else 1 if lane in ['forensics','k123','rebuild','gap'] or lane.startswith('reopen') else 2 if lane in ['modules','corners','readers','family'] else 3
   if gap>(.005 if lane in ['forensics','k123'] else .001):priority+=3
   # Round 28: a rectangle within 1e-8 of the bar is the held layout recomposed; 9 such kicks moved nothing.
   # Fresh stair-c and modules builds within 2e-5 above the bar go first (r27: 812 builds went 1.8e-4 below bar27).
   long_kick=((lane=='forensics' or lane.startswith('reopen-held')) and abs(gap)<1e-8) or (bool(re.search(r'/take-[a-z0-9-]+-r30/\d+\.csv$',str(p))) and gap<1e-8)
   if long_kick:priority=min(priority,1)
   if lane in ['stair','modules'] and 0<=gap<2e-5 and not isold:priority=1
   # Round 26: invent near files come out of the same lkick tool; 8 kicks of them (562 tries) moved nothing.
   if 1<=priority<50 and not long_kick and not isold:priority=1 if (lane in ('forensics','k123') and gap<1e-4) else 2 if (lane in ('forensics','k123') and gap<2e-3) else 6 if gap>2e-3 else 4
   if hashlib.sha256(p.read_bytes()).hexdigest() in withdrawn_shas():state('DROP withdrawn by its lane (sha256 in a WITHDRAW handoff line) '+str(p));continue
   if lane=='invent':priority=max(priority,50)
   if str(p) in backlog_claims():priority=max(priority,50)
   # Round 26: one lane writes many variants of one n; keep two pending at normal priority, the rest after the fresh work.
   if priority>=2 and not isold:
    pend=[q for q in W.glob('jobs/0[0-4]*-'+lane+'-'+str(n)+'-*.json') if not (R/'locks'/q.name).exists()]
    if len(pend)>=2:priority=50
   job=dict(tag=tag,n=n,start='starts/'+dst.name,seed=1125,remaining=1 if long_kick else 2 if gap<.001 else 1,seconds=(600 if lane.startswith('reopen-held') else 900) if long_kick else 180,miss=0,priority=priority,source=source,licence=lic,force_quench=side<bar[n]-1e-10*math.sqrt(n) or bool(re.search(r'/take-[a-z0-9-]+-r30/\d+\.csv$',str(p))))
   if input_proof:job['input_ancestry_proof']=str(input_proof)
   if long_kick:job['tool']='midm'
   # Round 28 A/B: kicks of quenched layouts were dry at sigma 0.003-0.02; half of the first passes use sigma 0.01-0.04.
   # 02:16Z: wide moved 4 of 7 runs (max 2.3e-3, the 697 row), default 14 of 51: wide for three in four, default kept as control.
   if int(hashlib.sha256(tag.encode()).hexdigest(),16)%4!=0:job.update(extra=['--sigs','0.01,0.02,0.04'],ab='wide')
   if long_kick and re.search(r'/take-[a-z0-9-]+-r30/\d+\.csv$',str(p)):
    priority=0;job['priority']=0
    if str(p) in backlog_claims():priority=50;job['priority']=50
    for _q in W.glob('jobs/000-*-'+str(n)+'-*.json'):
     if _q.name.startswith('000-00-') or (R/'locks'/_q.name).exists():continue
     try:_jq=json.load(open(_q))
     except ValueError:continue
     if _jq.get('tool')=='midm' and _jq.get('n')==n and load(W/_jq['start'])[1]<=side+1e-12:priority=50;job['priority']=50;break
   jp=W/'jobs'/('%03d-%s-1125.json'%(priority,tag));atom(jp,job)
   if job.get('tool')=='midm' and job['priority']==0:hand('claims 900 s midm_scan lkick,kick kick n=%d (seed 1125, boxE, job %s), start %s (byte snapshot %s, sha256 %s)'%(n,jp.name,p,dst,key.removeprefix('file:')))
   # Batch input transfers after intake.
   pool.setdefault(n,set()).add(dst);state('QUEUE '+tag+' from '+str(p)+' sidegap=%+.9g'%gap+'; command worker30.py invent_rest lkick180s; log runs/'+tag+'-s1125; deadline17:45UTC')
 if intake and time.time()<int((W/'search-deadline').read_text()):
  import pickle
  for line in (B/'handoff-r30.log').read_text().splitlines():
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
    rs(dd,remote+'designs/');atom(W/'jobs'/('001-'+tag+'.json'),dict(kind='design',f=.69,tag=tag));state('QUEUE new zones '+str(zp)+' as '+tag+'; log designs/'+tag+'; deadline17:45UTC')
 auditstamp=W/'last-audit'
 if False:
  with open(W/'audit.log','a') as out:subprocess.run([PY,str(W/'audit25.py')],stdout=out,stderr=subprocess.STDOUT,check=True)
  auditstamp.write_text(str(time.time()))
 rs(str(W/'starts')+'/',remote+'starts/');rs(str(W/'jobs')+'/',remote+'jobs/');subprocess.run(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python -I $SCRATCH/squares-twoshort/prioritize30.py'],check=True,timeout=30);atom(seenfile,sorted(seen));atom(recheck_path,sorted(recheck));
 if 'rtimes' in locals():atom(W/'recheck-times.json',rtimes)
 print(time.strftime('%FT%TZ',time.gmtime()),'done',len(list(R.glob('done/*.json'))),'jobs',len(list(R.glob('jobs/*.json'))),flush=True)
if __name__=='__main__':
 if '--loop' in sys.argv:
  while time.time()<int((W/'deadline').read_text())+300 and not (W/'STOP-COLLECT').exists():
   try:subprocess.run([PY,__file__,'--once'],check=True)
   except Exception as e:state('COLLECT ERROR '+repr(e));print(repr(e),flush=True)
   time.sleep(40)
 else:
  once('--no-intake' not in sys.argv)
  sys.stdout.flush();sys.stderr.flush();os._exit(0)
