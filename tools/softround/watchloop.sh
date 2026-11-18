#!/bin/sh
# looks at the other lanes' take dirs every 2 minutes until 8 minutes before the soft deadline, and collects after
# each look: take.tsv stays current and each new certified layout gets its line in the handoff log
PY=$SCRATCH/bounties-squares/venv/bin/python; H=$(cd "$(dirname "$0")" && pwd); W=$("$PY" -I "$H/ctl.py" where)
while [ $(( $(cat $W/boxA/deadline) - $(date +%s) )) -gt 480 ]; do
  [ -e $W/STOPWATCH ] && break        # a STOP in boxA/ stops only the boxA slot
  "$PY" -I "$H/ctl.py" watch >> $W/watch.log 2>&1
  "$PY" -I "$H/ctl.py" collect >> $W/collect.log 2>&1
  sleep 120
done
echo "watch loop ended $(date -u +%H:%M:%S)" >> $W/watch.log
