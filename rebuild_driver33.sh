#!/bin/zsh
# rebuild r33 driver: collector every 60 s (cert, certified-file quench, autopub with chain legs), follow and held feed every
# 300 s until 17:00Z (1794873600); box deadline 17:15Z (1794874500), then 8 more minutes of collection
cd $SCRATCH/bounties-squares/take-rebuild-r33/work
P=$SCRATCH/bounties-squares/venv/bin/python
i=0
while [ $(date +%s) -lt 1794874500 ]; do
  nice -n 5 /opt/homebrew/bin/timeout 600 $P -I tools/collect33.py >> collect.log 2>&1
  if [ $((i % 2)) -eq 0 ] && [ $(date +%s) -lt 1794873600 ]; then
    nice -n 5 /opt/homebrew/bin/timeout 300 $P -I tools/follow33.py >> follow.log 2>&1
    nice -n 5 /opt/homebrew/bin/timeout 300 $P -I tools/feedheld33.py >> feed.log 2>&1
  fi
  i=$((i+1))
  sleep 60
done
for j in 1 2 3 4 5 6 7 8; do nice -n 5 /opt/homebrew/bin/timeout 600 $P -I tools/collect33.py >> collect.log 2>&1; sleep 60; done
