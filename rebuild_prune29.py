"""prune29.py BOX KEY [KEY ...]: remove these unclaimed jobs from the queue of BOX (mm or st); prints the keys removed."""
import subprocess, sys
BOX = {'boxB': ('boxB', '$SCRATCH/squares-rebuild'), 'boxE': ('boxE', 'scratch/squares-rebuild')}
host, root = BOX[sys.argv[1]]
drop = set(sys.argv[2:])
q = subprocess.run(['ssh', host, 'cd %s && cat queue.tsv; echo @@SPLIT@@; ls claims' % root], capture_output=True, text=True, timeout=60).stdout
ql, cl = q.split('@@SPLIT@@', 1)
claimed = set(cl.split())
keep, gone = [], []
for l in ql.splitlines():
    k = l.split('\t')[0]
    if k in drop and k not in claimed:
        gone.append(k)
    else:
        keep.append(l)
if gone:
    subprocess.run(['ssh', host, 'cd %s && cat > queue.new && mv queue.new queue.tsv' % root], input='\n'.join(keep) + '\n', text=True, check=True, timeout=60)
print('removed', sys.argv[1], ' '.join(gone), '| not removed', ' '.join(sorted(drop - set(gone))))
