#!/usr/bin/env python3
"""Corner compositions that are one square short, below the side to beat: starts for midm_scan.py grow1.

forensics_pool.py build fails on every target the same way: two upright squares collide in the inner corners of
the two parts, so the layout holds one square too many. Leave one square of each colliding pair out and the layout
is valid with n - 1 squares at the side of the pair, which is below the side to beat. Round 17 quenched the other
kind of start (parts with a square to spare, valid with n squares, above the side to beat) and it did not shrink.
This start has room instead: the side may grow up to the side to beat while one square goes back in.

For each target with jobs in the build, the PAIRS lowest pairs of part versions are placed in all 8 x 8 symmetries.
A placement counts when one square from each colliding pair, at most E + 1 squares, makes it valid. The KEEP lowest
distinct placements per n are written as OUT/<n>-<i>.csv with the layout under the count n - 1 (the donor file of
midm_scan.py grow1), and OUT/list.tsv lists them.

Usage: forensics_short.py VERS.pkl MERGED.csv DETAILS.csv OUT [--only N,N] [--pairs 30] [--keep 4] [--extra 2]
"""
import sys, os, math, pickle, argparse
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forensics_compose as fc
import forensics_pool as fp


def short_layouts(PA, a, PB, b, n, e):
    """Valid layouts of n - 1 squares from two parts with e squares to spare and one square more left out."""
    sA, sB = PA.s, PB.s; f = max(sA - a, sB - b); s = a + b + f; out = []
    G = np.array([(i + 0.5, j + 0.5, 0.0) for i in range(a) for j in range(b)] + [(s - 0.5 - i, s - 0.5 - j, 0.0) for i in range(b) for j in range(a)], float).reshape(-1, 3)
    for gA in range(8):
        A2 = PA.S[gA].copy(); A2[:, 1] += s - sA
        for gB in range(8):
            B2 = PB.S[gB].copy(); B2[:, 0] += s - sB
            pairs = fp.collide(A2, B2, s, sA, sB)
            if not pairs:
                continue
            c = fp.cover(pairs, e + 1)
            if c is None:
                continue
            da = sorted({i for side, i in c if side == 'A'}); db = sorted({i for side, i in c if side == 'B'})
            X = np.r_[np.delete(A2, da, 0), np.delete(B2, db, 0), G]
            if len(X) < n - 1:
                continue
            X = X[:n - 1]
            K = fc.corners(X)
            if K.min() < -fp.TOL or K.max() > s + fp.TOL or fc.worst_overlap(X) < -fp.TOL:
                continue
            out.append((s, X, gA, gB, len(pairs)))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('vers'); ap.add_argument('merged'); ap.add_argument('details'); ap.add_argument('out')
    ap.add_argument('--only', default=''); ap.add_argument('--pairs', type=int, default=30); ap.add_argument('--keep', type=int, default=4)
    ap.add_argument('--extra', type=int, default=2)
    a = ap.parse_args()
    V = pickle.load(open(a.vers, 'rb')); D, fh = fc.held_f(a.details)
    T = fp.parts_table(V, fp.load_merged(a.merged)); cache = {}
    def part(key, i):
        if (key, i) not in cache:
            cache[(key, i)] = fp.Part(*T[key][i])
        return cache[(key, i)]
    os.makedirs(a.out, exist_ok=True); rows = []
    only = sorted(int(v) for v in a.only.split(',') if v) if a.only else range(2, 1001)
    for n in only:
        m, k = fc.mk(n)
        if k < 2 or (m, k) not in fh:
            continue
        ft = fh[(m, k)] - 2e-10 * math.sqrt(n); jobs = []
        for aa in range(1, m):
            b = m - aa
            for ka in range(1, 2 * aa + 1):
                LA = [i for i, v in enumerate(T.get((aa, ka), [])[:40]) if v[0] - aa < ft]
                if not LA:
                    continue
                for kb in range(max(1, k - ka), min(2 * b, k - ka + a.extra) + 1):
                    LB = [i for i, v in enumerate(T.get((b, kb), [])[:40]) if v[0] - b < ft]
                    for i in LA:
                        for j in LB:
                            jobs.append((max(T[(aa, ka)][i][0] - aa, T[(b, kb)][j][0] - b), ka + kb - k, aa, ka, i, b, kb, j))
        if not jobs:
            continue
        jobs.sort(); got = []; seen = set()
        for f, e, aa, ka, i, b, kb, j in jobs[:a.pairs]:
            for s, X, gA, gB, nc in short_layouts(part((aa, ka), i), aa, part((b, kb), j), b, n, e):
                key = (round(s, 8), round(float(np.sort(X[:, 0] + 3 * X[:, 1])[:7].sum()), 3))
                if key in seen:
                    continue
                seen.add(key); got.append((s, X, '%d+%d sym %d %d, %d colliding' % (aa * aa + ka, b * b + kb, gA, gB, nc)))
            if len(got) >= 4 * a.keep:
                break
        got.sort(key=lambda r: r[0])
        for q, (s, X, tag) in enumerate(got[:a.keep]):
            p = '%s/%d-%d.csv' % (a.out, n, q); fc.write_csv(p, n - 1, X)
            rows.append((n, p, D[n], s, (D[n] - s) / math.sqrt(n), tag))
        print('n %4d (%2d,%2d) to beat %.10f: %d short layouts; %s' % (n, m, k, D[n], len(got),
              '; '.join('%.10f (%s)' % (s, t) for s, _, t in got[:a.keep]) or 'none'), flush=True)
    rows.sort(key=lambda r: -r[4])
    with open(a.out + '/list.tsv', 'w') as h:
        h.write('n\tfile\tto_beat\tside_short\troom_score\twhat\n')
        for r in rows:
            h.write('%d\t%s\t%.10f\t%.10f\t%.3e\t%s\n' % r)
    print('%d starts for %d n' % (len(rows), len({r[0] for r in rows})), flush=True)


if __name__ == '__main__':
    main()
