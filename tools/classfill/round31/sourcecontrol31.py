import sys,json,shutil
sys.dont_write_bytecode=True
from pathlib import Path
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));import run31 as C
sys.path.insert(0,str(C.R));import forensics_round31 as F
cache=W/'fresh-source';F.prior.WORK=cache;F.public.WORK=cache
p=next((C.S/'take-forensics-r31/work/held-inputs').glob('*.csv'));n=int(p.stem)
ok,proof=F.queue_source_check(p,n,C.S,seconds=30)
assert ok,(p,proof)
bad=cache/'999-unrecorded-source-control.csv';bad.write_text('n,square_id,x,y,angle\n999,0,0.5,0.5,0\n999,1,1.5,0.5,0\n')
no,reason=F.queue_source_check(bad,999,C.S,seconds=15)
assert not no,reason
C.atom(W/'fresh-source-controls.json',dict(positive=dict(path=str(p),n=n,passed=ok,proof=proof),negative=dict(path=str(bad),rejected=not no,reason=reason)))
C.note('FRESH_SOURCE_CONTROL_PASS exact held projection '+str(p)+' accepted; unrecorded999 source refused '+str(reason.get('reason')))
print('SOURCE_CONTROLS_PASS',str(p),reason.get('reason'),flush=True)
