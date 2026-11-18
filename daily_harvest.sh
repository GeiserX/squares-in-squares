#!/bin/bash
# The daily public harvest, one command, up to the gate (it never builds a submission and never submits).
#
#   daily_harvest.sh PREV_HARVEST_DIR BASE_DETAILS.csv
#
# PREV_HARVEST_DIR   the harvest dir of the last run (its meta.json files say what we already hold)
# BASE_DETAILS.csv   details.csv of the gate dir of the held file (n, L, score); gate.json beside it names the file
#
# Steps, JOBS processes at most (default 4):
#   1. harvest_delta.py     Kaggle notebooks and datasets that are new or re-run since PREV_HARVEST_DIR
#      harvest_register.py  the Squares Project register and Doga Ozden's repos, from git, licence per packet
#   2. harvest_merge.py     per-n best of everything fetched, scored by the official metric, onto the held file
#   3. angle_take.py        licence allow-list, floatsafe at 2.2e-11, kept only when more than 1e-10 below held
#   4. literature_border.py one row and one column around every n, on the held file plus this take
# Output: a take dir in the layout engine_assemble.py reads (per-n csv, take.tsv) and harvest-best.tsv in it
# (n, score, L, source, licence of every n kept). The last lines print the take dir, the n kept, the gain and the
# PREV_HARVEST_DIR of the next run. Downloads are data: python runs with -I and nothing fetched is executed.
#
# Each run measures against the held file only. When the held file has not changed since an earlier run, name
# that run's take dirs in TAKES (space separated): an n this run does not improve on them is left out, so the
# take dirs can go to engine_assemble.py together, oldest first.
#
# Environment: SQUARES_SCRATCH (default $SCRATCH/bounties-squares), STAMP (default UTC now), TAKES, JOBS.
set -euo pipefail
[ $# -eq 2 ] || { sed -n '2,6p' "$0"; exit 2; }
LANE=$(cd "$(dirname "$0")" && pwd)
S=${SQUARES_SCRATCH:-$SCRATCH/bounties-squares}
PY="$S/venv/bin/python -I"
PREV=$(cd "$1" && pwd); DET=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
STAMP=${STAMP:-$(date -u +%Y-%m-%dT%H%MZ)}
NEW=$S/harvest-$STAMP; MERGED=$S/harvest-merged-$STAMP; TAKE=$S/take-harvest-$STAMP; LOG=$S/logs/daily-harvest-$STAMP
HELD=$($PY -c 'import json,sys; print(json.load(open(sys.argv[1]))["file"])' "$(dirname "$DET")/gate.json")
[ -s "$HELD" ] || { echo "held file $HELD not found"; exit 2; }
[ -e "$NEW" ] && { echo "$NEW exists; set STAMP"; exit 2; }
mkdir -p "$NEW" "$S/logs"
echo "held $HELD  prev $PREV  new $NEW"

echo "1. fetch (log $LOG-delta.log, $LOG-register.log)"
$PY "$LANE/harvest_delta.py" "$PREV" "$NEW" > "$LOG-delta.log" 2>&1
grep -Eq '^[1-9][0-9]* kernels' "$LOG-delta.log" || { echo "Kaggle was not reached (no notebook listed): nothing was fetched"; exit 3; }
echo "   kaggle: $(grep -c '^nb ' "$LOG-delta.log" || true) notebooks and $(grep -c '^ds ' "$LOG-delta.log" || true) datasets new or re-run; $(grep -c "file fail\|ds fail\|nb fail" "$LOG-delta.log" || true) failed downloads"
if $PY "$LANE/harvest_register.py" "$S/register-clones" "$NEW" > "$LOG-register.log" 2>&1; then
    echo "   $(grep '^register' "$LOG-register.log"); $(grep '^files:' "$LOG-register.log")"
    # a refused repo list or a failed clone ends with exit 0: say it here, or a missed source reads as "nothing new"
    grep -E '^(account list fail|clone fail)' "$LOG-register.log" | cut -c1-200 | sed 's/^/   REGISTER, NOT ALL READ: /' || true
else
    echo "   REGISTER NOT FETCHED (see $LOG-register.log): the run goes on with Kaggle only"
fi

echo "2. merge (log $LOG-merge.log)"
awk -F, 'BEGIN{OFS="\t"} NR==1{for(i=1;i<=NF;i++)c[$i]=i; print "n","score","L","reason"; next}{print $c["n"],$c["score"],$c["L"],"ok"}' "$DET" > "$NEW/base.tsv"
$PY "$LANE/harvest_merge.py" --harvest "$NEW" --base "$HELD" --base-tsv "$NEW/base.tsv" --out "$MERGED" --procs "${JOBS:-4}" > "$LOG-merge.log" 2>&1
echo "   $(tail -1 "$LOG-merge.log")"

echo "3. take with the licence allow-list (log $LOG-take.log)"
$PY "$LANE/angle_take.py" "$MERGED" "$DET" "$TAKE" > "$LOG-take.log" 2>&1
echo "   $(grep -c '^licence drop' "$LOG-take.log" || true) wins left out for their licence; $(tail -1 "$LOG-take.log")"

echo "4. border step (log $LOG-border.log)"
$PY "$LANE/literature_border.py" "$HELD" "$DET" "$TAKE" ${TAKES:-} "$TAKE" > "$LOG-border.log" 2>&1
echo "   $(tail -1 "$LOG-border.log")"

# one row per n in take.tsv (the border step appends), and the per-n record with side, source and licence
$PY - "$TAKE" ${TAKES:-} <<'EOF'
import csv, math, os, sys
take = sys.argv[1]
best, earlier = {}, {}
for t in sys.argv[2:]:
    for r in csv.DictReader(open(t + '/take.tsv'), delimiter='\t'):
        earlier[int(r['n'])] = min(float(r['new']), earlier.get(int(r['n']), 9.0))
for r in csv.DictReader(open(take + '/take.tsv'), delimiter='\t'):
    n = int(r['n'])
    if n not in best or float(r['new']) < float(best[n]['new']):
        best[n] = r
for n in [n for n in best if float(best[n]['new']) >= earlier.get(n, 9.0)]:
    print('left out: n=%d is no better than an earlier take (%s against %r)' % (n, best[n]['new'], earlier[n]))
    del best[n]; os.remove('%s/%d.csv' % (take, n))
with open(take + '/take.tsv.tmp', 'w') as h, open(take + '/harvest-best.tsv', 'w') as g:
    h.write('n\theld\tnew\tgain\tsource\tlicence\n'); g.write('n\tscore\tL\tsource\tlicence\n')
    for n in sorted(best):
        r = best[n]
        assert os.path.exists('%s/%d.csv' % (take, n)), n
        h.write('\t'.join(r[k] for k in ('n', 'held', 'new', 'gain', 'source', 'licence')) + '\n')
        g.write('%d\t%s\t%r\t%s\t%s\n' % (n, r['new'], (float(r['new']) + 1) * math.sqrt(n), r['source'], r['licence']))
os.replace(take + '/take.tsv.tmp', take + '/take.tsv')   # by rename: a reader never sees half a table
gain = sum(float(r['held']) - float(r['new']) for r in best.values())
print('kept %d n, gain %.10f: %s' % (len(best), gain, ' '.join(map(str, sorted(best)))))
EOF
echo "take dir: $TAKE   (per-n record: $TAKE/harvest-best.tsv)"
echo "next: engine_assemble.py $HELD OUT.csv $TAKE, then the gate with --last $(dirname "$DET")"
echo "next run: daily_harvest.sh $NEW <details.csv of the file held then>"
