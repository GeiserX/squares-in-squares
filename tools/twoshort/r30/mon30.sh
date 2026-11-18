#!/bin/bash
# Round 29 monitor pass: drop withdrawn inputs, demote busy n, report keeps, take rows, fresh kicks and handoff lines to us.
cd $SCRATCH/bounties-squares/take-twoshort-r30/work
while pgrep -f "manage30.py --once" >/dev/null; do sleep 2; done
P=../../venv/bin/python
date -u +%T
$P -I unqueue30.py | head -1 | cut -c1-160
$P -I demote30.py | cut -c1-200
grep KEEP certify.log | tail -3
echo "take:"; awk -F'\t' 'NR>1{print $1,$4}' ../take.tsv
$P -I kicks30.py 2>/dev/null | tail -1
ls -t boxE30/done 2>/dev/null | head -4
grep -E "\-> (twoshort|all):" ../../handoff-r30.log | grep -v "quenched rectangle near\|fresh build\|fresh border near\|WITHDRAW" | tail -${1:-6} | cut -c1-200
grep -E "ERROR|Traceback" ../STATE.txt | tail -2 | cut -c1-200
ssh boxE 'ps -axo etime,command | grep squares-twoshort | grep -E "lane/" | grep -v grep | cut -c1-130; uptime | sed "s/.*load/load/"'
