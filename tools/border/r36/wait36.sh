#!/bin/sh
# wait up to $1 s for a new kick result line in STATE.txt or a border-addressed handoff line; then print both
S=$SCRATCH/bounties-squares; T=$S/take-border-r36
k0=$(grep -cE "KICK [0-9]+ [0-9a-f]+m?r?[0-9]*: |SELF|certified" $T/STATE.txt); h0=$(wc -l < $S/handoff-r36.log); END=$(($(date +%s)+$1))
until [ $(date +%s) -ge $END ] || [ $(grep -cE "KICK [0-9]+ [0-9a-f]+m?r?[0-9]*: |SELF|certified" $T/STATE.txt) -gt $k0 ] || tail -n +$((h0+1)) $S/handoff-r36.log | grep -v "Z border -> " | grep -qE -- "-> *([a-z,]*,)?border|WITHDRAW|[Ww]ithdr|^[^ ]* main ->"; do sleep 15; done
date -u +%T; tail -n +$((h0+1)) $S/handoff-r36.log | grep -v "Z border -> " | grep -iE -- "-> *([a-z,]*,)?border|withdr|^[^ ]* main ->" | cut -c1-330
grep -E "KICK|CHAIN|SELF|DEEP|certified|ERROR|error" $T/STATE.txt | tail -n 4 | cut -c1-330
for p in driver kfeed36 deepfeed36 sfeed36 finish; do kill -0 $(cat $T/work/$p.pid) 2>/dev/null || echo "DEAD $p"; done
