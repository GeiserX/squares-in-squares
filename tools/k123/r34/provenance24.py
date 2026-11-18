import pathlib,csv,json,hashlib,sys,re,functools
import numpy as np
sys.dont_write_bytecode=True
csv.field_size_limit(20000000)
W=pathlib.Path(__file__).resolve().parent;S=W.parent.parent;R=pathlib.Path('.');sys.path.insert(0,str(W/'lane'))
import methods_lp as mlp
from geometry23 import key
@functools.lru_cache(None)
def tables():
 d={}
 for p in sorted((R/'results').glob('*.tsv')):
  if not re.match(r'(?:round\d+-best-|harvest-best-)',p.name):continue
  try:
   for row in csv.DictReader(open(p),delimiter='\t'):
    n=int(row['n']);score=float(row.get('score',row.get('new','nan')))
    if np.isfinite(score) and row.get('source'):d.setdefault(n,[]).append((score,str(p),row))
  except (ValueError,KeyError,csv.Error):pass
 return d
@functools.lru_cache(None)
def base():
 cache=W/'base-credit24.json'
 if cache.exists():return json.load(open(cache))
 P=mlp.load(str(S/'gather/round23-2026-11-13b.csv'));out={}
 for n,A in P.items():
  if n in (801,907):continue
  score=mlp.side(A)/np.sqrt(n)-1;hits=tables().get(n,[]);z=min(hits,key=lambda z:abs(z[0]-score)) if hits else None
  source=z[2]['source'] if z and abs(z[0]-score)<1e-8 else 'original clean seed; lanes/squares/README.md Outside data and results/harvest-best-2026-11-09.tsv'
  licence=z[2].get('licence','source credited in README.md Outside data') if z and abs(z[0]-score)<1e-8 else 'source credited in README.md Outside data'
  out[key(n,A)]=dict(clean=True,n=n,origin='candidate round23',table=z[1] if z else '',source=source,licence=licence,sha256_geometry=key(n,A))
 # Earlier held inputs are accepted only when their per-n source has no banned ancestry.
 H=mlp.load(str(S/'gather/round21-2026-11-13a.csv'))
 for n,A in H.items():
  if n in [639,691,745,858,918,980,981,801,907]:continue
  k=key(n,A)
  if k in out:continue
  score=mlp.side(A)/np.sqrt(n)-1
  old=[z for z in tables().get(n,[]) if re.search(r'round(?:[1-9]|1\d|2[01])-',z[1]) or 'harvest-best-2026-11-09' in z[1]]
  z=min(old,key=lambda z:abs(z[0]-score)) if old else None
  if not z or abs(z[0]-score)>1e-8:continue
  text=json.dumps(z[2])
  if banned(text):continue
  out[k]=dict(clean=True,n=n,origin='held round21',table=z[1],source=z[2]['source'],licence=z[2].get('licence','own'),sha256_geometry=k)
 tmp=W/('base-credit24.'+str(__import__('os').getpid())+'.tmp');tmp.write_text(json.dumps(out));tmp.replace(cache)
 return out

@functools.lru_cache(None)
def withdrawals(mtime):
 paths=[]
 for line in (S/'handoff-r24.log').read_text().splitlines():
  if 'WITHDRAW' not in line:continue
  paths.extend(re.findall(r'($DATA/[^\s,;]+\.csv)',line))
  if 'forensics' in line and 'WITHDRAW n981' in line:paths.append(str(S/'take-forensics-r24/981.csv'))
 return paths

def has_forbidden_801(obj,depth=0):
 if depth>8:return False
 if isinstance(obj,dict):
  src=obj.get('source')
  if isinstance(src,list) and len(src)==2 and (str(src[1])=='801' or (str(src[1])=='907' and str(src[0]) in ('held','seed merged0'))):return True
  return any(has_forbidden_801(v,depth+1) for v in obj.values())
 if isinstance(obj,list):return any(has_forbidden_801(v,depth+1) for v in obj)
 if isinstance(obj,str) and obj.lstrip().startswith(('{','[')):
  try:return has_forbidden_801(json.loads(obj),depth+1)
  except ValueError:pass
 return False

def banned(text):
 try:
  if has_forbidden_801(json.loads(text)):return True
 except ValueError:pass
 log=S/'handoff-r24.log'
 if log.exists() and any(p in text for p in withdrawals(log.stat().st_mtime_ns)):return True
 if re.search(r'"source"\s*:\s*\[\s*"[^"\n]+"\s*,\s*801\s*\]',text):return True
 return bool(re.search(r'CC BY-SA|Attribution.ShareAlike|(?:held|round2[0-3]).{0,30}\b(?:801|907)\b|(?:n\s*[=:]\s*|donor\s+)801\b|penguin069/squares-joegun-boxed-certified-union|prvsiyan/squares-verified-best-of-1105|take-forensics-r(?:[1-9]|1\d|2[0-3])/(?:near/)?918|take-harvest-r22/(?:near/)?(?:639|691|745|858|918)\b|take-(?:invent|midm)-r23/(?:near/)?639\b|take-forensics-r23/(?:near/)?980\b',text))

def legacy_credit(n,A,origin=None):
 k=key(n,A)
 if origin and banned(str(origin)):return None
 c=base().get(k)
 if c and (not origin or origin=='held'):return c
 if not origin or origin=='held':return None
 p=pathlib.Path(origin)
 # Frozen top-level r23 rows count only if candidate changed their n.
 if '-r23/' in origin and '/near/' not in origin:
  moved={r['n'] for r in json.load(open(S/'gate/cand-round23-1113a/gate.json'))['moved']}
  if n not in moved:return None
 if '/near/' in origin or pathlib.Path(str(p)+'.json').exists() or p.with_suffix('.json').exists():
  records=[]
  for sidecar in [pathlib.Path(str(p)+'.json'),p.with_suffix('.json')]:
   if sidecar.exists():
    try:records.append((str(sidecar),json.load(open(sidecar))))
    except (ValueError,OSError):pass
  if not records and '-from' not in p.stem:
   m=re.search(r'from(\d+)-(r\d+h[0-9a-f]+)',p.stem)
   ledger=p.parent.parent/'work/sources-all.tsv'
   if m and ledger.exists():
    donor=m[1]+'-'+m[2]
    try:
     row=next(r for r in csv.DictReader(open(ledger),delimiter='\t') if r['donor']==donor)
     records.append((str(ledger),row))
    except (ValueError,KeyError,StopIteration):pass
  for evidence,j in records:
   text=json.dumps(j)
   if banned(text):continue
   if isinstance(j,dict) and j.get('modules'):
    source=' | '.join(z.get('source','') for z in j['modules']);licence=' | '.join(z.get('licence','own') for z in j['modules'])
   elif isinstance(j,dict) and j.get('parts'):
    parts=j['parts'];source=json.dumps(parts,separators=(',',':'));licence=' | '.join(z.get('licence','own') for z in parts.values() if isinstance(z,dict))
   else:
    source=j.get('source',j.get('source_record','')) if isinstance(j,dict) else ''
    licence=j.get('licence','source terms recorded in '+evidence) if isinstance(j,dict) else ''
   if source:
    return dict(clean=True,n=n,origin=origin,evidence=evidence,source=source,licence=licence,sha256_geometry=k)
  return None
 ledger=p.parent/'take.tsv'
 if not ledger.exists():return None
 try:row=next(r for r in csv.DictReader(open(ledger),delimiter='\t') if int(r['n'])==n)
 except (ValueError,KeyError,StopIteration):return None
 if banned(json.dumps(row)):return None
 # Exact origin and clean recorded ancestry. Refuse ambiguous legacy parents.
 if not p.exists():return None
 try:
  if key(n,mlp.load(str(p),{n})[n])!=k:return None
 except Exception:return None
 if not re.search(r'-r(?:23|24|25|26|27|28|29|30|31|32|33|34)/',origin):return None
 return dict(clean=True,n=n,origin=origin,ledger=str(ledger),source=row['source'],licence=row.get('licence','own'),sha256_geometry=k)

# Every admitted layout is expanded and checked before it reaches a numerical job.
def credit(n,A,origin=None):
 from source25 import audit
 # A held geometry match never waives a direct withdrawn input path.
 if origin and origin!='held' and banned(str(origin)):return None
 from admission32 import held_binding32
 held_round33=held_binding32(n,A)
 if held_round33 is not None:
  if origin and origin!='held' and not str(origin).startswith(str(S/'gather')+'/'):
   # Keep explicit forbidden producer records out even when coordinates match a held row.
   if legacy_credit(n,A,origin) is None:return None
  # An exact submitted row is an owned boundary. The walker resolves its source table.
  c=base().get(key(n,A),{})
  c={**c,'clean':True,'n':n,'origin':origin or 'held','source':f'held n = {n} of round {held_round33}; per-n source table results/round{held_round33}-best-2026-11-{'17' if held_round33==33 else '13' if held_round33==23 else '16'}.tsv','licence':'own held layout; historical input terms in the per-n results-table row','sha256_geometry':key(n,A)}
  return audit(c)
 from policy27 import share
 if origin and origin!='held':
  sys.path.insert(0,str(R))
  import walker30 as quench_walk
  from admission32 import is_current_held
  if not is_current_held(n,A) and quench_walk.harvest_type(str(origin),n) and share(n,A)>=0.4:return None
 c=legacy_credit(n,A,origin)
 return audit(c) if c else None


from policy27 import banned
