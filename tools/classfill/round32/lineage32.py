"""Bind each computed output to its actual inputs and pinned source tree."""
import csv,hashlib,json,os
from functools import lru_cache
from pathlib import Path
W=Path('$SCRATCH/bounties-squares/take-classfill-r32/work')

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def atomic(p,value):
 p=Path(p);q=p.with_name(p.name+'.'+str(os.getpid())+'.tmp');q.write_text(json.dumps(value,indent=1)+'\n');q.replace(p)
@lru_cache(maxsize=64)
def held_rows(path,size,stamp,n):
 return sorted((int(r['square_id']),float(r['x']),float(r['y']),float(r['angle'])) for r in csv.DictReader(open(path)) if int(r['n'])==n)
def coordinates(path,n):return held_rows(str(path),Path(path).stat().st_size,Path(path).stat().st_mtime_ns,n)

def tree(receipt,expected=None,active=None):
 receipt=Path(receipt);active=set(active or ())
 if str(receipt) in active:raise ValueError('primary lineage cycle')
 active.add(str(receipt));r=read(receipt);j=r['job'];n=j['n'];out=Path(r['output']);digest=r['output_sha256']
 if sha(out)!=digest or (expected and expected!=digest):raise ValueError('changed output '+str(out))
 audit=r['finish']['original_byte_audit']
 if not audit.get('passed') or audit['input_sha256']!=digest:raise ValueError('output audit does not bind bytes')
 inp=Path(j['input_snapshot']);input_sha=j['input_sha256']
 if sha(inp)!=input_sha:raise ValueError('changed numerical input '+str(inp))
 proofpath=Path(j['proof']);proof=read(proofpath)
 if 'job' in proof:
  parent=tree(proofpath,input_sha,active)
 elif 'source_closure' in proof:
  if proof['sha256']!=input_sha:raise ValueError('source proof differs from numerical input')
  pinned=proof['source_closure']['full_ancestry'];docpath=Path(pinned['path'])
  if sha(docpath)!=pinned['sha256']:raise ValueError('changed source document')
  doc=read(docpath)
  if doc.get('packing_sha256')!=input_sha or doc.get('n')!=n:raise ValueError('source document does not bind numerical input')
  parent=doc['evidence']
 elif proof.get('row_sha256'):
  donor=Path(proof['path']);registry=read(W/'fresh-source/submitted-held30.json')
  if str(donor) not in registry or sha(donor)!=registry[str(donor)]['sha256'] or proof['row_sha256']!=input_sha:raise ValueError('held source pin differs')
  if coordinates(inp,n)!=coordinates(donor,n):raise ValueError('input is not the declared held projection')
  parent=dict(path=str(donor),n=n,snapshot_sha256=sha(donor),reason='submitted own held root')
 else:raise ValueError('unsupported primary input proof '+str(proofpath))
 return dict(path=str(out),n=n,snapshot_sha256=digest,reason='computed own classfill step with pinned numerical input',input=dict(path=str(inp),n=n,snapshot_sha256=input_sha,parent=parent),record=dict(operation=j.get('search_method'),kind=j['kind'],seed=j['seed'],seconds=j['seconds'],numerical_receipt_sha256=sha(receipt)))

def attach(path,receipt):
 path=Path(path);receipt=Path(receipt);r=read(receipt);digest=sha(path)
 if digest!=r['output_sha256']:raise ValueError('published copy differs from numerical result')
 ancestry=tree(receipt,digest)
 document=dict(path=str(path),n=r['job']['n'],packing_sha256=digest,evidence=ancestry)
 blob=json.dumps(document,sort_keys=True,separators=(',',':')).encode();key=hashlib.sha256(blob).hexdigest();directory=W/'primary-lineage';directory.mkdir(exist_ok=True);proof=directory/(key+'.json')
 if not proof.exists():proof.write_bytes(blob)
 origin=dict(path=r['output'],n=r['job']['n'],verified_ancestry=True,snapshot_sha256=digest,ancestry=ancestry,full_ancestry=dict(path=str(proof),sha256=key),public_first=r.get('public_first',False),audit_receipt=dict(path=str(receipt),sha256=sha(receipt)),source='own computed packing from the pinned primary input tree',licence='own computation on the recorded input terms')
 if sha(path)!=digest:raise ValueError('published copy changed while binding source')
 atomic(Path(str(path)+'.origin.json'),origin)
 return dict(origin=str(path)+'.origin.json',sha256=digest,source_proof=str(proof))

if __name__=='__main__':
 import tempfile
 receipt=W/'candidates/xcf549b53f021s3312.json';r=read(receipt)
 positive=tree(receipt);assert positive['snapshot_sha256']==r['output_sha256']
 try:tree(receipt,'0'*64)
 except ValueError:pass
 else:raise AssertionError('changed output pin accepted')
 with tempfile.TemporaryDirectory(dir=W) as td:
  changed=read(receipt);changed['job']['input_sha256']='0'*64;p=Path(td)/'bad-input.json';p.write_text(json.dumps(changed))
  try:tree(p)
  except ValueError:pass
  else:raise AssertionError('changed input pin accepted')
 print('PRIMARY_LINEAGE_CONTROL_PASS actual849 tree accepted; changed input/output pins refused')
