#!/bin/sh
# midm round 32: run pubnear32.py every 20 minutes on the changed public files that harvest r32 fetches, until 16:30Z.
# Each run reads only files whose sha256 no earlier run read (work/pubnear/processed32.txt) and appends its "pub" lines
# to work/extra-starts.txt, which the driver reads every step. One STATE line per run that adds starts.
B=$SCRATCH/bounties-squares
W=$B/take-midm-r32/work
END=1794846600   # 2026-11-16T16:30:00Z
i=2
while [ "$(date +%s)" -lt "$END" ] && [ ! -e "$W/STOP" ]; do
  out=$W/pubnear/run$i.txt
  timeout 1500 "$B/venv/bin/python" -I tools/midm/pubnear32.py > "$out" 2>&1
  c=$(grep -c '^pub ' "$out")
  if [ "$c" -gt 0 ]; then
    grep '^pub ' "$out" >> "$W/extra-starts.txt"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) boxA PUBNEAR32 run$i: $c starts appended to work/extra-starts.txt ($(grep -c '^# changed file' "$out") changed files; log work/pubnear/run$i.txt)" >> "$B/take-midm-r32/STATE.txt"
  fi
  i=$((i + 1))
  sleep 1200
done
