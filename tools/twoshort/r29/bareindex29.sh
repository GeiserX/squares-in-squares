#!/bin/zsh
# Refresh the bare-name index every 40 minutes in the background (round 27), until the deadline.
W=$SCRATCH/bounties-squares/take-twoshort-r29/work; B=$SCRATCH/bounties-squares
while [ $(date +%s) -lt $(( $(cat $W/deadline) + 300 )) ] && [ ! -e $W/STOP-COLLECT ]; do
  nice -n 10 find $B -maxdepth 5 -path '*/take-*' -name '[0-9]*.csv' -type f > $W/bare-index.bg.tmp 2>/dev/null && mv $W/bare-index.bg.tmp $W/bare-index.txt
  sleep 2400
done
