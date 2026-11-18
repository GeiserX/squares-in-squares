#!/bin/zsh
# holdlk.sh ROOT: while an old (pre-lk) worker of ROOT runs, keep lk: lines out of queue.tsv (in queue.hold); when the
# restart log shows every old worker replaced, put them back and exit
R=$1; cd $R; touch queue.hold
while true; do
  if [ -z "$(pgrep -f restart_idle.sh)" ]; then
    cat queue.hold >> queue.tsv; : > queue.hold; echo "$(date -u +%T) holdlk: restored" >> restart.log; exit 0
  fi
  if grep -q $'\tlk:' queue.tsv; then
    grep $'\tlk:' queue.tsv >> queue.hold; grep -v $'\tlk:' queue.tsv > queue.tmp; mv queue.tmp queue.tsv
  fi
  sleep 1
done
