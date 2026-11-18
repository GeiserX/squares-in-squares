#!/bin/bash
# The polish step: every n a take dir moved gets the fq quench and a short soft-box search before the gate.
# It never builds a submission and never submits.
#
#   daily_polish.sh TAKE_DIR BASE_DETAILS.csv OUT_TAKE_DIR
#
# TAKE_DIR          a take dir (per-n csv plus take.tsv), for example the one daily_harvest.sh wrote
# BASE_DETAILS.csv  details.csv of the gate dir of the held file (n, L, score); gate.json beside it names the file
# OUT_TAKE_DIR      the polished take dir; the work files go to OUT_TAKE_DIR/work (or WORK). It may already
#                   hold a take: several runs add to one dir, each with its own WORK, and per n the lower
#                   score stays
#
# Steps, JOBS processes at most (default 4):
#   1. engine_assemble.py  the held file with TAKES and TAKE_DIR on top: the start of every polish
#   2. engine_polish.py    fq quench of each n, default flags then the deep flags, up to three rounds
#   3. methods_soft.py     SOFT_SECONDS (default 60) of the soft-box search per n, from the quenched packing
#   4. tools/polish_take.py  floatsafe at 2.2e-11; an n is kept when its score is more than 1e-10 below the
#                          held score and more than 1e-10 below the packing it started from
# Output: OUT_TAKE_DIR in the layout engine_assemble.py reads. It holds only the n the polish made smaller, and
# each of them started from TAKE_DIR's packing, so give engine_assemble.py TAKE_DIR first and OUT_TAKE_DIR after
# it. take.tsv keeps the source and licence of the packing each n started from, with the polish named in front.
#
# To polish what several take dirs hold, some of them still being written, build TAKE_DIR first:
#   tools/take_lowest.py BASE_DETAILS.csv START_DIR TAKE_DIR [TAKE_DIR ...] --seen SEEN.tsv
# writes the lowest certified file per n as one take dir, and with --seen only the n that are new since the
# last call. Each file of START_DIR is a whole packing, so START_DIR goes to this script with no TAKES.
#
# Environment:
#   SQUARES_SCRATCH  default $SCRATCH/bounties-squares
#   TAKES            earlier take dirs that go under TAKE_DIR (space separated, oldest first); their n are
#                    polished only when NS names them
#   NS               more n to polish (space separated), from the held file or from TAKES
#   FQ_ONLY          n that get step 2 and not step 3 (space separated), for example the n another run
#                    already gives a long soft-box search
#   JOBS, SOFT_SECONDS; SOFT_SECONDS=0 skips step 3
#   N_LIMIT          seconds of step 2 per n (default 1200, 0 for none). An n still in its quench then is
#                    killed with its fq call and keeps nothing; the run goes on to the next n. A hung pool
#                    worker held the only polish slot for 33 minutes on 2026-11-12
#   WORK             the work dir of this run (default OUT_TAKE_DIR/work); it must not hold a run yet
#   DEADLINE_FILE    a file that holds a time in epoch seconds (it can be rewritten while the run goes). When
#                    that time passes, the fq calls of this run are ended, step 3 is skipped (an n whose soft
#                    search has not started yet is skipped, so step 3 ends at most SOFT_SECONDS late) and
#                    step 4 takes what the quench and the soft searches had certified
set -euo pipefail
[ $# -eq 3 ] || { sed -n '2,9p' "$0"; exit 2; }
LANE=$(cd "$(dirname "$0")" && pwd)
S=${SQUARES_SCRATCH:-$SCRATCH/bounties-squares}
PY="$S/venv/bin/python -I"
JOBS=${JOBS:-4}; SOFT_SECONDS=${SOFT_SECONDS:-60}; N_LIMIT=${N_LIMIT:-1200}
TAKE=$(cd "$1" && pwd); DET=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
mkdir -p "$3"; OUT=$(cd "$3" && pwd); W=${WORK:-$OUT/work}
[ -e "$W/base.csv" ] && { echo "$W already holds a run; set WORK"; exit 2; }
[ -s "$TAKE/take.tsv" ] || { echo "$TAKE has no take.tsv"; exit 2; }
HELD=$($PY -c 'import json,sys; print(json.load(open(sys.argv[1]))["file"])' "$(dirname "$DET")/gate.json")
[ -s "$HELD" ] || { echo "held file $HELD not found"; exit 2; }
mkdir -p "$W/fq" "$W/tmp" "$W/soft"; W=$(cd "$W" && pwd)
trap 'kill 0' INT TERM

NSLIST=$( { awk -F'\t' 'NR>1{print $1}' "$TAKE/take.tsv"; tr ' ,' '\n\n' <<<"${NS:-}"; } | { grep -E '^[0-9]+$' || true; } | sort -un | paste -sd, -)
[ -n "$NSLIST" ] || { echo "no n to polish: $TAKE/take.tsv is empty and NS is not set"; [ -e "$OUT/take.tsv" ] || printf 'n\theld\tnew\tgain\tsource\tlicence\tstart\tpolish_gain\n' > "$OUT/take.tsv"; exit 0; }
COUNT=$(tr ',' '\n' <<<"$NSLIST" | wc -l | tr -d ' ')
echo "held $HELD  take $TAKE  out $OUT"
echo "1. start file: $($PY "$LANE/engine_assemble.py" "$HELD" "$W/base.csv" ${TAKES:-} "$TAKE" | cut -c1-120)"
echo "   $COUNT n to polish: $NSLIST"

echo "2. fq quench (log $W/fq.log)"
(cd "$LANE" && SQ_TMP="$W/tmp" $PY engine_polish.py "$W/fq" --sub "$W/base.csv" --ns "$NSLIST" --jobs "$JOBS" --n-limit "$N_LIMIT") > "$W/fq.log" 2>&1 &
FQ=$!; LATE=
while kill -0 $FQ 2>/dev/null; do
    if [ -s "${DEADLINE_FILE:-}" ] && [ "$(date +%s)" -gt "$(cat "$DEADLINE_FILE")" ]; then
        # each fq call that ends this way returns nothing, so every n keeps what it had certified before
        [ -n "$LATE" ] || echo "   deadline passed $(date -u +%H:%M:%S): ending the fq calls"
        LATE=1; pkill -f "fq quench --in $W/tmp/" || true; sleep 0.3
    else
        sleep 2
    fi
done
wait $FQ || [ -n "$LATE" ]
echo "   $(tail -1 "$W/fq.log")"

SOFTNS=$(tr ',' '\n' <<<"$NSLIST" | awk -v skip=" $(tr ',' ' ' <<<"${FQ_ONLY:-}") " 'index(skip, " " $1 " ") == 0')
if [ "$SOFT_SECONDS" != 0 ] && [ -n "$SOFTNS" ] && [ -z "$LATE" ]; then
    echo "3. soft-box search, $SOFT_SECONDS s per n on $(wc -l <<<"$SOFTNS" | tr -d ' ') n: $(paste -sd, - <<<"$SOFTNS") (logs $W/soft/run-*.log)"
    $PY "$LANE/engine_assemble.py" "$W/base.csv" "$W/base2.csv" "$W/fq" > /dev/null
    # one process per n; a search that fails (its log says why) does not stop the others.
    # The n goes in as $1: macOS xargs -I refuses a command longer than 255 bytes.
    # An n whose turn comes after the deadline is skipped: the deadline also holds for a long list.
    export W LANE S SOFT_SECONDS DL=${DEADLINE_FILE:-}
    xargs -P "$JOBS" -n 1 <<<"$SOFTNS" sh -c 'if [ -s "$DL" ] && [ "$(date +%s)" -gt "$(cat "$DL")" ]; then
        echo "   deadline passed: no soft search on n=$1"; exit 0; fi
        cd "$LANE" && "$S/venv/bin/python" -I methods_soft.py \
        "$W/base2.csv" "$W/soft" --n "$1" --seconds "$SOFT_SECONDS" > "$W/soft/run-$1.log" 2>&1 || echo "   soft search failed on n=$1"' sh
    echo "   $(ls "$W/soft/raw" 2>/dev/null | wc -l | tr -d ' ') n with a find"
else
    echo "3. soft-box search skipped (SOFT_SECONDS=0, FQ_ONLY names every n, or the deadline passed)"
fi

echo "4. take (log $W/take.log)"
$PY "$LANE/tools/polish_take.py" "$DET" "$W" "$OUT" "$NSLIST" ${TAKES:-} "$TAKE" | tee "$W/take.log" | tail -1
echo "take dir: $OUT"
echo "next: engine_assemble.py $HELD OUT.csv ${TAKES:-} $TAKE $OUT, then the gate with --last $(dirname "$DET")"
