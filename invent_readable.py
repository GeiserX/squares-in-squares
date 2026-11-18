#!/usr/bin/env python3
"""What the zone cut reads: one row for each held layout of m LO to HI.

For each n: the main tilt (the most common tilt of the tilted squares, to 2 degrees), the kind by that tilt
(grid = no tilted square, arms = under 33 degrees, fault = 33 to 44, block45 = 44 and more), the answer of
modules.cut at tolerances 3e-3 and 1e-2, and the gap to the board. Prints the gap by kind and by answer.

Usage (from the scratch dir, which holds gather/ and main-r17/): invent_readable.py LO HI OUT.tsv
Our own code. Imports modules.py and reads packings as data only.
"""
import sys, math, csv, collections
import numpy as np
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modules
HELD = 'gather/round15-2026-11-12a.csv'
H = modules.read_layouts(HELD)
rows = collections.defaultdict(list)
with open(HELD) as h:
    r = csv.reader(h); next(r)
    for a in r:
        rows[int(a[1])].append(float(a[5]))
gap = {}
for l in open('main-r17/gap-by-n.tsv'):
    p = l.split('\t')
    if p[0] != 'n':
        gap[int(p[0])] = (float(p[3]), float(p[4]), float(p[6]))
lo, hi = int(sys.argv[1]), int(sys.argv[2])
out = open(sys.argv[3], 'w')
out.write('n\tm\tk\theld_f\tboard_f\tscore_gap\ttilted\tmain_tilt_deg\tshare_main\tkind\tcut_3e-3\tcut_1e-2\n')
for n in range(lo * lo, min(1000, (hi + 1) ** 2 - 1) + 1):
    m = math.isqrt(n); k = n - m * m
    ol, bl, sg = gap[n]
    ang = np.mod(np.degrees(np.array(rows[n])), 90.0)
    ang = np.where(ang > 45, 90 - ang, ang)
    t = ang[ang > 0.5]
    if len(t) == 0:
        main, share, kind = 0.0, 0.0, 'grid'
    else:
        c = collections.Counter(np.round(t).astype(int).tolist())
        md, cnt = c.most_common(1)[0]
        near = t[np.abs(t - md) <= 2.0]
        main = float(np.median(near)); share = len(near) / len(t)
        kind = 'block45' if main > 44.0 else ('fault' if main > 33.0 else 'arms')
    cuts = []
    for tol in (3e-3, 1e-2):
        try:
            d, why = modules.cut(H[n], n, tol)
        except Exception as e:
            d, why = None, 'EXC %r' % (e,)
        cuts.append('ok %d,%d' % (d['c1'], d['c2']) if d is not None else (why or 'refused')[:40])
    out.write('%d\t%d\t%d\t%.6f\t%.6f\t%.3e\t%d\t%.2f\t%.2f\t%s\t%s\t%s\n' % (n, m, k, ol - m, bl - m, max(sg, 0.0), len(t), main, share, kind, cuts[0], cuts[1]))
out.close()
R = list(csv.DictReader(open(sys.argv[3]), delimiter='\t'))
def tot(f): 
    s = [float(r['score_gap']) for r in R if f(r)]
    return len(s), sum(s)
print('all', tot(lambda r: True))
for kind in ('grid', 'arms', 'fault', 'block45'):
    print(kind, tot(lambda r: r['kind'] == kind), 'cut reads', tot(lambda r: r['kind'] == kind and (r['cut_3e-3'].startswith('ok') or r['cut_1e-2'].startswith('ok'))))
print('cut reads at 3e-3', tot(lambda r: r['cut_3e-3'].startswith('ok')), 'at 1e-2', tot(lambda r: r['cut_1e-2'].startswith('ok')), 'either', tot(lambda r: r['cut_3e-3'].startswith('ok') or r['cut_1e-2'].startswith('ok')))
print('cut refuses both', tot(lambda r: not (r['cut_3e-3'].startswith('ok') or r['cut_1e-2'].startswith('ok'))))
why = collections.Counter(); whyg = collections.Counter()
for r in R:
    if not (r['cut_3e-3'].startswith('ok') or r['cut_1e-2'].startswith('ok')):
        key = ''.join(ch for ch in r['cut_1e-2'] if not ch.isdigit())[:28]
        why[key] += 1; whyg[key] += float(r['score_gap'])
for kk, v in why.most_common(8): print('  refusal', repr(kk), v, '%.5f' % whyg[kk])
