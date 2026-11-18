#!/usr/bin/env python3
"""angle: list the tilt of every tilted patch of a submission and how close it is to atan(p/q).

  angle_scan.py SUB.csv OUT.tsv [--qmax 8] [--nmin 20]

A patch is a connected set of tilted squares (tilt over 1 degree off the axes, centres under 1.6 apart).
Its angle is the centre of the densest 0.02 degree window of its tilts, folded to [0, 45]. `share` is the part of
the patch inside that window. `p/q` is the nearest fraction with q <= qmax to tan(angle); `d_deg` is the distance in
degrees. Prints the hit rates at three tolerances beside the rate a uniform angle would give.
"""
import argparse, csv, collections, math, sys
from fractions import Fraction
import numpy as np


def load(path):
    P = collections.defaultdict(list)
    with open(path) as f:
        r = csv.DictReader(f)
        for row in r:
            P[int(row['n'])].append((float(str(row['x']).lstrip('s')), float(str(row['y']).lstrip('s')),
                                     float(str(row['angle']).lstrip('s'))))
    return P


def hw(t):
    return (abs(math.cos(t)) + abs(math.sin(t))) / 2


def side(sq):
    x0 = min(x - hw(a) for x, y, a in sq); x1 = max(x + hw(a) for x, y, a in sq)
    y0 = min(y - hw(a) for x, y, a in sq); y1 = max(y + hw(a) for x, y, a in sq)
    return max(x1 - x0, y1 - y0)


def fold(a):
    """radians -> degrees in [0, 45]"""
    d = math.degrees(a) % 90.0
    return 90.0 - d if d > 45 else d


def patches(sq, tilt_min=1.0, link=1.6):
    T = [(x, y, fold(a)) for x, y, a in sq if fold(a) > tilt_min]
    if not T:
        return []
    A = np.array(T); n = len(A)
    par = list(range(n))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    d2 = ((A[:, None, :2] - A[None, :, :2]) ** 2).sum(-1)
    for i, j in zip(*np.where(np.triu(d2 < link * link, 1))):
        par[find(i)] = find(j)
    g = collections.defaultdict(list)
    for i in range(n):
        g[find(i)].append(i)
    return [A[v] for v in sorted(g.values(), key=len, reverse=True)]


def dominant(ang, w=0.02):
    a = np.sort(ang); best = (0, a[0])
    j = 0
    for i in range(len(a)):
        while a[i] - a[j] > w:
            j += 1
        if i - j + 1 > best[0]:
            best = (i - j + 1, float(np.median(a[j:i + 1])))
    return best[1], best[0] / len(a)


def fracs(qmax):
    S = sorted({Fraction(p, q) for q in range(1, qmax + 1) for p in range(0, q + 1)})
    return [(f, math.degrees(math.atan(float(f)))) for f in S]


def nearest(deg, F):
    f, a = min(F, key=lambda t: abs(t[1] - deg))
    return f, deg - a


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('sub'); ap.add_argument('out')
    ap.add_argument('--qmax', type=int, default=8); ap.add_argument('--nmin', type=int, default=20)
    ap.add_argument('--minsize', type=int, default=4)
    a = ap.parse_args()
    P = load(a.sub); F = fracs(a.qmax); F6 = fracs(6)
    rows = []
    for n in sorted(P):
        if n < a.nmin:
            continue
        L = side(P[n]); m = int(L + 1e-9)
        for k, pt in enumerate(patches(P[n])):
            if len(pt) < a.minsize:
                continue
            ang, share = dominant(pt[:, 2])
            f, d = nearest(ang, F); f6, d6 = nearest(ang, F6)
            rows.append((n, m, L - m, k, len(pt), ang, share, float(pt[:, 2].min()), float(pt[:, 2].max()),
                         str(f), d, str(f6), d6))
    with open(a.out, 'w') as h:
        h.write('n\tm\tf\tpatch\tsquares\tangle\tshare\tmin\tmax\tpq\td_deg\tpq6\td6_deg\n')
        for r in rows:
            h.write('%d\t%d\t%.6f\t%d\t%d\t%.4f\t%.2f\t%.2f\t%.2f\t%s\t%+.4f\t%s\t%+.4f\n' % r)
    # hit rates against a uniform angle on (1, 45)
    print('%d patches of >= %d squares on %d n' % (len(rows), a.minsize, len({r[0] for r in rows})))
    for name, FF, col in (('q<=6', F6, 12), ('q<=%d' % a.qmax, F, 10)):
        inner = [x for x in FF if 1 < x[1] < 45]
        for tol in (0.005, 0.02, 0.1):
            hit = sum(1 for r in rows if abs(r[col]) <= tol)
            exp = (2 * tol * len(inner) + tol) / 44.0   # 45 itself has a one-sided window
            print('%s tol %.3f deg: %d of %d patches (%.1f%%), uniform would give %.1f%%' % (
                name, tol, hit, len(rows), 100 * hit / max(1, len(rows)), 100 * exp))
    c = collections.Counter((r[11]) for r in rows if abs(r[12]) <= 0.02)
    print('q<=6 hits within 0.02 deg by fraction:', dict(c.most_common()))


if __name__ == '__main__':
    main()
