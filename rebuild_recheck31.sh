#!/bin/zsh
# rebuild r31: re-run pub31.py (no new rows) every 5 min until 00:24Z (1794788640) so take.tsv drops rows a live take beats
cd $SCRATCH/bounties-squares/take-rebuild-r31/work
P=$SCRATCH/bounties-squares/venv/bin/python
while [ $(date +%s) -lt 1794788640 ]; do
  while pgrep -f "tools/collect31.py" > /dev/null; do sleep 3; done
  echo "$(date -u +%H:%M:%SZ) $(nice -n 5 $P -I tools/pub31.py 2>&1 | tail -1)" >> recheck.log
  sleep 300
done
