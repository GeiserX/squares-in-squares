#!/usr/bin/env python3
"""midm: exact slab recombination over a pool of layouts.

A fault line of a layout is a straight line across the whole box that no square crosses. It cuts the layout
into two slabs. A slab of one layout stacked on a slab of another is a legal packing with no search:
  squares = a1 + a2,  side = max(width1, width2, height1 + height2)
where the width of a slab is the side of the layout it comes from. Every layout gives its slabs in four
directions (cut from the bottom, the top, the left, the right), and the whole layout is a slab too.
This is the straight-line case of the fault-line composition; the public fault DP composes along a staircase
between two lattices and does not cut a layout that has no such staircase.

Usage: midm_slab.py scan POOL.csv [POOL2.csv ...] --held HELD.csv --out DIR [--lo 1] [--hi 1000] [--three 1]
  POOL    files of layouts (all their n are donors). --held is the file whose sides are the bar (also a donor)
  --three also tries bottom + middle + top, where the middle is a slab between two fault lines of one layout
  writes DIR/slab.tsv (every n where a composition is below the held side) and DIR/raw/<n>-slab.csv
"""
import argparse, csv, math, os, sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import methods_lp as mlp  # noqa: E402

TOL = 1e-10      # two squares may touch at a fault line; an overlap larger than this is no fault line


def turn(P, L, r):
    """The layout with direction r at the bottom: 0 as it is, 1 top, 2 left, 3 right. Returns (u, v, angle)."""
    x, y, t = P[:, 0], P[:, 1], P[:, 2]
    if r == 0:
        return np.column_stack([x, y, t])
    if r == 1:
        return np.column_stack([x, L - y, -t])
    if r == 2:
        return np.column_stack([y, x, math.pi / 2 - t])
    return np.column_stack([y, L - x, t - math.pi / 2])


def slabs_of(P, L):
    """[(r, height, count, lo_index_order, v0)] for every fault line in every direction, the whole layout included.
    A slab is the squares below the line; `height` is the top of its highest square."""
    out = []
    for r in range(4):
        Q = turn(P, L, r); h = mlp.half(Q[:, 2]); lo = Q[:, 1] - h; hi = Q[:, 1] + h
        o = np.argsort(lo); lo_s = lo[o]; top = np.maximum.accumulate(hi[o])
        k = np.flatnonzero(lo_s[1:] >= top[:-1] - TOL)       # line between square k and k+1 of the order
        for i in k:
            out.append((r, float(top[i]), int(i + 1)))
        out.append((r, float(top[-1]), len(P)))
    return out


def mids_of(P, L):
    """Middle slabs: the squares between two fault lines of direction 0 or 2. [(r, height, count, v_lo, v_hi)]"""
    out = []
    for r in (0, 2):
        Q = turn(P, L, r); h = mlp.half(Q[:, 2]); lo = Q[:, 1] - h; hi = Q[:, 1] + h
        o = np.argsort(lo); lo_s = lo[o]; top = np.maximum.accumulate(hi[o])
        k = np.flatnonzero(lo_s[1:] >= top[:-1] - TOL)
        for a in range(len(k)):
            for b in range(a + 1, len(k)):
                v0 = float(lo_s[k[a] + 1]); v1 = float(top[k[b]])
                out.append((r, v1 - v0, int(k[b] - k[a]), v0, v1))
    return out


def take(P, L, r, count):
    """The `count` lowest squares of direction r, with the slab's own floor at v = 0."""
    Q = turn(P, L, r); h = mlp.half(Q[:, 2]); o = np.argsort(Q[:, 1] - h)[:count]
    S = Q[o].copy(); S[:, 1] -= (S[:, 1] - mlp.half(S[:, 2])).min()
    return S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd'); ap.add_argument('pool', nargs='+'); ap.add_argument('--held', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--inflate', default='', help='N:D makes the bar of N worse by D (the control: the scan must then rebuild N)')
    ap.add_argument('--near', type=float, default=0.0, help='also write the compositions up to this far above the held side (up to 4 per n) to DIR/near, for a quench')
    ap.add_argument('--lo', type=int, default=1); ap.add_argument('--hi', type=int, default=1000); ap.add_argument('--three', type=int, default=0)
    a = ap.parse_args()
    os.makedirs(a.out + '/raw', exist_ok=True)
    held = {n: mlp.normal(P) for n, P in mlp.load(a.held).items()}; Lh = {n: mlp.side(P) for n, P in held.items()}
    lay = [(n, P, Lh[n], 'held') for n, P in held.items()]
    for p in a.pool:
        if os.path.abspath(p) == os.path.abspath(a.held):
            continue
        for n, P in mlp.load(p).items():
            P = mlp.normal(P); L = mlp.side(P)
            if abs(L - Lh.get(n, 0)) > 1e-9:
                lay.append((n, P, L, os.path.basename(p)))
    if a.inflate:
        k, d = a.inflate.split(':'); Lh[int(k)] += float(d)
    S = [(0.0, 0, 0.0, -1, 0)]                               # (height, count, width, layout index, r); the first is the empty slab
    for li, (n, P, L, _) in enumerate(lay):
        for r, hgt, cnt in slabs_of(P, L):
            S.append((hgt, cnt, L, li, r))
    H = np.array([s[0] for s in S]); C = np.array([s[1] for s in S]); W = np.array([s[2] for s in S])
    nmax = max(Lh); bar = np.full(2 * nmax + 2, -1.0)
    for n, L in Lh.items():
        bar[n] = L
    print('layouts', len(lay), 'slabs', len(S), 'of them whole layouts', 4 * len(lay), flush=True)
    order = np.argsort(W); Ws = W[order]; best = {}; near = defaultdict(list)
    for i in range(len(S)):
        if C[i] >= a.hi:
            continue
        if i == 0:
            J = np.arange(1, len(S))                         # the empty slab goes with every slab
        else:
            j0, j1 = np.searchsorted(Ws, W[i] - 1.01), np.searchsorted(Ws, W[i] + 1.01)
            J = order[j0:j1]; J = J[J >= i]
        cnt = C[i] + C[J]; ok = (cnt >= a.lo) & (cnt <= min(a.hi, nmax))
        J = J[ok]; cnt = cnt[ok]
        side = np.maximum(np.maximum(W[i], W[J]), H[i] + H[J])
        win = side < bar[cnt] - 1e-9
        for j, c, s in zip(J[win], cnt[win], side[win]):
            if int(c) not in best or s < best[int(c)][0]:
                best[int(c)] = (float(s), i, int(j), None)
        if a.near:
            nr = (side < bar[cnt] + a.near) & ~win
            for j, c, s in zip(J[nr], cnt[nr], side[nr]):
                li, lj = S[i][3], S[int(j)][3]
                if li == lj or (li < 0 and lay[lj][0] == int(c)) or (lj < 0 and lay[li][0] == int(c)):
                    continue                                  # the layout itself, cut and put together again
                near[int(c)].append((float(s), i, int(j)))
    if a.three:
        M = []
        for li, (n, P, L, _) in enumerate(lay):
            for r, hgt, cnt, v0, v1 in mids_of(P, L):
                M.append((hgt, cnt, L, li, r, v0, v1))
        print('middle slabs', len(M), flush=True)
        # bottom + middle + top: for every middle, the best pair of outer slabs by total height per count is too
        # many pairs; take the outer pair from one layout cut at one line (its bottom and its top), i.e. the
        # middle is put into a fault line of another layout
        byl = defaultdict(list)
        for li, (n, P, L, _) in enumerate(lay):
            byl[round(L, 1)].append(li)
        faults = {li: [(hgt, cnt) for r, hgt, cnt in slabs_of(lay[li][1], lay[li][2]) if r in (0, 2)] for li in range(len(lay))}
        for hgt, cnt, Lm, li, r, v0, v1 in M:
            for key in (round(Lm, 1) - 0.1, round(Lm, 1), round(Lm, 1) + 0.1):
                for lj in byl.get(round(key, 1), ()):
                    n2, P2, L2, _ = lay[lj]; c = n2 + cnt
                    if lj == li or c > min(a.hi, nmax) or c < a.lo or len(faults[lj]) < 2:
                        continue
                    s = max(Lm, L2, L2 + hgt)
                    if s < bar[c] - 1e-9 and (c not in best or s < best[c][0]):
                        best[c] = (s, (li, r, v0, v1, cnt), lj, 'mid')
    def build(i, j):
        (h1, c1, w1, l1, r1), (h2, c2, w2, l2, r2) = S[i], S[j]
        if l1 < 0:
            (h1, c1, w1, l1, r1), (h2, c2, w2, l2, r2) = S[j], S[i]
        P = take(lay[l1][1], lay[l1][2], r1, c1); parts = '%d of n=%d (%s) dir %d' % (c1, lay[l1][0], lay[l1][3], r1)
        if l2 >= 0:
            B = take(lay[l2][1], lay[l2][2], r2, c2); B[:, 1] = (h1 + h2) - B[:, 1]; B[:, 2] = -B[:, 2]
            P = np.vstack([P, B]); parts += ' + %d of n=%d (%s) dir %d' % (c2, lay[l2][0], lay[l2][3], r2)
        return mlp.normal(P), parts
    if a.near:
        os.makedirs(a.out + '/near', exist_ok=True)
        with open(a.out + '/near.tsv', 'w') as g:
            g.write('n\theld_side\tside\tabove\tparts\n')
            for n in sorted(near):
                seen = []
                for s, i, j in sorted(near[n])[:40]:
                    if any(abs(s - t) < 1e-7 for t in seen) or len(seen) >= 4:
                        continue
                    seen.append(s); P, parts = build(i, j)
                    if len(P) != n or mlp.min_gap(P) < -1e-9:
                        continue
                    g.write('%d\t%.9f\t%.9f\t%.2e\t%s\n' % (n, Lh[n], s, s - Lh[n], parts))
                    with open('%s/near/%d-slab%d.csv' % (a.out, n, len(seen)), 'w', newline='') as h:
                        w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                        for q, (x, y, t) in enumerate(P):
                            w.writerow([n, q, repr(float(x)), repr(float(y)), repr(float(t))])
        print('near: %d n have a composition within %g above the held side' % (len(near), a.near), flush=True)
    with open(a.out + '/slab.tsv', 'w') as g:
        g.write('n\theld_side\tnew_side\tgain_of_score\tparts\n')
        for n in sorted(best):
            s, i, j, kind = best[n]
            if kind is None:
                h1, c1, w1, l1, r1 = S[i]; h2, c2, w2, l2, r2 = S[j]
                if l1 < 0:
                    (h1, c1, w1, l1, r1), (h2, c2, w2, l2, r2) = S[j], S[i]
                A = take(lay[l1][1], lay[l1][2], r1, c1); parts = '%d squares of n=%d (%s, direction %d, height %.6f)' % (c1, lay[l1][0], lay[l1][3], r1, h1)
                P = A
                if l2 >= 0:
                    B = take(lay[l2][1], lay[l2][2], r2, c2)
                    B[:, 1] = (h1 + h2) - B[:, 1]; B[:, 2] = -B[:, 2]        # the second slab upside down on top
                    P = np.vstack([A, B])
                    parts += ' + %d squares of n=%d (%s, direction %d, height %.6f)' % (c2, lay[l2][0], lay[l2][3], r2, h2)
            else:
                continue                                     # a middle composition is reported by --three only as a count
            P = mlp.normal(P); sd = mlp.side(P); mg = mlp.min_gap(P)
            g.write('%d\t%.12f\t%.12f\t%.3e\t%s (built side %.12f, smallest gap %.2e)\n' % (n, Lh[n], s, (Lh[n] - s) / math.sqrt(n), parts, sd, mg))
            if len(P) == n and mg > -1e-9:
                with open('%s/raw/%d-slab.csv' % (a.out, n), 'w', newline='') as h:
                    w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                    for q, (x, y, t) in enumerate(P):
                        w.writerow([n, q, repr(float(x)), repr(float(y)), repr(float(t))])
    tot = sum((Lh[n] - best[n][0]) / math.sqrt(n) for n in best)
    print('n below the held side:', len(best), 'gain of score', '%.3e' % tot, sorted(best)[:60], flush=True)


if __name__ == '__main__':
    main()
