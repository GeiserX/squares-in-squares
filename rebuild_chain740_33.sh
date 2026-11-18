#!/bin/zsh
cd $SCRATCH/bounties-squares/take-rebuild-r33/work
P=$SCRATCH/bounties-squares/venv/bin/python
while [ $(date +%s) -lt 1794874500 ]; do
  nice -n 5 /opt/homebrew/bin/timeout 300 $P -I tools/chain740.py >> chain740.log 2>&1
  sleep 60
done
