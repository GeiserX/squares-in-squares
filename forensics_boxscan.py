#!/usr/bin/env python3
"""Find a clean box in a held layout and put a small held packing into it.

A box is clean when every square of the layout is either wholly inside it or wholly outside it. A clean
box of side a + f that holds a*a grid squares takes the held packing of a*a + ka squares instead, and the
layout then holds ka squares more at the same side. Two grids pushed into opposite corners leave a gap
of width f between them, so such boxes sit at the steps of that gap and in a free corner.

  scan    every held layout, every corner of an upright square as a box corner, the four directions,
          and every small held packing whose side fraction is at most the layout's. Tilted squares are
          tested by their bounding box. The box test allows 5e-8, because quenched layouts hold their
          grid squares only that well. Each result is checked again pair by pair before it is written
          to OUT/<n>.csv, and it needs one fq quench before the certificate.

A clean box is a stronger demand than forensics_compose.py makes. The 639 that tool builds shows no
clean box: the held 497 reaches into the box of the held 10 and touches none of its squares.
  ctl     a 6-by-6 grid at side 6.6213 with its last row and column at the far walls: the 5-by-5
          block must come back as a clean box for the held 26, and must not when the far column
          is moved 0.3 into the box.

Usage:
  forensics_boxscan.py scan HELD.csv HELD_DETAILS.csv OUT_DIR [--mod K,R] [--amax 12]
  forensics_boxscan.py ctl HELD.csv HELD_DETAILS.csv
"""
import sys, os, csv, math, argparse, collections
import numpy as np

import forensics_compose as fc

TOL = 5e-8            # quenched layouts hold their grid squares to about 1e-8, so the box test is this loose
BUILD_TOL = 2e-7      # overlap allowed in a built layout: the fq quench that follows takes it out


def aabb(Q):
    K = fc.corners(Q)
    return K[:, :, 0].min(1), K[:, :, 0].max(1), K[:, :, 1].min(1), K[:, :, 1].max(1)


def clean_boxes(Q, L, s, n_small):
    """Boxes of side s at the corners of upright squares: yields (gain, x0, y0, inside mask)."""
    x0, x1, y0, y1 = aabb(Q)
    up = np.abs(np.sin(2 * Q[:, 2])) < 1e-6
    P = np.unique(np.round(np.r_[np.c_[x0[up], y0[up]], np.c_[x1[up], y0[up]], np.c_[x0[up], y1[up]], np.c_[x1[up], y1[up]]], 9), axis=0)
    out = []
    for dx in (0, 1):
        for dy in (0, 1):
            bx0 = P[:, 0] - dx * s; by0 = P[:, 1] - dy * s; bx1 = bx0 + s; by1 = by0 + s
            ok = (bx0 >= -TOL) & (by0 >= -TOL) & (bx1 <= L + TOL) & (by1 <= L + TOL)
            if not ok.any():
                continue
            bx0, by0, bx1, by1 = bx0[ok, None], by0[ok, None], bx1[ok, None], by1[ok, None]
            inside = (x0 >= bx0 - TOL) & (x1 <= bx1 + TOL) & (y0 >= by0 - TOL) & (y1 <= by1 + TOL)
            inter = (x1 > bx0 + TOL) & (x0 < bx1 - TOL) & (y1 > by0 + TOL) & (y0 < by1 - TOL)
            ci = inside.sum(1)
            good = ((inter & ~inside).sum(1) == 0) & (ci < n_small)
            for i in np.nonzero(good)[0]:
                out.append((n_small - int(ci[i]), float(bx0[i, 0]), float(by0[i, 0]), inside[i].copy()))
    return out


def scan(rows, D, mod, amax):
    fh = {}
    for n in range(1, 1001):
        m, k = fc.mk(n); fh[(m, k)] = D[n] - m
    small = []                                         # (a, n_small, side fraction)
    for a in range(2, amax + 1):
        for k in range(1, 2 * a + 1):
            if (a, k) in fh and a * a + k in rows:
                small.append((a, a * a + k, fh[(a, k)]))
    frames = {}
    def fr(n):
        if n not in frames:
            frames[n] = fc.frame(rows[n])
        return frames[n]
    best = {}
    for nb in sorted(rows):
        if nb < 12 or (mod and nb % mod[0] != mod[1]):
            continue
        L, Q = fr(nb); m, k = fc.mk(nb); fB = L - m
        for a, ns, fa in small:
            if a > m - 1 or fa > fB + 1e-9:
                continue
            sA, A = fr(ns)
            if nb + 1 > 1000:
                continue
            for gain, bx, by, inside in clean_boxes(Q, L, sA, ns):
                n2 = nb + gain
                if n2 > 1000 or not (L < D[n2] - 1e-9):
                    continue
                if n2 not in best or L < best[n2][0] - 1e-12:
                    best[n2] = (L, nb, ns, bx, by, inside, gain)
    return best, fr


def build(best, fr, D, out):
    os.makedirs(out, exist_ok=True); got = 0; tot = 0.0
    for n2 in sorted(best):
        L, nb, ns, bx, by, inside, gain = best[n2]
        _, Q = fr(nb); sA, A = fr(ns)
        A2 = A.copy(); A2[:, 0] += bx; A2[:, 1] += by
        X = np.r_[Q[~inside], A2]
        K = fc.corners(X)
        w = fc.worst_overlap(X)
        if len(X) != n2 or w < -BUILD_TOL or K.min() < -BUILD_TOL or K.max() > L + BUILD_TOL:
            print('n %4d: box of n = %d in n = %d fails the full check (gap %.1e, %d squares)' % (n2, ns, nb, w, len(X)), flush=True); continue
        fc.write_csv('%s/%d.csv' % (out, n2), n2, X)
        g = (D[n2] - L) / math.sqrt(n2); got += 1; tot += g
        print('n %4d: the held %d in a clean box of the held %d at (%.4f, %.4f): side %.10f, held %.10f, gain %.3e' % (n2, ns, nb, bx, by, L, D[n2], g), flush=True)
    print('%d layouts written, gain %.6f before the certificate' % (got, tot), flush=True)


def cmd_ctl(held, details):
    D, _ = fc.held_f(details); rows = fc.load_all(held, {26})
    s26, A = fc.frame(rows[26]); L = s26 + 1
    G = np.array([(L - 0.5, j + 0.5, 0.0) for j in range(5)] + [(i + 0.5, L - 0.5, 0.0) for i in range(5)] + [(L - 0.5, L - 0.5, 0.0)]
                 + [(i + 0.5, j + 0.5, 0.0) for i in range(5) for j in range(5)], float)      # the last row and column stand at the far walls
    B = clean_boxes(G, L, s26, 26)
    hit = [b for b in B if abs(b[1]) < 1e-9 and abs(b[2]) < 1e-9]
    ok1 = bool(hit) and hit[0][0] == 1
    print('positive: the 5-by-5 corner block of a 6-by-6 grid at side %.4f is a clean box for the held 26: %s (want True)' % (L, ok1))
    G2 = G.copy(); G2[:5, 0] -= 0.3                    # the column at the far wall moved 0.3 into the box
    B2 = [b for b in clean_boxes(G2, L, s26, 26) if abs(b[1]) < 1e-9 and abs(b[2]) < 1e-9]
    ok2 = not B2
    print('negative: the same box with the far column moved 0.3 into it: %s (want no clean box)' % ('clean box found' if B2 else 'no clean box'))
    print('CONTROL GREEN' if ok1 and ok2 else 'CONTROL RED'); return 0 if ok1 and ok2 else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=['scan', 'ctl']); ap.add_argument('held'); ap.add_argument('details'); ap.add_argument('out', nargs='?')
    ap.add_argument('--mod', default=''); ap.add_argument('--amax', type=int, default=12)
    a = ap.parse_args()
    if a.cmd == 'ctl':
        sys.exit(cmd_ctl(a.held, a.details))
    D, _ = fc.held_f(a.details)
    rows = fc.load_all(a.held, set(range(1, 1001)))
    mod = tuple(int(v) for v in a.mod.split(',')) if a.mod else None
    best, fr = scan(rows, D, mod, a.amax)
    build(best, fr, D, a.out)
