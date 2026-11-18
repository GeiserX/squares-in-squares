#!/bin/sh
# r35: as mon.sh, but a certificate line of another class (n mod 4 != 0) addressed to border does not end the wait
S=$SCRATCH/bounties-squares; W=$S/take-border-r35/work
S0=$(wc -l < $S/handoff-r35.log); T0=$(md5 -q $S/take-border-r35/take.tsv); END=$(($(date +%s)+$1))
hit() { tail -n +$((S0+1)) $S/handoff-r35.log | grep -v "Z border -> " | grep -E -- "-> *([a-z,]*,)?border|WITHDRAW|[Ww]ithdr|REINSTATE|REOPEN|SOURCE-HOLD|take-border-r35|^[^ ]* main ->" | awk '{ if (match($0,/certified n=[0-9]+/)) { n=substr($0,RSTART+12,RLENGTH-12)+0; if (n%4!=0) next } print }'; }
until [ $(date +%s) -ge $END ] || [ "$(md5 -q $S/take-border-r35/take.tsv)" != "$T0" ] || [ -n "$(hit)" ]; do sleep 20; done
echo "== new lines:"; hit | cut -c1-300
date -u +%T; for p in driver kfeed35 deepfeed35 finish; do kill -0 $(cat $W/$p.pid) 2>/dev/null || echo "DEAD $p"; done
ssh boxC 'ps -ax -o pid,command | grep "squares-border-r35" | grep "worker.py [12]" | grep -v grep | grep -c .' 2>/dev/null | sed 's/^/boxC border workers: /'
echo "take rows: $(tail -n +2 $S/take-border-r35/take.tsv | cut -f1 | tr '\n' ' ')"
for t in $S/take-*-r35/take.tsv; do n=$(tail -n +2 $t | wc -l | tr -d ' '); [ "$n" -gt 0 ] && echo "TAKE $(basename $(dirname $t)) $n: $(tail -n +2 $t | cut -f1 | tr '\n' ' ')"; done
grep -E 'KICK [0-9]+ [0-9a-z]+: (raw|no)|CLAIM lost|WORKERS boxC|KICK stop|certified [0-9]|DEEP skip|error' $S/take-border-r35/STATE.txt | tail -n +${2:-1} | tail -6 | cut -c1-200
