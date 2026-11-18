import pathlib,sys,json,tempfile,copy
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from held_geometry33 import resolve_record
p=W.parents[1]/'take-k123-r29/work/ancestry/f274cb9cac68d7bce677dd75bab1f7eb5b22d46e110fa25779afdd96f3314064.json'
root=resolve_record(str(p));assert root, 'real n259 held catalogue must resolve'
with tempfile.TemporaryDirectory(dir=W)as d:
 q=pathlib.Path(d)/'wrong.json';v=json.load(open(p));v['layout']['sha256_geometry']='0'*64;q.write_text(json.dumps(v));assert resolve_record(q)is None
 v=json.load(open(p));v['layout']['n']=260;q.write_text(json.dumps(v));assert resolve_record(q)is None
 v=json.load(open(p));v['parents']=['direct withdrawn file'];q.write_text(json.dumps(v));assert resolve_record(q)is None
result=dict(real_held259_geometry_passes=True,wrong_geometry_hash_refused=True,wrong_count_refused=True,mixed_parent_record_refused=True)
(W/'controls-geometry33.json').write_text(json.dumps(result));print(json.dumps(result))
