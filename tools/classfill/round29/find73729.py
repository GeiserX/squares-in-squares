from common29 import *
import numpy as np
sys.path.insert(0,str(R))
import forensics_compose as fc
from light29 import load
origin=S/'take-forensics-r22/work/donors/737-fbd76ef9ba3df12b7c1f.csv'
target=read(str(origin)+'.origin.json')['digest'];matches=[];seen=set();count=0;began=time.time()
paths=[Path(p) for p in (W/'737-candidates.txt').read_text().splitlines()]
paths.sort(key=lambda p:(0 if 'take-forensics-r22/' in str(p) else 1,len(str(p))))
for p in paths:
 if time.time()-began>90:break
 sha=hashlib.sha256(p.read_bytes()).hexdigest()
 if sha in seen:continue
 seen.add(sha)
 try:a=load(str(p),{737})[737];_,a=fc.frame(np.array(a));digest=hashlib.sha256(np.round(a,12).tobytes()).hexdigest()
 except Exception:continue
 count+=1
 if digest==target:matches.append(dict(path=str(p),sha256=sha,origin=Path(str(p)+'.origin.json').exists(),sidecars=[str(q) for q in [p.with_suffix('.json'),Path(str(p)+'.json')] if q.exists()]));print('MATCH',matches[-1],flush=True)
atomic(W/'737-source-matches.json',dict(time=now(),checked=count,unique=len(seen),matches=matches));print('DONE',count,len(matches),flush=True)
