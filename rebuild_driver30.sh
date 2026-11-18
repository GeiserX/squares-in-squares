#!/bin/zsh
# rebuild r30 driver: collector every 60 s, follow every 300 s until 17:30Z (1794763800); deadline 17:45Z (1794764700)
cd $SCRATCH/bounties-squares/take-rebuild-r30/work
P=$SCRATCH/bounties-squares/venv/bin/python
i=0
while [ $(date +%s) -lt 1794764700 ]; do
  nice -n 5 $P -I tools/collect30.py >> collect.log 2>&1
  if [ $((i % 5)) -eq 0 ] && [ $(date +%s) -lt 1794763800 ]; then nice -n 5 $P -I tools/follow30.py >> follow.log 2>&1; fi
  i=$((i+1))
  sleep 60
done
# after the deadline: collect quench results that are still arriving for 8 more minutes
for j in 1 2 3 4 5 6 7 8; do nice -n 5 $P -I tools/collect30.py >> collect.log 2>&1; sleep 60; done
