"""Resolve a hash-bound k123 held catalogue leaf to its submitted geometry."""
import pathlib,json,re,hashlib,csv
import numpy as np
from held32 import resolve,S,SUBMITTED
_cache={}
def resolve_record(record):
 p=pathlib.Path(str(record).split(' n=',1)[0])
 if p.suffix!='.json'or not p.is_file()or not p.resolve().is_relative_to(S):return None
 try:
  d=json.load(open(p))
  if not isinstance(d,dict)or set(d)-{'layout','source','licence'}:return None
  v=d.get('layout',{});n=int(v.get('n',0));origin=v.get('origin','');expected=v.get('sha256_geometry','')
  m=re.fullmatch(r'held round(\d+)([a-z])',origin)
  if not m or not n or not v.get('clean')or not re.fullmatch('[0-9a-f]{64}',expected):return None
  options=[name for name in SUBMITTED if re.match('round'+m[1]+'-',name)and name.endswith(m[2]+'.csv')]
  if len(options)!=1:return None
  base=S/'gather'/options[0];root=resolve(dict(path=str(base),n=n))
  if root is None:return None
  key=(str(base),root['held_witness_file'],n)
  if key not in _cache:
   a=np.array([[float(r[k])for k in('x','y','angle')]for r in csv.DictReader(open(base))if int(r['n'])==n],dtype=np.float64)
   if len(a)!=n:return None
   a=np.ascontiguousarray(a[np.lexsort((a[:,2],a[:,1],a[:,0]))],dtype=np.float64)
   _cache[key]=hashlib.sha256(f'{n}:0:'.encode()+a.tobytes()).hexdigest()
  if _cache[key]!=expected:return None
  return root
 except (ValueError,KeyError,OSError,TypeError):return None
