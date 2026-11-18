"""Verify pins and share-check recorded public-first starts only."""
from common29 import *
from share_policy29 import POLICY
from prvsim29 import check
PUBLIC=re.compile(r'(?:$SCRATCH/bounties-squares/)?take-harvest-r\d+/work/public\d*/(?:starts|quick-starts)/[^\s<>";,()\\\[\]{}]+?\.csv')
def inspect(closure):
 a=read(closure,{});errors=[];checks=[];public_records=[];allpins=a.get('snapshots',[])+a.get('expanded',{}).get('history',{}).get('snapshots',[]);pinmap={q['path']:q for q in allpins};texts=[a.get('source','')]+a.get('expanded',{}).get('history',{}).get('parts',[])
 for q in allpins:
  p=Path(q['snapshot'])
  if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=q['sha256']:errors.append(dict(path=q['path'],error='snapshot hash differs or file missing'));continue
  if q['path'].endswith('.json') and p.stat().st_size<50000000:
   raw=p.read_text();texts.append(raw)
   try:
    def record(obj):
     if isinstance(obj,list):
      for child in obj:record(child)
     elif isinstance(obj,dict):
      if obj.get('original') and obj.get('snapshot') and obj.get('sha256'):
       pinmap[obj['original']]=dict(path=obj['original'],snapshot=obj['snapshot'],sha256=obj['sha256'])
      for child in obj.values():
       if isinstance(child,(dict,list)):record(child)
    value=json.loads(raw);record(value)
    if isinstance(value,dict) and q['path'].endswith('.csv.json'):
     src=value.get('source','');ref=re.match(r'\s*(?:public\s+)?([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\s*::',src) if isinstance(src,str) else None
     if ref and ref[1] not in ['Samanyu-dev/squares_in_squares','franciscouzo/square-packing'] and value.get('public_first') is not False:
      public_records.append(q['path'][:-5])

   except (ValueError,RecursionError):pass
 paths=sorted({str(S/m.group().removeprefix(str(S)+'/')) for text in texts for m in PUBLIC.finditer(text)}|set(public_records))
 for text in paths:
  p=Path(text);pin=pinmap.get(text)
  if not pin:
   if not p.is_file():errors.append(dict(path=text,error='public-first packing missing'));continue
   pin=blob(p)
  snap=Path(pin['snapshot'])
  if not snap.is_file() or hashlib.sha256(snap.read_bytes()).hexdigest()!=pin['sha256']:errors.append(dict(path=text,error='public-first pin differs'));continue
  try:
   with snap.open() as h:
    rr=csv.DictReader(h)
    if not {'x','y'}<=set(rr.fieldnames or []):continue
    ns=set()
    for row in rr:
     ns.add(int(row['n']) if 'n' in row else int(row['id'].split('_')[0]))
     if len(ns)>1:break
   if len(ns)!=1:errors.append(dict(path=text,error='public-first count is ambiguous'));continue
   n=next(iter(ns));measure=check(str(snap),n)
   checks.append(dict(n=n,original=text,snapshot=str(snap),sha256=pin['sha256'],share=measure['share'],excluded=measure['excluded'],policy='public-first ancestor'))
  except (OSError,ValueError,KeyError,AssertionError,csv.Error) as e:errors.append(dict(path=text,error=repr(e)))
 proof_hashes={hashlib.sha256(Path(closure).read_bytes()).hexdigest()}
 for key in ['prior_closure','repaired_from']:
  if isinstance(a.get(key),dict) and a[key].get('sha256'):proof_hashes.add(a[key]['sha256'])
 for digest,refusal in read(W/'public-proof-refusals.json',{}).items():
  if digest in proof_hashes:
   root=refusal['root'];checks.append(dict(n=root['n'],share=root['variants'][0]['share'],excluded=True,policy='byte-bound public-first archive proof',source_proof_sha256=digest,evidence=refusal))
 return dict(time=now(),closure=str(closure),policy=POLICY+'-public-first-roots',checks=checks,excluded=[q for q in checks if q['excluded']],errors=errors)
