#!/bin/sh
# wait up to $1 s for: a kick find, a certification, a leg, a reject, a border/main/withdraw handoff line, or a take change
S=$SCRATCH/bounties-squares; T=$S/take-border-r33
S0=$(wc -l < $T/STATE.txt); H0=$(wc -l < $S/handoff-r33.log); M0=$(md5 -q $T/take.tsv); END=$(($(date +%s)+$1))
until [ $(date +%s) -ge $END ] || tail -n +$((S0+1)) $T/STATE.txt | grep -qE "raw find [0-9.]+ \(-[0-9.]+e-0[1-8] |leg [0-9]+ queued|REJECT|Traceback|new seed" || tail -n +$((H0+1)) $S/handoff-r33.log | grep -v "Z border -> " | grep -v "WITHDRAW near exact" | grep -v "Z k123 -> " | grep -viE " claims? " | grep -qE -- "-> *([a-z, ]*,)?border|^[^ ]* main ->|take-border-r33"; do sleep 15; done
date -u +%T
tail -n +$((S0+1)) $T/STATE.txt | grep -vE "LP queue|no LP gain|KICK queue|no find below|queued certified-file fq|SELF " | cut -c1-260 | tail -14; echo "kicks done since: $(tail -n +$((S0+1)) $T/STATE.txt | grep -c "no find below\|raw find")"
echo "== handoff (border/main/withdraw):"; tail -n +$((H0+1)) $S/handoff-r33.log | grep -v "Z border -> " | grep -E -- "-> *([a-z, ]*,)?border|^[^ ]* main ->" | cut -c1-400
for p in driver kfeed33 deepfeed33 finish; do kill -0 $(cat $T/work/$p.pid) 2>/dev/null || echo "DEAD $p"; done
for f in driver kfeed33 deepfeed33; do tail -8 $T/work/$f.log | grep -E "Traceback|Error" | tail -2 | sed "s/^/$f: /"; done | cut -c1-200
