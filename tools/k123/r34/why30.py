from pathlib import Path
import sys,json
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp,legacy_credit
p=sys.argv[1];n=int(sys.argv[2]);c=legacy_credit(n,mlp.load(p,{n})[n],p)
if not c:print('legacy failed');raise SystemExit
s=(W/'source25.py').read_text()
s='\n'.join(l.replace('return None',f'return _refuse({i+1},locals())') for i,l in enumerate(s.splitlines()))
def refuse(i,vars):
 print('REFUSE',i,{k: str(vars[k])[:300] for k in ['bare','pp','name','p','pinned_path','have'] if k in vars},flush=True)
 (W/f'why{n}-{i}.json').write_text(json.dumps({k:str(v) for k,v in vars.items()},indent=2))
 return None
ns={'__name__':'diagnostic30','_refuse':refuse};exec(s,ns);print('accepted',bool(ns['audit_text'](json.dumps(c))),flush=True)
