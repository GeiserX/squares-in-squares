#!/bin/sh
# drive.sh K: K workers on this box; every child dies with it
D=$(cd "$(dirname "$0")" && pwd); cd "$D"
trap 'kill 0' EXIT
i=1; while [ $i -le $1 ]; do "$D/worker.sh" $i & i=$((i + 1)); done
wait
echo "done $(date -u +%H:%M:%S)" >> drv.out
