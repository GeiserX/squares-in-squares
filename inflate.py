#!/usr/bin/env python3
"""Inflate: can a waste pocket of a held layout grow into one more unit square?

Take the held packing of n, put it in a fixed box of side B, set a small square
of side s in a waste pocket and grow s by sequential LP while every other square
may move and turn. If s reaches 1 in a box below the held side of n + 1, that is
a smaller packing of n + 1. If it does not, the largest s per pocket (s_max) is a
map of where one more square almost fits.

  pockets  local maxima of the clearance function (distance from a point to the
           nearest square or wall) on a grid of 0.02, the best 8 per layout. The
           seed of a pocket is the largest square that fits there with every
           other square frozen, over four start angles.
  grow     variables: the move of every square (dx, dy, dangle inside a trust
           region) and s. Objective: the largest s. Constraints: the separation
           of every near pair on its best axis, linearised in the angles, with
           the new square at side s, and the four walls of the box. After each
           LP s is cut to what truly fits at the new place (exact: the gap of a
           pair is linear in s). If the unit squares then overlap by more than
           1e-6, the same LP runs again from the new point with a small angle
           trust radius (a repair). A step counts only if the true geometry
           overlaps by less than 1e-6 and s grew. Stop: s gains less than 1e-6
           over 10 steps, s reaches 1 - 1e-7, or the time cap of the grow.
  hit      when s = 1 the centres are scaled apart by 4e-6, the n + 1 squares
           are squeezed with methods_lp.slp and written to
           OUT/raw/<n+1>-inflate-<n>-p<k>-<box>.csv for methods_take.py.

The separating-axis choice, the kink rule and the squeeze are methods_lp's
(best_axes, _signs, slp); this file adds the rows of a square of side s and the
fixed walls. Every move variable is split in two non-negative parts with a cost
of 1e-6, so a square that no row pushes stays where it is. Only the tilted
squares and the squares within 5 of the new one may turn.

Environment: INFLATE_FORK=1 solves every LP in a forked child and falls back to
the dual simplex when the child dies (the interior point method of the HiGHS in
scipy 1.13 segfaults on some of these LPs). INFLATE_LP picks the HiGHS method.

Usage:
  inflate.py map     HELD.csv DETAILS.csv OUT --ns 814,923 [--top 3] [--top0 1] [--boxes B1,B0] [--seconds 150] [--seconds0 60]
                     (--top pockets grow in B1, the first --top0 of them in B0; seconds is the cap of one grow)
  inflate.py ctlpos  HELD.csv DETAILS.csv OUT --ns 815,924      (n + 1: delete one square per kind, grow from 0.3)
  inflate.py ctlgrid OUT                                        (the plain grid has no pocket)
  inflate.py pockets HELD.csv DETAILS.csv OUT --ns 814          (the pockets only)
  inflate.py squeeze OUT STATE.csv ...                          (a state grown with --nosqueeze, squeezed here)
  inflate.py cont    DETAILS.csv OUT STATE.csv ... [--seconds S] (grow on from a state that the time cap cut)
  --deadline FILE   a file with an epoch second; no new grow starts after it
Output: OUT/map/<n>.tsv, OUT/ctlpos/<n1>.tsv, OUT/state/<n>-p<k>-<box>.csv (the grown layout, n + 1 rows, the
new square last at its side s in the column side), OUT/raw/ on a hit.
Our own code; needs numpy and scipy only. Reads packings as data.
"""
import argparse, csv, math, os, select, sys, time

import numpy as np
from scipy.ndimage import maximum_filter
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, hstack
from scipy.spatial import cKDTree

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
import methods_lp as mlp  # noqa: E402

HALF_PI = math.pi / 2
GAP = mlp.GAP
ROT = 5.0            # every square this near the new one may turn; farther away only the tilted ones
EPS = 1e-6           # cost of one unit of move, against 1 for one unit of s
DONE = 1 - 1e-7      # s counts as 1 from here; the squeeze then sets every gap again
METHOD = os.environ.get('INFLATE_LP', 'highs-ipm')   # highs-ds where the interior point of an older HiGHS crashes
FORK = os.environ.get('INFLATE_FORK', '') == '1'
LP_TOL = 1e-8        # HiGHS tolerances; at 1e-10 older HiGHS builds answer 'model status unknown' on the repair LPs
TOL = 1e-6           # overlap a grow step may leave in the true geometry (the next LP removes it)


# ---------------------------------------------------------------- geometry with one square of side s

def new_axes(P, q, s, nb):
    """Best separating axis between the new square q = (x, y, angle) of side s and each unit square P[nb].
    -> gap, own (True where the axis is the new square's), phi (axis angle, from the owner to the other)."""
    k = len(nb)
    best = np.full(k, -np.inf); own = np.zeros(k, bool); PHI = np.zeros(k)
    dx, dy = P[nb, 0] - q[0], P[nb, 1] - q[1]
    for j in range(4):
        phi = q[2] + j * HALF_PI
        psi = P[nb, 2] - phi
        g = math.cos(phi) * dx + math.sin(phi) * dy - 0.5 * s - 0.5 * (np.abs(np.cos(psi)) + np.abs(np.sin(psi)))
        m = g > best; best[m] = g[m]; own[m] = True; PHI[m] = phi
        phi = P[nb, 2] + j * HALF_PI
        psi = q[2] - phi
        g = -(np.cos(phi) * dx + np.sin(phi) * dy) - 0.5 - 0.5 * s * (np.abs(np.cos(psi)) + np.abs(np.sin(psi)))
        m = g > best; best[m] = g[m]; own[m] = False; PHI[m] = phi[m]
    return best, own, PHI


def feas(P, q, s, B, units=True):
    """True smallest pair gap (the new square at side s) and smallest wall margin in the box [0, B]^2."""
    g = mlp.min_gap(P) if units else math.inf
    nb = np.array(cKDTree(P[:, :2]).query_ball_point(q[:2], 1.5), int)
    if len(nb):
        g = min(g, float(new_axes(P, q, s, nb)[0].min()))
    hq = s * 0.5 * (abs(math.cos(q[2])) + abs(math.sin(q[2])))
    w = min(q[0] - hq, q[1] - hq, B - q[0] - hq, B - q[1] - hq)
    if units:
        h = mlp.half(P[:, 2])
        w = min(w, (P[:, 0] - h).min(), (P[:, 1] - h).min(), (B - P[:, 0] - h).min(), (B - P[:, 1] - h).min())
    return g, float(w)


def s_fit(P, q, B):
    """The largest side the new square can have where it is: every pair GAP apart on its best axis, inside the box.
    The gap of a pair is linear in s on each axis, so this is exact."""
    hq = abs(math.cos(q[2])) + abs(math.sin(q[2]))
    s = 2 * min(q[0], q[1], B - q[0], B - q[1]) / hq
    nb = np.array(cKDTree(P[:, :2]).query_ball_point(q[:2], 1.5 + 1e-6), int)
    if not len(nb):
        return s
    dx, dy = P[nb, 0] - q[0], P[nb, 1] - q[1]
    lim = np.full(len(nb), -np.inf)
    for j in range(4):
        phi = q[2] + j * HALF_PI
        psi = P[nb, 2] - phi
        lim = np.maximum(lim, 2 * (math.cos(phi) * dx + math.sin(phi) * dy - 0.5 * (np.abs(np.cos(psi)) + np.abs(np.sin(psi))) - GAP))
        phi = P[nb, 2] + j * HALF_PI
        psi = q[2] - phi
        lim = np.maximum(lim, 2 * (-(np.cos(phi) * dx + np.sin(phi) * dy) - 0.5 - GAP) / (np.abs(np.cos(psi)) + np.abs(np.sin(psi))))
    return float(min(s, lim.min()))


def _linprog(cost, A, b, bounds, method):
    res = linprog(cost, A_ub=A, b_ub=b, bounds=bounds, method=method,
                  options={'primal_feasibility_tolerance': LP_TOL, 'dual_feasibility_tolerance': LP_TOL, 'presolve': True,
                           'time_limit': 60.0})
    return res.x if res.status == 0 else None


def solve_lp(cost, A, b, bounds, method):
    """The LP's solution or None. With INFLATE_FORK=1 the solver runs in a forked child, and when the child
    dies (the interior point of the HiGHS in scipy 1.13 segfaults on some of these LPs) the dual simplex
    solves the same LP in a second child."""
    if not FORK:
        return _linprog(cost, A, b, bounds, method)
    for meth in (method, 'highs-ds'):
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            try:
                x = _linprog(cost, A, b, bounds, meth)
                data = b'N' if x is None else b'X' + np.asarray(x, float).tobytes()
            except BaseException:
                data = b'N'
            with os.fdopen(w, 'wb') as h:
                h.write(data)
            os._exit(0)
        os.close(w)
        chunks = []; alive = True; t0 = time.time()
        while True:
            ready, _, _ = select.select([r], [], [], 5.0)
            if ready:
                c = os.read(r, 1 << 20)
                if not c:
                    break
                chunks.append(c)
            elif time.time() - t0 > 90:
                os.kill(pid, 9); alive = False; break
        os.close(r); os.waitpid(pid, 0)
        data = b''.join(chunks)
        if alive and data[:1] == b'X':
            return np.frombuffer(data[1:], float).copy()
        if alive and data[:1] == b'N':
            return None                      # solved, no optimum: the caller cuts the trust region
    return None


def lp_step(P, q, s, B, tr_c, tr_a, only_new=False, rot_all=False, method=None):
    """One LP: the largest s. tr_a = 0 freezes the angles (exact). -> (P, q, s) or None.
    Squares that may turn: the tilted ones and every square within ROT of the new one (rot_all: every square)."""
    n = len(P); N = n + 1
    A = np.vstack([P, q]); sz = np.ones(N); sz[n] = s
    free = tr_a > 0
    rot = np.ones(N, bool)
    if not rot_all:
        rot[:n] = (np.abs(((P[:, 2] + math.pi / 4) % HALF_PI) - math.pi / 4) > 1e-6) | (((P[:, :2] - q[:2]) ** 2).sum(1) < ROT ** 2)
    kt = 2.5 * tr_a
    reach = math.sqrt(2) + 3 * tr_c + 0.1
    tree = cKDTree(P[:, :2])
    nb = np.array(sorted(tree.query_ball_point(q[:2], reach)), int)
    _, own, phi = new_axes(P, q, s, nb)
    a = np.where(own, n, nb); b = np.where(own, nb, n)
    if not only_new:
        pairs = tree.query_pairs(reach, output_type='ndarray')
        if len(pairs):
            _, Au, Bu, PHIu = mlp.best_axes(P, pairs)
            a = np.concatenate([a, Au]); b = np.concatenate([b, Bu]); phi = np.concatenate([phi, PHIu])
    IS = 3 * N
    rows, cols, vals, rhs = [], [], [], []
    nr = 0

    def add(k, entries, bb):
        """k rows 'sum(entries) >= bb'."""
        nonlocal nr
        r = nr + np.arange(k)
        for c, v in entries:
            rows.append(r); cols.append(np.broadcast_to(c, (k,))); vals.append(np.broadcast_to(v, (k,)).astype(float))
        rhs.append(np.broadcast_to(bb, (k,)).astype(float)); nr += k

    branches = ((1, 1), (-1, 1), (1, -1))        # own signs; cos flipped; sin flipped (methods_lp's kink rule)
    # pairs: gap = u.(cb - ca) - sa/2 - (sb/2)(|cos psi| + |sin psi|), psi = angle of b - axis angle
    if len(a):
        ux, uy = np.cos(phi), np.sin(phi)
        dx, dy = A[b, 0] - A[a, 0], A[b, 1] - A[a, 1]
        psi = A[b, 2] - phi
        cp, sp = np.cos(psi), np.sin(psi)
        sc, nc = mlp._signs(cp, kt); ss, ns_ = mlp._signs(sp, kt)
        for fc, fs in branches:
            sel = nc & (rot[a] | rot[b]) if fc < 0 else ns_ & (rot[a] | rot[b]) if fs < 0 else np.ones(len(a), bool)
            if (fc < 0 or fs < 0) and not free:
                continue
            if not sel.any():
                continue
            aa, bb = a[sel], b[sel]
            c_, s_ = sc[sel] * fc, ss[sel] * fs
            hh = c_ * cp[sel] + s_ * sp[sel]
            g0 = ux[sel] * dx[sel] + uy[sel] * dy[sel] - 0.5 * sz[aa] - 0.5 * sz[bb] * hh
            ent = [(bb, ux[sel]), (N + bb, uy[sel]), (aa, -ux[sel]), (N + aa, -uy[sel]),
                   (IS, -0.5 * (aa == n) - 0.5 * hh * (bb == n))]
            if free:
                dh = 0.5 * sz[bb] * (-c_ * sp[sel] + s_ * cp[sel])
                perp = -uy[sel] * dx[sel] + ux[sel] * dy[sel]
                ent += [(2 * N + aa, perp + dh), (2 * N + bb, -dh)]
            add(len(aa), ent, GAP - g0)
    # walls of the fixed box: x - (size/2) h >= 0 and x + (size/2) h <= B, h = |cos| + |sin|
    idx = np.array([n]) if only_new else np.arange(N)
    c, sn = np.cos(A[idx, 2]), np.sin(A[idx, 2])
    sc, nc = mlp._signs(c, kt); ss, ns_ = mlp._signs(sn, kt)
    for fc, fs in branches:
        sel = nc & rot[idx] if fc < 0 else ns_ & rot[idx] if fs < 0 else np.ones(len(idx), bool)
        if (fc < 0 or fs < 0) and not free:
            continue
        if not sel.any():
            continue
        qi = idx[sel]
        c_, s_ = sc[sel] * fc, ss[sel] * fs
        h0 = c_ * c[sel] + s_ * sn[sel]; hp = -c_ * sn[sel] + s_ * c[sel]
        z = sz[qi]; isn = (qi == n).astype(float); one = np.ones(len(qi))
        for off, x0 in ((0, A[qi, 0]), (N, A[qi, 1])):
            lo = [(off + qi, one), (IS, -0.5 * h0 * isn)]
            hi = [(off + qi, -one), (IS, -0.5 * h0 * isn)]
            if free:
                lo.append((2 * N + qi, -0.5 * z * hp)); hi.append((2 * N + qi, -0.5 * z * hp))
            add(len(qi), lo, 0.5 * z * h0 - x0)
            add(len(qi), hi, x0 + 0.5 * z * h0 - B)

    S = coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(nr, 3 * N + 1)).tocsc()
    keep = np.array([n]) if only_new else np.arange(N)
    nk = len(keep)
    Sx, Sy = S[:, keep], S[:, N + keep]
    blocks = [Sx, -Sx, Sy, -Sy]
    bounds = [(0, tr_c)] * (4 * nk)
    if free:
        kr = keep[rot[keep]]; nt = len(kr)
        St = S[:, 2 * N + kr]
        blocks += [St, -St]; bounds += [(0, tr_a)] * (2 * nt)
    blocks.append(S[:, [IS]]); bounds.append((max(0.02 - s, -0.5), 1.0 - s))
    M = hstack(blocks).tocsr()
    cost = np.full(M.shape[1], EPS); cost[-1] = -1.0
    x = solve_lp(cost, -M, -np.concatenate(rhs), bounds, method or METHOD)
    if x is None:
        return None
    Q = A.copy()
    Q[keep, 0] += x[0:nk] - x[nk:2 * nk]; Q[keep, 1] += x[2 * nk:3 * nk] - x[3 * nk:4 * nk]
    if free:
        Q[kr, 2] += x[4 * nk:4 * nk + nt] - x[4 * nk + nt:4 * nk + 2 * nt]
    return Q[:n], Q[n].copy(), s + float(x[-1])


def grow(P, q, s, B, maxit=400, seconds=1e9, only_new=False, tr_c=0.05, tr_a=0.02, log=None):
    """Sequential LP on s. -> P, q, s, steps, why ('one', 'stall', 'time', 'steps').

    A step is one LP with the angles linearised, then up to two repair LPs: the same LP from the new point with
    an angle trust radius of 20 times the overlap left, which removes the second-order error of the first (a
    jammed box has no room to repair it with the angles frozen). After each LP s is cut to what truly fits
    (s_fit), because the LP drops the product of the change of s and the change of angle. The step counts if the true geometry then
    overlaps by less than TOL and s grew; if not, the angle trust radius is cut by 4."""
    t0 = time.time(); tra = tr_a; hist = [s]; why = 'steps'; it = 0

    def settle(R):
        """Cut s to what truly fits at the new place (exact), then the overlap left among the unit squares."""
        Pn, qn, sn = R
        sn = min(sn, s_fit(Pn, qn, B))
        if only_new:
            return (Pn, qn, sn), 0.0
        h = mlp.half(Pn[:, 2])
        w = min((Pn[:, 0] - h).min(), (Pn[:, 1] - h).min(), (B - Pn[:, 0] - h).min(), (B - Pn[:, 1] - h).min())
        return (Pn, qn, sn), max(-mlp.min_gap(Pn), -float(w))
    for it in range(1, maxit + 1):
        R = lp_step(P, q, s, B, tr_c, tra, only_new)
        v = math.inf
        if R is not None:
            R, v = settle(R)
            for _ in range(2):
                if v <= TOL or tra == 0 or R[2] < 0.02:
                    break
                R2 = lp_step(R[0], R[1], R[2], B, 0.02, max(1e-4, 20 * v), only_new)
                if R2 is None:
                    break
                R, v = settle(R2)
        ok = R is not None and v <= TOL and R[2] > s + 1e-12
        if log:
            log('  it %d tr_a %.1e s %.9f -> %s overlap %.1e %s' % (it, tra, s, 'None' if R is None else '%.9f' % R[2], max(v, 0), 'ok' if ok else 'rej'))
        if ok:
            P, q, s = R
            tra = min(max(tra, 1e-4) * 1.5, tr_a)
        elif tra > 0:
            tra = tra / 4 if tra > 2e-5 else 0.0       # last try: no turning at all
        else:
            why = 'stall'; hist.append(s); break
        hist.append(s)
        if s >= DONE:
            why = 'one'; break
        if len(hist) > 10 and hist[-1] - hist[-11] < 1e-6:
            why = 'stall'; break
        if time.time() - t0 > seconds:
            why = 'time'; break
    return P, q, s, it, why


# ---------------------------------------------------------------- pockets

def clearance(P, B, h=0.02, cap=0.8):
    """Distance from every grid point to the nearest square or wall (0 inside a square), cut at cap."""
    ng = int(math.floor(B / h)) + 1
    xs = np.arange(ng) * h
    wd = np.minimum(xs, B - xs)
    D = np.minimum(np.minimum.outer(wd, wd), cap)
    r = 0.5 * math.sqrt(2) + cap
    for x, y, t in P:
        i0 = max(0, int((x - r) / h)); i1 = min(ng, int((x + r) / h) + 2)
        j0 = max(0, int((y - r) / h)); j1 = min(ng, int((y + r) / h) + 2)
        X = xs[i0:i1, None] - x; Y = xs[None, j0:j1] - y
        c, s = math.cos(t), math.sin(t)
        u = np.abs(c * X + s * Y) - 0.5; v = np.abs(-s * X + c * Y) - 0.5
        d = np.hypot(np.maximum(u, 0), np.maximum(v, 0))
        np.minimum(D[i0:i1, j0:j1], d, out=D[i0:i1, j0:j1])
    return xs, D


def pockets(P, B, top=8, h=0.02, rmin=0.05, apart=0.45, seed=True):
    """-> [dict(x, y, r, s0, q)] by falling clearance r; q = (x, y, angle) of the seed square of side s0."""
    xs, D = clearance(P, B, h)
    w = int(round(0.2 / h))
    pk = np.argwhere((D == maximum_filter(D, size=2 * w + 1)) & (D > rmin))
    pk = pk[np.argsort(-D[pk[:, 0], pk[:, 1]], kind='stable')]
    out = []
    for i, j in pk:
        x, y = xs[i], xs[j]
        if any((x - o['x']) ** 2 + (y - o['y']) ** 2 < apart ** 2 for o in out):
            continue
        out.append(dict(x=float(x), y=float(y), r=float(D[i, j])))
        if len(out) == top:
            break
    if seed:
        for o in out:
            best = None
            for th in (0.0, math.pi / 8, math.pi / 4, 3 * math.pi / 8):
                q = np.array([o['x'], o['y'], th]); s = 0.9 * math.sqrt(2) * o['r']
                g, wl = feas(P, q, s, B, False)
                if g < 0 or wl < 0:
                    continue
                _, q, s, _, _ = grow(P, q, s, B, maxit=60, only_new=True, tr_c=0.03, tr_a=0.05)
                if best is None or s > best[0]:
                    best = (s, q)
            o['s0'], o['q'] = (best if best else (0.0, np.array([o['x'], o['y'], 0.0])))
    return out


# ---------------------------------------------------------------- zones of a two-arm layout

def arms_of(P, n):
    """The two arms of flush stacks (frontier_profile.flush_arms) -> [arm, arm] or None.
    arm: wall L/R/B/T, c, t (tilt), W (strip width), lo..hi (the flush run along the wall), ns (stacks)."""
    try:
        import frontier_profile as fp
    except Exception:
        return None
    L = mlp.side(P); m = math.isqrt(n - 1); f = L - m
    d = np.degrees(P[:, 2]) % 90.0; d[d > 45] -= 90
    arms = fp.flush_arms(np.column_stack([P[:, 0], P[:, 1], d]), L, m)
    if len(arms) < 2:
        return None
    a1 = arms[0]
    a2 = next((a for a in arms[1:] if (a[0] in 'LR') != (a1[0] in 'LR')), None)
    if a2 is None:
        return None
    out = []
    for wall, c, t, cen in (a1, a2):
        cen = np.array(cen); ax = 1 if wall in 'LR' else 0; p = 1 / math.cos(t)
        out.append(dict(wall=wall, c=c, t=t, W=c - 1 + f, ax=ax, ns=len(cen),
                        lo=float(cen[:, ax].min() - p / 2), hi=float(cen[:, ax].max() + p / 2)))
    return out


def freed(a, delta):
    """Wall length an arm frees when the box grows by delta: the box itself, and every flush stack turned upright
    by delta / (c sin t - cos t), which shortens its pitch 1 / cos t."""
    t = a['t']
    return delta * (1 + a['ns'] * math.tan(t) / (math.cos(t) * (a['c'] * math.sin(t) - math.cos(t))))


def kind_of(x, y, arms, L):
    """-> kind, lever, arm index. Kinds: corner, cap, tooth-wall, tooth-grid, run, grid-edge, grid; without two
    flush arms: wall, inner."""
    if arms is None:
        return ('wall' if min(x, y, L - x, L - y) < 1.2 else 'inner'), 1.0, -1
    dist = [{'L': x, 'R': L - x, 'B': y, 'T': L - y}[a['wall']] for a in arms]
    inn = [dist[i] < arms[i]['W'] + 0.25 for i in (0, 1)]
    if inn[0] and inn[1]:
        return 'corner', 1.0, -1
    for i in (0, 1):
        if not inn[i]:
            continue
        a, o = arms[i], arms[1 - i]
        u = y if a['ax'] == 1 else x
        if a['lo'] <= u <= a['hi']:
            return ('tooth-wall' if dist[i] < 1.0 else 'tooth-grid' if dist[i] > a['W'] - 1.0 else 'run'), 0.3, i
        low = o['wall'] in 'LB'                       # the shared corner is at the low end of this arm
        if (u < a['lo']) == low:
            return 'corner', 1 / math.sin(a['t']), i
        return 'cap', 1 / math.sin(a['t']), i
    return ('grid-edge' if min(dist[i] - arms[i]['W'] for i in (0, 1)) < 1.0 else 'grid'), 0.0, -1


def predict(pk, arms, L, delta):
    """The geometric guess of s_max in a box delta larger: seed + lever * wall freed by the arm beside it."""
    kind, lever, i = kind_of(pk['x'], pk['y'], arms, L)
    if arms is None:
        gain = 4 * delta
    elif i < 0:
        gain = max(freed(a, delta) for a in arms) if kind == 'corner' else delta
    else:
        gain = lever * freed(arms[i], delta)
    return kind, min(1.0, pk['s0'] + gain)


# ---------------------------------------------------------------- files

def held_sides(details):
    return {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}


def write_rows(path, n, P, sides=None):
    tmp = path + '.tmp'
    with open(tmp, 'w', newline='') as g:
        w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'] + (['side'] if sides is not None else []))
        for k, (x, y, th) in enumerate(P):
            w.writerow([n, k, repr(float(x)), repr(float(y)), repr(float(th))] + ([repr(float(sides[k]))] if sides is not None else []))
    os.replace(tmp, path)


def write_tsv(path, head, rows):
    tmp = path + '.tmp'
    with open(tmp, 'w') as h:
        h.write('\t'.join(head) + '\n')
        for r in rows:
            h.write('\t'.join(str(v) for v in r) + '\n')
    os.replace(tmp, path)


def finish(P, q, n1, out, tag, log):
    """s = 1: squeeze the n + 1 unit squares the lane's way and write the raw rows. -> side or None.
    A grown state may overlap by TOL, and the new square is 1e-7 short of 1. The centres are first scaled apart
    (by 4e-6, doubled until no pair overlaps), so methods_lp.slp starts from a legal packing and squeezes it."""
    Q0 = np.vstack([P, q]); e = 4e-6
    for _ in range(9):
        Q = Q0.copy(); Q[:, :2] *= 1 + e
        if mlp.min_gap(Q) >= 2.5e-11:
            break
        e *= 2
    # methods_lp asks 4e-11 of every pair and keeps a result only at 2.5e-11. The HiGHS of scipy 1.18 returns that
    # LP with a smallest gap of -1.6e-11 on these states, so the squeeze runs down a ladder of asked gaps and
    # keeps the smallest legal side.
    best = None; gap0 = mlp.GAP
    try:
        for gp in (1e-8, 1e-9, 2e-10, gap0):
            mlp.GAP = gp
            R, L1, _ = mlp.slp(Q if best is None else best[0], iters=60 if best is None else 10)
            if mlp.min_gap(R) >= 2.5e-11 and (best is None or L1 < best[1]):
                best = (R, L1)
    finally:
        mlp.GAP = gap0
    if best is None:
        log('SQUEEZE-BROKEN n1=%d %s: no legal packing from the grown state' % (n1, tag))
        return None
    Q, L1 = best
    os.makedirs(out + '/raw', exist_ok=True)
    write_rows('%s/raw/%d-%s.csv' % (out, n1, tag), n1, mlp.normal(Q))
    return L1


def past(deadline):
    try:
        return deadline and time.time() > float(open(deadline).read().split()[0])
    except Exception:
        return False


# ---------------------------------------------------------------- modes

MAP_HEAD = ['n', 'm', 'k', 'f', 'L', 'delta', 'pocket', 'x', 'y', 'kind', 'clear', 's0', 'pred_B1', 'rank', 'twin',
            'smax_B0', 'steps_B0', 'stop_B0', 'sec_B0', 'smax_B1', 'steps_B1', 'stop_B1', 'sec_B1', 'hit_side']


def run_map(a):
    Ls = held_sides(a.details)
    ns = [int(x) for x in a.ns.split(',')]
    pz = mlp.load(a.held, set(ns))
    for d in ('map', 'state'):
        os.makedirs('%s/%s' % (a.out, d), exist_ok=True)
    lg = open(a.out + '/inflate.log', 'a')

    def log(s):
        lg.write(s + '\n'); lg.flush(); print(s, flush=True)
    boxes = a.boxes.split(',')
    for n in ns:
        path = '%s/map/%d.tsv' % (a.out, n)
        if os.path.exists(path) or past(a.deadline):
            continue
        t0 = time.time()
        P = mlp.normal(pz[n]); L = mlp.side(P); m = math.isqrt(n - 1); k = n - m * m; f = L - m
        delta = Ls[n + 1] - L
        arms = arms_of(P, n)
        pk = pockets(P, L, top=8)
        for i, o in enumerate(pk):
            o['id'] = i; o['kind'], o['pred'] = predict(o, arms, L, max(delta - 1e-6, 0))
        order = []
        for o in sorted(pk, key=lambda o: -o['pred']):     # a mirror image of a pocket already listed is the same test
            o['twin'] = next((p['id'] for p in order if abs(p['x'] - o['y']) < 0.05 and abs(p['y'] - o['x']) < 0.05
                              and abs(p['s0'] - o['s0']) < 2e-3), '')
            order.append(o)
        log('n=%d L=%.9f delta=%.6f arms=%s pockets=%s (%.0fs)' % (
            n, L, delta, 'none' if arms is None else '%s%d/%s%d' % (arms[0]['wall'], arms[0]['c'], arms[1]['wall'], arms[1]['c']),
            ' '.join('%s:%.3f>%.3f' % (o['kind'], o['s0'], o['pred']) for o in order), time.time() - t0))
        res = {}
        for bx in boxes:                                   # every B1 grow of this n first, then B0
            B = L if bx == 'B0' else Ls[n + 1] - 1e-6
            if B < L - 1e-12:
                continue
            todo = [o for o in order if o['twin'] == ''][:a.top if bx == 'B1' else a.top0]
            for o in todo:
                if past(a.deadline):
                    break
                t1 = time.time()
                Pg, qg, s, steps, why = grow(P.copy(), o['q'].copy(), o['s0'], B, seconds=a.seconds if bx == 'B1' else a.seconds0)
                hit = ''
                if why == 'one' and not a.nosqueeze:
                    tag = 'inflate-%d-p%d-%s' % (n, o['id'], bx)
                    L1 = finish(Pg, qg, n + 1, a.out, tag, log)
                    hit = '' if L1 is None else '%.12f' % L1
                    log('ONE n=%d pocket %d %s: n+1 squeezed to side %s, held %.12f' % (n, o['id'], bx, hit, Ls[n + 1]))
                write_rows('%s/state/%d-p%d-%s.csv' % (a.out, n, o['id'], bx), n + 1, np.vstack([Pg, qg]), sides=[1.0] * n + [s])
                res[(o['id'], bx)] = (s, steps, why, time.time() - t1, hit)
                log('  n=%d p%d %s %s s0 %.4f pred %.4f -> s %.6f steps %d %s %.0fs' % (
                    n, o['id'], o['kind'], bx, o['s0'], o['pred'], s, steps, why, time.time() - t1))
        rows = []
        for rank, o in enumerate(order):
            r0 = res.get((o['id'], 'B0')); r1 = res.get((o['id'], 'B1'))
            rows.append([n, m, k, '%.6f' % f, '%.9f' % L, '%.6f' % delta, o['id'], '%.2f' % o['x'], '%.2f' % o['y'], o['kind'],
                         '%.3f' % o['r'], '%.6f' % o['s0'], '%.4f' % o['pred'], rank, o['twin']]
                        + (['%.6f' % r0[0], r0[1], r0[2], '%.0f' % r0[3]] if r0 else ['', '', '', ''])
                        + (['%.6f' % r1[0], r1[1], r1[2], '%.0f' % r1[3]] if r1 else ['', '', '', ''])
                        + [(r1[4] if r1 else '') or (r0[4] if r0 else '')])
        if not past(a.deadline):
            write_tsv(path, MAP_HEAD, rows)


def pick(P, n1, want):
    """A square of the held n + 1 of the wanted kind (cap: tilted, corner, corner-tilted, grid-edge: upright): the one
    nearest the middle of its kind."""
    L = mlp.side(P); arms = arms_of(P, n1)
    if arms is None:
        return None
    up = np.abs(((P[:, 2] + math.pi / 4) % HALF_PI) - math.pi / 4) < 1e-3
    cand = []
    for i, (x, y, t) in enumerate(P):
        kd = kind_of(x, y, arms, L)[0]
        if want == 'grid-edge':
            if kd == 'grid-edge' and up[i]:
                cand.append(i)
        elif want == 'corner-tilted':
            if kd == 'corner' and not up[i]:
                cand.append(i)
        elif kd == want and (want == 'corner' or not up[i]):
            cand.append(i)
    if not cand:
        return None
    c = P[cand, :2].mean(0)
    return cand[int(np.argmin(((P[cand, :2] - c) ** 2).sum(1)))]


def run_ctlpos(a):
    Ls = held_sides(a.details)
    ns = [int(x) for x in a.ns.split(',')]
    pz = mlp.load(a.held, set(ns))
    os.makedirs(a.out + '/ctlpos', exist_ok=True)
    kinds = a.kinds.split(',')
    for j, n1 in enumerate(ns):
        P = mlp.normal(pz[n1]); L = mlp.side(P)
        want = kinds[j % len(kinds)]
        i = pick(P, n1, want)
        if i is None:
            print('n1=%d no square of kind %s (no two flush arms?)' % (n1, want), flush=True); continue
        x, y, t = P[i]
        Q = np.delete(P, i, axis=0)
        t0 = time.time()
        Pg, qg, s, steps, why = grow(Q, np.array([x, y, 0.0]), 0.3, L, seconds=a.seconds,
                                     log=(lambda s_: print(s_, flush=True)) if a.verbose else None)
        os.makedirs(a.out + '/state', exist_ok=True)
        write_rows('%s/state/ctl%d-%s.csv' % (a.out, n1, want), n1, np.vstack([Pg, qg]), sides=[1.0] * (n1 - 1) + [s])
        L1 = None
        if why == 'one' and not a.nosqueeze:
            R, L1, _ = mlp.slp(np.vstack([Pg, qg]), iters=30)
            if mlp.min_gap(R) < 2.5e-11:
                L1 = None
        tilt = math.degrees(((t + math.pi / 4) % HALF_PI) - math.pi / 4)
        row = [n1, '%.12f' % L, want, i, '%.3f' % x, '%.3f' % y, '%.2f' % tilt, '%.12f' % s, steps, why,
               '%.0f' % (time.time() - t0), '' if L1 is None else '%.12f' % L1, '' if L1 is None else '%.2e' % (L1 - Ls[n1])]
        write_tsv('%s/ctlpos/%d-%s.tsv' % (a.out, n1, want), ['n1', 'held_side', 'kind', 'square', 'x', 'y', 'tilt_deg', 's', 'steps',
                                                    'stop', 'seconds', 'side_after_squeeze', 'side_minus_held'], [row])
        print('ctlpos', ' '.join(str(v) for v in row), flush=True)


def run_squeeze(a):
    """inflate.py squeeze OUT STATE.csv ...: a grown state whose new square reached 1 -> the lane's squeeze, raw rows."""
    out = a.args[0]
    for path in a.args[1:]:
        rows = list(csv.DictReader(open(path)))
        n1 = int(rows[0]['n']); s = float(rows[-1]['side'])
        P = np.array([(float(r['x']), float(r['y']), float(r['angle'])) for r in rows])
        tag = os.path.basename(path)[:-4]
        if s < DONE:
            print('squeeze %s: s = %.9f, not 1' % (tag, s), flush=True); continue
        L1 = finish(P[:-1], P[-1], n1, out, 'inflate-' + tag, lambda t: print(t, flush=True))
        print('squeeze %s n1=%d side %s' % (tag, n1, 'none' if L1 is None else '%.12f' % L1), flush=True)


def run_cont(a):
    """inflate.py cont DETAILS.csv OUT STATE.csv ...: grow on from a saved state <n>-p<k>-<box>.csv, in the same box."""
    Ls = held_sides(a.args[0]); out = a.args[1]
    for d in ('state', 'cont'):
        os.makedirs('%s/%s' % (out, d), exist_ok=True)
    for path in a.args[2:]:
        if past(a.deadline):
            break
        tag = os.path.basename(path)[:-4]; n = int(tag.split('-')[0]); bx = tag.split('-')[-1]
        rows = list(csv.DictReader(open(path)))
        A = np.array([(float(r['x']), float(r['y']), float(r['angle'])) for r in rows]); s = float(rows[-1]['side'])
        B = Ls[n] if bx == 'B0' else Ls[n + 1] - 1e-6
        t0 = time.time()
        Pg, qg, s1, steps, why = grow(A[:-1], A[-1], s, B, seconds=a.seconds)
        write_rows('%s/state/%s.csv' % (out, tag), n + 1, np.vstack([Pg, qg]), sides=[1.0] * n + [s1])
        row = [n, tag.split('-')[1], bx, '%.6f' % s, '%.6f' % s1, steps, why, '%.0f' % (time.time() - t0)]
        write_tsv('%s/cont/%s.tsv' % (out, tag), ['n', 'pocket', 'box', 's_before', 's_after', 'steps', 'stop', 'seconds'], [row])
        print('cont', ' '.join(str(v) for v in row), flush=True)


def run_ctlgrid(a):
    os.makedirs(a.out, exist_ok=True)
    rows = []
    for m in (5, 17, 31):
        g = np.arange(m) + 0.5
        P = np.array([(x, y, 0.0) for x in g for y in g])
        _, D = clearance(P, float(m))
        pk = pockets(P, float(m))
        rows.append([m * m, m, '%.3e' % D.max(), len(pk)])
        print('ctlgrid n=%d box %d largest clearance %.3e pockets %d' % (m * m, m, D.max(), len(pk)), flush=True)
    write_tsv(a.out + '/ctlgrid.tsv', ['n', 'box', 'largest_clearance', 'pockets'], rows)


def run_pockets(a):
    Ls = held_sides(a.details)
    ns = [int(x) for x in a.ns.split(',')]
    pz = mlp.load(a.held, set(ns))
    for n in ns:
        P = mlp.normal(pz[n]); L = mlp.side(P); arms = arms_of(P, n)
        delta = Ls.get(n + 1, L) - L
        t0 = time.time()
        pk = pockets(P, L)
        print('n=%d L=%.9f delta=%.6f arms=%s (%.1fs)' % (n, L, delta, arms, time.time() - t0))
        for o in pk:
            kd, pr = predict(o, arms, L, max(delta, 0))
            print('  (%.2f, %.2f) clear %.3f s0 %.4f angle %.1f %s pred %.3f' % (o['x'], o['y'], o['r'], o['s0'], math.degrees(o['q'][2]), kd, pr))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['map', 'ctlpos', 'ctlgrid', 'pockets', 'squeeze', 'cont'])
    ap.add_argument('args', nargs='+')
    ap.add_argument('--ns'); ap.add_argument('--top', type=int, default=3); ap.add_argument('--boxes', default='B1,B0')
    ap.add_argument('--seconds', type=float, default=150); ap.add_argument('--deadline')
    ap.add_argument('--nosqueeze', action='store_true', help='leave the squeeze of a grown state to the squeeze mode (another box)')
    ap.add_argument('--top0', type=int, default=1); ap.add_argument('--seconds0', type=float, default=60)
    ap.add_argument('--kinds', default='cap,corner,grid-edge'); ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args()
    if a.mode == 'ctlgrid':
        a.out = a.args[0]
        return run_ctlgrid(a)
    if a.mode == 'squeeze':
        return run_squeeze(a)
    if a.mode == 'cont':
        return run_cont(a)
    a.held, a.details, a.out = a.args
    {'map': run_map, 'ctlpos': run_ctlpos, 'pockets': run_pockets}[a.mode](a)


if __name__ == '__main__':
    main()
