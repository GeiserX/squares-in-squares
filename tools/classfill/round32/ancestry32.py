"""Reject withdrawn direct pins while stopping at submitted held containers."""
import json,hashlib
from pathlib import Path
from functools import lru_cache
@lru_cache(maxsize=64)
def file_sha(path,size,stamp):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def check(proof,withdrawn,held_registry):
 seen=set();checked=[];boundaries=[]
 def visit(value):
  if isinstance(value,list):
   for x in value:visit(x)
   return
  if not isinstance(value,dict):return
  path=value.get('path');n=value.get('n');expected=value.get('sha256') or value.get('snapshot_sha256') or value.get('packing_sha256')
  if path in held_registry and isinstance(n,int):
   rec=held_registry[path];p=Path(path)
   if file_sha(str(p),p.stat().st_size,p.stat().st_mtime_ns)!=rec['sha256']:raise ValueError('changed held container '+path)
   boundaries.append(dict(path=path,n=n));return
  pins=[(path,expected),(value.get('input_path') or value.get('input'),value.get('input_sha256'))]
  for pin,digest in pins:
   if pin and digest and str(pin).endswith('.csv'):
    line=withdrawn(digest)
    if line:raise ValueError('withdrawn ancestor '+str(pin)+' '+str(digest)+' '+str(line))
    checked.append(dict(path=pin,sha256=digest))
  for k,child in value.items():
   if k in ('record','source_record','licence_record','source','licence'):continue
   if k in ('full_ancestry',) and isinstance(child,dict) and child.get('path'):
    load(child['path'],child.get('sha256'))
   elif k in ('proof','source_proof','ancestry_file') and isinstance(child,str) and child.endswith('.json'):
    load(child,value.get('ancestry_sha256') if k=='ancestry_file' else None)
   else:visit(child)
 def load(path,expected=None):
  if path in seen:return
  seen.add(path)
  if len(seen)>1200:raise ValueError('direct ancestry exceeds 1200 files')
  p=Path(path)
  if not p.is_file():raise ValueError('missing ancestry '+path)
  raw=p.read_bytes()
  if expected and hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('changed ancestry '+path)
  visit(json.loads(raw))
 try:
  load(str(proof));return True,dict(checked=checked,held_boundaries=boundaries,proof_files=len(seen))
 except (OSError,ValueError) as e:return False,dict(reason=str(e),checked=checked,held_boundaries=boundaries)

if __name__=='__main__':
 import tempfile
 with tempfile.TemporaryDirectory() as td:
  d=Path(td);held=d/'held.csv';held.write_text('held')
  bad=dict(path='withdrawn.csv',n=2,sha256='f'*64)
  p=d/'control.json';p.write_text(json.dumps(bad));predicate=lambda x:x=='f'*64
  assert not check(p,predicate,{})[0]
  p.write_text(json.dumps(dict(path=str(held),n=2,parent=bad)))
  assert check(p,predicate,{str(held):dict(sha256=hashlib.sha256(held.read_bytes()).hexdigest())})[0]
  p.write_text(json.dumps(dict(parents=[dict(path=str(held),n=2,parent=bad),bad])))
  assert not check(p,predicate,{str(held):dict(sha256=hashlib.sha256(held.read_bytes()).hexdigest())})[0]
 print('ANCESTRY32_CONTROL_PASS direct withdrawal refuses; held boundary passes; mixed direct/held ancestry refuses')
