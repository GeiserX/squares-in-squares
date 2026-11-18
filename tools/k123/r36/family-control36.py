from pathlib import Path
import sys,json
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from family_guard36 import refresh,job_family,family_key
closed=refresh();key='j22c-deferred3615fe75bf96x0-549-752-j15-14-s-3';item=job_family(key,597);assert item and item[0] in closed
assert family_key(597,item[1]['geometries'])==family_key(597,list(reversed(item[1]['geometries'])))
assert family_key(598,item[1]['geometries']) not in closed
assert family_key(597,[item[1]['geometries'][0],'changed-physical-geometry']) not in closed
r={'own597_family_closed':True,'input_order_independent':True,'another_count_eligible':True,'changed_geometry_eligible':True,'closed_total':len(closed)};(W/'family-control36.json').write_text(json.dumps(r));print(json.dumps(r))
