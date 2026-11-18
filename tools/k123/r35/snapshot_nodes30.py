"""Find exact queued credits inside complete immutable source proofs."""
from pathlib import Path
import json,re,hashlib
RX=re.compile(r'$DATA/[^\s,;<>"\\]+\.json')
def credits(obj):
 from pinned28 import nodes
 queue=[obj];seen=set();out={};used=0
 while queue:
  obj=queue.pop();raw=json.dumps(obj)
  for c in nodes(obj):
   if c.get('n') and c.get('origin') and c.get('input_file_snapshot') and c.get('input_file_sha256') and c.get('input_record_snapshots'):
    out[(str(c['origin']),c['input_file_sha256'])]=c
  for name in set(RX.findall(raw)):
   if name in seen:continue
   seen.add(name);p=Path(name)
   if not p.is_file():continue
   used+=p.stat().st_size
   if len(seen)>1000 or used>50_000_000:raise ValueError('snapshot graph budget exceeded; binding deferred')
   data=p.read_bytes()
   if p.parent in [Path(__file__).resolve().parent/'ancestry',Path(__file__).resolve().parent/'input-snapshots'] and re.fullmatch('[0-9a-f]{64}',p.stem) and hashlib.sha256(data).hexdigest()!=p.stem:raise ValueError('changed hash-addressed source proof: '+str(p))
   try:j=json.loads(data)
   except ValueError:continue
   queue.append(j)
 return list(out.values())
