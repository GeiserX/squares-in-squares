#!/bin/zsh
# Round 38 end: kill every owned worker tree (boxE, boxC, boxB), archive the box scratch, verify by sha256, remove it.
W=$SCRATCH/bounties-squares/take-classfill-r38/work
R=scratch/squares-classfill-r38
touch $W/STOP
for h in boxE boxC boxB; do
  pids=$(cat $W/owned-${h}-*.json 2>/dev/null | /opt/homebrew/bin/python3 -c 'import sys,json,re;print(" ".join(str(json.loads(x)["pid"]) for x in re.findall(r"\{[^}]*\}",sys.stdin.read())))')
  echo "== $h kill trees of $pids"
  ssh -o ConnectTimeout=10 ${h} bash -s <<EOS
ids="$pids"
for i in 1 2 3 4 5 6 7 8; do ids="\$ids \$(for p in \$ids; do pgrep -P \$p; done)"; done
ids=\$(echo \$ids | tr ' ' '\n' | sort -u | tr '\n' ' ')
echo "tree: \$ids"
[ -n "\$ids" ] && { kill -TERM \$ids 2>/dev/null; sleep 3; kill -KILL \$ids 2>/dev/null; }
ps -axo pid,command | grep '[s]quares-classfill-r38\|[w]orker38' || echo NONE_LEFT
EOS
  mkdir -p $W/remote-$h
  rsync -a -e 'ssh -o ConnectTimeout=10' ${h}:$R/ $W/remote-$h/ || { echo RSYNC_FAIL $h; continue; }
  ssh ${h} "cd $R/ && find . -type f -print0 | xargs -0 shasum -a 256 | sort -k2" > $W/remote-$h.manifest
  (cd $W/remote-$h && find . -type f -print0 | xargs -0 shasum -a 256 | sort -k2) > $W/remote-$h.local
  if cmp -s $W/remote-$h.manifest $W/remote-$h.local && [ -s $W/remote-$h.manifest ]; then
    echo "VERIFIED $h $(wc -l < $W/remote-$h.manifest) files"
    if [ $h = boxB ]; then
      ssh ${h} "rm -rf $SCRATCH/squares-classfill-r38 && rm -f ~/$R && ls -d $SCRATCH/squares-classfill-r38 ~/$R 2>/dev/null || echo REMOVED"
    else
      ssh ${h} "rm -rf $R && ls -d $R 2>/dev/null || echo REMOVED"
    fi
  else
    echo "MISMATCH $h"; diff $W/remote-$h.manifest $W/remote-$h.local | head
  fi
done
