"""heldshare28.py OUT: for every n from 300 up whose bar28 row is the held round 26 b row (gather/round26-2026-11-14b.csv),
the share of its squares within 1e-3 of the prvsiyan best-of-1105 row of that n (rebuild_walk27.prv_share). Lanes gated
their kick starts on that share until 00:19Z of round 28, so a held row with a high share was likely never kicked.
Writes n, share1e3, share1e6, bar side, and whether a live r28 take holds that n."""
import csv, math, os, sys, collections
sys.path.insert(0, '.')
import rebuild_walk27 as w  # noqa: E402
import rebuild_take as rt  # noqa: E402
S = '$SCRATCH/bounties-squares/'
csv.field_size_limit(1 << 28)
bar = {int(r['n']): (float(r['bar']), r['source']) for r in csv.DictReader(open(S + 'take-rebuild-r31/work/bar31.tsv'), delimiter='\t')}
os.environ['SQ_ROUND'] = '31'
lv = rt.live(S + 'take-none-r28')
rows = collections.defaultdict(list)
NMIN = int(sys.argv[2]) if len(sys.argv) > 2 else 300
NMAX = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
for r in csv.DictReader(open(S + 'gather/round26-2026-11-14b.csv')):
    n = int(r['n'])
    if NMIN <= n <= NMAX and bar.get(n, (0, ''))[1].startswith('held'):
        rows[n].append(r)
os.makedirs(S + 'take-rebuild-r31/work/held26b', exist_ok=True)
out = open(sys.argv[1], "w")
for n in sorted(rows):
    p = S + 'take-rebuild-r31/work/held26b/%d.csv' % n
    with open(p, 'w') as h:
        h.write('n,square_id,x,y,angle\n')
        for r in rows[n]:
            h.write('%s,%s,%s,%s,%s\n' % (r['n'], r['square_id'], r['x'], r['y'], r['angle']))
    try:
        s = w.prv_share(p, n)
    except Exception as e:
        s = None
    out.write('%d\t%s\t%s\t%.12f\t%s\n' % (n, None if s is None else s['share1e3'], None if s is None else s['share1e6'],
                                          (1 + bar[n][0]) * math.sqrt(n), 'live' if n in lv else ''))
    out.flush()
