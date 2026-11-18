#!/bin/bash
# wait until boxE worker log (mirror) gains a run that moved 1e-8 of side or more, a QUENCH, ERROR or FAIL line,
# or our STATE gains a CERT, PRUNE, ERROR or a non-claim INBOX line
L=$SCRATCH/bounties-squares/take-twoshort-r31/work/boxE31/worker.log
S=$SCRATCH/bounties-squares/take-twoshort-r31/STATE.txt
n0=$(wc -l < $L); s0=$(wc -l < $S)
while true; do
  sleep 30
  new=$(tail -n +$((n0+1)) $L | awk '/QUENCH|ERROR|FAIL/{print;next} /DONE/{for(i=1;i<=NF;i++) if($i=="moved" && $(i+1)+0>=1e-8) print}')
  st=$(tail -n +$((s0+1)) $S | grep -E 'CERT n=|INBOX|ERROR|PRUNE' | grep -v 'INBOX.*claim')
  if [ -n "$new$st" ]; then echo "$new"; echo "$st"; date -u +%T; exit 0; fi
done
