#!/usr/bin/env python3
"""Layouts read as cores, and two cores with separate rows and columns in one square.

A row is plain when it holds m upright squares in a slab that no other square enters. A plain row or column
can be taken out. What is left is the core: r rows by c columns that gain k squares at the side fraction f.
Two cores add when they share no row and no column, so a core of r1 by c1 and one of r2 by c2 fit a square
of m = r1 + r2 = c1 + c2 with k1 + k2 squares over the grid. forensics_compose.py is the case of two square
cores. Here the cores may be rectangles, which fit a smaller square.

  census  MERGED.csv DETAILS.csv [OUT.tsv]   the core of every layout, and every n that two cores would give
                                             below the side to beat, by the sides alone
  build   MERGED.csv DETAILS.csv OUT_DIR N:N1:N2[,...]   n from the cores of the layouts of n1 and n2, in every
                                             orientation, with a check of every pair of squares
  ctl     MERGED.csv DETAILS.csv OUT_DIR     639 must come back from the 10 and the 497 with no row taken out,
                                             and n = 18 from two packings of 5 must give no layout
"""
import sys, os, math, collections
import numpy as np
from scipy.spatial import cKDTree
import forensics_compose as fc
import forensics_pool as fp

TOL = 1e-9


def plain(Q, m, axis):
    """Plain rows (axis 1) or columns (axis 0): [(centre, indices)]."""
    up = np.abs(np.sin(4 * Q[:, 2])) < 1e-6
    h = (np.abs(np.cos(Q[:, 2])) + np.abs(np.sin(Q[:, 2]))) / 2
    c = Q[:, axis]; lo = c - h; hi = c + h; groups = collections.defaultdict(list); out = []
    for i in np.nonzero(up)[0]:
        groups[round(float(c[i]), 5)].append(i)
    for yc, idx in groups.items():
        if len(idx) != m:
            continue
        rest = np.ones(len(Q), bool); rest[idx] = False
        if np.all((hi[rest] <= yc - 0.5 + 1e-6) | (lo[rest] >= yc + 0.5 - 1e-6)):
            out.append((yc, idx))
    return out


def core(sq, n, strip=True):
    """(width, height, squares, rows, columns, k, f) of a layout without its plain rows and columns."""
    m, k = fc.mk(n); s, Q = fc.frame(sq); f = s - m; Q = Q.copy(); r = c = m
    if strip:
        for axis in (1, 0):
            while True:
                cl = plain(Q, c if axis == 1 else r, axis)
                if not cl:
                    break
                yc, idx = max(cl); keep = np.ones(len(Q), bool); keep[idx] = False
                Q = Q[keep]; Q[Q[:, axis] > yc, axis] -= 1.0
                if axis == 1:
                    r -= 1
                else:
                    c -= 1
    if len(Q) != r * c + k:
        raise ValueError('core of n = %d: %d squares for %d rows, %d columns, k = %d' % (n, len(Q), r, c, k))
    return c + f, r + f, Q, r, c, k, f


def orient(w, h, Q, g):
    """The 8 orientations of a rectangle of squares: bit 0 flips x, bit 1 flips y, bit 2 swaps x and y."""
    R = Q.copy()
    if g & 1:
        R[:, 0] = w - R[:, 0]; R[:, 2] = -R[:, 2]
    if g & 2:
        R[:, 1] = h - R[:, 1]; R[:, 2] = -R[:, 2]
    if g & 4:
        R = np.column_stack([R[:, 1], R[:, 0], math.pi / 2 - R[:, 2]]); w, h = h, w
    return w, h, R


def compose(n, X, Y):
    """Core X bottom-left, core Y top-right, two grid blocks: (best valid layout or None, least collision)."""
    m, k = fc.mk(n); f = max(X[6], Y[6]); S = m + f; best = None; least = None
    if X[5] + Y[5] != k:
        return None, None
    for g1 in range(8):
        w1, h1, A = orient(X[0], X[1], X[2], g1); c1, r1 = round(w1 - X[6]), round(h1 - X[6])
        for g2 in range(8):
            w2, h2, B = orient(Y[0], Y[1], Y[2], g2); c2, r2 = round(w2 - Y[6]), round(h2 - Y[6])
            if c1 + c2 != m or r1 + r2 != m:
                continue
            B = B.copy(); B[:, 0] += S - w2; B[:, 1] += S - h2
            G = [(S - 0.5 - i, 0.5 + j, 0.0) for i in range(m - c1) for j in range(m - r2)] + [(0.5 + i, S - 0.5 - j, 0.0) for i in range(m - c2) for j in range(m - r1)]
            Z = np.r_[A, B, np.array(G, float).reshape(-1, 3)]
            if len(Z) != n:
                continue
            K = fc.corners(Z)
            if K.min() < -TOL or K.max() > S + TOL:
                continue
            bad = 0; deep = 0.0
            for i, j in cKDTree(Z[:, :2]).query_pairs(1.4143):
                gp = fc.gap(K[i], K[j])
                if gp < -TOL:
                    bad += 1; deep = max(deep, -gp)
            if least is None or (bad, deep) < least:
                least = (bad, deep)
            if bad == 0 and best is None:
                best = (S, Z)
    return best, least


def cmd_census(merged, details, out):
    D, fh = fc.held_f(details); M = fp.load_merged(merged); mods = {}
    for n in range(5, 1001):
        m, k = fc.mk(n)
        if k < 1 or (m, k) not in fh or fh[(m, k)] > 0.999:
            continue
        w, h, Q, r, c, k, f = core(M[n], n); mods[n] = (r, c, k, fh[(m, k)], m)
    best = {}
    for n, (r, c, k, f, m) in mods.items():
        key = (min(r, c), max(r, c), k)
        if key not in best or f < best[key][0]:
            best[key] = (f, n)
    print('%d layouts read, %d have a plain row or column, %d cores are not square' % (len(mods), sum(1 for v in mods.values() if min(v[0], v[1]) < v[4]), sum(1 for v in mods.values() if v[0] != v[1])))
    cores = [(a, b, k, f, n) for (a, b, k), (f, n) in best.items()]; res = {}
    for i, (a1, b1, k1, f1, n1) in enumerate(cores):
        for a2, b2, k2, f2, n2 in cores[i:]:
            f = max(f1, f2); K = k1 + k2
            for Mm in {a1 + b2, a1 + a2} if a1 + b2 == b1 + a2 or (a1 + a2 == b1 + b2) else ():
                if not ((a1 + b2 == Mm and b1 + a2 == Mm) or (a1 + a2 == Mm and b1 + b2 == Mm)):
                    continue
                if Mm > 31 or K > 2 * Mm or (Mm, K) not in fh:
                    continue
                g = (fh[(Mm, K)] - f) / math.sqrt(Mm * Mm + K); key = Mm * Mm + K
                if g > 2e-10 and (key not in res or g > res[key][0]):
                    res[key] = (g, n1, (a1, b1, k1), n2, (a2, b2, k2), f, a1 != b1 or a2 != b2)
    rows = []
    for nt, (g, n1, c1, n2, c2, f, rect) in sorted(res.items(), key=lambda x: -x[1][0]):
        m, k = fc.mk(nt); rows.append([nt, m, k, '%.9f' % fh[(m, k)], '%.9f' % f, '%.3e' % g, n1, '%dx%d' % c1[:2], n2, '%dx%d' % c2[:2], 'rectangle' if rect else 'square'])
    print('%d n where two cores give a lower side by the sides alone, %d of them with a core that is not square (%.5f of score)' % (len(rows), sum(1 for r in rows if r[-1] == 'rectangle'), sum(float(r[5]) for r in rows if r[-1] == 'rectangle')))
    for r in rows:
        if r[-1] == 'rectangle':
            print('   n %d (%d,%d) to beat f %s: cores of n = %d (%s) and n = %d (%s) give f %s, gain %s' % (r[0], r[1], r[2], r[3], r[6], r[7], r[8], r[9], r[4], r[5]))
    if out:
        with open(out, 'w') as h:
            h.write('n\tm\tk\tf_to_beat\tcores_f\tgain_if_valid\tn_a\tcore_a\tn_b\tcore_b\tcores\n')
            for r in rows:
                h.write('\t'.join(str(x) for x in r) + '\n')


def cmd_build(merged, details, out, specs, quiet=False):
    D, fh = fc.held_f(details); M = fp.load_merged(merged); os.makedirs(out, exist_ok=True); got = {}
    for spec in specs.split(','):
        n, n1, n2 = [int(x) for x in spec.split(':')]
        for strip in (True, False):
            X = core(M[n1], n1, strip); Y = core(M[n2], n2, strip)
            best, least = compose(n, X, Y); tag = 'cores %dx%d and %dx%d' % (X[3], X[4], Y[3], Y[4])
            if best:
                fc.write_csv('%s/%d.csv' % (out, n), n, best[1]); got[n] = best[0]
                print('n %d from n = %d and n = %d (%s): VALID side %.10f, to beat %.10f, gain %.3e' % (n, n1, n2, tag, best[0], D[n], (D[n] - best[0]) / math.sqrt(n)), flush=True)
                break
            print('n %d from n = %d and n = %d (%s): no valid layout, %s' % (n, n1, n2, tag, 'no orientation fits' if least is None else 'least collision %d pair(s), %.3f deep' % least), flush=True)
    return got


def cmd_ctl(merged, details, out):
    D, fh = fc.held_f(details); got = cmd_build(merged, details, out, '639:10:497,18:5:5')
    ok = 639 in got and got[639] < D[639] + 1e-8 and 18 not in got
    print('positive: 639 from the 10 and the 497: %s. negative: 18 from two packings of 5: %s' % ('layout at %.10f' % got[639] if 639 in got else 'NO LAYOUT', 'LAYOUT' if 18 in got else 'no layout'))
    print('CONTROL GREEN' if ok else 'CONTROL RED'); return 0 if ok else 1


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'census':
        cmd_census(a[1], a[2], a[3] if len(a) > 3 else None)
    elif a and a[0] == 'build':
        cmd_build(a[1], a[2], a[3], a[4])
    elif a and a[0] == 'ctl':
        sys.exit(cmd_ctl(a[1], a[2], a[3]))
    else:
        print(__doc__)
