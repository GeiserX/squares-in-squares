#!/bin/zsh
# invent r36 driver: every 90 s sync with boxE, rule-n guard, finish (certify/take). Ends 23:52Z.
W=$SCRATCH/bounties-squares/take-invent-r36/work; PY=$SCRATCH/bounties-squares/venv/bin/python
END=$(( $(date -j -u -f '%Y-%m-%dT%H:%M:%S' 2026-11-17T23:52:00 +%s) ))
while [ $(date +%s) -lt $END ]; do
  $W/tools/sync.sh >> $W/loop.log 2>&1
  $PY $W/tools/guard.py >> $W/loop.log 2>&1
  $PY $W/tools/finish.py >> $W/finish.log 2>&1
  sleep 90
done
echo "$(date -u +%FT%TZ) loop end" >> $W/loop.log
