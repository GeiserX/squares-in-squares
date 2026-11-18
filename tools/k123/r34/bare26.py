"""Resolve a short producer filename only when its bytes match the named hash."""
import pathlib,hashlib,re
from provenance24 import S
_cache={}
def resolve(bare):
 if bare in _cache:return _cache[bare]
 m=re.fullmatch(r'(\d+)-([0-9a-f]{8,})\.csv',bare)
 if not m:return []
 hits=[]
 for rnd in [26,25,24,23,22]:
  for folder in ['work/starts','work/unread','work/donors','work/inputs','near']:
   for p in S.glob(f'take-*-r{rnd}/{folder}/{bare}'):
    if hashlib.sha256(p.read_bytes()).hexdigest().startswith(m[2]):hits.append(p)
  if hits:break
 if hits:_cache[bare]=list(dict.fromkeys(hits))
 return hits
