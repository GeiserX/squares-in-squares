#!/bin/bash
set -e
cd "$(dirname "$0")"
name=$1
./py -I lane/stair-c_run.py add libbase "lib-$name" "z-$name" "external/$name.pkl" --tag b23 --per-class 2 --within 1.5 --max-loss 8 > "logs/add-$name.log" 2>&1
./py -I trim22.py "lib-$name" >> "logs/add-$name.log" 2>&1
./ranktail23.sh "lib-$name" "q-$name.tsv" > "logs/q-$name.log" 2>&1
printf '%s base ready %s\n' "$(date -u +%FT%TZ)" "$name" >> prep.log
