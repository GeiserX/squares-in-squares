#!/bin/sh
# softrelay.sh N [N ...] (on boxE): the soft-box island of methods_soft.py from the best kick find of each n,
# 240 s at --delta 2e-4 and 240 s at 1e-4, each ending 120 s after its last find. Raw results in run/softrelay/raw.
cd "$(dirname "$0")"; B=$HOME/scratch/squares-base
for n in "$@"; do
  for d in 2e-4 1e-4; do
    [ $(( $(cat deadline) - $(date +%s) )) -lt 300 ] && exit 0
    f=$($B/venv/bin/python - "$n" <<'PY'
import glob, sys
sys.path.insert(0, '.')
import methods_lp as mlp
n = int(sys.argv[1])
fs = glob.glob('run/s[2-9]*/raw/%d-*.csv' % n) + glob.glob('run/relay/raw/%d-*.csv' % n) + glob.glob('run/softrelay/raw/%d-*.csv' % n) + glob.glob('run/s10/raw/%d-*.csv' % n)
print(min(fs, key=lambda f: mlp.side(mlp.load(f, {n})[n])) if fs else '')
PY
)
    [ -z "$f" ] && break
    s=$(echo $d | cut -c1)
    $B/venv/bin/python methods_soft.py "$f" run/softrelay --n $n --seconds 240 --seed $s --start best --delta $d --dry 120 >> logs/softrelay.out 2>&1
  done
done
