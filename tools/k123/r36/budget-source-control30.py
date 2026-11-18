from pathlib import Path
import sys,json,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from admission_budget30 import run
from provenance24 import mlp,legacy_credit
from source25 import audit_text
p=W.parent/'295.csv';c=legacy_credit(295,mlp.load(str(p),{295})[295],str(p));assert c
start=time.time();result=run(audit_text,json.dumps(c,sort_keys=True),'real295-budget-control',seconds=120);assert result and result.get('clean')
bad={**c,'source':'recorded input prvsiyan/squares-verified-best-of-1105','licence':'CC BY-SA 4.0'};assert not run(audit_text,json.dumps(bad,sort_keys=True),'excluded-budget-control',seconds=120)
r={'actual295_full_admission_passes':True,'excluded_publication_still_rejected':True,'seconds':time.time()-start};(W/'budget-source-control30.json').write_text(json.dumps(r));print(json.dumps(r),flush=True)
