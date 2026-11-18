from pathlib import Path
import sys,json
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp,legacy_credit,credit
from policy27 import banned,share
import source25
sys.path.insert(0,'.')
import quench_walk
p=W/'reopened/982-final-own-r25.csv';A=mlp.load(str(p),{982})[982]
c=legacy_credit(982,A,str(p));source25.retry_origin(str(p));a=source25.audit(c) if c else None
r={'legacy':bool(c),'origin_banned':banned(str(p)),'harvest':quench_walk.harvest_type(str(p),982),'share':share(982,A),'audit':bool(a),'credit':bool(credit(982,A,str(p))),'cached_positive':any(v is not None and v.get('origin')==str(p) for v in source25._cache.values())}
from publication_source26 import check
r['publication']=check(p,c)
for v in source25._cache.values():
 if v and v.get('origin')==str(p):
  r['banned_checked_paths']=[x for x in v.get('checked_paths',[]) if banned(x)]
(W/'old982-credit28.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
