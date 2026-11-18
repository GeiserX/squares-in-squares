"""Check byte-bound held cuts and the complete-graph freeze path."""
import sys,pathlib,json,tempfile,csv,shutil
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
import ancestry28 as A,source_gate28 as G,public_branch30 as B
from held32 import resolve,projection
from freeze_held32 import freeze
S=W.parents[1];p=S/'take-forensics-r32/near/970-rect.csv';proof=A.audit(p,970);assert proof['ok'],proof
saved=G.prv_share;share=B.P.share
G.prv_share=lambda *args:(_ for _ in()).throw(AssertionError('owned layout received share test'))
B.P.share=lambda *args:(_ for _ in()).throw(AssertionError('owned ancestor received share test'))
e=G.freeze(p,970,proof['proof']);assert e['clean'],e
G.prv_share=saved;B.P.share=share
held=S/'take-forensics-r32/work/held-inputs/971.csv';assert projection(held,971)
with tempfile.TemporaryDirectory(dir=W)as tmp:
 folder=pathlib.Path(tmp);wrong=folder/'971.csv';wrong.write_bytes(held.read_bytes());shutil.copyfile(str(held)+'.json',str(wrong)+'.json')
 rows=list(csv.DictReader(open(wrong)));rows[0]['x']=str(float(rows[0]['x'])+.001)
 with wrong.open('w',newline='')as f:
  out=csv.DictWriter(f,fieldnames=rows[0].keys());out.writeheader();out.writerows(rows)
 assert projection(wrong,971)is None
 # Even correcting a per-n hash cannot forge the coordinates of the held projection.
 import hashlib
 meta=json.load(open(str(wrong)+'.json'));meta['sha256']=hashlib.sha256(wrong.read_bytes()).hexdigest();pathlib.Path(str(wrong)+'.json').write_text(json.dumps(meta));assert projection(wrong,971)is None
 graph=json.load(open(proof['proof']));leaf=next(v for v in graph['nodes'].values()if not v.get('parents'));leaf['source']='public unverified/root :: fetched file';bad=folder/'bad.json';bad.write_text(json.dumps(graph));assert freeze(p,970,bad)is None
result=dict(actual970_held_graph_passes_without_share=True,changed_held_bytes_refused=True,forged_projection_hash_refused=True,nonheld_leaf_cannot_use_fast_freeze=True)
(W/'controls-held32.json').write_text(json.dumps(result));print(json.dumps(result))
