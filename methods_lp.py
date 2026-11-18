#!/usr/bin/env python3
"""Contact LP "reclose": an exact local optimiser for one packing.

The public teams end every search with a fixed-angle contact LP (HiGHS): the
angles are frozen, every near pair keeps the separating axis it has now, and a
linear programme moves all centres at once to the smallest box. With frozen
angles the pair and wall constraints are exactly linear, so the LP result is a
valid packing, not an approximation.

This file is our own version, and it goes one step further than the fixed-angle
LP: a sequential LP that also turns the squares.

  step A  LP over (dx, dy, dtheta) of every square with the gap of each pair
          linearised in the angles, inside a trust region. Where a square is
          within the trust radius of parallel to a wall or to its neighbour
          (the V-shaped kink of |cos|+|sin|), both branches are written as rows,
          so the model never predicts a gain from crossing the kink.
  step B  fixed-angle LP at the new angles: exact, restores every gap.
  accept  if the true side fell, else shrink the angle trust radius.

Only numpy and scipy are needed, so it runs on any box. It writes plain float
rows; certification (floatsafe at 2.2e-11, the official metric, the held score)
is methods_take.py.

Usage:
  methods_lp.py SUB.csv OUTDIR [--ns 498,544 | --all | --nmin 100] [--jobs 2]
                [--iters 60] [--fixed] [--inflate E]
  --fixed    fixed-angle LP only (the public method), for the comparison
  --inflate  positive control: scale the centres by 1+E first (a looser start)
Output: OUTDIR/raw/<n>.csv (n,square_id,x,y,angle) when the side fell by more
than 1e-11, and OUTDIR/lp.tsv (n, L0, L1, gain of score, iterations, seconds).
"""
import argparse, csv, math, os, sys, time
from collections import defaultdict
from multiprocessing import Pool

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree

GAP = 4e-11          # gap asked of every pair in the LP (floatsafe needs 2.2e-11)
HALF_PI = math.pi / 2


def load(path, want=None):
    pz = defaultdict(list)
    with open(path, newline='') as h:
        for r in csv.DictReader(h):
            n = int(r['n'])
            if want is None or n in want:
                pz[n].append((int(r['square_id']), float(r['x']), float(r['y']), float(r['angle'])))
    return {n: np.array([v[1:] for v in sorted(rows)]) for n, rows in pz.items()}


def half(th):
    return 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))


def side(P):
    h = half(P[:, 2])
    return max((P[:, 0] + h).max() - (P[:, 0] - h).min(), (P[:, 1] + h).max() - (P[:, 1] - h).min())


def pair_list(P, reach):
    return cKDTree(P[:, :2]).query_pairs(reach, output_type='ndarray')


def best_axes(P, pairs):
    """For every pair the separating axis with the largest gap.

    Returns gap, a (the square that owns the axis), b (the other one), phi (axis
    angle, pointing from a to b)."""
    i, j = pairs[:, 0], pairs[:, 1]
    best = np.full(len(i), -np.inf)
    A = np.zeros(len(i), int); B = np.zeros(len(i), int); PHI = np.zeros(len(i))
    for a, b in ((i, j), (j, i)):
        dx, dy = P[b, 0] - P[a, 0], P[b, 1] - P[a, 1]
        for k in range(4):
            phi = P[a, 2] + k * HALF_PI
            proj = np.cos(phi) * dx + np.sin(phi) * dy
            psi = P[b, 2] - phi
            g = proj - 0.5 - 0.5 * (np.abs(np.cos(psi)) + np.abs(np.sin(psi)))
            m = g > best
            best[m] = g[m]; A[m] = a[m]; B[m] = b[m]; PHI[m] = phi[m]
    return best, A, B, PHI


def min_gap(P):
    pairs = pair_list(P, math.sqrt(2) + 1e-6)
    if not len(pairs):
        return math.inf
    return float(best_axes(P, pairs)[0].min())


def _signs(v, tol):
    """Sign choices of a term: its own sign, or both when it is within tol of zero."""
    s = np.where(v >= 0, 1.0, -1.0)
    near = np.abs(v) < tol
    return s, near


def solve(P, tr_c, tr_a, reach=math.sqrt(2) + 0.25):
    """One LP. tr_a = 0 freezes the angles (exact). Returns the new P or None."""
    n = len(P)
    free = tr_a > 0
    nv = (3 if free else 2) * n + 3           # dx, dy, [dth], lox, loy, L
    ix, iy = np.arange(n), n + np.arange(n)
    it = 2 * n + np.arange(n) if free else None
    ilx, ily, iL = nv - 3, nv - 2, nv - 1
    rows, cols, vals, rhs = [], [], [], []
    nr = 0

    def add(k, entries, b):
        """k rows 'sum(entries) >= b', stored as -sum <= -b."""
        nonlocal nr
        r = nr + np.arange(k)
        for c, v in entries:
            rows.append(r); cols.append(np.broadcast_to(c, (k,))); vals.append(-np.broadcast_to(v, (k,)).astype(float))
        rhs.append(-np.broadcast_to(b, (k,)).astype(float)); nr += k

    # pairs
    pairs = pair_list(P, reach)
    g, A, B, PHI = best_axes(P, pairs)
    ux, uy = np.cos(PHI), np.sin(PHI)
    dx, dy = P[B, 0] - P[A, 0], P[B, 1] - P[A, 1]
    psi = P[B, 2] - PHI
    cp, sp = np.cos(psi), np.sin(psi)
    kt = 2.5 * tr_a
    sc, nc = _signs(cp, kt); ss, ns_ = _signs(sp, kt)
    for fc, fs in ((1, 1), (-1, 1), (1, -1)):   # own signs; cos flipped; sin flipped
        if fc < 0:
            sel = nc
        elif fs < 0:
            sel = ns_
        else:
            sel = np.ones(len(g), bool)
        if not free and (fc < 0 or fs < 0):
            continue
        if not sel.any():
            continue
        a, b = A[sel], B[sel]
        c_, s_ = sc[sel] * fc, ss[sel] * fs
        # gap = u.(cb-ca) - 0.5 - 0.5*(c_*cos(psi) + s_*sin(psi))
        g0 = (ux[sel] * dx[sel] + uy[sel] * dy[sel]) - 0.5 - 0.5 * (c_ * cp[sel] + s_ * sp[sel])
        ent = [(ix[b], ux[sel]), (iy[b], uy[sel]), (ix[a], -ux[sel]), (iy[a], -uy[sel])]
        if free:
            dh = 0.5 * (-c_ * sp[sel] + s_ * cp[sel])        # d(0.5*h2)/dpsi
            perp = -uy[sel] * dx[sel] + ux[sel] * dy[sel]    # d(u.d)/dphi
            ent += [(it[a], perp + dh), (it[b], -dh)]
        add(len(a), ent, GAP - g0)

    # walls
    th = P[:, 2]
    c, s = np.cos(th), np.sin(th)
    sc, nc = _signs(c, kt); ss, ns_ = _signs(s, kt)
    for fc, fs in ((1, 1), (-1, 1), (1, -1)):
        if fc < 0:
            sel = nc
        elif fs < 0:
            sel = ns_
        else:
            sel = np.ones(n, bool)
        if not free and (fc < 0 or fs < 0):
            continue
        if not sel.any():
            continue
        q = np.nonzero(sel)[0]
        c_, s_ = sc[q] * fc, ss[q] * fs
        h0 = 0.5 * (c_ * c[q] + s_ * s[q])
        dh = 0.5 * (-c_ * s[q] + s_ * c[q])
        one = np.ones(len(q))
        for iv, ilo, x0 in ((ix, ilx, P[q, 0]), (iy, ily, P[q, 1])):
            lo = [(iv[q], one), (ilo, -one)]                  # x+dx-h >= lo
            hi = [(iv[q], -one), (ilo, one), (iL, one)]       # lo+L >= x+dx+h
            if free:
                lo.append((it[q], -dh)); hi.append((it[q], -dh))
            add(len(q), lo, h0 - x0)
            add(len(q), hi, x0 + h0)

    Aub = coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(nr, nv)).tocsr()
    bub = np.concatenate(rhs)
    cost = np.zeros(nv); cost[iL] = 1.0
    bounds = [(-tr_c, tr_c)] * (2 * n)
    if free:
        bounds += [(-tr_a, tr_a)] * n
    bounds += [(None, None), (None, None), (0, None)]
    res = linprog(cost, A_ub=Aub, b_ub=bub, bounds=bounds, method='highs',
                  options={'primal_feasibility_tolerance': 1e-10, 'dual_feasibility_tolerance': 1e-10, 'presolve': True})
    if res.status != 0:
        return None
    Q = P.copy()
    Q[:, 0] += res.x[ix]; Q[:, 1] += res.x[iy]
    if free:
        Q[:, 2] += res.x[it]
    return Q


def reclose(P, tr_c=0.02):
    """Fixed-angle LP, repeated while the side falls (the axes are picked again each time)."""
    L = side(P)
    for _ in range(6):
        Q = solve(P, tr_c, 0.0)
        if Q is None or min_gap(Q) < 2.5e-11:
            break
        LQ = side(Q)
        if LQ >= L - 1e-13:
            break
        P, L = Q, LQ
    return P, L


def slp(P, iters=60, tr_a=2e-3, tr_c=0.02, fixed=False, log=None):
    P, L = reclose(P, tr_c)
    if fixed:
        return P, L, 0
    done = 0; stall = 0
    for k in range(iters):
        done = k + 1
        Q = solve(P, tr_c, tr_a)
        if Q is not None:
            Q, LQ = reclose(Q, tr_c)
        ok = Q is not None and min_gap(Q) >= 2.5e-11 and LQ < L - 1e-13
        if log:
            log('  it %d tr_a %.1e L %.12f -> %s %s' % (k, tr_a, L, 'None' if Q is None else '%.12f' % LQ, 'ok' if ok else 'rej'))
        if ok:
            stall = stall + 1 if L - LQ < 1e-10 else 0
            P, L = Q, LQ
            tr_a = min(tr_a * 1.5, 5e-3)
            if stall >= 3:
                break
        else:
            tr_a /= 4
            if tr_a < 2e-8:
                break
    return P, L, done


def normal(P):
    """Put the bounding box at the origin."""
    h = half(P[:, 2]); Q = P.copy()
    Q[:, 0] -= (P[:, 0] - h).min(); Q[:, 1] -= (P[:, 1] - h).min()
    return Q


def job(a):
    n, P, iters, fixed, inflate, out = a
    t = time.time()
    L0 = side(P)
    if inflate:
        c = P[:, :2].mean(0); P = P.copy(); P[:, :2] = c + (P[:, :2] - c) * (1 + inflate)
    try:
        Q, L1, it = slp(P, iters=iters, fixed=fixed)
    except Exception as ex:      # one bad n must not stop a sweep
        return n, L0, L0, 0, time.time() - t, 'error %s' % ex
    if L1 < L0 - 1e-11:
        Q = normal(Q)
        with open('%s/raw/%d.csv' % (out, n), 'w', newline='') as g:
            w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
            for k, (x, y, th) in enumerate(Q):
                w.writerow([n, k, repr(float(x)), repr(float(y)), repr(float(th))])
    return n, L0, L1, it, time.time() - t, 'ok'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sub'); ap.add_argument('out')
    ap.add_argument('--ns'); ap.add_argument('--all', action='store_true'); ap.add_argument('--nmin', type=int, default=0)
    ap.add_argument('--mod'); ap.add_argument('--jobs', type=int, default=2); ap.add_argument('--iters', type=int, default=60)
    ap.add_argument('--fixed', action='store_true'); ap.add_argument('--inflate', type=float, default=0.0)
    a = ap.parse_args()
    want = set(int(x) for x in a.ns.split(',')) if a.ns else None
    pz = load(a.sub, want)
    ns = sorted(n for n in pz if n >= a.nmin and n >= 2)
    if a.mod:
        m, r = (int(x) for x in a.mod.split(','))
        ns = [n for n in ns if n % m == r]
    os.makedirs(a.out + '/raw', exist_ok=True)
    seen = set()
    tsv = a.out + '/lp.tsv'
    if os.path.exists(tsv):
        seen = set(int(l.split('\t')[0]) for l in open(tsv).read().splitlines()[1:] if l.strip())
    else:
        open(tsv, 'w').write('n\tL0\tL1\tgain\titers\tseconds\tstate\n')
    todo = [(n, pz[n], a.iters, a.fixed, a.inflate, a.out) for n in ns if n not in seen]
    tot = 0.0
    with Pool(a.jobs) as pool, open(tsv, 'a') as h:
        for n, L0, L1, it, sec, st in pool.imap_unordered(job, todo):
            gain = (L0 - L1) / math.sqrt(n)
            tot += max(gain, 0)
            h.write('%d\t%r\t%r\t%.3e\t%d\t%.1f\t%s\n' % (n, float(L0), float(L1), gain, it, sec, st)); h.flush()
            print('n=%d L %.12f -> %.12f gain %.3e it %d %.1fs %s total %.3e' % (n, L0, L1, gain, it, sec, st, tot), flush=True)


if __name__ == '__main__':
    main()
