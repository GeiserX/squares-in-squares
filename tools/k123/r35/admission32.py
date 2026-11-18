"""Bind source admission to numeric bytes and the full publication walker."""
from pathlib import Path
import json,hashlib,functools,time,os
W=Path(__file__).resolve().parent;S=W.parent.parent
_pack={}
def matching(c):
 from provenance24 import mlp,key
 n=int(c['n']);want=c.get('sha256_geometry')
 candidates=[c.get('input_file_snapshot'),c.get('origin')]
 for name in ['round34-2026-11-17a.csv','round33-2026-11-17a.csv','round32-2026-11-16a.csv','round31-2026-11-16b.csv','round30-2026-11-15c.csv','round23-2026-11-13b.csv','round21-2026-11-13a.csv']:
  candidates.append(str(S/'gather'/name))
 for name in candidates:
  if not name:continue
  p=Path(name)
  if not p.is_file():continue
  st=p.stat();stamp=(str(p),st.st_mtime_ns,st.st_size)
  if stamp not in _pack:_pack[stamp]=mlp.load(str(p))
  A=_pack[stamp].get(n)
  if A is not None and (not want or key(n,A)==want):return A,str(p)
 return None,None
@functools.lru_cache(None)
def audit_text(text):
 from provenance24 import key
 from publication_source26 import check
 c={k:v for k,v in json.loads(text).items() if k not in {'checked_paths','admission_receipt'}}
 if not c or not c.get('n') or not c.get('source') or not c.get('licence'):return None
 A,original_path=matching(c)
 if A is None:return None
 n=int(c['n'])
 import re,walker30
 if walker30.harvest_type(original_path,n) and not is_current_held(n,A):
  licence=c['licence']
  approved=re.search(r'Apache[ -]?(?:License[ ,v]*)?2(?:\.0)?|CC[ -]?BY[ -]?4(?:\.0)?|CC0|Creative Commons Attribution 4',licence,re.I)
  disallowed=re.search(r'\bOther\b|ShareAlike|BY[ -]?SA|\bMIT\b',licence,re.I)
  if not approved or disallowed:
   with (W/'admission-refused32.jsonl').open('a') as f:f.write(json.dumps({'n':n,'origin':c.get('origin'),'hits':['public-first licence is outside Apache 2.0, CC BY 4.0 or CC0'],'licence':licence})+'\n')
   return None
 sha=hashlib.sha256(text.encode()).hexdigest();D=W/'admission-probes32'/sha;D.mkdir(parents=True,exist_ok=True);p=D/f'{n}.csv'
 if not p.exists():
  import csv
  with p.open('w') as f:
   wr=csv.writer(f);wr.writerow(['n','square_id','x','y','angle']);wr.writerows((n,i,*a) for i,a in enumerate(A))
 # The probe retains the exact producer context as a source edge.
 # Bind a copied held layout to its submitted row before walking its ancestry.
 from provenance24 import mlp
 held_round32=held_binding32(n,A)
 if held_round32 is not None:
  c={**c,'source':f'held n = {n} of round {held_round32}; start source: '+c['source']}
 row={'n':str(n),'source':c['source'],'licence':c['licence']}

 Path(str(p)+'.json').write_text(json.dumps(row))
 result=check(p,row)
 from diagnostic32 import write as write_diagnostic32
 write_diagnostic32(D/'admission-check32.json',result)
 if not result['clean']:
  with (W/'admission-refused32.jsonl').open('a') as f:f.write(json.dumps({'n':n,'origin':c.get('origin'),'hits':result.get('hits'),'receipt':str(D/'admission-check32.json')})+'\n')
  return None
 proof={'layout':c,'source':c['source'],'licence':c['licence']}
 raw=json.dumps(proof,separators=(',',':'));h=hashlib.sha256(raw.encode()).hexdigest();folder=W/'ancestry';folder.mkdir(exist_ok=True);out=folder/(h+'.json')
 if not out.exists():out.write_text(raw)
 return {**c,'source':f'licensed ancestry sha256 {h}; full source_record {out}','ancestry_file':str(out),'ancestry_sha256':h,'clean':True,'seed_share_gate':'v6','checked_paths':[p for p in __import__('walker30').LAST_VIA if isinstance(p,str) and Path(p).exists()]}

def held_binding32(n,A):
 from provenance24 import mlp,key
 # These two files are explicitly named as submitted held files in the brief.
 for round_number32,name32 in [(34,'round34-2026-11-17a.csv'),(33,'round33-2026-11-17a.csv'),(32,'round32-2026-11-16a.csv'),(31,'round31-2026-11-16b.csv'),(23,'round23-2026-11-13b.csv')]:
  p=S/'gather'/name32;stamp=(str(p),p.stat().st_mtime_ns,p.stat().st_size)
  if stamp not in _pack:_pack[stamp]=mlp.load(str(p))
  if n in _pack[stamp] and key(n,A)==key(n,_pack[stamp][n]):return round_number32
 return None

def is_current_held(n,A):
 return held_binding32(n,A) is not None
