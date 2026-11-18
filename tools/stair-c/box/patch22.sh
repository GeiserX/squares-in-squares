#!/bin/bash
set -e
cd "$(dirname "$0")"
name=$1
./py -I patch22.py "$name" > "logs/add-$name.log" 2>&1
./py -I trim22.py "lib-$name" >> "logs/add-$name.log" 2>&1
./ranktail23.sh "lib-$name" "q-$name.tsv" > "logs/q-$name.log" 2>&1
printf '%s patch ready %s\n' "$(date -u +%FT%TZ)" "$name" >> prep.log
