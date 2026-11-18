#!/bin/sh
# quench: one fq quench of one certified file, on a box with no python.
# The loop of midm_fqonce.py: fq default flags, then the deep flags, up to six
# rounds while a round lowers the side by more than 3e-9. Round 28 raised three to six: 4 of 221 round 27 jobs still gained at round 3.
# Usage: quench_box.sh JOBDIR FQ DEADLINE_EPOCH
#   JOBDIR/in.txt   the certified file as fq text (quench_once.py prep)
#   writes JOBDIR/out.txt (the best side reached, or a copy of in.txt),
#   JOBDIR/box.log and, last, JOBDIR/done
J=$1; FQ=$2; DL=$3
POLISH="--no-alm --loosen 1.0 --flip-top 64 --pit 600"
cd "$J" || exit 2
rm -f done out.txt best.txt
cp in.txt cur.txt
side() { head -1 "$1" | awk '{print $2}'; }
ran=0
r=1
while [ $r -le 6 ]; do
  improved=0
  for fl in default polish; do
    now=$(date +%s); left=$((DL - now))
    [ $left -le 5 ] && break
    [ $left -gt 180 ] && left=180
    if [ $fl = default ]; then flags=""; else flags=$POLISH; fi
    rm -f try.txt
    perl -e 'alarm shift; exec @ARGV' $left "$FQ" quench --in cur.txt --out try.txt $flags >> box.log 2>&1
    rc=$?
    if [ $rc -eq 0 ] && [ -s try.txt ]; then
      ran=1
      a=$(side cur.txt); b=$(side try.txt)
      echo "round $r $fl rc=$rc $a -> $b" >> box.log
      # round 29: keep the lowest raw side of any try in best.txt, even a gain under 3e-9 (the loop threshold).
      # The polish of a certified file ends about 1e-9 lower (the dilation it removes); with the finer
      # certify step part of that stays (r28 fo-503 polish: 22.8935875555 -> 22.8935875544, dropped by the 3e-9 rule).
      if [ ! -s best.txt ] || awk -v a="$(side best.txt)" -v b="$b" 'BEGIN{exit !(b < a)}'; then cp try.txt best.txt; fi
      if awk -v a="$a" -v b="$b" 'BEGIN{exit !(b < a - 3e-9)}'; then
        mv try.txt cur.txt; improved=1
      fi
    else
      echo "round $r $fl rc=$rc no output" >> box.log
    fi
  done
  [ $improved -eq 0 ] && break
  r=$((r + 1))
done
mv cur.txt out.txt
echo "ran=$ran" > done
