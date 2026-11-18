from pathlib import Path
import sys,json,hashlib
W=Path(__file__).resolve().parent;S=W.parent.parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp,key
import admission32
p=S/'take-harvest-r22/work/collector/certified/52c2828aaa9bb34a242993b087e32c929e345b516309882921072b62a2365102.csv';A=mlp.load(str(p),{551})[551]
c={'n':551,'origin':str(p),'source':'kmmmvs/squares-public-merge-daily :: submission.csv; public-first '+str(p),'licence':'MIT','sha256_geometry':key(551,A),'clean':True}
assert not admission32.is_current_held(551,A)
r=admission32.audit_text(json.dumps(c));assert r is None
last=json.loads((W/'admission-refused32.jsonl').read_text().splitlines()[-1]);assert 'licence is outside' in last['hits'][0]
(W/'licence-control32.json').write_text(json.dumps({'public_mit_rejected_by_licence':True,'n':551}));print('public MIT control rejected by licence before share',flush=True)
