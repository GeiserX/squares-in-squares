#!/bin/zsh
S=$SCRATCH/bounties-squares; T=$S/take-border-r36; P="certified [0-9]+:|REJECT|Traceback|refused|raw find [0-9.]+ \(-[0-9.]+e-0[1-4]"
k0=$(grep -cE "$P" $T/STATE.txt); h0=$(wc -l < $S/handoff-r36.log); END=$(($(date +%s)+$1))
until [ $(date +%s) -ge $END ] || [ $(grep -cE "$P" $T/STATE.txt) -gt $k0 ] || tail -n +$((h0+1)) $S/handoff-r36.log | grep -v "Z border -> " | grep -qE -- "-> *border\b|WITHDRAW|^[^ ]* main ->"; do sleep 15; done
date -u +%T; tail -n +$((h0+1)) $S/handoff-r36.log | grep -v "Z border -> " | grep -E -- "-> *border\b|WITHDRAW|^[^ ]* main ->" | cut -c1-300
tail -n +1 $T/STATE.txt | grep -E "$P" | tail -n +$((k0+1)) | cut -c1-230
