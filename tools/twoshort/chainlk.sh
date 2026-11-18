#!/bin/zsh
# chainlk.sh N START TAG SEED0 STEPS : (round 21) a chain of invent_rest.py lkick runs without fq, 300 s each: each run starts from the
# best file so far; the seed goes up by one each run; stops after STEPS runs, after 3 runs in a row with no find, or 6 min before the
# deadline. Dir k21/c<N><TAG>/, log chain.log (one line per run: seed, start side, best side, file)
cd $SCRATCH/squares-twoshort
PY=$SCRATCH/squares-base/venv/bin/python
n=$1; cur=$2; tag=$3; s=$4; steps=$5; D=k21/c$n$tag; mkdir -p $D; miss=0
for i in $(seq 1 $steps); do
  [ $(( $(date -u +%s) + 360 )) -gt $(cat deadline) ] && break
  bar=$(grep "^$n," details-bar.csv | cut -d, -f2)
  nice -n 5 $PY -I lane/invent_rest.py $n $cur $D/s$s --seconds 300 --seed $s --modes lkick --bar $bar --deadline deadline > $D/s$s.log 2>&1
  f=$(grep BEST $D/s$s/slide-*.tsv 2>/dev/null | tail -1 | cut -f1)
  if [ -n "$f" ] && [ -f $D/s$s/raw/$n-sl$s-$f.csv ]; then cur=$D/s$s/raw/$n-sl$s-$f.csv; miss=0; else miss=$((miss+1)); fi
  echo "$(date -u +%H:%M:%S) seed $s: $(tail -1 $D/s$s.log) -> $cur" >> $D/chain.log
  [ $miss -ge 3 ] && break
  s=$((s+1))
done
echo "$(date -u +%H:%M:%S) END $cur" >> $D/chain.log
