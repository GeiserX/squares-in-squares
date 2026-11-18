#!/bin/zsh
# One supervision tick: liveness, newest boxE events, take rows, handoff lines for this lane.
W=$SCRATCH/bounties-squares/take-twoshort-r26/work; B=$SCRATCH/bounties-squares
date -u +%FT%TZ
ps -p $(cat $W/collector-pid) -o pid=,etime= || echo COLLECTOR DOWN
ssh -o ConnectTimeout=20 boxE 'pgrep -f "squares-twoshort/worker26.py" | wc -l; uptime; tail -8 $SCRATCH/squares-twoshort/worker.log | cut -c1-200'
cut -f1-4 $B/take-twoshort-r26/take.tsv
grep -E -- '-> (twoshort|all): (BASE|.*twoshort)' $B/handoff-r26.log | grep -v '^.*twoshort -> ' | tail -5 | cut -c1-300
grep -E 'COLLECT ERROR|SOURCE TRACE|CERT|KEEP|DROP' $B/take-twoshort-r26/STATE.txt | tail -5 | cut -c1-300
tail -3 $W/certify.log; tail -2 $W/prune-take.log
