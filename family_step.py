#!/usr/bin/env python3
# Credit required: reuse of this file, its layouts or its ideas must credit Sergio Fernández Rubio (GeiserX, https://github.com/GeiserX/squares-in-squares). See NOTICE and AI_NOTICE.md.
"""The exact shell step along a family line k - 2m = constant, with the collective re-tilt.

A held layout above n = 300 that is not the plain grid is two arms of tilted stacks on two neighbouring
walls plus an upright grid. With n = m^2 + k and side L = m + f, a stack is c unit squares in a row,
tilted by t so that it spans the arm: c cos t + sin t = c - 1 + f. Neighbour stacks touch along their
long sides, so the pitch along the wall is p = 1 / cos t.

  down  cut each arm between two stacks of its flush run and remove one stack, remove one grid row and
        one grid column, move everything beyond each cut in by exactly 1. That is 2m + 1 squares less,
        (m, k) -> (m - 1, k - 2), side L - 1 at the same f, legal as built, with a gap of p - 1 in
        each arm. Then the squeeze: the gap lets every flush stack tilt more, so the side falls by
        d = (p - 1) / (1 + s |dp/df| + Z) for s stacks in the arm, where Z is what the two end zones of
        the arm add (0 when they follow freely; measured median 2.3 to 3.4, avenues/family.md).
  up    the reverse: one more stack per arm, one more grid row and column. The new stack needs p of
        wall and the step gives 1, so the layout is opened by p first (a layout in a box L + p, at
        contact or up to 1.6e-2 inside a neighbour until the first exact LP), and the squeeze turns
        that room into tilt.

The squeeze is a sequential LP over every square (the two LPs of methods_lp: centres and angles
linearised, then the exact fixed-angle LP), accepted only when the exact LP returns a legal layout with
a smaller side. An upward step then alternates Evan Daniel's fq quench with the LP, because the LP
stops at jams that fq passes.

  family_step.py read  SUB.csv [N ...]                 what the reader sees, or why it refuses
  family_step.py ctl   SUB.csv DONOR TARGET OUTDIR     one step with every number and the load chain
  family_step.py plan  DETAILS.csv BOARD.json OUT.tsv DONORDIR TAG=FILE|DIR [...]
                                                       the ranked pairs; donors are copied to DONORDIR
  family_step.py run   PLAN.tsv DONORDIR DETAILS.csv OUTDIR --mod M,R [--deadline FILE] [--only up]
  family_step.py walk  WALKS.tsv DONORDIR DETAILS.csv OUTDIR --mod M,R [--deadline FILE]
                                                       one design carried shell after shell along its line
  family_step.py take  DETAILS.csv TAKEDIR OUTDIR [...] [--table T.tsv] [--sources S.tsv]
                                                       certify (floatsafe) and write the take layout

SUB.csv is a submission (id,n,square_id,x,y,angle) or a file of n,square_id,x,y,angle rows; angles in
radians. DETAILS.csv is the held file's n,L,score table. Our own code; it imports methods_lp,
frontier_stacks and floatsafe and calls the fq binary of Evan Daniel's MIT packer (SQ_FQ, or
SQ_BOX/ext/evand) when it is there. Reads data only: run with python -I.

Options by environment, all off by default: SQ_STRICT=1 keeps the wide reader off. SQ_LOOSE=1 lets the
wide reader take a wall with flush stacks but no two neighbours. SQ_APART=3e-2 repairs a start that
overlaps by up to that much (the default is 5e-3; an upward walk uses 3e-2 unless SQ_APART says otherwise).
SQ_WALLTOL=4e-2 lets the wide reader take a stack whose span or border distance is off by up to that much
(the default is 2e-2): a squeeze can leave one arm a few hundredths short of flush, as in the 795 that
boxA builds from the held 738. SQ_DRAW=1, 2 or 3 changes the order of the HiGHS solvers (a second draw of a build).
SQ_KEEPNEAR=1e-4 makes run keep the layout of a build that ends
less than that above the bar in OUTDIR/near, so another lane can polish it.

A walk reads each layout with read_any: the strict reader, the wide reader, then the wide reader with
the loose option. It writes every step's layout to OUTDIR/steps, so a later run can start from any of
them, and a line to OUTDIR/ends-R.tsv when it ends because a layout does not read. One build (a plan row
or a walk step) has a time limit, --buildsec (900 s): the LPs and fq get what is left of it, and the row
keeps the last legal layout with the state 'time limit'.
"""
import argparse, collections, csv, json, math, os, subprocess, sys, tempfile, time
csv.field_size_limit(50_000_000)

import numpy as np

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
import methods_lp as mlp  # noqa: E402
from frontier_stacks import stacks as chains_of  # noqa: E402

BOX = os.environ.get('SQ_BOX', '$SCRATCH/bounties-squares')
FQ = os.environ.get('SQ_FQ', os.path.join(BOX, 'ext/evand/search/packer/target/release/fq'))
POLISH = ['--no-alm', '--loosen', '1.0', '--flip-top', '64', '--pit', '600']
Q4 = math.pi / 4


class Unreadable(Exception):
    """The layout is not two clean arms and a grid; the message says what is in the way."""


# ---------------------------------------------------------------- files

def load(path, want=None):
    """-> {n: array (x, y, angle in radians)} in square_id order."""
    pz = collections.defaultdict(list)
    with open(path, newline='') as h:
        for r in csv.DictReader(h):
            n = int(r['n'])
            if want is None or n in want:
                pz[n].append((int(r['square_id']), float(r['x']), float(r['y']), float(r['angle'])))
    return {n: np.array([v[1:] for v in sorted(rows)]) for n, rows in pz.items()}


def write_rows(path, n, P):
    tmp = path + '.tmp'
    with open(tmp, 'w', newline='') as g:
        w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for k, (x, y, th) in enumerate(P):
            w.writerow([n, k, repr(float(x)), repr(float(y)), repr(float(th))])
    os.replace(tmp, path)


# ---------------------------------------------------------------- geometry

def fold(th):
    t = np.mod(th, math.pi / 2)
    return np.where(t > Q4, t - math.pi / 2, t)


def canon(P):
    """Box at the origin, angles folded to (-45, 45] degrees. -> side, array."""
    Q = np.array(P, float)
    Q[:, 2] = fold(Q[:, 2])
    h = mlp.half(Q[:, 2])
    Q[:, 0] -= (Q[:, 0] - h).min(); Q[:, 1] -= (Q[:, 1] - h).min()
    return float(mlp.side(Q)), Q


def turned(Q, s, op):
    """A symmetry of the box: 'T' swaps x and y, 'X' mirrors x, 'Y' mirrors y."""
    R = Q.copy()
    if op == 'T':
        R[:, 0], R[:, 1], R[:, 2] = Q[:, 1], Q[:, 0], fold(math.pi / 2 - Q[:, 2])
    elif op == 'X':
        R[:, 0], R[:, 2] = s - Q[:, 0], fold(-Q[:, 2])
    elif op == 'Y':
        R[:, 1], R[:, 2] = s - Q[:, 1], fold(-Q[:, 2])
    return R


def tilt_of(c, f):
    """The flush tilt: c cos t + sin t = c - 1 + f, the root below atan(1/c) is not the one; take t > atan(1/c)."""
    lo, hi = math.atan(1.0 / c), Q4 * 1.999
    g = lambda t: c * math.cos(t) + math.sin(t) - (c - 1 + f)
    if g(lo) < 0:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if g(mid) > 0: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def squeeze_d(c, f, s):
    """How far f falls when a gap of p - 1 is shared by s flush stacks of c: (p - 1) / (1 + s |dp/df|)."""
    t = tilt_of(c, f)
    p = 1 / math.cos(t)
    dpdf = (math.sin(t) / math.cos(t) ** 2) / (math.cos(t) - c * math.sin(t))
    return (p - 1) / (1 + s * abs(dpdf)), p, t, dpdf


# ---------------------------------------------------------------- read

def _flush_stacks(Q, s, m):
    f = s - m
    deg = np.degrees(Q[:, 2])
    tl = np.nonzero(np.abs(deg) > 0.5)[0]
    if len(tl) < 12:
        raise Unreadable('%d tilted squares: no arm' % len(tl))
    T = np.column_stack([Q[tl, 0], Q[tl, 1], deg[tl]])
    chains, _ = chains_of(T)
    walls = collections.defaultdict(list)
    for ch in chains:
        c = len(ch)
        if c < 5:
            continue
        th = math.radians(float(np.median(T[ch, 2])))
        t = abs(th)
        if abs(c * math.cos(t) + math.sin(t) - (c - 1 + f)) > 3e-3:
            continue
        ax = T[ch[-1], :2] - T[ch[0], :2]
        cen = T[ch, :2].mean(0); W = c - 1 + f
        if abs(ax[0]) > abs(ax[1]):
            wall = 'L' if cen[0] < W / 2 + 0.05 else 'R' if cen[0] > s - W / 2 - 0.05 else None
        else:
            wall = 'B' if cen[1] < W / 2 + 0.05 else 'T' if cen[1] > s - W / 2 - 0.05 else None
        if wall:
            walls[wall].append(dict(idx=tl[np.array(ch)], c=c, th=th, cen=cen))
    return walls, len(tl)


def _run(stk, axis, p):
    """The longest run of neighbour stacks one pitch apart with one tilt. -> (first, last) in the sorted list.

    The tolerances (4e-3 of pitch and of place, 0.17 degree of tilt) admit an arm that is a little loose
    (n = 747: twelve stacks of 10 at 18.17 to 18.27 degrees, 1e-3 apart). The step itself is checked
    exactly afterwards, so a loose run costs nothing."""
    best = (0, 0); a = 0
    for i in range(1, len(stk) + 1):
        pp = p if p is not None or i >= len(stk) else 1 / math.cos((stk[i]['th'] + stk[i - 1]['th']) / 2)
        ok = i < len(stk) and abs(stk[i]['cen'][axis] - stk[i - 1]['cen'][axis] - pp) < 4e-3 \
            and abs(stk[i]['cen'][1 - axis] - stk[i - 1]['cen'][1 - axis]) < 4e-3 \
            and abs(stk[i]['th'] - stk[i - 1]['th']) < 3e-3
        if not ok:
            if i - 1 - a > best[1] - best[0]:
                best = (a, i - 1)
            a = i
    return best


def read(P, n, wide=True):
    """-> dict with the turned layout (arm 1 on the left wall, arm 2 on the bottom wall) or Unreadable.

    The strict reader first (two whole flush arms). Where it refuses, the wide reader: it asks only for two
    neighbouring stacks of one tilt on each of two neighbouring walls. Neither guesses: the step that
    follows is checked by its count, its side and its smallest gap."""
    try:
        return read_strict(P, n)
    except Unreadable as ex:
        if not wide or os.environ.get('SQ_STRICT') or 'plain grid' in str(ex):
            raise
        first = str(ex)
    try:
        return read_wide(P, n)
    except Unreadable as ex:
        raise Unreadable('%s; wide reader: %s' % (first, ex))


def read_any(P, n):
    """read(), and where it refuses a tilted layout, the wide reader with the loose option on."""
    try:
        return read(P, n)
    except Unreadable as ex:
        if os.environ.get('SQ_STRICT') or 'plain grid' in str(ex):
            raise
        first = str(ex)
    try:
        return read_wide(P, n, loose=True)
    except Unreadable as ex:
        raise Unreadable('%s; loose: %s' % (first, ex))


def _wall_stacks(Q, s, m, tol=2e-2, bmax=2):
    """Every stack of 5 or more squares that spans a strip of width c - 1 + f (to tol) set b whole squares
    from a wall, b = 0 .. bmax. -> {wall: [stack]}, tilted squares. SQ_WALLTOL widens tol."""
    tol = max(tol, float(os.environ.get('SQ_WALLTOL') or 0))
    f = s - m
    deg = np.degrees(Q[:, 2])
    tl = np.nonzero(np.abs(deg) > 0.5)[0]
    if len(tl) < 10:
        raise Unreadable('%d tilted squares: no arm' % len(tl))
    T = np.column_stack([Q[tl, 0], Q[tl, 1], deg[tl]])
    chains, _ = chains_of(T)
    walls = collections.defaultdict(list)
    for ch in chains:
        c = len(ch)
        if c < 5:
            continue
        th = math.radians(float(np.median(T[ch, 2]))); t = abs(th)
        if abs(c * math.cos(t) + math.sin(t) - (c - 1 + f)) > tol:
            continue
        idx = tl[np.array(ch)]; hh = mlp.half(Q[idx, 2])
        ax = T[ch[-1], :2] - T[ch[0], :2]
        k = 0 if abs(ax[0]) > abs(ax[1]) else 1          # the stack lies along x (wall L or R) or along y (B or T)
        lo = float((Q[idx, k] - hh).min()); hi = float((Q[idx, k] + hh).max())
        for wall, d in ((('L', 'B')[k], lo), (('R', 'T')[k], s - hi)):
            b = int(round(d))
            if 0 <= b <= bmax and abs(d - b) < tol:
                walls[wall].append(dict(idx=idx, c=c, th=th, cen=Q[idx, :2].mean(0), b=b))
    return walls, len(tl)


def _best_run(stk, axis):
    """The longest run of neighbour stacks over the groups of one size and one border. -> (run, group size)"""
    groups = collections.defaultdict(list); best = None
    for a in stk:
        groups[(a['c'], a['b'])].append(a)
    for key in sorted(groups):
        g = sorted(groups[key], key=lambda a: a['cen'][axis])
        a, b = _run(g, axis, None)
        if best is None or b - a + 1 > len(best[0]):
            best = (g[a:b + 1], len(g))
    return best


def read_wide(P, n, loose=None):
    """The wide reader: on each of two neighbouring walls, two or more neighbouring stacks of one size and
    one tilt, one pitch apart, that span a strip from the wall (or from b whole border lines of upright
    squares at the wall) to the grid. Other stacks on the wall are left to the end zones.

    loose=True (or SQ_LOOSE=1) also takes a wall that has flush stacks but no two neighbours: its "run" is
    then every flush stack of its most common size, and the step tries the cut at five of them. One flush
    stack with clean faces is all a cut needs; the checks of the step decide."""
    loose = bool(os.environ.get('SQ_LOOSE')) if loose is None else loose
    s, Q = canon(P)
    m = int(math.floor(s + 1e-9)); f = s - m; k = n - m * m
    if f < 1e-6:
        raise Unreadable('plain grid')
    walls, ntilt = _wall_stacks(Q, s, m)
    def run_of(v, axis):
        r = _best_run(v, axis)
        if r and len(r[0]) >= 2:
            return r
        if loose and v:
            groups = collections.Counter((a['c'], a['b']) for a in v)
            key = max(sorted(groups), key=lambda k: groups[k])
            g = sorted((a for a in v if (a['c'], a['b']) == key), key=lambda a: a['cen'][axis])
            return (g, len(g))
        return None
    runs = {}
    for w, v in walls.items():
        r = run_of(v, 1 if w in 'LR' else 0)
        if r:
            runs[w] = r
    if loose and len(runs) > 2:                     # a loose wall only where a wall with a real pair needs a partner
        tight = {w for w, v in walls.items() if (_best_run(v, 1 if w in 'LR' else 0) or ([],))[0].__len__() >= 2}
        for group in ('LR', 'BT'):
            if any(w in tight for w in group):
                for w in group:
                    if w not in tight:
                        runs.pop(w, None)
    side = [w for w in 'LR' if w in runs]; base = [w for w in 'BT' if w in runs]
    if not side or not base:
        raise Unreadable('no two neighbouring walls with a pair of neighbouring stacks (walls with a pair: %s)' % (''.join(sorted(runs)) or '-'))
    w1 = max(side, key=lambda w: len(runs[w][0])); w2 = max(base, key=lambda w: len(runs[w][0]))
    ops = ''
    if w1 == 'R':
        Q = turned(Q, s, 'X'); ops += 'X'
    if w2 == 'T':
        Q = turned(Q, s, 'Y'); ops += 'Y'
    walls, _ = _wall_stacks(Q, s, m)
    r1 = run_of(walls.get('L', []), 1); r2 = run_of(walls.get('B', []), 0)
    if not r1 or not r2:
        raise Unreadable('arms lost after the turn')
    c1, c2 = r1[0][0]['c'], r2[0][0]['c']; b1, b2 = r1[0][0]['b'], r2[0][0]['b']
    W1, W2 = c1 - 1 + f, c2 - 1 + f; E1, E2 = b1 + W1, b2 + W2
    out = dict(n=n, s=s, m=m, k=k, f=f, Q=Q, ops=ops, c=(c1, c2), W=(W1, W2), E=(E1, E2), b=(b1, b2), wide=True,
               tilted=ntilt, arms=[])
    for (run, nfl), axis in ((r1, 1), (r2, 0)):
        th = float(np.median([a['th'] for a in run])); p = 1 / math.cos(th)
        out['arms'].append(dict(axis=axis, c=run[0]['c'], th=th, p=p, run=run, nflush=nfl,
                                lo=run[0]['cen'][axis] - p / 2, hi=run[-1]['cen'][axis] + p / 2))
    inA = Q[:, 0] < E1; inlowB = Q[:, 1] < E2
    up = np.abs(Q[:, 2]) < math.radians(0.5)
    rows, cols = {}, {}
    for j in range(m):
        y = s - 0.5 - j
        if y > E2:
            q = np.nonzero(~inA & (np.abs(Q[:, 1] - y) < 0.25))[0]
            if len(q) == m - b1 - c1 + 1 and up[q].all():
                rows[j] = q
        if y > E1:
            q = np.nonzero(~inlowB & (np.abs(Q[:, 0] - y) < 0.25))[0]
            if len(q) == m - b2 - c2 + 1 and up[q].all():
                cols[j] = q
    out['rows'], out['cols'] = rows, cols
    # the border lines: upright squares in whole columns at the wall of arm 1, whole rows at the wall of arm 2
    out['border'] = ([np.nonzero(up & (np.abs(Q[:, 0] - (i + 0.5)) < 0.25))[0] for i in range(b1)],
                     [np.nonzero(up & (np.abs(Q[:, 1] - (i + 0.5)) < 0.25))[0] for i in range(b2)])
    pt = _parts(out)
    out['zones'] = dict(corner=int(pt['corner'].sum()), cap1=int(pt['cap1'].sum()), cap2=int(pt['cap2'].sum()))
    if not rows or not cols:
        raise Unreadable('no full grid row or column (%d rows, %d columns)' % (len(rows), len(cols)))
    return out


def read_strict(P, n):
    """The strict reader: two whole arms of flush stacks, each with a run of three or more."""
    s, Q = canon(P)
    m = int(math.floor(s + 1e-9)); f = s - m; k = n - m * m
    if f < 1e-6:
        raise Unreadable('plain grid')
    walls, ntilt = _flush_stacks(Q, s, m)
    arms = {w: v for w, v in walls.items() if len(v) >= 3}
    if len(arms) < 2:
        raise Unreadable('%d arm(s) of flush stacks (walls %s)' % (len(arms), ''.join(sorted(walls)) or '-'))
    if len(arms) > 2:
        raise Unreadable('more than two arms (walls %s)' % ''.join(sorted(arms)))
    for w, v in arms.items():
        cs = sorted(set(a['c'] for a in v))
        if len(cs) > 1:
            raise Unreadable('arm on wall %s has two stack sizes %s' % (w, cs))
    w1, w2 = sorted(arms, key=lambda w: -len(arms[w]))
    if (w1 in 'LR') == (w2 in 'LR'):
        raise Unreadable('the two arms are on opposite walls %s%s' % (w1, w2))
    ops = ''
    if w1 in 'BT':
        Q = turned(Q, s, 'T'); ops += 'T'
        sw = {'B': 'L', 'T': 'R', 'L': 'B', 'R': 'T'}; w1, w2 = sw[w1], sw[w2]
    if w1 == 'R':
        Q = turned(Q, s, 'X'); ops += 'X'
    if w2 == 'T':
        Q = turned(Q, s, 'Y'); ops += 'Y'
    walls, _ = _flush_stacks(Q, s, m)
    if len(walls.get('L', [])) < 3 or len(walls.get('B', [])) < 3:
        raise Unreadable('arms lost after the turn')
    A1 = sorted(walls['L'], key=lambda a: a['cen'][1]); A2 = sorted(walls['B'], key=lambda a: a['cen'][0])
    c1, c2 = A1[0]['c'], A2[0]['c']
    W1, W2 = c1 - 1 + f, c2 - 1 + f
    out = dict(n=n, s=s, m=m, k=k, f=f, Q=Q, ops=ops, c=(c1, c2), W=(W1, W2), E=(W1, W2), b=(0, 0), wide=False,
               border=([], []), tilted=ntilt, arms=[])
    for stk, axis in ((A1, 1), (A2, 0)):
        th = float(np.median([a['th'] for a in stk])); p = 1 / math.cos(th)
        a, b = _run(stk, axis, p)
        if b - a + 1 < 3:
            raise Unreadable('arm %d: flush run of %d stack(s) (of %d flush stacks)' % (2 - axis, b - a + 1, len(stk)))
        run = stk[a:b + 1]
        for q in run:   # each spans wall to grid
            hh = mlp.half(Q[q['idx'], 2])
            lo = (Q[q['idx'], 1 - axis] - hh).min(); hi = (Q[q['idx'], 1 - axis] + hh).max()
            if lo > 5e-3 or abs(hi - (q['c'] - 1 + f)) > 6e-3:
                raise Unreadable('arm %d: a stack of the run spans %.4f to %.4f, not wall to grid' % (2 - axis, lo, hi))
        out['arms'].append(dict(axis=axis, c=run[0]['c'], th=th, p=p, run=run, nflush=len(stk),
                                lo=run[0]['cen'][axis] - p / 2, hi=run[-1]['cen'][axis] + p / 2))
    # the grid: full rows beside arm 1 and full columns above arm 2, on the lattice of the far corner
    inA = Q[:, 0] < W1; inlowB = Q[:, 1] < W2
    up = np.abs(Q[:, 2]) < math.radians(0.5)
    rows, cols = {}, {}
    for j in range(m):
        y = s - 0.5 - j
        if y > W2:
            q = np.nonzero(~inA & (np.abs(Q[:, 1] - y) < 0.25))[0]
            if len(q) == m - c1 + 1 and up[q].all():
                rows[j] = q
        if y > W1:
            q = np.nonzero(~inlowB & (np.abs(Q[:, 0] - y) < 0.25))[0]
            if len(q) == m - c2 + 1 and up[q].all():
                cols[j] = q
    out['rows'], out['cols'] = rows, cols
    pt = _parts(out)
    out['zones'] = dict(corner=int(pt['corner'].sum()), cap1=int(pt['cap1'].sum()), cap2=int(pt['cap2'].sum()))
    if not rows or not cols:
        raise Unreadable('no full grid row or column (%d rows, %d columns)' % (len(rows), len(cols)))
    return out


def describe(R):
    a1, a2 = R['arms']
    return ('n=%d m=%d k=%d f=%.6f line=%d c=%d,%d tilt=%.3f,%.3f run=%d,%d (flush %d,%d) rows=%d/%d cols=%d/%d '
            'corner=%d cap1=%d cap2=%d%s' % (
                R['n'], R['m'], R['k'], R['f'], R['k'] - 2 * R['m'], a1['c'], a2['c'], math.degrees(abs(a1['th'])),
                math.degrees(abs(a2['th'])), len(a1['run']), len(a2['run']), a1['nflush'], a2['nflush'],
                len(R['rows']), R['m'] - a2['c'] + 1, len(R['cols']), R['m'] - a1['c'] + 1,
                R['zones']['corner'], R['zones']['cap1'], R['zones']['cap2'],
                ' wide border=%d,%d' % R['b'] if R.get('wide') else ''))


# ---------------------------------------------------------------- the step

def _cuts(R, where=0.5):
    """The stack of each run at the cut, and the grid row / column that goes with it."""
    Q, s = R['Q'], R['s']; a1, a2 = R['arms']
    j1 = a1['run'][min(len(a1['run']) - 2, max(1, int(len(a1['run']) * where)))]
    j2 = a2['run'][min(len(a2['run']) - 2, max(1, int(len(a2['run']) * where)))]

    def nearest(d, v):
        ok = [j for j in d if (j - 1 in d or j == 0) and j + 1 in d]
        if not ok:
            raise Unreadable('no grid line with full neighbours at the cut')
        j = min(ok, key=lambda j: abs(s - 0.5 - j - v))
        if abs(s - 0.5 - j - v) > float(os.environ.get('SQ_CUTREACH') or 3.0):   # round 21: SQ_CUTREACH widens it
            raise Unreadable('the nearest full grid line is %.1f from the cut' % abs(s - 0.5 - j - v))
        return j
    r = nearest(R['rows'], j1['cen'][1]); q = nearest(R['cols'], j2['cen'][0])
    # a border line loses (or gains) the square beside the wall end of the cut stack
    bc = ([], [])
    for arm, j, lines in ((0, j1, R['border'][0]), (1, j2, R['border'][1])):
        end = j['idx'][np.argmin(Q[j['idx'], arm])]
        for li, line in enumerate(lines):
            if not len(line):
                raise Unreadable('arm %d: a border line has no upright squares' % (arm + 1))
            i = line[np.argmin(np.abs(Q[line, 1 - arm] - Q[end, 1 - arm]))]
            if abs(Q[i, 1 - arm] - Q[end, 1 - arm]) > 1.0 and os.environ.get('SQ_STAIRCUT'):
                # round 21: beside a staircase run the border line holds tilted squares, one per stack at the
                # pitch; the cut takes the one beside the wall end of the cut stack, at any angle
                col = np.nonzero((np.abs(Q[:, arm] - (li + 0.5)) < 0.3) & (Q[:, arm] < R['b'][arm]))[0]
                if len(col):
                    i = col[np.argmin(np.abs(Q[col, 1 - arm] - Q[end, 1 - arm]))]
            if abs(Q[i, 1 - arm] - Q[end, 1 - arm]) > 1.0:
                raise Unreadable('arm %d: no border square beside the cut' % (arm + 1))
            bc[arm].append(int(i))
    R['bcut'] = bc
    return j1, j2, r, q


def _beyond(R, j1, j2, r, q):
    """Which squares are beyond cut 1 (they move in y) and beyond cut 2 (they move in x)."""
    Q, s = R['Q'], R['s']; W1, W2 = R['E']
    yr, xq = s - 0.5 - r, s - 0.5 - q
    inA = Q[:, 0] < W1; lowB = Q[:, 1] < W2
    d1 = (Q[:, 0] - j1['cen'][0]) * -math.sin(j1['th']) + (Q[:, 1] - j1['cen'][1]) * math.cos(j1['th'])
    d2 = (Q[:, 0] - j2['cen'][0]) * math.cos(j2['th']) + (Q[:, 1] - j2['cen'][1]) * math.sin(j2['th'])
    b1 = np.where(inA, d1 > 0.5, Q[:, 1] > yr + 0.25)
    b2 = np.where(lowB, d2 > 0.5, Q[:, 0] > xq + 0.25)
    for i in R['bcut'][0]:                        # a border line is cut at its own square
        line = (np.abs(Q[:, 0] - Q[i, 0]) < 0.25) & (Q[:, 0] < R['b'][0])
        b1[line] = Q[line, 1] > Q[i, 1] + 0.5
    for i in R['bcut'][1]:
        line = (np.abs(Q[:, 1] - Q[i, 1]) < 0.25) & (Q[:, 1] < R['b'][1])
        b2[line] = Q[line, 0] > Q[i, 0] + 0.5
    return b1, b2, d1, d2


def down(R, where=0.5):
    """The shell-down step. -> (array of n - 2m - 1 squares in a box of side s - 1, info)."""
    Q, s, m = R['Q'], R['s'], R['m']
    j1, j2, r, q = _cuts(R, where)
    b1, b2, _, _ = _beyond(R, j1, j2, r, q)
    gone = np.zeros(len(Q), bool)
    gone[j1['idx']] = True; gone[j2['idx']] = True; gone[R['rows'][r]] = True; gone[R['cols'][q]] = True
    gone[R['bcut'][0] + R['bcut'][1]] = True
    if gone.sum() != 2 * m + 1:
        raise Unreadable('the cut removes %d squares, not 2m + 1 = %d' % (gone.sum(), 2 * m + 1))
    G = Q.copy()
    G[b1, 1] -= 1.0; G[b2, 0] -= 1.0
    G = G[~gone]
    side, G = canon(G)
    g = mlp.min_gap(G)
    if abs(side - (s - 1)) > 1e-7 or g < -1.5e-2:    # a loose arm can leave 1e-2 of overlap; the exact LP repairs it or refuses
        raise Unreadable('the cut is not clean: side %.9f (want %.9f), smallest gap %.2e' % (side, s - 1, g))
    return G, dict(side=side, gap=g, row=r, col=q, y1=float(j1['cen'][1]), x2=float(j2['cen'][0]), lab=zone_labels(R, 'down', j1, j2, r, q),
                   gone=gone, map=np.cumsum(~gone) - 1)


def up(R, where=0.5):
    """The shell-up step, opened by the pitch: one more stack per arm, one more grid row and column.

    Everything beyond cut 1 moves out by p1 in the arm strip and by 1 in the grid, likewise cut 2, and
    the far part of the grid is pushed out to the far walls. The box is then s + max(p1, p2). The start
    is at contact or overlaps (measured on 178 starts: none with a positive gap, 84 overlap, the worst by
    1.6e-2); the first exact LP of the squeeze makes it legal, and the squeeze takes the p - 1 back."""
    Q, s, m = R['Q'], R['s'], R['m']; a1, a2 = R['arms']
    j1, j2, r, q = _cuts(R, where)
    b1, b2, d1, d2 = _beyond(R, j1, j2, r, q)
    p1, p2 = a1['p'], a2['p']; pm = max(p1, p2)
    G = Q.copy()
    # arm strips: beyond the cut by the pitch (then the cap is pushed to the far wall of the bigger box);
    # grid and border lines: beyond the cut by pm as well, so the grid stays on the lattice of the far corner
    G[b1, 1] += pm; G[b2, 0] += pm
    new = []
    for i in j1['idx']:
        new.append((Q[i, 0], Q[i, 1] + p1, Q[i, 2]))
    for i in j2['idx']:
        new.append((Q[i, 0] + p2, Q[i, 1], Q[i, 2]))
    # A grid line can sit off the lattice by a few hundredths (n = 875: the column beside the arm is 0.089
    # low), so every new square is the copy of its own neighbour, one unit on.
    for i in R['rows'][r]:
        new.append((G[i, 0], Q[i, 1] + 1.0, Q[i, 2]))          # the row above row r, x as moved by cut 2
    for i in R['cols'][q]:
        new.append((Q[i, 0] + 1.0, G[i, 1], Q[i, 2]))          # the column right of column q, y as moved by cut 1
    cross = [i for i in R['rows'][r] if i in set(R['cols'][q].tolist())]
    if len(cross) != 1:
        raise Unreadable('row and column of the cut share %d squares' % len(cross))
    new.append((Q[cross[0], 0] + 1.0, Q[cross[0], 1] + 1.0, Q[cross[0], 2]))   # the crossing
    for i in R['bcut'][0]:
        new.append((G[i, 0], Q[i, 1] + 1.0, Q[i, 2]))          # one more square in each border line
    for i in R['bcut'][1]:
        new.append((Q[i, 0] + 1.0, G[i, 1], Q[i, 2]))
    # pm > 1 leaves a slit of pm - 1 beyond the new row and the new column, which the squeeze closes.
    G = np.vstack([G, np.array(new)])
    if len(G) != len(Q) + 2 * m + 3:
        raise Unreadable('the step adds %d squares, not 2m + 3 = %d' % (len(G) - len(Q), 2 * m + 3))
    side, G = canon(G)
    g = mlp.min_gap(G)
    # A grid block that is off the lattice near an arm leaves the copies up to 1.3e-2 inside a neighbour
    # (975 from 912). The exact LP of the squeeze repairs that in one solve; beyond 3e-2 (or SQ_APART, when
    # it asks more) the step is refused.
    if g < -max(3e-2, float(os.environ.get('SQ_APART') or 0)):
        raise Unreadable('the opened layout overlaps: smallest gap %.2e at side %.6f' % (g, side))
    return G, dict(side=side, gap=g, row=r, col=q, y1=float(j1['cen'][1]), x2=float(j2['cen'][0]), lab=zone_labels(R, 'up', j1, j2, r, q))


def build(R, direction, where0=0.5):
    """The step at the middle of the runs (or at where0); where that cut is refused, at four other places
    along the runs. A layout the strict reader accepts takes the middle cut as before. -> (array, info)"""
    first = None
    for where in [where0] + [w for w in (0.5, 0.3, 0.7, 0.1, 0.9) if w != where0]:
        try:
            return down(R, where) if direction == 'down' else up(R, where)
        except Unreadable as ex:
            first = first or ex
    raise first


def swap_far(G, info, Rd, Pt, nt, turn=False):
    """The far zone of each arm of an opened layout replaced by the target's own far zone.

    An upward step can jam because the donor's far ends do not fit the target's f (814 -> 873 stays
    0.0113 above held; with the swap it ends 9.4e-5 below). The far end is the free end of an arm, so the
    held target's far zone goes in whole, at its own distance from the far wall. G and info come from
    up() or down(). The two zones must hold the same squares to within whole
    stacks of the run; the stacks that make up the difference go with the zone. turn=True gives the
    target's arm 2 to the donor's arm 1. The result overlaps its neighbours (3.4e-2 on 814 -> 873), so
    every centre is moved apart and the exact LP takes the room back. -> legal array or Unreadable."""
    Rt = read(Pt, nt)
    lab = np.array(info['lab'], dtype=object); SG = info['side']
    parts = _parts(Rt); TQ = Rt['Q']
    tz = [(parts['cap1'], Rt['arms'][0]), (parts['cap2'], Rt['arms'][1])]
    if turn:
        TQ = turned(TQ, Rt['s'], 'T'); tz = tz[::-1]
    G2 = G.copy()
    for arm in (0, 1):
        capmask, tarm = tz[arm]
        c = Rd['arms'][arm]['c']
        if tarm['c'] != c:
            raise Unreadable('far-zone swap: arm %d has stacks of %d, the target of %d' % (arm + 1, c, tarm['c']))
        dcap = np.nonzero(lab == ('cap1', 'cap2')[arm])[0]; tcap = np.nonzero(capmask)[0]
        kd = kt = 0
        while len(dcap) + c * kd != len(tcap) + c * kt:
            if len(dcap) + c * kd < len(tcap) + c * kt:
                kd += 1
            else:
                kt += 1
            if kd + kt > 3:
                raise Unreadable('far-zone swap: the far zones of arm %d (%d and %d squares) do not differ by whole stacks' % (
                    arm + 1, len(dcap), len(tcap)))
        drun = Rd['arms'][arm]['run']; trun = tarm['run']
        if kd >= len(drun) - 1 or kt >= len(trun) - 1:
            raise Unreadable('far-zone swap: the run of arm %d is too short' % (arm + 1))
        dmore = [i for st in (drun[len(drun) - kd:] if kd else []) for i in st['idx']]
        if 'gone' in info:                            # a downward step: the squares have new places in the array
            if info['gone'][dmore].any():
                raise Unreadable('far-zone swap: the cut stack of arm %d is one of the stacks to swap' % (arm + 1))
            dmore = [int(info['map'][i]) for i in dmore]
        didx = list(dcap) + dmore
        tidx = list(tcap) + [i for st in (trun[len(trun) - kt:] if kt else []) for i in st['idx']]
        X = TQ[tidx].copy()
        X[:, 1 - arm] += SG - Rt['s']                 # the same distance from the far wall
        G2[didx] = X
    side, G2 = canon(G2)
    if mlp.min_gap(G2) < 2.5e-11:
        A = _apart(G2, most=8e-2)
        if A is None:
            raise Unreadable('far-zone swap: the swapped layout overlaps by %.2e' % -mlp.min_gap(G2))
        La = float(mlp.side(A))
        for _ in range(80):
            Q, LQ = _lp_exact(A, tr_c=0.1)
            if Q is None or not (LQ < La - 1e-7):
                break
            A, La = Q, LQ
        G2 = A
    return G2


# ---------------------------------------------------------------- the squeeze

def fq_quench(s, P, flags=(), timeout=900):
    """Evan Daniel's fq on (side, squares). -> (side, array) or (None, None)."""
    if not os.path.exists(FQ):
        return None, None
    left = _left()
    if left is not None:
        if left <= 0:
            return None, None
        timeout = min(timeout, max(5.0, left))
    d = tempfile.mkdtemp(prefix='fam', dir=os.environ.get('SQ_TMP'))
    a, b = d + '/a.txt', d + '/b.txt'
    with open(a, 'w') as h:
        h.write('%d %r\n' % (len(P), float(s)))
        for x, y, th in P:
            h.write('%r %r %r\n' % (float(x), float(y), math.degrees(float(th))))
    out = (None, None)
    try:
        r = subprocess.run([FQ, 'quench', '--in', a, '--out', b] + list(flags), capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0 and os.path.exists(b):
            L = [l.split() for l in open(b) if l.strip() and not l.startswith('#')]
            k = int(L[0][0])
            X = np.array([[float(v) for v in q[:3]] for q in L[1:k + 1]]); X[:, 2] = np.radians(X[:, 2])
            out = (float(L[0][1]), X)
    except subprocess.TimeoutExpired:
        pass
    for p_ in (a, b):
        if os.path.exists(p_): os.remove(p_)
    os.rmdir(d)
    return out


_METHOD = ['highs']
_LIMIT = {'end': None}      # the wall-clock end of the build in hand; run and walk set it per build


def set_limit(seconds):
    """Give the build that starts now `seconds` of wall clock (None: no limit)."""
    _LIMIT['end'] = None if not seconds else time.time() + seconds


def _left():
    """Seconds left of the build in hand, or None when it has no limit."""
    return None if _LIMIT['end'] is None else _LIMIT['end'] - time.time()


def _over():
    left = _left()
    return left is not None and left <= 0


def _linprog(cost, **kw):
    kw['method'] = _METHOD[0]
    left = _left()
    if left is not None:                   # HiGHS stops at the end of the build and the caller gets None
        kw['options'] = dict(kw.get('options') or {}, time_limit=max(1.0, left))
    res = _scipy_linprog(cost, **kw)
    _LAST['res'] = res
    return res


from scipy.optimize import linprog as _scipy_linprog  # noqa: E402
# methods_lp asks a gap of 4e-11 of an LP that HiGHS solves to 1e-10, so its exact step can come back
# 1e-10 inside a neighbour and its own 2.5e-11 check then rejects the whole move (measured on the gapped
# 757: every step rejected). Here, in this process only, the LP asks 2e-10 and the angle LP runs on the
# interior point solver (5 s against 9 to 47 s at n = 757). methods_lp.py itself is not changed.
mlp.GAP = 2e-10
mlp.linprog = _linprog


def _orders():
    """The HiGHS solver order of the angle LP and of the exact LP. SQ_DRAW=1, 2 or 3 changes it (ds first for
    the angles; ipm first for the exact LP; both): each picks other optimal vertices where the LP has several,
    so the sequential LP takes another path. A second draw of a near miss on the same scipy."""
    k = int(os.environ.get('SQ_DRAW') or 0)
    return (('highs-ds', 'highs-ipm') if k in (1, 3) else ('highs-ipm', 'highs-ds'),
            ('highs-ipm', 'highs', 'highs-ds') if k in (2, 3) else ('highs', 'highs-ipm', 'highs-ds'))


def _lp_angles(P, tr_a, tr_c=0.02):
    for meth in _orders()[0]:
        if _over():
            return None
        _METHOD[0] = meth
        try:
            Q = mlp.solve(P, tr_c, tr_a)
        except Exception:
            Q = None
        finally:
            _METHOD[0] = 'highs'
        if Q is not None:
            return Q
    return None


def legal(P, want=6e-11):
    """HiGHS can leave a pair 1e-10 to 3e-10 inside its neighbour. Scale the centres apart by that much
    (the cost is under 1e-8 of side); refuse anything worse. -> array or None."""
    g = mlp.min_gap(P)
    if g >= 2.5e-11:
        return P
    if g < -2e-8:
        return None
    Q = P.copy(); c = Q[:, :2].mean(0)
    Q[:, :2] = c + (Q[:, :2] - c) * (1 + (want - g) * 1.5)
    return Q if mlp.min_gap(Q) >= 2.5e-11 else None


def _apart(P, most=5e-3):
    """Scale the centres apart until no pair overlaps: a legal start in a box up to about 1% larger, for a
    step whose small overlap the exact LP does not repair. -> array or None."""
    if mlp.min_gap(P) < -most:
        return None
    Q = P.copy(); c = Q[:, :2].mean(0)
    for _ in range(12):
        g = mlp.min_gap(Q)
        if g >= 2.5e-11:
            return canon(Q)[1]
        Q[:, :2] = c + (Q[:, :2] - c) * (1 + 2.0 * max(-g, 1e-10))
    return None


def _solve_exact(P, tr_c):
    """The exact LP by three trust radii and every HiGHS solver. The HiGHS of scipy 1.13 ends 'unknown'
    (status 15) on one combination of an overlapping start and solves the next; a legal start is solved
    by the first."""
    for tr in (tr_c, 2.5 * tr_c, 6.25 * tr_c):
        for meth in _orders()[1]:
            if _over():
                return None
            _METHOD[0] = meth
            try:
                Q = mlp.solve(P, tr, 0.0)
            except Exception:
                Q = None
            finally:
                _METHOD[0] = 'highs'
            if Q is not None:
                return Q
    return None


def _lp_exact(P, tr_c=0.02, rounds=3):
    """Fixed-angle LP (exact): the smallest box for these angles and these separating axes, or None."""
    for _ in range(rounds):
        Q = _solve_exact(P, tr_c)
        if Q is None:
            return None, None
        P = Q
        Q = legal(P)
        if Q is not None:
            return Q, float(mlp.side(Q))
    return None, None


def squeeze(G, iters=60, log=None, fq=True, tr_a=2e-3, stop=None, apart=None):
    """Sequential LP over every square from a legal start, then the fq polish. -> (array, side, trace)

    One step: an LP over the centre and the angle of every square with the gaps linearised (the stacks of
    an arm turn together in it, because two squares face to face can only turn together), then the exact
    fixed-angle LP at the new angles. A step counts only when the exact LP returns a legal layout with a
    smaller side, so every stage is a legal layout. apart: the largest overlap of the start that is
    repaired (default SQ_APART or 5e-3)."""
    trace = []
    t0 = time.time()
    P, L = _lp_exact(G)
    if P is None:
        P = legal(G)
        if P is None:
            most = float(os.environ.get('SQ_APART', '5e-3')) if apart is None else apart
            P = _apart(G, most=most)               # an overlap up to 5e-3 (SQ_APART) that the exact LP did not repair
            if P is None:
                raise Unreadable('the start of the squeeze is not legal (gap %.2e)' % mlp.min_gap(G))
            L = float(mlp.side(P))
            wide = most > 5e-3                     # a larger overlap opens the box more: more rounds, a larger trust radius
            for _ in range(80 if wide else 12):    # the exact LP takes the room back, one trust radius at a time
                if _over():
                    break
                Q, LQ = _lp_exact(P, tr_c=0.1) if wide else _lp_exact(P)
                if Q is None or not (LQ < L - 1e-9):
                    break
                P, L = Q, LQ
        else:
            L = float(mlp.side(P))
    trace.append(('start', float(L), 0.0))
    stall = 0
    for it in range(iters):
        if (stop and stop()) or _over():
            break
        Qn = _lp_angles(P, tr_a)
        LQ = None
        if Qn is not None:
            Qn, LQ = _lp_exact(Qn)
        ok = Qn is not None and LQ < L - 1e-12
        if log:
            log('  it %d tr_a %.1e L %.9f -> %s %s %.0fs' % (it, tr_a, L, 'None' if LQ is None else '%.9f' % LQ, 'ok' if ok else 'rej', time.time() - t0))
        if ok:
            stall = stall + 1 if L - LQ < 3e-7 else 0
            P, L = Qn, LQ
            tr_a = min(tr_a * 1.5, 6e-3)
            if stall >= 3:
                break
        else:
            tr_a /= 4
            if tr_a < 2e-6:
                break
    trace.append(('slp', float(L), time.time() - t0))
    if fq:
        for name, fl in (('fq', ()), ('fq-polish', POLISH)):
            s2, X = fq_quench(L, canon(P)[1], fl)
            if s2 is not None and s2 < L - 1e-10:
                s3, X3 = canon(X)
                if mlp.min_gap(X3) > -1e-9:
                    P, L = X3, s3
            trace.append((name, float(L), time.time() - t0))
    return P, float(L), trace


# ---------------------------------------------------------------- parts

def _parts(R):
    """The squares of a read layout by part. The runs end on the long sides of their first and last
    stack, which are tilted lines, so the parts are cut along those lines and not across the strip."""
    Q = R['Q']; W1, W2 = R['E']; a1, a2 = R['arms']
    inA = Q[:, 0] < W1; lowB = ~inA & (Q[:, 1] < W2)

    def along(st, k):
        if k == 0:
            return (Q[:, 0] - st['cen'][0]) * -math.sin(st['th']) + (Q[:, 1] - st['cen'][1]) * math.cos(st['th'])
        return (Q[:, 0] - st['cen'][0]) * math.cos(st['th']) + (Q[:, 1] - st['cen'][1]) * math.sin(st['th'])
    c1 = inA & (along(a1['run'][0], 0) < -0.5); p1 = inA & (along(a1['run'][-1], 0) > 0.5)
    c2 = lowB & (along(a2['run'][0], 1) < -0.5); p2 = lowB & (along(a2['run'][-1], 1) > 0.5)
    return dict(corner=c1 | c2, cap1=p1, cap2=p2, run1=inA & ~c1 & ~p1, run2=lowB & ~c2 & ~p2, grid=~inA & ~lowB)


# ---------------------------------------------------------------- what blocks

def zone_labels(R, direction, j1, j2, r, q):
    """A zone name for every square of the stepped layout, in its order: corner, cap1, cap2 (the three
    end zones), run1, run2 (stacks of the flush runs), arm1, arm2 (other squares of the strips), grid."""
    Q = R['Q']; a1, a2 = R['arms']
    lab = np.array(['grid'] * len(Q), dtype=object)
    for name, mask in _parts(R).items():
        lab[mask] = name
    if direction == 'down':
        gone = np.zeros(len(Q), bool)
        gone[j1['idx']] = True; gone[j2['idx']] = True; gone[R['rows'][r]] = True; gone[R['cols'][q]] = True
        gone[R['bcut'][0] + R['bcut'][1]] = True
        return lab[~gone]
    extra = ['run1'] * len(j1['idx']) + ['run2'] * len(j2['idx']) + ['grid'] * (len(R['rows'][r]) + len(R['cols'][q]) + 1) \
        + ['arm1'] * len(R['bcut'][0]) + ['arm2'] * len(R['bcut'][1])
    return np.concatenate([lab, np.array(extra, dtype=object)])


_LAST = {}


def stress(P, lab=None):
    """The contacts that carry the side at fixed angles: the pairs and walls with a non-zero multiplier
    in the exact LP. -> list of (multiplier, i, j or wall name). A layout that is jammed short of flush
    has its end zone squares on this list; a healthy one has only runs, grid and walls."""
    reach = math.sqrt(2) + 0.25
    pairs = mlp.pair_list(P, reach)
    _LAST.clear()
    Q = mlp.solve(P, 0.02, 0.0)
    res = _LAST.get('res')
    if Q is None or res is None or not hasattr(res, 'ineqlin'):
        return None
    mu = -np.asarray(res.ineqlin.marginals)
    n = len(P); out = []
    for k in np.nonzero(mu[:len(pairs)] > 1e-7)[0]:
        out.append((float(mu[k]), int(pairs[k, 0]), int(pairs[k, 1])))
    w = mu[len(pairs):]
    for b, name in enumerate(('left wall', 'right wall', 'bottom wall', 'top wall')):
        for i in np.nonzero(w[b * n:(b + 1) * n] > 1e-7)[0]:
            out.append((float(w[b * n + i]), int(i), name))
    return out


def stress_summary(P, lab):
    """Counts of load-carrying contacts by the zones they join, most loaded first, as one line."""
    st = stress(P)
    if st is None:
        return 'no multipliers'
    cnt = collections.Counter()
    for mu, i, j in st:
        a = lab[i]; b = j if isinstance(j, str) else lab[j]
        if isinstance(j, str):
            b = 'wall'
        cnt['-'.join(sorted((a, b)))] += 1
    return ' '.join('%s:%d' % kv for kv in cnt.most_common())


# ---------------------------------------------------------------- certify

def certify(n, P):
    """The lane's rule: floatsafe at 2.2e-11, the official metric. -> (side, rows) or (None, None)."""
    import floatsafe
    rows = [{'n': str(n), 'square_id': str(i), 'x': repr(float(x)), 'y': repr(float(y)), 'angle': repr(float(a))}
            for i, (x, y, a) in enumerate(P)]
    _, fr, score, e = floatsafe.work((n, rows))
    if fr is None:
        return None, None
    return (score + 1.0) * math.sqrt(n), fr


# ---------------------------------------------------------------- commands

def cmd_read(a):
    P = load(a.sub, set(a.n) if a.n else None)
    for n in sorted(P):
        if n < 300 and not a.n:
            continue
        try:
            R = read(P[n], n)
            d, p, t, _ = squeeze_d(R['arms'][0]['c'], R['f'], len(R['arms'][0]['run']))
            print('reads  ', describe(R), 'd=%.5f' % d)
        except Unreadable as ex:
            print('refuses n=%d: %s' % (n, ex))


def step(P, n, direction, log=None, iters=80, fq=True, stop=None):
    """One step from a donor layout of n squares. -> dict(n, gapped side, squeezed array, side, trace, read)."""
    R = read(P, n)
    G, info = build(R, direction)
    nt = n - 2 * R['m'] - 1 if direction == 'down' else n + 2 * R['m'] + 3
    assert len(G) == nt
    X, L, trace = squeeze(G, iters=iters, log=log, fq=fq, stop=stop)
    return dict(n=nt, start=info['side'], P=X, side=L, trace=trace, R=R, info=info, G=G)


def cmd_ctl(a):
    os.makedirs(a.out, exist_ok=True)
    P = load(a.sub, {a.donor, a.target})
    R = read(P[a.donor], a.donor)
    print('donor ', describe(R))
    direction = 'down' if a.target < a.donor else 'up'
    c = R['arms'][0]['c']; s_after = len(R['arms'][0]['run']) + (-1 if direction == 'down' else 1)
    d, p, t, dpdf = squeeze_d(c, R['f'], s_after)
    print('formula: c=%d f=%.6f tilt=%.4f deg p=%.6f dp/df=%.4f s=%d d=%.6f' % (c, R['f'], math.degrees(t), p, dpdf, s_after, d))
    held = canon(P[a.target])[0] if a.target in P else float('nan')
    t0 = time.time()
    res = step(P[a.donor], a.donor, direction, log=print, iters=a.iters, fq=not a.nofq)
    if res['n'] != a.target:
        print('the step gives n=%d, not %d' % (res['n'], a.target)); return
    print('after the step: side %.9f, smallest gap %.2e, %d squares' % (res['start'], res['info']['gap'], res['n']))
    write_rows('%s/%d-gapped.csv' % (a.out, a.target), a.target, res['G'])
    for name, L, sec in res['trace']:
        print('  %-10s %.9f  (%.0f s)' % (name, L, sec))
    write_rows('%s/%d-from%d.csv' % (a.out, a.target, a.donor), a.target, res['P'])
    Lc, fr = certify(a.target, res['P'])
    base = res['start'] if direction == 'down' else R['s'] + 1
    print('result: side %.9f certified %s; held %.9f; step start %.9f; recovered %.6f = %.0f%% of d=%.6f; vs held %+.6f; %.0f s' % (
        res['side'], 'no' if Lc is None else '%.9f' % Lc, held, res['start'], base - res['side'],
        100 * (base - res['side']) / d, d, res['side'] - held, time.time() - t0))
    try:
        R2 = read(res['P'], a.target)
        print('result reads:', describe(R2))
    except Unreadable as ex:
        print('result does not read:', ex)
    lab = res['info']['lab']
    print('load-carrying contacts by zone:', stress_summary(res['P'], lab))
    st = stress(res['P']) or []
    X = res['P']
    for mu, i, j in sorted(st, key=lambda v: -v[0])[:40]:
        zi = lab[i]; zj = 'wall' if isinstance(j, str) else lab[j]
        if zi in ('corner', 'cap1', 'cap2') or zj in ('corner', 'cap1', 'cap2'):
            print('  %.3f  %s #%d (%.3f, %.3f, %.2f deg)  --  %s' % (mu, zi, i, X[i, 0], X[i, 1], math.degrees(X[i, 2]),
                  j if isinstance(j, str) else '%s #%d (%.3f, %.3f, %.2f deg)' % (zj, j, X[j, 0], X[j, 1], math.degrees(X[j, 2]))))


def targets_of(n, m):
    """The n one and two shells away on the line k - 2m = constant."""
    return {('down', 1): n - 2 * m - 1, ('down', 2): n - 4 * m, ('up', 1): n + 2 * m + 3, ('up', 2): n + 4 * m + 8}


def formula_side(R, direction):
    """Side after one step by the squeeze formula, the arm that needs more room decides."""
    ds = [squeeze_d(a['c'], R['f'], len(a['run']) + (-1 if direction == 'down' else 1))[0] for a in R['arms']]
    return R['s'] - 1 - min(ds) if direction == 'down' else R['s'] + 1 + max(ds)


def finish(X, L, held_t, direction, win, stop=None):
    """The polish after the sequential LP: the fq quench, and the LP again while fq still moves the layout.

    fq passes jams that stop the LP (872 from 813: the LP ends 1.1e-3 above the held side, fq then takes
    it 4.4e-4 below), so an up step gets it within 2e-2 of the held side and a down step within `win`."""
    if not (L < held_t + (max(win, 2e-2) if direction == 'up' else win)):
        return X, L
    for _ in range(3):
        if (stop and stop()) or _over():
            break
        s2, Y = fq_quench(L, canon(X)[1], ())
        if s2 is None or not (s2 < L - 1e-7):
            break
        s3, Y3 = canon(Y)
        Y3 = legal(Y3) if mlp.min_gap(Y3) > -1e-9 else None
        if Y3 is None:
            break
        X, L = Y3, float(mlp.side(Y3))
        X2, L2, _ = squeeze(X, iters=25, fq=False, stop=stop)
        if L2 < L:
            X, L = X2, L2
    s2, Y = fq_quench(L, canon(X)[1], POLISH)
    if s2 is not None and s2 < L - 1e-10:
        s3, Y3 = canon(Y)
        if mlp.min_gap(Y3) > -1e-9:
            X, L = Y3, s3
    return X, L


def cmd_plan(a):
    """Rank every (target, donor) pair of the sweep by the gain the board predicts."""
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(a.details))}
    board = {int(r['n']): float(r['L']) for r in json.load(open(a.board))}
    pz = {}
    for spec in a.donors:                       # TAG=FILE: a submission, or DIR of <n>.csv
        tag, path = spec.split('=', 1)
        if os.path.isdir(path):
            for fn in os.listdir(path):
                if fn.endswith('.csv') and fn[:-4].isdigit() and int(fn[:-4]) >= a.nmin:
                    try:
                        pz[(tag, int(fn[:-4]))] = load(os.path.join(path, fn))[int(fn[:-4])]
                    except Exception:
                        pass
        else:
            for n, P in load(path).items():
                if n >= a.nmin:
                    pz[(tag, n)] = P
    os.makedirs(a.donordir, exist_ok=True)
    rows = []
    with open(a.out + '.reads.tsv', 'w') as h:
        h.write('donor\tn\tside\tm\tk\tf\tline\tc1\tc2\ttilt1\ttilt2\trun1\trun2\tcorner\tcap1\tcap2\tstate\n')
        for (tag, n), P in sorted(pz.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            if len(P) != n:
                continue
            name = '%d-%s' % (n, tag)
            try:
                s0 = canon(P)[0]
                if tag != 'held' and not (s0 < held[n] + a.near) or (tag != 'held' and abs(s0 - held[n]) < 1e-7):
                    continue                    # a public donor: near the held side, and not the held layout itself
                R = read(P, n)
            except Unreadable as ex:
                h.write('%s\t%d\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t%s\n' % (name, n, ex)); continue
            a1, a2 = R['arms']
            h.write('%s\t%d\t%.9f\t%d\t%d\t%.6f\t%d\t%d\t%d\t%.3f\t%.3f\t%d\t%d\t%d\t%d\t%d\treads\n' % (
                name, n, R['s'], R['m'], R['k'], R['f'], R['k'] - 2 * R['m'], a1['c'], a2['c'], math.degrees(abs(a1['th'])),
                math.degrees(abs(a2['th'])), len(a1['run']), len(a2['run']), R['zones']['corner'], R['zones']['cap1'], R['zones']['cap2']))
            used = False
            for (direction, sh), t in targets_of(n, R['m']).items():
                if not (a.nmin <= t <= 1000) or t not in held:
                    continue
                gap_d = R['s'] - board[n]; gap_t = held[t] - board[t]
                pred = board[t] + gap_d
                form = formula_side(R, direction) if sh == 1 else float('nan')
                rows.append((-(held[t] - pred) / math.sqrt(t), t, name, direction, sh, pred, form, held[t], board[t]))
                used = True
            if used:
                write_rows(os.path.join(a.donordir, name + '.csv'), n, P)
    rows.sort()
    with open(a.out, 'w') as h:
        h.write('rank\ttarget\tdonor\tdirection\tshells\tpred_board\tpred_formula\theld\tboard\tpred_gain_score\n')
        for i, (g, t, name, direction, sh, pred, form, hl, bl) in enumerate(rows):
            h.write('%d\t%d\t%s\t%s\t%d\t%.9f\t%.9f\t%.9f\t%.9f\t%.3e\n' % (i, t, name, direction, sh, pred, form, hl, bl, -g))
    pos = [r for r in rows if r[0] < 0]
    print('pairs', len(rows), 'with a predicted gain', len(pos), 'on', len(set(r[1] for r in pos)), 'targets; reads table', a.out + '.reads.tsv')


def dname_of(row, a):
    return row['donor'] + (('+far' + ('T' if row.get('turn') == '1' else '')) if a.swap else '')


def cmd_run(a):
    """Build the plan rows of this worker, best first. Every row is written when it ends. With
    SQ_KEEPNEAR=EPS a build that ends less than EPS above the bar is kept in OUTDIR/near."""
    os.makedirs(a.out + '/raw', exist_ok=True)
    M, Rm = (int(x) for x in a.mod.split(','))
    plan = list(csv.DictReader(open(a.plan), delimiter='\t'))
    held = _bars(a.details, a.beat)
    tsv = '%s/rows-%d.tsv' % (a.out, Rm)
    seen = set()
    if os.path.exists(tsv):
        seen = set(tuple(l.split('\t')[:4]) for l in open(tsv).read().splitlines()[1:]
                   if 'opened layout overlaps' not in l and 'cut is not clean' not in l)   # refused by an older reader: try again
    else:
        open(tsv, 'w').write('target\tdonor\tdirection\tshells\tpred_board\tpred_formula\tafter_step\tafter_slp\tafter_squeeze\theld\tseconds\tstate\tchain\n')

    def dead():
        try:
            return a.deadline and time.time() > float(open(a.deadline).read().split()[0])
        except Exception:
            return False
    for row in plan:
        if int(row['rank']) % M != Rm or (a.only and row['direction'] not in a.only) or int(row['shells']) > a.shells:
            continue
        if float(row['pred_gain_score']) < a.mingain or dead():
            continue
        key = (row['target'], row['donor'] + (('+far' + ('T' if row.get('turn') == '1' else '')) if a.swap else ''), row['direction'], row['shells'])
        if key in seen:
            continue
        t = int(row['target']); dn = int(row['donor'].split('-')[0]); t0 = time.time()
        start = slp = final = float('nan'); state = 'ok'; chain = ''
        set_limit(a.buildsec)
        try:
            cur = load(os.path.join(a.donors, row['donor'] + '.csv'))[dn]; ncur = dn
            for k in range(int(row['shells'])):
                last = k == int(row['shells']) - 1
                R = read(cur, ncur)
                G, info = build(R, row['direction'], a.where)
                ncur = len(G)
                if k == 0:
                    start = info['side']
                if a.swap and last and ncur == t:   # the target's own far zones, this row's way round
                    G = swap_far(G, info, R, load(os.path.join(a.swap, '%d.csv' % t))[t], t, turn=row.get('turn') == '1')
                cur, L, trace = squeeze(G, iters=a.iters, fq=False, tr_a=a.tra, stop=dead)
                slp = L
                if last and ncur == t:
                    cur, L = finish(cur, L, held[t], row['direction'], a.fqwin, dead)
                final = L
                if last and L > held[t] + 1e-5:
                    try:
                        chain = stress_summary(cur, info['lab'])
                    except Exception as ex:
                        chain = 'no chain: %s' % str(ex)[:40]
            if ncur != t:
                state = 'wrong n %d' % ncur
            elif final < held[t] - 1e-9:
                write_rows('%s/raw/%d-%s%sfrom%s%s.csv' % (a.out, t, row['direction'], row['shells'], row['donor'],
                                                         ('+far' + ('T' if row.get('turn') == '1' else '')) if a.swap else ''), t, cur)
                state = 'below held'
            elif _over():
                state = 'time limit'
            if ncur == t and state != 'below held' and final < held[t] + float(os.environ.get('SQ_KEEPNEAR') or 0):
                os.makedirs(a.out + '/near', exist_ok=True)          # a near miss another lane can polish
                write_rows('%s/near/%d-%s%sfrom%s-w%g-t%g.csv' % (a.out, t, row['direction'], row['shells'], dname_of(row, a),
                                                                 a.where, a.tra), t, cur)
        except Unreadable as ex:
            state = 'refused: %s' % ex
        except Exception as ex:                   # one bad pair must not stop a sweep
            state = 'error: %s' % str(ex)[:80]
        if _over() and state.startswith('refused'):
            state += ' (time limit)'
        set_limit(None)
        dname = dname_of(row, a)
        with open(tsv, 'a') as h:
            h.write('%s\t%s\t%s\t%s\t%s\t%s\t%.9f\t%.9f\t%.9f\t%.9f\t%.0f\t%s\t%s\n' % (
                row['target'], dname, row['direction'], row['shells'], row['pred_board'], row['pred_formula'],
                start, slp, final, held[t], time.time() - t0, state, chain))
        print(row['target'], row['donor'], row['direction'], row['shells'], '%.9f' % final, 'held %.9f' % held[t], state, '%.0fs' % (time.time() - t0), flush=True)


def cmd_walk(a):
    """Carry one design along its line, shell after shell, while it stays near the held side.

    WALKS.tsv has rows donor, direction. Each step starts from the result of the step before it, so a
    design that wins at one n is tried at the next n of its line at once. Every layout is read with
    read_any, every step's layout goes to OUTDIR/steps, and a walk that ends because a layout does not
    read leaves a line in OUTDIR/ends-R.tsv. An upward step repairs a start that overlaps by up to 3e-2."""
    os.makedirs(a.out + '/raw', exist_ok=True); os.makedirs(a.out + '/steps', exist_ok=True)
    env_apart = float(os.environ['SQ_APART']) if os.environ.get('SQ_APART') else None
    M, Rm = (int(x) for x in a.mod.split(','))
    walks = [l.split('\t')[:2] for l in open(a.walks).read().splitlines() if l.strip() and not l.startswith('donor')]
    held = _bars(a.details, a.beat)
    tsv = '%s/rows-walk-%d.tsv' % (a.out, Rm)
    if not os.path.exists(tsv):
        open(tsv, 'w').write('target\tdonor\tdirection\tshells\tpred_board\tpred_formula\tafter_step\tafter_slp\tafter_squeeze\theld\tseconds\tstate\tchain\n')

    def dead():
        try:
            return a.deadline and time.time() > float(open(a.deadline).read().split()[0])
        except Exception:
            return False
    for i, (donor, direction) in enumerate(walks):
        if i % M != Rm or dead():
            continue
        dn = int(donor.split('-')[0])
        cur = load(os.path.join(a.donors, donor + '.csv'))[dn]; ncur = dn; miss = 0
        apart = env_apart if env_apart is not None else (3e-2 if direction == 'up' else None)
        for k in range(1, a.maxsteps + 1):
            if dead():
                break
            t0 = time.time(); start = slp = final = float('nan'); state = 'ok'; chain = ''; t = 0; go = False; far = ''
            set_limit(a.buildsec)
            try:
                try:
                    R = read_any(cur, ncur)
                except Unreadable as ex:
                    with open('%s/ends-%d.tsv' % (a.out, Rm), 'a') as h:
                        h.write('%s\t%s\t%d\t%d\t%s\n' % (donor, direction, k, ncur, ex))
                    raise
                t = targets_of(ncur, R['m'])[(direction, 1)]
                if not (1 <= t <= 1000):
                    break
                G, info = build(R, direction)
                start = info['side']
                X, L, trace = squeeze(G, iters=a.iters, fq=False, stop=dead, apart=apart)
                slp = L
                X, L = finish(X, L, held[t], direction, a.fqwin, dead)
                final = L; far = ''
                tf = os.path.join(a.swap, '%d.csv' % t) if a.swap else ''
                if tf and os.path.exists(tf) and not final < held[t] - 1e-9:
                    for turn in (False, True):      # the step again with the target's own far zones, both ways round
                        try:
                            X2, L2, _ = squeeze(swap_far(G, info, R, load(tf)[t], t, turn=turn), iters=a.iters, fq=False, stop=dead, apart=apart)
                            X2, L2 = finish(X2, L2, held[t], direction, a.fqwin, dead)
                        except Unreadable:
                            continue
                        if L2 < final:
                            X, final, far = X2, L2, '+farT' if turn else '+far'
                write_rows('%s/steps/%d-%s%dfrom%s%s.csv' % (a.out, t, direction, k, donor, far), t, X)
                if final < held[t] - 1e-9:
                    write_rows('%s/raw/%d-%s%dfrom%s%s.csv' % (a.out, t, direction, k, donor, far), t, X)
                    state = 'below held'
                elif _over():
                    state = 'time limit'
                elif L > held[t] + 1e-5 and not a.nochain:
                    try:
                        chain = stress_summary(X, info['lab'])
                    except Exception as ex:
                        chain = 'no chain: %s' % str(ex)[:40]
                if state == 'below held':
                    miss = 0
                elif not final < held[t] + 1e-7:   # a step that lands on the bar is the held design: not a miss
                    miss += 1
                # --misses N: the walk goes on from every result and ends after N steps in a row that do not win
                go = (miss < a.misses and final < held[t] + 5 * a.stopgap) if a.misses else final < held[t] + a.stopgap
                cur, ncur = X, t
            except Unreadable as ex:
                state = 'refused: %s' % ex
            except Exception as ex:
                state = 'error: %s' % str(ex)[:80]
            if _over() and state.startswith('refused'):
                state += ' (time limit)'
            set_limit(None)
            if t:
                with open(tsv, 'a') as h:
                    h.write('%d\t%s\t%s\t%d\tnan\tnan\t%.9f\t%.9f\t%.9f\t%.9f\t%.0f\t%s\t%s\n' % (
                        t, donor + far, direction, k, start, slp, final, held.get(t, float('nan')), time.time() - t0, state, chain))
                print(t, donor, direction, k, '%.9f' % final, 'held %.9f' % held.get(t, float('nan')), state, '%.0fs' % (time.time() - t0), flush=True)
            if not go:
                break


def _bars(details, beat=()):
    """The side a result must beat per n: the held side, and the side of the same n in every other take.tsv."""
    bar = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    for fn in beat or ():
        for r in csv.DictReader(open(fn), delimiter='\t'):
            n = int(r['n']); bar[n] = min(bar[n], (float(r['new']) + 1.0) * math.sqrt(n))
    return bar


def _built(r):
    return not r['state'].startswith(('refused', 'error', 'wrong'))


def _side_of(r):
    try:
        v = float(r['after_squeeze'])
        return v if v == v and _built(r) else float('inf')
    except (ValueError, TypeError):
        return float('inf')


def cmd_take(a):
    """Certify every raw layout the lane's way and write the take dir; take.tsv is replaced by rename."""
    import floatsafe
    held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(a.details))}
    bar = dict(held)                                # a win must also beat the same n of every --beat take
    for fn in a.beat or ():
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
            ok = fr is not None and score < bar[n] - 1e-10
            cert[fn[:-4]] = (ok, score)
            if not ok:
                print('drop', n, score, held[n], e, p); continue
            if n not in best or score < best[n][0]:
                best[n] = (score, fr, fn[:-4])
    os.makedirs(a.take, exist_ok=True)
    tot = 0.0; lines = ['n\theld\tnew\tgain\tsource\tlicence\n']
    for n in sorted(best):
        score, fr, tag = best[n]
        tmp = '%s/work/%d.csv.tmp' % (a.take, n)
        os.makedirs(os.path.dirname(tmp), exist_ok=True)
        with open(tmp, 'w', newline='') as g:
            w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
            for r in fr:
                w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
        os.replace(tmp, '%s/%d.csv' % (a.take, n))
        step_, donor = tag.split('-', 1)[1].split('from')
        far = donor.endswith(('+far', '+farT')); donor = donor.split('+far')[0]
        s_, lic = src.get(donor, ('the held packing of n = %s' % donor.split('-')[0], 'own search'))
        if far:
            s_ += ', with the far zones of the held packing of n = %d' % n
        tot += held[n] - score
        lines.append('%d\t%r\t%r\t%.3e\tfamily_step.py %s shell(s) %s from %s\t%s\n' % (
            n, held[n], score, held[n] - score, step_[-1], step_[:-1], s_, lic))
        print('keep', n, held[n], score, '%.3e' % (held[n] - score), tag)
    tmp = a.take + '/work/take.tsv.tmp'
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    open(tmp, 'w').write(''.join(lines)); os.replace(tmp, a.take + '/take.tsv')
    print('kept', len(best), 'gain', repr(tot))
    if a.table:
        rows = {}
        for d in a.outs:
            for fn in sorted(os.listdir(d)):
                if fn.startswith('rows-') and fn.endswith('.tsv'):
                    for r in csv.DictReader(open(os.path.join(d, fn)), delimiter='\t'):
                        key = (int(r['target']), r['donor'], r['direction'], r['shells'])
                        if key not in rows or _side_of(r) < _side_of(rows[key]):   # a pair built twice: the smaller side
                            rows[key] = r
        with open(a.table + '.tmp', 'w') as h:
            h.write('target\tdonor\tdirection\tshells\tpred_board\tpred_formula\tafter_step\tafter_slp\tafter_squeeze\theld\tdelta_vs_held\tcertified\tstate\tchain\n')
            for key in sorted(rows):
                r = rows[key]
                tag = '%s-%s%sfrom%s' % (r['target'], r['direction'], r['shells'], r['donor'])
                c = cert.get(tag)
                cs = 'no' if c is None else ('yes' if c[0] else 'no (%s)' % ('floatsafe' if c[1] >= held[key[0]] else 'under 1e-10'))
                if not _built(r):         # a pair refused at its second shell holds the sides of the first: not a result
                    r = dict(r, after_step='nan', after_slp='nan', after_squeeze='nan')
                try:
                    dv = '%.3e' % (float(r['after_squeeze']) - float(r['held']))
                    dv = '' if dv == 'nan' else dv
                except ValueError:
                    dv = ''
                h.write('\t'.join([r['target'], r['donor'], r['direction'], r['shells'], r['pred_board'], r['pred_formula'], r['after_step'],
                                   r['after_slp'], r['after_squeeze'], r['held'], dv, cs, r['state'], r.get('chain') or '']) + '\n')
        os.replace(a.table + '.tmp', a.table)
        print('table', a.table, len(rows), 'rows')


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    q = sp.add_parser('plan'); q.add_argument('details'); q.add_argument('board'); q.add_argument('out'); q.add_argument('donordir')
    q.add_argument('donors', nargs='+'); q.add_argument('--nmin', type=int, default=300); q.add_argument('--near', type=float, default=0.005)
    q.set_defaults(fn=cmd_plan)
    q = sp.add_parser('run'); q.add_argument('plan'); q.add_argument('donors'); q.add_argument('details'); q.add_argument('out')
    q.add_argument('--mod', default='1,0'); q.add_argument('--deadline'); q.add_argument('--iters', type=int, default=60)
    q.add_argument('--only'); q.add_argument('--shells', type=int, default=2); q.add_argument('--mingain', type=float, default=-1.0)
    q.add_argument('--fqwin', type=float, default=2e-3); q.add_argument('--beat', nargs='*', default=[])
    q.add_argument('--where', type=float, default=0.5); q.add_argument('--tra', type=float, default=2e-3)
    q.add_argument('--swap'); q.add_argument('--buildsec', type=float, default=900.0); q.set_defaults(fn=cmd_run)
    q = sp.add_parser('walk'); q.add_argument('walks'); q.add_argument('donors'); q.add_argument('details'); q.add_argument('out')
    q.add_argument('--mod', default='1,0'); q.add_argument('--deadline'); q.add_argument('--iters', type=int, default=60)
    q.add_argument('--maxsteps', type=int, default=8); q.add_argument('--stopgap', type=float, default=4e-3)
    q.add_argument('--fqwin', type=float, default=2e-3); q.add_argument('--misses', type=int, default=0)
    q.add_argument('--beat', nargs='*', default=[]); q.add_argument('--swap'); q.add_argument('--buildsec', type=float, default=900.0)
    q.add_argument('--nochain', action='store_true'); q.set_defaults(fn=cmd_walk)
    q = sp.add_parser('take'); q.add_argument('details'); q.add_argument('take'); q.add_argument('outs', nargs='+')
    q.add_argument('--table'); q.add_argument('--sources'); q.add_argument('--beat', nargs='*', default=[]); q.set_defaults(fn=cmd_take)
    q = sp.add_parser('read'); q.add_argument('sub'); q.add_argument('n', type=int, nargs='*'); q.set_defaults(fn=cmd_read)
    q = sp.add_parser('ctl'); q.add_argument('sub'); q.add_argument('donor', type=int); q.add_argument('target', type=int)
    q.add_argument('out'); q.add_argument('--iters', type=int, default=80); q.add_argument('--nofq', action='store_true'); q.set_defaults(fn=cmd_ctl)
    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
