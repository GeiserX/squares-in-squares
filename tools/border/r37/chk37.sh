#!/bin/zsh
# wait $1 s, then print new STATE events and new other-lane certified lines since the last call
cd $SCRATCH/bounties-squares/take-border-r37/work
T=$(( $(date +%s) + ${1:-480} )); until [ $(date +%s) -ge $T ]; do sleep 10; done
date -u +%H:%M:%S; uptime | sed 's/.*load/load/'
for f in driver dfeed37 kfeed37-boxC kfeed37-boxE kfeed37-boxB kfeed37-local finish; do ps -p $(cat $f.pid) >/dev/null 2>&1 || echo "DEAD $f"; done
a=$(cat .chk_state 2>/dev/null || echo 0); b=$(wc -l < ../STATE.txt); echo $b > .chk_state
sed -n "$((a+1)),${b}p" ../STATE.txt | grep -v WORKERS | grep -E "DFEED|IDLE|FRESH|KICK [0-9]|CLAIM|certified|near |stop|REJECT|refused|overtaken|not queued|fail" | cut -c1-210
h=$(cat .chk_h 2>/dev/null || echo 0); hb=$(wc -l < ../../handoff-r37.log); echo $hb > .chk_h
sed -n "$((h+1)),${hb}p" ../../handoff-r37.log | grep -iE "certified|withdraw|main ->" | grep -v "near donor" | grep -v "^.\{21\}border" | cut -c1-220
for t in ../../take-*-r37/take.tsv; do c=$(($(wc -l < $t)-1)); [ $c -gt 0 ] && echo "$t $c"; done
tail -20 dfeed37.log | grep -iE "Trace|Error" | head -2
for h in kfeed37-*.log; do tail -20 $h | grep -iE "Traceback" | head -1 | sed "s/^/$h /"; done
