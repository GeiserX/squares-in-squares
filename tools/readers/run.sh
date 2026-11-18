#!/bin/zsh
setopt nullglob
cd $1
R=$2
PY=$PWD/venv/bin/python
export SQ_TMP=$PWD/tmp$R SQ_FQ=$PWD/fq SQ_APART=3e-2 SQ_TWIN=5.5e-2
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
mkdir -p tmp$R done out$R qz quench/raw
while (( $(date +%s) < $(cat deadline) )); do
  for g in qz/*.csv; do
    mkdir done/qz-${g:t:r} 2>/dev/null || continue
    echo "quench ${g:t} slot $R $(date -u +%H:%M:%S)" >> out$R/run.log
    nice -n 5 $PY -I -u quench.py quench $g >> out$R/quench.log 2>&1
  done
  f=''
  for g in q$R/*.tsv; do
    if [ ! -e done/$R-${g:t:r} ]; then f=$g; break; fi
  done
  if [ -z "$f" ]; then sleep 10; continue; fi
  b=${f:t:r}
  echo "start $b slot $R $(date -u +%H:%M:%S)" >> out$R/run.log
  maxsteps=6
  [[ $b == *-return ]] && maxsteps=2
  nice -n 5 $PY -I -u family_readers.py walk $f donors details.csv out$R --deadline deadline --misses 2 --min-progress 1e-7 --nearout 0.015 --maxsteps $maxsteps --beat beat/*.tsv >> out$R/walk.log 2>&1
  touch done/$R-$b
  echo "finish $b slot $R $(date -u +%H:%M:%S)" >> out$R/run.log
 done
 echo "end slot $R $(date -u +%H:%M:%S)" >> out$R/run.log
