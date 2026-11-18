"""Export only code, packing pools and deterministic queue claims for the extra box."""
from pathlib import Path
import json,csv,tarfile,hashlib,time
R=Path.home()/'scratch/squares-k123';queue=(R/'queue.tsv').read_text();pools={l.split('\t')[7] for l in queue.splitlines() if len(l.split('\t'))>=8};allowed=[]
for pool in sorted(pools):
 if pool.startswith('fresh') or pool.startswith('deferred33') and (R/('sources-'+pool+'.json')).exists() and '-r33/' in (R/('sources-'+pool+'.json')).read_text():allowed.append(pool)
(R/'boxD-pools33.json.tmp').write_text(json.dumps(allowed));(R/'boxD-pools33.json.tmp').replace(R/'boxD-pools33.json')
(R/'boxD-claims33.json').write_text(json.dumps(sorted(p.name for p in (R/'claims').iterdir() if p.is_dir())))
with tarfile.open(R/'boxCD-export33.tgz.tmp','w:gz',compresslevel=1) as out:
 for name in ['queue.tsv','bars.tsv','boxD-pools33.json','boxD-claims33.json']:
  out.add(R/name,arcname=name)
 for pool in allowed:
  for name in [pool+'.csv','sources-'+pool+'.json','bars-'+pool+'.tsv']:
   if (R/name).exists():out.add(R/name,arcname=name)
(R/'boxCD-export33.tgz.tmp').replace(R/'boxCD-export33.tgz')
print(json.dumps({'pools':len(allowed),'bytes':(R/'boxCD-export33.tgz').stat().st_size,'sha256':hashlib.sha256((R/'boxCD-export33.tgz').read_bytes()).hexdigest()}))
