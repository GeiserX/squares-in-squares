#!/usr/bin/env python3
"""gadget lane: exact count models for the designs that absorb k = n - m^2 extra squares into a full grid.

Two families, both counted exactly at a given side (no optimisation inside a count):

  rigid   an a x b block at 45 degrees where four corner grids meet (the structure lane's rule, imported from
          structure_rigid45.pred). Our k = 1 designs are a = 5 (f = 0.535534) and a = 17 (f = 0.520815).
  slot    a horizontal band of tilted columns between two upright bands (Kearney and Shiu 2002, Fig. 6; the
          Hajba and Ellsworth s(1765) packing of 2024 is the same design with better ends). Frame: y grows down
          from the near wall. The near band has `ha` rows hanging from y = 0, the far band `hb` rows standing on
          y = W, W = m + f. The slot between them has height H = m - ha - hb + f. Column i is a 1 x c_i rectangle
          turned by the angle a (its long side goes down and to the left), with its top corner on the line y = ha
          at x = x1 + i sec(a), slid down its own axis by s_i. A full column holds c = h + 1 squares, with
          c cos a + sin a = H. Every grid cell of width 1 holds a stack from each wall. A band's cells are flush
          with the left wall up to its split and flush with the right wall after it, so the gap of f sits at the
          split. A stack goes as deep as the columns allow in its strip, and two stacks that share an x range hold
          at most m squares together (a dynamic programme over the chain of cells).

  The search (`structured`) takes each end on its own: a grid of 0.01 over its position, and every end of the
  family (the outermost 3 columns shortened by d <= dmax, d not rising toward the wall; the left end keeps them
  on the near line, the right end slides them to the far line, as s(1765) does). Then it counts every pair of
  the 3 best ends of both neighbouring grid points exactly, on a grid of 0.002 over x1, for the two largest N.

  gadget.py control                                  the controls: our two rigid designs, s(1765)
  gadget.py scan OUT.jsonl DEADLINE STEP m:f:h[:dmax] ...   largest count of the slot family per job
  gadget.py refine IN.jsonl K OUT.jsonl              smallest f of each design of IN with gain >= K
  gadget.py build DESIGN.jsonl LINE N OUT.csv        the packing of one design (centres, radians, y up)

  Kearney and Shiu's plain slot (rows in the two trapezia) is the special case with no short columns.
"""
import sys, os, math, json, itertools
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
S2 = math.sqrt(2)
EPS = 1e-9


# ---------------------------------------------------------------- rigid 45-degree blocks (structure lane rule)
def rigid_minf(m, k, amax=44):
    """Smallest f at which one rigid a x b block at 45 degrees gives gain >= k and fits at m."""
    from structure_rigid45 import pred
    best = None
    for a in range(1, amax + 1):
        for b in range(a, amax + 1):
            for A in range(max(0, math.ceil(a * S2 - 2)), math.ceil(a * S2) + 1):
                fa = (a * S2 - A) / 2
                if not 0 <= fa < 1: continue
                for B in range(max(0, math.ceil(b * S2 - 2)), math.ceil(b * S2) + 1):
                    fb = (b * S2 - B) / 2
                    if not 0 <= fb < 1: continue
                    f = max(fa, fb)
                    g, A2, B2 = pred(a, b, f + 1e-9)
                    if g >= k and (A2 + B2) / 2 + 2 <= m and (best is None or f < best[0]):
                        best = (f, a, b, g)
    return best


# ---------------------------------------------------------------- the slot model
def theta_of(c, H):
    """Angle a with c cos a + sin a = H on the branch tan a > 1/c (None when no column of c fits)."""
    lo = math.atan(1.0 / c); hi = math.pi / 2
    if c * math.cos(lo) + math.sin(lo) < H - 1e-15: return None
    for _ in range(100):
        mid = (lo + hi) / 2
        if c * math.cos(mid) + math.sin(mid) > H: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def column_poly(x1, ha, a, i, ci, si):
    ca, sa = math.cos(a), math.sin(a)
    px = x1 + i / ca - si * sa; py = ha + si * ca
    ex, ey = ca, sa            # local x
    ux, uy = -sa, ca           # local y (down the column)
    return [(px, py), (px + ex, py + ey), (px + ex + ci * ux, py + ey + ci * uy), (px + ci * ux, py + ci * uy)]


def strip_range(poly, xl, xr):
    """min and max y of a convex polygon inside the open strip xl < x < xr (None when it does not enter)."""
    pts = [p for p in poly if xl < p[0] < xr]
    n = len(poly)
    for k in range(n):
        (x0, y0), (x1, y1) = poly[k], poly[(k + 1) % n]
        if x0 == x1: continue
        for xs in (xl, xr):
            t = (xs - x0) / (x1 - x0)
            if 0 <= t <= 1: pts.append((xs, y0 + t * (y1 - y0)))
    # keep only points whose strip really has area inside the polygon
    if not pts: return None
    xs_ = [p[0] for p in poly]
    if max(xs_) <= xl + 1e-12 or min(xs_) >= xr - 1e-12: return None
    return min(p[1] for p in pts), max(p[1] for p in pts)


def cells(m, f, split):
    """x-left of the m cells of one band: flush left before the split, flush right after it."""
    return [j if j < split else j + f for j in range(m)]


def chain_max(m, near, far):
    """near, far: lists of (xl, cap). Max sum of stacks with near + far <= m where their cells overlap.
    Returns (total, near heights, far heights)."""
    items = sorted([(x, 0, idx) for idx, (x, _) in enumerate(near)] + [(x, 1, idx) for idx, (x, _) in enumerate(far)])
    # the overlap graph is a path in x order
    vals = []
    prev = None; best = None; back = []
    for x, side, idx in items:
        cap = (near if side == 0 else far)[idx][1]
        cap = max(0, min(m, cap))
        if prev is None or abs(x - prev[0]) >= 1 - 1e-12 or prev[1] == side:
            # no constraint with the previous item (no overlap, or same band: different cells never overlap)
            base = 0 if best is None else max(best)
            arg = None if best is None else best.index(max(best))
            nb = [v + base for v in range(cap + 1)]
            back.append(('free', arg, side, idx))
        else:
            # overlap with the previous item: v + w <= m
            pm = []; run = -1; runarg = None
            for v in range(len(best)):
                if best[v] > run: run = best[v]; runarg = v
                pm.append((run, runarg))
            nb = []; args = []
            for w in range(cap + 1):
                lim = min(m - w, len(best) - 1)
                if lim < 0: nb.append(-10 ** 9); args.append(None); continue
                nb.append(pm[lim][0] + w); args.append(pm[lim][1])
            back.append(('tied', args, side, idx))
        prev = (x, side); best = nb
        vals.append(nb)
    # trace back
    total = max(best); v = best.index(total)
    hn = [0] * len(near); hf = [0] * len(far)
    for t in range(len(items) - 1, -1, -1):
        kind, arg, side, idx = back[t]
        (hn if side == 0 else hf)[idx] = v
        if t == 0: break
        if kind == 'free': v = arg
        else: v = arg[v]
    return total, hn, hf


def slot_count(m, f, ha, hb, x1, lens, slides=None, a=None, c=None, splits=None, detail=False):
    """Exact count of one slot design. lens: the length of each column, left to right."""
    W = m + f; h = m - ha - hb; H = h + f
    if c is None: c = h + 1
    if a is None: a = theta_of(c, H)
    if a is None: return None
    slides = slides or [0.0] * len(lens)
    polys = [column_poly(x1, ha, a, i, ci, si) for i, (ci, si) in enumerate(zip(lens, slides)) if ci > 0]
    for P in polys:
        for (x, y) in P:
            if x < -1e-9 or x > W + 1e-9 or y < -1e-9 or y > W + 1e-9: return None
    def caps(xs):
        out_n = []; out_f = []
        for xl in xs:
            lo, hi = W, 0.0
            for P in polys:
                r = strip_range(P, xl + 1e-12, xl + 1 - 1e-12)
                if r is None: continue
                lo = min(lo, r[0]); hi = max(hi, r[1])
            out_n.append(int(math.floor(lo + EPS)))
            out_f.append(int(math.floor(W - hi + EPS)))
        return out_n, out_f
    best = None
    cand = splits if splits is not None else [(sa_, sb_) for sa_ in range(m + 1) for sb_ in range(m + 1)]
    cache = {}
    for sa_, sb_ in cand:
        xa = cells(m, f, sa_); xb = cells(m, f, sb_)
        if sa_ not in cache: cache[sa_] = caps(xa)
        if ('b', sb_) not in cache: cache[('b', sb_)] = caps(xb)
        capn = cache[sa_][0]; capf = cache[('b', sb_)][1]
        tot, hn, hf = chain_max(m, list(zip(xa, capn)), list(zip(xb, capf)))
        if best is None or tot > best[0]: best = (tot, sa_, sb_, hn, hf)
    tilted = sum(lens)
    if detail: return tilted + best[0], best, a
    return tilted + best[0]


# ---------------------------------------------------------------- fast exact count and the end search
def chain_fast(m, near, far):
    """Same value as chain_max, faster: only runs of binding overlaps (caps summing above m) need the DP."""
    items = sorted([(x, 0, cap) for x, cap in near] + [(x, 1, cap) for x, cap in far])
    caps = [max(0, min(m, it[2])) for it in items]
    total = 0; run = [caps[0]]
    for i in range(1, len(items)):
        tied = items[i][1] != items[i - 1][1] and abs(items[i][0] - items[i - 1][0]) < 1 - 1e-12 and caps[i] + caps[i - 1] > m
        if tied: run.append(caps[i]); continue
        total += _path_max(m, run); run = [caps[i]]
    return total + _path_max(m, run)


def _path_max(m, run):
    if len(run) == 1: return run[0]
    best = list(range(run[0] + 1))
    for cap in run[1:]:
        pm = []; r = -1
        for v in best:
            r = v if v > r else r; pm.append(r)
        best = [pm[min(m - w, len(pm) - 1)] + w if m - w >= 0 else -10 ** 9 for w in range(cap + 1)]
    return max(best)


class Slot:
    """One slot frame (m, f, h, c): the angle, and the caps of all cells for a set of columns."""
    def __init__(s, m, f, h, c=None, ha=None):
        s.m, s.f, s.h = m, f, h; s.W = m + f; s.H = h + f
        s.c = c if c is not None else h + 1
        s.a = theta_of(s.c, s.H)
        s.ha = ha if ha is not None else (m - h) // 2; s.hb = m - h - s.ha
        if s.a is not None:
            s.ca, s.sa = math.cos(s.a), math.sin(s.a); s.sec = 1 / s.ca
        R = min(7, m // 2)
        s.splits = sorted(set(list(range(0, R + 1)) + list(range(m - R, m + 1)) + [m // 2]))

    def polys(s, x1, lens, slides):
        out = []
        for i, (ci, si) in enumerate(zip(lens, slides)):
            if ci <= 0: continue
            P = column_poly(x1, s.ha, s.a, i, ci, si)
            for (x, y) in P:
                if x < -1e-9 or x > s.W + 1e-9 or y < -1e-9 or y > s.W + 1e-9: return None
            out.append((min(p[0] for p in P), max(p[0] for p in P), P))
        return out

    def count(s, x1, lens, slides, detail=False):
        if s.a is None: return None
        PP = s.polys(x1, lens, slides)
        if PP is None: return None
        m, f, W = s.m, s.f, s.W
        def capat(xl):
            lo, hi = W, 0.0
            for x0, x1_, P in PP:
                if x1_ <= xl + 1e-12 or x0 >= xl + 1 - 1e-12: continue
                r = strip_range(P, xl + 1e-12, xl + 1 - 1e-12)
                if r is None: continue
                lo = min(lo, r[0]); hi = max(hi, r[1])
            return int(math.floor(lo + EPS)), int(math.floor(W - hi + EPS))
        cL = [capat(j) for j in range(m)]; cS = [capat(j + f) for j in range(m)]
        if not detail:
            return sum(lens) + s._splits_fast(cL, cS)
        best = None
        for sn in s.splits:
            nl = [(j, cL[j][0]) if j < sn else (j + f, cS[j][0]) for j in range(m)]
            for sf in s.splits:
                fl = [(j, cL[j][1]) if j < sf else (j + f, cS[j][1]) for j in range(m)]
                t = chain_fast(m, nl, fl)
                if best is None or t > best[0]: best = (t, sn, sf)
        tot = sum(lens) + best[0]
        if not detail: return tot
        nl = [(j, cL[j][0]) if j < best[1] else (j + f, cS[j][0]) for j in range(m)]
        fl = [(j, cL[j][1]) if j < best[2] else (j + f, cS[j][1]) for j in range(m)]
        t, hn, hf = chain_max(m, nl, fl)
        assert t == best[0], (t, best)
        return tot, best[1], best[2], hn, hf

    def _splits_fast(s, cL, cS):
        m, f = s.m, s.f
        # cells that may sit in a binding pair (near + far > m for some modes of overlapping cells)
        hot = set()
        for j in range(m):
            an = max(cL[j][0], cS[j][0])
            for jj in (j - 1, j, j + 1):
                if 0 <= jj < m and an + max(cL[jj][1], cS[jj][1]) > m: hot.add(j); hot.add(jj)
        hot = sorted(hot)
        pnL = [0]; pnS = [0]; pfL = [0]; pfS = [0]
        for j in range(m):
            w = 0 if j in hot else 1
            pnL.append(pnL[-1] + w * cL[j][0]); pnS.append(pnS[-1] + w * cS[j][0])
            pfL.append(pfL[-1] + w * cL[j][1]); pfS.append(pfS[-1] + w * cS[j][1])
        best = None
        for sn in s.splits:
            cold_n = pnL[sn] + (pnS[m] - pnS[sn])
            nl = [(j, cL[j][0]) if j < sn else (j + f, cS[j][0]) for j in hot]
            for sf in s.splits:
                cold_f = pfL[sf] + (pfS[m] - pfS[sf])
                if hot:
                    fl = [(j, cL[j][1]) if j < sf else (j + f, cS[j][1]) for j in hot]
                    t = chain_fast(m, nl, fl)
                else: t = 0
                t += cold_n + cold_f
                if best is None or t > best: best = t
        return best

    def xmin(s, c0, s0):
        # leftmost corner of column 0 at x1: x1 - s0*sa - c0*sa (the down-left corner)
        return (s0 + c0) * s.sa

    def design(s, x1, left, right, N):
        """left/right: lists of (d, slide) for the outermost columns, outermost first."""
        lens = [s.c] * N; slides = [0.0] * N
        for i, (d, sl) in enumerate(left):
            if i < N: lens[i] = s.c - d; slides[i] = sl
        for i, (d, sl) in enumerate(right):
            j = N - 1 - i
            if j >= len(left): lens[j] = s.c - d; slides[j] = sl
        return lens, slides


def end_configs(P=3, dmax=5):
    """Outermost-first (d, slide) lists: lengths c - d with d non-increasing inward, all near- or all far-anchored."""
    out = []
    for ds in itertools.combinations_with_replacement(range(dmax + 1), P):
        ds = sorted(ds, reverse=True)
        out.append([(d, 0.0) for d in ds])
        if any(ds): out.append([(d, float(d)) for d in ds])
    return out


def nmax(S, x1, L, Rr):
    """Largest N whose design fits in the box (all corners inside)."""
    N = int((S.W - x1) / S.sec) + 2
    while N > len(L):
        lens, slides = S.design(x1, L, Rr, N)
        if S.polys(x1, lens, slides) is not None: return N
        N -= 1
    return None


def structured(m, f, h, k, step=0.02, P=3, dmax=4, c=None, top=10, exact=40):
    """Each end on its own: a grid over its position and every end configuration of the family, scored as the
    change against full columns there. Then every (x1, N) with the best ends of both sides, ranked by the sum of
    the two changes, and the best `exact` of them counted exactly."""
    S = Slot(m, f, h, c)
    if S.a is None: return None
    full = [(0, 0.0)] * P
    cfgs = [L for L in end_configs(P, dmax) if any(d for d, _ in L)]
    # the left end keeps its short columns on the near line, the right end slides them to the far line (s(1765))
    cfgL = [L for L in cfgs if all(sl == 0 for _, sl in L)]
    cfgR = [L for L in cfgs if all(sl == d for d, sl in L)]
    allsp = S.splits
    def cnt(x1, L, Rr, N):
        lens, slides = S.design(x1, L, Rr, N)
        return S.count(x1, lens, slides)
    lo = (S.c - dmax) * S.sa
    xs = [lo + i * step for i in range(int((S.c * S.sa + 1.6 - lo) / step))]
    left = {}
    S.splits = sorted(set(list(range(0, 9)) + [m // 2]))
    for x1 in xs:
        res = []
        N = nmax(S, x1, full, full)
        base = cnt(x1, full, full, N) if N else None
        for L in cfgL:
            N2 = nmax(S, x1, L, full)
            if N2 is None: continue
            n = cnt(x1, L, full, N2)
            if n is None: continue
            res.append((n - (base if (base is not None and N2 == N) else -10 ** 6), L))
        if base is not None: res.append((0, full))
        res.sort(key=lambda r: -r[0]); left[x1] = res[:top]
    right = {}
    S.splits = sorted(set(list(range(m - 8, m + 1)) + [m // 2]))
    us = [S.ca + i * step for i in range(int((S.c * S.sa + 2.0) / step))]
    for u in us:
        xl = S.W - u
        N = int((xl - (S.c * S.sa + 0.5)) / S.sec) + 1
        x1 = xl - (N - 1) * S.sec
        base = cnt(x1, full, full, N)
        res = [(0, full)] if base is not None else []
        for Rr in cfgR:
            n = cnt(x1, full, Rr, N)
            if n is None: continue
            res.append((n - (base if base is not None else -10 ** 6), Rr))
        res.sort(key=lambda r: -r[0]); right[u] = res[:top]
    S.splits = allsp
    # combine on a finer grid: each end's table at the grid point just below (more room is never worse for it)
    best = None; fine = step / 5; ntry = 0
    xf = [lo + i * fine for i in range(int((xs[-1] - lo) / fine) + 1)]
    for x1 in xf:
        ig = int((x1 - lo) / step + 1e-9)
        Ls = []
        for g in xs[max(0, ig):ig + 2]:
            for _, L in left.get(g, [])[:3]:
                if L not in Ls: Ls.append(L)
        if not Ls: continue
        Nm = int((S.W - x1) / S.sec) + 1
        for N in range(Nm, Nm - 2, -1):
            u = S.W - (x1 + (N - 1) * S.sec)
            iu = int((u - us[0]) / step + 1e-9)
            Rs = []
            for v in us[max(0, iu):iu + 2]:
                for _, Rr in right.get(v, [])[:3]:
                    if Rr not in Rs: Rs.append(Rr)
            for L in Ls:
                for Rr in Rs:
                    n = cnt(x1, L, Rr, N); ntry += 1
                    if n is not None and (best is None or n > best[0]): best = (n, x1, N, L, Rr)
    if best is None: return None
    n, x1, N, L, Rr = best
    lens, slides = S.design(x1, L, Rr, N)
    return {'m': m, 'f': f, 'h': h, 'c': S.c, 'k': k, 'count': n, 'gain': n - m * m, 'ok': n >= m * m + k,
            'x1': x1, 'N': N, 'L': L, 'R': Rr, 'lens': lens, 'slides': slides, 'ha': S.ha, 'hb': S.hb,
            'a_deg': math.degrees(S.a)}


def fits(m, f, h, c, k, lens, slides, x1s):
    S = Slot(m, f, h, c)
    if S.a is None: return None
    for x1 in x1s:
        n = S.count(x1, lens, slides)
        if n is not None and n >= m * m + k: return x1
    return None


def refine(d, k, flo=None, iters=24, span=0.1, step=0.0005):
    """Smallest f at which the design's columns (lengths, slides) still give m^2 + k, x1 re-placed each time."""
    m, h, c, lens, slides = d['m'], d['h'], d['c'], d['lens'], d['slides']
    hi = d['f']; x1 = d['x1']
    lo = flo if flo is not None else hi - 0.03
    if fits(m, hi, h, c, k, lens, slides, [x1]) is None: return None
    for _ in range(iters):
        mid = (lo + hi) / 2
        xs = sorted([x1 + (i - int(span / step)) * step for i in range(2 * int(span / step) + 1)], key=lambda v: abs(v - x1))
        got = fits(m, mid, h, c, k, lens, slides, xs)
        if got is not None: hi, x1 = mid, got
        else: lo = mid
    out = dict(d); out['f'] = hi; out['x1'] = x1
    S = Slot(m, hi, h, c); out['count'] = S.count(x1, lens, slides); out['a_deg'] = math.degrees(S.a)
    return out


def layout(d):
    """Squares (cx, cy, angle in radians) in the metric's frame (y up) for a design dict."""
    m, f, h, c = d['m'], d['f'], d['h'], d['c']
    S = Slot(m, f, h, c, ha=d.get('ha'))
    tot, sn, sf, hn, hf = S.count(d['x1'], d['lens'], d['slides'], detail=True)
    W = S.W; out = []
    ca, sa = S.ca, S.sa
    for i, (ci, si) in enumerate(zip(d['lens'], d['slides'])):
        px = d['x1'] + i / ca - si * sa; py = S.ha + si * ca
        for r in range(ci):
            cx = px + 0.5 * ca + (r + 0.5) * (-sa); cy = py + 0.5 * sa + (r + 0.5) * ca
            out.append((cx, W - cy, -S.a))
    for xl, dd in zip(cells(m, f, sn), hn):
        for r in range(dd): out.append((xl + 0.5, W - (r + 0.5), 0.0))
    for xl, e in zip(cells(m, f, sf), hf):
        for r in range(e): out.append((xl + 0.5, r + 0.5, 0.0))
    assert len(out) == tot
    return out, W


def write_csv(path, n, rows):
    import csv as _csv
    keep = sorted(rows, key=lambda r: (r[2] == 0.0,))[:n] if len(rows) > n else rows
    with open(path, 'w', newline='') as g:
        w = _csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for i, (x, y, t) in enumerate(keep): w.writerow([n, i, repr(x), repr(y), repr(t)])


# ---------------------------------------------------------------- controls
def control():
    rows = []
    for m, k in ((20, 1), (25, 1)):
        r = rigid_minf(m, k)
        rows.append({'control': 'rigid', 'm': m, 'k': k, 'f': r[0], 'a': r[1], 'b': r[2]})
    # Kearney and Shiu, m = 43: 28 + 15 rows, 36 columns of 16, plain trapezia -> 1850 at f = 0.5
    print(json.dumps(rows[0])); print(json.dumps(rows[1]))
    m = 42; W = 42.487978511860220940053587829982661; f = W - m
    a = math.radians(18.534719606457512215425149621112193)
    lens = [12, 13, 15] + [16] * 30 + [15, 14, 13]
    slides = [0.0] * 33 + [1.0, 2.0, 3.14773352187322466139228761244842092]
    x1 = 1 + 11 * math.tan(a)
    n, best, a2 = slot_count(m, f, 14, 13, x1, lens, slides, a=a, c=16, splits=[(4, 37)], detail=True)
    print(json.dumps({'control': 's1765', 'm': m, 'f': f, 'count': n, 'want': 1765, 'split': best[1:3]}))
    n2, best2, _ = slot_count(m, f, 14, 13, x1, lens, slides, a=a, c=16, detail=True)
    n3 = slot_count(m, f - 1e-6, 14, 13, x1, lens, slides, a=a, c=16)
    print(json.dumps({'control': 's1765 at f - 1e-6 (must fail or drop)', 'count': n3}))
    print(json.dumps({'control': 's1765 free splits', 'count': n2, 'split': best2[1:3]}))
    # Kearney and Shiu, m = 43, f = 1/2: 36 full columns of 16, no short column -> 1850 = 43^2 + 1
    S = Slot(43, 0.5, 15, 16); got = None
    for i in range(800):
        x1 = S.c * S.sa + i * 0.002; n = S.count(x1, [16] * 36, [0.0] * 36)
        if n is not None and (got is None or n > got[0]): got = (n, x1)
    print(json.dumps({'control': 'Kearney-Shiu m = 43, f = 0.5', 'count': got[0], 'want': 1850, 'x1': got[1]}))
    return rows


def main():
    cmd = sys.argv[1]
    if cmd == 'control':
        control(); return
    if cmd == 'scan':
        # gadget.py scan OUT.jsonl DEADLINE_EPOCH STEP m:f:h ...   (max count of the slot family at each job)
        import time
        out, dl, step = sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
        for job in sys.argv[5:]:
            if time.time() > dl: print('deadline', flush=True); break
            parts = job.split(':'); m = int(parts[0]); f = float(parts[1]); h = int(parts[2])
            dmax = int(parts[3]) if len(parts) > 3 else 4
            t = time.time(); r = structured(m, f, h, 1, step=step, dmax=dmax)
            rec = {'m': m, 'f': f, 'h': h, 'dmax': dmax, 'step': step, 'secs': round(time.time() - t)}
            if r: rec.update({x: r[x] for x in ('c', 'count', 'gain', 'x1', 'N', 'L', 'R', 'ha', 'hb', 'a_deg', 'lens', 'slides')})
            with open(out, 'a') as g: g.write(json.dumps(rec) + '\n')
            print(json.dumps({x: rec.get(x) for x in ('m', 'f', 'h', 'gain', 'N', 'L', 'R', 'secs')}), flush=True)
        return
    if cmd == 'refine':
        # gadget.py refine IN.jsonl K OUT.jsonl : smallest f for each design of IN with gain >= K
        inp, k, out = sys.argv[2], int(sys.argv[3]), sys.argv[4]
        for line in open(inp):
            d = json.loads(line)
            if d.get('gain', -9) < k: continue
            r = refine(d, k)
            if r is None: continue
            with open(out, 'a') as g: g.write(json.dumps(dict(r, k=k)) + '\n')
            print(json.dumps({x: r[x] for x in ('m', 'h', 'f', 'count', 'x1')}), flush=True)
        return
    if cmd == 'build':
        # gadget.py build DESIGN.jsonl LINE N OUT.csv : write the packing of one design (n squares, radians)
        d = json.loads(open(sys.argv[2]).read().splitlines()[int(sys.argv[3])])
        rows, W = layout(d); write_csv(sys.argv[5], int(sys.argv[4]), rows)
        print(json.dumps({'n': int(sys.argv[4]), 'rows': len(rows), 'side': W}))
        return
    raise SystemExit(__doc__)


if __name__ == '__main__':
    main()
