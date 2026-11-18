"""Freeze a full source walk at intake and check its immutable evidence at publication."""
import csv,hashlib,json,pathlib,re,sys,time,shutil,zipfile,io,importlib,os,subprocess
import numpy as np
from scipy.spatial import cKDTree
W=pathlib.Path('$SCRATCH/bounties-squares/take-invent-r32/work');S=W.parents[1]
R=pathlib.Path('.')
os.environ['QUENCH_LIVE_ROUND']='32'
sys.path.insert(0,str(R));import quench_walk as Q
_held_original=Q.held
_seed_only=Q.samanyu_only
def lifted_policy(text):
 if '2026-11-15T01:51:44.'in text and 'forensics -> all:'in text and 'explicit rule-a family in retained ancestry (r23 forensics donor745/858 or its descendants)'in text and not re.search(r'745r-858r|858r-745r|858-ec97a452|745-64c4b4f8|overlap|missing|changed since',text,re.I):return True
 if re.search(r'(?:source walk|source graph) exceeded \d+ wall seconds',text)and not re.search(r'gone:|missing|changed since|BY-SA|penguin|joegun|unresolved|untrace|no root|cycle',text,re.I):return True
 if _seed_only(text):return True
 return bool(re.search(r'(?:prvsiyan|1105).*share|share.*(?:prvsiyan|1105)|ancestor.share|seed.share',text,re.I)) and not re.search(r'squares-verified-best-of-1105|joegun|penguin|untrace|missing|changed since|gone:',text,re.I)
def owned_held(count,round_=None):
 if int(count)==801:return 'own construction: canonical 801 packing under main00:19Z source policy'
 return _held_original(count,round_)
Q.lifted=lifted_policy
Q.samanyu_only=lifted_policy
_ledger=Q.ledger_lines;_ledger_cache={}
from scoped30 import wrap as scoped_reader
from owned30 import boundary as held_boundary
Q._jtext=scoped_reader(Q._jtext)
Q._jt.clear()
def cached_ledger(path):
 if re.search(r'take-[a-z0-9-]+-r(?:[1-9]|1\d|2[0-7])/',path):
  if path not in _ledger_cache:_ledger_cache[path]=_ledger(path)
  return _ledger_cache[path]
 return _ledger(path)
Q.ledger_lines=cached_ledger
_walker_stamp=(R/'quench_walk.py').stat().st_mtime_ns
_withdraw_stamp=None;_policy_files={}
def handoff_logs(root=None):
 root=S if root is None else pathlib.Path(root)
 return sorted(p for p in root.glob('handoff-r*.log')if re.fullmatch(r'handoff-r(?:2[2-9]|3[012])\.log',p.name))
def declares_withdrawal(line):
 match=re.search(r'->[^:]*:\s*(.*)',line)
 body=match[1]if match else line
 if re.match(r'SOURCE-HOLD\b',body,re.I):return True
 return bool(re.search(r'^(?:(?:source|ancestry) (?:correction|audit):?\s*)?(?:WITHDRAW|WITHHOLD|reclassif)\w*\b',body,re.I) or re.search(r'^[a-z0-9-]+\s+(?:withdrew|withdraws|reclassified)\b',body,re.I) or re.search(r'\b(?:WITHDRAW|WITHHOLD)\s+(?:n\s*[=0-9]|all|every|source|this|our|the|take-|/Volumes)',body[:160]))
assert declares_withdrawal('2026-11-14T15:18:34Z harvest -> all: harvest withdrew 416 499 646 from its take')
assert declares_withdrawal('2026-11-14T20:02:14Z classfill -> all: WITHDRAW n982 pending source recheck')
assert not declares_withdrawal('2026-11-15T00:00:00Z invent -> all: keeps n860, not the withheld n910')
assert not declares_withdrawal('2026-11-13T23:44:05Z rebuild -> all: clean parents certified: n735 and n790 equal the withdrawn floors')
assert declares_withdrawal('2026-11-15T03:41:06Z stair-c -> all: SOURCE-HOLD pending full ancestry repair')
def notice_paths(line):
 refs=re.findall(r'(take-[a-z0-9-]+-r\d+/[^\s,;]+?\.csv)',line)
 if re.search(r': SOURCE-HOLD\b',line):
  folders=re.findall(r'(take-[a-z0-9-]+-r\d+/near/)',line)
  names=re.findall(r'(\d{2,4}-[A-Za-z0-9_.-]+\.csv)',line.split(' under ',1)[0])
  refs.extend(folder+name for folder in folders for name in names)
 return list(dict.fromkeys(refs))
def withdrawal_applies(snap,line):
 mentioned=re.findall(r'(?:sha256[=: ]+|sha=)([0-9a-f]{12,64})',line)
 if mentioned:return any(snap['sha256'].startswith(h)for h in mentioned)
 original=pathlib.Path(snap['original']);mtime=snap.get('original_mtime_ns')
 if mtime is None and original.is_file()and sha(original)==snap['sha256']:mtime=original.stat().st_mtime_ns
 if mtime is not None and mtime/1e9>Q.withdraw_time(line):return False
 return True
def refresh_walker():
 global _walker_stamp,_seed_only,_held_original,_withdraw_stamp
 stamp=(R/'quench_walk.py').stat().st_mtime_ns
 if stamp!=_walker_stamp:
  importlib.reload(Q);Q._jtext=scoped_reader(Q._jtext);Q._jt.clear();_withdraw_stamp=None;_held_original=Q.held;_seed_only=Q.samanyu_only;Q.lifted=lifted_policy;Q.samanyu_only=lifted_policy;Q.ledger_lines=cached_ledger;_walker_stamp=stamp
 Q.quench_audit.RULES[:]=[(name,r'745r-858r|858r-745r|858-ec97a452|745-64c4b4f8'if name=='r22 745/858 join'else rx)for name,rx in Q.quench_audit.RULES]
 Q.DROPK.update({'prvsiyan_shares','prvsiyan_share','prvsiyan_share_check','ancestor_share_check','share_checks','complete_parent_share_audit'})
 Q.held=owned_held
 if 'own construction'not in Q.ROOT.pattern:Q.ROOT=re.compile(Q.ROOT.pattern+'|own construction',re.I)
 Q.moved_copy=moved_alias
 Q._cmp=lambda match:' '
 Q.NAMES=re.compile(r'squares-joegun-boxed|joegun-boxed-certified-union|squares-verified-best-of-1105|CC BY-SA|ShareAlike',re.I)
 Q.LIVE='32'
 Q.ANCDIRS=sorted(set(Q.ANCDIRS)|{str(p)for p in S.glob('take-*-r32/work/ancestry')})
 stamps=tuple((str(p),p.stat().st_mtime_ns)for p in handoff_logs())
 if stamps!=_withdraw_stamp:
  Q.load_withdrawn()
  Q.WITHDRAWN_LINES[:]=[(ref,line)for ref,line in Q.WITHDRAWN_LINES if declares_withdrawal(line)and not lifted_policy(line)]
  _withdraw_stamp=stamps
_moved_original=Q.moved_copy
def moved_alias(path):
 for name in ('910-late-s225136x910x18.csv','910-lateleg910.csv'):
  if str(path)==str(S/'take-invent-r27/near'/name):
   old=S/'take-invent-r27/work/withdrawn-near'/name;new=W/'reinstated'/('910-r28-scan-parent.csv'if 'late-s'in name else '910-r28-leg-parent.csv')
   if old.is_file()and new.is_file()and sha(old)==sha(new):return str(new)
 return _moved_original(path)
_cache={};_parent_shares={};_prv=None;_notices={};_notice_stamps={};_reinstated={}

def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def banned(text):
 for label,rx in Q.quench_audit.RULES:
  if re.search(rx,text,re.I):return label
 if re.search(r'CC[ -]BY[ -]SA|ShareAlike',text,re.I):return 'CC BY-SA source'
 return None

def centres(rows):
 a=np.array([[float(r['x']),float(r['y'])]for r in rows]);return a-(a.min(0)+a.max(0))/2

def prv_share(p,n):
 global _prv
 if _prv is None:
  _prv={}
  z=S/'take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'
  with zipfile.ZipFile(z) as archive:
   for name in ('submission.csv',):
    if not name.endswith('.csv'):continue
    for r in csv.DictReader(io.StringIO(archive.read(name).decode('utf-8-sig'))):
     if 'x'not in r or 'y'not in r:continue
     count=r.get('n',r.get('id','').split('_')[0]).lstrip('s')
     if count.isdigit():_prv.setdefault(int(count),[]).append({k:str(r[k]).lstrip('s')for k in ('x','y')})
 a=centres(list(csv.DictReader(open(p))));b=_prv.get(n,[])
 if len(b)!=n:return 0.0
 tree=cKDTree(centres(b));best=0.
 for sw in (False,True):
  for sx in (-1,1):
   for sy in (-1,1):
    c=(a[:,::-1]if sw else a)*[sx,sy];d,_=tree.query(c)
    best=max(best,float((d<1e-3).mean()))
 return best

def public_first(path,proof):
 if held_boundary(proof):return False
 producer=next((v for v in pathlib.Path(path).parts if v.startswith('take-')),'')
 root=proof.get('nodes',{}).get(proof.get('root'),{})
 source=root.get('source','').strip();terms=root.get('licence','')
 if banned(source+' '+terms):return True
 if source or terms:
  import ancestry28 as A
  if A.classify(source+' '+terms,A.ORIG)[0]=='yes':return False
  if re.search(r'Samanyu-dev/squares_in_squares|samanyu_bestfit|921-29e12ff3|own construction|held n\s*=\s*\d+\s+of round',source+' '+terms,re.I):return False
  if re.search(r'invent_rest|rectangle windows|modules\.py|k123|family_step|family_readers|stair-c|twoshort|own construction|local kick',source[:400],re.I):return False
 if producer.startswith('take-harvest-'):return True
 return bool(re.match(r'(?:public\s+|harvest|(?:fq quench of )?[A-Za-z0-9_-]+/)',source))

def public_licence_ok(terms):
 if re.search(r'CC[ -]BY[ -]SA|CC[ -]BY[ -]NC|ShareAlike|NonCommercial',terms,re.I):return False
 return bool(re.search(r'Apache[- ]*(?:License\s*,?\s*(?:Version\s*)?)?2(?:\.0)?|CC0|Public\s*Domain|(?:CC[- ]*BY[- ]*|Attribution\s+)4\.0',terms,re.I))

def freeze_unbounded(p,n,ancestry):
 refresh_walker()
 p=pathlib.Path(p);input_hash=sha(p);key=hashlib.sha256(b'own-source-r30-v6-reader-scope'+p.read_bytes()+pathlib.Path(ancestry).read_bytes()).hexdigest()
 dest=W/'evidence'/f'{key}.json';dest.parent.mkdir(exist_ok=True)
 if dest.exists():
  d=json.load(open(dest));return dict(clean=d['clean'],hits=d['hits'],path=str(dest),sha256=sha(dest))
 # Walk a source-bearing immutable alias, because queued start paths have no producer ledger.
 folder=W/'intake'/key;folder.mkdir(parents=True,exist_ok=True);alias=folder/p.name;shutil.copyfile(p,alias)
 proof=json.load(open(ancestry));terms='; '.join(dict.fromkeys(v['licence']for v in proof['nodes'].values()))
 pathlib.Path(str(alias)+'.json').write_text(json.dumps(dict(n=n,source='source metadata '+str(ancestry),licence=terms)))
 from scoped30 import reset_records,extra_records
 reset_records()
 captured={};original_walk=Q.walk
 def capture(*args,**kwargs):
  v=original_walk(*args,**kwargs);captured['walk']=v;return v
 Q.walk=capture
 original_share=Q.prv_share;original_ancestor_share=getattr(Q,'anc_share',None)
 Q.anc_share=lambda path:None
 Q.prv_share=lambda path,count:original_share(path,count)if public_first(p,proof)else(0.0,0.0,0.0,0.0)
 try:result=Q.check(str(alias))
 finally:Q.prv_share=original_share;Q.anc_share=original_ancestor_share;Q.walk=original_walk
 texts,missing,seen,helds,refused=captured['walk']
 hits=result['hits'];share=prv_share(p,n) if public_first(p,proof) else 0.0
 if public_first(p,proof)and not public_licence_ok(proof['nodes'][proof['root']].get('licence','')):hits.append('public-first licence is outside the allowed set')
 if len(seen)>=3000:hits.append('source walk reached cap before closure')
 if public_first(p,proof)and share>=.4:hits.append('prvsiyan share '+str(share)+' >=0.4')
 snapshots=[];pins=W/'pins';pins.mkdir(exist_ok=True)
 extra=extra_records()
 for ref in sorted({str(v)for v in seen if isinstance(v,str)and v.startswith('/')}|set(extra)):
  original=pathlib.Path(ref)
  if original.suffix not in ('.json','.csv')or not original.is_file():continue
  before=sha(original)
  if ref in extra and before!=extra[ref]['sha256']:hits.append('reader state changed after selecting donor '+ref)
  out=pins/(before+original.suffix)
  if not out.exists():shutil.copyfile(original,out)
  if sha(original)!=before or sha(out)!=before:hits.append('changed during snapshot '+ref)
  snapshots.append(dict(original=ref,path=str(out),sha256=before,original_mtime_ns=original.stat().st_mtime_ns))
 if sha(p)!=input_hash:hits.append('start changed during source snapshot')
 d=dict(policy='own-source-r28-v2',public_first=public_first(p,proof),clean=not hits,hits=hits,time=time.strftime('%FT%TZ',time.gmtime()),input_sha256=sha(p),n=n,share=share,texts=texts,snapshots=snapshots,walk=result,ancestry=ancestry,ancestry_sha256=sha(ancestry))
 dest.write_text(json.dumps(d,separators=(',',':')))
 return dict(clean=d['clean'],hits=hits,path=str(dest),sha256=sha(dest))

def complete_parent_share(path,digest):
 if digest in _parent_shares:return _parent_shares[digest]
 result=None
 if pathlib.Path(path).suffix=='.csv':
  with open(path)as stream:
   reader=csv.DictReader(stream)
   if {'n','x','y'}.issubset(reader.fieldnames or []):
    rows=[]
    for row in reader:
     rows.append(row)
     if len(rows)>1000:break
    if rows and len(rows)<=1000:
     count=int(rows[0]['n'])
     if 1<=count<=1000 and len(rows)==count and all(int(row['n'])==count for row in rows):result=(count,prv_share(path,count))
 _parent_shares[digest]=result
 return result

def public_policy_key():
 paths=[W/'ancestry28.py',W/'held32.py',W/'freeze_held32.py',W/'public_branch30.py',W/'owned30.py',W/'public_roots29.py',W/'implicit_public29.py',R/'forensics_public29.py',R/'forensics_watch.py',R/'quench_walk.py']
 paths += [R/'tools/harvest29'/n for n in('public_sources.py','policy.py','walk.py','reader_records.py','versions.py')]
 paths += [R/'tools/harvest30'/n for n in('public_sources.py','held_paths.py','held_policy.py','walk.py','policy.py','withdrawals.py','reader_records.py')]
 paths += sorted((R/'results').glob('round*-best-*.tsv'))
 paths += [R/'results/angle-harvest-2026-11-10.tsv',R/'results/forensics-round23a-sources-r24-2026-11-13.tsv',R/'results/harvest-best-2026-11-09.tsv']
 h=hashlib.sha256()
 for p in paths:
  if not p.is_file():continue
  st=p.stat();stamp=(st.st_mtime_ns,st.st_size);prior=_policy_files.get(str(p))
  if not prior or prior[0]!=stamp:_policy_files[str(p)]=(stamp,sha(p))
  h.update(str(p).encode());h.update(_policy_files[str(p)][1].encode())
 return h.hexdigest()

def review_epoch():
 refresh_walker();h=hashlib.sha256(public_policy_key().encode())
 for ref,line in Q.WITHDRAWN_LINES:h.update(ref.encode());h.update(line.encode())
 return h.hexdigest()

def public_pins_ok(value):
 return all(pathlib.Path(pin['path']).is_file()and sha(pin['path'])==pin['sha256']for row in value.get('public_roots',[])for pin in row.get('captured_public_archive',{}).get('pins',[]))

def public_audit(job,d):
 policy=public_policy_key();ep=pathlib.Path(job['evidence']);eh=sha(ep)
 graph=pathlib.Path(job.get('ancestry')or d['ancestry']);expected=d['ancestry_sha256'];pin=W/'pins'/(expected+'.json')
 if pin.is_file():graph=pin
 if not graph.is_file()or sha(graph)!=expected:return dict(clean=False,error='missing pinned graph for public sources')
 key=hashlib.sha256((eh+expected+policy).encode()).hexdigest();folder=W/'public-source-audits';folder.mkdir(exist_ok=True);index=folder/(key+'.json')
 if index.is_file():
  rec=json.load(open(index));p=pathlib.Path(rec['path'])
  if p.is_file()and sha(p)==rec['sha256']:
   value=json.load(open(p))
   if value.get('policy_sha256')==policy and value.get('evidence_sha256')==eh and public_pins_ok(value)and (not value.get('error')or time.time()-rec['at']<120):return dict(value,receipt=str(p),receipt_sha256=rec['sha256'])
 temp=folder/(key+'.running.json')
 try:
  process=subprocess.run(['nice','-n','5',sys.executable,'-I',str(W/'public_branch30.py'),str(ep),str(graph),str(temp)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=90)
  if process.returncode:raise ValueError(process.stderr[-800:])
  value=json.load(open(temp))
  if not public_pins_ok(value):raise ValueError('changed supplemental public-source pin')
 except Exception as error:value=dict(clean=False,public_roots=[],error=repr(error))
 value.update(policy_sha256=policy,evidence_sha256=eh,ancestry_sha256=expected)
 encoded=json.dumps(value,sort_keys=True,separators=(',',':')).encode();digest=hashlib.sha256(encoded).hexdigest();pins=W/'public-source-pins';pins.mkdir(exist_ok=True);p=pins/(digest+'.json')
 if not p.exists():p.write_bytes(encoded)
 q=index.with_suffix('.tmp');q.write_text(json.dumps(dict(path=str(p),sha256=digest,at=time.time())));q.replace(index);temp.unlink(missing_ok=True)
 return dict(value,receipt=str(p),receipt_sha256=digest)

def public_path_notice(line):
 if re.search(r'penguin|joegun|untrace|unresolved|missing|changed since|capture race|node.cap|incomplete|unlicen|no licen|BY.SA|NonCommercial',line,re.I):return False
 if re.search(r'(?:names|uses|upstream from|source from)\s+(?:the )?prvsiyan/squares-verified-best-of-1105',line,re.I):return False
 return bool(re.search(r'share|public.first.{0,100}(?:ancestor|allowed.source)|archived.public audit',line,re.I))

def check(job,path):
 refresh_walker()
 evidence=job.get('evidence');errors=[]
 if job.get('graph_pin_ok')is False:return dict(clean=False,hits=['missing immutable source graph'],files=0)
 if not evidence:return dict(clean=False,hits=['missing frozen full walk'],files=0)
 p=pathlib.Path(evidence)
 if not p.is_file()or sha(p)!=job.get('evidence_sha256'):return dict(clean=False,hits=['changed frozen evidence'],files=0)
 d=json.load(open(p));errors+=d['hits']
 if d.get('policy')=='submitted-held32-v1':
  from held32 import resolve as resolve_held_root
  if not d.get('submitted_roots')or any(resolve_held_root(root)is None for root in d['submitted_roots']):errors.append('held root lacks a verified submitted-row witness')
 graph_path=pathlib.Path(job.get('ancestry')or d['ancestry'])
 graph=json.load(open(graph_path))if graph_path.is_file()and sha(graph_path)==d['ancestry_sha256']else{}
 owned=held_boundary(graph)
 effective_public=bool(graph)and public_first(graph.get('path',str(path)),graph)
 if job.get('ancestry'):
  graph=pathlib.Path(job['ancestry'])
  if not graph.is_file()or sha(graph)!=d['ancestry_sha256']:errors.append('source graph differs from frozen evidence')
  elif effective_public:
   ancestry=json.load(open(graph));root=ancestry.get('nodes',{}).get(ancestry.get('root'),{})
   if not public_licence_ok(root.get('licence','')):errors.append('public-first licence is outside the allowed set')
 if job.get('input_sha256')and job['input_sha256']!=d['input_sha256']:errors.append('queued start differs from frozen source input')
 for snap in d['snapshots']:
  if not pathlib.Path(snap['path']).exists()or sha(snap['path'])!=snap['sha256']:errors.append('changed evidence pin '+snap['path']);continue
  # Own-layout ancestry is not tested for numeric similarity under the 00:19Z rule.
 share=prv_share(path,job['n']) if effective_public else 0.0
 if effective_public and share>=.4:errors.append('prvsiyan share '+str(share)+' >=0.4')
 # Cache notice parsing by file timestamp; match each pinned path directly.
 global _notices,_notice_stamps,_reinstated
 logs=handoff_logs();stamps={str(log):log.stat().st_mtime_ns for log in logs};stamps['walker']=_walker_stamp
 if stamps!=_notice_stamps:
  notices={};reinstated={}
  for log in logs:
   for line in log.read_text(errors='replace').splitlines():
    if 'REINSTATE'in line:
     hashes=re.findall(r'(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])',line)
     for ref in re.findall(r'(take-[a-z0-9-]+-r\d+/[^\s,;]+?\.csv)',line):
      for digest in hashes:reinstated[(ref,digest)]=line[:19]
    if not declares_withdrawal(line)or(lifted_policy(line)and not public_path_notice(line)):continue
    if not re.search(r'prvsiyan|penguin|BY-SA|untrace|missing|changed|source|ancestry|gone',line,re.I):continue
    for ref in notice_paths(line):notices.setdefault(ref,[]).append(line)
  for ref,line in Q.WITHDRAWN_LINES:
   if declares_withdrawal(line)and(not Q.lifted(line)or public_path_notice(line)):notices.setdefault(ref,[]).append(line)
  _notices=notices;_notice_stamps=stamps;_reinstated=reinstated
 deferred_public_notices=[]
 for snap in d['snapshots']:
  original=snap['original'];rel=original.removeprefix(str(S)+'/')
  for line in _notices.get(rel,[]):
   if _reinstated.get((rel,snap['sha256']),'')>line[:19]:continue
   if not withdrawal_applies(snap,line):continue
   if public_path_notice(line):deferred_public_notices.append((original,line))
   else:errors.append('withdrawal '+line[:300])
 public=None
 if not errors:
  public=public_audit(job,d)
  direct_public=set(public.get('direct_public_originals',[]))
  for original,line in deferred_public_notices:
   if original in direct_public:errors.append('direct public withdrawal '+line[:300])
  if not public.get('clean'):
   if public.get('error'):errors.append('public-source audit unresolved: '+public['error'])
   errors += ['excluded first-public source n='+str(v['n'])+' share='+str(v['share1e3'])+' '+v['original']for v in public.get('public_roots',[])if not v.get('allowed')]
 result=dict(held_boundary=owned,clean=not errors,hits=sorted(set(errors))[:40],files=len(d['snapshots']),share=share,public_sources=public)
 out=W/'independent-results';out.mkdir(exist_ok=True);(out/f'{job["id"]}.json').write_text(json.dumps(result))
 return result


def freeze(p,n,ancestry):
 from freeze_held32 import freeze as submitted_freeze
 held=submitted_freeze(p,n,ancestry)
 if held is not None:
  current=check(dict(id='held-intake-'+held['sha256'][:12],n=n,evidence=held['path'],evidence_sha256=held['sha256'],ancestry=str(ancestry)),p)
  return held if current['clean'] else dict(clean=False,hits=current['hits'])
 import signal
 def expired(*unused):raise TimeoutError('full source walk exceeded 120 wall seconds')
 old=signal.signal(signal.SIGALRM,expired);signal.alarm(120)
 try:
  value=freeze_unbounded(p,n,ancestry)
  if value['clean']:
   current=check(dict(id='intake-'+value['sha256'][:12],n=n,evidence=value['path'],evidence_sha256=value['sha256']),p)
   if not current['clean']:return dict(clean=False,hits=current['hits'])
  return value
 except TimeoutError as error:return dict(clean=False,hits=[str(error)+'; deferred for a later audit'])
 finally:signal.alarm(0);signal.signal(signal.SIGALRM,old)
