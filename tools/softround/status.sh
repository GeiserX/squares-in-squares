#!/bin/sh
# Status of the two remote soft workers, including wall-limiter wrappers.
for b in boxC boxD; do
  echo "== $b"
  ssh -o ConnectTimeout=10 "$b" 'python3 -' <<'PY'
import pathlib, subprocess
root = pathlib.Path.home() / 'scratch/squares-soft-r33'
if not root.exists():
    print('scratch removed')
else:
    lines = subprocess.check_output(['ps', '-axo', 'pid=,pcpu=,command='], text=True).splitlines()
    soft = [s for s in lines if str(root) + '/methods_soft.py ' in s and '/softjob.py ' not in s]
    fq = [s for s in lines if str(root) + '/fq quench' in s]
    queue = (root / 'queue.txt').read_text().splitlines()
    taken = (root / 'taken.txt').read_text().splitlines()
    print('active soft', len(soft), 'fq', len(fq), 'queued', len(queue), 'taken', len(taken))
    for line in soft + fq:
        print(line.strip())
    print('last taken:', taken[-1] if taken else 'none')
PY
done
