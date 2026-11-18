#!/bin/sh
# fetch.sh (on boxE): put every raw result of the slice run into out-raw/ under the name <n>-<tag>@<dir>.csv.
# The control dirs (run/ctl, run/sctl, run/s1, run/slabctl, run/pt) hold results on older files: never copied.
cd "$(dirname "$0")"; rm -rf out-raw; mkdir out-raw
for f in run/s[2-9]*/raw/*.csv run/s[2-9]*/*/raw/*.csv run/s1[07-9]/raw/*.csv run/relay/raw/*.csv run/softrelay/raw/*.csv run/slab[0-9]*/raw/*.csv; do
  [ -e "$f" ] || continue
  b=$(basename "$f" .csv); n=${b%%-*}; rest=${b#*-}; d=$(dirname "$(dirname "$f")" | tr / _)
  cp "$f" "out-raw/$n-$rest@$d.csv"
done
ls out-raw | wc -l
