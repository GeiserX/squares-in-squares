"""Check source-record pins separately from byte-hash pins."""
from pathlib import Path
import hashlib,json,sys,os
W=Path(__file__).parent;sys.path.insert(0,str(W));import admit25 as A
p=W/'pin-control/1.csv';p.parent.mkdir(exist_ok=True);p.write_text('n,square_id,x,y,angle\n1,0,0,0,0\n');q=p.with_suffix('.json');clean=dict(source='our own design',licence='our own');q.write_text(json.dumps(clean))
rec,_=A.FS.record(p,1);pin=dict(path=str(p),n=1,sha256=hashlib.sha256(json.dumps(rec,sort_keys=True).encode()).hexdigest());byte=A.stamp(p)
record=dict(source='our own design',licence='our own',ancestry=dict(closure=dict(records=[byte],metadata_records=[pin])))
ok,detail=A.walk(record,n=1);assert ok,detail
q.write_text(json.dumps(dict(source='changed source',licence='unlicensed')));bad,detail=A.walk(record,n=1);assert not bad and any(e[1]=='pinned ancestor metadata differs' for e in detail['errors'])
q.write_text(json.dumps(clean));p.write_text(p.read_text()+'\n');badbyte,detail=A.walk(record,n=1);assert not badbyte and any(e[1]=='pinned ancestor hash differs' for e in detail['errors'])
result=dict(selected_metadata_pin_passes=ok,changed_metadata_refused=not bad,changed_bytes_refused=not badbyte);(W/'hash-schema-control.json').write_text(json.dumps(result,indent=2));print(result,flush=True);os._exit(0)
