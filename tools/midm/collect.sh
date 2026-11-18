#!/bin/sh
# collect.sh [final]: fetch the raw results of the slice run from boxE, certify them on boxA (one light
# process), give each certified file one fq quench on boxE, certify again and write the take dir.
# Without "final" the take dir is not touched: the result goes to work/stage2 for a look.
# The fq quench runs only on the certified files that are new or changed since the last call (work/fqdone keeps
# the files already quenched), so a call during the run adds one short process on boxE, not a long one.
BOX=$SCRATCH/bounties-squares; T=$BOX/take-midm-r17; W=$T/work
L=.; PY=$BOX/venv/bin/python
export MIDM_R16=$W/r16.tsv MIDM_R17=$W/r17.tsv MIDM_R18=$W/r18.tsv MIDM_HELD2=$BOX/gate/cand-round16-1112a/details.csv MIDM_CACHE=$W/floatsafe-cache.pkl
export MIDM_LIVE="$BOX/take-*-r17" MIDM_SNAPS=$W
HELD=$BOX/gate/cand-round15-1112a/details.csv; S=boxE; SD=scratch/squares-midm
mkdir -p $W/raw-in $W/raw-fq $W/stage1 $W/fqdone $W/fqnew
ssh $S "/bin/sh $SD/fetch.sh"
rsync -a --delete "$S:$SD/out-raw/" $W/raw-in/
rm -rf $W/stage1; $PY $L/midm_take.py $HELD $T $L/results $W/raw-in --stage $W/stage1 | grep -v '^drop' ; ls $W/stage1/*.csv > /dev/null 2>&1 || { echo "nothing certified"; exit 0; }
rm -rf $W/fqnew; mkdir -p $W/fqnew; new=0
for f in $W/stage1/*.csv; do
  b=$(basename $f)
  cmp -s $f $W/fqdone/$b || { cp $f $W/fqnew/$b; new=$((new + 1)); }
done
if [ $new -gt 0 ]; then
  cp $W/stage1/TAGS.tsv $W/fqnew/TAGS.tsv
  ssh $S "cd $SD && rm -rf fqin fqout && mkdir fqin"
  rsync -a $W/fqnew/ "$S:$SD/fqin/"
  ssh $S "cd $SD && nice -n 5 \$HOME/scratch/squares-base/venv/bin/python midm_fqonce.py fqin fqout \$HOME/scratch/squares-base/fq x"
  rsync -a --exclude tmp "$S:$SD/fqout/" $W/raw-fq/ 2>/dev/null
  for f in $W/fqnew/*.csv; do cp $f $W/fqdone/$(basename $f); done
fi
if [ "$1" = final ]; then
  $PY $L/midm_take.py $HELD $T $L/results $W/raw-in $W/raw-fq | grep -v '^drop'
else
  rm -rf $W/stage2; $PY $L/midm_take.py $HELD $T $L/results $W/raw-in $W/raw-fq --stage $W/stage2 | grep -v '^drop'
fi
