#!/bin/bash
cd "$(dirname "$0")"
export SQ_FQ=$PWD/fq SQ_BOX=$PWD/box OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
mkdir -p blog cert-in final
while :; do
  [ -e STOP ] && exit 0
  [ $(date -u +%s) -gt $(cat deadline) ] && exit 0
  ran=0
  while read -r name cmd; do
    [ -z "$name" ] && continue
    [ -e blog/$name.lock ] && continue
    ( set -C; : > blog/$name.lock ) 2>/dev/null || continue
    echo "$(date -u +%H:%M:%S) start $name ($1)" >> worker.log
    nice -n 5 ./py -I guard.py $cmd > blog/$name.log 2>&1 < /dev/null
    echo "$(date -u +%H:%M:%S) end $name rc $?" >> worker.log
    ran=1; break
  done < "$1"
  [ $ran = 0 ] && sleep 10
done
