"""Bind a clean replacement to both its CSV bytes and its new source record."""
import pathlib,json,csv,hashlib,functools
from provenance24 import W

def digest(row):
 return hashlib.sha256(json.dumps({k:row.get(k,'') for k in ['n','source','licence']},sort_keys=True).encode()).hexdigest()
def register(path,row):
 p=pathlib.Path(path);registry=W/'clean-replacements25.json';d=json.load(open(registry)) if registry.exists() else {}
 d[str(p)]={'csv_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_sha256':digest(row),'n':int(row['n'])}
 registry.with_suffix('.tmp').write_text(json.dumps(d));registry.with_suffix('.tmp').replace(registry)
@functools.lru_cache(2048)
def _allowed(path,csv_mtime,table_mtime,registry_mtime):
 p=pathlib.Path(path);j=json.load(open(W/'clean-replacements25.json'));r=j.get(path)
 if not r:return False
 try:row=next(z for z in csv.DictReader(open(p.parent/'take.tsv'),delimiter='\t') if int(z['n'])==r['n'])
 except (OSError,StopIteration,ValueError):return False
 return digest(row)==r['source_sha256'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['csv_sha256']
def allowed(path):
 try:
  p=pathlib.Path(path);return _allowed(str(p),p.stat().st_mtime_ns,(p.parent/'take.tsv').stat().st_mtime_ns,(W/'clean-replacements25.json').stat().st_mtime_ns)
 except OSError:return False
