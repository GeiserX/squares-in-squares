#!/usr/bin/env python3
"""Read the structure of every held layout and set it beside the board's side.

  frontier_read.py SUB.csv TARGETS.tsv OUT.tsv

One row per n >= 100 that holds a tilted square: m, k = n - m^2, our f and the board's f (side minus m),
squares short, the tilted count, the patches (connected groups of tilted squares, centres within 1.45),
the size, median tilt and bounding box of the two largest, the walls each one touches, and how many
upright squares sit on each of the four corner grids (a grid is the set of uprights whose distance to
its corner's two walls is whole to 1e-6). Our own code; reads data only. Run with python -I.
"""
import csv, math, sys, collections
import numpy as np


def load(path):
    P = collections.defaultdict(list)
    with open(path) as f:
        r = csv.reader(f); next(r)
        for row in r:
            P[int(row[1])].append((float(row[3]), float(row[4]), float(row[5])))
    return P


def hw(t):
    return (abs(math.cos(t)) + abs(math.sin(t))) / 2


def normal(sq):
    """Box [0, s]^2; the angle in degrees folded to (-45, 45]. The angle column of the file is in degrees
    when any value is above 2 pi, else radians."""
    deg = max(abs(a) for _, _, a in sq) > 6.3
    T = [(x, y, math.radians(a) if deg else a) for x, y, a in sq]
    x0 = min(x - hw(a) for x, y, a in T); y0 = min(y - hw(a) for x, y, a in T)
    s = max(max(x - x0 + hw(a) for x, y, a in T), max(y - y0 + hw(a) for x, y, a in T))
    out = []
    for x, y, a in T:
        d = math.degrees(a) % 90.0
        if d > 45: d -= 90
        out.append((x - x0, y - y0, d))
    return s, np.array(out)


def patches(T, reach=1.45):
    n = len(T); par = list(range(n))
    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(n):
        d = np.hypot(T[i + 1:, 0] - T[i, 0], T[i + 1:, 1] - T[i, 1])
        for j in np.nonzero(d < reach)[0]:
            a, b = find(i), find(i + 1 + int(j))
            if a != b: par[a] = b
    g = collections.defaultdict(list)
    for i in range(n): g[find(i)].append(i)
    return sorted(g.values(), key=len, reverse=True)


def grids(U, s):
    """Count uprights on each corner grid: bl, br, tl, tr (a square may sit on several)."""
    def whole(v):
        return np.abs(v - np.round(v)) < 1e-6
    lx = whole(U[:, 0] - 0.5); rx = whole(s - U[:, 0] - 0.5)
    by = whole(U[:, 1] - 0.5); ty = whole(s - U[:, 1] - 0.5)
    return [int((lx & by).sum()), int((rx & by).sum()), int((lx & ty).sum()), int((rx & ty).sum()),
            int((~(lx | rx) | ~(by | ty)).sum())]


def describe(sq):
    s, A = normal(sq)
    t = np.abs(A[:, 2]) > 1e-4
    T, U = A[t], A[~t]
    row = {'side': s, 'tilted': len(T), 'grids': grids(U, s) if len(U) else [0] * 5, 'patches': []}
    for g in patches(T)[:3] if len(T) else []:
        G = T[g]
        x0, x1, y0, y1 = G[:, 0].min() - .5, G[:, 0].max() + .5, G[:, 1].min() - .5, G[:, 1].max() + .5
        walls = ''.join(c for c, on in (('L', x0 < 1.0), ('R', x1 > s - 1.0), ('B', y0 < 1.0), ('T', y1 > s - 1.0)) if on)
        row['patches'].append((len(g), float(np.median(np.abs(G[:, 2]))), float(np.ptp(np.abs(G[:, 2]))), x1 - x0, y1 - y0, walls or '-'))
    row['npatch'] = len(patches(T)) if len(T) else 0
    return row


def main():
    sub, targets, out = sys.argv[1:4]
    P = load(sub)
    Tg = {int(r['n']): r for r in csv.DictReader(open(targets), delimiter='\t')}
    with open(out, 'w') as h:
        h.write('n\tm\tk\tours_f\tboard_f\tshort\ttilted\tnpatch\tp1\tp2\tgrid_bl\tgrid_br\tgrid_tl\tgrid_tr\toff_grid\n')
        for n in sorted(P):
            if n < 100: continue
            d = describe(P[n])
            if not d['tilted']: continue
            m = math.isqrt(n - 1); r = Tg[n]
            ps = ['%d@%.2f~%.2f %.1fx%.1f %s' % p for p in d['patches'][:2]] + ['', '']
            h.write('\t'.join(map(str, [n, m, n - m * m, '%.6f' % (float(r['ours_L']) - m), '%.6f' % (float(r['target_L']) - m),
                                        r['short'], d['tilted'], d['npatch'], ps[0], ps[1]] + d['grids'])) + '\n')


if __name__ == '__main__':
    main()
