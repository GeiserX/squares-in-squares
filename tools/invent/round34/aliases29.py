"""Find source-bearing immutable aliases by exact CSV bytes and count."""
import csv,hashlib,json,pathlib
S=pathlib.Path('$SCRATCH/bounties-squares');_index=None

def build():
 global _index
 if _index is not None:return _index
 index={}
 paths=list((S/'take-forensics-r28/work/feed').glob('**/*.csv.origin.json'))
 for origin in paths:
  try:
   value=json.load(open(origin));p=pathlib.Path(str(origin).removesuffix('.origin.json'))
   if value.get('verified_ancestry') and p.is_file():index.setdefault((int(value['n']),value['snapshot_sha256']),[]).append(str(p))
  except (OSError,KeyError,ValueError):pass
 for p in (S/'take-backlog-r28/near').glob('*.csv'):
  if not (p.with_suffix('.json').exists()or pathlib.Path(str(p)+'.json').exists()):continue
  try:
   count=int(p.name.split('-')[0]);digest=hashlib.sha256(p.read_bytes()).hexdigest();index.setdefault((count,digest),[]).append(str(p))
  except (OSError,ValueError):pass
 _index=index
 return index

def candidates(path,n):
 p=pathlib.Path(path)
 if not p.is_file():return []
 digest=hashlib.sha256(p.read_bytes()).hexdigest()
 return [pathlib.Path(v)for v in build().get((n,digest),[])if pathlib.Path(v)!=p and hashlib.sha256(pathlib.Path(v).read_bytes()).hexdigest()==digest]
