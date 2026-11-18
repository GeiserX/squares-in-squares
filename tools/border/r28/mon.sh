#!/bin/sh
# wait up to $1 s for a take change, a border-addressed or WITHDRAW/REINSTATE handoff line; then print a status
S=$SCRATCH/bounties-squares; W=$S/take-border-r28/work
S0=$(wc -l < $S/handoff-r28.log); T0=$(md5 -q $S/take-border-r28/take.tsv); END=$(($(date +%s)+$1))
until [ $(date +%s) -ge $END ] || [ "$(md5 -q $S/take-border-r28/take.tsv)" != "$T0" ] || tail -n +$((S0+1)) $S/handoff-r28.log | grep -v "Z border -> " | grep -qiE -- "-> *([a-z,]*,)?border|WITHDRAW|REINSTATE|REOPEN|take-border-r28"; do sleep 20; done
echo "== new handoff lines (border, withdraw, reinstate, main):"; tail -n +$((S0+1)) $S/handoff-r28.log | grep -iE -- "-> *([a-z,]*,)?border|WITHDRAW|REINSTATE|REOPEN|take-border-r28|^[^ ]* main ->" | cut -c1-330
sh $W/status.sh 2>&1 | cut -c1-240
for p in driver lpfeed wfeed finish; do kill -0 $(cat $W/$p.pid) 2>/dev/null || echo "DEAD $p"; done
ssh boxC 'ps -ax -o pid,command | grep "squares-border-r28/\|worker.py [12]\|wscan.py" | grep -v grep | grep -c .' 2>/dev/null | sed 's/^/boxC border procs: /'
for f in driver lpfeed wfeed; do tail -40 $W/$f.log | grep -E "Traceback|Error" | tail -2 | sed "s/^/$f: /"; done | cut -c1-200
