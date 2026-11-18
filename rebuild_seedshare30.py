"""seedshare29.py N [N ...]: best-of-1105 share (rebuild_walk27.prv_share) of the held round27b row of each n. Prints n, share1e3."""
import csv, sys, collections
sys.path.insert(0, '.')
import rebuild_walk27 as w
S = '$SCRATCH/bounties-squares/'
want = set(int(x) for x in sys.argv[1:])
rows = collections.defaultdict(list)
for r in csv.DictReader(open(S + 'gather/round27-2026-11-15b.csv')):
    if int(r['n']) in want:
        rows[int(r['n'])].append(r)
for n in sorted(rows):
    p = S + 'take-rebuild-r30/work/held27b/%d.csv' % n
    with open(p, 'w') as h:
        h.write('n,square_id,x,y,angle\n')
        for r in rows[n]:
            h.write('%s,%s,%s,%s,%s\n' % (r['n'], r['square_id'], r['x'], r['y'], r['angle']))
    s = w.prv_share(p, n)
    print(n, None if s is None else s['share1e3'], flush=True)
