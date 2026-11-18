#!/bin/sh
# isl/long.sh N SRC: one long soft-box island (1800 s, delta 2e-4, seed 13, dry 360) from SRC; ends by ../deadline.
cd "$(dirname "$0")"
n=$1; src=$2; out=run/$n; left=$(( $(cat ../deadline) - $(date +%s) - 600 ))
s=1800; [ $left -lt $s ] && s=$left
echo "LONG n=$n delta=2e-4 seed=13 s=$s dry=360 src=$src $(date -u +%H:%M:%S)" >> run.log
nice -n 5 ../venv/bin/python -I methods_soft.py $src $out --n $n --delta 2e-4 --seed 13 --seconds $s --dry 360 >> run.log 2>&1
echo "LONGDONE n=$n $(date -u +%H:%M:%S)" >> run.log
