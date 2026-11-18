"""Read one versioned source entry and compare unchanged held rows."""
from pathlib import Path
import csv,json,re,hashlib,os
from functools import lru_cache
csv.field_size_limit(16000000)
W=Path(__file__).parent;B=W.parent.parent

def owner(p):return next((q.name for q in [Path(p),*Path(p).parents] if re.fullmatch(r'take-.+-r\d+',q.name)),None)
@lru_cache(maxsize=2)
def text_at(path,mtime,size):return Path(path).read_text()
def field_entry(path,field,key):
 p=Path(path);st=p.stat();text=text_at(str(p),st.st_mtime_ns,st.st_size);m=re.search('"'+field+r'"\s*:\s*\{',text)
 if not m:return None
 m2=re.search(r'(?<!\\)'+re.escape(json.dumps(key))+r'\s*:',text[m.end():])
 if not m2:return None
 at=m.end()+m2.end()
 while text[at].isspace():at+=1
 return json.JSONDecoder().raw_decode(text,at)[0]
def reader_credit(state,donor,sha):
 seen=field_entry(state,'seen',sha);credit=field_entry(state,'sources',donor)
 if not isinstance(seen,dict) or seen.get('donor')!=donor or not isinstance(credit,list) or len(credit)!=2:return None
 return credit

def row_hashes(path):
 out={}
 for r in csv.DictReader(open(path)):
  n=int(r['n']);h=out.setdefault(n,hashlib.sha256());text='|'.join([r['square_id']]+[repr(float(str(r[k]).lstrip('s'))) for k in ['x','y','angle']])+'\n';h.update(text.encode())
 return {str(n):h.hexdigest() for n,h in out.items()}
@lru_cache(maxsize=1001)
def held_same(n):
 if n is None:return False
 import subprocess,io
 a=B/'gather/round23-2026-11-13a.csv';b=B/'gather/round23-2026-11-13b.csv';values=[]
 for p in [a,b]:
  run=subprocess.run(['/usr/bin/grep','^'+str(int(n))+',',str(p)],capture_output=True,text=True,check=False)
  if run.returncode!=0:return False
  header=p.open().readline();rows=csv.DictReader(io.StringIO(header+run.stdout));values.append([(r['square_id'],*[float(str(r[k]).lstrip('s')) for k in ['x','y','angle']]) for r in rows])
 return bool(values[0]) and values[0]==values[1]
