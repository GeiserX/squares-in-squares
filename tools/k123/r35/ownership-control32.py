from pathlib import Path
import sys,json,csv
W=Path(__file__).resolve().parent;S=W.parent.parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp
from family_step import write_rows
import walker30
A=mlp.load(str(S/'seeds/merged0.csv'),{503})[503];D=W/'ownership-control32';D.mkdir(exist_ok=True);p=D/'503.csv';write_rows(str(p),503,A)
Path(str(p)+'.json').write_text(json.dumps({'n':503,'source':'original seed: n = 503 of Samanyu-dev/squares_in_squares; own independently discovered packing; seeds/merged0.csv','licence':'own'}))
def refuse_share(*a,**k):raise AssertionError('share called on an own root')
walker30.prv_share=refuse_share;walker30.pol_fail=refuse_share
r=walker30.check(str(p));assert r['clean'],r
print('own503 control passed without a share measurement',flush=True)
(W/'ownership-control32.json').write_text(json.dumps({'own503_clean':True,'share_calls':0}))
