#!/bin/sh
# fetch.sh (on boxE): put every raw result of the round 19 kick run into out-raw/ as <n>-<tag>@<dir>.csv.
cd "$(dirname "$0")"; rm -rf out-raw; mkdir out-raw
for f in run/s[3-9][0-9]/raw/*.csv; do
  [ -e "$f" ] || continue
  b=$(basename "$f" .csv); n=${b%%-*}; rest=${b#*-}; d=$(dirname "$(dirname "$f")" | tr / _)
  cp "$f" "out-raw/$n-$rest@$d.csv"
done
ls out-raw | wc -l
