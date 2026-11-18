#!/bin/sh
# slice19-mod.sh N ...: modules.py build for each N from the frozen library lib17, against the bars (process 2 of the lane).
cd "$(dirname "$0")"; B=$HOME/scratch/squares-base
for n in "$@"; do
  [ -e STOP ] && exit 0
  [ $(( $(cat deadline) - $(date +%s) )) -lt 120 ] && exit 0
  $B/venv/bin/python -I modules.py build lib17 run/mod bars-details.csv $n --top ${TOP:-3} --fq $B/fq --deadline deadline --slack ${SLACK:-2e-3} >> logs/slice19-mod.out 2>&1
done
echo "slice19-mod done $(date -u +%H:%M:%S)" >> logs/slice19-mod.out
