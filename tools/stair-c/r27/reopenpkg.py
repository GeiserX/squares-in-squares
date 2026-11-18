"""Round 27 override 2: the states the round 26 Samanyu gate dropped sit in the merged
library, but the worker ranks only states that arrive in a package. Move them out of
libbase into priority packages (their tables included), one package per cut (C, F1, F2),
so each one is ranked over the box's targets first."""
import json,pickle,re,collections
from pathlib import Path
S=Path('$SCRATCH/bounties-squares');B=S/'take-stair-c-r27/work/box'
back=set(json.load(open(S/'take-stair-c-r27/work/base-audit.json'))['reopened'])
lib=pickle.load(open(B/'libbase/library.pkl','rb'));lens=pickle.load(open(B/'libbase/lens.pkl','rb'))
moved=[q for q in lib['mods'] if q['id'] in back]
lib['mods']=[q for q in lib['mods'] if q['id'] not in back]
groups=collections.OrderedDict()
for q in sorted(moved,key=lambda q:q['id']):groups.setdefault(re.sub(r'\.[^.]*$','',q['id']),[]).append(q)
for i,(g,qs) in enumerate(groups.items()):
    pickle.dump(dict(mods=[dict(q,ours=True) for q in qs],lens={q['id']:lens[q['id']] for q in qs if q['id'] in lens},origin='round27 reopened (Samanyu rule lifted)'),open(B/f'inbox/r27-priority-reopen-{i:03d}-{g}.pkl','wb'))
for q in moved:lens.pop(q['id'],None)
pickle.dump(lib,open(B/'libbase/library.pkl','wb'));pickle.dump(lens,open(B/'libbase/lens.pkl','wb'))
print('moved',len(moved),'states into',len(groups),'priority packages; library now',len(lib['mods']))
