#!/bin/bash
# quench: the collect loop. Every 30 s it rebuilds the live bar, runs `quench_once.py take` once on each
# finished job, republishes the take dir (quench_publish.py, which walks each start again first), logs a
# PUBLISH line in STATE.txt and posts one handoff line per new or lowered n.
# Usage: quench_collect.sh SCRATCH TAKEDIR ROUND BASE_DETAILS.csv DEADLINE_EPOCH
#   runs until 7 minutes after the deadline, so jobs that end at the deadline still get collected
S=$1; T=$2; R=$3; BASE=$4; DL=$5
L=$(cd "$(dirname "$0")" && pwd); PY=$S/venv/bin/python
cd "$S" || exit 2
while [ "$(date +%s)" -lt $((DL + 420)) ]; do
  new=0
  $PY -I $L/quench_bar.py $BASE $T/work/bar-collect.tsv $(ls $S/take-*-$R/take.tsv | grep -v "^$T/") > /dev/null 2>&1
  BAR=$T/work/bar-collect.tsv
  [ -s $BAR ] || { sleep 30; continue; }  # no bar this time: never take a job against nothing
  for J in $T/work/jobs/*/; do J=${J%/}
    [ -e $J/done ] && [ ! -e $J/result.json ] && [ -e $J/source.txt ] || continue
    r=$($PY -I $L/quench_once.py take $J $BAR 2>&1 | tail -1)
    echo "$(date -u +%FT%TZ) COLLECT $(basename $J): $r" >> $T/work/collect.log
    echo "$r" | grep -q '"counts": true' && new=1
  done
  if [ $new = 1 ] || ! cmp -s $BAR $T/work/bar-published.tsv; then
    cp $BAR $T/work/bar-published.tsv
    old=$(cut -f1,3 $T/take.tsv 2>/dev/null | tail -n +2)
    p=$($PY -I $L/quench_publish.py $T $BAR $S $R)
    nw=$(cut -f1,3 $T/take.tsv | tail -n +2)
    if [ "$old" != "$nw" ]; then
      echo "$(date -u +%FT%TZ) $(hostname -s) PUBLISH take.tsv: $p" >> $T/STATE.txt
      echo "$nw" | while read -r n s; do
        [ -n "$n" ] || continue  # an empty take.tsv gives one empty line (round 26 posted 'n=' lines)
        echo "$old" | grep -q "^$n	$s\$" && continue
        echo "$(date -u +%FT%TZ) quench -> all: certified n=$n, score=$s, one fq quench of a clean start (walked by quench_walk.py), $T/$n.csv; source in $T/take.tsv" >> $S/handoff-$R.log
      done
    fi
  fi
  sleep 30
done
