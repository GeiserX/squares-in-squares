#!/bin/bash
set -e
cd "$(dirname "$0")"
name=$1
./py -I - "$name" <<'PY'
import pickle,sys
sys.path.insert(0,'lane');import modules as M
name=sys.argv[1];a=pickle.load(open('external/'+name+'/mods.pkl','rb'));L={q['id']:M.tabulate(q) for q in a}
pickle.dump(dict(mods=a,lens=L),open('patches/'+name+'.pkl','wb'))
PY
./patch22.sh "$name"
