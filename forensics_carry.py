#!/usr/bin/env python3
"""The rows of the held arm carried to another width, with one plain fq quench.

The arm of the held 685 has 13 rows: 5, 7, 7, five rows of 8, a row of 9, three rows of 8 and 5 (forensics_arm.py ctl).
The lattice builders of forensics_arm.py do not find these rows. This tool reads them from the held layout and writes
them again by rule for a part of width C + f:

  - each held row keeps its left end and gets C - 9 squares more, as a straight row at the flush tilt of rows of C - 1
  - the heights of the rows scale with the pitch
  - nL rows stand in the lower run and nU rows in the upper run, with the row of C between them
  - the upright squares of the zone are stacked column by column from the floor. A column is counted from the left
    edge of the zone or from the right wall. An upright may enter a tilted square by a small depth, and fq moves it out
  - the part stands alone at the right wall of a square of side C + 7 + F, with 7 plain columns left of it
  - one plain fq quench (no polish flags: with them these starts end far above)

It prints the side each (nL, nU) ends at, and writes a csv when the side is at or below C + 7 + F.

Control (2026-11-12, round 19): C = 9 ends at 16.656407 for (5, 3), at 16.657125 for (3, 5) and at 16.663618 for
(6, 2), where 16.684144 is enough. So 260 comes back at m = 16 from rows by rule. The rows are read from the held arm,
so the control says that straight rows, stacked uprights and one quench are enough. It does not say that the rule for
another width is right. That is what a run at another C measures.

Usage: forensics_carry.py HELD.csv C [C ...] [--fq PATH] [--out DIR]
"""
import sys, os, math
import numpy as np

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
import forensics_turn as ft
import forensics_arm as fa

F = 0.6841436063588683


def depth(u, T, PT):
    """How deep the upright unit square at u enters the tilted squares T (0 when it enters none)."""
    worst = 0.0
    near = np.nonzero(np.hypot(T[:, 0] - u[0], T[:, 1] - u[1]) < 1.4143)[0]
    cu = np.array([[u[0] - .5, u[1] - .5], [u[0] + .5, u[1] - .5], [u[0] + .5, u[1] + .5], [u[0] - .5, u[1] + .5]])
    for j in near:
        d = np.inf
        for ang in (0.0, 90.0, T[j, 2], T[j, 2] + 90):
            a = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))]); pa = cu @ a; pb = PT[j] @ a
            d = min(d, min(pa.max(), pb.max()) - max(pa.min(), pb.min()))
            if d <= 0: break
        worst = max(worst, d)
    return worst


def stack_fill(T, X0, side, delta, step=0.02):
    """Uprights stacked in each column from the floor, a column at a time from both sides of the zone. An upright may
    enter a tilted square by delta at most and may not enter another upright."""
    PT = fa.corners(T); c = int(round(side - X0 - F)); out = []; cols = []
    for j in range(c): cols += [X0 + 0.5 + j, side - 0.5 - j]
    for x in cols:
        y = 0.5
        while y <= side - 0.5 + 1e-9:
            if all(abs(x - a) >= 1 - 1e-6 or abs(y - b) >= 1 - 1e-6 for a, b in out) and depth((x, y), T, PT) <= delta:
                out.append((x, y)); y += 1.0
            else: y += step
    return [(x, y, 0.0) for x, y in out]


def held_rows(held):
    """The 13 rows of the arm of the held 685: (squares, left end in the zone, height of the first centre of the straight row)."""
    s, A = ft.normalize(ft.load(held, 685)); T0 = A[np.abs(A[:, 2]) > 0.5]
    inpod = (T0[:, 1] > 16.5) & (T0[:, 0] < 18); arm = T0[~inpod].copy(); arm[:, 0] -= 17.0
    tm = math.radians(24.9); vv = arm[:, 0] * math.sin(tm) + arm[:, 1] * math.cos(tm); o = np.argsort(vv); rows = [[o[0]]]
    for a, b in zip(o[:-1], o[1:]):
        if vv[b] - vv[a] > 0.45: rows.append([])
        rows[-1].append(b)
    t9, W9 = fa.tilt(8, F); c9, s9 = math.cos(t9), math.sin(t9); h9 = 0.5 * (c9 + s9)
    H = []
    for r in rows:
        n = len(r); cx, cy = arm[r, 0].mean(), arm[r, 1].mean()
        H.append((n, cx - (n - 1) / 2 * c9 - h9, cy + (n - 1) / 2 * s9))
    return H


def carry(H, c, nL, nU):
    """Tilted squares of B(c) in the zone frame, the height of their top corner, and the row counts."""
    t9, W9 = fa.tilt(8, F); c9 = math.cos(t9); p9 = 1 / c9
    dc = c - 9; cs = c - 1; t, W = fa.tilt(cs, F); ct, st = math.cos(t), math.sin(t); h = 0.5 * (ct + st); p = 1 / ct; sg = p / p9
    idx = [0, 1, 2] + [3 + min(k, 4) for k in range(nL)] + [8] + [9 + min(k, 1) for k in range(max(nU - 1, 0))] + ([11] if nU >= 1 else []) + [12]
    ys = [0.726 + h + (H[0][0] + dc - 1) * st]             # the lowest corner of the first row stands 0.726 over the floor, as held
    for pos in range(1, len(idx)):
        i0, i1 = idx[pos - 1], idx[pos]
        ys.append(ys[-1] + (p if i1 == i0 else (H[i1][2] - H[i1 - 1][2]) * sg))
    sq = []; top = 0.0; counts = []
    for i, yf in zip(idx, ys):
        n, xl, _ = H[i]; xl = (2 + (xl - 2) * ct / c9) if xl > 2.5 else xl
        sq += [(xl + h + k * ct, yf - k * st, -math.degrees(t)) for k in range(n + dc)]; top = max(top, yf + h); counts.append(n + dc)
    return np.array(sq), top, counts


def main():
    a = sys.argv[1:]
    fq = os.path.expanduser('$SCRATCH/squares-base/fq'); out = '.'
    if '--fq' in a: i = a.index('--fq'); fq = a[i + 1]; a = a[:i] + a[i + 2:]
    if '--out' in a: i = a.index('--out'); out = a[i + 1]; a = a[:i] + a[i + 2:]
    if len(a) < 2: print(__doc__); return 2
    H = held_rows(a[0]); os.makedirs(out, exist_ok=True)
    print('held rows (squares, left end, height of the first centre):', [(n, round(float(x), 3), round(float(y), 3)) for n, x, y in H], flush=True)
    for c in [int(v) for v in a[1:]]:
        mp = c + 7; side = mp + F + 2e-9; X0 = side - (c + F); want = mp * mp + c // 2; best = None
        print('B(%d): alone at m = %d, want %d = %d^2 + %d at side %.9f' % (c, mp, want, mp, c // 2, side), flush=True)
        grid = [(i + 0.5, j + 0.5, 0.0) for i in range(7) for j in range(mp)]
        for nL in range(1, 16):
            for nU in range(1, 16):
                T, top, counts = carry(H, c, nL, nU); slack = side - top
                if slack < 0.1 or slack > 1.25: continue
                T = T.copy(); T[:, 0] += X0; need = want - len(grid) - len(T)
                for delta in (0.0, 0.03, 0.06, 0.1, 0.15, 0.2, 0.3):
                    U = stack_fill(T, X0, side, delta)
                    if len(U) >= need: break
                if len(U) > need:                              # too many: the ones that enter a tilted square deepest go out
                    PT = fa.corners(T); U = sorted(U, key=lambda u: depth(u, T, PT))[:need]
                msg = 'nL %d nU %d: rows %s, top slack %.3f, uprights %d of %d at depth %.2f' % (nL, nU, counts, slack, len(U), need, delta)
                if len(U) < need - 2: print('  ' + msg + ': short', flush=True); continue
                X = np.vstack([np.array(grid), T, np.array(U).reshape(-1, 3)])
                n = len(X); s1, Q = ft.quench(fq, side, X, [], timeout=200)
                ok = n == want and s1 is not None and s1 <= side + 1e-9
                print('  %s, %d squares, plain fq ends %s (%s)%s' % (msg, n, 'None' if s1 is None else '%.6f' % s1, 'None' if s1 is None else '%+.4f' % (s1 - side), '  REACHED' if ok else ''), flush=True)
                if n == want and s1 is not None and (best is None or s1 < best[0]):
                    best = (s1, nL, nU)
                    if ok: ft.write_rows('%s/carry-c%d-n%d.csv' % (out, c, want), want, Q)
        print('B(%d) best: %s, target %.9f' % (c, best, side), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
