#!/bin/zsh
# rebuild r32: pub32 with no new rows every 5 min until 17:24Z (1794849840), so take.tsv drops a row a live take beats
cd $SCRATCH/bounties-squares/take-rebuild-r32/work
P=$SCRATCH/bounties-squares/venv/bin/python
while [ $(date +%s) -lt 1794849840 ]; do
  echo "$(date -u +%FT%TZ) $(nice -n 5 /opt/homebrew/bin/timeout 300 $P -I tools/pub32.py 2>&1 | tail -3 | tr '\n' ' ')" >> recheck.log
  sleep 300
done
