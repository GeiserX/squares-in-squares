#!/bin/sh
# wait up to $1 s for a take change, a border-addressed or WITHDRAW/REINSTATE handoff line; then print a status
S=$SCRATCH/bounties-squares; W=$S/take-border-r34/work
S0=$(wc -l < $S/handoff-r34.log); T0=$(md5 -q $S/take-border-r34/take.tsv); END=$(($(date +%s)+$1))
until [ $(date +%s) -ge $END ] || [ "$(md5 -q $S/take-border-r34/take.tsv)" != "$T0" ] || tail -n +$((S0+1)) $S/handoff-r34.log | grep -v "Z border -> " | grep -qE -- "-> *([a-z,]*,)?border|WITHDRAW|[Ww]ithdr|REINSTATE|REOPEN|SOURCE-HOLD|take-border-r34"; do sleep 20; done
echo "== new handoff lines (border, withdraw, reinstate, main):"; tail -n +$((S0+1)) $S/handoff-r34.log | grep -iE -- "-> *([a-z,]*,)?border|withdr|REINSTATE|REOPEN|SOURCE-HOLD|take-border-r34|^[^ ]* main ->" | cut -c1-330
sh $W/status.sh 2>&1 | cut -c1-240
for p in driver kfeed34 deepfeed34 finish; do kill -0 $(cat $W/$p.pid) 2>/dev/null || echo "DEAD $p"; done
ssh boxC 'ps -ax -o pid,command | grep "worker.py [12]" | grep -v grep | grep -c .' 2>/dev/null | sed 's/^/boxC border procs: /'
for f in driver kfeed34 deepfeed34; do tail -40 $W/$f.log | grep -E "Traceback|Error" | tail -2 | sed "s/^/$f: /"; done | cut -c1-200
for t in $S/take-*-r34/take.tsv; do n=$(tail -n +2 $t | wc -l | tr -d ' '); [ "$n" -gt 0 ] && echo "TAKE $(basename $(dirname $t)) $n: $(tail -n +2 $t | cut -f1 | tr '\n' ' ')"; done
grep -E 'KICK|BOUNDARY' $S/take-border-r34/STATE.txt | tail -4 | cut -c1-230
