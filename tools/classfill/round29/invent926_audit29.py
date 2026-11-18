"""Use the invent lane's imported reader with all new artifacts redirected here."""
from common29 import *
import importlib.util
upstream=S/'take-invent-r29/work';sys.path.insert(1,str(upstream))
spec=importlib.util.spec_from_file_location('classfill_imported_invent_ancestry29',upstream/'ancestry28.py');A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
A.W=W/'invent-adapter';(A.W/'ancestry').mkdir(parents=True,exist_ok=True)
# SeedPolicy caches stay inside this lane as well.
A.POL.t=A.W.parent;A.POL.w=A.W
proof=next((W/'ancestry').glob('8b39a44d89f4*.json'));a=read(proof);p=W/'inputs/926-x8b39a44d89f4.csv'
r=A.audit(p,926,src=a['source'],lic=a['licence'],record=str(proof));atomic(W/'926-invent-reader.json',r);note('IMPORTED_READER_926 '+json.dumps({k:v for k,v in r.items() if k not in ['source','licence']})[:1600]);print(json.dumps({k:v for k,v in r.items() if k not in ['source','licence']},indent=1),flush=True)
