"""Outline search for a turned block (avenues/k123.md, section 5).

For each outline (a set of grid sites) the block is placed turned by phi, in its slid form and shrunk by --shrink, on a
grid of positions (--pos lo,hi,step). The uprights come from Evan Daniel's exact refill (fillfast, MIT, imported from
his clone through EVAND_PACKER), on the four wall lattices only. Each hole that holds N squares goes to the tartan LP
(k123_tartan.Hole.fit), which gives the smallest side for that hole. One json line per outline.

Outlines:
  default   the rectangle, and one jog in the rows or in the columns (rows up to r0 moved one column; x1/x2: one long row)
  --double  one jog in the rows and one in the columns, concave corners empty or all filled
  --dj2     the same, each jog with its long line
  --dj3     two jogs in each direction, each with its long line, gaps from --gaps
  --rj      jogs in the rows only: 0 to --nj long rows, gaps from --gaps
  --short   the rectangle with one or two rows one square short at an end (--nj 1 or 2)

usage: k123_outline.py HELD.csv N OUT.jsonl PART NPART [--rect AxB] [--phis deg,...] [--pos=-0.5,0.5,0.1]
           [--shrink 0.02] [--maxfit 8] [--target COUNT|auto] [--centre] [--ss x --sr x] [--write DIR --keep 0.0]
  --centre  the held layout is no single block: only its side is used, and the block goes to the middle of the box
  --write   save a layout whose side is below the held side plus --keep (the Kaggle row layout of family_step)
Control: k123_outline.py HELD.csv 261 out.jsonl 0 1 --rect 13x8 --rj --nj 1   gives 16.678779875 for "rj 2" and "rj 5"."""
import sys, os, math, json, time, argparse
HERE = os.path.dirname(os.path.abspath(sys.argv[0]))
for d in (HERE + '/lane', HERE):                 # on a box the lane tools sit in ./lane
    if os.path.isdir(d): sys.path.insert(0, d); break
import numpy as np
import k123_tartan as kt
import k123_block as kb
import methods_lp as mlp
import fillfast
_cand = fillfast.candidates
fillfast.candidates = lambda s_, T_, tau=0.0, reach=0: _cand(s_, T_, tau, 0)      # wall lattices only: no upright pushed against the block

ap = argparse.ArgumentParser()
ap.add_argument('held'); ap.add_argument('n', type=int); ap.add_argument('out'); ap.add_argument('part', type=int); ap.add_argument('npart', type=int)
ap.add_argument('--phis', default=''); ap.add_argument('--tau', type=float, default=0.12); ap.add_argument('--rect', default='')
ap.add_argument('--dl', type=float, default=0.0); ap.add_argument('--shrink', type=float, default=0.03); ap.add_argument('--pos', default='-0.4,0.4,0.2'); ap.add_argument('--extras', default='0,1,2'); ap.add_argument('--write', default=''); ap.add_argument('--only', default=''); ap.add_argument('--double', action='store_true'); ap.add_argument('--dj2', action='store_true'); ap.add_argument('--dj3', action='store_true'); ap.add_argument('--rj', action='store_true'); ap.add_argument('--short', action='store_true'); ap.add_argument('--centre', action='store_true'); ap.add_argument('--ss', type=float, default=1.0); ap.add_argument('--sr', type=float, default=1.0); ap.add_argument('--nj', type=int, default=3); ap.add_argument('--gaps', default='5,6,7'); ap.add_argument('--dj3d', default='-1'); ap.add_argument('--target', default=''); ap.add_argument('--djd', default='1'); ap.add_argument('--djone', default=''); ap.add_argument('--maxfit', type=int, default=4); ap.add_argument('--keep', type=float, default=0.002)
a = ap.parse_args()
P = kt.load(a.held, a.n)
try:
    H0 = kt.Hole(P)
except Exception as ex:                       # a held layout that is no single block: only its side is used
    H0 = None
n = a.n
if H0 is None or a.centre:
    hh = (np.abs(np.cos(P[:, 2])) + np.abs(np.sin(P[:, 2]))) / 2
    Lh = float(max((P[:, 0] + hh).max() - (P[:, 0] - hh).min(), (P[:, 1] + hh).max() - (P[:, 1] - hh).min()))
    class _H: pass
    H0 = _H(); H0.L = Lh; H0.a = H0.b = 0; H0.sites = []; H0.t0 = 0.0; H0.T = np.array([[Lh / 2, Lh / 2, 0.0]])
Lh = H0.L; Lr = Lh + a.dl
if a.rect:
    A, B = (int(x) for x in a.rect.split('x'))
else:
    A, B = H0.a, H0.b
print('n %d held %.9f block %d x %d (%d sites) at %.3f deg; search rect %d x %d' % (n, Lh, H0.a, H0.b, len(H0.sites), math.degrees(H0.t0), A, B), flush=True)
t45 = math.pi / 4

EXTRAS = [int(x) for x in a.extras.split(',')]
DJ_D = [int(x) for x in a.djd.split(',')]
GAPS = [int(x) for x in a.gaps.split(',')]
NJ = a.nj
DJ3_D = [int(x) for x in a.dj3d.split(',')]
DJ_ONE = [int(x) for x in a.djone.split(',')] if a.djone else []

def variants():
    V = [('rect', [(i, j) for j in range(B) for i in range(A)])]
    for r0 in range(0, B - 1):
        for d in (1, -1):
            for extra in EXTRAS:
                # rows 0..r0 moved d columns; row r0+1 covers both ranges when extra=1; extra=2: row r0 covers both
                S = []
                for j in range(B):
                    if j <= r0: rng = range(d, A + d)
                    else: rng = range(0, A)
                    if (extra == 1 and j == r0 + 1) or (extra == 2 and j == r0): rng = range(min(0, d), A + max(0, d))
                    S += [(i, j) for i in rng]
                V.append(('rows<=%d%+d x%d' % (r0, d, extra), S))
    for c0 in range(0, A - 1):
        for d in (1, -1):
            for extra in EXTRAS:
                S = []
                for i in range(A):
                    if i <= c0: rng = range(d, B + d)
                    else: rng = range(0, B)
                    if (extra == 1 and i == c0 + 1) or (extra == 2 and i == c0): rng = range(min(0, d), B + max(0, d))
                    S += [(i, j) for j in rng]
                V.append(('cols<=%d%+d x%d' % (c0, d, extra), S))
    return V


def corners(S):
    """Empty sites with a neighbour along i and a neighbour along j in the set (the concave corners of the outline)."""
    S = set(S); out = set()
    for (i, j) in S:
        for e in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if e in S or e in out:
                continue
            h = ((e[0] + 1, e[1]) in S) or ((e[0] - 1, e[1]) in S); v = ((e[0], e[1] + 1) in S) or ((e[0], e[1] - 1) in S)
            if h and v:
                out.add(e)
    return sorted(out)


def double_variants():
    """One jog in the rows and one in the columns."""
    V = []
    for r0 in range(0, B - 1):
        for c0 in range(0, A - 1):
            for d in DJ_D:
                for d2 in (1, -1):
                    base = []
                    for j in range(B):
                        for i in (range(d, A + d) if j <= r0 else range(0, A)):
                            base.append((i, j + d2) if i <= c0 else (i, j))
                    base = sorted(set(base))
                    cs = corners(base)
                    V.append(('dj r%d%+d c%d%+d none' % (r0, d, c0, d2), base))
                    V.append(('dj r%d%+d c%d%+d all%d' % (r0, d, c0, d2, len(cs)), base + cs))
                    for q, e in enumerate(cs):
                        if q in DJ_ONE:
                            V.append(('dj r%d%+d c%d%+d one%d' % (r0, d, c0, d2, q), base + [e]))
    return V


def dj2_variants():
    """One jog in the rows and one in the columns, each with its long line (the form that rebuilds 261 in one direction)."""
    V = []
    for r0 in range(0, B - 1):
        base = []
        for j in range(B):
            rng = range(1, A + 1) if j <= r0 else range(0, A)
            if j == r0 + 1: rng = range(0, A + 1)
            base += [(i, j) for i in rng]
        for c0 in range(0, A):
            for d2 in (1, -1):
                S = set()
                for (i, j) in base:
                    S.add((i, j + d2) if i <= c0 else (i, j))
                    if i == c0 + 1: S.add((i, j + d2))
                V.append(('dj2 r%d c%d%+d' % (r0, c0, d2), sorted(S)))
    return V


def dj3_variants():
    """Two jogs in the rows and two in the columns, each with its long line. Long rows at p1 < p2, long columns at
    q1 < q2, spacing from --gaps. Rows below a long row sit one column further; columns left of a long column sit one
    row lower (the 90 degree turn of the row rule)."""
    V = []
    for g1 in GAPS:
        for p1 in range(1, B - g1):
            p2 = p1 + g1
            base = []
            for j in range(B):
                lo, hi = (2, A + 2) if j < p1 else (1, A + 2) if j == p1 else (1, A + 1) if j < p2 else (0, A + 1) if j == p2 else (0, A)
                base += [(i, j) for i in range(lo, hi)]
            for g2 in GAPS:
                for q1 in range(1, A + 1 - g2):
                    q2 = q1 + g2
                    for d2 in DJ3_D:
                        S = set()
                        for (i, j) in base:
                            sh = (2,) if i < q1 else (2, 1) if i == q1 else (1,) if i < q2 else (1, 0) if i == q2 else (0,)
                            for k in sh:
                                S.add((i, j + k * d2))
                        V.append(('dj3 p%d,%d q%d,%d %+d' % (p1, p2, q1, q2, d2), sorted(S)))
    return V


def rj_variants():
    """Jogs in the rows only: long rows at p1 < p2 < ..., gaps from --gaps, 0 to --nj jogs. Rows below a long row sit
    one column further (the hand that rebuilds 261 at a positive turn)."""
    V = []
    def rec(ps):
        k = len(ps)
        base = []
        for j in range(B):
            below = sum(1 for q in ps if j < q)            # long rows above this row
            lo = below; hi = A + below
            if j in ps: hi += 1
            base += [(i, j) for i in range(lo, hi)]
        V.append(('rj ' + ','.join(str(q) for q in ps) if ps else 'rj none', base))
        if k < NJ:
            for g in (GAPS if ps else range(1, max(GAPS) + 1)):
                q = (ps[-1] + g) if ps else g
                if q < B:
                    rec(ps + [q])
    rec([])
    return V


def short_variants():
    """The rectangle with one or two rows one square short at an end (the held 332 has one such row). --nj 1 or 2."""
    V = []
    full = [(i, j) for j in range(B) for i in range(A)]
    ends = [(e, p) for p in range(B) for e in (0, A - 1)]
    for k, x in enumerate(ends):
        V.append(('short %d%s' % (x[1], 'L' if x[0] == 0 else 'R'), [q for q in full if q != x]))
        if NJ >= 2:
            for y in ends[k + 1:]:
                if y[1] - x[1] in GAPS:
                    V.append(('short %d%s,%d%s' % (x[1], 'L' if x[0] == 0 else 'R', y[1], 'L' if y[0] == 0 else 'R'), [q for q in full if q != x and q != y]))
    return V


def snap(U, C, L):
    """Uprights that the fill pushed against the block go back to the wall lattice on their side of the block;
    then any two that overlap lose one."""
    for k in range(len(U)):
        for ax in (0, 1):
            lo = U[k, ax] - 0.5; hi = L - U[k, ax] - 0.5
            if min(abs(lo - round(lo)), abs(hi - round(hi))) < 1e-7:
                continue
            o = 1 - ax
            near = C[np.abs(C[:, o] - U[k, o]) < 1.3]
            ref = near[:, ax].mean() if len(near) else C[:, ax].mean()
            U[k, ax] = math.floor(lo + 1e-9) + 0.5 if U[k, ax] < ref else L - 0.5 - math.floor(hi + 1e-9)
    keep = []
    for k in range(len(U)):
        if all(max(abs(U[k, 0] - U[l, 0]), abs(U[k, 1] - U[l, 1])) > 1 - 1e-9 for l in keep):
            keep.append(k)
    return U[keep]

if a.phis:
    phis = [math.radians(float(x)) for x in a.phis.split(',')]
else:
    p = math.asin(1 / (kt.R2 * max(A, B)))
    phis = [p, -p]
jobs = [(name, S, phi) for name, S in (short_variants() if a.short else rj_variants() if a.rj else dj3_variants() if a.dj3 else dj2_variants() if a.dj2 else double_variants() if a.double else variants()) for phi in phis]
if a.only:
    jobs = [j for j in jobs if j[0] == a.only]
jobs = jobs[a.part::a.npart]
out = open(a.out, 'a')
best = None
# the centre of the held block in the box
cen = H0.T[:, :2].mean(0) + a.dl / 2
p0, p1, dp = (float(x) for x in a.pos.split(','))
grid = np.arange(p0, p1 + 1e-9, dp)
for name, S, phi in jobs:
    t0 = time.time()
    S = np.array(S)
    t = t45 + phi
    Hs = kt.Hole.parts(Lh, np.zeros((0, 2)), S, t, cen, n)
    S0, R0 = Hs.start(phi, 'uniform')
    S0 = S0 * a.ss; R0 = R0 * a.sr                      # the share of the row slide and of the column slip in the start
    C0 = Hs.centres(t, cen, S0, R0)
    C0 += cen - C0.mean(0)
    res = dict(n=n, name=name, phi=round(math.degrees(phi), 4), tilted=len(C0))
    top = 0; hits = []
    for dx in grid:
        for dy in grid:
            C = C0 + np.array([dx, dy])
            T = np.c_[C, np.full(len(C), t)]
            Tr = T.copy(); Tr[:, :2] = C.mean(0) + (C - C.mean(0)) * (1 - a.shrink)
            try:
                F = kb.refill(Lr, Tr, a.tau)
            except Exception as ex:
                continue
            U = snap(F[len(T):, :2].copy(), C, Lr); cnt = len(T) + len(U)
            top = max(top, cnt)
            hits.append((cnt, float(dx), float(dy), U.copy(), C))
    tgt = n if not a.target else (top if a.target == 'auto' else int(a.target))
    hits = [h for h in hits if h[0] >= tgt]
    hits.sort(key=lambda h: h[0]); res['count'] = top; res['hits'] = len(hits)
    Lb = None
    for cnt, dx, dy, U, C in hits[:a.maxfit]:
        if cnt > tgt:
            d = np.abs(U - C.mean(0)).max(1); U = U[np.argsort(d)[:tgt - len(C)]]
        H = kt.Hole.parts(Lr, U, S, t, C.mean(0), n)
        ic, jc = (H.a - 1) / 2, (H.b - 1) / 2
        u = np.array([math.cos(t), math.sin(t)]); v = np.array([-u[1], u[0]])
        I = H.sites
        H.c0 = (C - np.outer(I[:, 0] - ic + S0[I[:, 1]], u) - np.outer(I[:, 1] - jc + R0[I[:, 0]], v)).mean(0)
        H.t0 = t
        for mode, cr, cs in [('scaled', 0, 0), ('uniform', 0, 0), ('teeth', 0, 0)]:
            if mode == 'scaled':
                if a.ss == 1.0 and a.sr == 1.0:
                    continue
                S1, R1 = S0.copy(), R0.copy()
            else:
                S1, R1 = H.start(phi, mode, cr, cs)
            L, O, S2, R2, tt = H.fit(0.0, S1, R1)
            if not np.isfinite(L):
                continue
            X = H.layout(tt, O, S2, R2, L + 2e-9)
            g = float(mlp.min_gap(X))
            if g > -1e-9 and (Lb is None or L < Lb[0]):
                Lb = (L, X, dx, dy, cnt)
    if Lb is not None:
        L, X, dx, dy, cnt = Lb
        res.update(L=round(float(L), 9), dL=round(float(L - Lh), 6), dx=dx, dy=dy)
        if a.write and L < Lh + a.keep:
            import family_step as fs
            os.makedirs(a.write, exist_ok=True)
            fs.write_rows('%s/%d-%s-%+.3f.csv' % (a.write, n, name.replace(' ', '_').replace('<=', 'le'), math.degrees(phi)), n, X)
        if best is None or L < best[0]:
            best = (float(L), name, math.degrees(phi))
    res['sec'] = round(time.time() - t0, 1)
    out.write(json.dumps(res) + '\n'); out.flush()
    print(res, flush=True)
print('best', best, flush=True)
