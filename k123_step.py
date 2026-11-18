#!/usr/bin/env python3
"""Cut rows and chains from a band, keeping both ends (avenues/k123.md, round 22).

Unlike the diagonal join, this cut permits a shift across the band. Upright
squares are assigned to the top-left or bottom-right lattice by their grid
phase. A cut removes s rows, s columns and c chains from the middle. The far
end moves by (-s, -s). Scan the two cut lines and their offset, then quench.

Control: 680 with s=5 and c=7 must rebuild 444 at 21.564693168 after fq.
This also tests the lattice classification against k123_step57.py.
"""
import argparse
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import family_step as fs
import k123_join as kj
import methods_lp as mlp


def cut(X, j0, s, c, xc, yc, off):
    U = X.Q[X.up]
    # The top-left lattice has x = integer + 0.5. The bottom-right one has
    # x = L - integer - 0.5. Pick the nearer phase, including float slack.
    phase = U[:, 0] - 0.5
    eleft = abs(phase - np.rint(phase))
    phase = X.L - U[:, 0] - 0.5
    eright = abs(phase - np.rint(phase))
    side = eleft < eright
    parts = []
    for above, V, x0, y0 in ((True, U[side], xc - off, yc + off),
                               (False, U[~side], xc + off, yc - off)):
        x, y = V[:, 0], V[:, 1]
        parts.append(V[(x < x0) & (y < y0)])
        B = V[(x > x0 + s) & (y > y0 + s)].copy()
        B[:, :2] -= s
        parts.append(B)
        if above:
            B = V[(x < x0) & (y > y0 + s)].copy()
            B[:, 1] -= s
        else:
            B = V[(x > x0 + s) & (y < y0)].copy()
            B[:, 0] -= s
        parts.append(B)
    parts.extend(X.Q[g] for g in X.G[:j0])
    for g in X.G[j0 + c:]:
        B = X.Q[g].copy()
        B[:, :2] -= s
        parts.append(B)
    return np.vstack(parts)


def insert(X, j1, rows, chains, d, cut):
    sh = rows + d
    seam = (X.c[j1-1].sum() + X.c[j1-chains].sum() + 2*sh)/2 + cut
    parts = [X.Q[g] for g in X.G[:j1]]
    for g in X.G[j1-chains:]:
        B = X.Q[g].copy()
        B[:, :2] += sh
        parts.append(B)
    U = X.Q[X.up]
    sm = U[:, 0] + U[:, 1]
    parts.append(U[sm < seam])
    B = U[sm + 2*rows >= seam].copy()
    B[:, :2] += sh
    parts.append(B)
    B = U[(U[:, 0] > X.L-rows) & (U[:, 1] < rows)].copy()
    B[:, 0] += sh
    parts.append(B)
    B = U[(U[:, 0] < rows) & (U[:, 1] > X.L-rows)].copy()
    B[:, 1] += sh
    parts.append(B)
    return np.vstack(parts)


def up_scan(a, X):
    best = []
    counts = set()
    js = [int(j) for j in a.j0.split(',')] if a.j0 else range(max(4, a.chains+1), len(X.G)-3)
    for j1 in js:
        local = []
        for d in (.01, .03, .04, .06, .1, .15, .2, .3):
            for cutline in np.arange(-3, 3.01, .25):
                F = insert(X, j1, a.rows, a.chains, d, float(cutline))
                counts.add(len(F))
                if len(F) != a.target:
                    continue
                gap = float(mlp.min_gap(F))
                local.append((gap, mlp.side(F), j1, d, float(cutline), F))
        local.sort(key=lambda r: (-round(r[0], 8), r[1]))
        selected = []
        used = set()
        for r in local:
            if r[3] in used:
                continue
            used.add(r[3])
            selected.append(r)
            if len(selected) == 2:
                break
        best.extend(selected)
        print('up j1', j1, 'counts', sorted(counts), 'matches', len(local),
              'gap', local[0][0] if local else None, flush=True)
    best.sort(key=lambda r: (-round(r[0], 8), r[1]))
    os.makedirs(a.out, exist_ok=True)
    for i, (gap, side, j1, d, cutline, F) in enumerate(best[:a.top]):
        path = f'{a.out}/{a.target}-step-{a.n}-up-s{a.rows}c{a.chains}-j{j1}-r{i}.csv'
        fs.write_rows(path, a.target, F)
        print('WRITE', path, 'gap', gap, 'side', side, 'd', d,
              'cut', cutline, flush=True)
    print('END up counts', sorted(counts), 'starts', min(len(best), a.top), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cur')
    ap.add_argument('n', type=int)
    ap.add_argument('out')
    ap.add_argument('--rows', type=int, default=1)
    ap.add_argument('--up', action='store_true', help='insert rows and chains instead of cutting')
    ap.add_argument('--chains', type=int, default=1)
    ap.add_argument('--target', type=int, required=True)
    ap.add_argument('--top', type=int, default=8)
    ap.add_argument('--j0', default='')
    ap.add_argument('--grid', type=float, default=.6)
    ap.add_argument('--dg', type=float, default=.2)
    a = ap.parse_args()
    Q, L = kj.norm(mlp.load(a.cur, {a.n})[a.n])
    X = kj.Lay(a.n, Q, L, str(a.n))
    if a.up:
        up_scan(a, X)
        return
    js = [int(j) for j in a.j0.split(',')] if a.j0 else range(4, len(X.G)-a.chains-4)
    best = []
    seen = set()
    counts = set()
    matched = 0
    os.makedirs(a.out, exist_ok=True)
    for j0 in js:
        J = (X.c[j0-1] + X.c[j0]) / 2
        local = []
        for off in np.arange(0, 5.01, .25):
            for dx in np.arange(-a.grid, a.grid+1e-9, a.dg):
                for dy in np.arange(-a.grid, a.grid+1e-9, a.dg):
                    F = cut(X, j0, a.rows, a.chains, J[0]+dx, J[1]+dy, off)
                    counts.add(len(F))
                    if len(F) != a.target:
                        continue
                    matched += 1
                    key = np.round(F[np.lexsort((F[:, 1], F[:, 0]))], 5).tobytes()
                    if key in seen:
                        continue
                    seen.add(key)
                    gap = float(mlp.min_gap(F))
                    local.append((gap, j0, float(dx), float(dy), float(off), F))
        local.sort(key=lambda r: -r[0])
        best.extend(local[:2])
        print('j0', j0, 'counts', sorted(counts), 'distinct', len(seen),
              'gap', local[0][0] if local else None, flush=True)
    best.sort(key=lambda r: -r[0])
    for i, (gap, j0, dx, dy, off, F) in enumerate(best[:a.top]):
        tag = f'{a.n}-s{a.rows}c{a.chains}-j{j0}-r{i}'
        path = f'{a.out}/{a.target}-step-{tag}.csv'
        fs.write_rows(path, a.target, F)
        print('WRITE', path, 'gap', gap, 'side', mlp.side(F),
              'cut', dx, dy, off, flush=True)
    print('END', 'matches', matched, 'distinct', len(seen), 'counts', sorted(counts), flush=True)


if __name__ == '__main__':
    main()
