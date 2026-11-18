"""Exercise final admission with a real certified-input fq receipt."""
import csv
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
import finalize as F
import walk as Q
from policy import control
from pins import control as pins_control

control();pins_control();Q.control()
# Reloading the adapter must preserve the original withdrawal loader.
import importlib
importlib.reload(Q);importlib.reload(Q);Q.load_withdrawn()
print('CONTROL repeated source-adapter reload does not recurse',flush=True)
rows=F.table(F.T/'take.tsv')
if not rows:raise SystemExit('real receipt control pending: take empty')
r=rows[0];n=int(r['n'])
jobs=[json.loads(p.read_text()) for p in (F.W/'jobs').glob('*.json')]
j=next(j for j in jobs if F.job_matches(r,j))
with tempfile.TemporaryDirectory(dir=F.W) as d:
    real=F.T;F.T=Path(d)
    (F.T/(str(n)+'.csv')).write_bytes((real/(str(n)+'.csv')).read_bytes())
    assert F.allowed(r,j,{n:float(r['new'])+1e-6})
    try:F.allowed(r,j,{n:float(r['new'])-1e-6})
    except ValueError:pass
    else:raise AssertionError('lower peer did not reject')
    p=F.T/(str(n)+'.csv');p.write_bytes(p.read_bytes()+b'\n')
    try:F.allowed(r,j,{n:float(r['new'])+1e-6})
    except ValueError:pass
    else:raise AssertionError('changed certificate did not reject')
    F.T=real
print('CONTROL actual certificate retained; lower peer and changed certificate bytes rejected',flush=True)
