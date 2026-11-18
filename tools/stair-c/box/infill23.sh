#!/bin/bash
set -e
cd "$(dirname "$0")"
f=$1
name=zip51f$f
./py -I lane/stair-c_infill.py carry ${ZIP_SOURCE:-external/zip51.pkl} corners/$name.pkl "$f" > logs/carry-$name.log 2>&1
./py -I - "$name" <<'PY'
import sys,pickle
b=pickle.load(open('corners/'+sys.argv[1]+'.pkl','rb'));sys.exit(0 if b else 1)
PY
mkdir -p z-$name/runs z-$name/zones
./py -I lane/zone_corner.py search corners/$name.pkl z-$name/runs --moves self,hop --counts 51 --minutes 4 --slot 180 --tail 20 --seed 23 --deadline deadline > logs/hop-$name.log 2>&1
./py -I lane/zone_corner.py table z-$name/runs z-$name/zones z-$name/zones.tsv --all --tag sc23 > logs/table-$name.log 2>&1
./py -I lane/zone_corner.py merge libbase z-$name/zones lib-$name --max-loss 8 > logs/add-$name.log 2>&1
./py -I lane/stair-c_run.py mark lib-$name z-$name >> logs/add-$name.log 2>&1
./py -I trim22.py lib-$name >> logs/add-$name.log 2>&1
./py -I lane/modules.py queue lib-$name details.csv q-$name.tsv --top 2 --slack .016 --need lib-$name/need.txt --depth .08 --ns ns-all.txt > logs/q-$name.log 2>&1
./py -I lane/stair-c_run.py jobs lib-$name q-$name.tsv raw-a details-r21.csv gap.tsv ./fq --max .014 --per 1 --done blog --source-key $name --py ./py --lane lane > jobs-$name.txt
cat jobs-$name.txt >> q.txt
printf '%s ready %s\n' "$(date -u +%FT%TZ)" "$name" >> prep.log
