#!/usr/bin/env python3
"""Turn the tilted squares of a held layout step by step with their angles fixed, and solve the rest by LP.

With every angle fixed, two squares stay apart when one of their four edge normals separates them, and
that is linear in the centres. So for a given set of angles the smallest side is a sequence of small LPs
(the separating normal of each close pair is picked again after each LP).

  curve   the side the held contact graph reaches at each angle between the held one and the board's one.
          It answers one question: can our layout follow the chain curve f(t) of forensics_curve.py,
          or does a contact stop it.
  drop    hold the side on the chain curve instead, let uprights overlap at a price, drop the uprights
          that still overlap, and at the end fill the uprights again exactly (Evan Daniel's fillfast,
          MIT, imported from his clone). The count says how many squares the turned band holds.

Usage:
  forensics_lp.py curve HELD.csv N BOARD_F BOARD_DEG [--steps 20]
  forensics_lp.py drop  HELD.csv N BOARD_F BOARD_DEG OUT [--steps 20]
"""
import sys, os, math, argparse
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree

import forensics_turn as ft


def axes_of(deg):
    t = np.radians(deg)
    return np.stack([np.c_[np.cos(t), np.sin(t)], np.c_[-np.sin(t), np.cos(t)]], axis=1)   # (n, 2, 2)


def half(E, k, ax):
    return (abs(ax @ E[k, 0]) + abs(ax @ E[k, 1])) / 2


def lp_step(X, deg, s, trust, fix_side=None, soft=None, keep=None):
    """One LP. fix_side None: minimise the side. Else the side is fixed and the overlap of the pairs that
    hold a square of `soft` is paid for; returns the slack per square."""
    n = len(X); E = axes_of(deg)
    idx = np.arange(n) if keep is None else np.array(sorted(keep))
    pos = {int(k): c for c, k in enumerate(idx)}
    tree = cKDTree(X[idx])
    pairs = tree.query_pairs(1.4143 + 2 * trust + 1e-6)
    nv = 2 * len(idx) + 1
    rows, cols, vals, rhs = [], [], [], []
    slack_of = []
    r = 0
    nslack = 0
    for a, b in pairs:
        i, j = int(idx[a]), int(idx[b])
        best = None
        for k in (i, j):
            for ax in E[k]:
                d = ax @ (X[j] - X[i])
                need = half(E, i, ax) + half(E, j, ax)
                gap = abs(d) - need
                if best is None or gap > best[0]:
                    best = (gap, ax if d >= 0 else -ax, need)
        gap, ax, need = best
        if gap > 2 * trust + 1e-9:
            continue
        # ax.(pj - pi) >= need  ->  ax.pi - ax.pj <= -need
        rows += [r] * 4; cols += [2 * a, 2 * a + 1, 2 * b, 2 * b + 1]; vals += [ax[0], ax[1], -ax[0], -ax[1]]
        if soft is not None and (i in soft or j in soft):
            slack_of.append((r, i if i in soft else j, j if (i in soft and j in soft) else None))
            nslack += 1
        rhs.append(-need); r += 1
    hx = np.array([(abs(E[k, 0, 0]) + abs(E[k, 1, 0])) / 2 for k in idx])
    hy = np.array([(abs(E[k, 0, 1]) + abs(E[k, 1, 1])) / 2 for k in idx])
    ns = len(slack_of)
    for c, (rr, _, _) in enumerate(slack_of):
        rows.append(rr); cols.append(nv + c); vals.append(-1.0)
    for a in range(len(idx)):                     # x + h <= s, y + h <= s
        for d, h in ((0, hx[a]), (1, hy[a])):
            rows += [r, r]; cols += [2 * a + d, nv - 1]; vals += [1.0, -1.0]; rhs.append(-h); r += 1
    A = coo_matrix((vals, (rows, cols)), shape=(r, nv + ns)).tocsr()
    lo = np.r_[np.repeat(X[idx], 1, axis=0).ravel() - trust, [0.0], np.zeros(ns)]
    hi = np.r_[X[idx].ravel() + trust, [np.inf], np.full(ns, np.inf)]
    lo[:2 * len(idx):2] = np.maximum(lo[:2 * len(idx):2], hx); lo[1:2 * len(idx):2] = np.maximum(lo[1:2 * len(idx):2], hy)
    cost = np.zeros(nv + ns)
    if fix_side is None:
        cost[nv - 1] = 1.0
    else:
        lo[nv - 1] = hi[nv - 1] = fix_side
        cost[nv:] = 1.0
    res = linprog(cost, A_ub=A, b_ub=np.array(rhs), bounds=np.c_[lo, hi], method='highs')
    if res.status != 0:
        return None, None, None
    Y = X.copy(); Y[idx] = res.x[:2 * len(idx)].reshape(-1, 2)
    sl = {}
    for c, (_, k, k2) in enumerate(slack_of):
        v = res.x[nv + c]
        if v > 1e-9:
            sl[k] = sl.get(k, 0.0) + v
            if k2 is not None:
                sl[k2] = sl.get(k2, 0.0) + v
    return Y, float(res.x[nv - 1]), sl


def settle(X, deg, s, trust=0.03, iters=12, keep=None):
    for _ in range(iters):
        Y, s2, _ = lp_step(X, deg, s, trust, keep=keep)
        if Y is None:
            return None, None
        done = abs(s2 - s) < 1e-12 and np.abs(Y - X).max() < 1e-10
        X, s = Y, s2
        if done:
            break
    return X, s


def chain_f(deg_t, i=4, j=3, q=6):
    t = math.radians(deg_t); C, S = math.cos(t), math.sin(t)
    return (q - i * C - j * S) / (C + S)


def angles_at(deg0, lam, held_dev, board_dev):
    """Scale each tilted square's distance from 45 degrees from the held value toward the board's."""
    out = deg0.copy()
    for k, d in enumerate(deg0):
        if abs(d) < 1e-6:
            continue
        dev = 45 - abs(d)
        new = dev * (1 + lam * (board_dev / held_dev - 1))
        out[k] = math.copysign(45 - new, d)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd'); ap.add_argument('held'); ap.add_argument('n', type=int); ap.add_argument('fb', type=float)
    ap.add_argument('board_deg', type=float); ap.add_argument('out', nargs='?', default='lpout')
    ap.add_argument('--steps', type=int, default=20); ap.add_argument('--chain', default='4,3,6')
    a = ap.parse_args()
    ci, cj, cq = (int(v) for v in a.chain.split(','))
    s, A = ft.normalize(ft.load(a.held, a.n)); m = int(s)
    import forensics_curve as fc
    t, cnt, nt = fc.main_angle([(x, y, math.radians(d)) for x, y, d in A])
    held_deg = math.degrees(t)
    held_dev, board_dev = 45 - held_deg, 45 - a.board_deg
    X = A[:, :2].copy(); deg0 = A[:, 2].copy()
    X, s1 = settle(X, deg0, s)
    print('n', a.n, 'held side %.10f, LP at the held angles %.10f' % (s, s1), flush=True)
    if a.cmd == 'curve':
        for st in range(1, a.steps + 1):
            lam = st / a.steps
            deg = angles_at(deg0, lam, held_dev, board_dev)
            td = held_deg + lam * (a.board_deg - held_deg)
            X2, s2 = settle(X, deg, s1 + 0.01)
            if X2 is None:
                print('step %d angle %.4f: LP infeasible' % (st, td)); break
            X, s1 = X2, s2
            print('step %2d angle %.4f  LP side %.9f  chain side %.9f  LP - chain %+.2e  LP - held %+.2e' % (
                st, td, s1, m + chain_f(td, ci, cj, cq), s1 - m - chain_f(td, ci, cj, cq), s1 - s), flush=True)
        return
    # drop: side on the chain curve, uprights may overlap at a price
    up = set(int(k) for k in np.nonzero(np.abs(deg0) < 1e-6)[0])
    keep = set(range(len(A)))
    dropped = []
    for st in range(1, a.steps + 1):
        lam = st / a.steps
        deg = angles_at(deg0, lam, held_dev, board_dev)
        td = held_deg + lam * (a.board_deg - held_deg)
        side = m + chain_f(td, ci, cj, cq) + 1e-9
        for _ in range(40):
            Y, _, sl = lp_step(X, deg, side, 0.03, fix_side=side, soft=up & keep, keep=keep)
            if Y is None:
                print('step %d: infeasible even with soft uprights' % st); return
            moved = np.abs(Y - X).max()
            X = Y
            if sl and moved < 1e-9:
                worst = max(sl, key=sl.get)
                keep.discard(worst); dropped.append(worst)
            elif not sl and moved < 1e-9:
                break
        print('step %2d angle %.4f side %.9f  kept %d of %d (dropped %d)' % (st, td, side, len(keep), len(A), len(dropped)), flush=True)
    sys.path.insert(0, os.environ.get('EVAND_PACKER', '$SCRATCH/bounties-squares/ext/evand/search/packer'))
    import fillfast
    side = m + a.fb + 1e-9
    deg = angles_at(deg0, 1.0, held_dev, board_dev)
    T = np.array([[X[k, 0], X[k, 1], deg[k]] for k in sorted(keep) if k not in up])
    F = fillfast.fill(side, T, mode='exact')
    print('n', a.n, 'at the board side %.9f: tilted %d, exact fill %d, need %d' % (side, len(T), len(F), a.n), flush=True)
    if len(F) >= a.n:
        os.makedirs(a.out, exist_ok=True)
        ft.write_rows('%s/%d-lp.csv' % (a.out, a.n), a.n, F[:a.n] if len(F) == a.n else np.r_[F[:len(T)], F[len(T):][:a.n - len(T)]])
        print('wrote', '%s/%d-lp.csv' % (a.out, a.n))


if __name__ == '__main__':
    main()
