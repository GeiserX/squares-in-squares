from pathlib import Path
import sys,csv,json,time,signal,faulthandler
faulthandler.register(signal.SIGUSR1,all_threads=True)
W=Path(__file__).resolve().parent;S=W.parent.parent;sys.path[:0]=[str(W),str(W/'lane')];csv.field_size_limit(1<<28)
import provenance24 as p
from admission32 import audit_text
results=[]
for n,origin in [(985,S/'take-k123-r29/985.csv'),(864,S/'take-border-r31/864.csv'),(646,S/'take-backlog-r31/646.csv')]:
 A=p.mlp.load(str(origin),{n})[n];c=p.legacy_credit(n,A,str(origin));t=time.time();r=audit_text(json.dumps(c));results.append({'n':n,'accepted':bool(r),'seconds':time.time()-t});assert r,results
bad={**c,'source':'recorded input prvsiyan/squares-verified-best-of-1105','licence':'CC BY-SA 4.0'};assert audit_text(json.dumps(bad)) is None
print(json.dumps(results),flush=True);(W/'admission-control32.json').write_text(json.dumps(results))
