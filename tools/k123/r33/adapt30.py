from pathlib import Path
import json
W=Path(__file__).resolve().parent;L=Path('.')
s=(L/'quench_walk.py').read_text().replace("LANE = os.path.dirname(os.path.abspath(__file__))",f"LANE = {str(L)!r}").replace('r2[2-9]','r[23][0-9]').replace("'QUENCH_LIVE_ROUND', '29'","'QUENCH_LIVE_ROUND', '31'").replace('2[2-8]|%s','2[2-9]|%s')
(W/'walker30.py').write_text(s)
for name in ['policy_walk27.py','publication_source26.py','policy27.py','provenance24.py']:
 p=W/name;s=p.read_text();s=s.replace('import quench_walk','import walker30 as quench_walk').replace('from quench_walk import *','from walker30 import *');p.write_text(s)
# The private policy adapter already applies two narrowly tested historical corrections.
# Use it for all entry points, including held-parent admission.
p=W/'policy_walk27.py';s=p.read_text();s+='\nfrom current_walk29 import configure\nconfigure(quench_walk)\n';p.write_text(s)
(W/'owned-helpers26.json').write_text(json.dumps([p.name for p in W.glob('*.py')]))
