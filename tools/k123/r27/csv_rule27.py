"""Check complete per-n CSV ancestors; partial module files are checked through their source layouts."""
import pathlib,csv,hashlib
import numpy as np
_cache={}
def one(path):
 p=pathlib.Path(path)
 if not p.is_file() or p.suffix!='.csv' or any(x in str(p) for x in ['/lib','/parts/','/cuts/']):return None
 st=p.stat();key=(str(p),st.st_mtime_ns,st.st_size)
 if key in _cache:return _cache[key]
 result=None
 try:
  rows=[];n=None
  for row in csv.DictReader(open(p)):
   if 'n' not in row or not all(k in row for k in ['x','y','angle']):break
   nn=int(row['n'])
   if n is None:n=nn
   elif n!=nn:break
   rows.append(row)
  else:
   if n is not None and len(rows)==n:
    from policy27 import share
    A=np.array([[float(r[k]) for k in ['x','y','angle']] for r in rows]);s=share(n,A)
    result={'n':n,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'share':s,'excluded':s>=.4}
 except (ValueError,KeyError,OSError):pass
 _cache[key]=result;return result
def file_checks(path,walker):
 n=int(next(csv.DictReader(open(path)))['n']);_,_,seen,_,_=walker.walk(str(path),n)
 return [z for p in sorted(seen) if (z:=one(p)) is not None]
