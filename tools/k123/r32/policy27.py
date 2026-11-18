"""Remaining round27 exclusions and source-specific withdrawal handling."""
import re,pathlib,functools,json,csv,zipfile,io
S=pathlib.Path('$SCRATCH/bounties-squares')
BAD=re.compile(r'CC BY-SA|Attribution.ShareAlike|ShareAlike|penguin069/squares-joegun-boxed-certified-union|squares-joegun-boxed|squares-verified-best-of-1105|take-harvest-r22/(?:near/)?(?:639|691|745|858|918)\b|take-(?:invent|midm)-r23/(?:near/)?639\b|take-forensics-r23/(?:near/)?980\b|take-forensics-r(?:1\d|2[0-3])/(?:near/)?918\b',re.I)
def lifted(line):
 # Mixed exclusions are never waived by a mention of the permitted seed.
 if BAD.search(line) or re.search(r'prvsiyan|changed|rewrit|gone|missing|untraceable licence|without traceable|generic original',line,re.I):return False
 return bool(re.search(r'Samanyu|seed(?:365|503|811|921|983)|bare921|held415/501/813/933|held933|735 tree',line,re.I))
@functools.lru_cache(8)
def withdrawals(stamps):
 out=[]
 for name,stamp in stamps:
  for line in pathlib.Path(name).read_text().splitlines():
   if re.search(r'\bWITHDRAW|\bWITHHOLD',line) and not lifted(line):
    out.extend((p,line) for p in re.findall(r'(take-[a-z0-9-]+-r\d+/[^\s,;]+?\.csv)',line))
 return out
_walk_stamp=None
_walk_sha=None
_lines_cache=None
_lines_clock=0.
_code_clock=0.
def lines():
 global _walk_stamp,_walk_sha,_lines_cache,_lines_clock,_code_clock
 import sys,importlib,time
 now=time.monotonic()
 if _lines_cache is not None and now-_lines_clock<2:return _lines_cache
 lane=pathlib.Path('.');sys.path.insert(0,str(lane))
 import walker30 as quench_walk
 if now-_code_clock>=60:
  stamp=(pathlib.Path(__file__).resolve().parent/'walker30.py').stat().st_mtime_ns
  if _walk_stamp!=stamp:
   digest=__import__('hashlib').sha256((pathlib.Path(__file__).resolve().parent/'walker30.py').read_bytes()).hexdigest()
   if digest!=_walk_sha:importlib.reload(quench_walk);_walk_sha=digest
   _walk_stamp=stamp
  _code_clock=now
 quench_walk.load_withdrawn()
 _lines_cache=list(quench_walk.WITHDRAWN_LINES);_lines_clock=time.monotonic()
 return _lines_cache
def resolved_seed_withdrawal(path,line):
 # The full 982 source walk resolves this Samanyu-only module chain (23 files,
 # no missing records). Keep later withdrawals of the same path active.
 return path=='take-stair-c-r17/near/921-29e12ff3.csv' and line.split(' ',1)[0] in {
  '2026-11-13T23:17:11Z','2026-11-14T01:27:36Z'}
def banned(text):
 # A walk's path list is diagnostic evidence, not an ancestry edge.
 try:
  value=json.loads(text)
  def drop32(x):
   if isinstance(x,dict):return {k:drop32(v) for k,v in x.items() if k!='checked_paths'}
   if isinstance(x,list):return [drop32(v) for v in x]
   return x
  text=json.dumps(drop32(value))
 except (ValueError,TypeError):pass
 active=lines()
 import walker30 as quench_walk
 if hasattr(quench_walk,'CMP'):text=quench_walk.CMP.sub(' ',text)
 if BAD.search(text):return True
 # Exact fetched public551 pin: kmmmvs daily merge, share0.788. Own geometry has no share gate.
 if 'take-harvest-r22/work/collector/certified/52c2828aaa9bb34a242993b087e32c929e345b516309882921072b62a2365102.csv' in text:
  pin=pathlib.Path('$SCRATCH/bounties-squares/take-harvest-r22/work/collector/certified/52c2828aaa9bb34a242993b087e32c929e345b516309882921072b62a2365102.csv')
  if pin.exists() and __import__('hashlib').sha256(pin.read_bytes()).hexdigest()=='52c2828aaa9bb34a242993b087e32c929e345b516309882921072b62a2365102':return True
 for p,line in active:
  from current_walk29 import retention_note
  if retention_note(line):continue
  if resolved_seed_withdrawal(p,line):continue
  if p in text:
   from replacements25 import allowed
   if not allowed(str(S/p)):return True
 return False
@functools.lru_cache(None)
def prv():
 p=S/'take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip';out={}
 with zipfile.ZipFile(p) as z:
  for name in ['submission.csv']:
   for row in csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig'))):
    r={str(k).strip().lower():v for k,v in row.items()};nn=str(r.get('n',r.get('id','').split('_')[0])).lstrip('s')
    if nn.isdigit() and 'x' in r and 'y' in r:out.setdefault(int(nn),[]).append((float(str(r['x']).lstrip('s')),float(str(r['y']).lstrip('s'))))
 return out
_share={}
def share(n,A):
 from publicshare31 import measure
 m=measure(n,A)
 return max(m[1],m[2])
