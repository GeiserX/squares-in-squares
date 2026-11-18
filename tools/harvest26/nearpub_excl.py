"""Share of squares of each near-pub start with the excluded layouts of remaining exclusions (data, read only).

  python -I nearpub_excl.py QUEUE.tsv OUT.tsv
For every start of the queue: the share of its squares within 1e-6 and 1e-3 of the prvsiyan 1105 row,
and (for 639 691 745 858 918) the r22 and areebbb layouts of the same n, best of 8
symmetries. OUT rows: n, start, worst label, share1e6, share1e3, maxd.
"""
import csv, sys
from pathlib import Path
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import audit_ac as A  # noqa: E402
from share_ac import share  # noqa: E402
csv.field_size_limit(1 << 26)
S = Path('$SCRATCH/bounties-squares')
q = list(csv.DictReader(open(sys.argv[1]), delimiter='\t'))
ns = sorted({int(r['n']) for r in q})
ex = {n: [] for n in ns}
for label, path in (('prvsiyan 1105', S / 'take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'),):
    if path.exists():
        got = A.read(str(path), ns)
        for n in ns:
            if len(got.get(n, [])) == n:
                ex[n].append((label, A.centres(got[n])))
for n in set(ns) & {639, 691, 745, 858, 918}:
    for label, rows in A.excluded(n):
        if not label.startswith(('prvsiyan', 'samanyu')):
            ex[n].append((label, A.centres(rows)))
with open(sys.argv[2], 'w') as fo:
    fo.write('n\tstart\tlabel\tshare1e6\tshare1e3\tmaxd\n')
    for r in q:
        n = int(r['n'])
        c = A.centres(list(csv.DictReader(open(r['start']))))
        worst = ('none', (0.0, 0.0, 0.0, 0.0))
        for label, e in ex[n]:
            s = share(c, e)
            if s[1] > worst[1][1] or (s[1] == worst[1][1] and s[0] > worst[1][0]):
                worst = (label, s)
        fo.write(f"{n}\t{r['start']}\t{worst[0]}\t{worst[1][0]:.3f}\t{worst[1][1]:.3f}\t{worst[1][3]:.3g}\n"); fo.flush()
print('done', len(q), flush=True)
