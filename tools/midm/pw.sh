#!/bin/sh
# pw.sh ID: one worker. It takes one unclaimed line at a time from the queue files named in prio.txt, in that
# order, until ./deadline passes or STOP exists. A queue file Q runs into the dir named in Q.out (default run/s6).
# A line is claimed by making claims3/<kind>-<n>-<seed>, so several workers share the queues and no line runs twice.
# While the file PAUSE exists the worker takes no new line, so a collect can use its slot for the fq quench:
# touch PAUSE, wait until "workerc.sh one-ID.q" is gone, collect, rm PAUSE.
cd "$(dirname "$0")"; id=$1; mkdir -p claims3
while :; do
  [ -e STOP ] && exit 0
  [ $(( $(cat deadline) - $(date +%s) )) -lt 90 ] && exit 0
  if [ -e PAUSE ]; then sleep 10; continue; fi
  got=0
  for q in $(cat prio.txt); do
    [ -e "$q" ] || continue
    while read kind n sub secs seed a b; do
      [ -z "$kind" ] && continue
      if mkdir "claims3/$kind-$n-$seed" 2>/dev/null; then
        echo "$kind $n $sub $secs $seed $a $b" > "one-$id.q"
        out=$(cat "$q.out" 2>/dev/null || echo run/s6)
        date -u +"%H:%M:%S $q $kind $n $seed -> $out"
        /bin/sh workerc.sh "one-$id.q" "$out" < /dev/null
        got=1; break
      fi
    done < "$q"
    [ $got = 1 ] && break
  done
  [ $got = 0 ] && sleep 15
done
