#!/usr/bin/env bash
# Rebuild the seed submission (seeds/merged0.csv) from public packings.
# Run on a box, never the laptop. Needs git, python3 with mpmath==1.4.1 pandas==2.2.3,
# and nightly Rust for sqpack (portable_simd).
#   bash build_seed.sh $SCRATCH/bounties-squares
set -euo pipefail
W=${1:?work dir}; L=$(cd "$(dirname "$0")" && pwd); PY=${PY:-$W/venv/bin/python}
mkdir -p "$W/ext" "$W/seeds" "$W/bin"
cd "$W/ext"
[ -d couzo ]   || git clone -q --depth 1 https://github.com/franciscouzo/square-packing.git couzo     # MIT
[ -d samanyu ] || git clone -q --depth 1 https://github.com/Samanyu-dev/squares_in_squares.git samanyu # no licence; packings are maths, credited
cd "$W"
"$PY" "$L/export_couzo.py" ext/couzo seeds/couzo.csv 2> seeds/couzo-export.log
cp ext/samanyu/data_out/submission_22.2498820.csv seeds/samanyu_22249.csv
"$PY" - <<'PY'
import csv
w = csv.writer(open('seeds/samanyu_bestfit.csv', 'w', newline=''), lineterminator='\n')
w.writerow(['id', 'n', 'square_id', 'x', 'y', 'angle']); i = 0
for f in ['ext/samanyu/best_fit.csv', 'ext/samanyu/best_fit_101_500.csv', 'ext/samanyu/best_fit_501_1000.csv']:
    for r in csv.DictReader(open(f)):
        w.writerow([i, r['n'], r['square_id'], r['x'], r['y'], r['angle']]); i += 1
PY
for s in couzo samanyu_22249 samanyu_bestfit; do nice -n 19 "$PY" "$L/score.py" seeds/$s.csv --jobs 8 --out seeds/$s.tsv; done
"$PY" "$L/merge.py" seeds/merged0.csv seeds/samanyu_22249.csv seeds/samanyu_22249.tsv \
  seeds/samanyu_bestfit.csv seeds/samanyu_bestfit.tsv seeds/couzo.csv seeds/couzo.tsv
nice -n 19 "$PY" "$L/score.py" seeds/merged0.csv --jobs 8 --out seeds/merged0.tsv
(cd ext/couzo && cargo +nightly build --release -q && cp "$(cargo +nightly metadata --format-version 1 --no-deps | "$PY" -c 'import json,sys;print(json.load(sys.stdin)["target_directory"])')/release/sqpack" "$W/bin/")
