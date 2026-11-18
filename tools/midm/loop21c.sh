#!/bin/sh
# loop21c.sh: round 21, on boxA. Every 6 minutes until 03:20 UTC a collect (collect21.sh final) writes the take
# dir, then handoff21.py writes one handoff line for each new or lower row.
BOX=$SCRATCH/bounties-squares; T=$BOX/take-midm-r21; W=$T/work
L=.; PY=$BOX/venv/bin/python
END=$(date -u -j -f "%Y-%m-%d %H:%M:%S" "${MIDM_END:-2026-11-13 03:20:00}" +%s)   # MIDM_END: the revive of 09:50Z
while [ $(date +%s) -lt $END ]; do
  /bin/sh $L/tools/midm/collect21.sh final > $W/collect-$(date -u +%H%M).log 2>&1
  $PY $L/tools/midm/handoff21.py
  sleep 360
done
