#!/bin/sh
# chain.sh N TAG [MODE]: the chain of one start, from starts/N-TAG.csv. No soft process runs past ./deadline.
#   pass   the 140 s island at --delta 2e-4 and then at 1e-4; on a find, one island (--seconds 1800 --dry 360)
#          from the best packing and then the fq quench of its result
#   full   the same, and the island runs when the two 140 s islands found nothing too
#   corner two 60 s islands, with an immediate quench on a find
#   probe  two 20 s islands, with an immediate quench on a find
#   short  the two 140 s islands only; a find gets the fq quench and no island
#   again  one island and, on a find, the quench (a packing the quench changed, or an n that owes an island)
#   island one island (seed 14) from a start whose pass was dry, and the quench on a find (an idle slot)
#   seed2  pass with the seeds 21 to 23 instead of 11 to 13 (a packing that had its pass with no find)
#   lpq    round 29: the LP follow of border and then the fq loop (a legal file just above the bar)
#   lk     round 32: 150 s invent_rest.py lkick legs (lkleg.py) of a held row, then fq on a move
#   kick   round 30: kickleg.py legs from the start itself, then fq (a file 2e-5 to 1.2e-4 of score over the bar)
#   round 30: every chain that reaches its fq quench then runs kickleg.py (900 s kick scan within 2.5e-4 of the bar) and fq
#   sfq    round 28: one 420 s island at delta 1e-4 that keeps its soft-free members, then the fq quench of each member
#          (sfq.py), then the fq quench of the best legal result if there is one
D=$(cd "$(dirname "$0")" && pwd); cd "$D"
LEGS=140; [ -f legs ] && LEGS=$(cat legs)
n=$1; tag=$2; mode=${3:-pass}; out=run/$n-$tag; mkdir -p $out
[ "$mode" = probe ] && LEGS=20
[ "$mode" = corner ] && LEGS=60
b=10; [ "$mode" = seed2 ] && b=20
if [ "$mode" = certified ]; then
  "$D/py" "$D/fqjob.py" $n $tag >> $out/chain.log 2>&1
  rc=$?
  if [ $rc -eq 0 ] || [ $rc -eq 3 ]; then
    echo "CHAINEND n=$n tag=$tag mode=certified $(date -u +%H:%M:%S)" >> $out/chain.log
  fi
  exit 0
fi
if [ "$mode" = deep ]; then
  # round 33 (main session 21:46Z shared deep-kick queue): one unprobed 900 s midm_scan kick,lkick seed of a held row with no
  # 900 s kick since its current geometry (legs only while a leg moves), then the full fq loop. This round 900 s kicks of
  # held rows paid on 701 and 812 while 150 s lkicks of the same pool were dry.
  mkdir -p $out/raw
  if KICKNOPROBE=1 "$D/py" "$D/kickleg.py" $n $tag >> $out/chain.log 2>&1; then
    "$D/py" "$D/fqjob.py" $n $tag >> $out/chain.log 2>&1
  fi
  echo "CHAINEND n=$n tag=$tag mode=deep $(date -u +%H:%M:%S)" >> $out/chain.log
  exit 0
fi
if [ "$mode" = kick ]; then
  # round 30 (14:40Z): kick legs straight from the start (no island), then fq: forensics rectangle files 2e-5 to 1.2e-4 of
  # score over the bar that no lane claimed (kickleg on island results gained 2.5e-5 to 3.0e-5 from 1.3e-4 to 1.4e-4 over)
  mkdir -p $out/raw
  if "$D/py" "$D/kickleg.py" $n $tag >> $out/chain.log 2>&1; then
    "$D/py" "$D/fqjob.py" $n $tag >> $out/chain.log 2>&1
  fi
  echo "CHAINEND n=$n tag=$tag mode=kick $(date -u +%H:%M:%S)" >> $out/chain.log
  exit 0
fi
if [ "$mode" = lk ]; then
  # round 32: twoshort-style 150 s invent_rest lkick legs of a held row no lane kicked in rounds 29 to 32 (lkleg.py), then
  # fq of the best when a leg moved the side (twoshort r31: 12 of 121 such rows moved, 2 of 70 for 900 s midm probes)
  mkdir -p $out/raw
  if "$D/py" "$D/lkleg.py" $n $tag >> $out/chain.log 2>&1; then
    echo "FQSTART n=$n tag=$tag $(date -u +%H:%M:%S)" >> $out/chain.log
    "$D/py" "$D/fqjob.py" $n $tag >> $out/chain.log 2>&1
  fi
  echo "CHAINEND n=$n tag=$tag mode=lk $(date -u +%H:%M:%S)" >> $out/chain.log
  exit 0
fi
if [ "$mode" = lpq ]; then
  # round 29: border's LP follow (methods_lp.py, 40 iterations) and then the fq loop of fqjob.py (default and polish
  # flags, up to three rounds), for a legal file just above the bar (r28 near 417: 1.2e-11 of score over bar29)
  "$D/py" "$D/methods_lp.py" starts/$n-$tag.csv $out/lp --ns $n --jobs 1 --iters 40 >> $out/chain.log 2>&1
  if [ -s $out/lp/raw/$n.csv ]; then mkdir -p $out/raw && cp $out/lp/raw/$n.csv $out/raw/$n-lp-1.csv; fi
  echo "FQSTART n=$n tag=$tag $(date -u +%H:%M:%S)" >> $out/chain.log
  "$D/py" "$D/fqjob.py" $n $tag >> $out/chain.log 2>&1
  if [ -f "$D/kickleg.py" ] && [ ! -e $out/STOP ] && "$D/py" "$D/kickleg.py" $n $tag >> $out/chain.log 2>&1; then
    "$D/py" "$D/fqjob.py" $n $tag >> $out/chain.log 2>&1
  fi
  echo "CHAINEND n=$n tag=$tag mode=lpq $(date -u +%H:%M:%S)" >> $out/chain.log
  exit 0
fi
left() { echo $(( $(cat deadline) - $(date +%s) )); }
found() { ls $out/raw/$n-best-*.csv > /dev/null 2>&1; }
leg() { # delta seed seconds dry
  l=$(left); s=$3
  [ -e $out/STOP ] && { echo "STOPPED n=$n tag=$tag $(date -u +%H:%M:%S)" >> $out/chain.log; return 1; }
  [ $l -lt 90 ] && { echo "SKIP n=$n tag=$tag seed=$2 left=$l" >> $out/chain.log; return 1; }
  [ $l -lt $s ] && s=$((l - 15))
  src=$("$D/py" bestof.py $n $tag)
  echo "LEG n=$n tag=$tag delta=$1 seed=$2 s=$s dry=$4 src=$src $(date -u +%H:%M:%S)" >> $out/chain.log
  "$D/py" "$D/softjob.py" $((s + 45)) "$D/py" "$D/methods_soft.py" $src $out --n $n --delta $1 --seed $2 --seconds $s --dry $4 $EXTRA >> $out/chain.log 2>&1
  return 0
}
EXTRA=""
if [ "$mode" = sfq ]; then
  EXTRA="--keep-softfree 1"
  leg 1e-4 41 420 400 || exit 0
  echo "SFQSTART n=$n tag=$tag $(date -u +%H:%M:%S)" >> $out/chain.log
  "$D/py" "$D/sfq.py" $n $tag 12 >> $out/chain.log 2>&1
  found || { echo "DRY n=$n tag=$tag mode=sfq $(date -u +%H:%M:%S)" >> $out/chain.log; exit 0; }
elif [ "$mode" = again ] && [ -f "$D/kickleg.py" ] && "$D/py" "$D/kickleg.py" $n $tag >> $out/chain.log 2>&1; then
  # round 30 (15:40Z): an again leg runs kick legs when the chain's best is within 2.5e-4 of the bar (again islands: 0 of 4
  # found this round; kick legs gained on 910 three times in a row), and the island again only when kickleg skips
  KICKED=1
elif [ "$mode" = again ] || [ "$mode" = island ]; then
  # round 27: an again leg takes a fresh seed (round 26: the again island on 791 reran seed 14 and repeated the first one)
  sd=14; if [ "$mode" = again ]; then c=$(grep -c '^LEG' $out/chain.log 2>/dev/null); sd=$((30 + ${c:-0})); fi
  leg 2e-4 $sd 1800 360 || exit 0
  [ -e $out/raw/$n-best-$sd.csv ] || { echo "DRY-AGAIN n=$n tag=$tag seed=$sd $(date -u +%H:%M:%S)" >> $out/chain.log; exit 0; }
else
  leg 2e-4 $((b + 1)) $LEGS 0
  leg 1e-4 $((b + 2)) $LEGS 0
  if ! found && [ "$mode" != full ] && [ "$mode" != corner ]; then echo "DRY n=$n tag=$tag $(date -u +%H:%M:%S)" >> $out/chain.log; exit 0; fi
  if [ "$mode" != short ] && [ "$mode" != probe ] && [ "$mode" != corner ]; then
    d=2e-4; if found && [ ! -e $out/raw/$n-best-$((b + 1)).csv ]; then d=1e-4; fi
    leg $d $((b + 3)) 1800 360
    found || { echo "DRY n=$n tag=$tag mode=$mode $(date -u +%H:%M:%S)" >> $out/chain.log; exit 0; }
  fi
fi
echo "FQSTART n=$n tag=$tag $(date -u +%H:%M:%S)" >> $out/chain.log
# no island after the quench: rounds 11 to 13 ran 5 such islands and none found
"$D/py" "$D/fqjob.py" $n $tag >> $out/chain.log 2>&1
# round 30: one 900 s kick scan (midm_scan kick,lkick) of the result when it is within 2.5e-4 of score of the bar, then fq
if [ -z "$KICKED" ] && [ -f "$D/kickleg.py" ] && [ ! -e $out/STOP ] && "$D/py" "$D/kickleg.py" $n $tag >> $out/chain.log 2>&1; then
  "$D/py" "$D/fqjob.py" $n $tag >> $out/chain.log 2>&1
fi
echo "CHAINEND n=$n tag=$tag mode=$mode $(date -u +%H:%M:%S)" >> $out/chain.log
exit 0
