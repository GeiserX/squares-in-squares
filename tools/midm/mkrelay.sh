#!/bin/sh
# mkrelay.sh: queue one more kick leg from every scan of seed 19 or more that ended with a find worth 3e-8 of
# score or more. The leg starts from the last raw file of that scan and gets the seed of the scan plus 100, so a
# chain of legs goes on until a leg finds less. relayed.txt keeps every ended scan that was looked at.
cd "$(dirname "$0")"; touch relayed.txt
for f in run/s6/scan-*.tsv run/s10/scan-*.tsv run/s1[7-9]/scan-*.tsv run/s2[0-9]/scan-*.tsv; do
  [ -e "$f" ] || continue
  d=$(dirname "$f"); b=$(basename "$f" .tsv); n=$(echo "$b" | cut -d- -f2); s=$(echo "$b" | cut -d- -f3)
  [ "$s" -ge 19 ] || continue
  grep -q "^$d $n $s\$" relayed.txt && continue
  e=$(grep -h "^# END" "$f" | tail -1); [ -z "$e" ] && continue
  echo "$d $n $s" >> relayed.txt
  set -- $(echo "$e" | sed 's/.*finds \([0-9]*\) best \([0-9.]*\) held \([0-9.]*\).*/\1 \2 \3/')
  [ "$1" -gt 0 ] || continue
  ok=$(awk -v b="$2" -v h="$3" -v n="$n" 'BEGIN{print ((h-b)/sqrt(n) >= 3e-8) ? 1 : 0}')
  [ "$ok" = 1 ] || continue
  r=$(ls $d/raw/$n-*-$s-$1.csv 2>/dev/null | head -1); [ -z "$r" ] && continue
  q=qrelay$(echo "$d" | sed 's|run/s||').q
  secs=150; [ "$n" -ge 700 ] && secs=200; [ "$n" -ge 900 ] && secs=260
  echo "scan $n $r $secs $((s + 100)) kick,lkick 0" >> "$q"
  [ -e "$q.out" ] || echo "$d" > "$q.out"
  date -u +"%H:%M:%S relay $n from $r seed $((s + 100)) -> $q"
done
