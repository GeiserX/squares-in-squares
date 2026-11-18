import pathlib,sys,json,time
W=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import S,mlp,credit
from source25 import audit
from base25 import current
P,o=current();out={}
for n,p in [(581,S/'take-k123-r24/581.csv'),(735,S/'take-rebuild-r25/735.csv'),(982,S/'take-k123-r25/982.csv')]:
 t=time.time();A=mlp.load(str(p),{n})[n];c=credit(n,A,str(p));out[str(n)]={'accepted':bool(c),'seconds':time.time()-t}
assert out['581']['accepted'] and out['735']['accepted'] and not out['982']['accepted'],out
assert audit(dict(source='own derived from 921-29e12ff3.csv',licence='own',clean=True)) is None
print(json.dumps(out),flush=True);(W/'source-controls26.json').write_text(json.dumps(out))
