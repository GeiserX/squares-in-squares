#!/bin/zsh
# rebuild r29 driver: collector every 60 s, follow every 300 s until 11:35Z (1794742500); deadline 11:45Z (1794743100)
cd $SCRATCH/bounties-squares/take-rebuild-r29/work
P=$SCRATCH/bounties-squares/venv/bin/python
i=0
while [ $(date +%s) -lt 1794743100 ]; do
  nice -n 5 $P -I tools/collect29.py >> collect.log 2>&1
  if [ $((i % 5)) -eq 0 ] && [ $(date +%s) -lt 1794742500 ]; then nice -n 5 $P -I tools/follow29.py >> follow.log 2>&1; fi
  i=$((i+1))
  sleep 60
done
# after the deadline: collect quench results that are still arriving for 8 more minutes
for j in 1 2 3 4 5 6 7 8; do nice -n 5 $P -I tools/collect29.py >> collect.log 2>&1; sleep 60; done
