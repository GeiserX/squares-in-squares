from pathlib import Path
import csv,json,sys
csv.field_size_limit(16000000)
W=Path(__file__).parent;B=W.parent.parent;sys.path.insert(0,str(W));sys.path.insert(0,str(W/'lane'));import floatsafe;from source24 import allowed,allowed_module
assert allowed('own near/793-harvest-793-61cf858e-s423.csv','our own')
assert not allowed('source n=639 from take-harvest-r22','our own')
assert not allowed_module(dict(id='639h.C',src='our own staircase',licence='our own'))
assert not allowed('penguin069/squares-joegun-boxed-certified-union','Apache 2.0')
rows=[{k:r[k] for k in ['n','square_id','x','y','angle']} for r in csv.DictReader(open(W.parent/'973.csv'))];n,fr,score,error=floatsafe.work((973,rows));held=next(float(r['score']) for r in csv.DictReader(open(B/'gate/cand-round23-1113a/details.csv')) if r['n']=='973');assert fr is not None and score<held-1e-10
bad=[dict(r) for r in rows]
for k in ['x','y','angle']:bad[1][k]=bad[0][k]
assert floatsafe.work((973,bad))[1] is None
out=dict(own_hash_accepted=True,excluded_count_rejected=True,excluded_id_rejected=True,excluded_root_rejected=True,known973_score=score,known973_gain=held-score,overlap_rejected=True)
(W/'control24.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
