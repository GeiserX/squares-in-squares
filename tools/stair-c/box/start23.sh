#!/bin/bash
cd "$(dirname "$0")"
cp "py-$1" py
chmod +x py worker22.sh
./py -I -c 'import scipy; print("SCIPY",scipy.__version__); assert scipy.__version__=="1.18.1"'
./py -I lane/stair-c_border.py control libbase > logs/control-restore.log 2>&1 || exit 1
if [ "$1" = s ]; then
 ./py -I fresh23.py q-module-primary.tsv q-mod-final.tsv q-mod-j0015.tsv > q.txt 2> logs/fresh-pending.log
fi
nohup nice -n 5 ./worker22.sh q.txt > outer1.log 2>&1 < /dev/null &
echo "$!" > worker1.pid
if [ "$1" = s ]; then
 nohup nice -n 5 ./worker22.sh q.txt > outer2.log 2>&1 < /dev/null &
 echo "$!" > worker2.pid
fi
cat worker*.pid
