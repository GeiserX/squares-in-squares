from pathlib import Path
import sys,json,hashlib
W=Path(__file__).resolve().parent
sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp,legacy_credit
import source25
p=W/'reopened/982-final-own-r25.csv'
A=mlp.load(str(p),{982})[982];c=legacy_credit(982,A,str(p));assert c
raw=json.dumps({'source':c['source'],'licence':c['licence']},separators=(',',':'))
proof=W/'retry-control28/ancestry'/(hashlib.sha256(raw.encode()).hexdigest()+'.json');proof.parent.mkdir(parents=True,exist_ok=True)
proof.unlink(missing_ok=True)
cc={**c,'origin':str(W/'retry-control28/982.csv'),'source':c['source']+'; required source_record '+str(proof)}
source25.audit_text.cache_clear();source25._cache={}
missing=source25.audit(cc)
assert missing is None
proof.write_text(raw)
stale=source25.audit(cc)
assert stale is None
source25.retry_origin(cc['origin']);repaired=source25.audit(cc)
assert repaired
result={'missing_proof_accepted':bool(missing),'repaired_before_explicit_retry_accepted':bool(stale),'repaired_after_explicit_retry_accepted':bool(repaired),'proof':str(proof)}
(W/'retry-controls28.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
