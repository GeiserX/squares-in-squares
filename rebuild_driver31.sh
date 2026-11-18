#!/bin/zsh
# rebuild r31 driver: collector every 60 s (cert, certified-file quench, autopub with chain legs), follow and held feed every
# 300 s until 00:00Z (1794787200); box deadline 00:15Z (1794788100), then 8 more minutes of collection
cd $SCRATCH/bounties-squares/take-rebuild-r31/work
P=$SCRATCH/bounties-squares/venv/bin/python
i=0
while [ $(date +%s) -lt 1794788100 ]; do
  nice -n 5 $P -I tools/collect31.py >> collect.log 2>&1
  if [ $((i % 5)) -eq 0 ] && [ $(date +%s) -lt 1794787200 ]; then
    nice -n 5 $P -I tools/follow31.py >> follow.log 2>&1
    nice -n 5 $P -I tools/feedheld31.py >> feed.log 2>&1
  fi
  i=$((i+1))
  sleep 60
done
for j in 1 2 3 4 5 6 7 8; do nice -n 5 $P -I tools/collect31.py >> collect.log 2>&1; sleep 60; done
