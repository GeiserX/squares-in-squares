#!/usr/bin/env python3
"""Search one end zone of a two-arm layout as its own problem.

  zone_search.py classes DETAILS.csv BOARD.json [LO HI]    loss against count class, ours and the board
  zone_search.py base    LIBWORK OUT.pkl F [C]             the library's far zones carried to F (start states)
  zone_search.py control BASE.pkl OUTDIR [--seed S] [--minutes M] [--part AB]
  zone_search.py search  BASE.pkl OUTDIR --count N [--minutes M] [--seed S] [--moves delete,row,insert,resume,hop]
  zone_search.py taper   C F OUTDIR LO HI [STEP]           enumerate the lattice tapers, build the best of every count
  zone_search.py table   OUTDIR OUT.tsv LIBWORK            every kept zone as a row, and as a module
  zone_search.py merge   LIBWORK OUTDIR NEWWORK            library.pkl and lens.pkl with the kept zones added
  zone_search.py predict NEWWORK DETAILS.csv OUT.tsv       the generator of modules.py with the new zones
  zone_search.py build   NEWWORK RAWDIR DETAILS.csv N      its build step for the choices that hold a new zone

The zone problem. A far zone lives in a strip of width W = c - 1 + f along a wall. Frame: x is the distance from
the wall the arm runs along (0 <= x <= W; the upright grid of the layout starts at x = W and is kept rigid),
y is the distance from the end wall. The other end is the face of a flush stack (c squares set face to face at
the tilt t with c cos t + sin t = W) that slides along y. Its position lam is where its near face crosses the
middle line x = W / 2. For N squares the length of the zone is the smallest lam at which they fit, and

  loss = c cos t * length - N

is what modules.py calls the loss of a far zone (a zone of flush stacks alone loses 0). One more flush stack adds
c squares and one pitch 1 / cos t and leaves the loss alone, so a zone serves the class N mod c.

Tools, all on the zone alone:
  exact     the smallest gap of a zone at a stack position (the lane's separating-axis test) and its length
  compact   the contact LP of modules.py on the zone (angles free in a trust region), repeated until it stops
  soft      an overlap energy on the zone's squares with the stack held at a position, minimised by L-BFGS;
            squeeze lowers the stack in steps while the energy still reaches zero
  moves     delete (beam over which square leaves), insert (a square in the largest pocket, the stack pushed out),
            row (rows of c - 1 uprights on the end wall under a known zone),
            hop (shake a neighbourhood, move one square to a pocket, snap angles to upright or to the flush tilt,
            change the kind of one square) and sweep (change the kind of every square in turn)
  taper     the far zones of the library are tapers: sub-stacks on the lattice of the flush stacks, and columns of
            uprights on the end wall under them. A dynamic programme over the slabs gives, for a stack position,
            the taper with the most squares, in closed form; the best taper of every count is then built and compacted

Our own code. Reads the library pickles of modules.py as data. Imports modules and methods_lp of this lane.
"""
import csv, glob, json, math, os, pickle, sys, time, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I drops the script dir
import numpy as np
from scipy.optimize import minimize
import modules as M
from methods_lp import best_axes, pair_list, half

SQ2 = math.sqrt(2)
CLEAR = 2.2e-11          # the clearance floatsafe asks of every pair
TOL = -2e-9              # a zone is legal when no gap is below this (modules.legal); a built layout is squeezed and certified
DELTA = 2e-5             # the gap the soft search asks for, so that its result is a legal start for the LP
EPS = 1e-13              # an overlap energy below this is zero


def geom(c, f):
    t = M.flush_tilt(c, f)
    return t, 1.0 / math.cos(t), c - 1 + f


def loss_of(c, f, count, length):
    return c * math.cos(M.flush_tilt(c, f)) * length - count


def mod_of(c, lean=-1):
    return dict(c=c, lean=lean, miss=[], rig=[])


# ----------------------------------------------------------------------------------------------- exact evaluator

def exact(P, c, f, lam, lean=-1):
    """Gaps of the zone P (x, y, degrees) with the stack face at lam.
    -> (smallest gap inside the zone and against the walls and the grid, smallest gap to the stack,
        squares whose centre lies beyond the stack)"""
    P = np.asarray(P, float); nz = len(P)
    S, mode = M.far_state(mod_of(c, lean), f, P, lam)
    pairs = pair_list(S, SQ2 + 1e-3)
    ma, mb = mode[pairs[:, 0]], mode[pairs[:, 1]]
    pairs = pairs[(ma == 0) | (mb == 0)]
    g_in = g_st = math.inf
    if len(pairs):
        g = best_axes(S, pairs)[0]
        st = (mode[pairs[:, 0]] == 1) | (mode[pairs[:, 1]] == 1)
        if st.any(): g_st = float(g[st].min())
        if (~st).any(): g_in = float(g[~st].min())
    h = half(S[:nz, 2])
    g_in = min(g_in, float((S[:nz, 0] - h).min()), float((S[:nz, 1] - h).min()))
    t, p, W = geom(c, f); a = lean * t
    beyond = int(((-math.sin(a) * (S[:nz, 0] - W / 2) + math.cos(a) * (S[:nz, 1] - (lam + p / 2))) > 0).sum())
    return g_in, g_st, beyond


def length(P, c, f, hi, lean=-1):
    """The length of a zone: the smallest stack position at which every gap inside is >= TOL and every gap to the
    stack is >= CLEAR, found below hi by bisection. -> (length, smallest gap inside) or None when hi is not legal."""
    g_in, g_st, b = exact(P, c, f, hi, lean)
    if g_in < TOL or g_st < CLEAR or b: return None
    lo = hi - 0.6
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        _, g_st, b = exact(P, c, f, mid, lean)
        if g_st >= CLEAR and not b: hi = mid
        else: lo = mid
    return hi, g_in


# ----------------------------------------------------------------------------------------------- the LP compactor

def compact(P, c, f, lam, lean=-1, rounds=4, turn=True):
    """The contact LP of modules.py on the zone alone, the stack sliding, repeated until it gains under 1e-9.
    -> (length, P) or None when the start is not legal and cannot be healed."""
    mod = mod_of(c, lean); out = None
    for _ in range(rounds):
        r = M.far_len(mod, f, P, lam + 1e-7, turn=turn)
        if r is None: break
        gain = lam - r[0]
        lam, P = r; out = (lam, P)
        if gain < 1e-9: break
    return out


# ----------------------------------------------------------------------------------------------- the soft search

def _hp(psi):
    return 0.5 * (-np.sign(np.cos(psi)) * np.sin(psi) + np.sign(np.sin(psi)) * np.cos(psi))


def soft_energy(v, nz, S, W, delta):
    """Sum of (delta - gap)^2 over every pair of squares closer than delta (zone and zone, zone and stack) and over
    the three walls x >= 0, x <= W, y >= 0, with its gradient in the zone's x, y, theta (radians)."""
    X = v.reshape(nz, 3)
    A = np.vstack([X, S]) if len(S) else X
    G = np.zeros_like(A)
    I, J = np.triu_indices(len(A), 1)
    keep = I < nz
    I, J = I[keep], J[keep]
    dx, dy = A[J, 0] - A[I, 0], A[J, 1] - A[I, 1]
    near = dx * dx + dy * dy < 2.05
    I, J, dx, dy = I[near], J[near], dx[near], dy[near]
    E = 0.0
    if len(I):
        best = np.full(len(I), -np.inf); own = np.zeros(len(I), int); PHI = np.zeros(len(I)); PSI = np.zeros(len(I))
        for o, (a, b, sg) in enumerate(((I, J, 1.0), (J, I, -1.0))):
            for k in range(4):
                phi = A[a, 2] + k * (math.pi / 2)
                psi = A[b, 2] - phi
                g = sg * (np.cos(phi) * dx + np.sin(phi) * dy) - 0.5 - 0.5 * (np.abs(np.cos(psi)) + np.abs(np.sin(psi)))
                m = g > best
                best[m] = g[m]; own[m] = o; PHI[m] = phi[m]; PSI[m] = psi[m]
        viol = delta - best
        m = viol > 0
        if m.any():
            E += float((viol[m] ** 2).sum())
            a = np.where(own[m] == 0, I[m], J[m]); b = np.where(own[m] == 0, J[m], I[m])
            sg = np.where(own[m] == 0, 1.0, -1.0)
            w = -2.0 * viol[m]                       # dE / dgap
            ux, uy = np.cos(PHI[m]), np.sin(PHI[m])
            hp = _hp(PSI[m])
            ddx, ddy = sg * dx[m], sg * dy[m]        # from the owner of the axis to the other square
            np.add.at(G, (b, 0), w * ux); np.add.at(G, (b, 1), w * uy)
            np.add.at(G, (a, 0), -w * ux); np.add.at(G, (a, 1), -w * uy)
            np.add.at(G, (a, 2), w * (-uy * ddx + ux * ddy + hp))
            np.add.at(G, (b, 2), -w * hp)
    th = X[:, 2]
    h = 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th))); dh = _hp(th)
    for gap, sx, col in ((X[:, 0] - h, 1.0, 0), (W - X[:, 0] - h, -1.0, 0), (X[:, 1] - h, 1.0, 1)):
        viol = delta - gap
        m = viol > 0
        if m.any():
            E += float((viol[m] ** 2).sum())
            w = -2.0 * viol[m]
            G[np.nonzero(m)[0], col] += w * sx
            G[np.nonzero(m)[0], 2] += -w * dh[m]
    return E, G[:nz].ravel()


def soft(P, c, f, lam, lean=-1, delta=DELTA, maxiter=200):
    """Minimise the overlap energy of the zone P (degrees) with the stack held at lam. -> (P, energy)"""
    t, p, W = geom(c, f)
    S = M.stack_squares(c, lean * math.degrees(t), W / 2, lam + p / 2); S[:, 2] = np.radians(S[:, 2])
    X = np.array(P, float); X[:, 2] = np.radians(X[:, 2]); nz = len(X)
    E0, _ = soft_energy(X.ravel(), nz, S, W, delta)
    if E0 <= EPS: return np.array(P, float), E0
    r = minimize(soft_energy, X.ravel(), args=(nz, S, W, delta), jac=True, method='L-BFGS-B',
                 options={'maxiter': maxiter, 'ftol': 1e-30, 'gtol': 1e-14})
    Q = r.x.reshape(nz, 3).copy(); Q[:, 2] = np.degrees(Q[:, 2])
    return Q, float(r.fun)


def squeeze(P, c, f, lam, lean=-1, step=0.08, out=0.05, tries=40):
    """Soft compaction. First push the stack out until the overlap energy reaches zero, then lower it in steps
    (halved on failure) while it still does. -> (P, lam) or None"""
    Q, E = soft(P, c, f, lam, lean)
    k = 0
    while E > EPS and k < tries:
        lam += out; k += 1
        Q, E = soft(Q, c, f, lam, lean)
    if E > EPS: return None
    P = Q
    while step > 2e-3:                               # the LP closes the rest
        Q, E = soft(P, c, f, lam - step, lean)
        if E <= EPS and exact(Q, c, f, lam - step, lean)[2] == 0: P = Q; lam -= step
        else: step *= 0.5
    return P, lam


def settle_zone(P, c, f, lam, lean=-1):
    """squeeze, then the LP. -> (length, P) or None. The result is legal by the exact test or it is dropped."""
    r = squeeze(P, c, f, lam, lean)
    if r is None: return None
    r2 = compact(r[0], c, f, r[1], lean)
    if r2 is None: return None
    le = length(r2[1], c, f, r2[0] + 1e-7, lean)
    if le is None: return None
    return le[0], r2[1]


# ----------------------------------------------------------------------------------------------- moves

def slab(P, c, f, lean=-1):
    """slab coordinate of every square: where the line through its centre, parallel to the stacks, crosses x = W / 2"""
    t, p, W = geom(c, f)
    return P[:, 1] - (P[:, 0] - W / 2) * math.tan(lean * t)


def add_stacks(P, c, f, lam, j, lean=-1):
    """the zone with j more flush stacks taken into it. -> (P, lam)"""
    t, p, W = geom(c, f)
    parts = [P] + [M.stack_squares(c, lean * math.degrees(t), W / 2, lam + (q + 0.5) * p) for q in range(j)]
    return np.vstack(parts), lam + j * p


def delete_beam(P, c, f, lam, d, beam=3, lean=-1, log=None):
    """Delete d squares one at a time. Each deletion is ranked by the length the fixed-angle LP reaches, ties by the
    slab coordinate (the square nearest the stack first); the best `beam` are compacted with free angles.
    -> [(length, P)] best first, for the last level"""
    mod = mod_of(c, lean)
    states = [(lam, P)]; peel = (lam, P)             # peel: the line that always deletes the square nearest the stack
    block = None                                     # block: the c squares nearest the stack taken out at once, one compaction
    if d >= c:
        Q = np.delete(P, np.argsort(-slab(P, c, f, lean))[:c], 0)
        block = compact(Q, c, f, lam, lean)
        if log: log('block of %d: %s' % (c, 'none' if block is None else '%.5f' % block[0]))
    for lev in range(d):
        nxt = []
        for lam0, P0 in states:
            sg = slab(P0, c, f, lean)
            for i in range(len(P0)):
                Q = np.delete(P0, i, 0)
                r = M.far_len(mod, f, Q, lam0 + 1e-7, turn=False)
                if r is not None: nxt.append((round(r[0], 5), -sg[i], r[0], r[1]))
        nxt.sort(key=lambda s: (s[0], s[1]))
        seen = set(); pick = []
        for s in nxt:
            key = (s[0], round(s[1], 3))
            if key in seen: continue
            seen.add(key); pick.append(s)
            if len(pick) >= beam: break
        states = []
        for s in pick:
            r = compact(s[3], c, f, s[2], lean)
            if r is not None: states.append(r)
        if peel is not None:
            Q = np.delete(peel[1], int(np.argmax(slab(peel[1], c, f, lean))), 0)
            peel = compact(Q, c, f, peel[0], lean)
            if peel is not None: states.append(peel)
        if lev == c - 1 and block is not None: states.append(block)
        states.sort(key=lambda s: s[0])
        if log: log('delete level %d: %s' % (lev + 1, ' '.join('%.5f' % s[0] for s in states)))
        if not states: return []
    return states


def pockets(P, c, f, lam, lean=-1, top=3, step=0.1):
    """Places for one more square: centres on a grid, upright or at the flush tilt, ranked by the smallest gap to
    everything there (the least overlap first). -> [(gap, x, y, angle in degrees)]"""
    t, p, W = geom(c, f)
    S = M.stack_squares(c, lean * math.degrees(t), W / 2, lam + p / 2)
    A = np.vstack([P, S]); A = np.c_[A[:, 0], A[:, 1], np.radians(A[:, 2])]
    xs = np.arange(0.5, W - 0.5 + 1e-9, step); ys = np.arange(0.5, lam + 0.5 * W * math.tan(t) + 0.3, step)
    out = []
    for ang in (0.0, lean * t):
        hh = 0.5 * (abs(math.cos(ang)) + abs(math.sin(ang)))
        gx, gy = np.meshgrid(xs, ys); gx, gy = gx.ravel(), gy.ravel()
        ok = (gx - hh >= 0) & (gx + hh <= W) & (gy - hh >= 0)
        ok &= (-math.sin(lean * t) * (gx - W / 2) + math.cos(lean * t) * (gy - (lam + p / 2))) < -0.8   # this side of the stack
        gx, gy = gx[ok], gy[ok]
        dx = A[None, :, 0] - gx[:, None]; dy = A[None, :, 1] - gy[:, None]
        best = np.full(dx.shape, -np.inf)
        for k in range(4):
            phi = ang + k * math.pi / 2
            g = math.cos(phi) * dx + math.sin(phi) * dy - 0.5 - 0.5 * (np.abs(np.cos(A[None, :, 2] - phi)) + np.abs(np.sin(A[None, :, 2] - phi)))
            best = np.maximum(best, g)
            phi2 = A[None, :, 2] + k * math.pi / 2
            g = -(np.cos(phi2) * dx + np.sin(phi2) * dy) - 0.5 - 0.5 * (np.abs(np.cos(ang - phi2)) + np.abs(np.sin(ang - phi2)))
            best = np.maximum(best, g)
        gmin = best.min(axis=1)
        for q in np.argsort(-gmin)[:top * 6]: out.append((float(gmin[q]), float(gx[q]), float(gy[q]), math.degrees(ang)))
    out.sort(key=lambda r: -r[0])
    pick = []
    for r in out:                                    # places that are not the same pocket
        if all((r[1] - q[1]) ** 2 + (r[2] - q[2]) ** 2 > 0.6 for q in pick): pick.append(r)
        if len(pick) >= top: break
    return pick


def insert(P, c, f, lam, lean=-1, top=3):
    """One more square in each of the largest pockets, the stack pushed out as little as the soft search needs.
    -> [(length, P)] best first"""
    res = []
    for g, x, y, a in pockets(P, c, f, lam, lean, top):
        Q = np.vstack([P, [[x, y, a]]])
        r = settle_zone(Q, c, f, lam + min(0.3, max(0.02, -g * 0.5)), lean)
        if r is not None: res.append(r)
    res.sort(key=lambda s: s[0])
    return res


def hop(P, c, f, lam, rng, lean=-1, kind=None):
    """One perturbed copy of the zone. shake: a square and its neighbours move by up to 0.15 and turn by up to 6
    degrees. reloc: one square leaves and returns in the largest pocket. snap: the squares of a neighbourhood take
    the nearer of upright and the flush tilt. flip: one square takes the farther of the two.
    -> (P, start position of the stack, kind)"""
    t, p, W = geom(c, f); ft = lean * math.degrees(t)
    kind = kind or rng.choice(['shake', 'shake', 'reloc', 'snap', 'flip', 'flip'])
    Q = P.copy(); n = len(Q)
    i = int(rng.integers(n))
    near = np.nonzero((Q[:, 0] - Q[i, 0]) ** 2 + (Q[:, 1] - Q[i, 1]) ** 2 < rng.choice([1.3, 2.0, 3.0]) ** 2)[0]
    if kind == 'shake':
        Q[near, :2] += rng.uniform(-0.15, 0.15, (len(near), 2)); Q[near, 2] += rng.uniform(-6, 6, len(near))
        return Q, lam + 0.1, kind
    if kind == 'snap':
        a = ((Q[near, 2] + 45) % 90) - 45
        Q[near, 2] = np.where(np.abs(a) < np.abs(a - ft), 0.0, ft)
        return Q, lam + 0.05, kind
    if kind == 'flip':                               # one square (or two neighbours) changes kind: upright <-> flush tilt
        for q in ([i] if rng.random() < 0.6 else list(near[:2])):
            a = ((Q[q, 2] + 45) % 90) - 45
            Q[q, 2] = ft if abs(a) < abs(a - ft) else 0.0
        return Q, lam + 0.12, kind
    Q = np.delete(Q, i, 0)
    pk = pockets(Q, c, f, lam, lean, top=3)
    pk = [r for r in pk if (r[1] - P[i, 0]) ** 2 + (r[2] - P[i, 1]) ** 2 > 0.5] or pk
    g, x, y, a = pk[int(rng.integers(len(pk)))]
    return np.vstack([Q, [[x, y, a]]]), lam + min(0.3, max(0.02, -g * 0.5)), kind


def snap_all(P, c, f, lean=-1):
    """every square at the nearer of upright and the flush tilt"""
    ft = lean * math.degrees(geom(c, f)[0])
    Q = P.copy(); a = ((Q[:, 2] + 45) % 90) - 45
    Q[:, 2] = np.where(np.abs(a) < np.abs(a - ft), 0.0, ft)
    return Q


def sweep(P, c, f, lam, lean=-1, log=None, until=None, stop=None):
    """A zone is a mixture of two kinds of square, upright and at the flush tilt. Change the kind of one square at
    a time (every square in turn), squeeze and compact, and keep each change that shortens the zone; repeat until
    a whole pass gains nothing. -> (length, P, changes kept)"""
    ft = lean * math.degrees(geom(c, f)[0]); kept = 0; again = True
    while again:
        again = False
        for i in np.argsort(-slab(P, c, f, lean)):
            if until is not None and time.time() > until: return lam, P, kept
            if stop is not None and lam <= stop: return lam, P, kept
            Q = P.copy(); a = ((Q[i, 2] + 45) % 90) - 45
            Q[i, 2] = ft if abs(a) < abs(a - ft) else 0.0
            r = settle_zone(Q, c, f, lam + 0.12, lean)
            if r is not None and r[0] < lam - 1e-7:
                lam, P = r; kept += 1; again = True
                if log: log('sweep: square %d changes kind, %.6f' % (i, lam))
    return lam, P, kept


def hops(P, c, f, lam, seconds, rng, lean=-1, temp=0.01, log=None, stop=None):
    """Basin hopping on the zone alone: hop, squeeze, LP; a longer zone is taken with probability exp(-d / temp).
    A sweep over the kinds runs first and again after every 60 hops that found a shorter zone.
    -> (length, P, hops tried, kinds that improved the best)"""
    t0 = time.time(); k = 0; won = collections.Counter()
    l, P, kept = sweep(P, c, f, lam, lean, log, until=t0 + seconds, stop=stop)
    if kept: won['sweep'] += kept
    best = cur = (l, P); swept = l
    while time.time() - t0 < seconds:
        if stop is not None and best[0] <= stop: break
        if k and k % 60 == 0 and best[0] < swept - 1e-7:
            l, P, kept = sweep(best[1], c, f, best[0], lean, log, until=t0 + seconds, stop=stop)
            if kept: won['sweep'] += kept; best = (l, P)
            cur = best; swept = best[0]
        Q, l0, kind = hop(cur[1], c, f, cur[0], rng, lean)
        r = settle_zone(Q, c, f, l0, lean); k += 1
        if r is None: continue
        d = r[0] - cur[0]
        if d < -1e-8 or rng.random() < math.exp(-max(d, 0.0) / temp): cur = r
        if r[0] < best[0] - 1e-8:
            best = r; won[kind] += 1
            if log: log('hop %d (%s) %.6f' % (k, kind, r[0]))
        if k % 25 == 0 and cur[0] > best[0] + 5 * temp: cur = best
    return best[0], best[1], k, dict(won)


def shaken(P, c, f, lam, rng, move=0.2, turn=10.0, lean=-1):
    """the control's start: every square moved by up to `move` and turned by up to `turn` degrees, then the stack
    pushed out until the soft search finds a legal zone. -> (P, lam) or None"""
    S = P.copy()
    S[:, :2] += rng.uniform(-move, move, (len(S), 2)); S[:, 2] += rng.uniform(-turn, turn, len(S))
    for stretch in (1.0, 1.15, 1.3, 1.5, 1.8):       # when pushing the stack alone leaves a jam, the rows are spread too
        Q = S.copy(); Q[:, 1] *= stretch; l = lam * stretch
        Q, E = soft(Q, c, f, l, lean)
        k = 0
        while E > EPS and k < 30:
            l += 0.05; k += 1
            Q, E = soft(Q, c, f, l, lean)
        if E <= EPS: return Q, l
    return None


# ----------------------------------------------------------------------------------------------- modules

def signature(P, c, f, lean=-1):
    """the same words as modules.py: sub-stacks at the arm's tilt by slab, leaning singles, uprights"""
    from frontier_stacks import stacks
    t, p, W = geom(c, f); ft = lean * math.degrees(t)
    tilted = np.nonzero(np.abs(P[:, 2]) > 0.5)[0]
    chains = [[int(tilted[i]) for i in ch] for ch in stacks(P[tilted])[0]] if len(tilted) else []
    def rigid(tol):
        groups = []; used = set()
        for ch in chains:
            if len(ch) < 2 or float(np.abs(P[ch, 2] - ft).max()) > tol: continue
            ax = P[ch[-1], :2] - P[ch[0], :2]
            if abs(ax[0]) <= abs(ax[1]): continue
            groups.append(list(ch)); used.update(ch)
        for i in range(len(P)):
            if i not in used and abs(P[i, 2] - ft) < min(tol, 0.05): groups.append([i]); used.add(i)
        return groups
    rig = rigid(0.35)
    grp = np.zeros(len(P), int); by = collections.defaultdict(list)
    sg = slab(P, c, f, lean); top = float(sg.max()) + 0.5 * p if len(P) else 0.0
    for g in rig:
        grp[g] = 1
        by[int(round((top - float(np.mean(sg[g]))) / p + 0.5))].append(len(g))
    taper = '.'.join('+'.join(map(str, sorted(by[q], reverse=True))) if q in by else '0' for q in range(1, max(by) + 1)) if by else '-'
    loose = int(((np.abs(P[:, 2]) > 0.5) & (grp == 0)).sum()); up = int((np.abs(P[:, 2]) <= 0.5).sum())
    return 'c%d:%s|l%d|u%d' % (c, taper, loose, up), grp, rigid(M.EXACT)


def as_module(P, c, f, lam, name, how, base):
    """A kept zone with the fields of a far module of modules.py (source 'zone_search.py'; the zone it was made
    from gives the licence and is named in the source)."""
    sig, grp, rig = signature(P, c, f)
    t = M.flush_tilt(c, f)
    return dict(n=0, m=0, k=0, f0=float(f), tag='z', kind='far', arm=1, c=c, lean=-1, P=np.array(P, float), grp=grp, rig=rig,
                miss=[], count=len(P), len0=float(lam), loss0=loss_of(c, f, len(P), lam), tilt0=math.degrees(t), sig=sig,
                id=name, how=how, src='zone_search.py: %s, from far zone %s <%s>' % (how, base['id'], base['src']),
                licence=base['licence'])


def rows_of(P):
    """a row listing of a zone: squares by row of y, each as x:angle"""
    o = np.lexsort((P[:, 0], np.round(P[:, 1])))
    by = collections.defaultdict(list)
    for i in o: by[int(round(P[i, 1]))].append('%.2f,%.2f:%+.0f' % (P[i, 0], P[i, 1], P[i, 2]))
    return ['y~%d  ' % r + '  '.join(by[r]) for r in sorted(by)]


def picture(P, c, f, lam, path, title=''):
    """svg of a zone: dark, uprights grey, squares at the flush tilt blue, others orange, the stack outlined"""
    t, p, W = geom(c, f); ft = -math.degrees(t)
    S = M.stack_squares(c, ft, W / 2, lam + p / 2)
    top = lam + 0.5 * W * math.tan(t) + 1.3; sc = 46.0
    def poly(x, y, a, fill, stroke):
        a = math.radians(a); co, si = math.cos(a), math.sin(a)
        pts = [(x + 0.5 * (sx * co - sy * si), y + 0.5 * (sx * si + sy * co)) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        return '<polygon points="%s" fill="%s" stroke="%s" stroke-width="1"/>' % (' '.join('%.2f,%.2f' % (10 + q[0] * sc, 30 + (top - q[1]) * sc) for q in pts), fill, stroke)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" style="background:#111">' % (20 + (W + 1) * sc, 40 + top * sc),
           '<text x="10" y="18" fill="#ddd" font-family="monospace" font-size="12">%s</text>' % title,
           '<rect x="10" y="30" width="%.2f" height="%.2f" fill="none" stroke="#666"/>' % (W * sc, top * sc)]
    for x, y, a in S: out.append(poly(x, y, a, 'none', '#888'))
    for x, y, a in P:
        col = '#555' if abs(a) < 0.5 else '#3b78c4' if abs(a - ft) < 0.35 else '#c9822b'
        out.append(poly(x, y, a, col, '#111'))
    out.append('</svg>')
    open(path, 'w').write('\n'.join(out))


# ----------------------------------------------------------------------------------------------- taper enumeration

def taper_sites(c, f, lam):
    """Options of every slab under the flush stack at lam, on the lattice of the flush stacks (lean -1).
    Slab j is the flush stack moved j pitches towards the end wall; an option is a run of slots a..b, moved along
    the stack by a (1 - cos t) so that it clears a upright columns on the wall side. Columns: c - 1 on the wall side
    (x from i to i + 1) and c - 1 on the grid side (x from W - 1 - i to W - i). -> [slab][(a, b, squares, cap of each
    of the 2 (c - 1) columns)], slab 0 being the flush stack itself."""
    t, p, W = geom(c, f); ct, st, tt = math.cos(t), math.sin(t), math.tan(t)
    h = 0.5 * (ct + st); d = 0.5 * (ct - st)
    x0 = np.r_[np.arange(c - 1), W - 1 - np.arange(c - 1)]          # left edges of the 2 (c - 1) columns
    def cap(cx, cy):
        """lowest point of each square over each column (inf when they do not share x). cx, cy: arrays of centres"""
        Lx, Ly, Bx, By, Rx = cx - h, cy - d, cx + d, cy - h, cx + h
        lo = np.maximum(x0[None, :], Lx[:, None]); hi = np.minimum(x0[None, :] + 1, Rx[:, None])
        over = hi - lo > 1e-9
        yl = np.where(hi <= Bx[:, None], Ly[:, None] - (hi - Lx[:, None]) * tt,
                      np.where(lo >= Bx[:, None], By[:, None] + (lo - Bx[:, None]) / tt, By[:, None]))
        return np.where(over, yl, np.inf)
    out = []
    j = 0
    while True:
        cy0 = lam + p / 2 - j * p
        opts = []
        if j == 0:
            s = np.arange(c); cx = W / 2 + (s - (c - 1) / 2) * ct; cy = cy0 - (s - (c - 1) / 2) * st
            opts.append((0, c - 1, np.c_[cx, cy], cap(cx, cy).min(0)))
        else:
            opts.append((0, -1, np.zeros((0, 2)), np.full(len(x0), np.inf)))
            for a in range(0, 4):
                sh = a * (1 - ct) / ct + (1e-6 if a else 0.0)       # along the stack, so that its wall-side corner is at x = a
                for b in range(a, c):
                    s = np.arange(a, b + 1)
                    cx = W / 2 + (s - (c - 1) / 2) * ct + sh * ct; cy = cy0 - (s - (c - 1) / 2) * st - sh * st
                    if (cy - h).min() < 1e-9 or (cx + h).max() > W + 1e-9: continue
                    opts.append((a, b, np.c_[cx, cy], cap(cx, cy).min(0)))
            if len(opts) == 1: break
        out.append(opts); j += 1
    return out


def taper_best(c, f, lam):
    """The largest count of the lattice designs at lam. -> (count, runs [(a, b)], squares x, y, degrees)"""
    t, p, W = geom(c, f)
    S = taper_sites(c, f, lam)
    fl = lambda v: np.where(np.isinf(v), 9, np.clip(np.floor(np.minimum(v, 8.0) + 1e-9), 0, 8)).astype(np.int64)
    caps = fl(S[0][0][3])[None, :]; cnt = np.zeros(1, int); idx = [np.zeros(1, int)]
    pw = 10 ** np.arange(caps.shape[1], dtype=np.int64)
    for opts in S[1:]:
        oc = fl(np.array([o[3] for o in opts])); on = np.array([o[1] - o[0] + 1 for o in opts])
        k = len(cnt)
        caps = np.minimum(caps[:, None, :], oc[None, :, :]).reshape(-1, caps.shape[1])
        cnt = (cnt[:, None] + on[None, :]).ravel()
        idx = [np.repeat(q, len(opts)) for q in idx] + [np.tile(np.arange(len(opts)), k)]
        key = caps @ pw                              # the dynamic programme: of the partial tapers that leave the same
        o = np.lexsort((-cnt, key))                  # column heights, only the one with the most squares goes on
        first = np.r_[True, key[o][1:] != key[o][:-1]]
        sel = o[first]
        caps, cnt, idx = caps[sel], cnt[sel], [q[sel] for q in idx]
    hts = np.where(caps >= 9, 0, caps)               # a column with nothing above it up to the stack does not exist
    m = c - 1
    best = None
    for kl in range(m + 1):
        tot = cnt + hts[:, :kl].sum(1) + hts[:, m:m + (m - kl)].sum(1)
        q = int(np.argmax(tot))
        if best is None or tot[q] > best[0]: best = (int(tot[q]), q, kl)
    N, q, kl = best
    runs = []; sq = []
    for jj, opts in enumerate(S[1:]):
        o = opts[int(idx[jj + 1][q])]; runs.append((o[0], o[1]))
        sq += [(x, y, -math.degrees(t)) for x, y in o[2]]
    for i in range(kl): sq += [(i + 0.5, 0.5 + r, 0.0) for r in range(hts[q, i])]
    for i in range(m - kl): sq += [(W - 0.5 - i, 0.5 + r, 0.0) for r in range(hts[q, m + i])]
    return N, runs, np.array(sq), (kl, [int(v) for v in hts[q, :kl]], [int(v) for v in hts[q, m:m + m - kl]])


def cmd_taper(a):
    """zone_search.py taper C F OUTDIR LO HI [STEP]   enumerate the lattice tapers for stack positions LO..HI: for
    every count the smallest position at which some taper holds it, then built as squares and compacted."""
    c, f, outdir, lo, hi = int(a[0]), float(a[1]), a[2], float(a[3]), float(a[4])
    step = float(a[5]) if len(a) > 5 else 0.002
    first = {}
    t0 = time.time(); prev = 0
    for lam in np.arange(lo, hi + 1e-9, step):
        N, runs, sq, up = taper_best(c, f, float(lam))
        for n in range(prev + 1, N + 1): first.setdefault(n, (float(lam), runs, sq, up, N))
        prev = max(prev, N)
    print('enumerated in %.0f s' % (time.time() - t0), flush=True)
    base = dict(id='lattice taper', src='zone_search.py taper enumeration (our own design)', licence='our own')
    for n in sorted(first):
        lam, runs, sq, up, N = first[n]
        if N != n or lam <= lo + 1e-9: continue                    # counts the lattice jumps over have no design of their own
        g = exact(sq, c, f, lam + 0.004)
        line = 'count %d class %d: lattice position %.4f (loss %.3f) runs %s uprights wall side %s grid side %s' % (
            n, n % c, lam, loss_of(c, f, n, lam), '.'.join('%d-%d' % r if r[1] >= r[0] else '0' for r in runs), up[1], up[2])
        r = settle_zone(sq, c, f, lam + 0.004)
        if r is None: print(line + ' | not built (gap %.1e)' % min(g[0], g[1]), flush=True); continue
        print(line + ' | built %.6f loss %.4f' % (r[0], loss_of(c, f, n, r[0])), flush=True)
        _save(outdir, 'zone-%d-s900' % n, dict(lam=r[0], gap=0.0, P=r[1], how='taper enumeration', base=base, c=c, f=f, count=n, seed=900, cpu=0.0))
    return 0


# ----------------------------------------------------------------------------------------------- commands

def cmd_classes(a):
    """Loss against count class, ours and the board, as if every layout had two arms of 8 (n from LO to HI)."""
    details, board = a[0], a[1]
    lo, hi = (int(a[2]), int(a[3])) if len(a) > 3 else (620, 1000)
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    brd = {int(r['n']): float(r['L']) for r in json.load(open(board))}
    bands = ((0.90, 0.94), (0.94, 0.97), (0.97, 1.0))
    cell = collections.defaultdict(list)
    for n in range(lo, hi + 1):
        m = math.isqrt(n - 1); k = n - m * m; fb = brd[n] - m; fo = held[n] - m
        for q, (b0, b1) in enumerate(bands):
            if b0 <= fb < min(b1, 1 - 1e-9):
                cell[((k - 2 * m - 1) % 8, q)].append((M.k_flush(m, fb, 8, 8) - k, M.k_flush(m, min(fo, 1.0), 8, 8) - k, n, fb, fo))
    print('class\t' + '\t'.join('board f %.2f-%.2f: n, board loss, our loss' % b for b in bands))
    for cl in range(8):
        cs = []
        for q in range(len(bands)):
            v = cell[(cl, q)]
            cs.append('-' if not v else '%d, %.2f, %.2f' % (len(v), np.median([x[0] for x in v]), np.median([x[1] for x in v])))
        print('%d\t' % cl + '\t'.join(cs))
    for q, b in enumerate(bands):
        v = [np.median([x[0] for x in cell[(cl, q)]]) for cl in range(8) if cell[(cl, q)]]
        w = [np.median([x[1] for x in cell[(cl, q)]]) for cl in range(8) if cell[(cl, q)]]
        print('band %.2f-%.2f: board loss by class from %.2f to %.2f (spread %.2f); ours from %.2f to %.2f (spread %.2f)' % (
            b[0], b[1], min(v), max(v), max(v) - min(v), min(w), max(w), max(w) - min(w)))
    return 0


def cmd_base(a):
    """The library's far zones of a c-arm carried to F by modules.far_at: the start states of a search."""
    work, out, f = a[0], a[1], float(a[2]); c = int(a[3]) if len(a) > 3 else 8
    lib = pickle.load(open(work + '/library.pkl', 'rb'))
    res = []
    for q in lib['mods']:
        if q['kind'] != 'far' or q['c'] != c or q['miss'] or abs(q['f0'] - f) > 0.04: continue
        if not (q['tag'] == 'h' or any(k in q['licence'] for k in M.OK_LICENCE)): continue
        at = M.far_at(q, f)
        if at is None: continue
        lam, P = at
        if q['lean'] != -1: P = np.c_[c - 1 + f - P[:, 0], P[:, 1], -P[:, 2]]
        r = compact(P, c, f, lam)
        if r is None: continue
        le = length(r[1], c, f, r[0] + 1e-7)
        if le is None: continue
        res.append(dict(id=q['id'], src=q['src'], licence=q['licence'], sig=q['sig'], count=q['count'], c=c, f=f, lam=le[0], P=r[1]))
        print('%s %s count %d length %.6f loss %.4f' % (q['id'], q['sig'], q['count'], le[0], loss_of(c, f, q['count'], le[0])), flush=True)
    pickle.dump(res, open(out, 'wb'))
    return 0


def _best_base(base, count):
    v = [b for b in base if b['count'] == count]
    return min(v, key=lambda b: b['lam']) if v else None


def _save(outdir, name, rec):
    os.makedirs(outdir, exist_ok=True)
    tmp = '%s/%s.pkl.tmp' % (outdir, name)
    pickle.dump(rec, open(tmp, 'wb')); os.replace(tmp, '%s/%s.pkl' % (outdir, name))


def _opt(a, key, default, cast=float):
    return cast(a[a.index(key) + 1]) if key in a else default


def cmd_control(a):
    """Find a library zone again: (A) from the zone with every square shaken; (B) from the next library zone of
    the same class (count + c), by deleting c squares. Pass: the library length within 1e-4."""
    base = pickle.load(open(a[0], 'rb')); outdir = a[1]
    seed = _opt(a, '--seed', 1, int); minutes = _opt(a, '--minutes', 8.0); which = _opt(a, '--part', 'AB', str)
    rng = np.random.default_rng(seed)
    c, f = base[0]['c'], base[0]['f']
    counts = sorted(set(b['count'] for b in base))
    n0 = _opt(a, '--count', counts[0], int)
    ref = _best_base(base, n0)
    log = lambda s: print('[control seed %d] %s' % (seed, s), flush=True)
    log('library zone %s count %d f %.3f length %.6f loss %.4f' % (ref['id'], n0, f, ref['lam'], loss_of(c, f, n0, ref['lam'])))
    out = dict(ref=ref['lam'], id=ref['id'], seed=seed)
    if 'A' in which:
        st = shaken(ref['P'], c, f, ref['lam'], rng)
        if st is None: log('A: no legal start'); out['A'] = None
        else:
            log('A: shaken start legal with the stack at %.4f' % st[1])
            r = settle_zone(st[0], c, f, st[1])
            log('A: after squeeze and LP %.6f (library %+.2e)' % (r[0], r[0] - ref['lam']))
            r2 = settle_zone(snap_all(st[0], c, f), c, f, st[1])
            if r2 is not None:
                log('A: with every angle snapped first %.6f (library %+.2e)' % (r2[0], r2[0] - ref['lam']))
                if r2[0] < r[0]: r = r2
            t0 = time.time()
            l, P, k, won = hops(r[1], c, f, r[0], minutes * 60, rng, log=log, stop=ref['lam'] + 1e-5)
            log('A: after %d hops in %.0f s: %.6f, library %.6f, difference %+.2e (%s) %s' % (
                k, time.time() - t0, l, ref['lam'], l - ref['lam'], 'PASS' if l - ref['lam'] < 1e-4 else 'FAIL', won))
            out['A'] = (l, P, k)
    if 'B' in which:
        nxt = None if '--plus-stack' in a else _best_base(base, n0 + c)     # --plus-stack: the zone with one more flush stack
        if nxt is None:
            P1, l1 = add_stacks(ref['P'], c, f, ref['lam'], 1); nid = ref['id'] + ' + 1 stack'
        else: P1, l1, nid = nxt['P'], nxt['lam'], nxt['id']
        log('B: from %s count %d length %.6f' % (nid, len(P1), l1))
        t0 = time.time()
        st = delete_beam(P1, c, f, l1, c, beam=_opt(a, '--beam', 2, int), log=log)
        if not st: log('B: the beam died'); out['B'] = None
        else:
            l, P = st[0]
            log('B: after %d deletions %.6f (library %+.2e), %.0f s' % (c, l, l - ref['lam'], time.time() - t0))
            k = 0; won = {}
            if l - ref['lam'] >= 1e-4:
                l, P, k, won = hops(P, c, f, l, minutes * 60, rng, log=log, stop=ref['lam'] + 1e-5)
            log('B: final %.6f, library %.6f, difference %+.2e (%s) after %d hops %s' % (l, ref['lam'], l - ref['lam'], 'PASS' if l - ref['lam'] < 1e-4 else 'FAIL', k, won))
            out['B'] = (l, P, k)
    _save(outdir, 'control-%d-%s' % (seed, which), out)
    return 0


def cmd_search(a):
    """Search the zone of one count at the f of BASE.pkl. Starts: delete from the library zones above the count,
    insert into the ones below. Then basin hopping from the best. Every improvement is saved."""
    base = pickle.load(open(a[0], 'rb')); outdir = a[1]
    N = _opt(a, '--count', None, int); minutes = _opt(a, '--minutes', 20.0); seed = _opt(a, '--seed', 1, int)
    moves = _opt(a, '--moves', 'delete,row,insert,hop', str).split(',')
    dl = _opt(a, '--deadline', None, str)
    rng = np.random.default_rng(seed)
    c, f = base[0]['c'], base[0]['f']
    t0 = time.time(); cpu0 = time.process_time()
    left = lambda: min(minutes * 60 - (time.time() - t0), (float(open(dl).read().strip()) - time.time()) if dl and os.path.exists(dl) else 1e9)
    log = lambda s: print('[N=%d seed %d %.0fs] %s' % (N, seed, time.time() - t0, s), flush=True)
    counts = sorted(set(b['count'] for b in base))
    best = None; found = []
    def keep(l, P, how, b):
        nonlocal best
        le = length(P, c, f, l + 1e-7)
        if le is None or len(P) != N: return
        found.append((le[0], how))
        if best is None or le[0] < best['lam'] - 1e-9:
            best = dict(lam=le[0], gap=le[1], P=P, how=how, base=dict(id=b['id'], src=b['src'], licence=b['licence']), c=c, f=f, count=N,
                        seed=seed, cpu=time.process_time() - cpu0)
            _save(outdir, 'zone-%d-s%d' % (N, seed), best)
            log('BEST %.6f loss %.4f by %s from %s' % (le[0], loss_of(c, f, N, le[0]), how, b['id']))
    if 'resume' in moves:                            # go on from the best zone of this count that OUTDIR holds
        for q in glob.glob('%s/zone-%d-s*.pkl' % (outdir, N)):
            r = pickle.load(open(q, 'rb'))
            if abs(r['f'] - f) < 1e-9 and r['c'] == c: keep(r['lam'], r['P'], r['how'], r['base'])
    if 'delete' in moves:
        for n1 in counts + [counts[-1] + c]:
            d = n1 - N
            if not 0 < d <= 6 or left() < 60: continue
            b = _best_base(base, n1)
            if b is None:
                b = _best_base(base, n1 - c); P1, l1 = add_stacks(b['P'], c, f, b['lam'], 1)
            else: P1, l1 = b['P'], b['lam']
            st = delete_beam(P1, c, f, l1, d, beam=3, log=log)
            for l, P in st[:1]: keep(l, P, 'delete %d from count %d' % (d, n1), b)
    if 'row' in moves:                               # r rows of c - 1 uprights on the end wall under a library zone
        for n1 in counts:
            r = (N - n1) // (c - 1)
            if (N - n1) % (c - 1) or not 0 < r <= 3: continue
            b = _best_base(base, n1)
            rows = np.array([(0.5 + i, 0.5 + q, 0.0) for q in range(r) for i in range(c - 1)])
            P1 = np.vstack([b['P'] + np.array([0.0, float(r), 0.0]), rows])
            st = compact(P1, c, f, b['lam'] + r)
            if st is not None: keep(st[0], st[1], '%d rows of %d uprights under count %d' % (r, c - 1, n1), b)
    if 'insert' in moves:
        for n1 in counts:
            d = N - n1
            if not 0 < d <= 4 or left() < 60: continue
            b = _best_base(base, n1)
            st = [(b['lam'], b['P'])]
            for q in range(d):
                nx = []
                for l, P in st[:2]: nx += insert(P, c, f, l)
                nx.sort(key=lambda s: s[0]); st = nx[:3]
                log('insert %d into count %d: %s' % (q + 1, n1, ' '.join('%.5f' % s[0] for s in st)))
                if not st: break
            for l, P in st[:1]: keep(l, P, 'insert %d into count %d' % (d, n1), b)
    if 'hop' in moves and best is not None:
        while left() > 30:
            b0 = best
            l, P, k, won = hops(b0['P'], c, f, b0['lam'], min(left() - 5, 240), rng, log=None)
            log('hops %d from %.6f: %.6f %s' % (k, b0['lam'], l, won))
            if l < b0['lam'] - 1e-9:
                keep(l, P, b0['how'].split(', then')[0] + ', then hops (%s)' % '+'.join(sorted(won)), b0['base'])
    if best is not None:
        best['cpu'] = time.process_time() - cpu0; best['found'] = found
        _save(outdir, 'zone-%d-s%d' % (N, seed), best)
        log('DONE count %d class %d length %.6f loss %.4f how %s cpu %.0f s' % (N, N % c, best['lam'], loss_of(c, f, N, best['lam']), best['how'], best['cpu']))
    else: log('DONE nothing found')
    return 0


def cmd_table(a):
    """The best zone of every count in OUTDIR: a module file each (zones/), a picture, and one table."""
    outdir, tsv, work = a[0], a[1], a[2]
    recs = collections.defaultdict(list)
    for p in sorted(glob.glob(outdir + '/zone-*.pkl') + glob.glob(outdir + '/f*/zone-*.pkl')):
        r = pickle.load(open(p, 'rb')); recs[(r['c'], round(r['f'], 4), r['count'])].append(r)
    zdir = outdir + '/zones'; os.makedirs(zdir, exist_ok=True)
    lines = ['kind\tc\tf\tcount\tclass\tlength\tloss\thow found\tfile\n']; mods = []
    for (c, f, n) in sorted(recs):
        r = min(recs[(c, f, n)], key=lambda r: r['lam'])
        cpu = sum(q.get('cpu', 0.0) for q in recs[(c, f, n)])
        name = 'z%d-%df%03d' % (c, n, round(f * 1000))
        mod = as_module(r['P'], c, f, r['lam'], name + '.F1', r['how'], r['base'])
        pickle.dump(mod, open('%s/%s.pkl' % (zdir, name), 'wb')); mods.append(mod)
        picture(r['P'], c, f, r['lam'], '%s/%s.svg' % (zdir, name), '%s  count %d  class %d  length %.5f  loss %.3f' % (name, n, n % c, r['lam'], mod['loss0']))
        with open('%s/%s.txt' % (zdir, name), 'w') as h:
            h.write('%s count %d class %d f %.3f length %.6f loss %.4f %s\n%s\n' % (name, n, n % c, f, r['lam'], mod['loss0'], mod['sig'], '\n'.join(rows_of(r['P']))))
        lines.append('far\t%d\t%.3f\t%d\t%d\t%.6f\t%.4f\t%s; %d runs, %.0f CPU-s\t%s\n' % (c, f, n, n % c, r['lam'], mod['loss0'], r['how'], len(recs[(c, f, n)]), cpu, 'zones/%s.pkl' % name))
        print(lines[-1].strip())
    open(tsv, 'w').writelines(lines)
    pickle.dump(mods, open(zdir + '/zones.pkl', 'wb'))
    return 0


def cmd_merge(a):
    """zone_search.py merge LIBWORK OUTDIR NEWWORK [--span 0.05] [--max-loss 4.2] [--above 1.0] [--f F,F,...] [--c C,C]
    library.pkl and lens.pkl of modules.py with the kept zones added (lengths tabulated by modules.tabulate within
    --span of the f a zone was found at)."""
    work, outdir, new = a[0], a[1], a[2]
    M.SPAN = _opt(a, '--span', 0.05); cut = _opt(a, '--max-loss', 4.2)
    lib = pickle.load(open(work + '/library.pkl', 'rb')); lens = pickle.load(open(work + '/lens.pkl', 'rb'))
    mods = pickle.load(open(outdir + '/zones/zones.pkl', 'rb'))
    best = {}
    for q in mods:                                   # one zone for each f and class: the lowest loss
        key = (q['c'], round(q['f0'], 4), q['count'] % q['c'])
        if q['loss0'] <= cut and (key not in best or q['loss0'] < best[key]['loss0'] - 1e-6): best[key] = q
    os.makedirs(new, exist_ok=True)
    above = _opt(a, '--above', 1.0)                  # per f: skip the cheapest class (the library has it) and the costly ones
    low = collections.defaultdict(lambda: 9e9)
    for key, q in best.items(): low[key[:2]] = min(low[key[:2]], q['loss0'])
    fs = [float(v) for v in _opt(a, '--f', '', str).split(',') if v]     # only the zones made at these f
    cs = [int(v) for v in _opt(a, '--c', '', str).split(',') if v]       # only the zones of these stack sizes
    for key in sorted(best):
        q = best[key]
        if not low[key[:2]] + 1e-6 < q['loss0'] <= low[key[:2]] + above: continue
        if fs and not any(abs(key[1] - v) < 1e-6 for v in fs): continue
        if cs and key[0] not in cs: continue
        t = M.tabulate(q)
        if t.get('knots') is None: print(q['id'], 'no table'); continue
        lib['mods'].append(q); lens[q['id']] = t
        print('%s count %d class %d: lock %.4f, f up to %.4f, length at f0 %.6f' % (q['id'], q['count'], key[2], t['lock'], t['knots'][0][-1], t['own']), flush=True)
    pickle.dump(lib, open(new + '/library.pkl', 'wb')); pickle.dump(lens, open(new + '/lens.pkl', 'wb'))
    return 0


def _library(work):
    return M.Library(work, only=(lambda q: q['tag'] in ('h', 'z') or any(k in q['licence'] for k in M.OK_LICENCE)))


def cmd_predict(a):
    """zone_search.py predict NEWWORK DETAILS.csv OUT.tsv [LO HI]   the generator of modules.py with the new zones:
    for every n the best choice of modules, and whether a new zone is in it."""
    work, details, out = a[:3]
    lo, hi = (int(a[3]), int(a[4])) if len(a) > 4 else (300, 1000)
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    lib = _library(work)
    rows = []
    for n in range(lo, hi + 1):
        m = math.isqrt(n - 1)
        if held[n] >= m + 1 - 1e-9: continue
        r = lib.best(n, top=1)
        if not r: continue
        f, stop, C, F1, F2, s1, s2 = r[0]
        z = sum(x['q']['tag'] == 'z' for x in (F1, F2))
        rows.append((n, held[n], m + f, m + f - held[n], C['id'], F1['id'], F2['id'], s1, s2, z))
        if z or m + f < held[n]: print('n=%d held %.6f predicted %.6f (%+.6f) %s %s %s stacks %d,%d new zones %d' % rows[-1], flush=True)
    with open(out, 'w') as h:
        h.write('n\theld_side\tpredicted_side\tpredicted_minus_held\tcorner\tfar1\tfar2\tstacks1\tstacks2\tnew_zones\n')
        for r in rows: h.write('%d\t%.6f\t%.6f\t%+.6f\t%s\t%s\t%s\t%d\t%d\t%d\n' % r)
    d = [r for r in rows if r[9]]
    print('n with a prediction: %d; with a new zone in the best choice: %d; of these below held: %d' % (len(rows), len(d), sum(r[3] < 0 for r in d)))
    return 0


def cmd_build(a):
    """zone_search.py build NEWWORK RAWDIR DETAILS.csv N [--top 2] [--skip 0] [--fq PATH] [--slack 0.003]
    The build step of modules.py (start a little above the prediction, the lane's LP, then the fq quench) for the
    choices of N that hold a new zone, without the first SKIP of them. Certify RAWDIR with `modules.py take`."""
    work, raw, details, n = a[0], a[1], a[2], int(a[3])
    top = _opt(a, '--top', 2, int); fq = _opt(a, '--fq', None, str); slack = _opt(a, '--slack', 0.003)
    skip = _opt(a, '--skip', 0, int); seen = 0
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}[n]
    lib = _library(work); os.makedirs(raw, exist_ok=True); m = math.isqrt(n - 1); done = 0
    for f, stop, C, F1, F2, s1, s2 in lib.best(n, top=top, below=held - m + slack):
        if not any(x['q']['tag'] == 'z' for x in (F1, F2)): continue
        seen += 1
        if seen <= skip: continue
        P = None; why = ''
        for up in (2e-4, 6e-4, 1.5e-3, 3e-3):
            P, why = M.assemble(lib, n, C, F1, F2, s1, s2, f + up)
            if P is not None:
                side, gap = M.layout_state(P)
                if gap > -1e-7 and side < m + f + up + 1e-6: break
                why = 'start side %.6f gap %.1e' % (side, gap); P = None
        tag = '%s+%s+%s' % (C['id'], F1['id'], F2['id'])
        if P is None:
            print('n=%d %s stacks %d,%d predicted %.6f: no start (%s)' % (n, tag, s1, s2, m + f, why), flush=True); continue
        Q, L = M._squeeze(n, P, fq, log=lambda s: print(s, flush=True))
        done += 1
        M.write_layout('%s/%d-%d.csv' % (raw, n, done), n, Q)
        json.dump(dict(n=n, predicted=m + f, start=side, built=L, held=held, stop=stop, stacks=[s1, s2],
                       modules=[dict(id=x['id'], source=x['q']['src'], licence=x['q']['licence']) for x in (C, F1, F2)]),
                  open('%s/%d-%d.json' % (raw, n, done), 'w'))
        print('n=%d BUILT %s predicted %.6f built %.9f held %.9f (%+.6f)' % (n, tag, m + f, L, held, L - held), flush=True)
    return 0


if __name__ == '__main__':
    cmds = dict(classes=cmd_classes, base=cmd_base, control=cmd_control, search=cmd_search, table=cmd_table, merge=cmd_merge, taper=cmd_taper,
                predict=cmd_predict, build=cmd_build)
    sys.exit(cmds[sys.argv[1]](sys.argv[2:]) or 0)
