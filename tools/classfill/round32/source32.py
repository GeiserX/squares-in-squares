"""Import producer admission while keeping every writable cache in this lane."""
import sys,json,hashlib,csv
from pathlib import Path
W=Path(__file__).parent;sys.path.insert(0,str(W));import run32 as C
sys.path.insert(0,str(C.R));import forensics_round32 as F
cache=W/'fresh-source';cache.mkdir(exist_ok=True);F.prior.WORK=cache;F.public.WORK=cache
# Round32's extra refusal writer uses its producer WORK. The underlying check
# has identical admission semantics and writes only through the rebased prior.
F.prior.check_parts=F._check_parts32

def output_public(proof):return F.output_share_needed([proof])

def controls():
 version=C.sha(F.__file__);saved=C.read(W/'fresh-source-controls.json',{})
 if saved.get('producer_sha256')==version:return saved
 p=next((C.S/'take-forensics-r32/work/held-inputs').glob('*.csv'));n=int(p.stem.split('-')[0])
 ok,proof=F.queue_source_check(p,n,C.S,seconds=30);assert ok,(p,proof)
 bad=cache/'999-unrecorded-source-control.csv';bad.write_text('n,square_id,x,y,angle\n999,0,0.5,0.5,0\n999,1,1.5,0.5,0\n')
 no,reason=F.queue_source_check(bad,999,C.S,seconds=15);assert not no,reason
 assert not output_public(proof),'held export must retain the owned exemption'
 record=dict(producer=str(F.__file__),producer_sha256=version,positive=dict(path=str(p),n=n,passed=ok,proof=proof),negative=dict(path=str(bad),rejected=not no,reason=reason),held_share_exemption=True)
 C.atom(W/'fresh-source-controls.json',record);C.note('FRESH_SOURCE32_CONTROL_PASS current held projection accepted, unrecorded source refused, held ancestry exempt; all caches remain in classfill work/')
 print('SOURCE32_CONTROLS_PASS',p,reason.get('reason'),flush=True);return record
if __name__=='__main__':controls()
