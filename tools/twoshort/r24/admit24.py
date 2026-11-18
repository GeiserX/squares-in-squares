"""Use recorded ancestry to distinguish new compositions from excluded old counts."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'.')
import forensics_sources as FS
from source24 import allowed,allowed_module
B=Path('$SCRATCH/bounties-squares');W=B/'take-twoshort-r24/work'
def trace_input(path,n):
 return FS.trace(Path(path),n,B)
def module_allowed(m):
 if allowed_module(m):return True
 source=m.get('src',m.get('source',''));lic=m.get('licence','')
 if not source or not lic or lic.startswith(('see ','unresolved')) or '-r24' not in source or not all(s in source for s in ['original_file','source_record']):return False
 try:
  parsed,_=json.JSONDecoder().raw_decode(source[source.index('{'):])
 except (ValueError,TypeError):return False
 if not isinstance(parsed,dict) or not all(k in parsed for k in ['A','B']):return False
 n=int(m.get('n',0))
 if n<=0:return False
 record=dict(source=source,licence=lic);digest=hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest();folder=W/'intake';folder.mkdir(exist_ok=True);p=folder/('module-record-'+digest[:20]+'.json');p.write_text(json.dumps(record))
 try:ok,proof=FS._trace(p,n,B,recorded=record)
 except (ValueError,OSError,KeyError,RecursionError):return False
 if ok:(folder/('module-proof-'+digest[:20]+'.json')).write_text(json.dumps(proof,indent=2))
 return ok
