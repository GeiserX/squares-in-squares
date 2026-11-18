"""Install a pinned queue bundle without overwriting running pool files."""
from pathlib import Path
import hashlib,json,tarfile,sys,os
R=Path.home()/'scratch/squares-k123';p=R/'boxCD-export33.tgz';assert hashlib.sha256(p.read_bytes()).hexdigest()==sys.argv[1]
with tarfile.open(p,'r:gz') as a:
 for m in a.getmembers():
  assert m.isfile() and '/' not in m.name and m.name not in {'.','..'}
  data=a.extractfile(m).read();target=R/m.name
  if target.exists() and m.name not in {'queue.tsv','bars.tsv','boxD-pools33.json','boxD-claims33.json'}:
   assert target.read_bytes()==data,('changed immutable pool',m.name);continue
  tmp=target.with_name(target.name+'.incoming');tmp.write_bytes(data);tmp.replace(target)
for name in json.load((R/'boxD-claims33.json').open()):(R/'claims'/name).mkdir(exist_ok=True)
p.unlink();print('queue bundle sha256 verified')
