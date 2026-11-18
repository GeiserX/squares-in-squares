#!/bin/bash
set -e
cd "$(dirname "$0")"
./py -I - <<'PY'
import pickle,sys
sys.path.insert(0,'lane');import zone_corner as Z
for q in pickle.load(open('patches/legacy52-newfar.pkl','rb'))['mods']:
 result=Z.check_corner(q);print('CONTROL legacy52',q['id'],q['count'],q['loss0'],result,flush=True);assert result[0] and q['count']==52
PY
./patch22.sh legacy52-newfar
