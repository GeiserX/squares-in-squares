#!/usr/bin/env python3
"""A step of 5 rows and 7 chains on a held band of chains of 3 (avenues/k123.md, section 10).

Seven chains of a band at a turn near 10 degrees are 7 / cos(turn) long on the diagonal, and five rows and
five columns are 5 * sqrt(2). The two differ by 0.04, so a held band at m gives a start for m - 5 and for
m + 5 that keeps both ends of the held band: cut seven chains, five rows and five columns out of the
middle (or copy them in), and leave the 0.04 to the squeeze. The ends of a held band are not uniform: the
last chains turn by other angles, and a band built at one angle does not find them.

  k123_step57.py HELD.csv N DIR OUTDIR [--j0 8,10,12,14,16,18] [--top 4] [--grid 0.6] [--dg 0.1]
    N    the held n to start from (680)
    DIR  down (n of m - 5: 5 rows, 5 columns and 7 chains fewer) or up (m + 5, from two copies of the layout;
         --j0 is then the chain at the seam)
  It writes OUTDIR/<n2>-step-<dir>-j<j0>-<rank>.csv: Kaggle rows of the starts with the right count and the
  smallest overlap. Use a start whose worst gap is not negative. Finish it with k123_turn.py (--turns=0, fq) or family_step.squeeze,
  then certify with methods_take.py on boxA.

  --n2 COUNT  the count of the target, for a band whose chains are not of 3 (267 up to 456: --n2 456)

Controls (2026-11-12, all to 1e-9 of side): the new 444 down gives the held 258, the held 403 up gives the held
629, and the new 579 up gives the 845 of take-border-r17.
Our own code. It imports methods_lp and family_step (write_rows) and does not change them.
"""
import argparse, math, os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import family_step as fs  # noqa: E402
import methods_lp as mlp  # noqa: E402


def boxed(P):
    """The layout moved so that its box is [0, L] x [0, L]. -> (array, L)"""
    Q = mlp.normal(P).copy(); cs = []
    for x, y, a in Q:
        for dx, dy in ((.5, .5), (.5, -.5), (-.5, .5), (-.5, -.5)):
            cs.append((x + dx * math.cos(a) - dy * math.sin(a), y + dx * math.sin(a) + dy * math.cos(a)))
    cs = np.array(cs); o = cs.min(axis=0)
    Q[:, :2] -= o
    return Q, float((cs.max(axis=0) - o).max())


def chains(Q):
    """The tilted squares in chains, ordered along the diagonal. -> (list of index arrays, upright index array)"""
    th = np.degrees(Q[:, 2]) % 90.0
    t = np.nonzero((th > 1.0) & (th < 89.0))[0]
    al = math.radians(float(np.median(th[t])) - 90.0)
    v = np.array([-math.sin(al), math.cos(al)])
    q = Q[t, :2] @ v
    order = np.argsort(q); groups = [[order[0]]]
    for i in order[1:]:
        if q[i] - q[groups[-1][-1]] > 0.3:
            groups.append([i])
        else:
            groups[-1].append(i)
    up = np.nonzero(~((th > 1.0) & (th < 89.0)))[0]
    return [t[np.array(g)] for g in groups], up


def step(Q, G, up, j0, s, X0, Y0, a=0.0):
    """The start after a step: s = 5 cuts, s = -5 copies in. The uprights above the band are cut at
    (X0 - a, Y0 + a) and the ones below it at (X0 + a, Y0 - a), so that no cut line crosses the band. -> array"""
    U = Q[up]; parts = []
    side = U[:, 1] > U[:, 0]
    for above, V, xc, yc in ((True, U[side], X0 - a, Y0 + a), (False, U[~side], X0 + a, Y0 - a)):
        x, y = V[:, 0], V[:, 1]
        parts.append(V[(x < xc) & (y < yc)])
        # the quarter on the far side of the band stays empty: no upright of this side belongs there
        far = ((x > xc + s) & (y > yc + s), -s, -s)
        cross = ((x < xc) & (y > yc + s), 0.0, -s) if above else ((x > xc + s) & (y < yc), -s, 0.0)
        for mask, dx, dy in (far, cross):
            B = V[mask].copy(); B[:, 0] += dx; B[:, 1] += dy; parts.append(B)
    for j, g in enumerate(G):
        if j < j0:
            parts.append(Q[g])
    for j, g in enumerate(G):
        if j >= j0 + (7 if s > 0 else -7):
            B = Q[g].copy(); B[:, 0] -= s; B[:, 1] -= s; parts.append(B)
    return np.vstack(parts)


def step_up(Q, G, up, j1, d, cut=0.0):
    """The start of a step up, from two copies of the layout. The second copy is moved by (5 + d, 5 + d).
    Chains j < j1 come from the first copy and chains j >= j1 - 7 from the second. An upright comes from the
    copy on its side of the seam (cut moves the seam of the uprights). The two far corners get the 25
    uprights of the corner next to them. With d = 0.03 the two chains at the seam do not overlap. -> array"""
    sh = 5.0 + d
    c = [float(Q[g, 0].mean() + Q[g, 1].mean()) for g in G]                 # x + y of each chain
    S = (c[j1 - 1] + c[j1 - 7] + 2 * sh) / 2 + cut                           # the seam, in x + y
    parts = [Q[g] for g in G[:j1]]
    for g in G[j1 - 7:]:
        B = Q[g].copy(); B[:, :2] += sh; parts.append(B)
    U = Q[up]; sm = U[:, 0] + U[:, 1]; L = float(U[:, :2].max()) + 0.5
    parts.append(U[sm < S])
    B = U[sm + 10.0 >= S].copy(); B[:, :2] += sh; parts.append(B)
    B = U[(U[:, 0] > L - 5.0) & (U[:, 1] < 5.0)].copy(); B[:, 0] += sh; parts.append(B)
    B = U[(U[:, 0] < 5.0) & (U[:, 1] > L - 5.0)].copy(); B[:, 1] += sh; parts.append(B)
    return np.vstack(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('held'); ap.add_argument('n', type=int); ap.add_argument('dir', choices=('down', 'up')); ap.add_argument('out')
    ap.add_argument('--j0', default='8,10,12,14,16,18'); ap.add_argument('--top', type=int, default=4)
    ap.add_argument('--grid', type=float, default=0.6); ap.add_argument('--dg', type=float, default=0.1)
    ap.add_argument('--n2', type=int, default=0, help='the count of the target, for a band of chains that are not of 3')
    a = ap.parse_args()
    Q, L = boxed(mlp.load(a.held, {a.n})[a.n]); m = int(L)
    G, up = chains(Q)
    if abs(float(np.mean([Q[g, 0].mean() - Q[g, 1].mean() for g in G]))) > 2.0:      # a band on the other diagonal: mirror
        Q[:, 0] = L - Q[:, 0]; Q[:, 2] = -Q[:, 2]
        G, up = chains(Q)
    s = 5.0 if a.dir == 'down' else -5.0
    m2 = m - int(s)
    # count: the step keeps k and the chains change by 7: n2 = n + (m2^2 - m^2) + (k2 - k), with k2 - k = 0
    # for the band law n = (m - 2)^2 + 3 N + e:
    n2 = (m2 - 2) ** 2 + 3 * (len(G) - (7 if s > 0 else -7)) + (a.n - (m - 2) ** 2 - 3 * len(G))
    n2 = a.n2 or n2
    os.makedirs(a.out, exist_ok=True)
    print('n %d m %d L %.9f chains %d -> n %d m %d (%s)' % (a.n, m, L, len(G), n2, m2, a.dir), flush=True)
    if a.dir == 'up':
        for j1 in (int(x) for x in a.j0.split(',')):
            if not (8 <= j1 <= len(G) - 1):
                continue
            rows = []
            for d in (0.03, 0.04, 0.06, 0.1, 0.15):
                for cut in np.arange(-1.0, 1.01, 0.25):
                    F = step_up(Q, G, up, j1, d, float(cut))
                    rows.append((len(F) == n2, float(mlp.min_gap(F)) if len(F) == n2 else -9.0, -d, len(F), float(cut), F))
            rows.sort(key=lambda r: (r[0], r[1], r[2]), reverse=True)
            print('j1 %d: counts %s' % (j1, sorted(set(r[3] for r in rows))), flush=True)
            for r, (ok, gap, d, cnt, cut, F) in enumerate(rows[:a.top]):
                if not ok:
                    continue
                path = '%s/%d-step-up-j%d-%d.csv' % (a.out, n2, j1, r)
                fs.write_rows(path, n2, F)
                print('  %s  worst gap %+.4f  d %.2f cut %+.2f  side of the start %.6f' % (os.path.basename(path), gap, -d, cut, mlp.side(F)), flush=True)
        return
    for j0 in (int(x) for x in a.j0.split(',')):
        if not (8 <= j0 <= len(G) - 8):
            continue
        J = (Q[G[j0 - 1], :2].mean(axis=0) + Q[G[j0], :2].mean(axis=0)) / 2
        seen = {}; counts = {}
        for off in np.arange(0.0, 3.01, 0.2):
            for dx in np.arange(-a.grid, a.grid + 1e-9, a.dg):
                for dy in np.arange(-a.grid, a.grid + 1e-9, a.dg):
                    F = step(Q, G, up, j0, s, J[0] + dx, J[1] + dy, float(off))
                    counts[len(F)] = counts.get(len(F), 0) + 1
                    if len(F) != n2:
                        continue
                    key = hash(np.round(F[np.lexsort((F[:, 1], F[:, 0]))], 4).tobytes())
                    if key not in seen:
                        seen[key] = (float(mlp.min_gap(F)), float(dx), float(dy), F, float(off))
        best = sorted(seen.values(), key=lambda r: -r[0])[:a.top]
        print('j0 %d: counts %s, %d distinct starts of %d' % (j0, dict(sorted(counts.items())), len(seen), n2), flush=True)
        for r, (gap, dx, dy, F, off) in enumerate(best):
            path = '%s/%d-step-%s-j%d-%d.csv' % (a.out, n2, a.dir, j0, r)
            fs.write_rows(path, n2, F)
            print('  %s  worst gap %+.4f  cut at %+.1f,%+.1f off %.1f  side of the start %.6f (box %d + %.6f)' % (
                os.path.basename(path), gap, dx, dy, off, mlp.side(F), m2, L - m), flush=True)


if __name__ == '__main__':
    main()
