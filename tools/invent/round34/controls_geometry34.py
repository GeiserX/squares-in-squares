import pathlib,sys,json,tempfile
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from held_geometry33 import resolve_record
import ancestry28 as A
S=W.parents[1]
p=S/'take-k123-r33/work/ancestry/083e67e16cd390a7caa16b0bf79616735499f8e087c0cdab4a72bc3ff78d4f15.json'
root=resolve_record(str(p));assert root,'real bare-origin held445 leaf must resolve'
old=S/'take-k123-r29/work/ancestry/f274cb9cac68d7bce677dd75bab1f7eb5b22d46e110fa25779afdd96f3314064.json'
assert resolve_record(str(old)),'round33 held259 control must still resolve'
with tempfile.TemporaryDirectory(dir=W)as d:
 q=pathlib.Path(d)/'wrong.json'
 for edit in ('hash','n','round','extra','source'):
  v=json.load(open(p))
  if edit=='hash':v['layout']['sha256_geometry']='0'*64
  if edit=='n':v['layout']['n']=446
  if edit=='round':v['source']=v['source'].replace('of round 32','of round 99');v['layout']['source']=v['source']
  if edit=='extra':v['parents']=['direct withdrawn file']
  if edit=='source':v['source']=v['source'].replace('held n = 445','held n = 446')
  q.write_text(json.dumps(v));assert resolve_record(str(q))is None,edit
a=A.audit(S/'take-forensics-r34/near/734-rect.csv',734);print('audit734',a.get('ok'),str(a.get('reason'))[:300])
result=dict(real_held445_bare_origin_passes=True,held259_still_passes=True,wrong_hash_count_round_parent_source_refused=True,audit734_ok=bool(a.get('ok')))
(W/'controls-geometry34.json').write_text(json.dumps(result));print(json.dumps(result))
