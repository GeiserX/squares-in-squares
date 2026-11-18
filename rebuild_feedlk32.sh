#!/bin/zsh
# rebuild r32: feedlk32.py every 90 s until 16:50Z (1794847800): 150 s invent_rest lkicks of work/lkorder.txt
cd $SCRATCH/bounties-squares/take-rebuild-r32/work
P=$SCRATCH/bounties-squares/venv/bin/python
while [ $(date +%s) -lt 1794847800 ]; do
  nice -n 5 /opt/homebrew/bin/timeout 300 $P -I tools/feedlk32.py >> feedlk.log 2>&1
  sleep 90
done
