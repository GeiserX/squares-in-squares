"""Admit only traced licensed inputs and store each complete proof once."""
import pathlib,json,hashlib,re,csv,functools
from provenance24 import W,S,banned
from ancestry24 import expand
from seed_notice24 import notice
(W/'ancestry').mkdir(exist_ok=True)
@functools.lru_cache(None)
def audit_text(text):
 c=json.loads(text)
 if not c.get('source') or not c.get('licence') or banned(text):return None
 c=expand(c)
 if not c.get('clean') or banned(json.dumps(c)):return None
 if notice(c['source'],c['licence'])[1] is not False:return None
 # Resolve full recorded parent paths, including relative frozen take paths.
 queue=[c];seen=set();records=[]
 while queue:
  node=queue.pop();t=json.dumps(node)
  # Follow hash-addressed immutable source proofs as well as CSV sidecars.
  for pp in re.findall(r'$DATA/[^\s,;<>"\\]+\.json',t):
   if pp in seen:continue
   seen.add(pp);jp=pathlib.Path(pp)
   if not jp.exists():continue
   try:
    jj=json.load(open(jp))
    if isinstance(jj,dict):records.append({'path':pp,'record':jj});queue.append(jj)
   except (ValueError,OSError):return None
  if 'original clean seed' in t or 'source credited in README.md Outside data' in t:return None
  if banned(t) or notice(t,'')[1] is not False:return None
  paths=set(re.findall(r'(?:$SCRATCH/bounties-squares/)?take-[^\s,;<>"\\]+\.csv',t))
  for name in paths:
   p=pathlib.Path(name) if name.startswith('/') else S/name
   if str(p) in seen:continue
   seen.add(str(p));data=[]
   for sidecar in [pathlib.Path(str(p)+'.json'),p.with_suffix('.json')]:
    if sidecar.exists():
     try:
      j=json.load(open(sidecar))
      if isinstance(j,dict):data.append(j)
     except (ValueError,OSError):return None
   if p.stem.isdigit() and (p.parent/'take.tsv').exists():
    try:data.append(next(r for r in csv.DictReader(open(p.parent/'take.tsv'),delimiter='\t') if r['n']==p.stem))
    except StopIteration:return None
   # Other source text already expands historical module and seed notices.
   for j in data:
    records.append({'path':str(p),'record':j});queue.append(j)
 if c.get('ancestry_file') and pathlib.Path(c['ancestry_file']).exists():return c
 out={'layout':c,'parents':records,'walked_paths':sorted(seen),'source':c['source'],'licence':c['licence']}
 raw=json.dumps(out,separators=(',',':'));sha=hashlib.sha256(raw.encode()).hexdigest();p=W/'ancestry'/f'{sha}.json'
 if not p.exists():p.write_text(raw)
 # Full source stays available by immutable hash. Keep areebbb per-n records inline too.
 upstream=''
 if 'areebbb/' in c['source']:
  upstream=' | '+c['source']
 return {**c,'source':f"licensed ancestry sha256 {sha}; full source_record {p}"+upstream,'ancestry_file':str(p),'ancestry_sha256':sha,'clean':True}

_cache=None
def audit(c):
 global _cache
 from provenance24 import banned
 if _cache is None:
  _cache={}
  cp=W/'admission-cache25.jsonl'
  if cp.exists():
   for l in cp.read_text().splitlines():
    try:
     k,v=json.loads(l);_cache[k]=v
    except ValueError:pass
 text=json.dumps(c,sort_keys=True,default=str)
 if banned(text):return None
 k=hashlib.sha256(text.encode()).hexdigest()
 if k in _cache:
  hit=_cache[k]
  if hit and banned(' '.join(hit.get('checked_paths',[]))):return None
  return hit
 result=audit_text(text)
 if result:
  result=dict(result)
  proof=json.load(open(result['ancestry_file'])) if result.get('ancestry_file') else {}
  result['checked_paths']=proof.get('walked_paths',[])
 _cache[k]=result
 with open(W/'admission-cache25.jsonl','a') as f:f.write(json.dumps([k,result],separators=(',',':'))+'\n')
 return result

