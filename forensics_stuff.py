#!/usr/bin/env python3
"""Take a stick band at the board's side that is a few squares short, add the missing squares, and quench.

forensics_sticks.py builds bands at the board's side and angle that hold n - 3 squares or so. This tool
puts the missing squares as uprights in the emptiest places of such a layout (they overlap there) and
lets the fq quench settle the whole layout with the side free. The band is then not the held one, so
the quench does not start in the held basin. A result counts when the side ends below the held side.

Usage: forensics_stuff.py N M F DELTA_DEG DIAG HELD_SIDE OUT --runs=RUNS [--chain 4,3,6] [--fq PATH] [--seeds 3]
RUNS is 'turn,u0,p,split,du;turn,u0,p,split,du' as forensics_sticks.py prints them.
"""
import sys, os, math, argparse
import numpy as np

import forensics_turn as ft
import forensics_sticks as fs


def emptiest(X, side, k, step=0.05):
    """k centres for extra uprights, each as far as possible from the squares already there."""
    P = [tuple(r[:2]) for r in X]
    g = np.arange(0.5, side - 0.5 + 1e-9, step)
    gx, gy = np.meshgrid(g, g)
    G = np.c_[gx.ravel(), gy.ravel()]
    out = []
    for _ in range(k):
        A = np.array(P)
        d = np.full(len(G), np.inf)
        for a in range(0, len(A), 64):
            dd = np.abs(G[:, None, :] - A[None, a:a + 64, :]).max(axis=2)       # Chebyshev: uprights
            d = np.minimum(d, dd.min(axis=1))
        b = int(np.argmax(d))
        out.append((float(G[b, 0]), float(G[b, 1]), float(d[b])))
        P.append((float(G[b, 0]), float(G[b, 1])))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n', type=int); ap.add_argument('m', type=int); ap.add_argument('f', type=float)
    ap.add_argument('delta', type=float); ap.add_argument('diag', type=int); ap.add_argument('--runs', required=True)
    ap.add_argument('held_side', type=float); ap.add_argument('out')
    ap.add_argument('--chain', default='4,3,6'); ap.add_argument('--fq', default=os.path.expanduser('$SCRATCH/squares-base/fq'))
    ap.add_argument('--seeds', type=int, default=3); ap.add_argument('--jit', type=float, default=0.004)
    a = ap.parse_args()
    chain = tuple(int(v) for v in a.chain.split(','))
    runs = []
    for part in a.runs.split(';'):
        t, u0, p, split, du = part.split(',')
        runs.append(dict(turn=int(t), u0=float(u0), p=int(p), split=int(split), du=float(du)))
    ch = fs.Channel(a.m, a.f, a.diag, *chain)
    cnt, X, mis = fs.count(ch, runs, a.delta)
    side = a.m + a.f
    print('n %d side %.10f: the band holds %d, need %d' % (a.n, side, cnt, a.n), flush=True)
    if cnt < 0 or cnt >= a.n:
        return
    add = emptiest(X, side, a.n - cnt)
    print('   added uprights at', [(round(x, 2), round(y, 2), 'room %.2f' % d) for x, y, d in add], flush=True)
    Y = np.array([tuple(r[:3]) for r in X] + [(x, y, 0.0) for x, y, _ in add], float)
    for seed in range(a.seeds):
        for polish in (False, True):
            Z = Y.copy()
            if seed:
                rng = np.random.default_rng(seed)
                Z[:, :2] += rng.normal(0, a.jit, (len(Z), 2))
            s2, Q = ft.quench(a.fq, side, Z, ft.POLISH if polish else [], timeout=400)
            if s2 is None:
                print('   seed %d polish %d: quench failed' % (seed, polish), flush=True); continue
            print('   seed %d polish %d: side %.10f  (%+.2e to held, %+.2e to the board)' % (seed, polish, s2, s2 - a.held_side, s2 - side), flush=True)
            if s2 < a.held_side - 1e-9:
                os.makedirs(a.out, exist_ok=True)
                path = '%s/%d-stuff-s%d%s.csv' % (a.out, a.n, seed, 'p' if polish else '')
                ft.write_rows(path, a.n, Q)
                print('   wrote', path, flush=True)


if __name__ == '__main__':
    main()
