#!/bin/sh
# loop20.sh: round 20, on boxA. Every 7 minutes until 00:48 UTC: a snapshot of the take dirs of the other lanes
# (snap20.py K) goes to the kick queue on boxE, then a collect writes the take dir and the handoff lines.
BOX=$SCRATCH/bounties-squares; T=$BOX/take-midm-r20; W=$T/work
L=.; PY=$BOX/venv/bin/python; S=boxE; SD=scratch/squares-midm
END=$(date -u -j -f "%Y-%m-%d %H:%M:%S" "2026-11-13 00:48:00" +%s)
while [ $(date +%s) -lt $END ]; do
  K=$(cat $W/nextK 2>/dev/null || echo 51)
  $PY $L/tools/midm/snap20.py $K 150 > $W/snap-$K.log 2>&1
  if [ -s $W/q$K-c1.q ] || [ -s $W/q$K-c2.q ] || [ -s $W/q$K-c3.q ] || [ -s $W/q$K-c4.q ]; then
    rsync -a $W/r$K "$S:$SD/" && rsync -a $W/q$K-c*.q "$S:$SD/"
    # a line of an earlier snapshot for the same n is now a kick of a file that is no longer the lowest: claim it away
    ns=$(cat $W/q$K-c*.q | awk '{print $2}' | tr '\n' ' ')
    ssh $S "cd $SD/claims && for n in $ns; do k=50; while [ \$k -lt $K ]; do mkdir -p \$n-\$k; k=\$((k + 1)); done; done"
    echo "$(date -u +%H:%M) loop20 snapshot $K -> boxE queue: $(grep -h '^class' $W/snap-$K.log | cut -c1-200 | tr '\n' ' ')" >> $T/STATE.txt
    echo $((K + 1)) > $W/nextK
  fi
  /bin/sh $L/tools/midm/collect20.sh final > $W/collect-$(date -u +%H%M).log 2>&1
  $PY $L/tools/midm/handoff20.py
  sleep 420
done
