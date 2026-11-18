#!/bin/sh
# worker.sh QUEUE OUT: run the lines of QUEUE one after another until ./deadline (epoch seconds) passes.
# A line is: scan N SUB SECONDS SEED MODES REF      (midm_scan.py; REF 0 = none)
#        or: walk N SUB SECONDS SEED MODES T        (midm_scan.py --walk T: the kicks walk between basins)
#        or: soft N SUB SECONDS SEED START DELTA    (methods_soft.py --dry 150; START best, drop1 or drop2)
#        or: seed N SUB SECONDS SEED KINDS DELTA    (midm_soft.py; on a find, methods_soft.py goes on from it)
#        or: sq N SUB SECONDS SEED MODE REF         (midm_sqpack.py; MODE local, drop or grow)
#        or: ftmc N SUB SECONDS SEED - REF          (midm_ftmc.py)
# With CLAIM=DIR several workers share one queue: a worker takes a line only when it can make DIR/<kind>-<n>-<seed>.
# BASE is the shared venv and fq on the box. Nothing here certifies: methods_take.py does, on boxA.
D=$(cd "$(dirname "$0")" && pwd); cd "$D"
BASE=${BASE:-$HOME/scratch/squares-base}
q=$1; out=$2; mkdir -p "$out"
while read kind n sub secs seed a b; do
  [ -z "$kind" ] && continue
  [ -e STOP ] && exit 0
  left=$(( $(cat deadline) - $(date +%s) ))
  [ $left -lt 60 ] && exit 0
  if [ -n "$CLAIM" ]; then mkdir -p "$CLAIM"; mkdir "$CLAIM/$kind-$n-$seed" 2>/dev/null || continue; fi
  [ $left -lt $secs ] && secs=$((left - 20))
  if [ "$kind" = scan ]; then
    "$BASE/venv/bin/python" midm_scan.py --n $n --sub $sub --out "$out" --fq "$BASE/fq" --seconds $secs --seed $seed --modes $a --ref $b --deadline deadline >> "$out/worker.log" 2>&1
  elif [ "$kind" = walk ]; then
    "$BASE/venv/bin/python" midm_scan.py --n $n --sub $sub --out "$out" --fq "$BASE/fq" --seconds $secs --seed $seed --modes $a --walk $b --deadline deadline >> "$out/worker.log" 2>&1
  elif [ "$kind" = seed ]; then
    "$BASE/venv/bin/python" midm_soft.py --n $n --sub $sub --out "$out" --seconds $secs --seed $seed --kinds $a --delta $b --deadline deadline >> "$out/worker.log" 2>&1
    f="$out/raw/$n-seed-$seed.csv"
    if [ -e "$f" ] && [ ! -e NOCHAIN ]; then
      "$BASE/venv/bin/python" methods_soft.py "$f" "$out/chain" --n $n --seconds 900 --seed $seed --start best --delta 2e-4 --dry 150 >> "$out/worker.log" 2>&1
    fi
  elif [ "$kind" = sq ]; then
    "$BASE/venv/bin/python" midm_sqpack.py --n $n --sub $sub --out "$out" --sqpack ./sqpack --mode $a --seconds $secs --seed $seed --ref $b >> "$out/worker.log" 2>&1
  elif [ "$kind" = ftmc ]; then
    "$BASE/venv/bin/python" midm_ftmc.py --n $n --sub $sub --out "$out" --ftmc ./ftmc --seconds $secs --seed $seed --ref $b >> "$out/worker.log" 2>&1
  else
    "$BASE/venv/bin/python" methods_soft.py $sub "$out/soft-$a" --n $n --seconds $secs --seed $seed --start $a --delta $b --dry 150 >> "$out/worker.log" 2>&1
  fi
done < "$q"
