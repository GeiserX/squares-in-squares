#!/bin/sh
# worker.sh ID: takes the first line of queue.txt (under qlock) and runs chain.sh on it, until ./deadline or ./STOP
D=$(cd "$(dirname "$0")" && pwd); cd "$D"
while :; do
  [ -e STOP ] && break
  [ $(( $(cat deadline) - $(date +%s) )) -lt 100 ] && break
  line=""
  if mkdir qlock 2> /dev/null; then
    line=$(head -1 queue.txt)
    if [ -n "$line" ]; then tail -n +2 queue.txt > queue.tmp; mv queue.tmp queue.txt; echo "$line w$1 $(date -u +%H:%M:%S)" >> taken.txt; fi
    rmdir qlock
  fi
  if [ -z "$line" ]; then sleep 10; continue; fi
  "$D/chain.sh" $line
done
echo "worker $1 ended $(date -u +%H:%M:%S)" >> drv.out
