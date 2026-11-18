#!/bin/sh
# loop20c.sh: round 20, on boxA. Every 6 minutes until 00:50 UTC a collect (collect20.sh final) writes the take
# dir, then handoff20.py writes one handoff line for each new or lower row.
BOX=$SCRATCH/bounties-squares; T=$BOX/take-midm-r20; W=$T/work
L=.; PY=$BOX/venv/bin/python
END=$(date -u -j -f "%Y-%m-%d %H:%M:%S" "2026-11-13 00:50:00" +%s)
while [ $(date +%s) -lt $END ]; do
  /bin/sh $L/tools/midm/collect20.sh final > $W/collect-$(date -u +%H%M).log 2>&1
  $PY $L/tools/midm/handoff20.py
  sleep 360
done
