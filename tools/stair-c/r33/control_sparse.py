"""Check sparse continuation against the measured complete corner fixture."""
import hashlib,json,pickle,sys
from pathlib import Path
sys.path[:0]=['lane','.']
import numpy as np
import modules as M
import corner_guard as G
import corner_stacks as K
G.install();K.install()
from sparse_table import tabulate
f=pickle.load(open('control-fixture.pkl','rb'));q=next(q for q in f['mods']if q['kind']=='corner')
actual=tabulate(q);expected=f['lens'][q['id']]['tab'];keep=actual['sparse_grid_indices'];outside=np.setdiff1d(np.arange(len(M.GRID)),keep)
assert np.allclose(actual['tab'][:,:,keep],expected[:,:,keep],rtol=1e-10,atol=1e-11,equal_nan=True)
assert np.isnan(actual['tab'][:,:,outside]).all()
assert np.isfinite(actual['tab'][:,:,keep]).any()
mutant=actual['tab'].copy();mutant[:,:,keep]+=.01
assert not np.allclose(mutant[:,:,keep],expected[:,:,keep],rtol=1e-10,atol=1e-11,equal_nan=True)
Path('sparse-control.json').write_text(json.dumps(dict(passed=True,kept=len(keep),total=len(M.GRID),helper_sha256=hashlib.sha256(Path('sparse_table.py').read_bytes()).hexdigest())))
print('CONTROL sparse corner matches full975 fixture on',len(keep),'of',len(M.GRID),'grid points; outside NaN; changed table refused',flush=True)
