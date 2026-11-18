import pathlib,sys,json,tempfile,hashlib
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
import ancestry28 as A,source_gate28 as G,public_branch30 as B
from freeze_held32 import freeze
p=W.parents[1]/'take-forensics-r33/near/789-rect.csv';proof=A.audit(p,789);assert proof['ok'],proof
old=G.prv_share;branch=B.P.share
G.prv_share=lambda *a:(_ for _ in()).throw(AssertionError('own input shared'))
B.P.share=lambda *a:(_ for _ in()).throw(AssertionError('own ancestor shared'))
e=G.freeze(p,789,proof['proof']);assert e['clean'],e
assert G.check(dict(id='mixed-owned33-control',n=789,ancestry=proof['proof'],evidence=e['path'],evidence_sha256=e['sha256']),p)['clean']
with tempfile.TemporaryDirectory(dir=W)as tmp:
 bad=pathlib.Path(tmp)/'bad.json';graph=json.load(open(proof['proof']));leaf=next(v for v in graph['nodes'].values()if v['source'].startswith('our own design; direct original'))
 leaf['source']=leaf['source'].replace('sha256 ', 'sha256 0');bad.write_text(json.dumps(graph));assert freeze(p,789,bad)is None
G.prv_share=old;B.P.share=branch
result=dict(actual789_held_and_original_seed_closure_passes=True,own_layout_no_share=True,wrong_seed_hash_refused=True)
(W/'controls-freeze33.json').write_text(json.dumps(result));print(json.dumps(result))
