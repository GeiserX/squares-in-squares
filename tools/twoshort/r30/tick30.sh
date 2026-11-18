#!/bin/zsh
# One supervision tick: liveness, newest boxE events, take rows, handoff lines for this lane.
W=$SCRATCH/bounties-squares/take-twoshort-r30/work; B=$SCRATCH/bounties-squares
date -u +%FT%TZ
ps -p $(cat $W/collector-pid) -o pid=,etime= || echo COLLECTOR DOWN
ps -p $(cat $W/qwalker-pid) -o pid=,etime= || echo QWALKER DOWN
ssh -o ConnectTimeout=20 boxE 'pgrep -f "worker30.py [12]" | wc -l; uptime; tail -6 $SCRATCH/squares-twoshort/worker.log | cut -c1-220'
cut -f1-4 $B/take-twoshort-r30/take.tsv
grep -E -- '-> (twoshort|all)' $B/handoff-r30.log | grep -v ' twoshort -> ' | tail -6 | cut -c1-300
grep -E 'COLLECT ERROR|SOURCE TRACE|KEEP|DROP|QUEUE' $B/take-twoshort-r30/STATE.txt | tail -6 | cut -c1-250
tail -3 $W/certify.log 2>/dev/null; tail -2 $W/prune-take.log 2>/dev/null; tail -3 $W/qwalker.log
