#!/usr/bin/env python3
"""A reader for the family step that takes arms the readers of family_step.py refuse.

family_step.py reads an arm by its stacks: chains of squares set face to face, two neighbours of one
size and one tilt. It refuses an arm whose stacks are sheared or hold several tilts (the chain breaks),
and an arm whose strip holds one square more than its stacks (a stack plus an odd square at the wall,
or border lines). This reader does not ask for stacks. It asks for a cut.

  A cut window is a straight band of width 1 across a strip, along the row axis of one tilted square of
  the strip. The layer of the window is every square of the strip whose centre is in the band. The
  strip of arm 1 is x < E1 = s - g1, where g1 upright squares of the far grid stand beside the layer.
  A layer must hold m + 1 - g1 squares: that is one more than the m - g1 upright columns it replaces.
  down  take out one layer per arm, one grid row and one grid column, and move everything beyond each
        cut in by 1. The count is (m + 1 - g1) + (m + 1 - g2) + g1 + g2 - 1 = 2m + 1, as for the family
        step, so the result is on the same line k - 2m, at side L - 1 as built.
  up    put in a copy of one layer per arm, moved along the wall, one more grid row and one more column.
Which layer: where both arms have twins (a neighbouring layer whose squares are this layer's squares
moved along the wall by one spacing d, to SQ_TWIN in place and angle, default 1e-2), the cut is at a twin
and the copy goes in at d. Every contact type of the arm is then kept, and down-then-up gives back the
held layout (the control: 814, 339, 417 and 462 come back within 1e-7). Elsewhere the cut is at any layer
near the middle and the copy goes in at its clearance, the smallest move that clears it of its own copy;
that round trip loses 1.8e-3 to 2.6e-3 (500, 502), because the copy differs from the layer taken out.
With SQ_TWIN above 1e-2 a layout without twins is cut at its closest pair of layers, ranked by the defect
alone. That round trip comes back within 1e-7 while the worse arm's defect is under about 4e-2 (539, 504,
376); near 5e-2 it scatters both ways (548 ends below its held side, 595 above); from about 5.5e-2 the copy
overlaps its neighbour by more than the repair takes and the cut falls back (500). The walks of round 13 use
SQ_TWIN=5.5e-2.
The reader tries every tilted square as the seed of a window, at seven offsets, and keeps a window only
when its layer has the right count. It does not guess: family_step's own down() and up() then check the
count, the side (L - 1 to 1e-7) and the smallest gap of every cut.
A layout with tilted squares on one wall only would step by 2m squares on the line k - m (one layer, one
grid column of m, one grid row of g); none of the held layouts from 300 up is one (avenues/readers.md).

  family_readers.py read  SUB.csv [N ...]              what this reader sees, or why it refuses
  family_readers.py reach SUB.csv OUT.tsv              every n from 300 up: which reader takes it, and the cuts
  family_readers.py ctl   SUB.csv N OUTDIR [--gapped] [--fq]   the control: down one shell, then up (--gapped: no LP
                                                       between), against the held side
  family_readers.py walk  WALKS.tsv DONORDIR DETAILS.csv OUTDIR --mod M,R [--deadline FILE] [--beat TAKE.tsv ...]
                                                       [--pick P]: the first step at the P-th ranked cut
  family_readers.py trip  LIST.tsv DONORDIR DETAILS.csv OUTDIR [--twins 4e-2,5.5e-2,6.5e-2] [--deadline FILE] [--beat ...]
                                                       round trips as a polish: down one shell as built, up again,
                                                       the squeeze and fq, once per distinct cut over the SQ_TWIN values
  family_readers.py band  LIST.tsv DONORDIR DETAILS.csv OUTDIR [--ctl]   the band step: a diagonal cut across a
                                                       corner-to-corner band, k shells (rows donor, direction, k)
  family_readers.py take  DETAILS.csv TAKEDIR OUTDIR [...] [--sources S.tsv] [--beat TAKE.tsv ...] [--table T.tsv]

Our own code. It imports family_step (the step, the squeeze, the certification) and changes nothing in
it. Reads data only: run with python -I. avenues/readers.md has the derivation and the measurements.
"""
import argparse, collections, csv, math, os, sys, time

csv.field_size_limit(16 * 1024 * 1024)

import numpy as np

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
import family_step as fs  # noqa: E402

mlp = fs.mlp
Unreadable = fs.Unreadable
OFFS = (0.0, 0.15, -0.15, 0.3, -0.3, 0.42, -0.42)


# ---------------------------------------------------------------- layers

def cross_gap(A, B):
    """The smallest gap between a square of A and a square of B (negative: they overlap)."""
    P = np.vstack([A, B]); na = len(A)
    ii, jj = np.meshgrid(np.arange(na), na + np.arange(len(B)), indexing='ij')
    pairs = np.column_stack([ii.ravel(), jj.ravel()])
    d = np.hypot(P[pairs[:, 0], 0] - P[pairs[:, 1], 0], P[pairs[:, 0], 1] - P[pairs[:, 1], 1])
    pairs = pairs[d < math.sqrt(2) + 1e-6]
    if not len(pairs):
        return math.inf
    return float(mlp.best_axes(P, pairs)[0].min())


def pitch_of(Q, idx, axis):
    """The pitch of a layer: the smallest move along the wall (1 or more) that clears it of its own copy."""
    A = Q[idx]

    def clear(d):
        B = A.copy(); B[:, axis] += d
        return cross_gap(A, B) >= 1e-10
    if clear(1.0):
        return 1.0
    lo, hi = 1.0, 1.0
    while not clear(hi):
        hi += 0.1
        if hi > 2.0:
            return None
    for _ in range(40):
        mid = (lo + hi) / 2
        if clear(mid): hi = mid
        else: lo = mid
    return hi


def thickness(Q, idx, s):
    """The smallest and the median thickness of a layer along the wall (y), sampled across the strip (x)."""
    A = Q[idx]; out = []
    lo = float((A[:, 0] - mlp.half(A[:, 2])).min()); hi = float((A[:, 0] + mlp.half(A[:, 2])).max())
    for x in np.linspace(lo + 0.02, hi - 0.02, 400):
        ys = []
        for cx, cy, th in A:
            c, sn = math.cos(th), math.sin(th)
            # the chord of the square on the vertical line at x: |u| <= 1/2 and |v| <= 1/2 in its own frame
            lo_t, hi_t = -math.inf, math.inf; dx = x - cx
            for a, b in ((-sn, dx * c), (c, -dx * sn)):      # u = dx c + t sn ... written as b + a t
                pass
            # u = dx*c + t*sn, v = -dx*sn + t*c
            for k0, k1 in ((dx * c, sn), (-dx * sn, c)):
                if abs(k1) < 1e-12:
                    if abs(k0) > 0.5:
                        lo_t, hi_t = 1.0, 0.0
                    continue
                t1, t2 = (-0.5 - k0) / k1, (0.5 - k0) / k1
                lo_t = max(lo_t, min(t1, t2)); hi_t = min(hi_t, max(t1, t2))
            if hi_t > lo_t:
                ys.append((cy + lo_t, cy + hi_t))
        if ys:
            out.append(max(b for a, b in ys) - min(a for a, b in ys))
    return (float(min(out)), float(np.median(out))) if out else (0.0, 0.0)


def _layers(Q, s, m):
    """In the frame of arm 1 (strip at the left wall, layers across in x): every layer that a window takes.

    -> list of dict(idx, c, th, cen, g): the squares, their count, the tilt of the window, a point on its
    middle line, and the number of grid squares beside it."""
    tilt = np.abs(Q[:, 2]) > math.radians(0.5)
    h = mlp.half(Q[:, 2])
    out = {}
    for i in np.nonzero(tilt)[0]:
        th = float(Q[i, 2]); u = (math.cos(th), math.sin(th)); v = (-u[1], u[0])
        a = (Q[:, 0] - Q[i, 0]) * u[0] + (Q[:, 1] - Q[i, 1]) * u[1]
        d = (Q[:, 0] - Q[i, 0]) * v[0] + (Q[:, 1] - Q[i, 1]) * v[1]
        w0 = np.nonzero(tilt & (np.abs(d) < 0.5))[0]
        w0 = w0[np.argsort(a[w0])]
        k = int(np.nonzero(w0 == i)[0][0]); r = l = k
        while r + 1 < len(w0) and a[w0[r + 1]] - a[w0[r]] < 1.35: r += 1
        while l > 0 and a[w0[l]] - a[w0[l - 1]] < 1.35: l -= 1
        run = w0[l:r + 1]                              # the tilted squares side by side with the seed
        if len(run) < 3:
            continue
        hi = float((Q[run, 0] + h[run]).max())         # where the run ends at the grid
        g = int(round(s - hi))
        if abs(s - hi - g) > 0.1 or g < 2:
            continue
        E = s - g; w = m + 1 - g
        if w < 4:
            continue
        rs = set(run.tolist())
        for o in OFFS:
            L = np.nonzero((Q[:, 0] < E) & (d - o > -0.5) & (d - o <= 0.5))[0]
            if len(L) != w or not rs <= set(L.tolist()):
                continue
            key = (g, frozenset(L.tolist()))
            if key in out:
                continue
            cen = Q[L, :2].mean(0)
            dm = (cen[0] - Q[i, 0]) * v[0] + (cen[1] - Q[i, 1]) * v[1] - o
            cen = cen - dm * np.array(v)                # the point of the middle line nearest the mean centre
            out[key] = dict(idx=L[np.argsort(Q[L, 0])], c=w, th=th, cen=cen, b=0, g=g, ntilt=int(tilt[L].sum()))
    return list(out.values())


def _arm_runs(Q, s, m):
    """-> for arm 1 and arm 2 of this frame, {g: [layer]} sorted along the wall."""
    L1 = _layers(Q, s, m)
    L2 = _layers(fs.turned(Q, s, 'T'), s, m)
    for a in L2:                                        # back from the transposed frame
        a['cen'] = a['cen'][::-1].copy(); a['th'] = -a['th']
    runs = []
    for layers, axis in ((L1, 1), (L2, 0)):
        by = collections.defaultdict(list)
        for a in layers:
            by[a['g']].append(a)
        for g in by:
            by[g].sort(key=lambda a: a['cen'][axis])
        runs.append(by)
    return runs


def _grid(Q, s, m, g1, g2):
    """The full grid rows beside arm 1 and the full grid columns beside arm 2, on the lattice of the far corner."""
    E1, E2 = s - g1, s - g2
    inA = Q[:, 0] < E1; inlowB = Q[:, 1] < E2
    up = np.abs(Q[:, 2]) < math.radians(0.5)
    rows, cols = {}, {}
    for j in range(m):
        y = s - 0.5 - j
        if y > E2:
            q = np.nonzero(~inA & (np.abs(Q[:, 1] - y) < 0.25))[0]
            if len(q) == g1 and up[q].all():
                rows[j] = q
        if y > E1:
            q = np.nonzero(~inlowB & (np.abs(Q[:, 0] - y) < 0.25))[0]
            if len(q) == g2 and up[q].all():
                cols[j] = q
    return rows, cols


def read_layers(P, n):
    """-> a read layout in family_step's own form (arm 1 at the left wall, arm 2 at the bottom wall, the
    grid at the far corner), whose runs are the layers a cut window takes; or Unreadable."""
    s, Q0 = fs.canon(P)
    m = int(math.floor(s + 1e-9)); f = s - m; k = n - m * m
    if f < 1e-6:
        raise Unreadable('plain grid')
    ntilt = int((np.abs(Q0[:, 2]) > math.radians(0.5)).sum())
    if ntilt < 10:
        raise Unreadable('%d tilted squares: no arm' % ntilt)
    best = None; why = collections.Counter()
    for ops in ('', 'X', 'Y', 'XY'):
        Q = Q0
        for op in ops:
            Q = fs.turned(Q, s, op)
        by1, by2 = _arm_runs(Q, s, m)
        if not by1 or not by2:
            why['a window with the right count on %s' % ('no wall' if not by1 and not by2 else 'one wall only')] += 1
            continue
        for g1 in sorted(by1, key=lambda g: -len(by1[g]))[:3]:
            for g2 in sorted(by2, key=lambda g: -len(by2[g]))[:3]:
                rows, cols = _grid(Q, s, m, g1, g2)
                if not rows or not cols:
                    why['layers on two walls but no full grid row or column beside them'] += 1
                    continue
                score = (min(len(by1[g1]), len(by2[g2])), len(by1[g1]) + len(by2[g2]))
                if best is None or score > best[0]:
                    best = (score, ops, Q, g1, g2, by1[g1], by2[g2], rows, cols)
    if best is None:
        raise Unreadable('no cut window: %s' % '; '.join('%s (%d of 4 turns)' % kv for kv in why.most_common()))
    _, ops, Q, g1, g2, run1, run2, rows, cols = best
    E1, E2 = s - g1, s - g2; w1, w2 = m + 1 - g1, m + 1 - g2
    out = dict(n=n, s=s, m=m, k=k, f=f, Q=Q, ops=ops, c=(w1, w2), W=(E1, E2), E=(E1, E2), b=(0, 0), wide=True,
               border=([], []), tilted=ntilt, arms=[], rows=rows, cols=cols, reader='layers')
    for run, axis in ((run1, 1), (run2, 0)):
        th = float(np.median([a['th'] for a in run])); p = 1 / math.cos(th)
        out['arms'].append(dict(axis=axis, c=run[0]['c'], th=th, p=p, run=run, nflush=len(run),
                                lo=run[0]['cen'][axis] - p / 2, hi=run[-1]['cen'][axis] + p / 2))
    pt = fs._parts(out)
    out['zones'] = dict(corner=int(pt['corner'].sum()), cap1=int(pt['cap1'].sum()), cap2=int(pt['cap2'].sum()))
    return out


# ---------------------------------------------------------------- the step

def _one(R, j1, j2, direction):
    """family_step's own step at one layer per arm. -> (array, info, the read layout with these two cuts)"""
    a1, a2 = R['arms']
    if direction == 'up':
        for j, a in ((j1, a1), (j2, a2)):
            if 'p' not in j:
                j['p'] = pitch_of(R['Q'], j['idx'], a['axis'])
            if j['p'] is None:
                raise Unreadable('a layer does not clear its own copy within one more unit')
    R2 = dict(R, arms=[dict(a1, run=[j1], p=j1.get('p', a1['p'])), dict(a2, run=[j2], p=j2.get('p', a2['p']))])
    G, info = fs.down(R2) if direction == 'down' else fs.up(R2)
    return G, info, R2


TWIN = float(os.environ.get('SQ_TWIN', '1e-2'))   # two layers are twins when every square of one is the square of the other moved along the wall


def twins(R):
    """Mark every layer of each run that has a twin beside it: a disjoint layer of the same count whose
    squares are its own squares moved along the wall by one spacing d (0.9 < d < 1.6), to TWIN in place and
    in angle. A cut at such a layer keeps every contact type of the arm: down, its neighbour takes its place;
    up, its copy goes in at the spacing d, which is the contact it already has with its twin.
    -> sets layer['twin'] = (defect, d) on the layers that have one (the best twin)."""
    Q = R['Q']
    for arm in R['arms']:
        al = arm['axis']; ac = 1 - al; run = arm['run']
        srt = [j['idx'][np.argsort(Q[j['idx'], ac])] for j in run]
        for a in range(len(run)):
            for b in range(a + 1, len(run)):
                if len(srt[a]) != len(srt[b]) or set(srt[a].tolist()) & set(srt[b].tolist()):
                    continue
                D = Q[srt[b]] - Q[srt[a]]
                D[:, 2] = (D[:, 2] + math.pi / 4) % (math.pi / 2) - math.pi / 4
                d = float(np.median(D[:, al]))
                if not 0.9 < d < 1.6:
                    continue
                dev = max(float(np.abs(D[:, al] - d).max()), float(np.abs(D[:, ac]).max()), float(np.abs(D[:, 2]).max()))
                if dev < TWIN:
                    for j in (a, b):
                        if 'twin' not in run[j] or dev < run[j]['twin'][0]:
                            run[j]['twin'] = (dev, d)
    return R


def twin_cuts(R, direction):
    """The step at a twin layer in each arm, the twins nearest the middle first. -> list of (gap, i1, i2)."""
    twins(R)
    run1, run2 = R['arms'][0]['run'], R['arms'][1]['run']
    t1 = [i for i in range(len(run1)) if 'twin' in run1[i]]; t2 = [i for i in range(len(run2)) if 'twin' in run2[i]]
    if not t1 or not t2:
        raise Unreadable('no twin layers (arm 1: %d, arm 2: %d)' % (len(t1), len(t2)))
    # the closest twins first (by power of ten of the defect), then nearest the middle; a pair whose defect is
    # 1e-2 or more (SQ_TWIN above 1e-2: the closest pair of a layout without twins) ranks by its defect alone
    def near(run):
        def key(i):
            dev = run[i]['twin'][0]
            if dev >= 1e-2:
                return (0, dev)
            return (round(math.log10(max(dev, 1e-12))), abs(i - (len(run) - 1) / 2))
        return key
    t1.sort(key=near(run1))
    t2.sort(key=near(run2))
    good = []; first = None
    for i1 in t1[:4]:
        for i2 in t2[:4]:
            j1, j2 = run1[i1], run2[i2]
            if direction == 'up':
                j1['p'], j2['p'] = j1['twin'][1], j2['twin'][1]
            try:
                good.append((_one(R, j1, j2, direction)[1]['gap'], i1, i2))
            except Unreadable as ex:
                first = first or ex
        if good:
            break
    if not good:
        raise first
    good.sort(key=lambda v: v[0] > -5e-3, reverse=True)   # stable: nearest the middle first among the legal ones
    return good


def cuts(R, direction):
    """Every pair of layers worth a build, best first: -> list of (gap, i1, i2).

    One arm at a time: the layers of arm 1 against a layer of arm 2 near the middle, then the layers of
    arm 2 against the best of arm 1. A cut that is legal as built ranks by how near the middle it is."""
    run1, run2 = R['arms'][0]['run'], R['arms'][1]['run']
    memo = {}

    def val(i1, i2):
        if (i1, i2) not in memo:
            try:
                memo[(i1, i2)] = _one(R, run1[i1], run2[i2], direction)[1]['gap']
            except Unreadable as ex:
                memo[(i1, i2)] = ex
        return memo[(i1, i2)]

    def pm(i1, i2):                                     # the opening of an upward step: the larger layer pitch
        return max(run1[i1].get('p') or 1.0, run2[i2].get('p') or 1.0) if direction == 'up' else 1.0

    def rank(i, run, g):
        return (min(g, 0.0), -abs(i - (len(run) - 1) / 2))
    mid = lambda run: sorted(range(len(run)), key=lambda i: abs(i - (len(run) - 1) / 2))
    first = None
    for i2 in mid(run2)[:8]:
        ok = [(rank(i1, run1, val(i1, i2)), i1) for i1 in range(len(run1)) if not isinstance(val(i1, i2), Exception)]
        if not ok:
            first = first or val(mid(run1)[0], i2)
            continue
        i1 = max(ok)[1]
        for j in range(len(run2)):
            val(i1, j)
        break
    good = [(g, i1, i2) for (i1, i2), g in memo.items() if not isinstance(g, Exception)]
    if not good:
        raise first or Unreadable('no layer pair to cut')
    if direction == 'up':       # every layer pitch near the middle, so the smallest opening can win
        for i in mid(run1)[:8]:
            if 'p' not in run1[i]:
                run1[i]['p'] = pitch_of(R['Q'], run1[i]['idx'], 1)
        for i in mid(run2)[:8]:
            if 'p' not in run2[i]:
                run2[i]['p'] = pitch_of(R['Q'], run2[i]['idx'], 0)
        best1 = min((i for i in mid(run1)[:8] if run1[i]['p']), key=lambda i: run1[i]['p'], default=None)
        best2 = min((i for i in mid(run2)[:8] if run2[i]['p']), key=lambda i: run2[i]['p'], default=None)
        if best1 is not None and best2 is not None:
            val(best1, best2)
        good = [(g, i1, i2) for (i1, i2), g in memo.items() if not isinstance(g, Exception)]
        # an upward start that overlaps by less than 5e-3 is repaired; among those the smallest opening first
        good.sort(key=lambda v: (v[0] > -5e-3, -pm(v[1], v[2]), -abs(v[1] - (len(run1) - 1) / 2) - abs(v[2] - (len(run2) - 1) / 2)), reverse=True)
        return good
    good.sort(key=lambda v: (min(v[0], 0.0), -abs(v[1] - (len(run1) - 1) / 2) - abs(v[2] - (len(run2) - 1) / 2)), reverse=True)
    return good


def build_layers(R, direction, pick=0):
    """The step at twin layers where both arms have them; else at the best pair of layers by cuts().
    -> (array, info, R2); info['cut'] says which."""
    try:
        good = twin_cuts(R, direction); how = 'twin'
    except Unreadable as ex:
        good = cuts(R, direction); how = 'any (%s)' % ex
    if pick >= len(good):
        raise Unreadable('cut %d asked, %d ranked' % (pick, len(good)))
    g, i1, i2 = good[pick]
    j1, j2 = R['arms'][0]['run'][i1], R['arms'][1]['run'][i2]
    if how == 'twin' and direction == 'up':
        j1['p'], j2['p'] = j1['twin'][1], j2['twin'][1]
    G, info, R2 = _one(R, j1, j2, direction)
    info['cut'] = how
    return G, info, R2


def read_build(P, n, direction, mine_first=False, pick=0):
    """A step from any layout: family_step's readers first, this reader where they refuse or cannot cut.
    pick > 0: this reader only, at its pick-th ranked cut (the alternative cuts of a walk's first step).
    -> (array, info, read layout, name of the reader)"""
    errs = []
    if pick:
        try:
            R = read_layers(P, n)
            G, info, R2 = build_layers(R, direction, pick)
            return G, info, R2, 'layers cut %d' % pick
        except Unreadable as ex:
            raise Unreadable('layers: %s' % ex)
    order = ('layers', 'family') if mine_first else ('family', 'layers')
    for who in order:
        try:
            if who == 'family':
                R = fs.read(P, n)
                G, info = fs.build(R, direction)
                return G, info, R, 'wide' if R.get('wide') else 'strict'
            R = read_layers(P, n)
            G, info, R2 = build_layers(R, direction)
            return G, info, R2, 'layers'
        except Unreadable as ex:
            errs.append('%s: %s' % (who, ex))
    raise Unreadable(' | '.join(errs))


# ---------------------------------------------------------------- the band step

BAND_TILT = 5.0        # degrees: a square turned less than this is a grid square, not a band square


def band_frame(P):
    """A corner-to-corner band in the frame where it runs from (0, 0) to (s, s). -> (s, Q, tilted mask)."""
    s, Q = fs.canon(P)
    up = np.abs(Q[:, 2]) < math.radians(BAND_TILT)   # the squeeze turns grid squares by up to a degree or so
    T = Q[~up]
    if len(T) < 10:
        raise Unreadable('%d tilted squares: no band' % len(T))
    if np.cov(T[:, 0], T[:, 1])[0, 1] < 0:          # the band runs along (-1, 1): mirror x
        Q = Q.copy(); Q[:, 0] = s - Q[:, 0]; Q[:, 2] = -Q[:, 2]; T = Q[~up]
    b = (T[:, 1] - T[:, 0]) / math.sqrt(2)
    if np.abs(b).max() > 2.5:
        raise Unreadable('the tilted squares are not one band along the diagonal (|b| up to %.1f)' % np.abs(b).max())
    return s, Q, ~up


def band_build(Q, s, k, direction, a0):
    """The band step at the diagonal cut a = a0 (a = (x + y) / sqrt 2), k shells.

    down: keep every square with a < a0, move every square with a >= a0 + k sqrt 2 by (-k, -k), drop the rest
          (one band period of length k sqrt 2, and k rows and k columns of each grid); clip to the box s - k.
    up:   keep every square with a < a0 + k sqrt 2, move every square with a >= a0 by (k, k) (the band period
          [a0, a0 + k sqrt 2) is now in twice), and fill the two corners the moves leave open with the upright
          grid moved by (0, k) above the band and by (k, 0) below it.
    Both grids are lattices that a move by (k, k) keeps, so only the band meets itself at a misfit: the twin
    defect of the band under (k, k). -> array"""
    a = (Q[:, 0] + Q[:, 1]) / math.sqrt(2); D = k * math.sqrt(2)
    if direction == 'down':
        A = Q[a < a0]
        B = Q[a >= a0 + D] - np.array([k, k, 0.0])
        G = np.vstack([A, B])
        sn = s - k
        ok = (G[:, 0] > 0) & (G[:, 1] > 0) & (G[:, 0] < sn) & (G[:, 1] < sn)
        return G[ok]
    A = Q[a < a0 + D]
    B = Q[a >= a0] + np.array([k, k, 0.0])
    G = [A, B]
    up = np.abs(Q[:, 2]) < math.radians(BAND_TILT)
    for mv, side_ in (((0, k), 1), ((k, 0), -1)):
        C = Q[up] + np.array([mv[0], mv[1], 0.0])
        ac = (C[:, 0] + C[:, 1]) / math.sqrt(2); bc = (C[:, 1] - C[:, 0]) * side_
        inA = (C[:, 0] < s) & (C[:, 1] < s) & (ac < a0 + D)
        inB = (C[:, 0] > k) & (C[:, 1] > k) & (ac >= a0 + D)
        G.append(C[(bc > 0) & ~inA & ~inB])
    return np.vstack(G)


def band_step(P, n, k, direction, offs=None):
    """The band step over cuts near the middle. The count it builds depends on the cut; the count that most
    cuts give is the band's own period (in the held bands k = 3 shells hold 113 squares, not 6m + 6), so the
    step keeps that count, at the cut with the largest smallest gap as built. -> (array, info)"""
    s, Q, tilt = band_frame(P)
    if offs is None:            # every cut along the band in steps of 0.1, so a down step finds where the band meets itself best
        lo = 3.0 - (s / math.sqrt(2) - k / math.sqrt(2)); hi = s * math.sqrt(2) - 3.0 - k * math.sqrt(2) - (s / math.sqrt(2) - k / math.sqrt(2))
        offs = np.arange(lo, hi, 0.1)
    target = s + k if direction == 'up' else s - k
    by = collections.defaultdict(list); why = []
    for o in offs:
        a0 = s / math.sqrt(2) - k / math.sqrt(2) + o
        G = band_build(Q, s, k, direction, a0)
        L = float(mlp.side(G))
        if abs(L - target) > 1e-7:
            why.append('side %.6f, want %.6f' % (L, target)); continue
        by[len(G)].append((round(mlp.min_gap(G), 6), -abs(o), a0, G, L))
    if not by:
        raise Unreadable('band step %s %d: %s' % (direction, k, '; '.join(sorted(set(why))[:3])))
    c = max(by, key=lambda c: len(by[c]))
    g, _, a0, G, L = max(by[c], key=lambda v: v[:2])
    if g < -max(3e-2, float(os.environ.get('SQ_APART') or 0)):
        raise Unreadable('band step %s %d: the opened layout overlaps (smallest gap %.2e)' % (direction, k, g))
    return G, dict(side=L, gap=g, a0=a0, s=s, cuts=len(by[c]))


def cmd_band(a):
    """The band step over a list: rows donor, direction, shells. Each step: band_step, the squeeze, finish.
    --ctl: the round trip, the step and its inverse at the same cut with no LP between (it must give back the
    donor exactly), then the round trip the other way round with the squeeze, against the held side."""
    os.makedirs(a.out + '/raw', exist_ok=True)
    held = fs._bars(a.details, a.beat)
    tsv = '%s/rows-band.tsv' % a.out
    if not os.path.exists(tsv):
        open(tsv, 'w').write(HEAD)

    def dead():
        try:
            return a.deadline and time.time() > float(open(a.deadline).read().split()[0])
        except Exception:
            return False
    for l in open(a.list).read().splitlines():
        if not l.strip() or l.startswith('donor') or dead():
            continue
        donor, direction, k = l.split('\t')[:3]; k = int(k)
        dn = int(donor.split('-')[0])
        P = fs.load(os.path.join(a.donors, donor + '.csv'))[dn]
        t0 = time.time(); start = slp = final = gap = float('nan'); state = 'ok'; t = 0; chain = ''
        fs.set_limit(a.buildsec)
        try:
            s, Q, tilt = band_frame(P)
            if a.ctl:
                G, info = band_step(P, dn, k, direction)
                back = band_build(G, info['side'], k, 'down' if direction == 'up' else 'up', info['a0'])
                same = len(back) == dn and np.allclose(np.array(sorted(map(tuple, np.round(back, 9)))), np.array(sorted(map(tuple, np.round(Q, 9)))))
                chain = 'ctl: %s %d then back at the same cut gives the donor %s' % (direction, k, 'exactly' if same else 'NOT')
            G, info = band_step(P, dn, k, direction)
            t = len(G); start = info['side']; gap = info['gap']
            chain += ' cut a0=%.3f' % info['a0']
            X, L, trace = fs.squeeze(G, iters=a.iters, fq=False, stop=dead)
            slp = L
            if a.ctl:                                   # back again from the squeezed step, the other way
                G2, info2 = band_step(X, t, k, 'down' if direction == 'up' else 'up')
                Y, L2, _ = fs.squeeze(G2, iters=a.iters, fq=False, stop=dead)
                chain += '; round trip after the LP: n=%d side %.9f, donor %.9f, %+.2e' % (len(Y), L2, s, L2 - s)
            X, L = fs.finish(X, L, held.get(t, L), direction, a.fqwin, dead)
            final = L
            if t in held and final < held[t] - 1e-9:
                fs.write_rows('%s/raw/%d-band%s%dfrom%s.csv' % (a.out, t, direction, k, donor), t, X)
                state = 'below held'
        except Unreadable as ex:
            state = 'refused: %s' % str(ex)[:300]
        except Exception as ex:
            state = 'error: %s' % str(ex)[:80]
        if fs._over() and state == 'ok':
            state = 'time limit'
        fs.set_limit(None)
        with open(tsv, 'a') as h:
            h.write('%d\t%s\t%s\t%d\t%.9f\t%.9f\t%.9f\t%.9f\t%.0f\t%s\t%s\t%.2e\t%s\n' % (
                t, donor, 'band' + direction, k, start, slp, final, held.get(t, float('nan')), time.time() - t0, state, 'band', gap, chain))
        print(t, donor, 'band' + direction, k, '%.9f' % final, 'bar %.9f' % held.get(t, float('nan')), state, chain, '%.0fs' % (time.time() - t0), flush=True)


def describe(R):
    a1, a2 = R['arms']
    return ('n=%d m=%d k=%d f=%.6f line=%d layer=%d,%d squares (tilted %d,%d) window tilt=%.2f,%.2f layers=%d,%d '
            'grid beside=%d,%d rows=%d cols=%d turn=%s' % (
                R['n'], R['m'], R['k'], R['f'], R['k'] - 2 * R['m'], a1['c'], a2['c'],
                int(np.median([j['ntilt'] for j in a1['run']])), int(np.median([j['ntilt'] for j in a2['run']])),
                math.degrees(abs(a1['th'])), math.degrees(abs(a2['th'])), len(a1['run']), len(a2['run']),
                R['m'] + 1 - a1['c'], R['m'] + 1 - a2['c'], len(R['rows']), len(R['cols']), R['ops'] or '-'))


# ---------------------------------------------------------------- commands

def classify(P, n):
    """Which reader takes a layout: 'plain grid', 'strict', 'wide', 'loose', or '' (none of family_step's)."""
    s = fs.canon(P)[0]
    if s - math.floor(s + 1e-9) < 1e-6:
        return 'plain grid'
    for name, fn in (('strict', lambda: fs.read_strict(P, n)), ('wide', lambda: fs.read_wide(P, n, loose=False)),
                     ('loose', lambda: fs.read_wide(P, n, loose=True))):
        try:
            fn(); return name
        except Unreadable:
            pass
    return ''


def cmd_read(a):
    P = fs.load(a.sub, set(a.n) if a.n else None)
    for n in sorted(P):
        if n < 300 and not a.n:
            continue
        try:
            R = read_layers(P[n], n)
            line = 'reads   ' + describe(R)
            for di in ('down', 'up'):
                try:
                    G, info, R2 = build_layers(R, di)
                    line += ' | %s builds: side %.9f gap %.2e' % (di, info['side'], info['gap'])
                except Unreadable as ex:
                    line += ' | %s refused: %s' % (di, ex)
            print(line)
        except Unreadable as ex:
            print('refuses n=%d: %s' % (n, ex))


def cmd_reach(a):
    """Every n from 300 up: the class by family_step's readers, then this reader's read, its twins and its two cuts."""
    P = fs.load(a.sub)
    with open(a.out + '.tmp', 'w') as h:
        h.write('n\tm\tf\tfamily_reader\tlayers_reader\tlayer1\tlayer2\ttilted1\ttilted2\tlayers1\tlayers2\ttwins1\ttwins2'
                '\tdown\tdown_gap\tdown_cut\tup\tup_gap\tup_cut\tup_open\n')
        for n in sorted(P):
            if n < 300:
                continue
            cl = classify(P[n], n)
            s = fs.canon(P[n])[0]; m = int(math.floor(s + 1e-9))
            cells = [''] * 16
            if cl != 'plain grid':
                try:
                    R = read_layers(P[n], n); a1, a2 = R['arms']
                    twins(R)
                    cells[0] = 'reads'
                    cells[1:9] = [a1['c'], a2['c'], int(np.median([j['ntilt'] for j in a1['run']])),
                                  int(np.median([j['ntilt'] for j in a2['run']])), len(a1['run']), len(a2['run']),
                                  sum('twin' in j for j in a1['run']), sum('twin' in j for j in a2['run'])]
                    for q, di in ((9, 'down'), (12, 'up')):
                        try:
                            G, info, R2 = build_layers(R, di)
                            cells[q] = 'builds'; cells[q + 1] = '%.2e' % info['gap']; cells[q + 2] = info['cut'].split(' ')[0]
                            if di == 'up':
                                cells[15] = '%.4f' % (info['side'] - s - 1)
                        except Unreadable as ex:
                            cells[q] = 'refused: %s' % ex
                except Unreadable as ex:
                    cells[0] = 'refused: %s' % ex
            h.write('\t'.join(map(str, [n, m, '%.6f' % (s - m), cl or 'none'] + cells)) + '\n'); h.flush()
    os.replace(a.out + '.tmp', a.out)


def cmd_ctl(a):
    """The control: one shell down from a held layout with the squeeze, then one shell up from the result.
    The round trip must come back to a legal layout of the same n within 1e-7 of the held side."""
    os.makedirs(a.out, exist_ok=True)
    P = fs.load(a.sub, {a.n})[a.n]
    s0 = fs.canon(P)[0]
    R = read_layers(P, a.n)
    print('donor ', describe(R), flush=True)
    t0 = time.time()
    G, info, R2 = build_layers(R, 'down')
    j1, j2 = R2['arms'][0]['run'][0], R2['arms'][1]['run'][0]
    Qt = fs.turned(R2['Q'], R2['s'], 'T')
    print('down as built: %d squares (%d less = 2m + 1 = %d), side %.9f = held %.9f - 1 %+.1e, smallest gap %.2e' % (
        len(G), a.n - len(G), 2 * R['m'] + 1, info['side'], s0, info['side'] - (s0 - 1), info['gap']))
    print('  cut: %s; twin defect and spacing of the cut layers: %s, %s' % (
        info.get('cut', ''), j1.get('twin', '-'), j2.get('twin', '-')))
    print('  layer of arm 1: %d squares, %d tilted, median thickness along the wall %.4f' % (
        len(j1['idx']), j1['ntilt'], thickness(R2['Q'], j1['idx'], s0)[1]))
    print('  layer of arm 2: %d squares, %d tilted, median thickness along the wall %.4f' % (
        len(j2['idx']), j2['ntilt'], thickness(Qt, j2['idx'], s0)[1]), flush=True)
    fs.write_rows('%s/%d-down-gapped.csv' % (a.out, len(G)), len(G), G)
    nd = len(G)
    if a.gapped:            # the exactness test: the step up from the layout as built, with no LP between
        X = G
        print('no LP between the two steps', flush=True)
    else:
        X, L, trace = fs.squeeze(G, iters=a.iters, fq=False, log=print if a.verbose else None)
        print('down after the sequential LP: n=%d side %.9f (%.0f s)' % (nd, L, time.time() - t0), flush=True)
    fs.write_rows('%s/%d-down.csv' % (a.out, nd), nd, X)
    G2, info2, Rb, who = read_build(X, nd, 'up', mine_first=True)
    print('up as built (reader %s): %d squares, side %.9f, smallest gap %.2e' % (who, len(G2), info2['side'], info2['gap']), flush=True)
    if who == 'layers':
        print('  cut: %s; twin defect and spacing of the copied layers: %s, %s' % (
            info2.get('cut', ''), Rb['arms'][0]['run'][0].get('twin', '-'), Rb['arms'][1]['run'][0].get('twin', '-')), flush=True)
    if len(G2) != a.n:
        print('CONTROL FAILS: the round trip gives n=%d' % len(G2)); return
    Y, L2, trace2 = fs.squeeze(G2, iters=a.iters, fq=False, log=print if a.verbose else None)
    print('up after the sequential LP: n=%d side %.9f; held %.9f; difference %+.3e (%.0f s)' % (len(Y), L2, s0, L2 - s0, time.time() - t0), flush=True)
    if a.fq and abs(L2 - s0) > 1e-7:
        Y, L2 = fs.finish(Y, L2, s0, 'up', 2e-2)
        print('after fq and the LP: side %.9f; difference %+.3e (%.0f s)' % (L2, L2 - s0, time.time() - t0), flush=True)
    fs.write_rows('%s/%d-roundtrip.csv' % (a.out, a.n), a.n, Y)
    g = mlp.min_gap(Y)
    Lc, fr = fs.certify(a.n, Y)
    print('round trip: smallest gap %.2e, floatsafe side %s' % (g, 'none (not legal)' if Lc is None else '%.9f' % Lc))
    if abs(L2 - s0) <= 1e-7:
        print('CONTROL PASSES: %.9f against held %.9f' % (L2, s0))
    else:
        print('CONTROL %s: %.9f against held %.9f' % ('ends below the held side' if L2 < s0 else 'FAILS', L2, s0))
        lab = info2['lab']
        print('load-carrying contacts by zone:', fs.stress_summary(Y, lab))


HEAD = 'target\tdonor\tdirection\tshells\tafter_step\tafter_slp\tafter_squeeze\tbar\tseconds\tstate\treader\tgap\tchain\n'


def walk_misses(misses, state, improvement, minimum):
    return 0 if state == 'below held' and improvement > minimum else misses + 1


def cmd_walk(a):
    """family_step's walk with read_build: WALKS.tsv has rows donor, direction. A direction ends after
    --misses steps in a row that do not end below the bar, or at a step that ends 5 * stopgap above it.
    A third column pick (or --pick P for every row) > 0: the first step is at the pick-th ranked cut of the
    layer reader (0 is the best); the rows of that walk have shells 'KcP' and its layouts go to
    raw/N-DIRKcPfromDONOR.csv."""
    os.makedirs(a.out + '/raw', exist_ok=True)
    if a.nearout:
        os.makedirs(a.out + '/near', exist_ok=True)
    M, Rm = (int(x) for x in a.mod.split(','))
    walks = [(l.split('\t') + [''])[:3] for l in open(a.walks).read().splitlines() if l.strip() and not l.startswith('donor')]
    walks = [(d, r, int(p) if p.strip() else a.pick) for d, r, p in walks]
    deferred = set()
    if os.path.exists(a.defer_list):
        for r in csv.DictReader(open(a.defer_list), delimiter='\t'):
            if not os.path.basename(a.walks).startswith(r.get('allow_prefix') or 'y'):
                deferred.add((r['donor'], r['direction'], int(r['pick'])))
    held = fs._bars(a.details, a.beat)
    tsv = '%s/rows-walk-%d.tsv' % (a.out, Rm)
    done = set()
    if os.path.exists(tsv):
        for l in open(tsv).read().splitlines()[1:]:
            v = l.split('\t')
            if v[3].split('c')[0] == '1':
                done.add((v[1], v[2], int(v[3].split('c')[1]) if 'c' in v[3] else 0))
    else:
        open(tsv, 'w').write(HEAD)

    def dead():
        try:
            return a.deadline and time.time() > float(open(a.deadline).read().split()[0])
        except Exception:
            return False
    for i, (donor, direction, pick) in enumerate(walks):
        if (donor, direction, pick) in deferred:
            print('deferred lower-priority walk', donor, direction, pick, flush=True)
            continue
        if i % M != Rm or dead() or (donor, direction, pick) in done:
            continue
        dn = int(donor.split('-')[0])
        cur = fs.load(os.path.join(a.donors, donor + '.csv'))[dn]; ncur = dn; miss = 0
        for k in range(1, a.maxsteps + 1):
            if dead():
                break
            t0 = time.time(); start = slp = final = gap = float('nan'); state = 'ok'; chain = ''; t = 0; go = False; who = ''
            ks = '%dc%d' % (k, pick) if pick else '%d' % k
            limit = a.buildsec
            if a.deadline:
                remaining = float(open(a.deadline).read().split()[0]) - time.time()
                if remaining <= 0:
                    break
                limit = min(limit, remaining)
            fs.set_limit(limit)
            try:
                G, info, R, who = read_build(cur, ncur, direction, mine_first=(k == 1), pick=pick if k == 1 else 0)
                t = len(G)
                if not (1 <= t <= 1000):
                    break
                start = info['side']; gap = info['gap']
                X, L, trace = fs.squeeze(G, iters=a.iters, fq=False, stop=dead)
                slp = L
                X, L = fs.finish(X, L, held[t], direction, a.fqwin, dead)
                final = L
                if a.nearout and math.isfinite(final) and final < held[t] + a.nearout:
                    fs.write_rows('%s/near/%d-%s%sfrom%s.csv' % (a.out, t, direction, ks, donor), t, X)
                if final < held[t] - 1e-9:
                    fs.write_rows('%s/raw/%d-%s%sfrom%s.csv' % (a.out, t, direction, ks, donor), t, X)
                    state = 'below held'
                elif L > held[t] + 1e-5:
                    try:
                        chain = fs.stress_summary(X, info['lab'])
                    except Exception as ex:
                        chain = 'no chain: %s' % str(ex)[:40]
                miss = walk_misses(miss, state, held[t] - final, a.min_progress)
                go = miss < a.misses and final < held[t] + 5 * a.stopgap
                cur, ncur = X, t
            except Unreadable as ex:
                state = 'refused: %s' % str(ex)[:300]
                if not t:
                    m = int(math.floor(fs.canon(cur)[0] + 1e-9))
                    t = ncur - 2 * m - 1 if direction == 'down' else ncur + 2 * m + 3
                    if not (1 <= t <= 1000):
                        break
            except Exception as ex:
                state = 'error: %s' % str(ex)[:80]
            if fs._over() and state == 'ok':
                state = 'time limit'
            fs.set_limit(None)
            if t:
                with open(tsv, 'a') as h:
                    h.write('%d\t%s\t%s\t%s\t%.9f\t%.9f\t%.9f\t%.9f\t%.0f\t%s\t%s\t%.2e\t%s\n' % (
                        t, donor, direction, ks, start, slp, final, held.get(t, float('nan')), time.time() - t0, state, who, gap, chain))
                print(t, donor, direction, ks, '%.9f' % final, 'bar %.9f' % held.get(t, float('nan')), state, who, '%.0fs' % (time.time() - t0), flush=True)
            if not go:
                break


def cmd_trip(a):
    """Round trips as a polish: one shell down from each layout of LIST.tsv as built (no LP between), one shell
    up again from that, then the squeeze and the fq polish of finish(), once per SQ_TWIN value of --twins.
    Two values that give the same two cuts run once. A round trip that comes back within 1e-7 of its start
    is exact and gets no fq. -> rows-trip-R.tsv (direction 'trip', shells = the index of the SQ_TWIN value)
    and raw/N-tripJfromDONOR.csv for every end below the bar."""
    global TWIN
    os.makedirs(a.out + '/raw', exist_ok=True)
    M, Rm = (int(x) for x in a.mod.split(','))
    donors = [l.split('\t')[0] for l in open(a.list).read().splitlines() if l.strip() and not l.startswith('donor')]
    held = fs._bars(a.details, a.beat)
    tws = [float(x) for x in a.twins.split(',')]
    tsv = '%s/rows-trip-%d.tsv' % (a.out, Rm)
    done = set()
    if os.path.exists(tsv):
        done = set((l.split('\t')[1], l.split('\t')[3]) for l in open(tsv).read().splitlines()[1:])
    else:
        open(tsv, 'w').write(HEAD)

    def dead():
        try:
            return a.deadline and time.time() > float(open(a.deadline).read().split()[0])
        except Exception:
            return False

    def sig(Rx):
        return tuple(frozenset(arm['run'][0]['idx'].tolist()) for arm in Rx['arms']) if 'arms' in Rx else ()
    for i, donor in enumerate(donors):
        if i % M != Rm or dead():
            continue
        n = int(donor.split('-')[0])
        P = fs.load(os.path.join(a.donors, donor + '.csv'))[n]
        s0 = fs.canon(P)[0]
        seen = {}
        for j, tw in enumerate(tws, 1):
            if dead() or (donor, str(j)) in done:
                continue
            TWIN = tw
            t0 = time.time(); start = slp = final = gap = float('nan'); state = 'ok'; who = ''; chain = ''
            fs.set_limit(a.buildsec)
            try:
                R = read_layers(P, n)
                G, info, R2 = build_layers(R, 'down')
                d1, d2 = (R2['arms'][q]['run'][0].get('twin', (float('nan'),))[0] for q in (0, 1))
                chain = 'SQ_TWIN=%g down %s %.1e/%.1e' % (tw, info['cut'].split(' ')[0], d1, d2)
                G2, info2, Rb, who = read_build(G, len(G), 'up', mine_first=True)
                if len(G2) != n:
                    raise Unreadable('the round trip gives n=%d' % len(G2))
                if who == 'layers':
                    u1, u2 = (Rb['arms'][q]['run'][0].get('twin', (float('nan'),))[0] for q in (0, 1))
                    chain += ', up %s %.1e/%.1e' % (info2['cut'].split(' ')[0], u1, u2)
                key = (sig(R2), who, sig(Rb))
                start = info2['side']; gap = info2['gap']
                if key in seen:
                    state = 'same cuts as SQ_TWIN=%g' % seen[key]
                else:
                    seen[key] = tw
                    X, L, trace = fs.squeeze(G2, iters=a.iters, fq=False, stop=dead)
                    slp = L
                    if abs(L - s0) > 1e-7:
                        X, L = fs.finish(X, L, held[n], 'up', a.fqwin, dead)
                    else:
                        state = 'exact'
                    final = L
                    if final < held[n] - 1e-9:
                        fs.write_rows('%s/raw/%d-trip%dfrom%s.csv' % (a.out, n, j, donor), n, X)
                        state = 'below held'
            except Unreadable as ex:
                state = 'refused: %s' % str(ex)[:300]
            except Exception as ex:
                state = 'error: %s' % str(ex)[:80]
            if fs._over() and state == 'ok':
                state = 'time limit'
            fs.set_limit(None)
            with open(tsv, 'a') as h:
                h.write('%d\t%s\t%s\t%d\t%.9f\t%.9f\t%.9f\t%.9f\t%.0f\t%s\t%s\t%.2e\t%s\n' % (
                    n, donor, 'trip', j, start, slp, final, held.get(n, float('nan')), time.time() - t0, state, who, gap, chain))
            print(n, donor, 'trip', j, '%.9f' % final, 'bar %.9f' % held.get(n, float('nan')), state, chain, '%.0fs' % (time.time() - t0), flush=True)


def cmd_take(a):
    """Certify every raw layout the lane's way (floatsafe at 2.2e-11, more than 1e-10 below the held score
    and below the same n of every --beat take) and write the take dir; take.tsv is replaced by rename."""
    import floatsafe
    held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(a.details))}
    bar = dict(held)
    for fn in a.beat or ():
        if os.path.exists(fn):
            for r in csv.DictReader(open(fn), delimiter='\t'):
                bar[int(r['n'])] = min(bar[int(r['n'])], float(r['new']))
    src = {}
    if a.sources:
        for r in csv.DictReader(open(a.sources), delimiter='\t'):
            src[r['donor']] = (r['source'], r['licence'])
    best = {}; cert = {}
    for d in a.outs:
        rawdir = os.path.join(d, 'raw')
        for fn in sorted(os.listdir(rawdir)) if os.path.isdir(rawdir) else []:
            if not fn.endswith('.csv'):
                continue
            n = int(fn.split('-')[0]); p = os.path.join(rawdir, fn)
            rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(p))]
            if len(rows) != n:
                print('drop', n, 'rows', len(rows), p); continue
            _, fr, score, e = floatsafe.work((n, rows))
            ok = fr is not None and score < held[n] - 1e-10 and score < bar[n]
            cert[fn[:-4]] = (ok, score, 'floatsafe' if fr is None else 'not below held by 1e-10 and every other take' if not ok else '')
            if not ok:
                print('drop', n, score, held[n], bar[n], e, p); continue
            if n not in best or score < best[n][0]:
                best[n] = (score, fr, fn[:-4])
    os.makedirs(a.take + '/work', exist_ok=True)
    tot = 0.0; lines = ['n\theld\tnew\tgain\tsource\tlicence\n']
    for n in sorted(best):
        score, fr, tag = best[n]
        tmp = '%s/work/%d.csv.tmp' % (a.take, n)
        with open(tmp, 'w', newline='') as g:
            w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
            for r in fr:
                w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
        os.replace(tmp, '%s/%d.csv' % (a.take, n))
        step_, donor = tag.split('-', 1)[1].split('from')
        s_, lic = src.get(donor, ('the held packing of n = %s' % donor.split('-')[0], 'own search'))
        tot += held[n] - score
        if step_[:-1] == 'trip':
            what = 'family_readers.py round trip (one shell down, then up again, at the layer cut) of %s' % s_
        elif step_.startswith('band'):
            what = 'family_readers.py band step, %s shells %s (a diagonal cut across the corner-to-corner band, one band period) from %s' % (
                step_[-1], step_[4:-1], s_)
        elif 'c' in step_:          # a walk whose first step is at an alternative cut (walk --pick)
            dk, pk = step_.split('c')
            what = 'family_readers.py %s shell(s) %s, the first at cut %s of the layer reader, from %s' % (
                dk.lstrip('updown'), dk.rstrip('0123456789'), pk, s_)
        else:
            what = 'family_readers.py %s shell(s) %s from %s' % (step_[-1], step_[:-1], s_)
        lines.append('%d\t%r\t%r\t%.3e\t%s\t%s\n' % (n, held[n], score, held[n] - score, what, lic))
        print('keep', n, held[n], score, '%.3e' % (held[n] - score), tag)
    tmp = a.take + '/work/take.tsv.tmp'
    open(tmp, 'w').write(''.join(lines)); os.replace(tmp, a.take + '/take.tsv')
    print('kept', len(best), 'gain', repr(tot))
    if a.table:
        rows = {}
        for d in a.outs:
            for fn in sorted(os.listdir(d)):
                if fn.startswith('rows-') and fn.endswith('.tsv'):
                    for r in csv.DictReader(open(os.path.join(d, fn)), delimiter='\t'):
                        key = (int(r['target']), r['donor'], r['direction'], r['shells'])
                        if key not in rows or fs._side_of(r) < fs._side_of(rows[key]):
                            rows[key] = r
        with open(a.table + '.tmp', 'w') as h:
            h.write('target\tdonor\tdirection\tshells\treader\tgap_as_built\tafter_step\tafter_slp\tafter_squeeze\tbar\tdelta_vs_bar\tcertified\tstate\tchain\n')
            for key in sorted(rows):
                r = rows[key]
                tag = '%s-%s%sfrom%s' % (r['target'], r['direction'], r['shells'], r['donor'])
                c = cert.get(tag)
                cs = 'no' if c is None else ('yes' if c[0] else 'no (%s)' % c[2])
                try:
                    dv = '%.3e' % (float(r['after_squeeze']) - float(r['bar']))
                    dv = '' if dv == 'nan' else dv
                except ValueError:
                    dv = ''
                h.write('\t'.join([r['target'], r['donor'], r['direction'], r['shells'], r['reader'], r['gap'], r['after_step'],
                                   r['after_slp'], r['after_squeeze'], r['bar'], dv, cs, r['state'], r.get('chain') or '']) + '\n')
        os.replace(a.table + '.tmp', a.table)
        print('table', a.table, len(rows), 'rows')


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    q = sp.add_parser('read'); q.add_argument('sub'); q.add_argument('n', type=int, nargs='*'); q.set_defaults(fn=cmd_read)
    q = sp.add_parser('reach'); q.add_argument('sub'); q.add_argument('out'); q.set_defaults(fn=cmd_reach)
    q = sp.add_parser('ctl'); q.add_argument('sub'); q.add_argument('n', type=int); q.add_argument('out')
    q.add_argument('--iters', type=int, default=80); q.add_argument('--fq', action='store_true'); q.add_argument('--verbose', action='store_true')
    q.add_argument('--gapped', action='store_true')
    q.set_defaults(fn=cmd_ctl)
    q = sp.add_parser('walk'); q.add_argument('walks'); q.add_argument('donors'); q.add_argument('details'); q.add_argument('out')
    q.add_argument('--mod', default='1,0'); q.add_argument('--deadline'); q.add_argument('--iters', type=int, default=60)
    q.add_argument('--maxsteps', type=int, default=6); q.add_argument('--stopgap', type=float, default=4e-3)
    q.add_argument('--fqwin', type=float, default=2e-3); q.add_argument('--misses', type=int, default=2)
    q.add_argument('--min-progress', type=float, default=1e-7, help='side gain needed to reset misses; raw and near exports are unchanged')
    q.add_argument('--beat', nargs='*', default=[]); q.add_argument('--buildsec', type=float, default=600.0)
    q.add_argument('--nearout', type=float, default=0.015, help='save walk ends within this side gap in OUT/near (0 disables)')
    q.add_argument('--defer-list', default='defer.tsv', help='walk priorities to apply before fresh-layout searches')
    q.add_argument('--pick', type=int, default=0); q.set_defaults(fn=cmd_walk)
    q = sp.add_parser('trip'); q.add_argument('list'); q.add_argument('donors'); q.add_argument('details'); q.add_argument('out')
    q.add_argument('--mod', default='1,0'); q.add_argument('--deadline'); q.add_argument('--iters', type=int, default=60)
    q.add_argument('--twins', default='4e-2,5.5e-2,6.5e-2'); q.add_argument('--fqwin', type=float, default=2e-3)
    q.add_argument('--beat', nargs='*', default=[]); q.add_argument('--buildsec', type=float, default=600.0); q.set_defaults(fn=cmd_trip)
    q = sp.add_parser('band'); q.add_argument('list'); q.add_argument('donors'); q.add_argument('details'); q.add_argument('out')
    q.add_argument('--deadline'); q.add_argument('--iters', type=int, default=60); q.add_argument('--ctl', action='store_true')
    q.add_argument('--fqwin', type=float, default=2e-3); q.add_argument('--beat', nargs='*', default=[])
    q.add_argument('--buildsec', type=float, default=600.0); q.set_defaults(fn=cmd_band)
    q = sp.add_parser('take'); q.add_argument('details'); q.add_argument('take'); q.add_argument('outs', nargs='+')
    q.add_argument('--table'); q.add_argument('--sources'); q.add_argument('--beat', nargs='*', default=[]); q.set_defaults(fn=cmd_take)
    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
