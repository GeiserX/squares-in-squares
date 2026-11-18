"""Freeze a full source walk at intake and check its immutable evidence at publication."""
import csv,hashlib,json,pathlib,re,sys,time,shutil,zipfile,io,importlib
import numpy as np
from scipy.spatial import cKDTree
W=pathlib.Path('$SCRATCH/bounties-squares/take-invent-r27/work');S=W.parents[1]
R=pathlib.Path('.')
sys.path.insert(0,str(R));import quench_walk as Q
Q.lifted=Q.samanyu_only
_ledger=Q.ledger_lines;_ledger_cache={}
def cached_ledger(path):
 if re.search(r'take-[a-z0-9-]+-r(?:[1-9]|1\d|2[0-6])/',path):
  if path not in _ledger_cache:_ledger_cache[path]=_ledger(path)
  return _ledger_cache[path]
 return _ledger(path)
Q.ledger_lines=cached_ledger
_walker_stamp=(R/'quench_walk.py').stat().st_mtime_ns
def declares_withdrawal(line):
 match=re.search(r'->[^:]*:\s*(.*)',line)
 body=match[1]if match else line
 return bool(re.search(r'^(?:(?:source|ancestry) (?:correction|audit):?\s*)?(?:WITHDRAW|WITHHOLD|reclassif)\w*\b',body,re.I) or re.search(r'^[a-z0-9-]+\s+(?:withdrew|withdraws|reclassified)\b',body,re.I) or re.search(r'\b(?:WITHDRAW|WITHHOLD)\s+(?:n\s*[=0-9]|all|every|source|this|our|the|take-|/Volumes)',body[:160]))
assert declares_withdrawal('2026-11-14T15:18:34Z harvest -> all: harvest withdrew 416 499 646 from its take')
assert declares_withdrawal('2026-11-14T20:02:14Z classfill -> all: WITHDRAW n982 pending source recheck')
assert not declares_withdrawal('2026-11-13T23:44:05Z rebuild -> all: clean parents certified: n735 and n790 equal the withdrawn floors')
def refresh_walker():
 global _walker_stamp
 stamp=(R/'quench_walk.py').stat().st_mtime_ns
 if stamp!=_walker_stamp:
  importlib.reload(Q);Q.lifted=Q.samanyu_only;Q.ledger_lines=cached_ledger;_walker_stamp=stamp
 Q.load_withdrawn()
 Q.WITHDRAWN_LINES[:]=[(ref,line)for ref,line in Q.WITHDRAWN_LINES if declares_withdrawal(line)]
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

def freeze_unbounded(p,n,ancestry):
 refresh_walker()
 p=pathlib.Path(p);input_hash=sha(p);key=hashlib.sha256(b'shared-r27-v3'+p.read_bytes()+pathlib.Path(ancestry).read_bytes()).hexdigest()
 dest=W/'evidence'/f'{key}.json';dest.parent.mkdir(exist_ok=True)
 if dest.exists():
  d=json.load(open(dest));return dict(clean=d['clean'],hits=d['hits'],path=str(dest),sha256=sha(dest))
 # Walk a source-bearing immutable alias, because queued start paths have no producer ledger.
 folder=W/'intake'/key;folder.mkdir(parents=True,exist_ok=True);alias=folder/p.name;shutil.copyfile(p,alias)
 proof=json.load(open(ancestry));terms='; '.join(dict.fromkeys(v['licence']for v in proof['nodes'].values()))
 pathlib.Path(str(alias)+'.json').write_text(json.dumps(dict(n=n,source='source metadata '+str(ancestry),licence=terms)))
 captured={};original_walk=Q.walk
 def capture(*args,**kwargs):
  v=original_walk(*args,**kwargs);captured['walk']=v;return v
 Q.walk=capture
 original_share=Q.prv_share
 Q.prv_share=lambda path,count:(0.0,prv_share(path,count),0.0)
 try:result=Q.check(str(alias))
 finally:Q.prv_share=original_share;Q.walk=original_walk
 texts,missing,seen,helds,refused=captured['walk']
 hits=result['hits'];share=prv_share(p,n)
 if len(seen)>=3000:hits.append('source walk reached cap before closure')
 if share>=.4:hits.append('prvsiyan share '+str(share)+' >=0.4')
 snapshots=[];pins=W/'pins';pins.mkdir(exist_ok=True)
 for ref in sorted(str(v)for v in seen if isinstance(v,str)and v.startswith('/')):
  original=pathlib.Path(ref)
  if original.suffix not in ('.json','.csv')or not original.is_file():continue
  before=sha(original);out=pins/(before+original.suffix)
  if not out.exists():shutil.copyfile(original,out)
  if sha(original)!=before or sha(out)!=before:hits.append('changed during snapshot '+ref)
  snapshots.append(dict(original=ref,path=str(out),sha256=before))
 if sha(p)!=input_hash:hits.append('start changed during source snapshot')
 d=dict(clean=not hits,hits=hits,time=time.strftime('%FT%TZ',time.gmtime()),input_sha256=sha(p),n=n,share=share,texts=texts,snapshots=snapshots,walk=result,ancestry=ancestry,ancestry_sha256=sha(ancestry))
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

def check(job,path):
 refresh_walker()
 evidence=job.get('evidence');errors=[]
 if not evidence:return dict(clean=False,hits=['missing frozen full walk'],files=0)
 p=pathlib.Path(evidence)
 if not p.is_file()or sha(p)!=job.get('evidence_sha256'):return dict(clean=False,hits=['changed frozen evidence'],files=0)
 d=json.load(open(p));errors+=d['hits']
 if job.get('input_sha256')and job['input_sha256']!=d['input_sha256']:errors.append('queued start differs from frozen source input')
 for snap in d['snapshots']:
  if not pathlib.Path(snap['path']).exists()or sha(snap['path'])!=snap['sha256']:errors.append('changed evidence pin '+snap['path']);continue
  ancestor=complete_parent_share(snap['path'],snap['sha256'])
  if ancestor and ancestor[1]>=.4:errors.append('excluded complete ancestor n='+str(ancestor[0])+' share='+str(ancestor[1])+' '+snap['original'])
 share=prv_share(path,job['n'])
 if share>=.4:errors.append('prvsiyan share '+str(share)+' >=0.4')
 # Cache notice parsing by file timestamp; match each pinned path directly.
 global _notices,_notice_stamps,_reinstated
 logs=list(S.glob('handoff-r2[2-7].log'));stamps={str(log):log.stat().st_mtime_ns for log in logs};stamps['walker']=_walker_stamp
 if stamps!=_notice_stamps:
  notices={};reinstated={}
  for log in logs:
   for line in log.read_text(errors='replace').splitlines():
    if 'REINSTATE'in line:
     hashes=re.findall(r'(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])',line)
     for ref in re.findall(r'(take-[a-z0-9-]+-r\d+/[^\s,;]+?\.csv)',line):
      for digest in hashes:reinstated[(ref,digest)]=line[:19]
    if not declares_withdrawal(line)or Q.lifted(line):continue
    if not re.search(r'prvsiyan|penguin|BY-SA|untrace|missing|changed|source|ancestry|gone',line,re.I):continue
    for ref in re.findall(r'(take-[a-z0-9-]+-r\d+/[^\s,;]+?\.csv)',line):notices.setdefault(ref,[]).append(line)
  for ref,line in Q.WITHDRAWN_LINES:
   if not Q.lifted(line)and declares_withdrawal(line):notices.setdefault(ref,[]).append(line)
  _notices=notices;_notice_stamps=stamps;_reinstated=reinstated
 for snap in d['snapshots']:
  original=snap['original'];rel=original.removeprefix(str(S)+'/')
  for line in _notices.get(rel,[]):
   if _reinstated.get((rel,snap['sha256']),'')>line[:19]:continue
   mentioned=re.findall(r'(?:sha256[=: ]+|sha=)([0-9a-f]{12,64})',line)
   if mentioned and not any(snap['sha256'].startswith(h)for h in mentioned):continue
   if not mentioned and pathlib.Path(original).is_file()and sha(original)!=snap['sha256']:continue
   errors.append('withdrawal '+line[:300])
 result=dict(clean=not errors,hits=sorted(set(errors))[:40],files=len(d['snapshots']),share=share)
 out=W/'independent-results';out.mkdir(exist_ok=True);(out/f'{job["id"]}.json').write_text(json.dumps(result))
 return result


def freeze(p,n,ancestry):
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
