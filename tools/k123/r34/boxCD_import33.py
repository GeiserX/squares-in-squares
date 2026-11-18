"""Install immutable inputs before publishing a queue bundle to running workers."""
from pathlib import Path
import hashlib,json,tarfile,sys
R=Path.home()/'scratch/squares-k123';p=R/'boxCD-export33.tgz';assert hashlib.sha256(p.read_bytes()).hexdigest()==sys.argv[1]
mutable={'queue.tsv','bars.tsv','boxD-pools33.json','boxD-claims33.json'};pending={}
with tarfile.open(p,'r:gz') as a:
 for m in a.getmembers():
  assert m.isfile() and '/' not in m.name and m.name not in {'.','..'}
  data=a.extractfile(m).read();target=R/m.name
  if m.name in mutable:pending[m.name]=data;continue
  if target.exists():
   assert target.read_bytes()==data,('changed immutable pool',m.name);continue
  tmp=target.with_name(target.name+'.incoming');tmp.write_bytes(data);tmp.replace(target)
assert mutable<=pending.keys()
for pool in json.loads(pending['boxD-pools33.json']):
 assert all((R/name).is_file() for name in [pool+'.csv','sources-'+pool+'.json','bars-'+pool+'.tsv']),('incomplete ready pool',pool)
# Workers may see the old queue while these files replace. Every input is already installed.
for name in ['bars.tsv','boxD-claims33.json','boxD-pools33.json','queue.tsv']:
 target=R/name;tmp=target.with_name(target.name+'.incoming');tmp.write_bytes(pending[name]);tmp.replace(target)
for name in json.loads(pending['boxD-claims33.json']):(R/'claims'/name).mkdir(exist_ok=True)
p.unlink();print('queue bundle sha256 verified; immutable inputs installed before queue publication')
