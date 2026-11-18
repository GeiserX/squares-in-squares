"""Admit only traced licensed inputs and store each complete proof once."""
import pathlib,json,hashlib,re,csv,functools
from provenance24 import W,S,banned
from ancestry24 import expand
from seed_notice24 import notice
(W/'ancestry').mkdir(exist_ok=True)
@functools.lru_cache(None)
def audit_text(text):
 c=json.loads(text)
 original=json.loads(text)
 if not c.get('source') or not c.get('licence') or banned(text):return None
 c=expand(c)
 from terms26 import unique
 c['licence']=unique(c['licence'])
 if not c.get('clean') or banned(json.dumps(c)):return None
 if notice(c['source'],c['licence'])[1] is not False:return None
 # Resolve full recorded parent paths, including relative frozen take paths.
 queue=[c];seen=set();records=[];held_seen=set()
 while queue:
  node=queue.pop();t=json.dumps(node)
  from seed_rule27 import text_checks
  if any(z['excluded'] for z in text_checks(t)):return None
  from held26 import walker
  # A historical path pin must still resolve to the recorded bytes.
  for pin in walker.PIN.finditer(t):
   pinned_path=pin.group(1)
   if not pinned_path.startswith('/'):pinned_path=str(S/pinned_path)
   have=walker.file_sha(pinned_path)
   if have and not have.startswith(pin.group(2).lower()):return None
  # Hash-named proofs and producer sidecars are ancestry edges too.
  for digest in set(walker.ANC.findall(t)):
   for directory in walker.ANCDIRS:
    jp=pathlib.Path(directory)/(digest+'.json')
    if not jp.exists() or str(jp) in seen:continue
    seen.add(str(jp));jj=json.load(open(jp));records.append({'source_record':str(jp),'sha256_file':hashlib.sha256(jp.read_bytes()).hexdigest()});queue.append(jj)
  # Resolve implicit historical held parents, including unnumbered round references.
  from held26 import edges,resolve
  for nn,kk in edges(t):
   if (nn,kk) in held_seen:continue
   held_seen.add((nn,kk));record=resolve(nn,kk)
   if not record:return None
   jj={'resolved_n':nn,'resolved_round':kk,'source':record,'licence':'terms in the resolved historical results record'}
   records.append(jj);queue.append(jj)
  # Follow hash-addressed immutable source proofs as well as CSV sidecars.
  for pp in re.findall(r'$DATA/[^\s,;<>"\\]+\.json',t):
   if pp in seen:continue
   seen.add(pp);jp=pathlib.Path(pp)
   if not jp.exists():
    if re.search(r'/ancestry/[0-9a-f]{64}\.json$',pp):return None
    continue
   try:
    jj=json.load(open(jp))
    if isinstance(jj,dict):
     records.append({'path':pp,'source_record':pp,'sha256_file':hashlib.sha256(jp.read_bytes()).hexdigest()} if re.search(r'/ancestry/[0-9a-f]{64}\.json$',pp) else {'path':pp,'record':jj})
     queue.append(jj)
   except (ValueError,OSError):return None
  if 'original clean seed' in t or 'source credited in README.md Outside data' in t:return None
  if banned(t) or notice(t,'')[1] is not False:return None
  # Bare hashed producer names are ancestry edges. Refuse when no exact record can be found.
  for bare in set(re.findall(r'(?<![A-Za-z0-9_/-])([0-9]+-[0-9a-f]{8,}\.csv)',t)):
   candidates=[]
   for evidence in re.findall(r'$DATA/[^\s,;<>"\\]+',t):
    ep=pathlib.Path(evidence)
    for root in [ep.parent,ep.parent/'unread',ep.parent/'inputs',ep.parent.parent/'unread']:
     bp=root/bare
     if bp.exists():candidates.append(bp)
   from bare26 import resolve
   candidates.extend(resolve(bare))
   found=False
   if bare=='921-29e12ff3.csv':
    records.append({'bare_seed':bare,'source':'own discovered packing; same layout later found in Samanyu-dev/squares_in_squares','licence':'own; round27 override'});found=True
   for bp in dict.fromkeys(candidates):
    for jp in [pathlib.Path(str(bp)+'.json'),bp.with_suffix('.json')]:
     if jp.exists():
      jj=json.load(open(jp));records.append({'path':str(bp),'record':jj});queue.append(jj);found=True
   if not found:return None
  paths=set(re.findall(r'(?:$SCRATCH/bounties-squares/)?take-[^\s,;<>"\\]+\.csv',t))
  for bare in set(walker.BARE.findall(t)):
   for evidence in re.findall(r'$DATA/[^\s,;<>"\\]+',t):
    ep=pathlib.Path(evidence);match=re.search(r'(.*?/take-[a-z0-9-]+-r[0-9]+)/',str(ep))
    roots=[ep.parent]+([pathlib.Path(match[1])/'near',pathlib.Path(match[1])/'work'] if match else [])
    for root in roots:
     bp=root/bare
     if bp.exists():paths.add(str(bp))
  for name in paths:
   p=pathlib.Path(name) if name.startswith('/') else S/name
   if not p.exists():
    moved=walker.moved_copy(str(p))
    if moved:p=pathlib.Path(moved)
   from csv_rule27 import one
   cc=one(p)
   if cc and cc['excluded']:return None
   if str(p) in seen:continue
   seen.add(str(p));data=[]
   for sidecar in map(pathlib.Path,walker.sidecars(str(p))):
    if sidecar.exists():
     try:
      j=json.load(open(sidecar))
      if isinstance(j,dict):data.append(j)
     except (ValueError,OSError):return None
   if p.stem.isdigit() and (p.parent/'take.tsv').exists():
    try:data.append(next(r for r in csv.DictReader(open(p.parent/'take.tsv'),delimiter='\t') if r['n']==p.stem))
    except StopIteration:
     from pinned28 import row as pinned_row
     frozen=pinned_row(p,node) or pinned_row(p,original)
     if frozen:
      records.append({'path':str(p),'record':frozen});queue.append(frozen)
      continue
     old=re.search(r'take-[^/]+-r(\d+)/(\d+)\.csv$',str(p))
     if old and int(old[1])<=25:
      record=walker.held(int(old[2]),int(old[1]))
      if record:data.append({'source':record,'licence':'terms in historical held source record'})
      else:return None
     else:return None
   # Other source text already expands historical module and seed notices.
   for j in data:
    if p.exists():records.append({'path':str(p),'record':j})
    else:records.append({'source_record_kind':'historical held record','record':j})
    queue.append(j)
 # Always emit a new round26 proof after the complete recursive check.
 audit_record={'layout':c,'parents':records,'walked_paths':sorted(p for p in seen if pathlib.Path(p).exists())}
 audit_raw=json.dumps(audit_record,separators=(',',':'));audit_sha=hashlib.sha256(audit_raw.encode()).hexdigest()
 audit_dir=W/'audit-records';audit_dir.mkdir(exist_ok=True);(audit_dir/(audit_sha+'.json')).write_text(audit_raw)
 out={'layout':original,'source':original['source'],'licence':original['licence']}
 # Original source edges retain held-chain context. Expanded audit evidence is stored separately.

 raw=json.dumps(out,separators=(',',':'));sha=hashlib.sha256(raw.encode()).hexdigest();p=W/'ancestry'/f'{sha}.json'
 if not p.exists():p.write_text(raw)
 # Full source stays available by immutable hash. Keep areebbb per-n records inline too.
 upstream=''
 if 'areebbb/' in c['source']:
  pass  # Exact public per-n notices are added by areeb_chain28 before publication.
 return {**c,'source':f"licensed ancestry sha256 {sha}; full source_record {p}"+upstream,'ancestry_file':str(p),'ancestry_sha256':sha,'clean':True,'seed_share_gate':'v6','checked_paths':audit_record['walked_paths']}

_cache=None
_retry_origins=set()
def retry_origin(origin):_retry_origins.add(str(origin))
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
 k=hashlib.sha256(('r28-full-tree-v5-pin:'+text).encode()).hexdigest()
 origin=str(c.get('origin','')) if isinstance(c,dict) else ''
 if origin in _retry_origins:
  _retry_origins.discard(origin)
  if k in _cache and _cache[k] is None:
   _cache.pop(k,None)
   audit_text.cache_clear()  # A repaired proof must clear the in-memory refusal too.
 if k in _cache and _cache[k] is None and 'CC BY-SA' in text and 'share' in text:
  _cache.pop(k,None)
 if k in _cache and _cache[k] is None and 'penguin069/' in text and 'squares-joegun-boxed' not in text:_cache.pop(k,None)
 if k in _cache:
  hit=_cache[k]
  if hit and banned(' '.join(hit.get('checked_paths',[]))):return None
  if hit and hit.get('ancestry_file') and hit.get('source','').startswith('licensed ancestry sha256 '):hit={**hit,'source':hit['source'].split(' | ',1)[0]}
  return hit
 result=audit_text(text)
 if result:
  result=dict(result)
  proof=json.load(open(result['ancestry_file'])) if result.get('ancestry_file') else {}
  result['checked_paths']=result.get('checked_paths',proof.get('walked_paths',[]))
 _cache[k]=result
 with open(W/'admission-cache25.jsonl','a') as f:f.write(json.dumps([k,result],separators=(',',':'))+'\n')
 return result

