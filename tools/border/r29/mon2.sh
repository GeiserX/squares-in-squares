#!/bin/sh
# wait up to $1 s for a take change of ours, a line addressed to border, a main line, or a withdrawal naming our take; print a short status
S=$SCRATCH/bounties-squares; W=$S/take-border-r29/work
S0=$(wc -l < $S/handoff-r29.log); T0=$(md5 -q $S/take-border-r29/take.tsv); K0=$(grep -cE "BOUNDARY [0-9]+ b|KICK [0-9]+ [0-9a-f]+:|certified [0-9]+:" $S/take-border-r29/STATE.txt); END=$(($(date +%s)+$1))
until [ $(date +%s) -ge $END ] || [ "$(md5 -q $S/take-border-r29/take.tsv)" != "$T0" ] || [ "$(grep -cE "BOUNDARY [0-9]+ b|KICK [0-9]+ [0-9a-f]+:|certified [0-9]+:" $S/take-border-r29/STATE.txt)" != "$K0" ] || tail -n +$((S0+1)) $S/handoff-r29.log | grep -v "Z border -> " | grep -qE -- "-> *([a-z,]*,)?border[,:]|^[^ ]* main ->|(WITHDRAW|[Ww]ithdr|SOURCE-HOLD)[^\n]*take-border-r29"; do sleep 20; done
date -u +%T; tail -n +$((S0+1)) $S/handoff-r29.log | grep -v "Z border -> " | grep -E -- "-> *([a-z,]*,)?border[,:]|^[^ ]* main ->|(WITHDRAW|[Ww]ithdr|SOURCE-HOLD).*take-border-r29" | cut -c1-300
tail -n +2 $S/take-border-r29/take.tsv | cut -f1-4
grep -E "BOUNDARY [0-9]+ b|KICK [0-9]+ [0-9a-f]+:|certified [0-9]+:" $S/take-border-r29/STATE.txt | tail -n +$((K0+1)) | cut -c1-260
for p in driver lpfeed sfeed kfeed29 finish; do kill -0 $(cat $W/$p.pid) 2>/dev/null || echo "DEAD $p"; done
