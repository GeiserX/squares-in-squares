#!/bin/sh
# wait until epoch $1 for a raw find, a border-addressed handoff line, or a dead driver
S=$SCRATCH/bounties-squares; T=$S/take-border-r36
k0=$(grep -cE "raw find|certified fresh|SELF" $T/STATE.txt); h0=$(wc -l < $S/handoff-r36.log)
dead(){ for p in driver kfeed36 deepfeed36 sfeed36 finish; do kill -0 $(cat $T/work/$p.pid) 2>/dev/null || echo "DEAD $p"; done; }
until [ $(date +%s) -ge $1 ] || [ $(grep -cE "raw find|certified fresh|SELF" $T/STATE.txt) -gt $k0 ] || [ -n "$(dead)" ] || tail -n +$((h0+1)) $S/handoff-r36.log | grep -v "Z border -> " | grep -qE -- "-> *([a-z,]*,)?border[a-z,]*: *(hands|takes back|withdr|WITHDR)|WITHDRAW|[Ww]ithdr|^[^ ]* main -> *([a-z,]*,)?(all|border)"; do sleep 20; done
date -u +%T; dead; tail -n +$((h0+1)) $S/handoff-r36.log | grep -v "Z border -> " | grep -iE -- "-> *([a-z,]*,)?border|withdr|^[^ ]* main -> *([a-z,]*,)?(all|border)" | cut -c1-330
grep -E "KICK [0-9]+ [0-9a-f]+m?r?[0-9]*: |raw find|SELF|certified fresh" $T/STATE.txt | tail -n 6 | cut -c1-260
