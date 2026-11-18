#!/bin/sh
# quench (round 28): fq's own kick on a certified best row, for a box with no python (boxD).
# Each try kicks the best file so far (fq quench --kick SIGMA --loosen L --seed S), polishes it with the deep flags,
# and keeps it when the side drops by more than 3e-9. Midm's fq kicks of round 24 gave 8 rows (0.0011).
# Usage: quench_fqkick.sh JOBDIR FQ DEADLINE_EPOCH
#   JOBDIR/in.txt      the start as fq text (quench_once.py prep --no-cert)
#   JOBDIR/fqkick.txt  "N SEED SECONDS"
#   writes JOBDIR/out.txt (the best file), box.log and, last, done
J=$1; FQ=$2; DL=$3
POLISH="--no-alm --loosen 1.0 --flip-top 64 --pit 600"
cd "$J" || exit 2
rm -f done out.txt
read N SEED SEC < fqkick.txt
cp in.txt best.txt
side() { head -1 "$1" | awk '{print $2}'; }
end=$(( $(date +%s) + SEC )); [ $end -gt $((DL - 60)) ] && end=$((DL - 60))
i=0; finds=0
while [ "$(date +%s)" -lt $end ]; do
  i=$((i + 1))
  case $((i % 4)) in 1) sig=0.003;; 2) sig=0.01;; 3) sig=0.02;; 0) sig=0.04;; esac
  case $((i % 2)) in 1) lo=1.0;; 0) lo=1.005;; esac
  left=$((end - $(date +%s))); [ $left -le 5 ] && break; [ $left -gt 150 ] && left=150
  rm -f k.txt p.txt
  perl -e 'alarm shift; exec @ARGV' $left "$FQ" quench --in best.txt --out k.txt --loosen $lo --kick $sig --seed $((SEED * 1000 + i)) > /dev/null 2>&1
  [ -s k.txt ] || { echo "try $i kick $sig loosen $lo: no output" >> box.log; continue; }
  left=$((end - $(date +%s) + 30)); [ $left -gt 150 ] && left=150
  perl -e 'alarm shift; exec @ARGV' $left "$FQ" quench --in k.txt --out p.txt $POLISH > /dev/null 2>&1
  [ -s p.txt ] || cp k.txt p.txt
  a=$(side best.txt); b=$(side p.txt)
  if awk -v a="$a" -v b="$b" 'BEGIN{exit !(b < a - 3e-9)}'; then
    mv p.txt best.txt; finds=$((finds + 1)); echo "try $i kick $sig loosen $lo: find $a -> $b" >> box.log
  else
    echo "try $i kick $sig loosen $lo: $b (best $a)" >> box.log
  fi
done
echo "fqkick n=$N seed $SEED tries $i finds $finds start $(side in.txt) best $(side best.txt)" >> box.log
mv best.txt out.txt
echo "ran=1 fqkick" > done
