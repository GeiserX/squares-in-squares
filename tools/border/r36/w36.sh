#!/bin/zsh
# wait up to $1 s for a new border event (kick result, certified, leg, refused) or a handoff line naming border/main
S=$SCRATCH/bounties-squares; T=$S/take-border-r36
k0=$(grep -cE "certified [0-9]+:|refused|Traceback|REJECT|DFEED skip|WORKERS" $T/STATE.txt); h0=$(wc -l < $S/handoff-r36.log); END=$(($(date +%s)+$1))
until [ $(date +%s) -ge $END ] || [ $(grep -cE "certified [0-9]+:|refused|Traceback|REJECT|DFEED skip|WORKERS" $T/STATE.txt) -gt $k0 ] || tail -n +$((h0+1)) $S/handoff-r36.log | grep -v "Z border -> " | grep -qiE -- "-> *border\b|WITHDRAW|^[^ ]* main ->"; do sleep 15; done
date -u +%T; tail -n +$((h0+1)) $S/handoff-r36.log | grep -v "Z border -> " | grep -v "certified near donor" | grep -iE -- "-> *border|withdr|^[^ ]* main ->|certified" | cut -c1-300
grep -E "KICK [0-9]+ [0-9a-f]+: |certified |CHAIN|refused|Traceback|DFEED|CLAIM" $T/STATE.txt | tail -4 | cut -c1-230
