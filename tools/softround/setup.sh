#!/bin/sh
# setup.sh BOX DEADLINE FQDEADLINE: the box scratch of a round (epoch seconds for the two deadlines). For boxC and boxD:
# $SCRATCH/squares-soft-r33 with a venv on the box's uv Python 3.12 (numpy 2.5.4, scipy 1.18.1; round 32: a copy of the
# box's squares-corners venv when it is there, as the quench lane does), the box scripts, the
# lane's methods_soft.py and methods_lp.py, the fq binary, starts/ and queue-BOX.txt as queue.txt. For boxA: the same
# under W/boxA with the scratch venv of boxA. Only code, the fq binary and packing csv go to a box.
PY=$SCRATCH/bounties-squares/venv/bin/python; H=$(cd "$(dirname "$0")" && pwd); W=$("$PY" -I "$H/ctl.py" where)
LANE=$(cd "$H/../.." && pwd); b=$1; dl=$2; fdl=$3
mkdir -p $W/box && cp $H/chain.sh $H/worker.sh $H/drive.sh $H/bestof.py $H/softjob.py $H/fqjob.py $H/qorder.py $LANE/methods_soft.py $LANE/methods_lp.py $LANE/midm_scan.py $H/kickleg.py $H/lkleg.py $LANE/invent_rest.py $LANE/family_step.py $LANE/frontier_stacks.py $LANE/frontier_read.py $W/box/
[ -x $W/box/fq ] || { echo "no fq binary in $W/box"; exit 1; }
if [ "$b" = boxA ]; then
  D=$W/boxA; mkdir -p $D/run $D/tmp $D/starts && cp $W/box/* $D/ && { cp $W/starts/*.csv $D/starts/ 2>/dev/null || :; } && cp $W/queue-boxA.txt $D/queue.txt
  printf '#!/bin/sh\nexec %s -I "$@"\n' "$PY" > $D/py; chmod +x $D/py; echo $dl > $D/deadline; echo $fdl > $D/fqdeadline; : > $D/taken.txt
  echo "boxA ready"; exit 0
fi
ssh -o ConnectTimeout=10 $b 'mkdir -p $SCRATCH/squares-soft-r33/run $SCRATCH/squares-soft-r33/tmp $SCRATCH/squares-soft-r33/starts' || exit 1
scp -q $W/box/* "$b:scratch/squares-soft-r33/" || exit 1
scp -q $W/starts/*.csv "$b:scratch/squares-soft-r33/starts/" 2>/dev/null || :
scp -q $W/queue-$b.txt "$b:scratch/squares-soft-r33/queue.txt" || exit 1
ssh -o ConnectTimeout=10 $b "cd $SCRATCH/squares-soft-r33 && echo $dl > deadline && echo $fdl > fqdeadline && : > taken.txt &&
  { [ -x venv/bin/python ] || cp -R $SCRATCH/squares-corners/venv venv || { ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3 -m venv venv && venv/bin/pip install -q numpy==2.5.4 scipy==1.18.1; }; } &&
  printf '#!/bin/sh\nexec \$HOME/scratch/squares-soft-r33/venv/bin/python -I \"\$@\"\n' > py && chmod +x py &&
  ./py -c 'import sys, numpy, scipy; print(sys.version.split()[0], numpy.__version__, scipy.__version__)' && echo $b ready"
