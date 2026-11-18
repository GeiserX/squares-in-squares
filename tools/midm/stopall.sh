#!/bin/sh
# stopall.sh: stop every process of the midm lane on this box (matched by its working dir), then list what is left.
cd $SCRATCH/squares-midm || exit 0
touch STOP
for round in 1 2 3; do
  for p in $(pgrep -f "pw.sh|pwp.sh|workerc.sh|relayloop.sh|mkrelay.sh|midm_scan.py|midm_fqonce.py|midm_soft.py|methods_soft.py|relay.py|fq quench"); do
    cwd=$(lsof -a -p $p -d cwd -Fn 2>/dev/null | grep '^n' | cut -c2-)
    case "$cwd" in "$HOME/scratch/squares-midm"*) kill $p 2>/dev/null;; esac
  done
  sleep 2
done
left=0
for p in $(pgrep -f "pw.sh|pwp.sh|workerc.sh|relayloop.sh|mkrelay.sh|midm_|methods_soft.py|relay.py|fq quench"); do
  cwd=$(lsof -a -p $p -d cwd -Fn 2>/dev/null | grep '^n' | cut -c2-)
  case "$cwd" in "$HOME/scratch/squares-midm"*) left=$((left + 1)); ps -o pid=,command= -p $p | cut -c1-120;; esac
done
echo "midm processes left: $left"
