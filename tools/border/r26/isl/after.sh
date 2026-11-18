#!/bin/sh
# isl/after.sh: wait for run2.sh to end, then run run3.sh (one island process at a time).
cd "$(dirname "$0")"
until grep -q -E "DONE2|SKIP" run.log; do sleep 10; done
exec ./run3.sh
