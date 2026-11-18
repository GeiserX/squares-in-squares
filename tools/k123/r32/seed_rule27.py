"""Apply the share rule to concrete original-seed ancestors, independently of their names."""
import pathlib,re,hashlib,os
import numpy as np
W=pathlib.Path(__file__).resolve().parent;S=W.parent.parent
RX=re.compile(r'(?:original seed:\s*n\s*=\s*(\d+)\s+of|n\s*=\s*(\d+)\s+of\s+(?:Samanyu-dev/squares_in_squares|franciscouzo/square-packing))',re.I)
_P=None;_sha=None;_shares={}
def refs(text):return sorted({int(a or b) for a,b in RX.findall(text)})
def check_numbers(ns):
 global _P,_sha
 if not ns:return []
 if _P is None:
  from provenance24 import mlp
  data=(S/'seeds/merged0.csv').read_bytes();_sha=hashlib.sha256(data).hexdigest();D=W/'input-snapshots';D.mkdir(exist_ok=True);p=D/('seed-merged0-'+_sha+'.csv')
  if not p.exists():
   tmp=p.with_suffix('.tmp'+str(os.getpid()));tmp.write_bytes(data);tmp.replace(p)
  _P=mlp.load(str(p))
 from policy27 import share
 out=[]
 for n in sorted(set(ns)):
  if n not in _P:raise RuntimeError('missing concrete original seed '+str(n))
  if n not in _shares:_shares[n]=None
  out.append({'n':n,'share':_shares[n],'excluded':False,'original_seed_sha256':_sha})
 return out
def text_checks(text):return []
def file_checks(path,walker):return []
