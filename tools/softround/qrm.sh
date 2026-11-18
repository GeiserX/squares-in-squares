#!/bin/sh
# qrm.sh BOX "N TAG" REASON: take a line that has not started out of a box queue and mark the job skipped in plan.json
PY=$SCRATCH/bounties-squares/venv/bin/python; H=$(cd "$(dirname "$0")" && pwd); W=$("$PY" -I "$H/ctl.py" where)
if [ "$1" = boxA ]; then run() { sh -c "cd $W/boxA && $1"; }; else run() { ssh -o ConnectTimeout=10 "$B" "cd scratch/squares-methods && $1"; }; fi
B=$1
out=$(run "until mkdir qlock 2>/dev/null; do sleep 1; done; if grep -q '^$2\$' queue.txt; then grep -v '^$2\$' queue.txt > queue.tmp; mv queue.tmp queue.txt; echo removed; else echo absent; fi; rmdir qlock")
echo "$1 $2: $out"
[ "$out" = removed ] && "$PY" -I - "$W" "$2" "$3" <<'PY'
import json, os, sys
W = sys.argv[1]
f = sys.argv[2].split(); pl = json.load(open(W + '/plan.json'))
for j in pl['jobs']:
    if (j['n'], j['tag']) == (int(f[0]), f[1]): j['skipped'] = sys.argv[3]
tmp = W + '/plan.json.tmp'; json.dump(pl, open(tmp, 'w'), indent=0); os.rename(tmp, W + '/plan.json')
PY
