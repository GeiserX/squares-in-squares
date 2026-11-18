#!/bin/sh
# final21.sh: end of round 21 for the midm lane (run on boxA after 03:25Z).
BOX=$SCRATCH/bounties-squares; T=$BOX/take-midm-r21; W=$T/work
L=.; PY=$BOX/venv/bin/python; S=boxE; SD=scratch/squares-midm
pkill -f tools/midm/loop21s.sh; pkill -f tools/midm/loop21c.sh
while pgrep -f "collect21.sh final" > /dev/null; do sleep 5; done
ssh $S "touch $SD/STOP"
# our two workers only, by pid (other lanes run their own copies of the midm tools on boxE)
i=0; while [ $i -lt 40 ] && ssh $S "ps -p \$(cat $SD/kw.pids | tr ' ' ,) > /dev/null"; do sleep 10; i=$((i + 1)); done
echo "kw.py left on boxE: $(ssh $S "ps -o pid= -p \$(cat $SD/kw.pids | tr ' ' ,) | wc -l")"
/bin/sh $L/tools/midm/collect21.sh final > $W/collect-final.log 2>&1; tail -30 $W/collect-final.log
$PY $L/tools/midm/handoff21.py
mkdir -p $W/r21-boxE; rsync -a --exclude tmp "$S:$SD/run" "$S:$SD/logs" "$S:$SD/legs.q" "$S:$SD/legsB.q" $W/r21-boxE/ ; ssh $S "cd $SD && cat q*-c*.q" > $W/r21-boxE/queues.txt
echo "run dirs copied: $(ls $W/r21-boxE/run | wc -l), scans $(ls $W/r21-boxE/run/*/scan-*.tsv | wc -l)"
