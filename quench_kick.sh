#!/bin/sh
# quench (round 28): one lkick leg on a certified best row, then the fq loop of quench_box.sh on its best raw result.
# Runs on a box with python (boxB squares-base venv) in an idle quench slot; quench_drive.sh starts it for a
# job that holds kick.json. The lkick is invent_rest.py --modes lkick (the backlog lane's kick of fresh rows).
# Usage: quench_kick.sh JOBDIR FQ DEADLINE_EPOCH PY KLANE
#   JOBDIR/cert.csv  the start rows (quench_once.py prep --no-cert)
#   JOBDIR/kick.json {"n", "seed", "seconds", "bar_side", "tool" (lkick, the default, or midm), "modes" (midm only)}
# tool midm runs midm_scan.py (fq's own --kick, the local lkick and bkick, or melt and hop) instead of invent_rest.py.
#   writes JOBDIR/out.txt (fq text of the best result, or in.txt when the kick found nothing), box.log, done
J=$1; FQ=$2; DL=$3; PY=$4; KL=$5
BD=$(cd "$(dirname "$0")" && pwd)
cd "$J" || exit 2
rm -f done out.txt
eval "$($PY -I -c 'import json; d=json.load(open("kick.json")); print("N=%d SEED=%d SEC=%d BARS=%r TOOL=%s MODES=%s PROBE=%d" % (d["n"], d["seed"], d["seconds"], d["bar_side"], d.get("tool", "lkick"), d.get("modes", "kick,lkick,bkick"), d.get("probe", 0)))')"
now=$(date +%s); left=$((DL - now - 60)); [ $left -lt $SEC ] && SEC=$left
echo "$DL" > kdeadline
if [ "$SEC" -gt 20 ]; then
  if [ "$TOOL" = midm ]; then
    # round 31 probe: with PROBE > 0 the scan stops at the first check after PROBE seconds (two tries done, or 3*PROBE s)
    # when no try has come 1e-9 of side below the start (no FIND line). Round 30: 10 of 89 kicks improved on any try and
    # every one that paid improved early (968 on 11 of 75 tries); the 995 kick ran all 44 tries with no find.
    perl -e 'alarm shift; exec @ARGV' $((SEC + 120)) $PY -I "$KL/midm_scan.py" --n $N --sub cert.csv --out run --fq "$FQ" --seconds $SEC --seed $SEED --modes $MODES --ref 0 --deadline kdeadline >> box.log 2>&1 &
    KP=$!
    if [ "$PROBE" -gt 0 ]; then
      t0=$(date +%s)
      while kill -0 $KP 2>/dev/null; do
        sleep 10
        el=$(( $(date +%s) - t0 ))
        [ $el -ge $PROBE ] || continue
        tries=$(grep -c '^[0-9]' run/scan-$N-$SEED.tsv 2>/dev/null); tries=${tries:-0}
        finds=$(grep -c '^# FIND' run/scan-$N-$SEED.tsv 2>/dev/null); finds=${finds:-0}
        if [ "$finds" -gt 0 ]; then echo "probe: find after ${el}s ($tries tries), the scan runs on" >> box.log; break; fi
        if [ "$tries" -ge 2 ] || [ $el -ge $((PROBE * 3)) ]; then
          echo "probe: no find in ${el}s ($tries tries), scan stopped" >> box.log
          pkill -P $KP 2>/dev/null; kill $KP 2>/dev/null; sleep 2; pkill -9 -P $KP 2>/dev/null; kill -9 $KP 2>/dev/null
          break
        fi
      done
    fi
    wait $KP
  else
    perl -e 'alarm shift; exec @ARGV' $((SEC + 120)) $PY -I "$KL/invent_rest.py" $N cert.csv run --seconds $SEC --seed $SEED --modes lkick --bar $BARS --deadline kdeadline >> box.log 2>&1
  fi
  echo "$TOOL rc=$? seed $SEED ${SEC}s $MODES" >> box.log
fi
best=$($PY -I -c '
import csv, glob, math, sys
sys.path.insert(0, sys.argv[1])
import methods_lp as mlp
from midm_scan import to_fq
b = None
for p in glob.glob("run/raw/*.csv"):
    try:
        P = mlp.load(p, {int(sys.argv[2])})[int(sys.argv[2])]
        s = to_fq(P)[0]
    except Exception:
        continue
    if b is None or s < b[0]:
        b = (s, p)
print(b[1] if b else "")
' "$KL" $N)
if [ -n "$best" ]; then
  echo "lkick best raw $best" >> box.log
  mkdir -p k && $PY -I "$KL/quench_once.py" prep "$best" k --no-cert >> box.log 2>&1 && sh "$BD/quench_box.sh" "$J/k" "$FQ" "$DL" && cat k/box.log >> box.log && cp k/out.txt out.txt && { [ ! -s k/best.txt ] || cp k/best.txt best.txt; }
fi
[ -s out.txt ] || cp in.txt out.txt
echo "ran=1 kick" > done
