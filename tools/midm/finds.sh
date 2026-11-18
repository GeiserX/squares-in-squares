cd $SCRATCH/squares-midm
for f in run/s[2-9]/scan-*.tsv run/s1[07-9]/scan-*.tsv run/s2[0-9]/scan-*.tsv run/relay/scan-*.tsv; do
  [ -e "$f" ] || continue
  grep -h "^# FIND" "$f" | tail -1 | sed "s|^|$f |"
done
