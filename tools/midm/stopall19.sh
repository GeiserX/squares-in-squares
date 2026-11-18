#!/bin/sh
# stopall.sh: end every process of the midm lane on this box (by its working dir), and say how many are left.
cd "$(dirname "$0")"; touch STOP
for p in $(pgrep -u "$(id -u)" -f 'scratch/squares-midm|midm_scan.py|kw.py|midm_fqonce.py|slice19'); do
  kill "$p" 2>/dev/null
done
sleep 2
echo "midm processes left: $(pgrep -u "$(id -u)" -f 'midm_scan.py|kw.py|midm_fqonce.py|slice19' | wc -l | tr -d ' ')"
