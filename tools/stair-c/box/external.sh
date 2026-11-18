#!/bin/bash
set -e
cd "$(dirname "$0")"
name=$1
./py -I lane/zone_corner.py check "external/$name" > "logs/check-$name.log" 2>&1
./py -I lane/zone_corner.py merge libbase "external/$name" "lib-$name" --max-loss 8 > "logs/add-$name.log" 2>&1
./py -I - "$name" <<'PY'
import pickle,sys
name=sys.argv[1];p='lib-'+name+'/library.pkl';d=pickle.load(open(p,'rb'));ids={q['id'] for q in pickle.load(open('external/'+name+'/corners.pkl','rb'))}
for q in d['mods']:
 if q['id'] in ids:q['ours']=True
pickle.dump(d,open(p,'wb'));open('lib-'+name+'/need.txt','w').write('\n'.join(ids)+'\n')
PY
./py -I trim22.py "lib-$name" >> "logs/add-$name.log" 2>&1
./ranktail23.sh "lib-$name" "q-$name.tsv" > "logs/q-$name.log" 2>&1
printf '%s external ready %s\n' "$(date -u +%FT%TZ)" "$name" >> prep.log
