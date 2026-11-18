#!/bin/sh
# loop21s.sh: round 21, on boxA. Every 3 minutes until 03:10 UTC a snapshot of the take dirs of the other lanes
# (snap21.py K) goes to the kick queue on boxE. The collect runs in loop21c.sh, so a wait for the fq quench
# (up to 8 minutes while a worker ends a scan of 450 s) never holds a new start back.
BOX=$SCRATCH/bounties-squares; T=$BOX/take-midm-r21; W=$T/work
L=.; PY=$BOX/venv/bin/python; S=boxE; SD=scratch/squares-midm
END=$(date -u -j -f "%Y-%m-%d %H:%M:%S" "${MIDM_END:-2026-11-13 03:10:00}" +%s)   # MIDM_END: the revive of 09:50Z
while [ $(date +%s) -lt $END ]; do
  K=$(cat $W/nextK 2>/dev/null || echo 21)
  $PY $L/tools/midm/snap21.py $K 150 > $W/snap-$K.log 2>&1
  if [ -s $W/q$K-c1.q ] || [ -s $W/q$K-c2.q ] || [ -s $W/q$K-c3.q ] || [ -s $W/q$K-c4.q ]; then
    rsync -a $W/r$K "$S:$SD/" && rsync -a $W/q$K-c*.q "$S:$SD/"
    # a line of an earlier snapshot for the same n is now a kick of a file that is no longer the lowest: claim it away
    ns=$(cat $W/q$K-c*.q | awk '{print $2}' | tr '\n' ' ')
    ssh $S "cd $SD/claims && for n in $ns; do k=21; while [ \$k -lt $K ]; do mkdir -p \$n-\$k; k=\$((k + 1)); done; done"
    echo "$(date -u +%H:%M) loop21s snapshot $K -> boxE queue: $(grep -h '^class' $W/snap-$K.log | cut -c1-200 | tr '\n' ' ')" >> $T/STATE.txt
    echo $((K + 1)) > $W/nextK
  fi
  sleep 180
done
