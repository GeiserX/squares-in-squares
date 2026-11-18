#!/usr/bin/env python3
"""Modules of a two-arm layout: cut every layout into its end zones, then build layouts from the zones.

  modules.py library  WORK HELD.csv RESULTS_DIR [TAG=MERGED_DIR ...]   cut the held file and the public bests
  modules.py lens     WORK [--jobs 2]            length of every module on a grid of f (the contact LP)
  modules.py rebuild  WORK                       control 1, exact: every layout from its own modules
  modules.py control  WORK                       control 1 from the tables, and control 2
  modules.py cover    WORK                       what the library holds, by stack size and band of f
  modules.py build    WORK RAWDIR DETAILS.csv N  build the best choices for N and squeeze them
  modules.py take     DETAILS.csv TAKEDIR RAWDIR certify the builds the lane's way
  modules.py export   WORK OUT.tsv               the library as one table
  modules.py model    WORK DETAILS.csv BOARD.json    the zone-loss model on the held file
  modules.py predict  WORK DETAILS.csv BOARD.json OUT.tsv
  modules.py start    WORK OUT.csv N CORNER FAR1 FAR2 S1 S2 F      the start layout of one prediction
  modules.py grow     WORK RESULTS_DIR TAG=PATH ...   cut more layouts into the library (a take dir or a held file)
  modules.py slide    WORK SOURCE ...            give every module the slide of the rest beside it (cut again from its layout)
  modules.py loo      WORK OUT.tsv [--part I/K]  leave one out: predict every held layout without the modules of its n
  modules.py queue    WORK DETAILS.csv OUT.tsv [--top 3] [--slack S] [--need IDS] [--part I/K] [--ns FILE]
  modules.py job      WORK RAWDIR DETAILS.csv NAME N CORNER FAR1 FAR2 S1 S2 F [--fq PATH] [--squeeze slp|family|both]
  modules.py grant    WORK OUT.pkl [--part I/K] [--levels G,G,...] | WORK --merge OUT.pkl ...   corners with a grant they
                     were not found with

A two-arm layout has side L = m + f and n = m^2 + k squares. It is turned so that arm 1 (stacks of c1 squares
set face to face, each stack flush between the left wall and the line x = W1 = c1 - 1 + f) runs up the left
wall and arm 2 (c2, W2) runs along the bottom wall. A flush stack has tilt t with c cos t + sin t = c - 1 + f
and takes p = 1 / cos t of wall. The far face of the last flush stack of an arm is a straight cut across the
whole strip, and so is the near face of the first one. These four cuts split the layout into

  corner    all that lies before the first flush stack of both arms
  run 1, 2  s1 and s2 flush stacks
  far 1, 2  all that lies beyond the last flush stack of an arm, up to the end wall
  rest      the grid of (m - c1 + 1)(m - c2 + 1) upright squares on the far corner

A cut is measured where it crosses the middle line of its strip. Then, with y0 and x0 the two lengths of the
corner (from the bottom wall and from the left wall), and l1, l2 the lengths of the far zones,

  y0 + s1 p1 + l1 = m + f        x0 + s2 p2 + l2 = m + f
  n = corner + s1 c1 + far 1 + s2 c2 + far 2 + rest

hold exactly. If the stacks ran through a zone it would hold c cos t squares per unit of wall, so the loss
of a far zone is c cos t l - count and the loss of a corner is c1 cos t1 y0 + c2 cos t2 (x0 - W1) - count.
The three losses add up to k_flush - k of the zone-loss model. A zone may take the place of a few cells of
the rest; its count is then lowered by those cells and it carries their list.

The length a module takes at another f comes from its geometry: the squares at the arm's tilt are turned to
the flush tilt of the new f, every other square keeps its angle, and a fixed-angle contact LP (exact for
frozen angles) pushes the flush stack next to the module as far towards the end wall as the module allows.
A layout put together from modules at their LP positions is legal by construction, so a predicted side is
an upper bound for that choice of modules.

Our own code. Reads packings as data only (run with python -I). Imports frontier_read, frontier_stacks,
frontier_profile and methods_lp of this lane.
"""
import csv, glob, json, math, os, pickle, sys, collections
csv.field_size_limit(2**30)  # Full source chains can exceed the default 128 KiB.

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I drops the script dir
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
from frontier_read import normal
from frontier_stacks import stacks
from frontier_profile import flush_arms
from methods_lp import best_axes, pair_list, half

OK_LICENCE = ('Apache 2.0', 'Apache-2.0', 'CC BY 4.0', 'CC-BY-4.0', 'CC0')
FLUSH_TOL = 3e-3
LOOSE_TOL = 1e-2                                         # a layout that does not cut at FLUSH_TOL is cut again with arms
#   flush to this (stacks a little wider or narrower than their strip); a layout that cuts at FLUSH_TOL keeps that cut
GRID = np.round(np.arange(0.600, 0.9951, 0.005), 3)      # the f values a module's length is tabulated at
COST = ((1.0, 0.02), (1.0, 0.5), (1.0, 1.0), (0.5, 1.0), (0.02, 1.0))   # the corner's trade between its two lengths
CSPAN = 0.06                                             # the same for a corner
SPAN = 0.10                                              # a module is used within this distance of the f it was found at
GAP = 0.0                                                # the module LPs allow contact; the squeeze of a built layout opens the gaps
DEEP = 0                                                 # cells of the rest beside a zone that go to the zone when their square
#   has slid off the grid. 0: the rest is kept as a rigid grid (a legal choice, so a prediction stays an upper bound).
#   3 was tried: a corner that leans on a slid column then solves (n = 998), but a far zone whose 18 cells all slid
#   (n = 814) does not, because a row of the rest slides as a whole and ties the zones at its two ends together.
SLID = 1e-4                                              # a square of the rest this far off its cell has slid
EXACT = 0.03                                             # degrees: a stack this close to an arm's tilt turns with the arm
POKE = 2e-5                                              # a square of a zone this far past the grid edge of its strip pokes
SLIDE = True                                             # row 0 and column 0 of the rest keep the slide they were found with
CHORD = False                                            # a corner holds only the 5 states it was found in (one per cost of
#   COST). True: also 2 points on the chord between two neighbours, as before round 12. The set of a corner's states is
#   not convex, so a point on the chord is not a state: on 2026-11-12 every prediction of the 934 kind (934, 873, 814,
#   predicted below held, built above it or with no start) fitted only at such a point.


# ----------------------------------------------------------------------------------------------- the model

def flush_tilt(c, f):
    """t with c cos t + sin t = c - 1 + f on the falling branch (tan t > 1/c)."""
    return math.atan2(1.0, c) + math.acos(min(1.0, (c - 1 + f) / math.hypot(c, 1.0)))


def pitch(c, f):
    return 1.0 / math.cos(flush_tilt(c, f))


def k_flush(m, f, c1, c2):
    g1 = f - math.sin(flush_tilt(c1, f)); g2 = f - math.sin(flush_tilt(c2, f))
    return (m + f) * g1 + (c1 - 1) * f + (m - c1 + 1) * g2


# ----------------------------------------------------------------------------------------------- the cut

def read_layouts(path):
    """-> {n: [(x, y, angle)]} from a submission file or a per-n file (columns by name)."""
    P = collections.defaultdict(list)
    with open(path, newline='') as h:
        for r in csv.DictReader(h):
            P[int(r['n'])].append((float(str(r['x']).lstrip('s')), float(str(r['y']).lstrip('s')), float(str(r['angle']).lstrip('s'))))
    return P


def arms_at(A, s, m, tol):
    """frontier_profile.flush_arms with the flush tolerance tol (it is that function at tol = 3e-3)"""
    if tol == 3e-3: return flush_arms(A, s, m)
    f = s - m
    T = A[np.abs(A[:, 2]) > 0.5]
    if len(T) < 12: return []
    chains, _ = stacks(T)
    arms = collections.defaultdict(list)
    for ch in chains:
        c = len(ch)
        if c < 5: continue
        t = math.radians(abs(float(np.median(T[ch, 2]))))
        if abs(c * math.cos(t) + math.sin(t) - (c - 1 + f)) > tol: continue
        ax = T[ch[-1], :2] - T[ch[0], :2]; cen = T[ch, :2].mean(0); W = c - 1 + f
        if abs(ax[0]) > abs(ax[1]): wall = 'L' if cen[0] < W / 2 + 0.05 else 'R' if cen[0] > s - W / 2 - 0.05 else None
        else: wall = 'B' if cen[1] < W / 2 + 0.05 else 'T' if cen[1] > s - W / 2 - 0.05 else None
        if wall: arms[(wall, c)].append((cen, t))
    out = [(w, c, float(np.median([x for _, x in v])), [p for p, _ in v]) for (w, c), v in arms.items() if len(v) >= 3]
    return sorted(out, key=lambda a: -len(a[3]))


def turned(sq, n, tol=FLUSH_TOL):
    """-> None or dict: the layout with arm 1 on the left wall and arm 2 on the bottom wall (x, y, degrees)."""
    m = math.isqrt(n - 1)
    s, A = normal(sq); f = s - m
    if not 0.3 < f < 1: return None
    arms = arms_at(A, s, m, tol)
    if len(arms) < 2: return None
    a1 = arms[0]
    a2 = next((a for a in arms[1:] if (a[0] in 'LR') != (a1[0] in 'LR')), None)
    if a2 is None: return None
    w1, w2 = a1[0], a2[0]
    X = A.copy()
    if w1 in 'BT':
        X[:, [0, 1]] = X[:, [1, 0]]; X[:, 2] = -X[:, 2]
        sw = {'B': 'L', 'T': 'R', 'L': 'B', 'R': 'T'}; w1, w2 = sw[w1], sw[w2]
    if w1 == 'R': X[:, 0] = s - X[:, 0]; X[:, 2] = -X[:, 2]
    if w2 == 'T': X[:, 1] = s - X[:, 1]; X[:, 2] = -X[:, 2]
    return dict(n=n, m=m, k=n - m * m, s=s, f=f, X=X, c1=a1[1], c2=a2[1])


def cut(sq, n, tol=None):
    """Cut a layout into its modules. -> (dict, None) or (None, reason). tol None: at FLUSH_TOL, and when that
    refuses the layout, at LOOSE_TOL (the reason given is the one at FLUSH_TOL)."""
    if tol is None:
        d, r = cut(sq, n, FLUSH_TOL)
        if d is not None: return d, r
        d2, _ = cut(sq, n, LOOSE_TOL)
        if d2 is not None: d2['tol'] = LOOSE_TOL
        return (d2, None) if d2 is not None else (None, r)
    d = turned(sq, n, tol)
    if d is None: return None, 'no two flush arms'
    X, s, f, m = d['X'], d['s'], d['f'], d['m']
    N = len(X)
    tilted = np.nonzero(np.abs(X[:, 2]) > 0.5)[0]
    T = X[tilted]
    chains, _ = stacks(T)
    chains = [[int(tilted[i]) for i in ch] for ch in chains]
    arm = {}
    for which, c in ((1, d['c1']), (2, d['c2'])):
        W = c - 1 + f
        got = []
        for ch in chains:
            if len(ch) != c: continue
            a = float(np.median(X[ch, 2])); t = math.radians(abs(a))
            err = c * math.cos(t) + math.sin(t) - W
            if abs(err) > tol: continue
            ax = X[ch[-1], :2] - X[ch[0], :2]; cen = X[ch, :2].mean(0)
            if which == 1 and abs(ax[0]) > abs(ax[1]) and abs(cen[0] - W / 2) < 0.05: got.append((cen[1], a, err))
            if which == 2 and abs(ax[1]) > abs(ax[0]) and abs(cen[1] - W / 2) < 0.05: got.append((cen[0], a, err))
        if len(got) < 3: return None, 'arm %d has %d flush stacks' % (which, len(got))
        got.sort()
        a = float(np.median([g[1] for g in got]))
        if any(abs(g[1] - a) > 0.2 for g in got): return None, 'arm %d leans both ways' % which
        arm[which] = dict(c=c, W=W, a=a, t=math.radians(abs(a)), pos=[g[0] for g in got], err=float(np.median([g[2] for g in got])))
    A1, A2 = arm[1], arm[2]
    c1, c2 = A1['c'], A2['c']
    W1, W2 = A1['W'], A2['W']
    p1, p2 = 1 / math.cos(A1['t']), 1 / math.cos(A2['t'])
    # slab coordinate: where the line through a centre, parallel to the stacks, crosses the middle line of the strip
    sig1 = X[:, 1] - (X[:, 0] - W1 / 2) * math.tan(math.radians(A1['a']))     # arm 1 stacks run along (cos a, sin a)
    sig2 = X[:, 0] + (X[:, 1] - W2 / 2) * math.tan(math.radians(A2['a']))     # arm 2 stacks run along (-sin a, cos a)
    y0 = A1['pos'][0] - p1 / 2; y1 = A1['pos'][-1] + p1 / 2
    x0 = A2['pos'][0] - p2 / 2; x1 = A2['pos'][-1] + p2 / 2
    zone = np.full(N, '', dtype=object)
    # the rest: one upright per cell of the far-corner grid; what is odd there belongs to the zone beside it
    ni, nj = m - c1 + 1, m - c2 + 1
    def owner(ci, cj):
        if ci <= 3 and cj <= 3: return 'C'
        if ci <= 3 and cj >= nj - 4: return 'F1'
        if cj <= 3 and ci >= ni - 4: return 'F2'
        return None
    # a cell of the rest beside a zone (three deep) whose square has slid off the grid goes to that zone: the rest is
    # not a wall there, its rows and columns slide into the room a zone leaves, and the zone is built on that
    tt1, tt2 = math.tan(A1['t']), math.tan(A2['t'])
    J1 = math.ceil(s - y1 + W1 / 2 * tt1 + 0.5); J2 = math.ceil(s - x1 + W2 / 2 * tt2 + 0.5)
    jm = math.ceil(y0 + W1 / 2 * tt1 + 0.5 - W2); im = math.ceil(x0 + W2 / 2 * tt2 + 0.5 - W1)
    def beside(ci, cj):
        if (ci < DEEP and cj < jm) or (cj < DEEP and ci < im): return 'C'
        if ci < DEEP and cj >= nj - J1: return 'F1'
        if cj < DEEP and ci >= ni - J2: return 'F2'
        return None
    cell = {}; given = {}
    for i in np.nonzero((X[:, 0] >= W1) & (X[:, 1] >= W2))[0]:
        ci = int(round(X[i, 0] - W1 - 0.5)); cj = int(round(X[i, 1] - W2 - 0.5))
        ex, ey = X[i, 0] - (W1 + .5 + ci), X[i, 1] - (W2 + .5 + cj)
        good = (abs(X[i, 2]) < 2.0 and abs(ex) < 0.3 and abs(ey) < 0.3 and 0 <= ci < ni and 0 <= cj < nj and (ci, cj) not in cell)
        off = max(abs(ex), abs(ey)) > SLID or abs(X[i, 2]) > 0.01
        o = (beside(ci, cj) if 0 <= ci < ni and 0 <= cj < nj else None) or owner(ci, cj)
        if good and not (off and beside(ci, cj)):
            cell[(ci, cj)] = i; zone[i] = 'R'
        else:
            if o is None: return None, 'rest broken at cell %d,%d' % (ci, cj)
            zone[i] = o
            if good:
                given[(ci, cj)] = o; X[i, 2] = 0.0     # it stands between cells that stay on the grid, so it is set upright
    miss = {'C': [], 'F1': [], 'F2': []}
    for ci in range(ni):
        for cj in range(nj):
            if (ci, cj) not in cell:
                o = given.get((ci, cj)) or beside(ci, cj) or owner(ci, cj)
                if o is None: return None, 'rest empty at cell %d,%d' % (ci, cj)
                miss[o].append((ci, cj))
    inA = (zone == '') & (X[:, 0] < W1)
    inB = (zone == '') & (X[:, 0] >= W1)
    zone[inA & (sig1 < y0)] = 'C'; zone[inA & (sig1 > y1)] = 'F1'; zone[inA & (zone == '')] = 'S1'
    zone[inB & (sig2 < x0)] = 'C'; zone[inB & (sig2 > x1)] = 'F2'; zone[inB & (zone == '')] = 'S2'
    s1 = (y1 - y0) / p1; s2 = (x1 - x0) / p2
    for nm, sv, c, z in (('1', s1, c1, 'S1'), ('2', s2, c2, 'S2')):
        if abs(sv - round(sv)) > 0.02: return None, 'run %s is %.3f pitches' % (nm, sv)
        if (zone == z).sum() != c * round(sv): return None, 'run %s holds %d squares in %d stacks of %d' % (nm, (zone == z).sum(), round(sv), c)
    # row 0 of the rest (the cells on the bottom strip) and column 0 (on the left strip): how far each cell stands
    # from its place on the grid, along the row or the column (negative: towards the corner)
    row0 = np.array([(X[cell[(i, 0)], 0] - (W1 + .5 + i), X[cell[(i, 0)], 1] - (W2 + .5)) if (i, 0) in cell else (0.0, 0.0) for i in range(ni)])
    col0 = np.array([(X[cell[(0, j)], 0] - (W1 + .5), X[cell[(0, j)], 1] - (W2 + .5 + j)) if (0, j) in cell else (0.0, 0.0) for j in range(nj)])
    d.update(arm=arm, zone=zone, y0=y0, y1=y1, x0=x0, x1=x1, s1=round(s1), s2=round(s2), p1=p1, p2=p2, W1=W1, W2=W2,
             sig1=sig1, sig2=sig2, miss=miss, chains=chains, ni=ni, nj=nj, row0=row0, col0=col0)
    return d, None


def slide_fields(d):
    """The slide of the rest beside the zones of a cut layout. -> {'F1': {...}, 'F2': {...}, 'C': {...}}

    A square of a zone can poke past the grid edge of its strip, into a gap of row 0 (or column 0) of the rest. The
    gap is there because every cell of the row between the corner and the poke stands the same distance g towards
    the corner, in room the corner leaves at the head of the row. So a far zone that pokes needs g of slide, and
    the corner of the same layout grants it. A far zone carries the found places of the cells beside it (slide, in
    its own frame, from the end wall) and its need g; a corner carries the found places at its end of the row and
    of the column (offr, offc: x and y of every cell, because a cell at the head of a row also dodges a square of the
    corner sideways) and what it grants (g2 for row 0 and arm 2, g1 for column 0 and arm 1).
    Where no square pokes, the cells are kept on the grid (all zero), as before."""
    X, zone, W1, W2, ni, nj = d['X'], d['zone'], d['W1'], d['W2'], d['ni'], d['nj']
    h = half(np.radians(X[:, 2]))
    tt1, tt2 = math.tan(d['arm'][1]['t']), math.tan(d['arm'][2]['t'])
    def pokes(z, arm):
        if arm == 2: q = (zone == z) & (X[:, 1] < W2) & (X[:, 0] > W1) & (X[:, 1] + h > W2 + POKE)
        else: q = (zone == z) & (X[:, 0] < W1) & (X[:, 1] > W2) & (X[:, 0] + h > W1 + POKE)
        return bool(q.any())
    out = {'C': {}, 'F1': {}, 'F2': {}}
    for arm, both, ax, lo, hi, fz, nn in (
            (2, d['row0'], 0, math.ceil(d['x0'] + W2 / 2 * tt2 + 0.5 - W1), math.floor(d['x1'] - W2 / 2 * tt2 - 1.5 - W1), 'F2', ni),
            (1, d['col0'], 1, math.ceil(d['y0'] + W1 / 2 * tt1 + 0.5 - W2), math.floor(d['y1'] - W1 / 2 * tt1 - 1.5 - W2), 'F1', nj)):
        lo = min(max(int(lo), 0), nn - 1); hi = min(max(int(hi), lo), nn - 1)
        prof = both[:, ax]                                   # the offsets along the row (the column)
        pc, pf = pokes('C', arm), pokes(fz, arm)
        if pc or pf:
            own = np.array(both[:lo + 2])
            own[min(2, max(lo - 1, 0)):, 1 - ax] = 0.0       # only the two cells at the head dodge sideways: the LP does not
            #   test a flush stack against a cell, so no cell beside a flush stack may stand inside the strip
            # the grant is the slide of the last cell the corner carries: every cell beyond it may stand that far
            out['C']['offr' if arm == 2 else 'offc'] = own; out['C']['g%d' % arm] = max(0.0, float(-own[-1, ax]))
        else:
            out['C']['offr' if arm == 2 else 'offc'] = None; out['C']['g%d' % arm] = 0.0
        if pf:
            A = d['arm'][arm]; lam = d['s'] - (d['x1'] if arm == 2 else d['y1'])
            keep = int(math.ceil(lam + A['c'] * math.sin(A['t']) + 2.5)) + 1         # the cells far_state holds, and one more
            sl = np.maximum(-np.array(prof)[::-1][:min(keep, nn - lo)], 0.0)
            out[fz] = dict(slide=sl, g=float(sl.max()), poke=True)      # the need: every cell beyond stands at least this far
        else:
            out[fz] = dict(slide=None, g=0.0, poke=False)
    return out


def modules_of(d, src, licence, tag):
    """The three modules of a cut layout, each in its own frame.

    far: xi = distance from the outer wall, eta = distance from the end wall; the cut is at eta = length on xi = W/2.
    corner: the turned frame itself. Angles in degrees; grp 1 or 2 marks the squares at the tilt of arm 1 or 2."""
    X, s, m, f, zone = d['X'], d['s'], d['m'], d['f'], d['zone']
    A1, A2 = d['arm'][1], d['arm'][2]
    c1, c2 = A1['c'], A2['c']
    out = []
    base = dict(n=d['n'], m=m, k=d['k'], f0=f, src=src, licence=licence, tag=tag)

    def rigid(idx, a, horizontal, tol=0.35):
        """chains at tilt a (to tol degrees) that run along the arm's stacks, as lists of positions in idx; + singles"""
        pos = {int(i): q for q, i in enumerate(idx)}
        groups = []; used = set()
        for ch in d['chains']:
            mem = [i for i in ch if i in pos]
            if len(mem) < 2 or float(np.abs(X[mem, 2] - a).max()) > tol: continue
            ax = X[mem[-1], :2] - X[mem[0], :2]
            if (abs(ax[0]) > abs(ax[1])) != horizontal: continue
            groups.append([pos[i] for i in mem]); used.update(mem)
        for i in idx:
            if int(i) not in used and abs(X[i, 2] - a) < min(tol, 0.05): groups.append([pos[int(i)]]); used.add(int(i))
        return groups

    for z, c, W, a_arm, a_loc, lam, sig, cut_at, p, horizontal in (
            ('F1', c1, d['W1'], A1['a'], -A1['a'], s - d['y1'], d['sig1'], d['y1'], d['p1'], True),
            ('F2', c2, d['W2'], A2['a'], A2['a'], s - d['x1'], d['sig2'], d['x1'], d['p2'], False)):
        idx = np.nonzero(zone == z)[0]
        if z == 'F1':
            loc = np.c_[X[idx, 0], s - X[idx, 1], -X[idx, 2]]; miss = [(ci, d['nj'] - 1 - cj) for ci, cj in d['miss'][z]]
        else:
            loc = np.c_[X[idx, 1], s - X[idx, 0], X[idx, 2]]; miss = [(cj, d['ni'] - 1 - ci) for ci, cj in d['miss'][z]]
        rig = rigid(idx, a_arm, horizontal)
        grp = np.zeros(len(idx), int)
        slab = collections.defaultdict(list)
        for g in rig:
            grp[g] = 1
            slab[int(round(float(np.mean(sig[idx[g]]) - cut_at) / p + 0.5))].append(len(g))
        taper = '.'.join('+'.join(map(str, sorted(slab[q], reverse=True))) if q in slab else '0' for q in range(1, max(slab) + 1)) if slab else '-'
        loose = int(((np.abs(loc[:, 2]) > 0.5) & (grp == 0)).sum()); up = int((np.abs(loc[:, 2]) <= 0.5).sum())
        cnt = len(idx) - len(miss)
        t = math.radians(abs(a_arm))
        sign = 'c%d:%s|l%d|u%d' % (c, taper, loose, up) + ('|x%d' % len(miss) if miss else '')
        out.append(dict(base, kind='far', arm=1 if z == 'F1' else 2, c=c, lean=1 if a_loc > 0 else -1, P=loc, grp=grp,
                        rig=rigid(idx, a_arm, horizontal, EXACT), miss=miss,
                        count=cnt, len0=lam, loss0=c * math.cos(t) * lam - cnt, tilt0=abs(a_arm), sig=sign,
                        id='%d%s.%s' % (d['n'], tag, z)))
    idx = np.nonzero(zone == 'C')[0]
    loc = X[idx].copy()
    r1 = rigid(idx, A1['a'], True); r2 = [g for g in rigid(idx, A2['a'], False) if not any(set(g) & set(h) for h in r1)]
    grp = np.zeros(len(idx), int)
    tap = []
    for rg, gi, sig, cut_at, p in ((r1, 1, d['sig1'], d['y0'], d['p1']), (r2, 2, d['sig2'], d['x0'], d['p2'])):
        slab = collections.defaultdict(list)
        for g in rg:
            grp[g] = gi
            slab[int(round(float(cut_at - np.mean(sig[idx[g]])) / p + 0.5))].append(len(g))
        ks = [q for q in slab if q >= 1]
        tap.append('.'.join('+'.join(map(str, sorted(slab[q], reverse=True))) if q in slab else '0' for q in range(1, max(ks) + 1)) if ks else '-')
    loose = int(((np.abs(loc[:, 2]) > 0.5) & (grp == 0)).sum()); up = int((np.abs(loc[:, 2]) <= 0.5).sum())
    miss = list(d['miss']['C'])
    cnt = len(idx) - len(miss)
    r1 = rigid(idx, A1['a'], True, EXACT); r2 = [g for g in rigid(idx, A2['a'], False, EXACT) if not any(set(g) & set(h) for h in r1)]
    for g in r1: grp[g] = 1          # only the squares at the exact tilt of an arm are turned with it
    for g in r2: grp[g] = 2
    t1, t2 = A1['t'], A2['t']
    sign = 'c%dx%d:%s/%s|l%d|u%d|%s%s' % (c1, c2, tap[0], tap[1], loose, up, '+' if A1['a'] > 0 else '-', '+' if A2['a'] > 0 else '-') + \
           ('|x%d' % len(miss) if miss else '')
    out.append(dict(base, kind='corner', c1=c1, c2=c2, lean1=1 if A1['a'] > 0 else -1, lean2=1 if A2['a'] > 0 else -1, P=loc, grp=grp,
                    rig=r1 + r2, miss=miss, count=cnt, y0=d['y0'], x0=d['x0'],
                    loss0=c1 * math.cos(t1) * d['y0'] + c2 * math.cos(t2) * (d['x0'] - d['W1']) - cnt,
                    tilt1=abs(A1['a']), tilt2=abs(A2['a']), sig=sign, id='%d%s.C' % (d['n'], tag)))
    return out


def slid(d, mods):
    """The slid twins of the modules of a cut layout: a copy (id + '~') of every module beside which the rest has
    slid, with the fields of slide_fields. The module itself stays as it is, with the rest on the grid beside it: it
    is longer, and it fits every corner. -> (twins, ids of the layout with the twins in place)"""
    sf = slide_fields(d); out = []; ids = []
    for q in mods:
        f = sf['C' if q['kind'] == 'corner' else 'F%d' % q['arm']]
        moved = (f.get('offr') is not None or f.get('offc') is not None) if q['kind'] == 'corner' else f['poke']
        if moved:
            v = dict(q); v.update(f); v['id'] = q['id'] + '~'; out.append(v)
        ids.append(q['id'] + '~' if moved else q['id'])
    return out, ids


# ----------------------------------------------------------------------------------------------- the contact LP

def contact_lp(P, mode, cost, caps, tr=0.25, reach=2.2, tr_a=0.0, elastic=False):
    """One contact LP. P: x, y, theta (radians). mode: 0 free, -1 fixed, 1 moves by (0, u1), 2 moves by (u2, 0).
    Walls at x = 0 and y = 0. Minimises cost . (u1, u2) with u <= caps.
    tr_a = 0: the angles are frozen and the LP is exact. tr_a > 0: the free squares may also turn by up to tr_a,
    with every gap linearised in the angles (both branches of |cos| + |sin| are written near a kink, as in
    methods_lp). elastic: every row may be broken by v >= 0 and v is minimised first.
    -> (new P, (u1, u2), v) or None."""
    N = len(P)
    free = np.nonzero(mode == 0)[0]; nf = len(free)
    vi = np.full(N, -1); vi[free] = np.arange(nf)
    rot = tr_a > 0
    na = nf if rot else 0
    iu = (2 * nf + na, 2 * nf + na + 1); iv = 2 * nf + na + 2; nv = iv + 1
    pairs = pair_list(P, reach)
    ma, mb = mode[pairs[:, 0]], mode[pairs[:, 1]]
    pairs = pairs[~(((ma != 0) & (mb != 0)) & ~((ma > 0) & (mb > 0) & (ma != mb)))]   # drop pairs that cannot move against each other
    g, A, B, PHI = best_axes(P, pairs)
    ux, uy = np.cos(PHI), np.sin(PHI)
    dx, dy = P[B, 0] - P[A, 0], P[B, 1] - P[A, 1]
    psi = P[B, 2] - PHI
    cp, sp = np.cos(psi), np.sin(psi)
    kt = 2.5 * tr_a
    rows, cols, vals, rhs = [], [], [], []
    nr = 0
    sc0 = np.where(cp >= 0, 1.0, -1.0); ss0 = np.where(sp >= 0, 1.0, -1.0)
    for fc, fs in ((1, 1), (-1, 1), (1, -1)):       # own signs; cos flipped; sin flipped (only where near zero)
        if fc < 0: sel = np.abs(cp) < kt
        elif fs < 0: sel = np.abs(sp) < kt
        else: sel = np.ones(len(g), bool)
        if (fc < 0 or fs < 0) and not rot: continue
        if not sel.any(): continue
        a, b = A[sel], B[sel]
        c_, s_ = sc0[sel] * fc, ss0[sel] * fs
        g0 = ux[sel] * dx[sel] + uy[sel] * dy[sel] - 0.5 - 0.5 * (c_ * cp[sel] + s_ * sp[sel])
        r = nr + np.arange(len(a))
        for body, sgn in ((b, -1.0), (a, 1.0)):     # rows are -(u.(dB - dA) + ...) <= g0 - GAP
            md = mode[body]
            q = md == 0
            rows += [r[q], r[q]]; cols += [2 * vi[body[q]], 2 * vi[body[q]] + 1]; vals += [sgn * ux[sel][q], sgn * uy[sel][q]]
            q = md == 1
            rows.append(r[q]); cols.append(np.full(q.sum(), iu[0])); vals.append(sgn * uy[sel][q])
            q = md == 2
            rows.append(r[q]); cols.append(np.full(q.sum(), iu[1])); vals.append(sgn * ux[sel][q])
        if rot:
            dh = 0.5 * (-c_ * sp[sel] + s_ * cp[sel])
            perp = -uy[sel] * dx[sel] + ux[sel] * dy[sel]
            q = mode[a] == 0
            rows.append(r[q]); cols.append(2 * nf + vi[a[q]]); vals.append(-(perp + dh)[q])
            q = mode[b] == 0
            rows.append(r[q]); cols.append(2 * nf + vi[b[q]]); vals.append(dh[q])
        if elastic:
            rows.append(r); cols.append(np.full(len(r), iv)); vals.append(-np.ones(len(r)))
        rhs.append(g0 - GAP); nr += len(a)
    th = P[free, 2]
    c, s = np.cos(th), np.sin(th)
    sc0 = np.where(c >= 0, 1.0, -1.0); ss0 = np.where(s >= 0, 1.0, -1.0)
    for fc, fs in ((1, 1), (-1, 1), (1, -1)):
        if fc < 0: sel = np.abs(c) < kt
        elif fs < 0: sel = np.abs(s) < kt
        else: sel = np.ones(nf, bool)
        if (fc < 0 or fs < 0) and not rot: continue
        if not sel.any(): continue
        k = np.nonzero(sel)[0]
        c_, s_ = sc0[k] * fc, ss0[k] * fs
        h0 = 0.5 * (c_ * c[k] + s_ * s[k]); dh = 0.5 * (-c_ * s[k] + s_ * c[k])
        for ax in (0, 1):                           # x + dx - h(theta + dth) >= GAP, the same for y
            r = nr + np.arange(len(k))
            rows.append(r); cols.append(2 * k + ax); vals.append(-np.ones(len(k)))
            if rot: rows.append(r); cols.append(2 * nf + k); vals.append(dh)
            if elastic: rows.append(r); cols.append(np.full(len(k), iv)); vals.append(-np.ones(len(k)))
            rhs.append(P[free[k], ax] - h0 - GAP); nr += len(k)
    h = half(P[:, 2])
    for gi, ax in ((1, 1), (2, 0)):                 # a moving stack stays off the wall it moves towards
        q = np.nonzero(mode == gi)[0]
        rows.append(nr + np.arange(len(q))); cols.append(np.full(len(q), iu[gi - 1])); vals.append(-np.ones(len(q)))
        rhs.append(P[q, ax] - h[q] - GAP); nr += len(q)
    Aub = coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(nr, nv)).tocsr()
    cst = np.zeros(nv); cst[iu[0]], cst[iu[1]] = cost
    if elastic: cst[iv] = 1e4
    bounds = [(-tr, tr)] * (2 * nf) + [(-tr_a, tr_a)] * na
    for gi in (1, 2):
        if (mode == gi).any(): bounds.append((-tr, min(tr, caps[gi - 1]) if caps[gi - 1] is not None else tr))
        else: bounds.append((0, 0))
    bounds.append((0, None) if elastic else (0, 0))
    res = linprog(cst, A_ub=Aub, b_ub=np.concatenate(rhs), bounds=bounds, method='highs',
                  options={'primal_feasibility_tolerance': 1e-10, 'dual_feasibility_tolerance': 1e-10})
    if res.status != 0: return None
    Q = P.copy()
    k = np.arange(nf)
    Q[free, 0] += res.x[2 * k]; Q[free, 1] += res.x[2 * k + 1]
    if rot: Q[free, 2] += res.x[2 * nf + k]
    u = (float(res.x[iu[0]]), float(res.x[iu[1]]))
    Q[mode == 1, 1] += u[0]; Q[mode == 2, 0] += u[1]
    return Q, u, float(res.x[iv])


def settle(P, mode, cost, caps=(None, None), iters=10):
    """Repeat the fixed-angle LP (the axes are picked again each time) until the cost stops falling.
    -> (P, (u1, u2)) or None."""
    tot = [0.0, 0.0]
    for it in range(iters):
        cp = tuple(None if c is None else c - t for c, t in zip(caps, tot))
        out = contact_lp(P, mode, cost, cp)
        if out is None and it == 0: out = contact_lp(P, mode, cost, cp, tr=0.6, reach=3.2)
        if out is None: return None
        P, u, _ = out
        tot[0] += u[0]; tot[1] += u[1]
        if it and abs(cost[0] * u[0] + cost[1] * u[1]) < 1e-10: break
    return P, tuple(tot)


def relax(P, mode, cost, caps=(None, None), tr_a=4e-3, iters=40, heal=25):
    """settle, then let the free squares turn (a sequential LP with a fixed-angle LP after every step).
    When the fixed-angle LP has no solution at the start, turn the squares first to make room (heal).
    -> (P, (u1, u2)) or None."""
    out = settle(P, mode, cost, caps)
    k = 0; v0 = None
    while out is None and k < heal:
        k += 1
        r = contact_lp(P, mode, (0.0, 0.0), (0.0, 0.0), tr=0.02, tr_a=tr_a, elastic=True)   # the moving stacks may only back off
        if r is None or (v0 is not None and r[2] > 0.98 * v0 and r[2] > 1e-7): return None
        P, v0 = r[0], r[2]
        if v0 < 1e-7: out = settle(P, mode, cost, caps)
    if out is None: return None
    P, tot = out; tot = list(tot)
    for it in range(iters):
        cp = tuple(None if c is None else c - t for c, t in zip(caps, tot))
        r = contact_lp(P, mode, cost, cp, tr_a=tr_a)
        o = None
        if r is not None:
            cq = tuple(None if c is None else c - r[1][i] for i, c in enumerate(cp))
            o = settle(r[0], mode, cost, cq)
        if o is not None and legal(o[0], mode):
            u = (r[1][0] + o[1][0], r[1][1] + o[1][1]); gain = -(cost[0] * u[0] + cost[1] * u[1])
        else:
            gain = -1.0
        if gain > 1e-9:
            P = o[0]; tot[0] += u[0]; tot[1] += u[1]
            tr_a = min(tr_a * 1.5, 8e-3)
            if gain < 1e-7: break
        else:
            tr_a /= 4
            if tr_a < 2e-6: break
    return P, tuple(tot)


def legal(P, mode=None, tol=-2e-9):
    pairs = pair_list(P, math.sqrt(2) + 1e-3)
    if mode is not None:
        ma, mb = mode[pairs[:, 0]], mode[pairs[:, 1]]
        pairs = pairs[~(((ma != 0) & (mb != 0)) & ~((ma > 0) & (mb > 0) & (ma != mb)))]
    if not len(pairs): return True
    return float(best_axes(P, pairs)[0].min()) >= tol


def retilt(P, rig, new):
    """Turn every rigid group about its own centre to the angle new[group] (degrees). P in degrees."""
    Q = P.copy()
    for g, a in zip(rig, new):
        da = math.radians(a - float(np.median(P[g, 2])))
        cen = P[g, :2].mean(0); v = P[g, :2] - cen
        co, si = math.cos(da), math.sin(da)
        Q[g, 0] = cen[0] + co * v[:, 0] - si * v[:, 1]; Q[g, 1] = cen[1] + si * v[:, 0] + co * v[:, 1]; Q[g, 2] = a
    return Q


def stack_squares(c, a_deg, cx, cy, along_x=True):
    """c squares set face to face at tilt a; they run along (cos a, sin a) or, for arm 2, along (-sin a, cos a)."""
    a = math.radians(a_deg)
    u = (math.cos(a), math.sin(a)) if along_x else (-math.sin(a), math.cos(a))
    j = np.arange(c) - (c - 1) / 2
    return np.c_[cx + j * u[0], cy + j * u[1], np.full(c, a_deg)]


def far_state(mod, f, Pm, lam):
    """bodies of a far module at f: its squares (free), the last flush stack (moves along eta), cells of the rest (fixed)"""
    c = mod['c']; W = c - 1 + f; t = flush_tilt(c, f); p = 1 / math.cos(t)
    st = stack_squares(c, mod['lean'] * math.degrees(t), W / 2, lam + p / 2)
    J = int(math.ceil(lam + c * math.sin(t) + 2.5))
    sl = mod.get('slide') if SLIDE else None; g = mod.get('g', 0.0) if SLIDE else 0.0
    off = (lambda j: float(sl[j]) if j < len(sl) else g) if sl is not None else (lambda j: 0.0)
    cells = np.array([(W + .5 + i, .5 + j + (off(j) if i == 0 else 0.0), 0.0) for i in range(max(DEEP + 1, 2)) for j in range(J)
                      if (i, j) not in set(mod['miss'])])
    P = np.vstack([Pm, st, cells]); P[:, 2] = np.radians(P[:, 2])
    mode = np.r_[np.zeros(len(Pm), int), np.ones(c, int), -np.ones(len(cells), int)]
    return P, mode


def far_len(mod, f, Pm, lam, turn=True):
    """Shortest length of a far module at f, from the state (Pm, lam). turn: its squares may turn. -> (len, Pm) or None"""
    c = mod['c']
    ang = mod['lean'] * math.degrees(flush_tilt(c, f))
    Pm = retilt(Pm, mod['rig'], [ang] * len(mod['rig']))
    P, mode = far_state(mod, f, Pm, lam)
    out = relax(P, mode, (1.0, 0.0)) if turn else settle(P, mode, (1.0, 0.0))
    if out is None or not legal(out[0], mode): return None
    Q = out[0][:len(Pm)].copy(); Q[:, 2] = np.degrees(Q[:, 2])
    return lam + out[1][0], Q


def corner_slide(mod):
    """-> f(i, j): the offset (dx, dy) of cell (i, j) of the rest beside a corner: as found at the corner's end of
    row 0 and of column 0, then the grant all along the row (the column), and zero for every other cell.
    The head cell (0, 0) is the head of the row and of the column: it takes its found place, and the grant of an arm
    whose cells were not found slid (a variant of `grant`) moves it too, so it never stands behind its run."""
    if not SLIDE: return lambda i, j: (0.0, 0.0)
    r, c, g2, g1 = mod.get('offr'), mod.get('offc'), mod.get('g2', 0.0), mod.get('g1', 0.0)
    def f(i, j):
        if i == 0 and j == 0:
            if r is not None and c is not None: return (float(r[0][0]), float(r[0][1]))
            if r is not None: x, y = float(r[0][0]), float(r[0][1])
            elif c is not None: x, y = float(c[0][0]), float(c[0][1])
            else: x, y = 0.0, 0.0
            if r is None and g2 > 0: x = min(x, -g2)
            if c is None and g1 > 0: y = min(y, -g1)
            return (x, y)
        if j == 0:
            if r is None: return (-g2, 0.0)
            return (float(r[i][0]), float(r[i][1])) if i < len(r) else (-g2, 0.0)
        if i == 0:
            if c is None: return (0.0, -g1)
            return (float(c[j][0]), float(c[j][1])) if j < len(c) else (0.0, -g1)
        return (0.0, 0.0)
    return f


def cells_collide(mod, tol=1e-9):
    """True when cells (1, 0) and (0, 1) of the rest beside a corner overlap: a run granted towards the corner beside a
    run that was found slid towards the corner (or granted too). No head cell makes such a corner legal, and the LP of
    the corner does not see it (it does not test two fixed bodies)."""
    miss = set(map(tuple, mod['miss']))
    if (1, 0) in miss or (0, 1) in miss: return False
    cs = corner_slide(mod); a, b = cs(1, 0), cs(0, 1)
    return 1 + a[0] - b[0] < 1 - tol and 1 + b[1] - a[1] < 1 - tol


def corner_state(mod, f, Pm, y0, x0):
    c1, c2 = mod['c1'], mod['c2']
    W1, W2 = c1 - 1 + f, c2 - 1 + f
    t1, t2 = flush_tilt(c1, f), flush_tilt(c2, f)
    s1 = stack_squares(c1, mod['lean1'] * math.degrees(t1), W1 / 2, y0 + 0.5 / math.cos(t1))
    s2 = stack_squares(c2, mod['lean2'] * math.degrees(t2), x0 + 0.5 / math.cos(t2), W2 / 2, along_x=False)
    # the rest along both strips up to the first flush stacks (a corner may run far along an arm)
    im = int(math.ceil(x0 - W1 + c2 * math.sin(t2) + 2.5)); jm = int(math.ceil(y0 - W2 + c1 * math.sin(t1) + 2.5))
    gone = set(map(tuple, mod['miss']))
    deep = max(DEEP, 2)
    cs = corner_slide(mod)
    cells = np.array([(W1 + .5 + i + cs(i, j)[0], W2 + .5 + j + cs(i, j)[1], 0.0)
                      for i in range(max(im, deep + 1)) for j in range(max(jm, deep + 1))
                      if (i <= deep or j <= deep) and (i, j) not in gone])
    P = np.vstack([Pm, s1, s2, cells]); P[:, 2] = np.radians(P[:, 2])
    mode = np.r_[np.zeros(len(Pm), int), np.ones(c1, int), 2 * np.ones(c2, int), -np.ones(len(cells), int)]
    return P, mode


def corner_len(mod, f, Pm, y0, x0, cost=(1.0, 1.0), caps=(None, None)):
    """Smallest cost . (y0, x0) of a corner at f, from the state (Pm, y0, x0). -> (y0, x0, Pm) or None"""
    new = [mod['lean1'] * math.degrees(flush_tilt(mod['c1'], f)) if mod['grp'][g[0]] == 1 else
           mod['lean2'] * math.degrees(flush_tilt(mod['c2'], f)) for g in mod['rig']]
    Pm = retilt(Pm, mod['rig'], new)
    P, mode = corner_state(mod, f, Pm, y0, x0)
    # a turned twin (mod['turn'], round 19): the squares of the corner may also turn at every step, as in a far zone.
    # On 2026-11-12 the frozen-angle table of 813mi17.C was 0.05 longer on both lengths, at the f of its 754 build,
    # than the corner that the fq squeeze left there.
    out = relax(P, mode, cost, caps) if mod.get('turn') else settle(P, mode, cost, caps)
    if out is None or not legal(out[0], mode): return None
    Q = out[0][:len(Pm)].copy(); Q[:, 2] = np.degrees(Q[:, 2])
    return y0 + out[1][0], x0 + out[1][1], Q


def tabulate(mod):
    """Lengths of one module against f, by continuation from the state it was found in, within SPAN of its own f.
    far: knots (f, length) from its lock (the smallest f it exists at, found by bisection) upwards.
    corner: (y0, x0) on GRID for the five costs of COST."""
    f0 = mod['f0']
    gi = [i for i, f in enumerate(GRID) if abs(f - f0) <= (SPAN if mod['kind'] == 'far' else CSPAN) + 1e-9]
    up = [i for i in gi if GRID[i] >= f0]; dn = [i for i in gi if GRID[i] < f0][::-1]
    if mod['kind'] == 'far' and mod.get('walk'):
        return tabulate_dense(mod)
    if mod['kind'] == 'far':
        at = far_len(mod, f0, mod['P'], mod['len0'] + 1e-6)
        if at is None: return dict(id=mod['id'], own=None, knots=None)
        knots = {f0: at[0]}
        lam, Pm = at
        for i in up:
            r = far_len(mod, float(GRID[i]), Pm, lam + 0.02)
            if r is None: break
            lam, Pm = r; knots[float(GRID[i])] = lam
        lam, Pm = at; ok = f0
        for i in dn:
            r = far_len(mod, float(GRID[i]), Pm, lam + 0.02)
            if r is None:
                lo = float(GRID[i])                  # the lock lies between lo and ok
                for _ in range(6):
                    mid = (lo + ok) / 2
                    r = far_len(mod, mid, Pm, lam + 0.02)
                    if r is None: lo = mid
                    else: lam, Pm = r; ok = mid; knots[mid] = lam
                break
            lam, Pm = r; ok = float(GRID[i]); knots[ok] = lam
        fs = np.array(sorted(knots))
        return dict(id=mod['id'], own=at[0], knots=(fs, np.array([knots[f] for f in fs])), lock=float(fs[0]))
    tab = np.full((len(COST), 2, len(GRID)), np.nan)
    own = []
    for q, cost in enumerate(COST):
        at = corner_len(mod, f0, mod['P'], mod['y0'] + 1e-6, mod['x0'] + 1e-6, cost)
        own.append(None if at is None else at[:2])
        if at is None: continue
        for seq in (up, dn):
            y0, x0, Pm = at
            for i in seq:
                r = corner_len(mod, float(GRID[i]), Pm, y0 + 0.02, x0 + 0.02, cost)
                if r is None: break
                y0, x0, Pm = r; tab[q, 0, i] = y0; tab[q, 1, i] = x0
    return dict(id=mod['id'], own=own, tab=tab)


def tabulate_dense(mod):
    """A far zone walked by steps of mod['walk'] from the f it was found at, up and down mod['walk_span'], with a knot
    at every step (path walks the build the same way). On 2026-11-12 the walk by 0.0005 found a state shorter than the
    GRID table by more than 1e-3 within 0.01 of f0 in 73 of 144 far zones, and a longer one (the table has no state
    there) by more than 1e-3 in 12: the length of a far zone is not straight between two knots 0.005 apart."""
    f0, w = mod['f0'], mod['walk']; span = mod.get('walk_span', 0.03)
    at = far_len(mod, f0, mod['P'], mod['len0'] + 1e-6)
    if at is None: return dict(id=mod['id'], own=None, knots=None)
    knots = {f0: at[0]}
    for sgn in (1, -1):
        lam, Pm = at
        for i in range(1, int(round(span / w)) + 1):
            f = f0 + sgn * w * i
            if not GRID[0] - 1e-9 <= f <= GRID[-1] + 1e-9: break
            r = far_len(mod, f, Pm, lam + 0.02)
            if r is None: break
            lam, Pm = r; knots[f] = lam
    fs = np.array(sorted(knots))
    return dict(id=mod['id'], own=at[0], knots=(fs, np.array([knots[f] for f in fs])), lock=float(fs[0]))


# ----------------------------------------------------------------------------------------------- the generator

FF = np.round(np.arange(0.600, 0.99901, 0.0002), 4)     # the f values a choice of modules is tested at
_PIT = {}


def pit(c):
    if c not in _PIT: _PIT[c] = np.array([pitch(c, f) for f in FF])
    return _PIT[c]


def _on_ff(fs, vs):
    a = np.interp(FF, fs, vs)
    a[(FF < fs[0] - 1e-9) | (FF > fs[-1] + 1e-9)] = np.nan
    return a


class Library:
    """The modules with their lengths on FF. A far module holds L[f]; a corner holds the 5 states (Y, X)[f] of its
    trade between the two lengths (from 'y0 first' through 'smallest sum' to 'x0 first'); with --chord on the command
    line, 13 points (2 more on each chord, see CHORD)."""

    def __init__(self, work, only=None):
        global CHORD
        if '--chord' in sys.argv: CHORD = True
        lib = pickle.load(open(work + '/library.pkl', 'rb')); lens = pickle.load(open(work + '/lens.pkl', 'rb'))
        self.mods = {q['id']: q for q in lib['mods']}; self.layouts = lib['layouts']; self.lens = lens
        self.far = collections.defaultdict(list); self.corners = []; self.byid = {}
        for q in lib['mods']:
            t = lens.get(q['id'])
            if t is None or (only and not only(q)): continue
            if q['kind'] == 'far':
                if t.get('knots') is None: continue
                fs, ls = t['knots']
                e = dict(id=q['id'], count=q['count'], lean=q['lean'], sym=not q['miss'] and not q.get('poke'), L=_on_ff(fs, ls),
                         lock=t['lock'], g=q.get('g', 0.0) if SLIDE else 0.0, q=q, kin=kin(q))
                self.far[q['c']].append(e); self.byid[q['id']] = e
            else:
                tab = t['tab']; pts = []
                for qi in range(len(COST)):
                    ok = ~np.isnan(tab[qi, 0])
                    pts.append([_on_ff(GRID[ok], tab[qi, ax][ok]) for ax in (0, 1)] if ok.sum() >= 2 else None)
                mid = pts[len(COST) // 2]
                if mid is None: continue
                V = [[np.where(np.isnan(p[ax]), mid[ax], p[ax]) for ax in (0, 1)] if p is not None else mid for p in pts]
                ws = (0, 1 / 3, 2 / 3) if CHORD else (0,)
                Y = np.array([V[k][0] + (V[k + 1][0] - V[k][0]) * w for k in range(len(V) - 1) for w in ws] + [V[-1][0]])
                X = np.array([V[k][1] + (V[k + 1][1] - V[k][1]) * w for k in range(len(V) - 1) for w in ws] + [V[-1][1]])
                e = dict(id=q['id'], c1=q['c1'], c2=q['c2'], count=q['count'], lean1=q['lean1'], lean2=q['lean2'], Y=Y, X=X, q=q,
                         g1=q.get('g1', 0.0) if SLIDE else 0.0, g2=q.get('g2', 0.0) if SLIDE else 0.0, kin=kin(q))
                self.corners.append(e); self.byid[q['id']] = e
        self._opts = {}; self._farv = {}; self._oarr = {}; self.w = slice(0, len(FF))

    def fit(self, C, F1, F2, m, s1, s2):
        """Smallest f at which both arms fit. -> (f, what stops it) or None. 'fit': an arm is full; 'edge': a module
        does not exist below this f (a far zone's lock, or the end of a table)."""
        w = self.w; ff = FF[w]
        with np.errstate(invalid='ignore'):
            a1 = m + ff - s1 * pit(C['c1'])[w] - F1['L'][w]  # what arm 1 leaves for the corner
            a2 = m + ff - s2 * pit(C['c2'])[w] - F2['L'][w]
            g = np.minimum(a1 - C['Y'][:, w], a2 - C['X'][:, w])
            g = np.where(np.isnan(g), -np.inf, g).max(axis=0)
        ok = np.nonzero(g >= 0)[0]
        if not len(ok): return None
        i = int(ok[0])
        if i == 0 or not np.isfinite(g[i - 1]): return float(ff[i]), 'edge'
        return float(ff[i - 1] + (ff[i] - ff[i - 1]) * (-g[i - 1]) / (g[i] - g[i - 1])), 'fit'

    def fit_many(self, C, cand, m):
        """fit for many choices of one corner at once: cand = [(lb, F1, s1, F2, s2)]. -> [(f, stop) or None]"""
        w = self.w; ff = FF[w]; nw = len(ff)
        Y, X = C['Y'][:, w], C['X'][:, w]
        out = []
        step = max(8, int(3e6 // (Y.shape[0] * max(nw, 1))))
        for k0 in range(0, len(cand), step):
            ch = cand[k0:k0 + step]
            S1 = np.array([t[2] for t in ch], float)[:, None]; S2 = np.array([t[4] for t in ch], float)[:, None]
            L1 = np.array([t[1]['L'][w] for t in ch]); L2 = np.array([t[3]['L'][w] for t in ch])
            with np.errstate(invalid='ignore'):
                a1 = m + ff - S1 * pit(C['c1'])[w] - L1
                a2 = m + ff - S2 * pit(C['c2'])[w] - L2
                g = np.minimum(a1[:, None, :] - Y[None], a2[:, None, :] - X[None])
                g = np.where(np.isnan(g), -np.inf, g).max(axis=1)
            ok = g >= 0
            has = ok.any(axis=1); first = ok.argmax(axis=1)
            for k in range(len(ch)):
                if not has[k]: out.append(None); continue
                i = int(first[k])
                if i == 0 or not np.isfinite(g[k, i - 1]): out.append((float(ff[i]), 'edge')); continue
                out.append((float(ff[i - 1] + (ff[i] - ff[i - 1]) * (-g[k, i - 1]) / (g[k, i] - g[k, i - 1])), 'fit'))
        return out

    def window(self, lo=None, hi=None):
        """Search only f in [lo, hi] from now on (no arguments: all of FF). A module with no length there drops out
        at once. With fit_many, this makes a queue over every n affordable."""
        w = slice(0, len(FF)) if lo is None else slice(max(0, int(np.searchsorted(FF, lo))), min(len(FF), int(np.searchsorted(FF, hi)) + 2))
        if (w.start, w.stop) != (self.w.start, self.w.stop): self.w = w; self._opts = {}; self._farv = {}; self._oarr = {}

    def options(self, C, arm, m):
        """[(far module, stacks, lower bound of f, squares)] for one arm of corner C in shell m"""
        key = (C['id'], arm, m)
        if key in self._opts: return self._opts[key]
        Fs, fi, s, lb, cnt = self.opt_arrays(C, arm, m)
        out = [(Fs[a], int(b), float(c), int(d)) for a, b, c, d in zip(fi, s, lb, cnt)]
        self._opts[key] = out
        return out

    def opt_arrays(self, C, arm, m):
        """options as arrays: (far modules of the class, index into them, stacks, lower bound of f, squares), in the
        order of options. Round 16: all far zones of the class at once, the same options in the same order as the loop
        over F of rounds 1 to 15. The first f at which s stacks fit is the first index where the running maximum of
        smax reaches s."""
        key = (C['id'], arm, m)
        if key in self._oarr: return self._oarr[key]
        c = C['c1'] if arm == 1 else C['c2']; need = -C['lean1'] if arm == 1 else C['lean2']
        w = self.w; ff = FF[w]; cl = C['Y' if arm == 1 else 'X'][:, w]
        V = self._farv.get((c, w.start, w.stop))
        if V is None:
            Fs = self.far[c]
            V = self._farv[(c, w.start, w.stop)] = (Fs, np.array([F['L'][w] for F in Fs]).reshape(len(Fs), len(ff)),
                                                    np.array([F['lean'] for F in Fs]), np.array([F['sym'] for F in Fs], bool),
                                                    np.array([F['g'] for F in Fs], float), np.array([F['count'] for F in Fs], int))
        Fs, Lw, lean, sym, gg, count = V
        e = np.zeros(0, int); out = (Fs, e, e, np.zeros(0), e)
        ga = int(C['id'].split('^')[1][0]) if '^' in C['id'] else 0     # the arm a grant variant (see grant) was given its grant on
        if not np.isfinite(cl).any() or not len(Fs):
            self._oarr[key] = out; return out
        with np.errstate(invalid='ignore', all='ignore'):
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore'); short = np.nanmin(cl, axis=0)
        sel = (sym | (lean == need)) & (gg <= C['g%d' % arm] + 2e-3)     # a zone that pokes into a gap this corner does not grant is out
        if ga == arm: sel &= gg > 2e-3                                    # a grant costs length, so only beside a zone that pokes
        rows = np.nonzero(sel)[0]
        if len(rows):
            with np.errstate(invalid='ignore'):
                smax = np.floor((m + ff - Lw[rows] - short) / pit(c)[w])
            ok = np.isfinite(smax); has = ok.any(axis=1)
            rows, smax, ok = rows[has], smax[has], ok[has]
        if not len(rows):
            self._oarr[key] = out; return out
        lo = np.where(ok, smax, np.inf).min(axis=1); hi = np.where(ok, smax, -np.inf).max(axis=1)
        s0 = np.maximum(1, lo - 1); K = int((hi - s0).max()) + 1
        if K <= 0:
            self._oarr[key] = out; return out
        S = s0[:, None] + np.arange(K)[None, :]
        r, i = np.nonzero(S <= hi[:, None])
        st = S[r, i]
        # each row of the running maximum is sorted, so one searchsorted over all rows, each lifted by its own offset
        cm = np.maximum.accumulate(np.where(ok, np.clip(smax, -1e6, 1e6), -2e6), axis=1)
        nw = cm.shape[1]; off = np.arange(len(rows), dtype=float)[:, None] * 1e7
        first = np.searchsorted((cm + off).ravel(), st + off[r, 0], 'left') - r * nw
        st = st.astype(int)
        out = (Fs, rows[r], st, ff[first], count[rows[r]] + st * c)
        self._oarr[key] = out
        return out

    def best(self, n, top=3, below=None, need=None, distinct=False, foreign=False, depth=None, above=None, accept=None):
        """The choices of modules with the smallest f for n. -> [(f, stop, corner, far 1, far 2, s1, s2)]
        need: a set of module ids; only choices that hold one of them count (the others were tried before).
        distinct: two choices that differ only by a module of the same family count once (the lower f).
        foreign: only corners cut from a layout of another n (a design this n does not hold yet).
        depth: with below, search only f in [below - depth, below] (see window); a choice that fits at the low end
        of that window comes back with the stop 'edge'. above: reject a choice whose first fit is below this f,
        before it can occupy a top slot. The default leaves every choice eligible."""
        m = math.isqrt(n - 1); res = []
        if depth is not None and below is not None: self.window(below - depth, below)
        else: self.window()
        def key(t):
            return (t[2]['kin'], t[3]['kin'], t[4]['kin'], t[5], t[6]) if distinct else id(t)
        needc = None if need is None else {e['q']['c'] for c in self.far for e in self.far[c] if e['id'] in need}
        nmask = {}
        for C in self.corners:
            if m - C['c1'] + 1 < 5 or m - C['c2'] + 1 < 5: continue
            if foreign and C['q']['n'] == n: continue
            Q = n - (m - C['c1'] + 1) * (m - C['c2'] + 1) - C['count']
            cnew = need is None or C['id'] in need
            if not cnew and C['c1'] not in needc and C['c2'] not in needc: continue   # no far zone of the list fits either arm
            # the pairs of options of the two arms that hold Q squares, as a join on the count (round 16); the same
            # candidates in the same order as the loop over arm 1 then arm 2 of rounds 1 to 15, sorted stably by f
            Fa, i1, sa, la, na = self.opt_arrays(C, 1, m); Fb, i2, sb, lb2, nb2 = self.opt_arrays(C, 2, m)
            if not len(na) or not len(nb2): continue
            o2 = np.argsort(nb2, kind='stable'); srt = nb2[o2]
            tg = Q - na; a0 = np.searchsorted(srt, tg, 'left'); a1 = np.searchsorted(srt, tg, 'right')
            cntp = a1 - a0
            if not cntp.sum(): continue
            P1 = np.repeat(np.arange(len(na)), cntp)
            P2 = o2[np.repeat(a0 - np.cumsum(cntp) + cntp, cntp) + np.arange(cntp.sum())]
            if not cnew:
                for cc in (C['c1'], C['c2']):
                    if cc not in nmask: nmask[cc] = np.array([F['id'] in need for F in self.far[cc]], bool)
                keep = nmask[C['c1']][i1[P1]] | nmask[C['c2']][i2[P2]]
                P1, P2 = P1[keep], P2[keep]
            lbp = np.maximum(la[P1], lb2[P2])
            if below is not None:
                keep = lbp < below; P1, P2, lbp = P1[keep], P2[keep], lbp[keep]
            od = np.lexsort((P2, P1, lbp)); P1, P2, lbp = P1[od], P2[od], lbp[od]
            cand = [(float(l), Fa[i1[p]], int(sa[p]), Fb[i2[q]], int(sb[q])) for l, p, q in zip(lbp, P1, P2)]
            k0 = 0
            while k0 < len(cand):                           # in blocks, so the bound of the best found so far still prunes
                if len(res) >= top: cand = [t for t in cand[k0:] if t[0] < res[top - 1][0]]; k0 = 0
                blk = cand[k0:k0 + 256]; k0 += 256
                if not blk: break
                for (lb, F1, s1, F2, s2), r in zip(blk, self.fit_many(C, blk, m)):
                    if r is not None and (above is None or r[0] >= above) and (accept is None or accept(C, r[0])):
                        res.append((r[0], r[1], C, F1, F2, s1, s2))
                res.sort(key=lambda t: t[0])
                seen = set(); keep = []
                for t in res:
                    if key(t) not in seen: seen.add(key(t)); keep.append(t)
                res = keep[:max(top, 1)]
        return res[:top]


def kin(q):
    """The family of a module: what tells two modules apart for the choice of a build."""
    if q['kind'] == 'far': return ('far', q['c'], q['count'], q['sig'].split('|u')[1].split('|')[0], len(q['miss']))
    return ('corner', q['c1'], q['c2'], q['count'], q['sig'])


def usable(q):
    """A module the generator may use: from a held layout, from a layout of our own takes, or with an accepted licence."""
    return q['tag'] == 'h' or q.get('ours') or any(k in q['licence'] for k in OK_LICENCE)


def path(f0, f, walk=None):
    """The values of f a module is walked through from f0 to f: the knots of GRID in between, as `tabulate` walks them,
    then f. The state of a module depends on the steps it took, so the build has to take the steps of the table.
    walk: a far zone tabulated by steps of this size from f0 (see dense) is walked by the same steps."""
    if walk:
        k = int(math.floor(abs(f - f0) / walk + 1e-9))
        ks = [f0 + math.copysign(walk * i, f - f0) for i in range(1, k + 1)]
    else:
        ks = [float(g) for g in GRID if f0 <= g <= f] if f >= f0 else [float(g) for g in GRID[::-1] if f <= g < f0]
    return ks + ([float(f)] if not ks or abs(ks[-1] - f) > 1e-12 else [])


def far_at(mod, f):
    """State of a far module at f, by continuation from the f it was found at. -> (length, squares) or None"""
    at = far_len(mod, mod['f0'], mod['P'], mod['len0'] + 1e-6)
    if at is None: return None
    for g in path(mod['f0'], f, mod.get('walk')):
        at = far_len(mod, float(g), at[1], at[0] + 0.02)
        if at is None: return None
    return at


def corner_at(mod, f, cap_y, cap_x):
    """State of a corner at f with y0 <= cap_y and x0 <= cap_x. -> (y0, x0, squares) or None

    The corner trades one length for the other, and the set of its states is not convex, so one LP from the state of
    the smallest sum does not always reach a state under both caps. Here the corner first goes to f with one length
    as small as it gets (by continuation from the f it was found at). That state is under one cap, or no state is.
    From there a chain of LPs lowers the other length and keeps the first one under its cap, so every step starts
    from a legal state. Both orders are tried, then the state of the smallest sum."""
    steps = path(mod['f0'], f)
    for first in (0, 1, None):
        cost = (1.0, 1.0) if first is None else ((1.0, 0.02) if first == 0 else (0.02, 1.0))
        at = corner_len(mod, mod['f0'], mod['P'], mod['y0'] + 1e-6, mod['x0'] + 1e-6, cost)
        for g in steps:
            if at is None: break
            at = corner_len(mod, float(g), at[2], at[0] + 0.02, at[1] + 0.02, cost)
        if at is None: continue
        if at[0] <= cap_y + 1e-9 and at[1] <= cap_x + 1e-9: return at
        if first is None:
            r = corner_len(mod, f, at[2], at[0], at[1], caps=(cap_y - at[0], cap_x - at[1]))
        elif first == 0:
            if at[0] > cap_y + 1e-9: return None            # the smallest y0 is above its cap: no state fits
            r = corner_len(mod, f, at[2], at[0], at[1], cost=(1e-3, 1.0), caps=(cap_y - at[0], None))
        else:
            if at[1] > cap_x + 1e-9: return None
            r = corner_len(mod, f, at[2], at[0], at[1], cost=(1.0, 1e-3), caps=(None, cap_x - at[1]))
        if r is not None and r[0] <= cap_y + 1e-9 and r[1] <= cap_x + 1e-9: return r
    return None


def assemble(lib, n, C, F1, F2, s1, s2, f):
    """The layout of one choice at f: modules at their LP positions, flush stacks, the rest. -> (array x, y, radians) or (None, why)"""
    m = math.isqrt(n - 1); L = m + f
    qc, q1, q2 = C['q'], F1['q'], F2['q']
    c1, c2 = qc['c1'], qc['c2']
    W1, W2 = c1 - 1 + f, c2 - 1 + f
    t1, t2 = flush_tilt(c1, f), flush_tilt(c2, f); p1, p2 = 1 / math.cos(t1), 1 / math.cos(t2)
    f1 = far_at(q1, f); f2 = far_at(q2, f)
    if f1 is None or f2 is None: return None, 'a far zone does not exist at f'
    co = corner_at(qc, f, L - f1[0] - s1 * p1, L - f2[0] - s2 * p2)
    if co is None: return None, 'the corner does not fit under both arms'
    y0, x0, Pc = co
    parts = [Pc]
    parts += [stack_squares(c1, qc['lean1'] * math.degrees(t1), W1 / 2, y0 + (j + .5) * p1) for j in range(s1)]
    parts += [stack_squares(c2, qc['lean2'] * math.degrees(t2), x0 + (j + .5) * p2, W2 / 2, along_x=False) for j in range(s2)]
    ni, nj = m - c1 + 1, m - c2 + 1
    gone = set(map(tuple, qc['miss']))
    a = f1[1].copy()
    if q1['lean'] != -qc['lean1']: a[:, 0] = W1 - a[:, 0]; a[:, 2] = -a[:, 2]
    parts.append(np.c_[a[:, 0], L - a[:, 1], -a[:, 2]]); gone |= {(i, nj - 1 - j) for i, j in q1['miss']}
    a = f2[1].copy()
    if q2['lean'] != qc['lean2']: a[:, 0] = W2 - a[:, 0]; a[:, 2] = -a[:, 2]
    parts.append(np.c_[L - a[:, 1], a[:, 0], a[:, 2]]); gone |= {(ni - 1 - i, j) for j, i in q2['miss']}
    # the rest: on the grid, but row 0 and column 0 keep the slide of the corner (its found places, then its grant
    # all along the run) and, beside a far zone that pokes, the found places of that zone
    cs = corner_slide(qc)
    off = {(i, 0): cs(i, 0) for i in range(ni)}; off.update({(0, j): cs(0, j) for j in range(1, nj)})
    if SLIDE:
        for far, arm, fl, nn, grant in ((q2, 2, f2[0], ni, qc.get('g2', 0.0)), (q1, 1, f1[0], nj, qc.get('g1', 0.0))):
            if far.get('slide') is None: continue
            sl = far['slide']
            reach = int(math.ceil(fl + far['c'] * math.sin(flush_tilt(far['c'], f)) + 2.5))     # the cells far_state holds
            for j in range(min(len(sl), nn - 1, reach)):
                if arm == 2: off[(ni - 1 - j, 0)] = (-float(sl[j]), 0.0)
                else: off[(0, nj - 1 - j)] = (0.0, -float(sl[j]))
        # along the row (the column) no cell may stand further towards the corner than the cell before it
        if any(off[(i + 1, 0)][0] < off[(i, 0)][0] - 1e-9 for i in range(ni - 1) if (i, 0) not in gone and (i + 1, 0) not in gone) or \
           any(off[(0, j + 1)][1] < off[(0, j)][1] - 1e-9 for j in range(nj - 1) if (0, j) not in gone and (0, j + 1) not in gone):
            return None, 'the corner grants a far zone no slide'
    parts.append(np.array([(W1 + .5 + i + off.get((i, j), (0.0, 0.0))[0], W2 + .5 + j + off.get((i, j), (0.0, 0.0))[1], 0.0)
                           for i in range(ni) for j in range(nj) if (i, j) not in gone]))
    P = np.vstack(parts); P[:, 2] = np.radians(P[:, 2])
    if len(P) != n: return None, 'holds %d squares' % len(P)
    return P, None


def first_f(n, C, F1, F2, s1, s2, f_from, f_to, step=1e-3):
    """Smallest f in [f_from, f_to] at which the choice puts together a legal layout (scan, then bisection to 1e-4)."""
    def ok(f):
        P, _ = assemble(None, n, C, F1, F2, s1, s2, f)
        return P is not None and layout_state(P)[1] > -1e-7
    f = f_from
    while f <= f_to + 1e-12:
        if ok(f):
            lo, hi = f - step, f
            if f > f_from:
                for _ in range(4):
                    mid = (lo + hi) / 2
                    if ok(mid): hi = mid
                    else: lo = mid
            return hi
        f += step
    return None


def layout_state(P):
    """(side, smallest gap of any pair) of a layout x, y, radians"""
    from methods_lp import side, min_gap
    return float(side(P)), float(min_gap(P))


def write_layout(path, n, P):
    with open(path, 'w', newline='') as g:
        w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for k, (x, y, th) in enumerate(P): w.writerow([n, k, repr(float(x)), repr(float(y)), repr(float(th))])


# ----------------------------------------------------------------------------------------------- commands

def held_sources(results_dir):
    """n -> (source, licence): the newest table of the lane that names the n. The tables are the per-round bests
    (*best-20*.tsv) and the tables of a step that changed the held file outside a round (angle-harvest-2026-11-10.tsv);
    they are read in the order of the date in their name, then the round, then the name."""
    import re
    src = {}
    def order(q):
        b = os.path.basename(q); r = b.split('-')[0]
        return (re.search(r'20\d\d-\d\d-\d\d', b).group(0), int(r[5:]) if r.startswith('round') and r[5:].isdigit() else 0, b)
    for p in sorted(set(glob.glob(results_dir + '/*best-20*.tsv') + glob.glob(results_dir + '/*-harvest-20*.tsv')), key=order):
        for r in csv.DictReader(open(p), delimiter='\t'):
            if r.get('n', '').isdigit() and r.get('source'): src[int(r['n'])] = (r['source'], r.get('licence', ''))
    return src


def cmd_library(a):
    work, held_csv, results = a[0], a[1], a[2]
    os.makedirs(work, exist_ok=True)
    hs = held_sources(results)
    mods = []; layouts = []; why = collections.Counter(); seen = {}
    H = read_layouts(held_csv)
    def take(sq, n, src, lic, tag):
        s = normal(sq)[0]
        if (n, round(s, 7)) in seen: return
        d, r = cut(sq, n)
        if d is None:
            why[(tag == 'h', r.split(' is ')[0].split(' holds')[0].split(' at cell')[0])] += 1; return
        seen[(n, round(s, 7))] = tag
        ms = modules_of(d, src, lic, tag)
        mods.extend(ms)
        t1, t2 = d['arm'][1]['t'], d['arm'][2]['t']
        layouts.append(dict(n=n, tag=tag, m=d['m'], k=d['k'], f=d['f'], s=d['s'], c1=d['c1'], c2=d['c2'], s1=d['s1'], s2=d['s2'],
                            ids=[q['id'] for q in ms], err1=d['arm'][1]['err'], err2=d['arm'][2]['err'], src=src, licence=lic,
                            loss=k_flush(d['m'], d['f'], d['c1'], d['c2']) - d['k'], loss_cut=sum(q['loss0'] for q in ms)))
    for n in sorted(H):
        if n >= 300:
            src, lic = hs.get(n, ('seed merged0 (Couzo, Samanyu-dev)', 'see README'))
            take(H[n], n, 'held: ' + src, lic, 'h')
    nheld = len(layouts)
    for spec in a[3:]:
        tag, dr = spec.split('=', 1)
        bt = dr + '/best.tsv'
        if not os.path.exists(bt): continue
        for r in csv.DictReader(open(bt), delimiter='\t'):
            n = int(r['n'])
            if n < 300 or not any(q in r['licence'] for q in OK_LICENCE): continue
            p = '%s/best/%d.csv' % (dr, n)
            if not os.path.exists(p): continue
            try: sq = read_layouts(p)[n]
            except Exception: continue
            if len(sq) == n: take(sq, n, r['source'], r['licence'], tag)
    pickle.dump(dict(mods=mods, layouts=layouts), open(work + '/library.pkl', 'wb'))
    with open(work + '/library.tsv', 'w') as h:
        h.write('id\tkind\tc\tsignature\tcount\tlength\tlength2\tf\ttilt\tloss\tn\tsource\tlicence\n')
        for q in mods:
            if q['kind'] == 'far':
                h.write('%s\tfar%d\t%d\t%s\t%d\t%.5f\t\t%.6f\t%.3f\t%.3f\t%d\t%s\t%s\n' % (
                    q['id'], q['arm'], q['c'], q['sig'], q['count'], q['len0'], q['f0'], q['tilt0'], q['loss0'], q['n'], q['src'], q['licence']))
            else:
                h.write('%s\tcorner\t%dx%d\t%s\t%d\t%.5f\t%.5f\t%.6f\t%.3f/%.3f\t%.3f\t%d\t%s\t%s\n' % (
                    q['id'], q['c1'], q['c2'], q['sig'], q['count'], q['y0'], q['x0'], q['f0'], q['tilt1'], q['tilt2'], q['loss0'], q['n'], q['src'], q['licence']))
    print('layouts cut: %d held, %d public; modules %d' % (nheld, len(layouts) - nheld, len(mods)))
    print('not cut:', dict(why))
    e = np.array([abs(l['loss'] - l['loss_cut']) for l in layouts])
    print('loss by the model against the sum of the three zones: median |diff| %.3f, max %.3f' % (np.median(e), e.max()))


def cmd_lens(a):
    from multiprocessing import Pool
    work = a[0]; jobs = int(a[a.index('--jobs') + 1]) if '--jobs' in a else 2
    lib = pickle.load(open(work + '/library.pkl', 'rb'))
    out = pickle.load(open(work + '/lens.pkl', 'rb')) if os.path.exists(work + '/lens.pkl') and '--all' not in a else {}
    todo = [q for q in lib['mods'] if q['id'] not in out]     # a module keeps its id, so a table is made once
    print('modules %d, with a table %d, to do %d' % (len(lib['mods']), len(out), len(todo)), flush=True)
    with Pool(jobs) as pool:
        for k, r in enumerate(pool.imap_unordered(tabulate, todo, chunksize=1)):
            out[r['id']] = r
            if k % 20 == 0: print(k, len(todo), flush=True)
    pickle.dump(out, open(work + '/lens.pkl.tmp', 'wb')); os.replace(work + '/lens.pkl.tmp', work + '/lens.pkl')
    print('done', len(out))


def _held_board(details, board):
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    brd = {int(r['n']): float(r['L']) for r in json.load(open(board))}
    return held, brd


def cmd_model(a):
    """Points 1 to 3 of the zone-loss model, from the cut of the held file."""
    work, details, board = a[:3]
    lib = pickle.load(open(work + '/library.pkl', 'rb'))
    held, brd = _held_board(details, board)
    rows = []
    for l in lib['layouts']:
        if l['tag'] != 'h': continue
        n, m = l['n'], l['m']
        fb = brd[n] - m
        rows.append((n, l['f'], l['c1'], l['c2'], l['loss'], k_flush(m, fb, l['c1'], l['c2']) - l['k'], l['loss_cut'], l['err1'], l['err2']))
    R = np.array(rows)
    d = R[:, 4] - R[:, 5]
    for nm, sel in (('f < 0.87', R[:, 1] < 0.87), ('f >= 0.87', R[:, 1] >= 0.87)):
        print('%s: %d layouts, our loss - board loss: median %.2f, min %.2f, max %.2f' % (nm, sel.sum(), np.median(d[sel]), d[sel].min(), d[sel].max()))
    for n in (757, 814, 756, 873):
        r = R[R[:, 0] == n]
        if len(r): print('n=%d ours %.2f board %.2f' % (n, r[0, 4], r[0, 5]))
    e = np.abs(R[:, 4] - R[:, 6])
    print('loss of the model - sum of the three zone losses: median %.3f, max %.3f; flush error of the stacks: median %.1e, max %.1e' % (
        np.median(e), e.max(), np.median(np.abs(R[:, 7:9])), np.abs(R[:, 7:9]).max()))
    for c in ((8, 8), (7, 7), (6, 6)):
        for lo, hi in ((0.65, 0.75), (0.75, 0.87), (0.87, 0.94), (0.94, 1.0)):
            s = (R[:, 2] == c[0]) & (R[:, 3] == c[1]) & (R[:, 1] >= lo) & (R[:, 1] < hi)
            if s.sum(): print('c = %d and %d, f %.2f to %.2f: %d layouts, our loss %.2f to %.2f, board %.2f to %.2f' % (
                c[0], c[1], lo, hi, s.sum(), R[s, 4].min(), R[s, 4].max(), R[s, 5].min(), R[s, 5].max()))
    g = {'f < 0.85': [0, 0.0], 'f >= 0.85': [0, 0.0]}
    for n in held:
        m = math.isqrt(n - 1)
        if n < 300 or held[n] >= m + 1 - 1e-9: continue
        b = g['f < 0.85' if held[n] - m < 0.85 else 'f >= 0.85']
        b[0] += 1; b[1] += (held[n] - brd[n]) / math.sqrt(n)
    print('gap to the board for n >= 300 below the plain grid:', {k: (v[0], round(v[1], 4)) for k, v in g.items()}, 'total %.4f' % sum(v[1] for v in g.values()))


def cmd_control(a):
    work = a[0]
    lib = Library(work)
    print('modules with a table: %d corners, %d far zones' % (len(lib.corners), sum(len(v) for v in lib.far.values())))
    # the lock of a far zone against the f it was found at
    d = np.array([F['q']['f0'] - F['lock'] for v in lib.far.values() for F in v])
    print('far zones: found f - lock: median %.4f; within 1e-3: %d of %d; more than 0.01 below: %d' % (np.median(d), (d < 1e-3).sum(), len(d), (d > 0.01).sum()))
    own = np.array([F['q']['len0'] - lib.lens[F['id']]['own'] for v in lib.far.values() for F in v])
    print('far zones: found length - LP length at the found f: median %.4f, 5%% %.4f, 95%% %.4f' % (np.median(own), np.percentile(own, 5), np.percentile(own, 95)))
    # control 1
    err = []; out = []
    for l in lib.layouts:
        C, F1, F2 = (lib.byid.get(i) for i in (l['ids'][2], l['ids'][0], l['ids'][1]))
        if C is None or F1 is None or F2 is None:
            out.append((l['n'], l['tag'], 'no table')); continue
        r = lib.fit(C, F1, F2, l['m'], l['s1'], l['s2'])
        if r is None:
            out.append((l['n'], l['tag'], 'no fit')); continue
        err.append((r[0] - l['f'], l['n'], l['tag'], r[1], l['f'], max(F1['lock'], F2['lock'])))
    E = np.array([e[0] for e in err])
    print('control 1: %d layouts; |f - held f| <= 1e-3 on %d; median %.1e; worst below %.4f, worst above %.4f; no result: %d' % (
        len(E), (np.abs(E) <= 1e-3).sum(), np.median(np.abs(E)), E.min(), E.max(), len(out)))
    print('  stopped by a lock or a table end: %d, by the arms: %d' % (sum(e[3] == 'edge' for e in err), sum(e[3] == 'fit' for e in err)))
    for e in sorted(err, key=lambda e: -abs(e[0]))[:12]: print('  n=%d%s diff %+.4f stop %s f %.4f lock %.4f' % (e[1], e[2], e[0], e[3], e[4], e[5]))
    for o in out[:20]: print('  ', o)
    with open(work + '/control1.tsv', 'w') as h:
        h.write('n\ttag\tf\tf_generator\tdiff\tstop\n')
        for e in err: h.write('%d\t%s\t%.6f\t%.6f\t%+.6f\t%s\n' % (e[1], e[2], e[4], e[4] + e[0], e[0], e[3]))
    # control 2: the modules of one layout on its line neighbours
    L = {(l['n'], l['tag']): l for l in lib.layouts}
    for src, steps in ((814, (-1, 1)), (757, (1, 2)), (873, (-1, -2))):
        l = L.get((src, 'h'))
        if l is None: continue
        C, F1, F2 = (lib.byid.get(i) for i in (l['ids'][2], l['ids'][0], l['ids'][1]))
        if C is None or F1 is None or F2 is None: print('control 2: no table for', src); continue
        for st in steps:
            m = l['m'] + st; s1, s2 = l['s1'] + st, l['s2'] + st
            n = C['count'] + F1['count'] + F2['count'] + s1 * l['c1'] + s2 * l['c2'] + (m - l['c1'] + 1) * (m - l['c2'] + 1)
            r = lib.fit(C, F1, F2, m, s1, s2)
            hl = L.get((n, 'h'))
            ex = first_f(n, C, F1, F2, s1, s2, hl['f'] - 0.012, min(0.998, hl['f'] + 0.035)) if hl else None
            print('control 2: modules of %d on n=%d (m=%d, stacks %d and %d): table %s; put together at f %s; held f %s' % (
                src, n, m, s1, s2, 'no fit' if r is None else '%.4f (%s)' % r, 'none' if ex is None else '%.4f' % ex,
                'n/a' if hl is None else '%.4f' % hl['f']), flush=True)


def cmd_predict(a):
    work, details, board, out = a[:4]
    held, brd = _held_board(details, board)
    lib = Library(work, only=usable)
    rows = []; closes = 0.0; gap = 0.0; nreg = 0
    ns = [n for n in sorted(held) if n >= 300 and held[n] < math.isqrt(n - 1) + 1 - 1e-9]
    for n in ns:
        m = math.isqrt(n - 1)
        r = lib.best(n, top=1)
        if not r: continue
        f, stop, C, F1, F2, s1, s2 = r[0]
        nreg += 1; gap += (held[n] - brd[n]) / math.sqrt(n)
        closes += max(0.0, held[n] - (m + f)) / math.sqrt(n)
        rows.append((n, m, n - m * m, held[n], brd[n], m + f, stop, C, F1, F2, s1, s2))
        if len(rows) % 40 == 0: print(n, flush=True)
    with open(out, 'w') as h:
        h.write('n\tm\tk\theld_side\tboard_side\tpredicted_side\tpredicted_minus_held\tstop\tcorner\tfar1\tfar2\tstacks1\tstacks2\tcorner_source\tfar1_source\tfar2_source\n')
        for n, m, k, hs, bs, ps, stop, C, F1, F2, s1, s2 in rows:
            src = ['%s [%s]' % (x['q']['src'], x['q']['licence']) for x in (C, F1, F2)]
            h.write('%d\t%d\t%d\t%.6f\t%.6f\t%.6f\t%+.6f\t%s\t%s\t%s\t%s\t%d\t%d\t%s\t%s\t%s\n' % (
                n, m, k, hs, bs, ps, ps - hs, stop, C['id'], F1['id'], F2['id'], s1, s2, src[0], src[1], src[2]))
    d = np.array([r[5] - r[3] for r in rows])
    print('n >= 300 below the plain grid: %d; with a prediction: %d (their gap to the board %.4f)' % (len(ns), nreg, gap))
    print('predicted below held by more than 0.002: %d; by more than 1e-4: %d; within 1e-3 of held: %d' % ((d < -0.002).sum(), (d < -1e-4).sum(), (np.abs(d) <= 1e-3).sum()))
    print('score the library closes if every prediction below held were built: %.5f' % closes)


def cmd_start(a):
    """modules.py start WORK OUT.csv N CORNER FAR1 FAR2 S1 S2 F"""
    work, out, n, ic, i1, i2, s1, s2, f = a[0], a[1], int(a[2]), a[3], a[4], a[5], int(a[6]), int(a[7]), float(a[8])
    lib = Library(work)
    P, why = assemble(lib, n, lib.byid[ic], lib.byid[i1], lib.byid[i2], s1, s2, f)
    if P is None:
        print('n=%d no start: %s' % (n, why)); return 1
    side, gap = layout_state(P)
    print('n=%d start side %.6f (m + f = %.6f) smallest gap %.2e' % (n, side, math.isqrt(n - 1) + f, gap))
    write_layout(out, n, P)
    return 0


def cmd_check(a):
    """modules.py check WORK ROWS.tsv OUT.tsv [--up 3e-3] [--step 5e-4]
    The rows of a queue as the build starts them: the far zones walked to f (far_at) and the corner under both caps
    (corner_at), with the gap test of the layout. A table holds a far zone only at its knots, 0.005 apart, and the
    length can jump between two knots (on 2026-11-12, 814h09.F1 is 5.2e-3 longer at f = 0.95375 than its table, so
    the 601 choice predicted 2e-4 below held had no start there). Writes each row with the smallest f at which it
    starts (first_f, from the predicted f up to --up above it) and that side; empty when it does not start."""
    work, rows_p, out = a[:3]
    up = float(a[a.index('--up') + 1]) if '--up' in a else 3e-3
    step = float(a[a.index('--step') + 1]) if '--step' in a else 5e-4
    lib = Library(work)
    rows = [r for r in csv.DictReader(open(rows_p), delimiter='\t') if r['n'] != 'n']
    with open(out + '.tmp', 'w') as h:
        h.write('n\tpredicted_side\tchecked_side\tchecked_minus_predicted\tcorner\tfar1\tfar2\tstacks1\tstacks2\tf\n')
        for r in rows:
            n, f = int(r['n']), float(r['f']); m = math.isqrt(n - 1)
            C, F1, F2 = lib.byid.get(r['corner']), lib.byid.get(r['far1']), lib.byid.get(r['far2'])
            g = None if None in (C, F1, F2) else first_f(n, C, F1, F2, int(r['stacks1']), int(r['stacks2']), f, f + up, step)
            h.write('%d\t%.6f\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%r\n' % (n, m + f, '' if g is None else '%.6f' % (m + g), '' if g is None else '%+.6f' % (g - f),
                                                                r['corner'], r['far1'], r['far2'], r['stacks1'], r['stacks2'], f))
            h.flush()
    os.replace(out + '.tmp', out)
    return 0


def _squeeze(n, P, fq=None, log=print):
    import methods_lp
    P, L, it = methods_lp.slp(methods_lp.normal(P), iters=60)
    log('n=%d lp side %.9f after %d steps, gap %.2e' % (n, L, it, methods_lp.min_gap(P)))
    if fq and os.path.exists(fq):
        import subprocess, tempfile
        d = tempfile.mkdtemp(prefix='modfq')
        with open(d + '/a.txt', 'w') as h:
            h.write('%d %r\n' % (n, float(L)))
            for x, y, th in methods_lp.normal(P): h.write('%r %r %r\n' % (float(x), float(y), math.degrees(float(th))))
        try:
            r = subprocess.run([fq, 'quench', '--in', d + '/a.txt', '--out', d + '/b.txt', '--no-alm', '--loosen', '1.0', '--flip-top', '64', '--pit', '600'],
                               capture_output=True, text=True, timeout=1500)
            if r.returncode == 0 and os.path.exists(d + '/b.txt'):
                rows = [l.split() for l in open(d + '/b.txt') if l.strip() and not l.startswith('#')]
                Q = np.array([[float(v) for v in q[:3]] for q in rows[1:n + 1]]); Q[:, 2] = np.radians(Q[:, 2])
                Q, L2, _ = methods_lp.slp(methods_lp.normal(Q), iters=10)
                log('n=%d fq side %.9f, gap %.2e' % (n, L2, methods_lp.min_gap(Q)))
                if L2 < L and methods_lp.min_gap(Q) > -1e-9: P, L = Q, L2     # the take step opens the last gaps (floatsafe)
        except subprocess.TimeoutExpired:
            log('n=%d fq timed out' % n)
        for q in ('a.txt', 'b.txt'):
            if os.path.exists(d + '/' + q): os.remove(d + '/' + q)
        os.rmdir(d)
    return methods_lp.normal(P), L


def cmd_squeeze(a):
    """modules.py squeeze START.csv OUT.csv [FQ]   the lane's sequential LP, then the fq quench when the binary is given"""
    n, sq = next(iter(read_layouts(a[0]).items()))
    P, L = _squeeze(n, np.array(sq), a[2] if len(a) > 2 else None)
    write_layout(a[1], n, P)
    print('n=%d final side %.9f' % (n, L))
    return 0


def cmd_build(a):
    """modules.py build WORK RAWDIR DETAILS.csv N [--top 3] [--fq PATH] [--deadline FILE] [--slack 0.0]
    Build the best choices of modules for N: the start layout a little above the predicted f, then the squeeze.
    --slack S also builds choices predicted up to S of side above held: the squeeze lands below the prediction."""
    work, raw, details, n = a[0], a[1], a[2], int(a[3])
    top = int(a[a.index('--top') + 1]) if '--top' in a else 3
    fq = a[a.index('--fq') + 1] if '--fq' in a else None
    dl = a[a.index('--deadline') + 1] if '--deadline' in a else None
    slack = float(a[a.index('--slack') + 1]) if '--slack' in a else 0.0
    import time
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}[n]
    lib = Library(work, only=usable)
    os.makedirs(raw, exist_ok=True); m = math.isqrt(n - 1)
    done = 0
    for f, stop, C, F1, F2, s1, s2 in lib.best(n, top=top, below=held - m + slack):
        if dl and os.path.exists(dl) and time.time() > float(open(dl).read().strip()): print('n=%d deadline' % n); break
        P = None
        for up in (2e-4, 6e-4, 1.5e-3, 3e-3):
            P, why = assemble(lib, n, C, F1, F2, s1, s2, f + up)
            if P is not None:
                side, gap = layout_state(P)
                if gap > -1e-7 and side < m + f + up + 1e-6: break
                why = 'start side %.6f gap %.1e' % (side, gap); P = None
        tagc = '%s+%s+%s' % (C['id'], F1['id'], F2['id'])
        if P is None:
            print('n=%d %s stacks %d,%d predicted %.6f: no start (%s)' % (n, tagc, s1, s2, m + f, why), flush=True); continue
        print('n=%d %s stacks %d,%d predicted %.6f held %.6f start %.6f gap %.1e' % (n, tagc, s1, s2, m + f, held, side, gap), flush=True)
        Q, L = _squeeze(n, P, fq, log=lambda s: print(s, flush=True))
        done += 1
        write_layout('%s/%d-%d.csv' % (raw, n, done), n, Q)
        json.dump(dict(n=n, predicted=m + f, start=side, built=L, held=held, stop=stop, stacks=[s1, s2],
                       modules=[dict(id=x['id'], source=x['q']['src'], licence=x['q']['licence']) for x in (C, F1, F2)]),
                  open('%s/%d-%d.json' % (raw, n, done), 'w'))
        print('n=%d BUILT %s predicted %.6f built %.9f held %.9f (%+.6f)' % (n, tagc, m + f, L, held, L - held), flush=True)
    return 0


def cmd_take(a):
    """modules.py take DETAILS.csv TAKEDIR RAWDIR [RAWDIR ...] [--beat TAKEDIR ...]
    Certify the builds the lane's way (floatsafe, below held by 1e-10). --beat: a build is kept only if it is also
    below the same n of these take dirs (their take.tsv)."""
    import floatsafe
    details, out = a[:2]
    raws = [x for x in (a[2:a.index('--beat')] if '--beat' in a else a[2:])]
    beat = a[a.index('--beat') + 1:] if '--beat' in a else []
    held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(details))}
    bar = dict(held); who = {}
    for d in beat:
        if not os.path.exists(d + '/take.tsv'): continue
        for r in csv.DictReader(open(d + '/take.tsv'), delimiter='\t'):
            if r['n'].isdigit() and float(r['new']) < bar[int(r['n'])]: bar[int(r['n'])] = float(r['new']); who[int(r['n'])] = os.path.basename(d.rstrip('/'))
    best = {}; nraw = 0
    for raw in raws:
        for p in sorted(glob.glob(raw + '/*.csv')):
            n = int(os.path.basename(p)[:-4].split('-')[0]); nraw += 1
            rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(p))]
            if len(rows) != n: print('drop', n, 'rows', len(rows), p); continue
            _, fr, score, e = floatsafe.work((n, rows))
            if fr is None or not (score < held[n] - 1e-10): print('drop', n, score, held[n], e, p); continue
            if not (score < bar[n] - 1e-10): print('drop', n, score, 'not below', who.get(n), bar[n], p); continue
            if n not in best or score < best[n][0]: best[n] = (score, fr, p)
    os.makedirs(out, exist_ok=True)
    lines = ['n\theld\tnew\tgain\tsource\tlicence\n']; tot = 0.0; net = 0.0
    for n in sorted(best):
        score, fr, p = best[n]
        with open('%s/%d.csv.tmp' % (out, n), 'w', newline='') as g:
            w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
            for r in fr: w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
        os.replace('%s/%d.csv.tmp' % (out, n), '%s/%d.csv' % (out, n))
        j = json.load(open(p[:-4] + '.json'))
        sq = 'family_step.squeeze' if j.get('squeeze') == 'family' else 'methods_lp, fq'
        src = ('modules.py: corner %s, far zones %s and %s, squeezed (' + sq + ')') % tuple('%s <%s>' % (q['id'], q['source']) for q in j['modules'])
        lic = '; '.join(sorted(set(q['licence'] for q in j['modules'])))
        tot += held[n] - score; net += bar[n] - score
        lines.append('%d\t%r\t%r\t%.3e\t%s\t%s\n' % (n, held[n], score, held[n] - score, src, lic))
        print('keep', n, held[n], score, '%.3e' % (held[n] - score), 'over the other takes %.3e' % (bar[n] - score), p)
    for p in glob.glob(out + '/*.csv'):                         # a csv that no row names any more
        if int(os.path.basename(p)[:-4]) not in best: os.remove(p)
    with open(out + '/take.tsv.tmp', 'w') as h: h.writelines(lines)
    os.replace(out + '/take.tsv.tmp', out + '/take.tsv')
    print('raw files', nraw, 'kept', len(best), 'gain', repr(tot), 'gain over the other takes', repr(net))
    return 0


def cmd_grow(a):
    """modules.py grow WORK RESULTS_DIR [--label L] TAG=PATH [TAG=PATH ...]
    Cut more layouts into the library. PATH is a take dir (per-n csv and take.tsv, which names source and licence
    of every row) or a held file (sources from RESULTS_DIR). A layout the library holds already (same n, same side
    to 1e-7) is skipped. The modules get the tag in their id; their tables are made by the next `lens`.
    Writes the new ids to WORK/new-L.txt."""
    work, results = a[0], a[1]
    label = a[a.index('--label') + 1] if '--label' in a else 'grow'
    specs = [x for x in a[2:] if '=' in x]
    lib = pickle.load(open(work + '/library.pkl', 'rb'))
    seen = {(l['n'], round(l['s'], 7)) for l in lib['layouts']}
    ids = {q['id'] for q in lib['mods']}
    hs = held_sources(results)
    journal = work + '/new-' + label + '.txt'
    prior = lib.setdefault('growth_ids', {}).get(label, [])
    if os.path.exists(journal):
        prior += open(journal).read().split()
    new = list(dict.fromkeys(i for i in prior if i in ids))
    initial = len(new)
    why = collections.Counter(); per = collections.Counter()
    def checkpoint():
        # Geometry and its pending ids share one atomic pickle checkpoint.
        lib['growth_ids'][label] = list(new)
        with open(work + '/library.pkl.tmp', 'wb') as h:
            pickle.dump(lib, h)
        os.replace(work + '/library.pkl.tmp', work + '/library.pkl')
        with open(journal + '.tmp', 'w') as h:
            h.write(''.join(i + '\n' for i in new))
        os.replace(journal + '.tmp', journal)

    for spec in specs:
        tag, path = spec.split('=', 1)
        items = []
        if os.path.isdir(path):
            if not os.path.exists(path + '/take.tsv'): continue
            name = os.path.basename(path.rstrip('/'))
            for r in csv.DictReader(open(path + '/take.tsv'), delimiter='\t'):
                p = '%s/%s.csv' % (path, r['n'])
                if r['n'].isdigit() and os.path.exists(p):
                    items.append((int(r['n']), p, '%s n=%s: %s' % (name, r['n'], r.get('source', '')), r.get('licence', '')))
        else:
            H = read_layouts(path)
            for n in sorted(H):
                src, lic = hs.get(n, ('seed merged0 (Couzo, Samanyu-dev)', 'see README'))
                items.append((n, H[n], 'held: ' + src, lic))
        for n, what, src, lic in items:
            if n < 300: continue
            try: sq = what if isinstance(what, list) else read_layouts(what)[n]
            except Exception: why[(tag, 'unreadable')] += 1; continue
            if len(sq) != n: why[(tag, 'wrong count')] += 1; continue
            sd = normal(sq)[0]
            if (n, round(sd, 7)) in seen: why[(tag, 'held already')] += 1; continue
            d, r = cut(sq, n)
            if d is None:
                why[(tag, r.split(' is ')[0].split(' holds')[0].split(' at cell')[0])] += 1; continue
            seen.add((n, round(sd, 7)))
            t = tag; k = 0
            while '%d%s.C' % (n, t) in ids:
                t = tag + 'abcdefghijklmnopqrstuvwxyz'[k]; k += 1
            ms = modules_of(d, src, lic, t)
            for q in ms: q['ours'] = True; ids.add(q['id'])
            tw, ids_slide = slid(d, ms)
            lib['mods'].extend(ms + tw); new.extend(q['id'] for q in ms + tw); per[tag] += 1
            lib['layouts'].append(dict(n=n, tag=t, m=d['m'], k=d['k'], f=d['f'], s=d['s'], c1=d['c1'], c2=d['c2'], s1=d['s1'], s2=d['s2'],
                                       ids=[q['id'] for q in ms], ids_slide=ids_slide, err1=d['arm'][1]['err'], err2=d['arm'][2]['err'], src=src, licence=lic,
                                       loss=k_flush(d['m'], d['f'], d['c1'], d['c2']) - d['k'], loss_cut=sum(q['loss0'] for q in ms)))
            checkpoint()
    checkpoint()
    print('grow %s: layouts cut %s; modules added %d; library now %d layouts, %d modules' % (label, dict(per), len(new) - initial, len(lib['layouts']), len(lib['mods'])))
    print('not cut:', {'%s: %s' % k: v for k, v in why.items()})
    return 0


def cmd_slide(a):
    """modules.py slide WORK SOURCE [SOURCE ...]
    Give the library the slid twins of its modules (see slid). A module is cut again from its layout, which is looked
    up by n and side in the sources: a submission file, a take dir (N.csv) or a merged harvest dir (best/N.csv).
    The next `lens` makes the tables of the twins. Writes their ids to WORK/slide-ids.txt."""
    work, srcs = a[0], a[1:]
    lib = pickle.load(open(work + '/library.pkl', 'rb'))
    files = {p: read_layouts(p) for p in srcs if os.path.isfile(p)}
    by = {q['id']: q for q in lib['mods']}
    found = 0; new = []; lost = []
    for l in lib['layouts']:
        n = l['n']; d = None
        if 'ids_slide' in l: found += 1; continue
        cands = [H[n] for H in files.values() if n in H]
        for p in srcs:
            if os.path.isdir(p):
                for q in ('%s/%d.csv' % (p, n), '%s/best/%d.csv' % (p, n)):
                    if os.path.exists(q):
                        try: cands.append(read_layouts(q)[n])
                        except Exception: pass
        for sq in cands:
            if len(sq) == n and round(normal(sq)[0], 7) == round(l['s'], 7):
                d, _ = cut(sq, n)
                if d is not None: break
        if d is None: lost.append('%d%s' % (n, l['tag'])); continue
        found += 1
        tw, ids = slid(d, [by[i] for i in l['ids']])
        l['ids_slide'] = ids
        for v in tw:
            if v['id'] not in by: lib['mods'].append(v); by[v['id']] = v; new.append(v['id'])
    pickle.dump(lib, open(work + '/library.pkl.tmp', 'wb')); os.replace(work + '/library.pkl.tmp', work + '/library.pkl')
    with open(work + '/slide-ids.txt', 'w') as h: h.write(''.join(i + '\n' for i in new))
    far = [q for q in lib['mods'] if q['kind'] == 'far' and q['id'].endswith('~')]
    cor = [q for q in lib['mods'] if q['kind'] == 'corner' and q['id'].endswith('~')]
    print('layouts found again: %d of %d (not found: %s)' % (found, len(lib['layouts']), ' '.join(lost) or 'none'))
    print('slid twins: %d far zones (%d need a slide above zero), %d corners (%d grant a slide above zero); new now: %d' % (
        len(far), sum(q['g'] > 0 for q in far), len(cor), sum(max(q['g1'], q['g2']) > 0 for q in cor), len(new)))
    return 0


GLEVELS = (0.04, 0.10, 0.16)                             # the grants a corner is given (in units of side)


def cmd_grant(a):
    """modules.py grant WORK OUT.pkl [--part I/K] [--levels G,G,...]     modules.py grant WORK --merge OUT.pkl [OUT.pkl ...]
    A far zone that pokes into row 0 (column 0) needs every cell of that row to stand g towards the corner, and only
    the corner of its own layout grants it (its slid twin). Here every plain corner (one whose cells were found on the
    grid) is given the grants of GLEVELS that the poking far zones of its stack size need: row 0 (column 0) is pushed
    by g at the head, as corner_slide does for a grant, and the corner is solved again at the f it was found at for the
    5 costs of COST. Its table is the table of the corner plus that cost in y0 and x0 (each at least 0), all along f
    (measured at one f).
    The build solves the granted corner exactly (corner_at with the same slide). Variant id: corner id + '^<arm>g<g*100>'.
    --levels: the grants to give instead of GLEVELS; a variant the library holds already is not made again, and a variant
    whose cells (1, 0) and (0, 1) overlap (cells_collide) is not made at all.
    --merge: add the variants to WORK/library.pkl and WORK/lens.pkl and write their ids to WORK/grant-ids.txt."""
    work = a[0]
    if '--merge' in a:
        lib = pickle.load(open(work + '/library.pkl', 'rb')); lens = pickle.load(open(work + '/lens.pkl', 'rb'))
        have = {q['id'] for q in lib['mods']}; new = []
        for p in a[a.index('--merge') + 1:]:
            for v, t in pickle.load(open(p, 'rb')):
                if v['id'] in have: continue
                lib['mods'].append(v); lens[v['id']] = t; have.add(v['id']); new.append(v['id'])
        pickle.dump(lib, open(work + '/library.pkl.tmp', 'wb')); os.replace(work + '/library.pkl.tmp', work + '/library.pkl')
        pickle.dump(lens, open(work + '/lens.pkl.tmp', 'wb')); os.replace(work + '/lens.pkl.tmp', work + '/lens.pkl')
        open(work + '/grant-ids.txt', 'w').write(''.join(i + '\n' for i in new))
        print('grant variants added', len(new), 'library now', len(lib['mods']))
        return 0
    out = a[1]
    part = tuple(map(int, a[a.index('--part') + 1].split('/'))) if '--part' in a else (0, 1)
    levels = tuple(float(x) for x in a[a.index('--levels') + 1].split(',')) if '--levels' in a else GLEVELS
    lib = Library(work, only=usable)
    need = collections.defaultdict(set)
    for c, v in lib.far.items():
        for F in v:
            if F['g'] > 2e-3: need[c].add(min([g for g in levels if g >= F['g'] - 1e-9] or [levels[-1]]))
    nskip = collections.Counter()
    res = []
    for C in lib.corners[part[0]::part[1]]:
        q = C['q']
        if '^' in q['id']: continue
        base = None
        for arm in (1, 2):
            c = q['c%d' % arm]
            if q.get('offc' if arm == 1 else 'offr') is not None: continue      # a slid twin keeps the grant it was found with
            for g in sorted(need.get(c, ())):
                if g <= q.get('g%d' % arm, 0.0) + 2e-3: continue
                v = dict(q); v['g%d' % arm] = g; v['id'] = '%s^%dg%02d' % (q['id'], arm, round(g * 100))
                if v['id'] in lib.byid: nskip['have'] += 1; continue            # made before (--levels adds finer grants)
                if cells_collide(v): nskip['collide'] += 1; continue           # see cells_collide
                if base is None:
                    base = [corner_len(q, q['f0'], q['P'], q['y0'] + 1e-6, q['x0'] + 1e-6, cost) for cost in COST]
                tab = lib.lens[q['id']]['tab'].copy(); cost_of = []
                for qi, cost in enumerate(COST):
                    r = corner_len(v, q['f0'], q['P'], q['y0'] + 1e-6, q['x0'] + 1e-6, cost)
                    if r is None or base[qi] is None: tab[qi] = np.nan; cost_of.append(None); continue
                    dy, dx = float(r[0] - base[qi][0]), float(r[1] - base[qi][1])
                    tab[qi, 0] += max(dy, 0.0); tab[qi, 1] += max(dx, 0.0); cost_of.append((dy, dx))
                    #   a grant only takes room, so a length that falls is the LP moving along the trade, not the grant:
                    #   the variant's table never goes below the corner's (at its own f a state of the variant dominates it)
                v['grant_cost'] = cost_of
                res.append((v, dict(id=v['id'], own=None, tab=tab)))
                mid = cost_of[len(COST) // 2]
                print(v['id'], 'cost at the smallest sum', 'none' if mid is None else '%+.4f %+.4f' % mid, flush=True)
    pickle.dump(res, open(out + '.tmp', 'wb')); os.replace(out + '.tmp', out)
    print('variants', len(res), 'skipped', dict(nskip))
    return 0


def cmd_loo(a):
    """modules.py loo WORK OUT.tsv [--part I/K]
    Leave one out, the standing control of the generator: for every held layout of the library, take every module of
    that n away (all files, twins too) and let the generator predict the layout's f from the modules of other n."""
    work, out = a[:2]
    part = tuple(map(int, a[a.index('--part') + 1].split('/'))) if '--part' in a else (0, 1)
    lib = Library(work, only=usable)
    corners, far = lib.corners, lib.far
    held = [l for l in lib.layouts if l['tag'] == 'h'][part[0]::part[1]]
    rows = []
    with open(out + '.tmp', 'w') as h:
        h.write('n\tm\tc1\tc2\theld_f\tpredicted_f\tdiff\tcorner\tfar1\tfar2\n')
        for l in held:
            n = l['n']
            lib.corners = [C for C in corners if C['q']['n'] != n]
            lib.far = collections.defaultdict(list, {c: [F for F in v if F['q']['n'] != n] for c, v in far.items()})
            lib._opts = {}
            r = lib.best(n, top=1)
            if not r:
                h.write('%d\t%d\t%d\t%d\t%.6f\t\t\t\t\t\n' % (n, l['m'], l['c1'], l['c2'], l['f'])); continue
            f, stop, C, F1, F2, s1, s2 = r[0]
            rows.append((l['f'], f - l['f']))
            h.write('%d\t%d\t%d\t%d\t%.6f\t%.6f\t%+.6f\t%s\t%s\t%s\n' % (n, l['m'], l['c1'], l['c2'], l['f'], f, f - l['f'], C['id'], F1['id'], F2['id']))
            h.flush()
    os.replace(out + '.tmp', out)
    loo_summary(rows, len(held))
    return 0


def loo_summary(rows, nheld):
    d = np.array([r[1] for r in rows]); f = np.array([r[0] for r in rows])
    if not len(d): print('leave one out: no prediction'); return
    print('leave one out: %d held layouts, %d with a prediction; predicted - held f: median %+.4f, quartiles %+.4f and %+.4f, min %+.4f, max %+.4f' % (
        nheld, len(d), np.median(d), np.percentile(d, 25), np.percentile(d, 75), d.min(), d.max()))
    print('  within 1e-3: %d, 2e-3: %d, 5e-3: %d, 1e-2: %d; held f below 0.8: %d layouts, median %s' % (
        (np.abs(d) <= 1e-3).sum(), (np.abs(d) <= 2e-3).sum(), (np.abs(d) <= 5e-3).sum(), (np.abs(d) <= 1e-2).sum(), (f < 0.8).sum(),
        '%+.4f' % np.median(d[f < 0.8]) if (f < 0.8).any() else 'none'))


def cmd_queue(a):
    """modules.py queue WORK DETAILS.csv OUT.tsv [--top 3] [--slack 0.003] [--need IDS.txt] [--part I/K] [--ns FILE] [--depth D]
    The distinct choices of modules for every n (300 and more, held below the plain grid), one row per choice, with
    the predicted side. Only choices up to --slack of side above held are searched. --need: only choices that hold a
    module of this list. --part I/K: every K-th n from the I-th (to share the work between processes).
    --foreign: only choices whose corner was cut from a layout of another n.
    --depth D: search only from D of side below held up to the slack (Library.window); the rows are the same as
    without it wherever the prediction is inside that window (checked on 5 n: 174 s without, 60 s with D = 0.05).
    --min-margin D: discard predictions below held + D before choosing the top rows (default -0.005, the ranker's
    existing cutoff). Set it to -1 to reproduce the old queue. This prevents unreachable table states from masking
    the next choices, which the ranker could not recover after the queue wrote only its top three."""
    work, details, out = a[:3]
    top = int(a[a.index('--top') + 1]) if '--top' in a else 3
    slack = float(a[a.index('--slack') + 1]) if '--slack' in a else 0.003
    need = set(open(a[a.index('--need') + 1]).read().split()) if '--need' in a else None
    part = tuple(map(int, a[a.index('--part') + 1].split('/'))) if '--part' in a else (0, 1)
    depth = float(a[a.index('--depth') + 1]) if '--depth' in a else None
    min_margin = float(a[a.index('--min-margin') + 1]) if '--min-margin' in a else -0.005
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    lib = Library(work, only=usable)
    ns = [n for n in sorted(held) if n >= 300 and held[n] < math.isqrt(n - 1) + 1 - 1e-9]
    if '--ns' in a:
        want = [int(x) for x in open(a[a.index('--ns') + 1]).read().split()]; ns = [n for n in want if n in held]
    ns = ns[part[0]::part[1]]
    with open(out + '.tmp', 'w') as h:
        h.write('n\tm\theld_side\tpredicted_side\tpredicted_minus_held\tstop\trank\tcorner\tfar1\tfar2\tstacks1\tstacks2\tf\n')
        for q, n in enumerate(ns):
            m = math.isqrt(n - 1)
            for rk, (f, stop, C, F1, F2, s1, s2) in enumerate(lib.best(n, top=top, below=held[n] - m + slack, need=need, distinct=True,
                                                                      foreign='--foreign' in a, depth=depth,
                                                                      above=held[n] - m + min_margin)):
                h.write('%d\t%d\t%.6f\t%.6f\t%+.6f\t%s\t%d\t%s\t%s\t%s\t%d\t%d\t%r\n' % (
                    n, m, held[n], m + f, m + f - held[n], stop, rk + 1, C['id'], F1['id'], F2['id'], s1, s2, f))
            h.flush()
            if q % 25 == 0: print(q, len(ns), n, flush=True)
    os.replace(out + '.tmp', out)
    print('done', len(ns))
    return 0


def _squeeze_family(n, P, fq=None, log=print):
    """The squeeze of family_step.py: its sequential LP turns the arms too, then two fq passes. -> (array, side)"""
    if fq: os.environ['SQ_FQ'] = fq
    import family_step                                   # sets methods_lp.GAP and its LP solver for this process
    Q, L, trace = family_step.squeeze(P, log=None, fq=bool(fq))
    log('n=%d family squeeze: %s' % (n, ', '.join('%s %.9f (%.0f s)' % t for t in trace)))
    import methods_lp
    return methods_lp.normal(Q), L


def cmd_job(a):
    """modules.py job WORK RAWDIR DETAILS.csv NAME N CORNER FAR1 FAR2 S1 S2 F [--fq PATH] [--squeeze slp|family|both]
    Build one choice of modules: the start layout a little above the predicted f, then the squeeze.
    slp: methods_lp.slp, then the fq quench. family: family_step.squeeze. both: the two from the same start, the
    smaller side is kept and both sides are written to the record."""
    import time
    work, raw, details, name, n, ic, i1, i2, s1, s2, f = a[0], a[1], a[2], a[3], int(a[4]), a[5], a[6], a[7], int(a[8]), int(a[9]), float(a[10])
    fq = a[a.index('--fq') + 1] if '--fq' in a else None
    how = a[a.index('--squeeze') + 1] if '--squeeze' in a else 'slp'
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}[n]
    lib = Library(work)
    C, F1, F2 = lib.byid[ic], lib.byid[i1], lib.byid[i2]
    os.makedirs(raw, exist_ok=True); m = math.isqrt(n - 1)
    P = None; why = ''
    for up in (2e-4, 6e-4, 1.5e-3, 3e-3):
        P, why = assemble(lib, n, C, F1, F2, s1, s2, f + up)
        if P is not None:
            side, gap = layout_state(P)
            if gap > -1e-7 and side < m + f + up + 1e-6: break
            why = 'start side %.6f gap %.1e' % (side, gap); P = None
    tagc = '%s+%s+%s' % (ic, i1, i2)
    if P is None:
        print('n=%d %s stacks %d,%d predicted %.6f: no start (%s)' % (n, tagc, s1, s2, m + f, why), flush=True)
        json.dump(dict(n=n, predicted=m + f, held=held, built=None, why=why, stacks=[s1, s2], ids=[ic, i1, i2]), open('%s/%s.nostart' % (raw, name), 'w'))
        return 0
    print('n=%d %s stacks %d,%d predicted %.6f held %.6f start %.6f gap %.1e' % (n, tagc, s1, s2, m + f, held, side, gap), flush=True)
    log = lambda s: print(s, flush=True)
    got = {}; secs = {}
    for h in (('slp', 'family') if how == 'both' else (how,)):       # slp first: family_step changes methods_lp for the process
        t0 = time.time()
        try:
            got[h] = _squeeze(n, P.copy(), fq, log=log) if h == 'slp' else _squeeze_family(n, P.copy(), fq, log=log)
        except Exception as ex:
            log('n=%d %s squeeze failed: %s' % (n, h, ex))
        secs[h] = time.time() - t0
    if not got: return 0
    h = min(got, key=lambda q: got[q][1]); Q, L = got[h]
    write_layout('%s/%s.csv' % (raw, name), n, Q)
    json.dump(dict(n=n, predicted=m + f, start=side, built=L, held=held, stacks=[s1, s2], squeeze=h,
                   sides={q: got[q][1] for q in got}, seconds=secs,
                   modules=[dict(id=x['id'], source=x['q']['src'], licence=x['q']['licence']) for x in (C, F1, F2)]),
              open('%s/%s.json' % (raw, name), 'w'))
    print('n=%d BUILT %s predicted %.6f built %.9f held %.9f (%+.6f) %s' % (
        n, tagc, m + f, L, held, L - held, ' '.join('%s %.9f %.0fs' % (q, got[q][1], secs[q]) for q in got)), flush=True)
    return 0


def cmd_rebuild(a):
    """modules.py rebuild WORK [--rigid] [N ...]   control 1, exact: put every layout together again from its own three
    modules (the slid twins where it has them; --rigid: the modules with the rest on the grid), at its own f plus the
    smallest of 0, 1e-4, 3e-4, 1e-3, 3e-3 that gives a legal layout."""
    global SLIDE
    if '--rigid' in a: SLIDE = False; a = [x for x in a if x != '--rigid']      # the modules as cut, the rest on the grid
    work = a[0]; want = set(map(int, a[1:]))
    lib = pickle.load(open(work + '/library.pkl', 'rb'))
    by = {q['id']: dict(id=q['id'], q=q) for q in lib['mods']}
    res = []
    for l in lib['layouts']:
        if want and l['n'] not in want: continue
        ids = l.get('ids_slide', l['ids']) if SLIDE else l['ids']
        C, F1, F2 = by[ids[2]], by[ids[0]], by[ids[1]]
        got = None; why = ''
        for up in (0.0, 1e-4, 3e-4, 1e-3, 3e-3):
            P, why = assemble(None, l['n'], C, F1, F2, l['s1'], l['s2'], l['f'] + up)
            if P is not None and layout_state(P)[1] > -1e-7:
                got = up; break
        res.append((l['n'], l['tag'], l['f'], got, max(abs(l['err1']), abs(l['err2'])), why or ''))
        print('n=%d%s f %.6f rebuilt at +%s (flush error %.1e) %s' % (l['n'], l['tag'], l['f'], got, res[-1][4], '' if got is not None else why), flush=True)
    with open(work + ('/control1-exact.tsv' if SLIDE else '/control1-rigid.tsv'), 'w') as h:
        h.write('n\ttag\tf\trebuilt_at_plus\tflush_error\n')
        for r in res: h.write('%d\t%s\t%.6f\t%s\t%.2e\n' % r[:5])
    cnt = collections.Counter(r[3] for r in res)
    print('control 1, exact: %d layouts;' % len(res), ', '.join('+%s: %d' % (k, cnt[k]) for k in sorted(cnt, key=lambda v: (v is None, v))))
    bad = [r for r in res if r[3] is None or r[3] > 1e-3]
    print('not within 1e-3: %d; of these with a flush error above 1e-4: %d' % (len(bad), sum(r[4] > 1e-4 for r in bad)))
    return 0


def cmd_export(a):
    """modules.py export WORK OUT.tsv   the library as one table: one row per module, with the lock of a far zone"""
    work, out = a[:2]
    lib = pickle.load(open(work + '/library.pkl', 'rb')); lens = pickle.load(open(work + '/lens.pkl', 'rb'))
    with open(out, 'w') as h:
        h.write('id\tkind\tc\tsignature\tcount\tlength\tlength2\tf\ttilt\tloss\tlock\tf_max\tmissing_rest_cells\tn\tsource\tlicence\n')
        for q in lib['mods']:
            t = lens.get(q['id'], {})
            if q['kind'] == 'far':
                kn = t.get('knots')
                h.write('%s\tfar%d\t%d\t%s\t%d\t%.5f\t\t%.6f\t%.3f\t%.3f\t%s\t%s\t%d\t%d\t%s\t%s\n' % (
                    q['id'], q['arm'], q['c'], q['sig'], q['count'], q['len0'], q['f0'], q['tilt0'], q['loss0'],
                    '' if kn is None else '%.5f' % kn[0][0], '' if kn is None else '%.4f' % kn[0][-1], len(q['miss']), q['n'], q['src'], q['licence']))
            else:
                tab = t.get('tab'); ok = None if tab is None else GRID[~np.isnan(tab[len(COST) // 2, 0])]
                h.write('%s\tcorner\t%dx%d\t%s\t%d\t%.5f\t%.5f\t%.6f\t%.3f/%.3f\t%.3f\t%s\t%s\t%d\t%d\t%s\t%s\n' % (
                    q['id'], q['c1'], q['c2'], q['sig'], q['count'], q['y0'], q['x0'], q['f0'], q['tilt1'], q['tilt2'], q['loss0'],
                    '' if ok is None or not len(ok) else '%.3f' % ok[0], '' if ok is None or not len(ok) else '%.3f' % ok[-1],
                    len(q['miss']), q['n'], q['src'], q['licence']))
    print('wrote', out, len(lib['mods']))
    return 0


def cmd_cover(a):
    """modules.py cover WORK   what the library holds: the lowest loss of a far zone and of a corner by stack size and
    band of f, and for arms of equal stack size the count classes (corner + two far zones, modulo c) it can make."""
    lib = Library(a[0])
    bands = [(lo, lo + 0.04) for lo in np.arange(0.68, 0.999, 0.04)]
    print('far zones: lowest loss usable in the band (number of modules)')
    print('c\t' + '\t'.join('%.2f' % b[0] for b in bands))
    for c in sorted(lib.far):
        cells = []
        for lo, hi in bands:
            sel = (FF >= lo) & (FF < hi); best = None; cnt = 0
            cosf = np.array([c * math.cos(flush_tilt(c, f)) for f in FF[sel]])
            for F in lib.far[c]:
                v = cosf * F['L'][sel] - F['count']
                if np.isfinite(v).any():
                    cnt += 1; best = float(np.nanmin(v)) if best is None else min(best, float(np.nanmin(v)))
            cells.append('-' if best is None else '%.2f (%d)' % (best, cnt))
        print('%d\t' % c + '\t'.join(cells))
    print('corners: lowest loss at the smallest sum of lengths, at the f they were found at')
    by = collections.defaultdict(list)
    for C in lib.corners: by[(C['c1'], C['c2'])].append(C)
    for key in sorted(by):
        print('%dx%d: ' % key + ', '.join('%.3f:%.2f(%d)' % (C['q']['f0'], C['q']['loss0'], C['count'] % max(key)) for C in sorted(by[key], key=lambda C: C['q']['f0'])))
    print('equal arms: count class (corner + two far zones) mod c -> lowest sum of the three losses as found, by band of f')
    for c in (6, 7, 8):
        tab = collections.defaultdict(lambda: None)
        for C in by.get((c, c), []):
            for F1 in lib.far[c]:
                if abs(F1['q']['f0'] - C['q']['f0']) > 0.02: continue
                for F2 in lib.far[c]:
                    if abs(F2['q']['f0'] - C['q']['f0']) > 0.02: continue
                    band = 'f<0.78' if C['q']['f0'] < 0.78 else 'f<0.90' if C['q']['f0'] < 0.90 else 'f>=0.90'
                    key = (band, (C['count'] + F1['count'] + F2['count']) % c)
                    v = C['q']['loss0'] + F1['q']['loss0'] + F2['q']['loss0']
                    if tab[key] is None or v < tab[key]: tab[key] = v
        for band in ('f<0.78', 'f<0.90', 'f>=0.90'):
            print('c=%d %s: ' % (c, band) + ' '.join('%d:%s' % (r, '-' if tab[(band, r)] is None else '%.2f' % tab[(band, r)]) for r in range(c)))
    return 0


if __name__ == '__main__':
    cmds = dict(library=cmd_library, lens=cmd_lens, model=cmd_model, control=cmd_control, predict=cmd_predict, start=cmd_start,
                squeeze=cmd_squeeze, build=cmd_build, take=cmd_take, cover=cmd_cover, rebuild=cmd_rebuild, export=cmd_export,
                grow=cmd_grow, queue=cmd_queue, job=cmd_job, slide=cmd_slide, loo=cmd_loo, grant=cmd_grant, check=cmd_check)
    sys.exit(cmds[sys.argv[1]](sys.argv[2:]) or 0)
