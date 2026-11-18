#!/bin/bash
set -e
cd "$(dirname "$0")"
pool=$1
out=$2
./py -I lane/stair-c_rank.py "$pool" "$out"
./py -I lane/stair-c_run.py jobs "$pool" "$out" raw-a details-r21.csv gap.tsv ./fq --max .008 --per 1 --done blog --source-key "$pool" --py ./py --lane lane >> q.txt
