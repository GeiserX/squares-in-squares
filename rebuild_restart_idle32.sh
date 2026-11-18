#!/bin/zsh
# restart_idle.sh ROOT PY FQ: replace each running lane/rebuild_run.py worker of ROOT, when it has no child (idle between jobs),
# by a new worker on the current lane code (round 32: lk mode). Ends when every old worker is replaced.
R=$1; P=$2; FQ=$3; cd $R
old=($(pgrep -f "lane/rebuild_run.py $R"))
echo "$(date -u +%T) old workers: $old" >> restart.log
i=0
while [ ${#old} -gt 0 ]; do
  keep=()
  for p in $old; do
    if [ -z "$(pgrep -P $p)" ]; then
      kill $p; i=$((i+1))
      REBUILD_TRIAGE=0.002 nohup nice -n 5 $P -I lane/rebuild_run.py $R $FQ $P > worker-r$i.log 2>&1 < /dev/null &
      echo "$(date -u +%T) replaced $p by $!" >> restart.log
    else
      keep+=($p)
    fi
  done
  old=($keep)
  sleep 2
done
