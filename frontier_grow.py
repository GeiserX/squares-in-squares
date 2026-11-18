#!/usr/bin/env python3
"""frontier: one more stack in an arm, then a soft relaxation in a larger box.

A flush stack of c tilted squares takes the room of c - 1 uprights plus the slack f, over a length
1 / cos t of the wall. So an arm that grows by one stack adds one square, and it needs
1 / cos t - 1 more wall than the row of uprights it replaces. A larger side pays for that twice: the
box is longer, and every flush stack turns upright a little, so the whole arm gets shorter.

For a held n at side L(n) this builds n + 1 squares: one arm is cut between two stacks, one period is
copied in, the far part moves one period along the wall, and the c - 1 uprights that the moved squares
overlap most are removed. The result overlaps a little. It is relaxed (the overlap energy of
methods_soft, all squares free) in a ladder of boxes from just under the held L(n + 1) upwards. The
first box that comes out overlap-free is repaired by the exact LP (methods_lp). A side below the held
L(n + 1) is a hit; the raw file goes to OUT/raw for methods_take.py.

  frontier_grow.py SUB.csv DETAILS.csv OUT [--ns a,b | --lo 500 --hi 999] [--min-step 0.004] [--part i/k]
                   [--seconds 1500]

The control is in the same table: a pair where the rule alone returns the held L(n + 1) to 1e-4 is a
packing we hold rebuilt from its neighbour. Our own code; it imports the lane's tools only.
"""
import argparse, csv, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import methods_lp as mlp
import methods_soft as ms
from engine_patch import cluster, pen_matrix
from frontier_arm import arm_of

STEPS = (-5e-4, 0.004, 0.012, 0.03, 0.06)


def fold(P):
    D = P.copy(); d = np.degrees(P[:, 2]) % 90.0
    d[d > 45] -= 90
    D[:, 2] = d
    return D


def children(P0):
    """-> [(label, squares)] with one more square than P0: one per arm that has a period"""
    D = fold(P0)
    ti = np.nonzero(np.abs(D[:, 2]) > 0.5)[0]
    if len(ti) < 12: return []
    T = D[ti]; up = np.nonzero(np.abs(D[:, 2]) <= 0.5)[0]
    out = []
    for gi, g in enumerate(sorted(cluster(T), key=len, reverse=True)[:3]):
        arm = arm_of(T[g])
        if arm is None: continue
        t, tc, v = arm; per = float(np.linalg.norm(v))
        far = ti[g][t > tc]; slab = ti[g][(t > tc - per) & (t <= tc)]
        Q = P0.copy(); Q[far, 0] += v[0]; Q[far, 1] += v[1]
        new = P0[slab].copy(); new[:, 0] += v[0]; new[:, 1] += v[1]
        M = fold(np.vstack([Q[far], new]))
        pen = pen_matrix(D[up], M).max(1)
        k = len(slab) - 1
        order = np.argsort(-pen)[:k]
        if pen[order[-1]] < 0.05: continue          # the far part does not reach c - 1 uprights: no room to trade
        keep = np.ones(len(P0), bool); keep[up[order]] = False
        out.append(('arm%d c%d' % (gi, len(slab)), np.vstack([Q[keep], new])))
    return out


def settle(X, L0, Lt):
    """-> (offset of the first overlap-free box over Lt, legal side or None, squares)"""
    for off in STEPS:
        box = Lt + off
        S = X.copy(); S[:, :2] *= box / L0
        R, E = ms.relax(S, box, 4000)
        if E > 1e-13:
            R, E = ms.relax(R, box, 4000)
        if E > 1e-13: continue
        r = ms.legal(R)
        if r is None: return off, None, None
        return off, r[1], r[0]
    return None, None, None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('sub'); ap.add_argument('details'); ap.add_argument('out')
    ap.add_argument('--ns'); ap.add_argument('--lo', type=int, default=500); ap.add_argument('--hi', type=int, default=999)
    ap.add_argument('--min-step', type=float, default=0.004); ap.add_argument('--part', default='0/1')
    ap.add_argument('--seconds', type=float, default=1500)
    a = ap.parse_args()
    os.makedirs(a.out + '/raw', exist_ok=True)
    ms.load_kernel()
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(a.details))}
    if a.ns:
        ns = [int(x) for x in a.ns.split(',')]
    else:
        ns = [n for n in range(a.lo, a.hi + 1) if n + 1 in held and held[n + 1] - held[n] >= a.min_step
              and math.isqrt(n - 1) == math.isqrt(n)]
        ns.sort(key=lambda n: held[n] - held[n + 1])
    i, k = map(int, a.part.split('/')); ns = ns[i::k]
    Ps = mlp.load(a.sub, set(ns))
    t0 = time.time(); wins = 0
    tag = a.part.replace('/', 'of')
    with open('%s/grow-%s.tsv' % (a.out, tag), 'a') as h:
        h.write('n\tto\theld_L\theld_next_L\tchild\tfree_at_offset\tlegal_L\tlegal_minus_held_next\n')
        for n in ns:
            if time.time() - t0 > a.seconds: break
            P0 = mlp.normal(Ps[n]); L0 = mlp.side(P0); Lt = held[n + 1]
            try:
                kids = children(P0)
            except Exception as e:
                h.write('%d\t%d\t%r\t%r\terror %s\t\t\t\n' % (n, n + 1, L0, Lt, e)); continue
            if not kids:
                h.write('%d\t%d\t%r\t%r\tno arm with a period\t\t\t\n' % (n, n + 1, L0, Lt)); h.flush(); continue
            for lab, X in kids:
                off, LR, R = settle(X, L0, Lt)
                h.write('%d\t%d\t%r\t%r\t%s\t%s\t%s\t%s\n' % (n, n + 1, L0, Lt, lab, '' if off is None else off,
                                                             '' if LR is None else repr(LR), '' if LR is None else '%.6f' % (LR - Lt)))
                h.flush()
                if LR is not None and LR < Lt - 1e-9:
                    wins += 1; ms.write(a.out, n + 1, R, 'grow%d' % n)
                    print('HIT n=%d from %d: %.9f -> %.9f (%s)' % (n + 1, n, Lt, LR, lab), flush=True)
    print('done part %s: %d hits, %.0fs' % (a.part, wins, time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
