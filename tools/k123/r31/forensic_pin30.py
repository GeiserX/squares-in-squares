"""Read missing producer rows only from exact frozen packing/evidence bindings."""
from pathlib import Path
import json,re,hashlib,csv,functools
RX=re.compile(r'$DATA/[^\s,;<>"\\]+\.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def payloads(obj):
 from pinned28 import nodes
 yield from nodes(obj)
@functools.lru_cache(64)
def proofs(text):
 queue=[json.loads(text)];seen=set();bindings={};evidence=[]
 while queue and len(seen)<500:
  obj=queue.pop();raw=json.dumps(obj)
  for name in set(RX.findall(raw)):
   if name in seen:continue
   seen.add(name);p=Path(name)
   if not p.is_file() or p.stat().st_size>10_000_000:continue
   data=p.read_bytes()
   if len(p.stem)==64 and re.fullmatch('[0-9a-f]{64}',p.stem) and hashlib.sha256(data).hexdigest()!=p.stem:continue
   try:j=json.loads(data)
   except ValueError:continue
   queue.append(j)
   if isinstance(j,dict):
    if j.get('path') and j.get('snapshot_sha256') and name.endswith('.csv.origin.json'):
     cp=Path(name[:-len('.origin.json')])
     if cp.is_file() and sha(cp)==j['snapshot_sha256']:bindings[(j['path'],j['snapshot_sha256'])]=str(cp)
    if j.get('path') and j.get('packing_sha256') and isinstance(j.get('evidence'),dict):evidence.append((name,j))
 result={}
 for name,j in evidence:
  k=(j['path'],j['packing_sha256']);e=j['evidence'];r=e.get('record')
  if k not in bindings or e.get('path')!=j['path'] or not isinstance(r,dict) or not r.get('source') or not r.get('licence'):continue
  n=str(j.get('n'));cp=Path(bindings[k]);p=Path(k[0])
  if r.get('n')!=n or p.stem!=n:continue
  if p.is_file() and sha(p)!=k[1]:continue
  rows=list(csv.DictReader(cp.open()))
  if len(rows)!=int(n) or any(r.get('n')!=n for r in rows):continue
  result[k[0]]={'source':r['source'],'licence':r['licence'],'producer_record_snapshot':name,'producer_record_sha256':sha(Path(name)),'producer_csv_snapshot':str(cp),'producer_csv_sha256':k[1],'recovery_rule':'exact frozen forensics packing and producer record'}
 return result

def row(path,obj):
 try:return proofs(json.dumps(obj,sort_keys=True,default=str)).get(str(path))
 except (OSError,ValueError,KeyError):return None
