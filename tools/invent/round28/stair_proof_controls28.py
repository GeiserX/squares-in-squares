"""Expand a hash-bound source record and refuse changed or missing proof records."""
import pathlib,sys,json,hashlib
W=pathlib.Path('$SCRATCH/bounties-squares/take-invent-r28/work');sys.path.insert(0,str(W))
import ancestry28 as A
proof=W/'stair-proof-control.json';proof.write_text(json.dumps(dict(source='own construction control907, original invent arm and plain rest',licence='our own construction')))
digest=hashlib.sha256(proof.read_bytes()).hexdigest();src='stair-c proof '+str(proof)+' immutable sha256 '+digest
p=W/'starts/control907.csv'
valid=A.audit(p,907,src,'our own construction');assert valid['ok'],valid
bad=A.audit(p,907,src.replace(digest,'0'*64),'our own construction');assert not bad['ok']and 'changed or missing compact source'in bad['reason']
missing=A.audit(p,907,src.replace(str(proof),str(W/'missing-stair-proof.json')),'our own construction');assert not missing['ok']
result=dict(hash_bound_source_expanded=True,wrong_hash_refused=True,missing_proof_refused=True,control_nodes=valid['nodes'])
(W/'stair-proof-controls.json').write_text(json.dumps(result));print(json.dumps(result))
