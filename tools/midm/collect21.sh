#!/bin/sh
# collect21.sh [final]: round 21. Fetch the raw kick results from boxE, certify them on boxA (one light
# process) against the round 19 file and every take-*-r20 and take-*-r21 dir, let the kick worker on boxE give
# each new certified file one fq quench between two scans (fqin/GO -> fqout/DONE), certify again and write the take dir.
# Without "final" the take dir is not touched: the result goes to work/stage2 for a look.
BOX=$SCRATCH/bounties-squares; T=$BOX/take-midm-r21; W=$T/work
L=.; PY=$BOX/venv/bin/python
export MIDM_CACHE=$W/floatsafe-cache.pkl MIDM_LIVE="$BOX/take-*-r20 $BOX/take-*-r21" MIDM_SNAPS=$W MIDM_TAGSDIR=$W
HELD=$BOX/gate/cand-round19-1112a/details.csv; S=boxE; SD=scratch/squares-midm
mkdir -p $W/raw-in $W/raw-fq $W/raw-own $W/stage1 $W/fqdone $W/fqnew
ssh $S "/bin/sh $SD/fetch.sh"
rsync -a --delete "$S:$SD/out-raw/" $W/raw-in/
rm -rf $W/stage1; MIDM_TAGSDIR=$W/stage1 $PY $L/midm_take.py $HELD $T $L/results $W/raw-in --stage $W/stage1 | grep -v '^drop' ; ls $W/stage1/*.csv > /dev/null 2>&1 || { echo "nothing certified"; exit 0; }
rm -rf $W/fqnew; mkdir -p $W/fqnew; new=0
for f in $W/stage1/*.csv; do
  b=$(basename $f)
  cmp -s $f $W/fqdone/$b || { cp $f $W/fqnew/$b; new=$((new + 1)); }
done
if [ $new -gt 0 ]; then
  cp $W/stage1/TAGS.tsv $W/fqnew/TAGS.tsv
  ssh $S "cd $SD && rm -rf fqin fqout && mkdir fqin"
  rsync -a $W/fqnew/ "$S:$SD/fqin/"
  if ssh $S "pgrep -f kw.py > /dev/null"; then
    ssh $S "touch $SD/fqin/GO"          # the kick worker runs the quench between two scans
    i=0
    while [ $i -lt 48 ]; do
      ssh $S "test -e $SD/fqout/DONE" && break
      sleep 10; i=$((i + 1))
    done
  else                                  # no worker: the slot is free, run the quench here
    ssh $S "cd $SD && nice -n 5 \$HOME/scratch/squares-base/venv/bin/python midm_fqonce.py fqin fqout \$HOME/scratch/squares-base/fq x > logs/fqonce.out 2>&1; touch fqout/DONE"
  fi
  if ssh $S "test -e $SD/fqout/DONE"; then
    rsync -a --exclude tmp --exclude DONE "$S:$SD/fqout/" $W/raw-fq/ 2>/dev/null
    for f in $W/fqnew/*.csv; do cp $f $W/fqdone/$(basename $f); done
  else
    echo "the fq quench did not end in 8 minutes: these files are written without it this time"
  fi
fi
if [ "$1" = final ]; then
  $PY $L/midm_take.py $HELD $T $L/results $W/raw-in $W/raw-fq | grep -v '^drop'
else
  rm -rf $W/stage2; MIDM_TAGSDIR=$W/stage2 $PY $L/midm_take.py $HELD $T $L/results $W/raw-in $W/raw-fq --stage $W/stage2 | grep -v '^drop'
fi
echo COLLECT-DONE
