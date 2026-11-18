#!/usr/bin/env python3
"""Put two held layouts into opposite corners of one square.

A layout of a*a + ka squares at side a + fa goes into the top-left corner and one of b*b + kb squares at
side b + fb into the bottom-right corner of a square of side a + b + f, with f the larger of fa and fb.
An a-by-b block of grid squares fills the bottom-left corner and a b-by-a block the top-right corner.
The count is (a + b)^2 + ka + kb. The two boxes overlap in one small square of side fa + fb - f at the
middle, so the layout is valid only when the two packings do not collide there. A layout that keeps a
corner empty (two grids pushed into opposite corners) gives that for free.

  table   every n where two held layouts give a side below the held one, by the sides alone.
  build   tries each pair of the table in the 64 pairs of symmetries, checks every pair of squares of
          the result for overlap, and writes OUT/<n>.csv when the layout is valid.
  fill    the same pairs, but only the tilted squares of the two layouts are kept. The uprights come
          from the exact fill, and fq quenches each layout that reaches the count.
  ctl     n = 18 from two packings of 5 must give no layout (the known side of 18 is larger), and the
          overlap check must tell touching squares from crossed ones.

Usage:
  forensics_compose.py table HELD_DETAILS.csv [OUT.tsv]
  forensics_compose.py build HELD.csv HELD_DETAILS.csv OUT_DIR [--only N,N,...] [--all-splits]
  forensics_compose.py fill HELD.csv HELD_DETAILS.csv OUT_DIR [--only N,N,...] [--fq PATH] [--max-splits 4]
  forensics_compose.py ctl HELD.csv HELD_DETAILS.csv
"""
import sys, os, csv, math, argparse, collections
import numpy as np
from scipy.spatial import cKDTree

TOL = 1e-12


def mk(n):
    m = math.isqrt(n); return m, n - m * m


def held_f(details):
    D = {int(r[0]): float(r[1]) for r in csv.reader(open(details)) if r[0].isdigit()}
    fh = {}
    for n in range(1, 1001):
        m, k = mk(n); fh[(m, k)] = D[n] - m
    return D, fh


def splits(fh, min_gain=1e-9):
    """n -> list of (f, a, ka, b, kb), best first. ka and kb are the k of the held layouts used."""
    best = {}
    for a in range(1, 32):
        run = None; src = None
        for k in range(2 * a, 0, -1):
            if (a, k) in fh and (run is None or fh[(a, k)] <= run):
                run = fh[(a, k)]; src = k
            if run is not None:
                best[(a, k)] = (run, src)
    out = {}
    for n in range(2, 1001):
        m, k = mk(n)
        if k < 2:
            continue
        rows = []
        for a in range(1, m):
            b = m - a
            for ka in range(1, k):
                kb = k - ka
                if (a, ka) not in best or (b, kb) not in best:
                    continue
                (fa, sa), (fb, sb) = best[(a, ka)], best[(b, kb)]
                f = max(fa, fb)
                if f < fh[(m, k)] - min_gain:
                    rows.append((f, a, sa, b, sb))
        if rows:
            out[n] = sorted(set(rows))
    return out


def load_all(held, want):
    rows = collections.defaultdict(list)
    for r in csv.DictReader(open(held)):
        n = int(r['n'])
        if n in want:
            rows[n].append((float(str(r['x']).lstrip('s')), float(str(r['y']).lstrip('s')), float(str(r['angle']).lstrip('s'))))
    return rows


def corners(Q):
    c, s = np.cos(Q[:, 2]), np.sin(Q[:, 2])
    off = np.array([[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]])
    return Q[:, None, :2] + np.stack([off[:, 0] * c[:, None] - off[:, 1] * s[:, None], off[:, 0] * s[:, None] + off[:, 1] * c[:, None]], -1)


def frame(sq):
    """Squares as (x, y, radians) with the box at the origin; returns (side, array)."""
    Q = np.array(sq, float); K = corners(Q)
    x0, y0 = K[:, :, 0].min(), K[:, :, 1].min()
    Q[:, 0] -= x0; Q[:, 1] -= y0
    return max(K[:, :, 0].max() - x0, K[:, :, 1].max() - y0), Q


def sym(Q, s, g):
    """One of the 8 symmetries of the box [0, s]^2."""
    R = Q.copy()
    if g & 4:
        R[:, 0] = s - R[:, 0]; R[:, 2] = -R[:, 2]
    for _ in range(g & 3):
        x, y = R[:, 0].copy(), R[:, 1].copy()
        R[:, 0] = s - y; R[:, 1] = x; R[:, 2] += math.pi / 2
    return R


def gap(P, Q):
    """Separating-axis gap of two squares given as 4x2 corner arrays (negative = overlap depth)."""
    best = -np.inf
    for K in (P, Q):
        for i in (0, 1):
            u = K[i + 1] - K[i]; u = u / np.hypot(*u)
            a, b = P @ u, Q @ u
            best = max(best, b.min() - a.max(), a.min() - b.max())
    return best


def worst_overlap(Q, R=None):
    """Smallest gap over the near pairs of Q (or between Q and R)."""
    KQ = corners(Q); worst = np.inf
    if R is None:
        for i, j in cKDTree(Q[:, :2]).query_pairs(1.4143):
            worst = min(worst, gap(KQ[i], KQ[j]))
    else:
        if not len(R) or not len(Q):
            return worst
        KR = corners(R); t = cKDTree(R[:, :2])
        for i, near in enumerate(t.query_ball_point(Q[:, :2], 1.4143)):
            for j in near:
                worst = min(worst, gap(KQ[i], KR[j]))
    return worst


def compose(A, sA, a, B, sB, b):
    """Every valid layout of the two packings in opposite corners: yields (side, squares, gA, gB)."""
    fa, fb = sA - a, sB - b; f = max(fa, fb); s = a + b + f
    grid = [(i + 0.5, j + 0.5, 0.0) for i in range(a) for j in range(b)] + [(s - 0.5 - i, s - 0.5 - j, 0.0) for i in range(b) for j in range(a)]
    G = np.array(grid, float).reshape(-1, 3)
    for gA in range(8):
        A2 = sym(A, sA, gA); A2[:, 1] += s - sA                    # top-left
        nearA = A2[(A2[:, 0] > s - sB - 1.5) & (A2[:, 1] < sB + 1.5)]
        for gB in range(8):
            B2 = sym(B, sB, gB); B2[:, 0] += s - sB                # bottom-right
            nearB = B2[(B2[:, 0] < sA + 1.5) & (B2[:, 1] > s - sA - 1.5)]
            if worst_overlap(nearA, nearB) < -TOL:
                continue
            yield s, np.r_[A2, B2, G], gA, gB


def write_csv(path, n, X):
    with open(path, 'w', newline='') as h:
        w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for i, (x, y, g) in enumerate(X):
            w.writerow([n, i, repr(float(x)), repr(float(y)), repr(float(g))])


def try_split(rows, n, a, ka, b, kb):
    nA, nB = a * a + ka, b * b + kb
    sA, A = frame(rows[nA]); sB, B = frame(rows[nB])
    for s, X, gA, gB in compose(A, sA, a, B, sB, b):
        if len(X) < n:
            return None
        X = X[:n] if len(X) == n else np.r_[X[:nA + nB], X[nA + nB:][:n - nA - nB]]
        K = corners(X)
        if K.min() < -TOL or K.max() > s + TOL:
            continue
        w = worst_overlap(X)
        if w < -TOL:
            continue
        return s, X, gA, gB, w
    return None


def tilted_part(Q):
    return Q[np.abs(np.sin(4 * Q[:, 2])) > 1e-6]


def cmd_fill(held, details, out, only, fq, max_splits):
    """The same two layouts, but only their tilted squares are kept and the uprights come from the exact fill
    (Evan Daniel's fillfast, MIT, imported from his clone through EVAND_PACKER). Each layout that reaches the count
    is quenched once with fq and written when its side is below the held side."""
    sys.path.insert(0, os.environ.get('EVAND_PACKER', '$SCRATCH/bounties-squares/ext/evand/search/packer'))
    import fillfast, forensics_turn as ft
    D, fh = held_f(details); S = splits(fh, min_gain=2e-7)
    if only:
        S = {n: S[n] for n in S if n in only}
    want = set()
    for n in S:
        for f, a, ka, b, kb in S[n][:max_splits]:
            want.add(a * a + ka); want.add(b * b + kb)
    rows = load_all(held, want)
    os.makedirs(out, exist_ok=True)
    for n in sorted(S, key=lambda n: -(fh[mk(n)] - S[n][0][0]) / math.sqrt(n)):
        m, k = mk(n); best = 0; done = False; fills = 0
        for f, a, ka, b, kb in S[n][:max_splits]:
            nA, nB = a * a + ka, b * b + kb
            sA, A = frame(rows[nA]); sB, B = frame(rows[nB])
            s = a + b + max(sA - a, sB - b) + 2e-9
            seen = set()
            for gA in range(8):
                A2 = sym(A, sA, gA); A2[:, 1] += s - sA; TA = tilted_part(A2)
                for gB in range(8):
                    B2 = sym(B, sB, gB); B2[:, 0] += s - sB; TB = tilted_part(B2)
                    key = (tuple(np.round(np.sort(TA[:, 0] * 7 + TA[:, 1]), 6)), tuple(np.round(np.sort(TB[:, 0] * 7 + TB[:, 1]), 6)))
                    if key in seen:
                        continue
                    seen.add(key)
                    if worst_overlap(TA, TB) < -1e-9:
                        continue
                    T = np.r_[TA, TB]; T = np.c_[T[:, :2], np.degrees(T[:, 2])]
                    R = fillfast.fill(s, T, mode='exact', time_limit=5); fills += 1
                    best = max(best, len(R))
                    if len(R) < n:
                        continue
                    X = np.r_[R[:len(T)], R[len(T):][:n - len(T)]]
                    s2, Q = ft.quench(fq, s, X, [], timeout=600)
                    if s2 is None or s2 >= D[n] - 1e-9:
                        print('n %4d (%2d,%2d): fill reaches %d from n = %d and n = %d but the quench ends at %s (held %.10f)' % (n, m, k, len(R), nA, nB, s2, D[n]), flush=True)
                        continue
                    ft.write_rows('%s/%d.csv' % (out, n), n, Q)
                    print('n %4d (%2d,%2d): BUILT from n = %d (symmetry %d) and n = %d (symmetry %d): side %.10f, held %.10f, gain %.3e' % (n, m, k, nA, gA, nB, gB, s2, D[n], (D[n] - s2) / math.sqrt(n)), flush=True)
                    done = True; break
                if done:
                    break
            if done:
                break
        if not done:
            print('n %4d (%2d,%2d): best fill %d of %d over %d fills (gain if valid %.3e)' % (n, m, k, best, n, fills, (fh[(m, k)] - S[n][0][0]) / math.sqrt(n)), flush=True)


def cmd_table(details, out):
    D, fh = held_f(details); S = splits(fh)
    tot = 0.0; lines = []
    for n in sorted(S, key=lambda n: -(fh[mk(n)] - S[n][0][0]) / math.sqrt(n)):
        m, k = mk(n); f, a, ka, b, kb = S[n][0]; g = (fh[(m, k)] - f) / math.sqrt(n); tot += g
        lines.append([n, m, k, '%.9f' % fh[(m, k)], '%.9f' % f, '%.3e' % g, a * a + ka, b * b + kb, len(S[n])])
    print('%d n where two held layouts have a lower side by the sides alone, %.6f of score if every one were valid' % (len(S), tot))
    for l in lines[:40]:
        print('   n %4d (%2d,%2d) held f %s -> %s gain %s  from n = %d and n = %d  (%d splits)' % tuple(l))
    if out:
        with open(out, 'w', newline='') as h:
            w = csv.writer(h, delimiter='\t'); w.writerow(['n', 'm', 'k', 'held_f', 'composed_f', 'gain_if_valid', 'n_a', 'n_b', 'splits']); w.writerows(lines)


def cmd_build(held, details, out, only, all_splits):
    D, fh = held_f(details); S = splits(fh)
    if only:
        S = {n: S[n] for n in S if n in only}
    want = set()
    for n in S:
        for f, a, ka, b, kb in S[n]:
            want.add(a * a + ka); want.add(b * b + kb)
    rows = load_all(held, want)
    os.makedirs(out, exist_ok=True); got = 0; tot = 0.0
    for n in sorted(S):
        m, k = mk(n); done = False; tried = 0
        for f, a, ka, b, kb in (S[n] if all_splits else S[n][:6]):
            tried += 1
            r = try_split(rows, n, a, ka, b, kb)
            if r is None:
                continue
            s, X, gA, gB, w = r
            if s >= D[n] - 1e-9:
                continue
            write_csv('%s/%d.csv' % (out, n), n, X)
            g = (D[n] - s) / math.sqrt(n); got += 1; tot += g
            print('n %4d (%2d,%2d): VALID from n = %d (symmetry %d) and n = %d (symmetry %d): side %.10f, held %.10f, gain %.3e, smallest gap %.1e' % (n, m, k, a * a + ka, gA, b * b + kb, gB, s, D[n], g, w), flush=True)
            done = True; break
        if not done:
            print('n %4d (%2d,%2d): no valid layout in %d splits (best by the sides: n = %d and n = %d)' % (n, m, k, tried, S[n][0][1] ** 2 + S[n][0][2], S[n][0][3] ** 2 + S[n][0][4]), flush=True)
    print('%d of %d n built, gain %.6f before the certificate' % (got, len(S), tot))


def cmd_ctl(held, details):
    """A split that must fail (n = 18 from two packings of 5: the known side of 18 is 4.8229) and the overlap check."""
    D, fh = held_f(details); rows = load_all(held, {5, 52})
    r = try_split(rows, 18, 2, 1, 2, 1)
    bad = r is not None
    print('negative: n = 18 from two packings of 5 at 4.7071 (the known optimum is 4.8229): %s (want no layout)' % ('LAYOUT FOUND' if bad else 'no layout'))
    sA, A = frame(rows[5]); G = np.array([(0.5, 0.5, 0.0), (0.5, 1.5, 0.0)])
    ok = abs(worst_overlap(np.r_[G])) < 1e-9 and worst_overlap(np.array([(0.5, 0.5, 0.0), (0.9, 0.5, 0.3)])) < -0.1
    print('overlap check: two touching grid squares give gap 0 and two crossed squares a negative gap: %s' % ok)
    print('CONTROL GREEN' if ok and not bad else 'CONTROL RED'); return 0 if ok and not bad else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=['table', 'build', 'fill', 'ctl']); ap.add_argument('args', nargs='*')
    ap.add_argument('--only', default=''); ap.add_argument('--all-splits', action='store_true')
    ap.add_argument('--fq', default=os.path.expanduser('$SCRATCH/squares-base/fq')); ap.add_argument('--max-splits', type=int, default=4)
    a = ap.parse_args()
    if a.cmd == 'fill':
        cmd_fill(a.args[0], a.args[1], a.args[2], {int(v) for v in a.only.split(',') if v}, a.fq, a.max_splits); sys.exit(0)
    if a.cmd == 'table':
        cmd_table(a.args[0], a.args[1] if len(a.args) > 1 else None)
    elif a.cmd == 'build':
        cmd_build(a.args[0], a.args[1], a.args[2], {int(v) for v in a.only.split(',') if v}, a.all_splits)
    else:
        sys.exit(cmd_ctl(a.args[0], a.args[1]))
