#!/bin/sh
# verify.sh BOX: compare every file under run/ on the box, and its queue files, with the copy here (md5), before the box scratch is removed
PY=$SCRATCH/bounties-squares/venv/bin/python; H=$(cd "$(dirname "$0")" && pwd); W=$("$PY" -I "$H/ctl.py" where); b=$1; mkdir -p $W/logs
ssh -o ConnectTimeout=10 $b 'cd $SCRATCH/squares-soft-r33 && find run -type f ! -path "*/softfree/*" -exec md5 -r {} + | sort -k2; md5 -r queue.txt taken.txt drv.out deadline fqdeadline | sort -k2' > $W/logs/$b-remote.md5 || { echo "$b NOT VERIFIED (ssh)"; exit 1; }
(cd $W/$b && find run -type f ! -path "*/softfree/*" -exec md5 -r {} + | sort -k2; md5 -r queue.txt taken.txt drv.out deadline fqdeadline | sort -k2) > $W/logs/$b-local.md5
if [ -s $W/logs/$b-remote.md5 ] && cmp -s $W/logs/$b-remote.md5 $W/logs/$b-local.md5; then echo "$b VERIFIED: $(wc -l < $W/logs/$b-remote.md5 | tr -d ' ') files, same"; else echo "$b NOT VERIFIED: remote $(wc -l < $W/logs/$b-remote.md5 | tr -d ' ') local $(wc -l < $W/logs/$b-local.md5 | tr -d ' ')"; diff $W/logs/$b-remote.md5 $W/logs/$b-local.md5 | head -5; exit 1; fi
