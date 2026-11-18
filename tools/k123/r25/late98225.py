"""Rescan the changed 982 return using an already pinned licensed class pool."""
import json,time
from provenance24 import W,S,mlp,credit
from stage24 import stage
D=W/'fresh10218';P=mlp.load(str(D/'fresh10218.csv'));manifest=json.load(open(D/'sources-fresh10218.json'));orig={int(n):c['origin'] for n,c in manifest.items()};old=P[982].copy();p=W.parent/'982.csv';P[982]=mlp.load(str(p),{982})[982];orig[982]=str(p)
assert credit(982,P[982],str(p))
assert mlp.side(P[982])<mlp.side(old)-1e-9
pairs=[(982,n) for n in P]
print('CHANGED INPUT982 side',mlp.side(old),'->',mlp.side(P[982]),'partners',len(pairs),flush=True)
stage('fresh20000',P,orig,pairs,'fresh-changed982','new certified982 return; pinned class partners from fresh10218')
