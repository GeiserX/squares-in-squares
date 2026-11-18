#!/bin/sh
# border r26: contact LP reclose (methods_lp.py) on fresh near misses, one process, stops at the deadline file time minus 7 min.
cd $SCRATCH/squares-border-r26/lp
END=$(cut -d. -f1 ../deadline); STOP=$((END-420))
for f in $(ls nin | sort); do
  now=$(date +%s); [ $now -ge $STOP ] && echo "deadline stop before $f" && break
  b=${f%.csv}; n=${b#*_}
  timeout 90 nice -n 5 ../venv/bin/python -I methods_lp.py nin/$f nout/$b --ns $n --jobs 1 --iters 40 > nlog/$b.log 2>&1
  echo "$b $(tail -1 nout/$b/lp.tsv 2>/dev/null)"
done
echo done
