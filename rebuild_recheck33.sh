#!/bin/zsh
# rebuild r33: pub33 with no new rows every 5 min until 17:24Z (1794875040), so take.tsv drops a row a live take beats
cd $SCRATCH/bounties-squares/take-rebuild-r33/work
P=$SCRATCH/bounties-squares/venv/bin/python
while [ $(date +%s) -lt 1794875040 ]; do
  echo "$(date -u +%FT%TZ) $(nice -n 5 /opt/homebrew/bin/timeout 300 $P -I tools/pub33.py 2>&1 | tail -3 | tr '\n' ' ')" >> recheck.log
  sleep 300
done
