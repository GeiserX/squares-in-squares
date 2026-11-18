#!/bin/zsh
# rebuild r30: re-run pub30.py (no new rows) every 5 min until 17:54Z (1794765240) so take.tsv drops rows a live take beats
cd $SCRATCH/bounties-squares/take-rebuild-r30/work
P=$SCRATCH/bounties-squares/venv/bin/python
while [ $(date +%s) -lt 1794765240 ]; do
  while pgrep -f "tools/collect30.py" > /dev/null; do sleep 3; done
  echo "$(date -u +%H:%M:%SZ) $(nice -n 5 $P -I tools/pub30.py 2>&1 | tail -1)" >> recheck.log
  sleep 300
done
