#!/bin/bash
# The polish of what a round's builders write while they still write it, in one command:
#
#   tools/polish_follow.sh BASE_DETAILS.csv OUT_TAKE_DIR DEADLINE_FILE 'TAKE_DIR_GLOB' ['TAKE_DIR_GLOB' ...]
#
# Every LOOK seconds (default 900, or at once when OUT_TAKE_DIR/follow/look.now exists), tools/take_lowest.py
# --seen writes per n the lowest certified file of the take dirs the globs match now that is new since the
# last look. Each n gets its own start dir and a line in the high queue, by gain over held; a newer file of an
# n replaces its waiting line. SLOTS workers (default 2) each run daily_polish.sh on one n at a time (fq only,
# 1 process) and add what it certifies to OUT_TAKE_DIR. When the high queue is empty a worker takes the next n
# of LOW (space separated) from the held packing, unless a builder holds a lower file of it.
#
# Near files: at each look tools/near_starts.py also reads the csv files under any near/ folder of those take
# dirs, and of the dirs NEAR_DIRS matches (space separated globs, for example a take dir of the round before).
# A builder writes there a layout that certifies a little above the held score. Per n the lowest new one within
# NEAR_MAX of the held score (default 2e-5; 0 turns this off) goes to the near queue, which the workers take
# after the high queue and before LOW. The fq quench may take it under held, and only then is it kept.
#
# DEADLINE_FILE holds a time in epoch seconds and can be rewritten while the run goes. At that time the looks
# stop, each worker's fq call ends and its take step still runs. Quote the globs: they are matched at each look.
# A dir whose name matches EXCLUDE (default polish|assemble) and OUT_TAKE_DIR itself are never read.
# Logs: OUT_TAKE_DIR/follow/queue.log (one line per look and per n). Run it under nohup; it ends by itself.
set -u
[ $# -ge 4 ] || { sed -n '2,22p' "$0"; exit 2; }
LANE=$(cd "$(dirname "$0")/.." && pwd)
S=${SQUARES_SCRATCH:-$SCRATCH/bounties-squares}
DET=$1; mkdir -p "$2"; OUT=$(cd "$2" && pwd); DL=$3; shift 3; GLOBS=("$@")
F=$OUT/follow; mkdir -p "$F/starts" "$F/work"; HI=$F/queue-hi.txt; NE=$F/queue-near.txt; LO=$F/queue-lo.txt; LOG=$F/queue.log
SLOTS=${SLOTS:-2}; LOOK=${LOOK:-900}; EXCLUDE=${EXCLUDE:-polish|assemble}; NEAR_MAX=${NEAR_MAX:-2e-5}
alive() { [ "$(date +%s)" -lt "$(cat "$DL")" ]; }
lock() { until mkdir "$F/queue.lock" 2>/dev/null; do sleep 1; done; }
unlock() { rmdir "$F/queue.lock"; }
: > "$HI"; : > "$NE"; for n in ${LOW:-}; do echo "$n $F/empty"; done > "$LO"
mkdir -p "$F/empty"; printf 'n\theld\tnew\tgain\tsource\tlicence\n' > "$F/empty/take.tsv"

worker() {
    local name=$1 line n td w
    while alive; do
        lock
        line=
        for q in "$HI" "$NE" "$LO"; do
            if [ -s "$q" ]; then line=$(head -1 "$q"); tail -n +2 "$q" > "$q.tmp"; mv "$q.tmp" "$q"; break; fi
        done
        unlock
        [ -n "$line" ] || { sleep 20; continue; }
        set -- $line; n=$1; td=$2
        if [ "$td" = "$F/empty" ] && grep -q "^$n	" "$F/seen.tsv" 2>/dev/null; then
            echo "$(date -u +%H:%M:%S) $name skip $n: a builder holds a lower file" >> "$LOG"; continue
        fi
        w=$F/work/$n-$name-$(date +%s)
        echo "$(date -u +%H:%M:%S) $name start $n from $td" >> "$LOG"
        NS=$n FQ_ONLY=$n JOBS=1 DEADLINE_FILE=$DL WORK=$w "$LANE/daily_polish.sh" "$td" "$DET" "$OUT" > "$w.out" 2>&1
        echo "$(date -u +%H:%M:%S) $name end $n exit $?: $(grep '^kept' "$w/take.log" 2>/dev/null | cut -c1-200)" >> "$LOG"
    done
}
k=0
while alive; do
    k=$((k+1)); t0=$(date +%s); st=$F/look-$k
    dirs=$(for g in "${GLOBS[@]}"; do ls -d $g 2>/dev/null; done | sort -u | grep -v -E "$EXCLUDE" | grep -v -x "$OUT")
    "$S/venv/bin/python" -I "$LANE/tools/take_lowest.py" "$DET" "$st" $dirs --seen "$F/seen.tsv" > "$st.log" 2>&1
    echo "$(date -u +%H:%M:%S) look $k: $(tail -1 "$st.log")" >> "$LOG"
    if [ -s "$st/take.tsv" ]; then
        tail -n +2 "$st/take.tsv" | sort -t$'\t' -k4,4gr | while IFS=$'\t' read -r n rest; do
            p=$F/starts/$n-$k; mkdir -p "$p"; cp "$st/$n.csv" "$p/"
            { head -1 "$st/take.tsv"; printf '%s\t%s\n' "$n" "$rest"; } > "$p/take.tsv"
            lock; { grep -v "^$n " "$HI"; echo "$n $p"; } > "$HI.tmp"; mv "$HI.tmp" "$HI"; unlock
        done
    fi
    ndirs=$( { echo "$dirs"; for g in ${NEAR_DIRS:-}; do ls -d $g 2>/dev/null; done; } | grep . | sort -u | grep -v -x "$OUT")
    if [ "$NEAR_MAX" != 0 ] && [ -n "$ndirs" ]; then
        "$S/venv/bin/python" -I "$LANE/tools/near_starts.py" "$DET" "$F/starts" "$F/seen-near.txt" "$F/seen.tsv" \
            $ndirs --max "$NEAR_MAX" --tag "$k" > "$st-near.log" 2>&1
        echo "$(date -u +%H:%M:%S) look $k: $(tail -1 "$st-near.log")" >> "$LOG"
        grep '^start ' "$st-near.log" | while read -r _ n p gap; do
            lock; echo "$n $p" >> "$NE"; unlock
        done
    fi
    [ $k = 1 ] && for i in $(seq 1 "$SLOTS"); do worker "w$i" & done     # after the first look, so it goes first
    while alive && [ "$(date +%s)" -lt $((t0 + LOOK)) ] && [ ! -e "$F/look.now" ]; do sleep 5; done
    rm -f "$F/look.now"
done
wait
echo "$(date -u +%H:%M:%S) ended at the deadline; the take dir holds $(($(wc -l < "$OUT/take.tsv" 2>/dev/null || echo 1) - 1)) n" >> "$LOG"
