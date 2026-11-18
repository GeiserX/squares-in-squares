import csv,json,math,sys
from pathlib import Path
sys.path.insert(0,str(Path('lane').resolve()))
import finesafe as fs
import floatsafe as base
rows=[dict(n='2',square_id='0',x='0.5',y='0.5',angle='0.0'),dict(n='2',square_id='1',x='1.5',y='0.5',angle='0.0')]
a=base.work((2,rows));b=fs.work((2,rows))
assert b[1] is not None and b[2]<=a[2]
assert base.clearance(b[1])>=base.MIN_CLEARANCE
assert base.clearance(base.via_pandas(b[1]))>=base.MIN_CLEARANCE
bad=[dict(r) for r in rows];bad[1]['x']='0.6'
assert fs.work((2,bad))[1] is None
print(json.dumps(dict(passed=True,ladder_side=(1+a[2])*math.sqrt(2),fine_side=(1+b[2])*math.sqrt(2),clearance=base.clearance(b[1]),pandas_clearance=base.clearance(base.via_pandas(b[1])),bad_overlap='refused')))
