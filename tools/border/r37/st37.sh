#!/bin/zsh
cd $SCRATCH/bounties-squares/take-border-r37/work
date -u +%H:%M:%S; uptime | sed 's/.*load/load/'
for f in driver dfeed37 kfeed37-boxC kfeed37-boxE kfeed37-boxB kfeed37-local; do ps -p $(cat $f.pid) >/dev/null 2>&1 || echo "DEAD $f"; done
echo "-- STATE (last 12, no WORKERS)"; grep -v WORKERS ../STATE.txt | tail -12 | cut -c1-260
echo "-- handoff certified/fresh lines (last 8)"; grep -iE "certif" ../../handoff-r37.log | grep -v "^.\{21\}border" | tail -8 | cut -c1-220
echo "-- takes"; for t in ../../take-*-r37/take.tsv; do echo "$t $(($(wc -l < $t)-1))"; done
tail -3 dfeed37.log | grep -i -E "error|Traceback" | head -3
