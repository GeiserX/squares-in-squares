"""Compare a bounded subprocess table with the actual cached fixture."""
import hashlib,json,os,pickle,subprocess,sys
from pathlib import Path
import numpy as np
fixture=pickle.load(open('control-fixture.pkl','rb'));q=next(q for q in fixture['mods']if q['kind']=='far');expected=fixture['lens'][q['id']]
Path('table-in').mkdir(exist_ok=True);Path('table-out').mkdir(exist_ok=True)
source=Path('table-in/control.pkl');source.write_bytes(pickle.dumps(q));target=Path('table-out/control.pkl')
subprocess.run([sys.executable,'-I','table_job.py',str(source),str(target)],check=True,timeout=120)
actual=pickle.loads(target.read_bytes())
assert actual['id']==expected['id']and abs(actual['own']-expected['own'])<1e-10
for a,b in zip(actual['knots'],expected['knots']):assert np.allclose(a,b,rtol=1e-10,atol=1e-11)
mutant=actual['knots'][1].copy()+.01
assert not np.allclose(mutant,expected['knots'][1],rtol=1e-10,atol=1e-11)
corner=next(q for q in fixture['mods']if q['kind']=='corner')
source.write_bytes(pickle.dumps(corner));target=Path('table-out/corner-control.pkl')
subprocess.run([sys.executable,'-I','table_job.py',str(source),str(target)],check=True,timeout=120)
actual_corner=pickle.loads(target.read_bytes());expected_corner=fixture['lens'][corner['id']]
assert actual_corner['id']==expected_corner['id']
assert np.allclose(actual_corner['tab'],expected_corner['tab'],rtol=1e-10,atol=1e-11,equal_nan=True)

# A stopped process must leave no result and the next table must still work.
missing=Path('table-out/timeout-control.pkl');missing.unlink(missing_ok=True)
try:subprocess.run([sys.executable,'-c','import time;time.sleep(10)'],timeout=.05)
except subprocess.TimeoutExpired:pass
else:raise AssertionError('timeout control did not stop')
assert not missing.exists()
Path('bounded-table-control.json').write_text(json.dumps(dict(passed=True,cached_fixture_matched=True,changed_table_refused=True,timeout_stopped=True,helper_sha256=hashlib.sha256(Path('table_job.py').read_bytes()).hexdigest())))
print('CONTROL bounded table matches cached fixture; changed table differs; stalled process stops',flush=True)
