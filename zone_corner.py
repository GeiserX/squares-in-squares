#!/usr/bin/env python3
"""Search the corner zone of a two-arm layout as its own problem: zone_search.py with two sliding stacks.

  zone_corner.py base    LIBWORK OUT.pkl F C1 C2 [--ids A,B] [--own] [--zones]   the library's corners of C1 x C2 carried to F (start
                         states); --own [--shift D]: each at the f it was found at plus D (C1 = 0: every pair of arms)
  zone_corner.py control BASE.pkl OUTDIR --id ID [--seed S] [--minutes M]
  zone_corner.py search  BASE.pkl OUTDIR --id ID [--down D] [--up U] [--minutes M] [--seed S]
                         [--moves self,resume,delete,insert,hop] [--deadline FILE] [--beam B] [--counts N,N] [--slot SECONDS]
                         [--caps DY,DX]   (the hops under the caps y0 - DY and x0 - DX of the start corner; they go on once both fit)
  zone_corner.py adopt   BASE.pkl OUTDIR                       every corner of BASE.pkl as kept states (angles free at its f)
  zone_corner.py sweep   BASE.pkl OUTDIR [--part I/K] [--slot S] [--down D] [--mixed] [--resume]   hops on the own count
                         of every corner of BASE.pkl, and on the counts with up to D squares deleted (--mixed: arms of
                         two sizes only; --resume: from the kept states of earlier runs in OUTDIR at the same f)
  zone_corner.py zbase   OUT.pkl ZONESDIR... [--mixed] [--max-loss X] [--ids A,B]   stored zone-search corners as start
                         states at their own f (for search and sweep)
  zone_corner.py table   OUTDIR ZONESDIR TSV [--per 4] [--tag T] [--over ZDIR,...]   every kept corner as a module file and a
                         row (rows are appended); --over: only states 1e-3 below the stored corners of those dirs
  zone_corner.py merge   LIBWORK ZONESDIR NEWWORK [--max-loss X] [--also LIB2]   library.pkl and lens.pkl with the kept corners added
  zone_corner.py predict NEWWORK DETAILS.csv OUT.tsv [LO HI]   the generator of modules.py; marks the choices with a new zone
  zone_corner.py build   NEWWORK RAWDIR DETAILS.csv N [--top 2] [--fq PATH] [--slack S] [--gate G] [--quench D] [--skip K]
  zone_corner.py quench  RAWDIR [N ...]                       the fq quench of the polish lane on built layouts

The corner problem. Frame of a corner module of modules.py: arm 1 (stacks of c1) runs up the left wall in the strip
0 <= x <= W1 = c1 - 1 + f, arm 2 (c2) runs along the bottom wall in the strip 0 <= y <= W2. The upright grid starts
at (W1, W2) and is kept rigid. The corner ends at the near face of the first flush stack of each arm: y0 is where the
face of the stack of arm 1 crosses x = W1 / 2, x0 where the face of the stack of arm 2 crosses y = W2 / 2. Both
stacks slide. For a count N the result is a trade curve: for each cap on y0, the smallest x0. And

  loss = c1 cos t1 * y0 + c2 cos t2 * (x0 - W1) - N

is the corner loss of modules.py. One more flush stack on an arm adds c squares and one pitch and leaves the loss
alone, so what a corner serves is its count modulo c and its two lengths modulo the pitch.

Tools (the evaluator, the compactor and the soft energy are those of zone_search.py and modules.py, with two faces):
  exact     smallest gap inside the corner, to each stack, and the squares beyond a stack; the two lengths of a
            frozen corner by bisection on each stack
  compact   the contact LP of modules.py on the corner alone, angles free in a trust region, cost a1 y0 + a2 x0,
            optional caps on the two lengths
  trade     the trade curve of a state: smallest y0, smallest x0, and the smallest x0 under caps on y0 in between
  soft      the overlap energy of zone_search.py with both stacks and the grid cells held; squeeze lowers both stacks
  moves     delete (beam, ranked by the fixed-angle LP on w1 y0 + w2 x0, plus the block move: the c squares nearest
            a stack face out at once), insert (largest pockets), hop (shake, flip, reloc)
  weights   since round 14 the hops, their LP, the delete ranking and the kept order use w1 y0 + w2 x0 with
            (w1, w2) proportional to (c1 cos t1, c2 cos t2), as the loss does (WEIGH); for arms of one size it is y0 + x0

Our own code. Reads the library pickles of modules.py as data. Imports modules, zone_search and methods_lp.
"""
import csv, glob, json, math, os, pickle, sys, time, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I drops the script dir
import numpy as np
from scipy.optimize import minimize
import modules as M
import zone_search as Z
from methods_lp import best_axes, pair_list, half

SQ2 = math.sqrt(2)
CLEAR, TOL, DELTA, EPS = Z.CLEAR, Z.TOL, Z.DELTA, Z.EPS
FAR = 1e9                # the soft energy of zone_search has a wall at x = W; a corner has none


def cmod(c1, c2, lean1=1, lean2=-1):
    return dict(c1=c1, c2=c2, lean1=lean1, lean2=lean2, miss=[], rig=[], grp=np.zeros(0, int))


def geom(mod, f):
    c1, c2 = mod['c1'], mod['c2']
    t1, t2 = M.flush_tilt(c1, f), M.flush_tilt(c2, f)
    return t1, t2, 1 / math.cos(t1), 1 / math.cos(t2), c1 - 1 + f, c2 - 1 + f


def loss_of(mod, f, count, y0, x0):
    t1, t2, p1, p2, W1, W2 = geom(mod, f)
    return mod['c1'] * math.cos(t1) * y0 + mod['c2'] * math.cos(t2) * (x0 - W1) - count


WEIGH = 'loss'           # 'loss': the hops, the delete ranking and the kept order weigh y0 by c1 cos t1 and x0 by c2 cos t2,
                         # as the loss does; 'sum': y0 + x0 (the rule before round 14). Arms of one size: the same.


def weights(mod, f):
    """The weights of the two lengths in the loss, c1 cos t1 and c2 cos t2, scaled to sum 2 ((1, 1) for arms of one size)."""
    if WEIGH != 'loss': return 1.0, 1.0
    t1, t2 = geom(mod, f)[:2]
    w1, w2 = mod['c1'] * math.cos(t1), mod['c2'] * math.cos(t2)
    return 2 * w1 / (w1 + w2), 2 * w2 / (w1 + w2)


# ----------------------------------------------------------------------------------------------- exact evaluator

def exact(P, mod, f, y0, x0):
    """Gaps of the corner P (x, y, degrees) with the two stack faces at y0 and x0.
    -> (smallest gap inside, against the walls and the grid; smallest gap to stack 1; to stack 2; squares beyond a stack)"""
    P = np.asarray(P, float); nz = len(P)
    S, mode = M.corner_state(mod, f, P, y0, x0)
    pairs = pair_list(S, SQ2 + 1e-3)
    ma, mb = mode[pairs[:, 0]], mode[pairs[:, 1]]
    k = (ma == 0) | (mb == 0)
    pairs, ma, mb = pairs[k], ma[k], mb[k]
    g_in = g1 = g2 = math.inf
    if len(pairs):
        g = best_axes(S, pairs)[0]
        s1 = (ma == 1) | (mb == 1); s2 = (ma == 2) | (mb == 2); o = ~(s1 | s2)
        if s1.any(): g1 = float(g[s1].min())
        if s2.any(): g2 = float(g[s2].min())
        if o.any(): g_in = float(g[o].min())
    h = half(S[:nz, 2])
    g_in = min(g_in, float((S[:nz, 0] - h).min()), float((S[:nz, 1] - h).min()))
    t1, t2, p1, p2, W1, W2 = geom(mod, f)
    a1, a2 = mod['lean1'] * t1, mod['lean2'] * t2
    d1 = -math.sin(a1) * (S[:nz, 0] - W1 / 2) + math.cos(a1) * (S[:nz, 1] - (y0 + p1 / 2))
    d2 = math.cos(a2) * (S[:nz, 0] - (x0 + p2 / 2)) + math.sin(a2) * (S[:nz, 1] - W2 / 2)
    return g_in, g1, g2, int(((d1 > 0) | (d2 > 0)).sum())


def lengths(P, mod, f, y0, x0):
    """The two lengths of a frozen corner: the smallest y0 and the smallest x0 at which every gap inside is >= TOL
    and every gap to a stack is >= CLEAR, by bisection on each stack. -> (y0, x0, smallest gap inside) or None"""
    g_in, g1, g2, b = exact(P, mod, f, y0, x0)
    if g_in < TOL or g1 < CLEAR or g2 < CLEAR or b: return None
    lo, hi = y0 - 0.6, y0
    for _ in range(46):
        mid = 0.5 * (lo + hi)
        r = exact(P, mod, f, mid, x0)
        if r[1] >= CLEAR and not r[3]: hi = mid
        else: lo = mid
    y0 = hi
    lo, hi = x0 - 0.6, x0
    for _ in range(46):
        mid = 0.5 * (lo + hi)
        r = exact(P, mod, f, y0, mid)
        if r[2] >= CLEAR and not r[3]: hi = mid
        else: lo = mid
    return y0, hi, g_in


# ----------------------------------------------------------------------------------------------- the LP compactor

def compact(P, mod, f, y0, x0, cost=(1.0, 1.0), caps=(None, None), rounds=3, turn=True):
    """The contact LP of modules.py on the corner alone with both stacks sliding: minimise cost . (y0, x0) with
    y0 <= caps[0] and x0 <= caps[1] (absolute values). -> (y0, x0, P) or None"""
    out = None
    for _ in range(rounds):
        S, mode = M.corner_state(mod, f, P, y0 + 1e-7, x0 + 1e-7)
        cp = (None if caps[0] is None else caps[0] - y0 - 1e-7, None if caps[1] is None else caps[1] - x0 - 1e-7)
        r = M.relax(S, mode, cost, cp) if turn else M.settle(S, mode, cost, cp)
        if r is None or not M.legal(r[0], mode): break
        Q = r[0][:len(P)].copy(); Q[:, 2] = np.degrees(Q[:, 2])
        gain = -(cost[0] * r[1][0] + cost[1] * r[1][1]) - (cost[0] + cost[1]) * 1e-7
        y0, x0, P = y0 + 1e-7 + r[1][0], x0 + 1e-7 + r[1][1], Q
        out = (y0, x0, P)
        if gain < 1e-9: break
    return out


def trade(P, mod, f, y0, x0, steps=5):
    """The trade curve of a state: [(y0, x0)] from the smallest y0 to the smallest x0, with the smallest x0 under
    each cap on y0 in between (a chain of LPs, each from a legal state)."""
    A = compact(P, mod, f, y0, x0, cost=(1.0, 0.02))
    B = compact(P, mod, f, y0, x0, cost=(0.02, 1.0))
    if A is None or B is None: return []
    pts = [(A[0], A[1])]
    cur = A
    for cap in np.linspace(A[0], B[0], steps + 2)[1:-1]:
        r = compact(cur[2], mod, f, cur[0], cur[1], cost=(1e-3, 1.0), caps=(float(cap), None), rounds=2)
        if r is None: continue
        cur = r; pts.append((r[0], r[1]))
    pts.append((B[0], B[1]))
    return pts


# ----------------------------------------------------------------------------------------------- the soft search

def soft(P, mod, f, y0, x0, delta=DELTA, maxiter=200):
    """Minimise the overlap energy of the corner with both stacks and the grid cells held. -> (P, energy)"""
    S, mode = M.corner_state(mod, f, P, y0, x0)
    nz = len(P); X = S[:nz].copy(); O = S[nz:]
    E0, _ = Z.soft_energy(X.ravel(), nz, O, FAR, delta)
    if E0 <= EPS: return np.array(P, float), E0
    r = minimize(Z.soft_energy, X.ravel(), args=(nz, O, FAR, delta), jac=True, method='L-BFGS-B',
                 options={'maxiter': maxiter, 'ftol': 1e-30, 'gtol': 1e-14})
    Q = r.x.reshape(nz, 3).copy(); Q[:, 2] = np.degrees(Q[:, 2])
    return Q, float(r.fun)


def squeeze(P, mod, f, y0, x0, step=0.08, out=0.05, tries=40):
    """Push both stacks out until the overlap energy reaches zero, then lower them (both, then one at a time) in
    steps that are halved on failure. -> (P, y0, x0) or None"""
    Q, E = soft(P, mod, f, y0, x0)
    k = 0
    while E > EPS and k < tries:
        y0 += out; x0 += out; k += 1
        Q, E = soft(Q, mod, f, y0, x0)
    if E > EPS: return None
    P = Q
    while step > 4e-3:                               # the LP closes the rest
        moved = False
        for dy, dx in ((step, step), (step, 0.0), (0.0, step)):
            Q, E = soft(P, mod, f, y0 - dy, x0 - dx)
            if E <= EPS and exact(Q, mod, f, y0 - dy, x0 - dx)[3] == 0:
                P, y0, x0, moved = Q, y0 - dy, x0 - dx, True
                break
        if not moved: step *= 0.5
    return P, y0, x0


def settle_zone(P, mod, f, y0, x0, cost=(1.0, 1.0)):
    """squeeze, then the LP. -> (y0, x0, P) or None. The result is legal by the exact test or it is dropped."""
    r = squeeze(P, mod, f, y0, x0)
    if r is None: return None
    r2 = compact(r[0], mod, f, r[1], r[2], cost)
    if r2 is None: return None
    le = lengths(r2[2], mod, f, r2[0] + 1e-7, r2[1] + 1e-7)
    if le is None: return None
    return le[0], le[1], r2[2]


# ----------------------------------------------------------------------------------------------- moves

def face_dist(P, mod, f, y0, x0):
    """For every square, its signed distance to the face of stack 1 and of stack 2 (0 at the face, negative inside)."""
    t1, t2, p1, p2, W1, W2 = geom(mod, f)
    a1, a2 = mod['lean1'] * t1, mod['lean2'] * t2
    P = np.asarray(P, float)
    d1 = -math.sin(a1) * (P[:, 0] - W1 / 2) + math.cos(a1) * (P[:, 1] - (y0 + p1 / 2))
    d2 = math.cos(a2) * (P[:, 0] - (x0 + p2 / 2)) + math.sin(a2) * (P[:, 1] - W2 / 2)
    return d1, d2


def face_near(P, mod, f, y0, x0):
    """For every square, its signed distance to the nearer stack face (0 at the face, negative inside the corner)."""
    return np.maximum(*face_dist(P, mod, f, y0, x0))


TIES = 'face'            # delete_beam: equal LP sums are told apart by the square's distance to a stack face ('face'), or
                         # only the first deletion of each sum is kept ('first', the rule before round 13)


def delete_beam(P, mod, f, y0, x0, d, beam=2, log=None, keep=None, until=None):
    """Delete d squares one at a time. Each deletion is ranked by the sum of lengths the fixed-angle LP reaches, and
    equal sums by the deleted square's distance to a stack face (nearest first); the best `beam` are compacted with
    free angles. keep(level, y0, x0, P) is called with the best of every level. The sums are weighted as the loss
    (weights). Block move: when d >= c of an arm, the c squares nearest that arm's stack face also go out at once,
    with one compaction, and join the states of level c (one square at a time fails control B: each compaction
    moves the rest, so the next square nearest the face is no longer one of the stack's own)."""
    w = weights(mod, f)
    ws = lambda r: w[0] * r[0] + w[1] * r[1]
    states = [(y0, x0, P)]
    block = collections.defaultdict(list)
    for arm, c in ((0, mod['c1']), (1, mod['c2'])):
        if d < c: continue
        dist = face_dist(P, mod, f, y0, x0)[arm]
        r = compact(np.delete(P, np.argsort(-dist)[:c], 0), mod, f, y0, x0, cost=w, rounds=8)
        if log: log('block of %d at stack %d: %s' % (c, arm + 1, 'none' if r is None else '%.5f+%.5f' % r[:2]))
        if r is not None: block[c].append(r)
    for lev in range(d):
        nxt = []
        for y, x, P0 in states:
            near = face_near(P0, mod, f, y, x)
            for i in range(len(P0)):
                if until is not None and time.time() > until: break
                Q = np.delete(P0, i, 0)
                r = compact(Q, mod, f, y, x, cost=w, rounds=1, turn=False)
                if r is not None: nxt.append((round(ws(r), 5), -float(near[i]), r))
        nxt.sort(key=lambda s: s[0] if TIES == 'first' else s[:2])
        seen = set(); pick = []
        for s in nxt:
            key = s[0] if TIES == 'first' else (s[0], round(s[1], 3))
            if key in seen: continue
            seen.add(key); pick.append(s[2])
            if len(pick) >= beam: break
        states = []
        for r in pick:
            r2 = compact(r[2], mod, f, r[0], r[1], cost=w)
            if r2 is not None: states.append(r2)
        states += block.get(lev + 1, [])
        states.sort(key=ws)
        if log: log('delete level %d: %s' % (lev + 1, ' '.join('%.5f+%.5f' % s[:2] for s in states)))
        if not states: return []
        if keep: keep(lev + 1, *states[0])
        if until is not None and time.time() > until: break
    return states


def pockets(P, mod, f, y0, x0, top=3, step=0.1):
    """Places for one more square: centres on a grid, upright or at the tilt of an arm, ranked by the smallest gap
    to everything there (the least overlap first). -> [(gap, x, y, angle in degrees)]"""
    t1, t2, p1, p2, W1, W2 = geom(mod, f)
    a1, a2 = mod['lean1'] * t1, mod['lean2'] * t2
    A, mode = M.corner_state(mod, f, P, y0, x0)
    xs = np.arange(0.5, x0 + 0.5 * W2 * math.tan(t2) + 0.3, step); ys = np.arange(0.5, y0 + 0.5 * W1 * math.tan(t1) + 0.3, step)
    out = []
    for ang in (0.0, a1, a2):
        hh = 0.5 * (abs(math.cos(ang)) + abs(math.sin(ang)))
        gx, gy = np.meshgrid(xs, ys); gx, gy = gx.ravel(), gy.ravel()
        ok = (gx - hh >= 0) & (gy - hh >= 0) & ((gx + hh <= W1) | (gy + hh <= W2))
        ok &= (-math.sin(a1) * (gx - W1 / 2) + math.cos(a1) * (gy - (y0 + p1 / 2))) < -0.8
        ok &= (math.cos(a2) * (gx - (x0 + p2 / 2)) + math.sin(a2) * (gy - W2 / 2)) < -0.8
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
    for r in out:
        if all((r[1] - q[1]) ** 2 + (r[2] - q[2]) ** 2 > 0.6 for q in pick): pick.append(r)
        if len(pick) >= top: break
    return pick


def insert(P, mod, f, y0, x0, top=3):
    """One more square in each of the largest pockets, the stacks pushed out as little as the soft search needs.
    -> [(y0, x0, P)] smallest sum first"""
    res = []
    for g, x, y, a in pockets(P, mod, f, y0, x0, top):
        Q = np.vstack([P, [[x, y, a]]])
        push = min(0.3, max(0.02, -g * 0.5))
        r = settle_zone(Q, mod, f, y0 + push, x0 + push)
        if r is not None: res.append(r)
    w = weights(mod, f)
    res.sort(key=lambda s: w[0] * s[0] + w[1] * s[1])
    return res


def hop(P, mod, f, y0, x0, rng):
    """One perturbed copy: shake (a neighbourhood moves by up to 0.15 and turns by up to 6 degrees), flip (one
    square takes another of the three angles: upright, the tilt of arm 1, the tilt of arm 2), snap (a neighbourhood
    takes the nearest of the three), reloc (one square leaves and returns in a large pocket). -> (P, y0, x0, kind)"""
    t1, t2 = geom(mod, f)[:2]
    angs = (0.0, mod['lean1'] * math.degrees(t1), mod['lean2'] * math.degrees(t2))
    kind = rng.choice(['shake', 'shake', 'shake', 'flip', 'flip', 'reloc', 'reloc', 'snap', 'snap', 'snapall'])
    Q = P.copy(); i = int(rng.integers(len(Q)))
    near = np.nonzero((Q[:, 0] - Q[i, 0]) ** 2 + (Q[:, 1] - Q[i, 1]) ** 2 < rng.choice([1.3, 2.0, 3.0]) ** 2)[0]
    if kind == 'shake':
        Q[near, :2] += rng.uniform(-0.15, 0.15, (len(near), 2)); Q[near, 2] += rng.uniform(-6, 6, len(near))
        return Q, y0 + 0.1, x0 + 0.1, kind
    if kind == 'snapall':                            # every square within 5 degrees of one of the three angles takes it
        return snap_all(Q, mod, f, within=5.0), y0 + 0.05, x0 + 0.05, kind
    if kind == 'snap':                               # the squares of a neighbourhood take the nearest of the three angles
        Q[near] = snap_all(Q[near], mod, f)
        return Q, y0 + 0.05, x0 + 0.05, kind
    if kind == 'flip':
        a = ((Q[i, 2] + 45) % 90) - 45
        other = [v for v in angs if abs(((v - a + 45) % 90) - 45) > 1.0]
        Q[i, 2] = other[int(rng.integers(len(other)))]
        return Q, y0 + 0.12, x0 + 0.12, kind
    Q = np.delete(Q, i, 0)
    pk = pockets(Q, mod, f, y0, x0, top=3)
    pk = [r for r in pk if (r[1] - P[i, 0]) ** 2 + (r[2] - P[i, 1]) ** 2 > 0.5] or pk
    g, x, y, a = pk[int(rng.integers(len(pk)))]
    push = min(0.3, max(0.02, -g * 0.5))
    return np.vstack([Q, [[x, y, a]]]), y0 + push, x0 + push, kind


def hops(P, mod, f, y0, x0, seconds, rng, temp=0.01, log=None, stop=None, seen=None, caps=None, go_on=False):
    """Basin hopping on the corner alone, on the sum of the two lengths weighted as the loss (weights; for arms of one
    size the plain sum). seen(y0, x0, P, kind) gets every legal state within 0.12 of the best weighted sum (a longer
    y0 with a shorter x0 is another point of the trade curve). stop is a weighted sum.
    caps=(Y, X): hops under a cap. The objective is the larger excess max(y0 - Y, x0 - X) (the sum breaks ties), the
    LP of each hop leans on the length that is further over its cap, and the run stops when both fit.
    go_on (search --caps, round 19): the run does not stop when both fit. The objective is the weighted sum plus 1000
    times the excess over the caps, so the hops go on lowering the loss with neither length over its cap. Without it a
    start that already fits its caps made 0 hops.
    -> (y0, x0, P, hops tried, kinds that won)"""
    w = weights(mod, f)
    ws = lambda r: w[0] * r[0] + w[1] * r[1]
    if caps is None: obj = ws
    elif go_on: obj = lambda r: ws(r) + 1000.0 * max(r[0] - caps[0], r[1] - caps[1], 0.0)
    else: obj = lambda r: max(r[0] - caps[0], r[1] - caps[1]) + 1e-3 * ws(r)
    t0 = time.time(); k = 0; won = collections.Counter()
    best = cur = (y0, x0, P)
    while time.time() - t0 < seconds:
        if stop is not None and ws(best) <= stop: break
        if caps is not None and not go_on and best[0] <= caps[0] and best[1] <= caps[1]: break
        Q, ys, xs, kind = hop(cur[2], mod, f, cur[0], cur[1], rng)
        fits = caps is not None and cur[0] <= caps[0] and cur[1] <= caps[1]
        cost = w if caps is None or (go_on and fits) else ((1.0, 0.2) if cur[0] - caps[0] > cur[1] - caps[1] else (0.2, 1.0))
        r = settle_zone(Q, mod, f, ys, xs, cost); k += 1
        if r is None: continue
        if seen is not None and ws(r) < ws(best) + 0.12: seen(r[0], r[1], r[2], kind)
        d = obj(r) - obj(cur)
        if d < -1e-8 or rng.random() < math.exp(-max(d, 0.0) / temp): cur = r
        if obj(r) < obj(best) - 1e-8:
            best = r; won[kind] += 1
            if log: log('hop %d (%s) %.6f + %.6f' % (k, kind, r[0], r[1]))
        if k % 25 == 0 and obj(cur) > obj(best) + 5 * temp: cur = best
    return best[0], best[1], best[2], k, dict(won)


def shaken(P, mod, f, y0, x0, rng, move=0.2, turn=10.0):
    """the control's start: every square moved by up to `move` and turned by up to `turn` degrees, then the stacks
    pushed out until the soft search finds a legal corner. -> (P, y0, x0) or None"""
    S = P.copy()
    S[:, :2] += rng.uniform(-move, move, (len(S), 2)); S[:, 2] += rng.uniform(-turn, turn, len(S))
    for stretch in (1.0, 1.1, 1.2, 1.35):
        Q = S.copy(); Q[:, :2] *= stretch; y, x = y0 * stretch, x0 * stretch
        Q, E = soft(Q, mod, f, y, x)
        k = 0
        while E > EPS and k < 30:
            y += 0.05; x += 0.05; k += 1
            Q, E = soft(Q, mod, f, y, x)
        if E <= EPS: return Q, y, x
    return None


def snap_all(P, mod, f, within=None):
    """every square at the nearest of upright, the tilt of arm 1 and the tilt of arm 2 (only when it is `within` degrees)"""
    t1, t2 = geom(mod, f)[:2]
    angs = np.array([0.0, mod['lean1'] * math.degrees(t1), mod['lean2'] * math.degrees(t2)])
    Q = P.copy(); a = ((Q[:, 2] + 45) % 90) - 45
    d = np.abs(a[:, None] - angs[None, :]); k = np.argmin(d, axis=1)
    ok = np.ones(len(Q), bool) if within is None else d[np.arange(len(Q)), k] <= within
    Q[ok, 2] = angs[k[ok]]
    return Q


# ----------------------------------------------------------------------------------------------- modules

def as_module(P, mod, f, y0, x0, name, how, base):
    """A kept corner with the fields of a corner module of modules.py. Squares at the exact tilt of an arm (chains
    along the arm's stacks, and singles) turn with the arm when the module is carried to another f."""
    from frontier_stacks import stacks
    t1, t2, p1, p2, W1, W2 = geom(mod, f)
    a1, a2 = mod['lean1'] * math.degrees(t1), mod['lean2'] * math.degrees(t2)
    tilted = np.nonzero(np.abs(P[:, 2]) > 0.5)[0]
    chains = [[int(tilted[i]) for i in ch] for ch in stacks(P[tilted])[0]] if len(tilted) else []
    def rigid(a, horizontal, tol, taken):
        groups = []; used = set(taken)
        for ch in chains:
            if len(ch) < 2 or float(np.abs(P[ch, 2] - a).max()) > tol or set(ch) & used: continue
            ax = P[ch[-1], :2] - P[ch[0], :2]
            if (abs(ax[0]) > abs(ax[1])) != horizontal: continue
            groups.append(list(ch)); used.update(ch)
        for i in range(len(P)):
            if i not in used and abs(P[i, 2] - a) < min(tol, 0.05): groups.append([i]); used.add(i)
        return groups
    r1 = rigid(a1, True, M.EXACT, ()); r2 = rigid(a2, False, M.EXACT, {i for g in r1 for i in g})
    grp = np.zeros(len(P), int)
    for g in r1: grp[g] = 1
    for g in r2: grp[g] = 2
    loose = int(((np.abs(P[:, 2]) > 0.5) & (grp == 0)).sum()); up = int((np.abs(P[:, 2]) <= 0.5).sum())
    sig = 'c%dx%d:z%d/%d|l%d|u%d|%s%s' % (mod['c1'], mod['c2'], int((grp == 1).sum()), int((grp == 2).sum()), loose, up,
                                           '+' if mod['lean1'] > 0 else '-', '+' if mod['lean2'] > 0 else '-')
    return dict(n=0, m=0, k=0, f0=float(f), tag='z', kind='corner', c1=mod['c1'], c2=mod['c2'], lean1=mod['lean1'], lean2=mod['lean2'],
                P=np.array(P, float), grp=grp, rig=r1 + r2, miss=[], count=len(P), y0=float(y0), x0=float(x0),
                loss0=loss_of(mod, f, len(P), y0, x0), tilt1=math.degrees(t1), tilt2=math.degrees(t2), sig=sig, id=name, how=how,
                src='zone_corner.py: %s, from corner %s <%s>' % (how, base['id'], base['src']), licence=base['licence'])


def picture(P, mod, f, y0, x0, path, title=''):
    """svg of a corner: dark, uprights grey, squares at an arm's tilt blue, others orange, the stacks outlined"""
    t1, t2 = geom(mod, f)[:2]
    S, mode = M.corner_state(mod, f, P, y0, x0)
    top = float(S[:, 1].max()) + 1.2; sc = 40.0
    a1, a2 = mod['lean1'] * t1, mod['lean2'] * t2
    def poly(x, y, a, fill, stroke):
        co, si = math.cos(a), math.sin(a)
        pts = [(x + 0.5 * (sx * co - sy * si), y + 0.5 * (sx * si + sy * co)) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
        return '<polygon points="%s" fill="%s" stroke="%s" stroke-width="1"/>' % (' '.join('%.2f,%.2f' % (10 + q[0] * sc, 30 + (top - q[1]) * sc) for q in pts), fill, stroke)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" style="background:#111">' % (20 + (float(S[:, 0].max()) + 1.2) * sc, 40 + top * sc),
           '<text x="10" y="18" fill="#ddd" font-family="monospace" font-size="12">%s</text>' % title]
    for (x, y, a), md in zip(S, mode):
        if md == -1: out.append(poly(x, y, a, '#2a2a2a', '#111'))
        elif md > 0: out.append(poly(x, y, a, 'none', '#888'))
        else:
            col = '#555' if abs(a) < 0.009 else '#3b78c4' if min(abs(a - a1), abs(a - a2)) < 0.006 else '#c9822b'
            out.append(poly(x, y, a, col, '#111'))
    out.append('</svg>')
    open(path, 'w').write('\n'.join(out))


# ----------------------------------------------------------------------------------------------- commands

_opt = Z._opt
_save = Z._save


def cmd_base(a):
    """The library's corners of C1 x C2 carried to F along the knots of modules.path, then compacted with free angles."""
    work, out, f, c1, c2 = a[0], a[1], float(a[2]), int(a[3]), int(a[4])
    ids = [v for v in _opt(a, '--ids', '', str).split(',') if v]
    span = _opt(a, '--span', 0.03)
    own = '--own' in a                               # every corner at the f it was found at (F is not used; C1 = 0: every pair of arms)
    shift = _opt(a, '--shift', 0.0)                  # with --own: at that f plus this
    lib = pickle.load(open(work + '/library.pkl', 'rb'))
    res = []
    for q in lib['mods']:
        if q['kind'] != 'corner' or q['miss'] or q['id'].endswith('~'): continue
        if q['tag'] == 'z' and '--zones' not in a: continue
        if own:
            if c1 and (q['c1'], q['c2']) != (c1, c2): continue
            f = round(q['f0'] + shift, 6); c1q, c2q = q['c1'], q['c2']
            if not 0.6 <= f <= 0.995: continue
        else:
            if (q['c1'], q['c2']) != (c1, c2): continue
            c1q, c2q = c1, c2
        if ids and q['id'] not in ids: continue
        if not ids and not own and abs(q['f0'] - f) > span: continue
        if not (q['tag'] in ('h', 'z') or q.get('ours') or any(k in q['licence'] for k in M.OK_LICENCE)): continue
        st = carry(q, f, soft='--soft' in a, log=lambda s: print(q['id'], s, flush=True))
        if st is None: print(q['id'], 'does not reach f'); continue
        mod = st[3]; le = st
        res.append(dict(id=q['id'], src=q['src'], licence=q['licence'], sig=q['sig'], count=q['count'], c1=c1q, c2=c2q, lean1=q['lean1'],
                        lean2=q['lean2'], f=f, y0=le[0], x0=le[1], P=st[2]))
        print('%s f %.4f count %d (class %d) y0 %.6f x0 %.6f sum %.6f loss %.4f %s' % (q['id'], f, q['count'], q['count'] % c1q, le[0], le[1], le[0] + le[1],
              loss_of(mod, f, q['count'], le[0], le[1]), q['sig']), flush=True)
    pickle.dump(res, open(out, 'wb'))
    return 0


def cmd_zbase(a):
    """zone_corner.py zbase OUT.pkl ZONESDIR [ZONESDIR ...] [--mixed] [--max-loss X] [--ids A,B]: the stored corners of
    zone-search dirs (zc*.pkl) as start states at their own f, y0 and x0 (no carry), for search and sweep. Only the
    corners legal at their stored f (check_corner)."""
    out = a[0]; dirs = [v for v in a[1:] if not v.startswith('--') and os.path.isdir(v)]
    cut = _opt(a, '--max-loss', 4.6); ids = [v for v in _opt(a, '--ids', '', str).split(',') if v]
    res = []
    for d in dirs:
        for p in sorted(glob.glob(d + '/zc*.pkl')):
            q = pickle.load(open(p, 'rb'))
            if '--mixed' in a and q['c1'] == q['c2']: continue
            if q['loss0'] > cut or (ids and q['id'] not in ids) or not check_corner(q)[0]: continue
            res.append(dict(id=q['id'], src=q['src'], licence=q['licence'], sig=q['sig'], count=q['count'], c1=q['c1'], c2=q['c2'],
                            lean1=q['lean1'], lean2=q['lean2'], f=q['f0'], y0=q['y0'], x0=q['x0'], P=q['P']))
            print('%s %dx%d f %.6f count %d loss %.4f' % (q['id'], q['c1'], q['c2'], q['f0'], q['count'], q['loss0']), flush=True)
    pickle.dump(res, open(out, 'wb'))
    print('%d corners' % len(res))
    return 0


def _pick(base, a):
    cid = _opt(a, '--id', None, str)
    b = next((b for b in base if b['id'] == cid), None) if cid else base[0]
    return b, cmod(b['c1'], b['c2'], b['lean1'], b['lean2'])


def cmd_control(a):
    """Find a library corner again from the corner with every square shaken. Pass: both lengths within 1e-4 of the
    library's (or a smaller sum)."""
    base = pickle.load(open(a[0], 'rb')); outdir = a[1]
    seed = _opt(a, '--seed', 1, int); minutes = _opt(a, '--minutes', 8.0)
    move = _opt(a, '--move', 0.2); turn = _opt(a, '--turn', 10.0)
    rng = np.random.default_rng(seed)
    b, mod = _pick(base, a); f = b['f']; wb = weights(mod, f)
    log = lambda s: print('[control %s seed %d] %s' % (b['id'], seed, s), flush=True)
    log('library corner count %d f %.3f y0 %.6f x0 %.6f loss %.4f' % (b['count'], f, b['y0'], b['x0'], loss_of(mod, f, b['count'], b['y0'], b['x0'])))
    t0 = time.time()
    if _opt(a, '--mode', 'A', str) == 'B':           # B: one more flush stack on an arm (the next corner of the class), then delete c
        global TIES
        TIES = _opt(a, '--ties', TIES, str)
        t1, t2, p1, p2, W1, W2 = geom(mod, f)
        arm = _opt(a, '--arm', 1 if b['c1'] >= b['c2'] else 2, int)
        if arm == 1:
            S = M.stack_squares(b['c1'], mod['lean1'] * math.degrees(t1), W1 / 2, b['y0'] + 0.5 / math.cos(t1)); y, x = b['y0'] + p1, b['x0']
        else:
            S = M.stack_squares(b['c2'], mod['lean2'] * math.degrees(t2), b['x0'] + 0.5 / math.cos(t2), W2 / 2, along_x=False); y, x = b['y0'], b['x0'] + p2
        c = len(S); P1 = np.vstack([b['P'], S])
        le = lengths(P1, mod, f, y + 1e-7, x + 1e-7)
        if le is None: log('the corner with one more stack is not legal'); return 1
        log('B: one more stack of %d on arm %d: count %d y0 %.6f x0 %.6f; delete %d (ties: %s)' % (c, arm, len(P1), le[0], le[1], c, TIES))
        st = delete_beam(P1, mod, f, le[0], le[1], c, beam=_opt(a, '--beam', 4, int), log=log)
        if not st: log('FAIL: no state after the deletions'); return 1
        best = min(st, key=lambda s: wb[0] * s[0] + wb[1] * s[1])
        log('after the deletions: y0 %.6f (%+.2e) x0 %.6f (%+.2e) (%.0f s)' % (best[0], best[0] - b['y0'], best[1], best[1] - b['x0'], time.time() - t0))
        pool = []
    else:
        st = shaken(b['P'], mod, f, b['y0'], b['x0'], rng, move, turn)
        if st is None: log('no legal start'); return 1
        log('shaken start legal with the stacks at %.4f and %.4f (%.0f s)' % (st[1], st[2], time.time() - t0))
        best = None
        pool = (('squeeze and LP', st[0]), ('every angle snapped first', snap_all(st[0], mod, f)))
    for nm, P0 in pool:
        r = settle_zone(P0, mod, f, st[1], st[2])
        if r is None: log('%s: no legal state' % nm); continue
        log('%s: y0 %.6f (%+.2e) x0 %.6f (%+.2e) (%.0f s)' % (nm, r[0], r[0] - b['y0'], r[1], r[1] - b['x0'], time.time() - t0))
        if best is None or wb[0] * r[0] + wb[1] * r[1] < wb[0] * best[0] + wb[1] * best[1]: best = r
    k = 0; won = {}
    capped = '--sum-only' not in a                   # the repair of round 13: a second phase under the library's two lengths as caps
    L0 = loss_of(mod, f, b['count'], b['y0'], b['x0'])     # pass: both lengths back, or a lower loss (for arms of two sizes the sum is not the loss)
    passed = lambda r: (abs(r[0] - b['y0']) < 1e-4 and abs(r[1] - b['x0']) < 1e-4) or loss_of(mod, f, b['count'], r[0], r[1]) < L0 - 1e-6
    if best is not None and not passed(best):
        y, x, P, k, won = hops(best[2], mod, f, best[0], best[1], minutes * 60 * (0.5 if capped else 1.0), rng, log=log, stop=wb[0] * b['y0'] + wb[1] * b['x0'] + 1e-5)
        best = (y, x, P)
        log('phase 1 (sum): y0 %.6f (%+.2e) x0 %.6f (%+.2e) after %d hops' % (y, y - b['y0'], x, x - b['x0'], k))
    if capped and best is not None and not passed(best):
        caps = (b['y0'] + 5e-5, b['x0'] + 5e-5); fr = [best]
        for cost, cp in (((0.02, 1.0), (caps[0], None)), ((1.0, 0.02), (None, caps[1])), ((1.0, 1.0), caps)):
            lp = compact(best[2], mod, f, best[0], best[1], cost=cost, caps=cp)
            le = lengths(lp[2], mod, f, lp[0] + 1e-7, lp[1] + 1e-7) if lp is not None else None
            if le is not None: fr.append((le[0], le[1], lp[2])); log('capped LP %s: %.6f %.6f' % (cost, le[0], le[1]))
        best = min(fr, key=lambda r: max(r[0] - caps[0], r[1] - caps[1]))
        if not passed(best):
            y, x, P, k2, won2 = hops(best[2], mod, f, best[0], best[1], minutes * 30, rng, log=log, caps=caps)
            best = (y, x, P); k += k2
            for kk, v in won2.items(): won['cap ' + kk] = v
    if best is None: log('FAIL: nothing legal'); return 1
    dy, dx = best[0] - b['y0'], best[1] - b['x0']
    ok = passed(best); dl = loss_of(mod, f, b['count'], best[0], best[1]) - L0
    log('final y0 %.6f (%+.2e) x0 %.6f (%+.2e) sum %+.2e loss %+.4f after %d hops %s, %.0f s: %s' % (best[0], dy, best[1], dx, dy + dx, dl, k, won, time.time() - t0, 'PASS' if ok else 'FAIL'))
    _save(outdir, 'control-%s-%d' % (b['id'], seed), dict(ref=(b['y0'], b['x0']), got=best[:2], P=best[2], hops=k, ok=ok))
    return 0


def cmd_search(a):
    """Corners of other counts from one library corner at the f of BASE.pkl: delete up to --down squares (beam),
    insert up to --up squares (pockets), then hops on every count found, the lowest loss first. For every count the
    file holds its trade curve as states: the ones that no other state beats in both lengths."""
    base = pickle.load(open(a[0], 'rb')); outdir = a[1]
    down = _opt(a, '--down', 0, int); up = _opt(a, '--up', 0, int); minutes = _opt(a, '--minutes', 20.0); seed = _opt(a, '--seed', 1, int)
    moves = _opt(a, '--moves', 'delete,insert,hop', str).split(','); beam = _opt(a, '--beam', 2, int)
    dl = _opt(a, '--deadline', None, str); tail = _opt(a, '--tail', 60.0)     # seconds kept for the end of the run
    rng = np.random.default_rng(seed)
    b, mod = _pick(base, a); f = b['f']; c1 = b['c1']; wb = weights(mod, f)
    bb = dict(id=b['id'], src=b['src'], licence=b['licence'])
    t0 = time.time(); cpu0 = time.process_time()
    left = lambda: min(minutes * 60 - (time.time() - t0), (float(open(dl).read().strip()) - time.time()) if dl and os.path.exists(dl) else 1e9)
    log = lambda s: print('[%s seed %d %.0fs] %s' % (b['id'], seed, time.time() - t0, s), flush=True)
    front = collections.defaultdict(list)            # count -> the states no other state beats in both lengths, smallest sum first
    def save(N):
        e = front[N][0]
        # f in the name: runs of one corner at two f keep both
        _save(outdir, 'corner-%s-%d-f%.4f-s%d' % (b['id'], N, f, seed), dict(front=front[N], y0=e['y0'], x0=e['x0'], P=e['P'], how=e['how'], base=bb, c1=c1,
              c2=b['c2'], lean1=b['lean1'], lean2=b['lean2'], f=f, count=N, seed=seed, cpu=time.process_time() - cpu0, tag=b['id']))
    def keep(y, x, P, how, checked=False):
        if not checked:
            le = lengths(P, mod, f, y + 1e-7, x + 1e-7)
            if le is None: return
            y, x = le[0], le[1]
        N = len(P); fr = front[N]
        if any(e['y0'] <= y + 1e-6 and e['x0'] <= x + 1e-6 for e in fr): return
        first = not fr or wb[0] * y + wb[1] * x < wb[0] * fr[0]['y0'] + wb[1] * fr[0]['x0'] - 1e-9
        fr[:] = [e for e in fr if not (y <= e['y0'] + 1e-6 and x <= e['x0'] + 1e-6)] + [dict(y0=y, x0=x, P=P, how=how)]
        fr.sort(key=lambda e: wb[0] * e['y0'] + wb[1] * e['x0']); del fr[10:]       # the lowest loss first
        save(N)
        if first: log('BEST count %d class %d: y0 %.6f x0 %.6f sum %.6f loss %.4f by %s' % (N, N % c1, y, x, y + x, loss_of(mod, f, N, y, x), how))
    lossN = lambda N: loss_of(mod, f, N, front[N][0]['y0'], front[N][0]['x0'])
    log('start %s count %d y0 %.6f x0 %.6f loss %.4f' % (b['id'], b['count'], b['y0'], b['x0'], loss_of(mod, f, b['count'], b['y0'], b['x0'])))
    if 'resume' in moves:
        for q in glob.glob('%s/corner-%s-*-s*.pkl' % (outdir, b['id'])):
            r = pickle.load(open(q, 'rb'))
            if abs(r['f'] - f) > 1e-9: continue
            for e in r.get('front') or [r]: keep(e['y0'], e['x0'], e['P'], e['how'])
    if 'self' in moves: keep(b['y0'], b['x0'], b['P'], 'the library corner at this f')
    if 'delete' in moves and down:
        delete_beam(b['P'], mod, f, b['y0'], b['x0'], down, beam=beam, log=log, until=time.time() + left() - tail / 2,
                    keep=lambda lev, y, x, P: keep(y, x, P, 'delete %d from count %d' % (lev, b['count'])))
    if 'insert' in moves and up:
        st = [(b['y0'], b['x0'], b['P'])]
        for q in range(up):
            if left() < tail: break
            nx = []
            for y, x, P in st[:beam]: nx += insert(P, mod, f, y, x, top=_opt(a, '--top', 3, int))
            nx.sort(key=lambda s: wb[0] * s[0] + wb[1] * s[1]); st = nx[:3]
            log('insert %d: %s' % (q + 1, ' '.join('%.5f+%.5f' % s[:2] for s in st)))
            if not st: break
            for y, x, P in st: keep(y, x, P, 'insert %d into count %d' % (q + 1, b['count']), checked=True)
    only = [int(v) for v in _opt(a, '--counts', '', str).split(',') if v]      # hops on these counts only
    slot = _opt(a, '--slot', 180.0)
    cut = [float(v) for v in _opt(a, '--caps', '', str).split(',') if v]      # --caps DY,DX: hops under the caps (y0 - DY, x0 - DX) of the start
    caps = (b['y0'] - cut[0], b['x0'] - cut[1]) if cut else None              # (one length shorter at the other's value: what one layout needs)
    if 'hop' in moves and not front:                 # round 19: hops alone (no self, resume, delete or insert) start from the corner
        keep(b['y0'], b['x0'], b['P'], 'the library corner at this f')
    over = lambda e: max(e['y0'] - caps[0], e['x0'] - caps[1], 0.0) if caps else 0.0
    if 'hop' in moves:
        while left() > tail and front:
            tried = 0
            for N in sorted((N for N in front if not only or N in only), key=lossN):          # the nearest to the go line first
                if left() < tail: break
                e = min(front[N], key=lambda v: (over(v), wb[0] * v['y0'] + wb[1] * v['x0']))   # under caps: the best state that fits
                how = e['how'].split(', then')[0] + ', then hops'
                y, x, P, k, won = hops(e['P'], mod, f, e['y0'], e['x0'], min(left() - tail / 2, slot), rng, caps=caps, go_on=True,
                                       seen=lambda y, x, P, kind: keep(y, x, P, how, checked=True))
                if caps is not None: keep(y, x, P, how + ' under caps', checked=True)
                tried += k
                log('hops %d on count %d from loss %.4f (%.6f + %.6f): %.4f (%.6f + %.6f) %s; %d states on its curve' % (k, N, loss_of(mod, f, N, e['y0'], e['x0']),
                    e['y0'], e['x0'], loss_of(mod, f, N, y, x), y, x, won, len(front[N])))
            if not tried: break                      # round 19: a pass with no hop at all ends the loop (it spun 2.7 million times)
    for N in sorted(front):
        e = front[N][0]
        e['trade'] = trade(e['P'], mod, f, e['y0'], e['x0']) if left() > 20 and '--no-trade' not in a else []
        save(N)
        log('DONE count %d class %d loss %.4f how %s | states %s | LP trade of the first %s' % (N, N % c1, lossN(N), e['how'],
            ' '.join('%.4f,%.4f' % (v['y0'], v['x0']) for v in front[N]), ' '.join('%.4f,%.4f' % p for p in e['trade'])))
    return 0


def cmd_adopt(a):
    """zone_corner.py adopt BASE.pkl OUTDIR: every corner of BASE.pkl as kept states at its f: the smallest sum, and the
    smallest y0 and the smallest x0 when they differ (the LP with free angles; the tables of modules.py keep the angles)."""
    base = pickle.load(open(a[0], 'rb')); outdir = a[1]; k = 0
    for b in base:
        mod = cmod(b['c1'], b['c2'], b['lean1'], b['lean2']); f = b['f']
        how = 'the library corner carried to this f, angles free'
        fr = [dict(y0=b['y0'], x0=b['x0'], P=b['P'], how=how)]
        for cost in ((1.0, 0.02), (0.02, 1.0)):
            r = compact(b['P'], mod, f, b['y0'], b['x0'], cost=cost, rounds=1)
            le = lengths(r[2], mod, f, r[0] + 1e-7, r[1] + 1e-7) if r is not None else None
            if le is not None and all(abs(le[0] - e['y0']) > 4e-3 or abs(le[1] - e['x0']) > 4e-3 for e in fr):
                fr.append(dict(y0=le[0], x0=le[1], P=r[2], how=how + ', one length first'))
        _save(outdir, 'corner-%s-%d-s0' % (b['id'], b['count']), dict(front=fr, y0=b['y0'], x0=b['x0'], P=b['P'], how=how,
              base=dict(id=b['id'], src=b['src'], licence=b['licence']), c1=b['c1'], c2=b['c2'], lean1=b['lean1'], lean2=b['lean2'], f=f,
              count=b['count'], seed=0, cpu=0.0, tag=b['id']))
        k += len(fr)
    print('%d corners, %d states' % (len(base), k))
    return 0


def cmd_sweep(a):
    """zone_corner.py sweep BASE.pkl OUTDIR [--part I/K] [--slot S] [--seed S] [--deadline FILE] [--down D]
    Hops on the own count of every corner of BASE.pkl in turn, S seconds each: more states of its trade curve.
    --down D: also delete up to D squares first and give each of those counts S seconds (the next count classes)."""
    base = pickle.load(open(a[0], 'rb'))
    pi, pk = (int(v) for v in _opt(a, '--part', '0/1', str).split('/'))
    slot = _opt(a, '--slot', 40.0); dl = _opt(a, '--deadline', None, str); seed = _opt(a, '--seed', 1, int)
    down = _opt(a, '--down', 0, int)                 # also the counts with up to this many squares deleted
    mv = 'self,delete,hop' if down else 'self,hop'
    if '--resume' in a: mv = 'resume,' + mv          # the kept states of earlier runs of the corner in OUTDIR at this f
    for j, b in enumerate(base):
        if j % pk != pi: continue
        if '--mixed' in a and b['c1'] == b['c2']: continue     # only arms of two sizes
        if dl and os.path.exists(dl) and time.time() > float(open(dl).read().strip()) - slot: break
        cmd_search([a[0], a[1], '--id', b['id'], '--moves', mv, '--down', str(down), '--beam', '4',
                    '--minutes', str((slot * (1 + down) + 8 + 10 * down) / 60), '--slot', str(slot), '--tail', '6',
                    '--seed', str(seed), '--no-trade'] + (['--deadline', dl] if dl else []))
    return 0


def cmd_table(a):
    """zone_corner.py table OUTDIR ZONESDIR TSV [--per 4]: for every (arms, f, count) the states no other state beats in
    both lengths (over every run in OUTDIR), up to --per of them as module files with a picture, and a row each. Rows
    are appended to TSV (kind 'corner'); the 'length' column holds y0+x0."""
    outdir, zdir, tsv = a[0], a[1], a[2]; per = _opt(a, '--per', 4, int)
    tag = _opt(a, '--tag', '', str)                  # appended to every name, so a rebuilt table never reuses an old id
    old = {}                                         # --over ZDIR,...: only states below the stored corners of these dirs
    for d in [v for v in _opt(a, '--over', '', str).split(',') if v]:
        for q in pickle.load(open(d + '/corners.pkl', 'rb')):
            k = (q['c1'], q['c2'], round(q['f0'], 4), q['count']); old[k] = min(old.get(k, math.inf), q['loss0'])
    recs = collections.defaultdict(list); cpu = collections.Counter(); runs = collections.Counter()
    for p in sorted(glob.glob(outdir + '/corner-*.pkl') + glob.glob(outdir + '/*/corner-*.pkl')):
        r = pickle.load(open(p, 'rb')); key = (r['c1'], r['c2'], round(r['f'], 4), r['count'])
        cpu[key] += r.get('cpu', 0.0); runs[key] += 1
        for e in r.get('front') or [r]: recs[key].append(dict(e, base=r['base'], lean1=r['lean1'], lean2=r['lean2'], f_run=r['f']))
    os.makedirs(zdir, exist_ok=True)
    lines = []; mods = []
    for key in sorted(recs):
        c1, c2, f, n = key
        fr = []; w = weights(cmod(c1, c2), f)       # the first state is the one of lowest loss
        for e in sorted(recs[key], key=lambda e: w[0] * e['y0'] + w[1] * e['x0']):
            if not any(v['y0'] <= e['y0'] + 1e-6 and v['x0'] <= e['x0'] + 1e-6 for v in fr): fr.append(e)
        pick = fr[:1] + sorted(fr[1:], key=lambda e: e['y0'])[:1] + sorted(fr[1:], key=lambda e: e['x0'])[:1]
        pick += [e for e in fr if not any(e is v for v in pick)]
        seen = []; pick = [e for e in pick if not any(e is v for v in seen) and not seen.append(e)][:per]
        for j, r in enumerate(pick):
            if r['how'] == 'the library corner at this f' and '--all' not in a: continue      # the library has it
            mod = cmod(c1, c2, r['lean1'], r['lean2'])
            if loss_of(mod, r.get('f_run', f), n, r['y0'], r['x0']) > old.get(key, math.inf) - 1e-3: continue
            name = 'zc%dx%d-%df%04d%s%s' % (c1, c2, n, round(f * 10000), 'abcdefgh'[j], tag)
            q = as_module(r['P'], mod, r.get('f_run', f), r['y0'], r['x0'], name + '.C', r['how'], r['base'])   # the state belongs to its run's exact f, not the rounded key
            q['trade'] = r.get('trade', [])
            pickle.dump(q, open('%s/%s.pkl' % (zdir, name), 'wb')); mods.append(q)
            picture(r['P'], mod, r.get('f_run', f), r['y0'], r['x0'], '%s/%s.svg' % (zdir, name), '%s count %d class %d y0 %.5f x0 %.5f loss %.3f' % (name, n, n % c1, r['y0'], r['x0'], q['loss0']))
            tr = ' '.join('%.4f,%.4f' % p for p in q['trade'])
            lines.append('corner\t%dx%d\t%s\t%d\t%d\t%.6f+%.6f\t%.4f\t%s of %s; state %d of %d on the trade curve%s; %d runs, %.0f CPU-s\t%s\n' % (
                c1, c2, ('%.6f' % q['f0']) if tag else ('%.4f' % f), n, n % c1, r['y0'], r['x0'], q['loss0'], r['how'], r['base']['id'], j + 1, len(fr),
                ('; LP trade ' + tr) if tr else '', runs[key], cpu[key], 'zones/%s.pkl' % name))
            print(lines[-1].strip())
    with open(tsv, 'a') as h: h.writelines(lines)
    pickle.dump(mods, open(zdir + '/corners.pkl', 'wb'))
    return 0


def check_corner(q, f=None):
    """A stored corner at its stored f0 (or at f), y0 and x0 by the exact test. -> (legal, gap inside and against the
    grid, gap to stack 1, gap to stack 2, squares beyond a stack). Legal: inside >= TOL, both stacks >= 0, none beyond."""
    mod = cmod(q['c1'], q['c2'], q['lean1'], q['lean2'])
    g_in, g1, g2, b = exact(q['P'], mod, q['f0'] if f is None else f, q['y0'], q['x0'])
    return g_in >= TOL and g1 >= 0 and g2 >= 0 and b == 0, g_in, g1, g2, b


def cmd_check(a):
    """zone_corner.py check PATH ...: every stored corner (zc*.pkl files of a zones dir, or one file) at the f stored with
    it. Prints the illegal ones and a count."""
    files = []
    for p in a:
        if p.startswith('--'): continue
        files += sorted(glob.glob(p + '/zc*.pkl')) if os.path.isdir(p) else [p]
    bad = 0; worst = math.inf
    for p in files:
        q = pickle.load(open(p, 'rb'))
        ok, g_in, g1, g2, b = check_corner(q)
        worst = min(worst, g_in, g1, g2)
        if not ok:
            bad += 1
            print('ILLEGAL %s f0 %.6f inside %.2e stack1 %.2e stack2 %.2e beyond %d' % (os.path.basename(p), q['f0'], g_in, g1, g2, b))
    print('%d of %d stored corners illegal at their stored f; smallest gap %.2e' % (bad, len(files), worst))
    return 1 if bad else 0


def cmd_merge(a):
    """library.pkl and lens.pkl of modules.py with the kept corners added (tables by modules.tabulate)."""
    work, zdir, new = a[0], a[1], a[2]
    cut = _opt(a, '--max-loss', 4.6)
    lib = pickle.load(open(work + '/library.pkl', 'rb')); lens = pickle.load(open(work + '/lens.pkl', 'rb'))
    have = {q['id'] for q in lib['mods']}
    os.makedirs(new, exist_ok=True)
    also = _opt(a, '--also', None, str)              # a second library: its zone-search modules come along with their tables
    if also:
        l2 = pickle.load(open(also + '/library.pkl', 'rb')); t2 = pickle.load(open(also + '/lens.pkl', 'rb')); k = 0
        for q in l2['mods']:
            if q['tag'] == 'z' and q['id'] not in have and q['id'] in t2:
                lib['mods'].append(q); lens[q['id']] = t2[q['id']]; have.add(q['id']); k += 1
        print('%d zone-search modules from %s' % (k, also), flush=True)
    zc = pickle.load(open(zdir + '/corners.pkl', 'rb'))
    if '--drop-old' in a:                            # corners of a zone search that are not in ZONESDIR (stored with a rounded f before f97bc88)
        keep_ids = {q['id'] for q in zc}
        gone = {q['id'] for q in lib['mods'] if q['kind'] == 'corner' and q['tag'] == 'z' and q['id'] not in keep_ids}
        lib['mods'] = [q for q in lib['mods'] if q['id'] not in gone]
        for i in gone: lens.pop(i, None)
        have -= gone
        print('dropped %d corners of a zone search that ZONESDIR does not hold' % len(gone), flush=True)
    pre = {}
    for p in [v for v in _opt(a, '--tables', '', str).split(',') if v]:
        pre.update(pickle.load(open(p, 'rb')))       # tables made by `tables`, in parts
    for q in zc:
        if q['loss0'] > cut or q['id'] in have: continue
        t = pre[q['id']] if q['id'] in pre else M.tabulate(q)
        if all(o is None for o in t['own']): print(q['id'], 'no table'); continue
        lib['mods'].append(q); lens[q['id']] = t
        print('%s count %d class %d loss %.4f: %d of %d table points' % (q['id'], q['count'], q['count'] % q['c1'], q['loss0'],
              int((~np.isnan(t['tab'][:, 0])).sum()), t['tab'][:, 0].size), flush=True)
    pickle.dump(lib, open(new + '/library.pkl', 'wb')); pickle.dump(lens, open(new + '/lens.pkl', 'wb'))
    return 0


def cmd_tables(a):
    """zone_corner.py tables ZONESDIR OUT.pkl [--part I/K] [--max-loss X]: modules.tabulate on the corners of a zones
    dir (one part of them), saved as {id: table} for `merge --tables`."""
    zdir, out = a[0], a[1]
    pi, pk = (int(v) for v in _opt(a, '--part', '0/1', str).split('/')); cut = _opt(a, '--max-loss', 4.6)
    zc = sorted(pickle.load(open(zdir + '/corners.pkl', 'rb')), key=lambda q: q['id'])
    res = {}
    for j, q in enumerate(zc):
        if j % pk != pi or q['loss0'] > cut: continue
        res[q['id']] = M.tabulate(q)
        if len(res) % 20 == 0: _save(os.path.dirname(os.path.abspath(out)), os.path.basename(out)[:-4], res)
    _save(os.path.dirname(os.path.abspath(out)), os.path.basename(out)[:-4], res)
    print('%d tables' % len(res))
    return 0


def carry(q, f, soft=False, log=None):
    """A library corner carried from its own f to f along the knots of modules.path, then compacted with free angles.
    soft: where the LP step finds no state (the corner locks), the squares at an arm's tilt are turned to the new
    tilt and the soft search pushes the stacks out and squeezes them back (the corner may lengthen there).
    -> (y0, x0, P, mod) or None"""
    mod = cmod(q['c1'], q['c2'], q['lean1'], q['lean2'])
    at = M.corner_len(q, q['f0'], q['P'], q['y0'] + 1e-6, q['x0'] + 1e-6)
    for g in M.path(q['f0'], f):
        if at is None: return None
        r = M.corner_len(q, float(g), at[2], at[0] + 0.02, at[1] + 0.02)
        if r is None and soft:
            new = [q['lean1'] * math.degrees(M.flush_tilt(q['c1'], g)) if q['grp'][grp[0]] == 1 else
                   q['lean2'] * math.degrees(M.flush_tilt(q['c2'], g)) for grp in q['rig']]
            sz = settle_zone(M.retilt(at[2], q['rig'], new), mod, float(g), at[0] + 0.1, at[1] + 0.1)
            r = None if sz is None else (sz[0], sz[1], sz[2])
            if log: log('f %.3f: the LP locks; soft step %s' % (g, 'none' if r is None else '%.5f + %.5f' % r[:2]))
        at = r
    if at is None: return None
    r = compact(at[2], mod, f, at[0], at[1])
    if r is None: return None
    le = lengths(r[2], mod, f, r[0] + 1e-7, r[1] + 1e-7)
    return None if le is None else (le[0], le[1], r[2], mod)


def cmd_needs(a):
    """zone_corner.py needs LIBWORK BAR.csv OUT.pkl [LO HI] [--slack S] [--top K] [--margin D] [--part I/K]
    For every n, the generator's choices that fit within S of side above the bar: the corner, its count, and the two
    caps it must meet at the target f (the bar's f less D): what arm 1 and arm 2 leave for the corner there.
    excess = how far the corner's tabulated states are from both caps (<= 0: the choice already fits)."""
    work, details, out = a[:3]
    lo, hi = (int(a[3]), int(a[4])) if len(a) > 4 and not a[3].startswith('--') else (300, 1000)
    pi, pk = (int(v) for v in _opt(a, '--part', '0/1', str).split('/'))
    slack = _opt(a, '--slack', 0.0015); top = _opt(a, '--top', 4, int); margin = _opt(a, '--margin', 1e-4)
    bar = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    lib = _library(work); rows = []
    need = _need(lib, a)                             # since round 15: only choices that hold a zone-search corner
    ns = [int(v) for v in open(_opt(a, '--ns', '', str)).read().split()] if '--ns' in a else range(lo, hi + 1)
    for n in ns:
        if n % pk != pi: continue
        m = math.isqrt(n - 1)
        if bar[n] >= m + 1 - 1e-9: continue
        fb = bar[n] - m; ft = fb - margin
        for f, stop, C, F1, F2, s1, s2 in lib.best(n, top=top, below=fb + slack, depth=0.03, need=need):
            L1 = float(np.interp(ft, M.FF, F1['L'])); L2 = float(np.interp(ft, M.FF, F2['L']))
            if not (np.isfinite(L1) and np.isfinite(L2)): continue
            a1 = m + ft - s1 * M.pitch(C['c1'], ft) - L1; a2 = m + ft - s2 * M.pitch(C['c2'], ft) - L2
            Y = np.array([np.interp(ft, M.FF, v) for v in C['Y']]); X = np.array([np.interp(ft, M.FF, v) for v in C['X']])
            ex = np.maximum(Y - a1, X - a2); ex = float(np.nanmin(ex)) if np.isfinite(ex).any() else math.inf
            rows.append(dict(n=n, m=m, bar=bar[n], f_fit=f, ft=ft, C=C['id'], F1=F1['id'], F2=F2['id'], s1=s1, s2=s2, a1=a1, a2=a2,
                             excess=ex, c1=C['c1'], c2=C['c2'], count=C['count']))
            print('n=%d bar %.6f fit %.6f (%+.6f) %s %s %s %d,%d caps %.5f %.5f excess %+.5f' % (n, bar[n], m + f, m + f - bar[n], C['id'],
                  F1['id'], F2['id'], s1, s2, a1, a2, ex), flush=True)
    pickle.dump(rows, open(out, 'wb'))
    print('%d choices on %d n' % (len(rows), len({r['n'] for r in rows})))
    return 0


def cmd_capsearch(a):
    """zone_corner.py capsearch LIBWORK NEEDS.pkl OUTDIR [--part I/K] [--slot S] [--deadline FILE] [--max-excess E]
    [--seed S] [--starts K] [--first N:C,...]: hops under a cap. For every row of `needs` (smallest excess first), the corner carried to the target f
    of that n, then hops on the larger excess over the two caps for S seconds, stopping when both fit. Every state
    near the best goes into a run file that `table` reads."""
    work, needs, outdir = a[:3]
    pi, pk = (int(v) for v in _opt(a, '--part', '0/1', str).split('/'))
    slot = _opt(a, '--slot', 60.0); dl = _opt(a, '--deadline', None, str); mx = _opt(a, '--max-excess', 0.06)
    seed = _opt(a, '--seed', 1, int); rng = np.random.default_rng(seed); starts = _opt(a, '--starts', 1, int)
    first = [tuple(v.split(':')) for v in _opt(a, '--first', '', str).split(',') if v]   # n:corner pairs that run first
    lib = pickle.load(open(work + '/library.pkl', 'rb')); mods = {q['id']: q for q in lib['mods']}
    rows = sorted([r for r in pickle.load(open(needs, 'rb')) if r['excess'] <= mx and r['excess'] > 0], key=lambda r: r['excess'])
    one = {}                                         # the smallest excess of each (n, corner): other far zones give other caps
    for r in rows: one.setdefault((r['n'], r['C']), r)
    rows = sorted(one.values(), key=lambda r: (('%d' % r['n'], r['C']) not in first, r['excess']))
    done = set()
    for j, r in enumerate(rows):
        if j % pk != pi: continue
        if dl and os.path.exists(dl) and time.time() > float(open(dl).read().strip()) - slot: break
        key = (r['n'], r['C'], round(r['a1'], 4), round(r['a2'], 4))
        if key in done: continue
        done.add(key)
        q = mods[r['C'].rstrip('~')] if r['C'] in mods or r['C'].rstrip('~') in mods else None
        if q is None or '^' in r['C']: continue
        t0 = time.time(); cpu0 = time.process_time(); f = r['ft']; caps = (r['a1'], r['a2'])
        # --starts K (since round 16): the corner carried from its own f, and the K - 1 library corners of the same arms,
        # leans and count with the f0 nearest the target (its other stored states), each carried to the target f
        sib = sorted([p for p in lib['mods'] if p['kind'] == 'corner' and p['id'] != q['id'] and not p['id'].endswith('~') and not p['miss']
                      and (p['c1'], p['c2'], p['lean1'], p['lean2'], p['count']) == (q['c1'], q['c2'], q['lean1'], q['lean2'], q['count'])],
                     key=lambda p: abs(p['f0'] - f))[:starts - 1]
        fr = []
        def seen(yy, xx, PP, kind):
            if any(e['y0'] <= yy + 1e-6 and e['x0'] <= xx + 1e-6 for e in fr): return
            fr[:] = [e for e in fr if not (yy <= e['y0'] + 1e-6 and xx <= e['x0'] + 1e-6)] + [dict(y0=yy, x0=xx, P=PP, how='hops under the caps of n=%d' % r['n'])]
        e0 = None; tops = []; mod = None
        for s in [q] + sib:
            st = carry(s, f, soft=True)
            if st is None: print('n=%d %s does not reach f %.5f' % (r['n'], s['id'], f), flush=True); continue
            y, x, P, mod = st
            if e0 is None: e0 = max(y - caps[0], x - caps[1])
            best = [(max(y - caps[0], x - caps[1]), y, x, P)]
            seen(y, x, P, 'start')
            for cost, cp in (((0.02, 1.0), (caps[0], None)), ((1.0, 0.02), (None, caps[1])), ((1.0, 1.0), caps)):   # the trade curve under one cap
                lp = compact(P, mod, f, y, x, cost=cost, caps=cp)
                le = lengths(lp[2], mod, f, lp[0] + 1e-7, lp[1] + 1e-7) if lp is not None else None
                if le is not None: seen(le[0], le[1], lp[2], 'capped LP'); best.append((max(le[0] - caps[0], le[1] - caps[1]), le[0], le[1], lp[2]))
            tops.append(min(best, key=lambda t: t[0]))
            print('n=%d %s from %s (f0 %.5f): excess %+.5f' % (r['n'], r['C'], s['id'], s['f0'], tops[-1][0]), flush=True)
        if not tops: continue
        tops.sort(key=lambda t: t[0]); k = 0; won = collections.Counter()
        if tops[0][0] <= 0: yb, xb, Pb, won = tops[0][1], tops[0][2], tops[0][3], {'capped LP': 1}
        else:
            yb = xb = math.inf; Pb = None
            for ex, y, x, P in tops:                 # the slot is shared among the starts, best start first
                y1, x1, P1, k1, w1 = hops(P, mod, f, y, x, slot / len(tops), rng, caps=caps, seen=seen)
                k += k1; won.update(w1)
                if max(y1 - caps[0], x1 - caps[1]) < max(yb - caps[0], xb - caps[1]): yb, xb, Pb = y1, x1, P1
                if yb <= caps[0] and xb <= caps[1]: break
        seen(yb, xb, Pb, 'best')
        fits = yb <= caps[0] and xb <= caps[1]
        fr.sort(key=lambda e: max(e['y0'] - caps[0], e['x0'] - caps[1]))
        e1 = max(yb - caps[0], xb - caps[1])
        P = Pb
        print('n=%d %s count %d f %.5f caps %.5f %.5f: excess %+.5f -> %+.5f after %d hops %s (%.0f s)%s' % (r['n'], r['C'], len(P), f, caps[0], caps[1],
              e0, e1, k, won, time.time() - t0, ' FITS' if fits else ''), flush=True)
        if e1 < e0 - 1e-6:
            _save(outdir, 'corner-%s-%d-cap%d' % (r['C'], len(P), r['n']), dict(front=fr[:6], y0=fr[0]['y0'], x0=fr[0]['x0'], P=fr[0]['P'],
                  how=fr[0]['how'], base=dict(id=q['id'], src=q['src'], licence=q['licence']), c1=q['c1'], c2=q['c2'], lean1=q['lean1'],
                  lean2=q['lean2'], f=f, count=len(P), seed=seed, cpu=time.process_time() - cpu0, tag=q['id'], caps=caps, n=r['n'], fits=fits))
    return 0


def _need(lib, a):
    """the corners a choice must hold: --new ZDIR, the corners of that zones dir; else every corner of a zone search.
    The need set holds corners only, so a choice must hold one of them as its corner: the library keeps only those
    corners, and the generator no longer works out the far-zone options of every other corner first (minutes, not
    an hour, on a library of 8,000 modules)."""
    zd = _opt(a, '--new', None, str)
    if zd: need = {q['id'] for q in pickle.load(open(zd + '/corners.pkl', 'rb'))} & set(lib.mods)
    else: need = {q['id'] for q in lib.mods.values() if q['kind'] == 'corner' and q['tag'] == 'z'}
    if all(lib.mods[i]['kind'] == 'corner' for i in need):
        lib.corners = [C for C in lib.corners if C['id'] in need]
    return need


def _library(work):
    return M.Library(work, only=(lambda q: q['tag'] in ('h', 'z') or q.get('ours') or any(k in q['licence'] for k in M.OK_LICENCE)))


def cmd_predict(a):
    """The generator of modules.py on every n below the plain grid; a choice with a module of a zone search is marked."""
    work, details, out = a[:3]
    lo, hi = (int(a[3]), int(a[4])) if len(a) > 4 and not a[3].startswith('--') else (300, 1000)
    part = _opt(a, '--part', '0/1', str); pi, pk = (int(v) for v in part.split('/'))
    slack = _opt(a, '--slack', 0.004)                # only choices predicted below held plus this
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    lib = _library(work)
    need = _need(lib, a)
    rows = []
    ns = [int(v) for v in open(_opt(a, '--ns', '', str)).read().split()] if '--ns' in a else range(lo, hi + 1)
    for n in ns:
        if n % pk != pi: continue
        m = math.isqrt(n - 1)
        if held[n] >= m + 1 - 1e-9: continue
        r = lib.best(n, top=1, need=need, below=held[n] - m + slack, depth=_opt(a, '--depth', 0.05))
        if not r: continue
        f, stop, C, F1, F2, s1, s2 = r[0]
        rows.append((n, held[n], m + f, m + f - held[n], C['id'], F1['id'], F2['id'], s1, s2))
        if m + f < held[n] + 0.0015: print('n=%d held %.6f predicted %.6f (%+.6f) %s %s %s stacks %d,%d' % rows[-1], flush=True)
    with open(out, 'w') as h:
        h.write('n\theld_side\tpredicted_side\tpredicted_minus_held\tcorner\tfar1\tfar2\tstacks1\tstacks2\n')
        for r in rows: h.write('%d\t%.6f\t%.6f\t%+.6f\t%s\t%s\t%s\t%d\t%d\n' % r)
    print('n with a choice that holds a new corner: %d; predicted below held: %d; within 0.003: %d' % (
        len(rows), sum(r[3] < 0 for r in rows), sum(r[3] < 0.003 for r in rows)))
    return 0


def quench(n, path, L):
    """The fq quench of engine_polish.py on one built layout (default flags, then the polish flags, up to 3 passes, each
    win certified by floatsafe). A certified smaller layout replaces the file. -> the side of the file"""
    import tempfile, shutil, engine_polish, floatsafe
    rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(path))]
    fr = floatsafe.work((n, rows))[1]            # start fq from the certified file, as the polish lane does: from the raw
    sq = [(float(r['x']), float(r['y']), float(r['angle'])) for r in (fr or rows)]   # build (contacts at 0) fq found nothing on 551
    d = tempfile.mkdtemp(prefix='zcq', dir=os.environ.get('SQ_TMP'))
    tmo = float(os.environ.get('ZC_FQ_TIMEOUT', 0)) or (1800 if n >= 900 else 1000 if n >= 700 else 600)   # since round 16: the 983
    q0 = engine_polish.quench                                                                              # quench ran into fq's 600 s
    engine_polish.quench = lambda s, X, fl=(), **k: q0(s, X, fl, timeout=tmo)
    try:
        t0 = time.time(); _, s0, s1, log = engine_polish.job((n, sq, d, 3))
    finally:
        engine_polish.quench = q0
    if s1 is not None and os.path.exists('%s/%d.csv' % (d, n)):
        shutil.copy('%s/%d.csv' % (d, n), path + '.tmp'); os.replace(path + '.tmp', path)
        print('n=%d QUENCH %.9f -> %.9f (%+.3e of side, %.0f s)' % (n, s0, s1, s1 - s0, time.time() - t0), flush=True); L = s1
    else: print('n=%d quench: no certified gain on %.9f (%.0f s)' % (n, s0, time.time() - t0), flush=True)
    shutil.rmtree(d, ignore_errors=True)
    return L


def cmd_quench(a):
    """zone_corner.py quench RAWDIR [N ...]: the fq quench on built layouts (n-k.csv) already in RAWDIR"""
    for p in sorted(glob.glob(a[0] + '/*.csv')):
        n = int(os.path.basename(p).split('-')[0])
        if len(a) > 1 and str(n) not in a[1:]: continue
        quench(n, p, None)
    return 0


def cmd_build(a):
    """The build step of modules.py for the choices of N that hold a new corner. Certify RAWDIR with `modules.py take`.
    --quench D: a build that ends less than D of side above the bar (5e-4 is a good value) gets the fq quench of the
    polish lane before the file is final."""
    work, raw, details, n = a[0], a[1], a[2], int(a[3])
    top = _opt(a, '--top', 2, int); fq = _opt(a, '--fq', None, str); slack = _opt(a, '--slack', 0.003); gate = _opt(a, '--gate', 0.0012)
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}[n]
    lib = _library(work); os.makedirs(raw, exist_ok=True); m = math.isqrt(n - 1); done = 0
    need = _need(lib, a); skip = _opt(a, '--skip', 0, int)
    for f, stop, C, F1, F2, s1, s2 in lib.best(n, top=4 * (top + skip), below=held - m + slack, need=need):
        if done >= top + skip: break                 # --top counts the choices that have a start, of the best 4 * top
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
        if side > held + gate:                       # the squeeze takes 0.0002 to 0.0017 off a start; a start further above the bar is left
            print('n=%d %s stacks %d,%d predicted %.6f start %.6f: left, the start is %.6f above the bar' % (n, tag, s1, s2, m + f, side, side - held), flush=True); continue
        if done < skip:                              # --skip K: the first K choices with a start were built by an earlier run
            done += 1; continue
        Q, L = M._squeeze(n, P, fq, log=lambda s: print(s, flush=True))
        done += 1
        M.write_layout('%s/%d-%d.csv' % (raw, n, done), n, Q)
        if '--quench' in a and L < held + _opt(a, '--quench', 5e-4):  # the quench of the polish lane: fq with its default flags, then its
            L = quench(n, '%s/%d-%d.csv' % (raw, n, done), L)           # polish flags, up to 3 passes (it found 1e-6 to 1e-5 in our builds)
        json.dump(dict(n=n, predicted=m + f, start=side, built=L, held=held, stop=stop, stacks=[s1, s2],
                       modules=[dict(id=x['id'], source=x['q']['src'], licence=x['q']['licence']) for x in (C, F1, F2)]),
                  open('%s/%d-%d.json' % (raw, n, done), 'w'))
        print('n=%d BUILT %s predicted %.6f built %.9f held %.9f (%+.6f)' % (n, tag, m + f, L, held, L - held), flush=True)
    return 0


if __name__ == '__main__':
    cmds = dict(base=cmd_base, zbase=cmd_zbase, control=cmd_control, search=cmd_search, sweep=cmd_sweep, adopt=cmd_adopt, table=cmd_table, check=cmd_check,
                tables=cmd_tables, needs=cmd_needs, capsearch=cmd_capsearch, merge=cmd_merge, predict=cmd_predict, build=cmd_build,
                quench=cmd_quench)
    sys.exit(cmds[sys.argv[1]](sys.argv[2:]) or 0)
