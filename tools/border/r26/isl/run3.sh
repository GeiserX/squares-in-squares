#!/bin/sh
# isl/run3.sh: two soft-box islands (140 s at delta 2e-4 seed 11, then 140 s at 1e-4 seed 12 from the best so far) on each
# endpoint in starts3/, one at a time; output run/<start name>/. Ends by ../deadline.
cd "$(dirname "$0")"
for f in starts3/*.csv; do
  t=$(basename $f .csv); n=$(echo $t | cut -d- -f1); out=run/$t; mkdir -p $out
  for leg in "2e-4 11" "1e-4 12"; do
    set -- $leg
    [ $(( $(cat ../deadline) - $(date +%s) )) -lt 600 ] && { echo "SKIP $t deadline" >> run.log; exit 0; }
    src=$f; b=$(ls -t $out/raw/$n-*.csv 2>/dev/null | head -1); [ -n "$b" ] && src=$b
    echo "LEG t=$t n=$n delta=$1 seed=$2 src=$src $(date -u +%H:%M:%S)" >> run.log
    nice -n 5 ../venv/bin/python -I methods_soft.py $src $out --n $n --delta $1 --seed $2 --seconds 140 --dry 0 >> run.log 2>&1
  done
done
echo "DONE3 $(date -u +%H:%M:%S)" >> run.log
