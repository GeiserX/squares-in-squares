#!/usr/bin/env python3
"""Seam join: the left part of one layout and the right part of another, cut on one straight line.

Put layout L at the left wall and layout L' at the right wall of a square of side S = max(side L, side L').
Cut both on the vertical line x = t. Keep the squares of L that lie whole left of t and the squares of L' that lie
whole right of t. No square crosses the line, so the two parts cannot meet. Where a layout is lower than S, the band
above it on its side of the line takes plain upright squares. The count is

    N(t) = left(L, t) + right(L', t) + floor(t) * floor(S - side L) + floor(S - t) * floor(S - side L')

and the result is a packing of N(t) squares at side S. It is better than the table when the table needs a side
above S for N(t) squares. A cut with one side empty is a layout alone, not a join, so it is skipped. Each layout faces the line with each of its four sides. Both are read from the same
files: every layout of the merge and of the take files. The k123 lane joins chosen pairs at a seam and quenches
(round 20); this is the plain count over every pair with a straight cut and no quench.

Usage: forensics_seam.py DETAILS.csv OUT_DIR [--dm 2] [--pad 2e-10] [--ctl N] FILE.csv [FILE.csv ...]
  --dm   pairs whose whole sides differ by at most this many units
  --ctl  report the best N(t) for the pairs of layout N with itself (a control: it must give N, not more)
Positive control (round 20): a 9 x 9 grid and the best 52 as layouts 81 and 52, with every table entry from 69 up
raised by 10: the tool finds, builds and checks 80 and 81 at side 9. With the true table it finds none.
"""
import sys, os, csv, math, collections, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forensics_compose as fc
import forensics_pool as fp

EPS = 1e-9


def layouts(p):
    L = collections.defaultdict(list)
    with open(p) as h:
        for r in csv.DictReader(h):
            try:
                L[int(r['n'])].append((fp.fnum(r['x']), fp.fnum(r['y']), fp.fnum(r['angle'])))
            except (KeyError, ValueError):
                continue
    return {n: np.array(v, float) for n, v in L.items() if len(v) == n}


def rot(Q, s, r):
    """Turn the layout by r quarter turns inside its box [0, s]^2."""
    R = Q.copy()
    for _ in range(r):
        x, y = R[:, 0].copy(), R[:, 1].copy()
        R[:, 0], R[:, 1] = s - y, x; R[:, 2] = R[:, 2] + math.pi / 2
    return R


def main():
    argv = sys.argv[1:]
    def opt(name, default, cast):
        if name in argv:
            i = argv.index(name); v = cast(argv[i + 1]); del argv[i:i + 2]; return v
        return default
    dm = opt('--dm', 2, int); pad = opt('--pad', 2e-10, float); ctl = opt('--ctl', 0, int)
    details, out, files = argv[0], argv[1], argv[2:]
    D = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    Dn = np.array([D[n] for n in range(1, 1001)])
    def kmax(S):
        """The largest count the table packs at side S (with the certificate padding)."""
        ok = np.nonzero(Dn <= S + pad * 30)[0]
        return int(ok.max()) + 1 if len(ok) else 0
    lay = []
    seen = set()
    for p in files:
        for n, A in layouts(p).items():
            s, Q = fc.frame(A); key = (n, round(s, 9))
            if key in seen:
                continue
            seen.add(key)
            lay.append((n, s, Q, os.path.basename(p)))
    os.makedirs(out, exist_ok=True); t0 = time.time()
    # per layout and quarter turn: sorted right edges (for a left part) and sorted left edges (for a right part)
    E = []
    for n, s, Q, src in lay:
        rows = []
        for r in range(4):
            R = rot(Q, s, r); K = fc.corners(R)
            rows.append((np.sort(K[:, :, 0].max(1)), np.sort(K[:, :, 0].min(1))))
        E.append(rows)
    bym = collections.defaultdict(list)
    for i, (n, s, Q, src) in enumerate(lay):
        bym[int(math.floor(s + EPS))].append(i)
    hits = {}; npairs = 0; best_ctl = 0
    for i, (n, s, Q, src) in enumerate(lay):
        if ctl and n != ctl:
            continue
        m = int(math.floor(s + EPS))
        for m2 in range(m - dm, m + dm + 1):
            for j in bym.get(m2, []):
                n2, s2 = lay[j][0], lay[j][1]
                if ctl and n2 != ctl:
                    continue
                S = max(s, s2); K0 = kmax(S); hS = math.floor(S - s + EPS); hS2 = math.floor(S - s2 + EPS); sh = S - s2
                for r in range(4):
                    xr = E[i][r][0]
                    for r2 in range(4):
                        xl = E[j][r2][1] + sh; npairs += 1
                        T = np.r_[xr, xl, 0.0, S]
                        left = np.searchsorted(xr, T + EPS, side='right')
                        right = len(xl) - np.searchsorted(xl, T - EPS, side='left')
                        N = left + right + np.floor(T + EPS) * hS + np.floor(S - T + EPS) * hS2
                        N[(left == 0) | (right == 0)] = -1  # a cut with one side empty is a layout alone, not a join
                        k = int(np.argmax(N)); Nk = int(N[k])
                        if ctl:
                            best_ctl = max(best_ctl, Nk); continue
                        if Nk > K0 and Nk <= 1000 and (Nk not in hits or S < hits[Nk][0]):
                            hits[Nk] = (S, i, r, j, r2, float(T[k]))
    print('%d layouts, %d pairs of quarter turns, %.0f s' % (len(lay), npairs, time.time() - t0))
    if ctl:
        print('control: the best seam of layout %d with itself holds %d squares (want %d)' % (ctl, best_ctl, ctl)); return
    for Nk in sorted(hits):
        S, i, r, j, r2, t = hits[Nk]
        n, s, Q, src = lay[i]; n2, s2, Q2, src2 = lay[j]
        A = rot(Q, s, r); KA = fc.corners(A); A = A[KA[:, :, 0].max(1) <= t + EPS]
        B = rot(Q2, s2, r2); B[:, 0] += S - s2; KB = fc.corners(B); B = B[KB[:, :, 0].min(1) >= t - EPS]
        hS, hS2 = int(math.floor(S - s + EPS)), int(math.floor(S - s2 + EPS))
        G = [(x + 0.5, S - 0.5 - y, 0.0) for x in range(int(math.floor(t + EPS))) for y in range(hS)]
        G += [(S - 0.5 - x, S - 0.5 - y, 0.0) for x in range(int(math.floor(S - t + EPS))) for y in range(hS2)]
        X = np.r_[A, B, np.array(G, float).reshape(-1, 3)][:Nk]
        w = fc.worst_overlap(X); Kx = fc.corners(X)
        okb = Kx.min() >= -1e-9 and Kx.max() <= S + 1e-9
        g = (D[Nk] - S) / math.sqrt(Nk)
        print('   N %d at side %.10f against %.10f (gain %.3e): left of %d [%s] turn %d, right of %d [%s] turn %d, cut at %.6f; %d squares built, worst gap %.1e, in box %s' % (
            Nk, S, D[Nk], g, n, src, r, n2, src2, r2, t, len(X), w, okb))
        if len(X) == Nk and w >= -1e-9 and okb:
            fc.write_csv('%s/%d.csv' % (out, Nk), Nk, X)


if __name__ == '__main__':
    main()
