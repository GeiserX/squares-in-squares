cd $SCRATCH/squares-midm
for d in run/s2 run/s3 run/s4 run/s5 run/s6 run/s7 run/s8 run/s9 run/s10 run/s17 run/s18 run/s19 run/s2[0-9] run/relay run/wctl; do
  for f in $d/scan-*.tsv; do [ -e "$f" ] || continue; grep -h "^# END\|^# WALK" "$f" | sed "s|^|$d |; s|\$| file=$(basename "$f")|"; done
done
