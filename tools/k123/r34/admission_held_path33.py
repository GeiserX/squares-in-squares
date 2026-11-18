"""Check the full admission stack on the shared held-path positive control."""
from pathlib import Path
import os,sys,time,json
W=Path(__file__).resolve().parent;S=W.parent.parent;sys.path[:0]=[str(W),str(W/'lane')]
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
from provenance24 import credit,mlp
from source25 import audit
p=S/'take-forensics-r33/near/911-rect.csv';t=time.time();A=mlp.load(str(p),{911})[911];c=credit(911,A,str(p));out={'path':str(p),'accepted':c is not None,'seconds':time.time()-t,'source':c.get('source','')[:350] if c else ''}
(W/'admission-held-path33.json').write_text(json.dumps(out,indent=2));print(json.dumps(out));assert c is not None,'full admission still refused the held-path positive control'
