#!/usr/bin/env python3
"""rigidsoft_bandlist.py HELD.csv OUT.tsv [NMIN]: read every n of a held file as one 45 degree block along a diagonal with two side
staircases (rigidsoft_band.teeth), and list the bands that rigidsoft_band.fault can move. Dry: no quench.
Columns: n, side, tilted squares, rows x squares per row, top left teeth, bottom right teeth, pinched rows,
changes of sense, bands the move accepts, bands with both leftover teeth within 0.12 of the middle, best band."""
import csv, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rigidsoft as RS, rigidsoft_band as BD, rigidsoft_hop as HP
held, out = sys.argv[1], sys.argv[2]; nmin = int(sys.argv[3]) if len(sys.argv) > 3 else 60
pz = {}
for r in csv.DictReader(open(held, newline='')):
    pz.setdefault(int(r['n']), []).append((int(r['square_id']), float(r['x']), float(r['y']), float(r['angle'])))
h = open(out, 'w'); h.write('n\tside\ttilted\trows\tfull\tmirror\tTL\tBR\tpinches\tchanges\tbands\tfit\tbest\n')
for n in sorted(pz):
    if n < nmin:
        continue
    s, X = RS.normalize(np.array([v[1:] for v in sorted(pz[n])]))
    til = np.abs(X[:, 2]) >= 3
    if til.sum() < 12:
        continue
    dev = np.where(X[til, 2] > 0, X[til, 2] - 45.0, X[til, 2] + 45.0)
    if np.abs(dev).max() > 4:
        continue
    P = X[til, :2] - X[til, :2].mean(axis=0); w, V = np.linalg.eigh(P.T @ P)
    mir = V[0, -1] * V[1, -1] < 0
    if mir:
        X = np.column_stack([s - X[:, 0], X[:, 1], -X[:, 2]])
    try:
        tt, idx, row, dv, a0, full = BD.teeth(s, X)
    except Exception as e:
        h.write('%d\t%.9f\t%d\tERR %s\n' % (n, s, til.sum(), str(e)[:60])); continue
    nrow = int(row.max()) + 1
    cnt = [int((row == r).sum()) for r in range(nrow)]
    if nrow < 6 or sum(1 for c in cnt if c == full) < 0.7 * nrow or not tt['TL'] or not tt['BR']:
        h.write('%d\t%.9f\t%d\t%d\t%d\t%d\t%d\t%d\tno block read (%s)\n' % (n, s, til.sum(), nrow, full, mir, len(tt['TL']), len(tt['BR']), ','.join(map(str, cnt))[:60])); continue
    pin = BD.pinches(tt, nrow); seq = [pin[r] for r in sorted(pin)]
    ch = sum(1 for a, b in zip(seq, seq[1:]) if a != b)
    nb = 0; nf = 0; best = None
    for side in ('TL', 'BR'):
        other = 'BR' if side == 'TL' else 'TL'
        for k1 in range(1, nrow - 1):
            for k2 in range(k1 + 1, nrow):
                mine = [t for t, q in tt[side] if k1 - 0.7071 < t < k2 + 0.7071]
                lo = [t for t in mine if t < k1]; hi = [t for t in mine if t > k2]; mid = [t for t in mine if k1 <= t <= k2]
                adv = [t for t, q in tt[other] if (k1 + 1.4142 <= t <= k2 if side == 'TL' else k1 <= t <= k2 - 1.4142)]
                if len(lo) != 1 or len(hi) != 1 or len(mid) != len(adv) or cnt[k1 - 1] != full or cnt[k2] != full:
                    continue
                nb += 1
                fit = max(abs(lo[0] - (k1 - 1) - 0.5), abs(hi[0] - k2 - 0.5))
                nf += fit <= 0.12
                if best is None or fit < best[0]:
                    best = (fit, '%s%d:%d' % (side, k1, k2))
    h.write('%d\t%.9f\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%d\t%d\t%d\t%s\n' % (n, s, til.sum(), nrow, full, mir, len(tt['TL']), len(tt['BR']),
            ''.join('%d%s' % (r, '+' if pin[r] > 0 else '-') for r in sorted(pin)), ch, nb, nf, 'none' if best is None else '%s fit %.2f' % (best[1], best[0])))
h.close()
