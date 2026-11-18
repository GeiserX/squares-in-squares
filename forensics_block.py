#!/usr/bin/env python3
"""One rigid block of p sticks by q squares at the board's angle, locked on two grid corners, with the exact fill.

The two chains of a matched board value say more than the angle. With `pure` the chain that has no f
(4 C + 6 S = 7 for 0.7244, 7 C + 10 S = 12 for 0.7381), the first chain plus k times `pure` is

    (4 + 4k + f) C + (3 + 6k + f) S = 6 + 7k      for 0.7244:  6, 13, 20 sticks
    (4 + 7k + f) C + (3 + 10k + f) S = 6 + 12k    for 0.7381:  6, 18, 30 sticks

Read along the band this is a block of 13 (or 18) sticks side by side between a corner of the
bottom-left grid and a corner of the top-right grid, while each stick of 6 sits between a corner of the
bottom-right grid and a corner of the top-left grid. So the design is one lattice block of 13 x 6
(18 x 6) with a grid corner on each of its four sides.

This tool places that block: its long lower side through a corner (a + f, b) of the bottom-right grid,
its lower end through a corner (a', b') of the bottom-left grid, for every such pair that keeps the
block inside the square. The uprights come from the exact fill (Evan Daniel's fillfast, MIT, imported
from his clone). It prints the count of each position and writes the layouts that reach n.

Usage:
  forensics_block.py N M F T_DEG OUT [--p 13] [--q 6] [--classes natural|all] [--top 10]
"""
import sys, os, math, argparse, time
import numpy as np

sys.path.insert(0, os.environ.get('EVAND_PACKER', '$SCRATCH/bounties-squares/ext/evand/search/packer'))
import fillfast  # noqa: E402
import forensics_turn as ft  # noqa: E402

CLASSES = {'BL': (0, 0), 'BR': (1, 0), 'TL': (0, 1), 'TR': (1, 1)}     # does x (y) carry f


def block(p, q, t, P0):
    C, S = math.cos(t), math.sin(t)
    eu = np.array([S, C]); ev = np.array([-C, S])
    deg = -math.degrees(t)
    T = []
    for i in range(p):
        for j in range(q):
            c = P0 + (i + 0.5) * eu + (j + 0.5) * ev
            T.append((float(c[0]), float(c[1]), deg))
    return T


def positions(m, f, t, p, q, long_cls, end_cls, tol=1e-9):
    """Bottom corners P0 with a corner of long_cls on the lower long side and one of end_cls on the lower end."""
    C, S = math.cos(t), math.sin(t)
    eu = np.array([S, C]); ev = np.array([-C, S])
    side = m + f
    fx1, fy1 = CLASSES[long_cls]; fx2, fy2 = CLASSES[end_cls]
    out = {}
    for a in range(0, m + 1):
        for b in range(0, m + 1):
            G1 = np.array([a + fx1 * f, b + fy1 * f]); v1 = G1 @ ev; u1 = G1 @ eu
            for a2 in range(0, m + 1):
                for b2 in range(0, m + 1):
                    G2 = np.array([a2 + fx2 * f, b2 + fy2 * f]); u2 = G2 @ eu; v2 = G2 @ ev
                    if not (-tol <= u1 - u2 <= p + tol and -tol <= v2 - v1 <= q + tol):
                        continue
                    P0 = u2 * eu + v1 * ev
                    cs = [P0, P0 + p * eu, P0 + q * ev, P0 + p * eu + q * ev]
                    if min(c.min() for c in cs) < -tol or max(c.max() for c in cs) > side + tol:
                        continue
                    out[(round(P0[0], 9), round(P0[1], 9))] = (P0, (a, b), (a2, b2))
    return list(out.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n', type=int); ap.add_argument('m', type=int); ap.add_argument('f', type=float)
    ap.add_argument('t_deg', type=float); ap.add_argument('out')
    ap.add_argument('--p', default='13'); ap.add_argument('--q', type=int, default=6)
    ap.add_argument('--classes', default='natural'); ap.add_argument('--top', type=int, default=10)
    ap.add_argument('--secs', type=float, default=120)
    a = ap.parse_args()
    t = math.radians(a.t_deg); side = a.m + a.f
    pairs = [('BR', 'BL')] if a.classes == 'natural' else [(x, y) for x in CLASSES for y in CLASSES]
    t0 = time.time()
    for p in (int(v) for v in a.p.split(',')):
        res = []
        for lc, ec in pairs:
            for P0, g1, g2 in positions(a.m, a.f, t, p, a.q, lc, ec):
                if time.time() - t0 > a.secs:
                    break
                T = block(p, a.q, t, P0)
                X = fillfast.fill(side, np.array(T, float).reshape(-1, 3), mode='exact', time_limit=5)
                res.append((len(X), lc, ec, g1, g2, P0, X))
        res.sort(key=lambda r: -r[0])
        print('n %d side %.12f t %.6f block %d x %d: %d positions, plain grid %d, need %d, %.0fs' % (
            a.n, side, a.t_deg, p, a.q, len(res), a.m * a.m, a.n, time.time() - t0), flush=True)
        for c, lc, ec, g1, g2, P0, X in res[:a.top]:
            print('   count %d (%+d)  long side on %s%s, end on %s%s, bottom corner (%.6f, %.6f)' % (
                c, c - a.m * a.m, lc, g1, ec, g2, P0[0], P0[1]), flush=True)
        k = 0
        for c, lc, ec, g1, g2, P0, X in res:
            if c < a.n or k >= 3:
                break
            os.makedirs(a.out, exist_ok=True)
            tilt = [r for r in X if abs(r[2]) > 1e-6]; upr = [r for r in X if abs(r[2]) <= 1e-6]
            path = '%s/%d-block%dx%d-%d.csv' % (a.out, a.n, p, a.q, k)
            ft.write_rows(path, a.n, np.array(tilt + upr[:a.n - len(tilt)]))
            print('wrote', path, flush=True); k += 1


if __name__ == '__main__':
    main()
