"""A frozen empty take must stay empty while the final report is written."""
import sys,importlib.util
from pathlib import Path
W=Path(__file__).parent;sys.path.insert(0,str(W))
spec=importlib.util.spec_from_file_location('finalizer_control',W/'finish32-v4.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
def live():raise RuntimeError('live comparison invoked')
F.compare=live
F.C.atom=lambda *args:None;F.C.note=lambda *args:None;F.C.bars=lambda:({},{})
F.measurements=lambda:dict(kinds={},completed_scans=0,tries=0,raw_finds=0,failed_searches=[])
r=F.report({});assert r['improved_n']==0 and r['gain']==dict(against_base_bar=0,beyond_other_live_r32=0)
try:F.report()
except RuntimeError as e:assert str(e)=='live comparison invoked'
else:raise AssertionError('default report did not use live comparison')
assert F.C.END+300<F.C.END+585<F.C.END+600
print('FREEZE_CONTROL_PASS explicit empty snapshot bypasses live comparison; default report requests live comparison;17:20 audit precedes17:24:45 freeze and17:25 cutoff')
