#!/usr/bin/env python3
"""Where a two-arm layout loses its squares: the end loss E split over the two ends of each arm and the corner.

Usage: invent_parts.py DETAILS.csv HELD.csv SCRATCH OUT.tsv N [N ...]
  DETAILS.csv  the gate details of the held file      HELD.csv  the held file
  SCRATCH      the scratch dir: the lowest file of each N over HELD.csv and the take-*-r17 dirs is read

The layout is turned so that one arm is on the left wall and one on the bottom wall. The arm size c of a wall comes
from the main tilt t there and the side fraction f: c = (1 - f + sin t) / (1 - cos t). With W = c - 1 + f the box has
four parts:
  the corner   x < W1 and y < W2, c1 - 1 by c2 - 1 plain squares
  arm 1        x < W1 and y > W2, a flush arm holds c1 - 1 + g1 squares per unit of wall there, g = f - sin t
  arm 2        x > W1 and y < W2, the same with c2 and g2
  the rest     x > W1 and y > W2, a plain block
A square is in the part that holds its centre. The loss of a part is what a flush arm (or the plain grid) would hold
there less what the layout holds. Each arm is cut near the middle of its wall, along a line between two stacks, so that no stack is cut:
the near part ends at the corner and the far part at the far wall. The corner number alone means little, because a
square that lies across the line of the corner counts where its centre is: read the sum of the corner and the two
near ends. The five losses add to E = (m - c2 + 1) g1 + (m - c1 + 1) g2 - k, the end loss of the
census (invent_census.py). The control is that sum, to 1e-6.

The last columns give the corner in the frame of modules.k_flush, with the narrower arm first. There the three end
zones cost k_flush - k = corner + far zone 1 + far zone 2. The far zones are the far parts above, and the corner is
all that is left, with what the plain block lacks. The line of the twoshort avenue for a pair with no library
corner is 0.55 (c1 + c2) - 6.3. This tool asks for no stack and no cut, so it also reads the layouts that
modules.cut refuses.

Our own code. Reads x, y, angle rows.
"""
import csv, glob, math, os, sys
import numpy as np

details, heldp, S, out = sys.argv[1:5]
NS = [int(x) for x in sys.argv[5:]]
held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
num = lambda v: float(str(v).lstrip('s'))


def lowest(n):
    best = (held[n], 'held', None)
    for d in sorted(glob.glob(S + '/take-*-r17')):
        p = d + '/take.tsv'
        if not os.path.exists(p): continue
        for r in csv.DictReader(open(p), delimiter='\t'):
            try: nn = int(r['n']); new = float(r['new'])
            except Exception: continue
            f = '%s/%d.csv' % (d, n)
            if nn == n and os.path.exists(f) and (new + 1) * math.sqrt(n) < best[0]: best = ((new + 1) * math.sqrt(n), os.path.basename(d)[5:-4], f)
    return best


CACHE = {}


def rows_of(path, n):
    if path not in CACHE:
        d = {}
        for r in csv.DictReader(open(path)): d.setdefault(r.get('n', ''), []).append(r)
        CACHE[path] = d
    d = CACHE[path]
    return d.get(str(n)) or d.get('') or []


def load(path, n):
    R = rows_of(path, n)
    P = np.array([[num(r['x']), num(r['y']), num(r['angle'])] for r in R])
    c, s = np.abs(np.cos(P[:, 2])), np.abs(np.sin(P[:, 2])); h = (c + s) / 2
    lo = min((P[:, 0] - h).min(), (P[:, 1] - h).min()); L = max((P[:, 0] + h).max(), (P[:, 1] + h).max()) - lo
    P[:, 0] -= lo; P[:, 1] -= lo
    return P, L


def turn(P, L, k):
    """the k-th of the 8 symmetries of the box"""
    x, y, a = P[:, 0].copy(), P[:, 1].copy(), P[:, 2].copy()
    if k & 1: x = L - x; a = -a
    if k & 2: y = L - y; a = -a
    if k & 4: x, y = y, x; a = math.pi / 2 - a
    return np.stack([x, y, a], 1)


def tilt(a): return np.abs(((np.degrees(a) + 45) % 90) - 45)


def read(P, L):
    m = int(L + 1e-9); f = L - m
    best = None
    for k in range(8):
        Q = turn(P, L, k); t = tilt(Q[:, 2]); T = Q[t > 1.0]
        if len(T) < 20: return None
        near = ((T[:, 0] < 12.5) | (T[:, 1] < 12.5)).sum()
        left = T[(T[:, 0] < 9) & (T[:, 1] > 13)]; bot = T[(T[:, 1] < 9) & (T[:, 0] > 13)]
        if len(left) < 10 or len(bot) < 10: continue
        key = (near, -abs(len(left) - len(bot)), len(left))        # arm 1 (left) is the one with fewer tilted squares
        if best is None or key > best[0]: best = (key, Q, left, bot)
    if best is None: return None
    _, Q, left, bot = best
    res = {}
    cs = []
    for T in (left, bot):
        t = math.radians(float(np.median(tilt(T[:, 2]))))
        c = (1 - f + math.sin(t)) / (1 - math.cos(t)); cs.append((c, t))
    (c1r, t1), (c2r, t2) = cs
    c1, c2 = round(c1r), round(c2r)
    if abs(c1 - c1r) > 0.25 or abs(c2 - c2r) > 0.25: return dict(m=m, f=f, note='arm sizes %.2f %.2f are not whole' % (c1r, c2r))
    t1 = solve(c1, f); t2 = solve(c2, f)
    g1 = f - math.sin(t1); g2 = f - math.sin(t2); W1 = c1 - 1 + f; W2 = c2 - 1 + f
    x, y = Q[:, 0], Q[:, 1]
    k = len(Q) - m * m
    corner = (c1 - 1) * (c2 - 1) - ((x < W1) & (y < W2)).sum()
    rest = (m - c1 + 1) * (m - c2 + 1) - ((x >= W1) & (y >= W2)).sum()
    r1 = c1 - 1 + g1; r2 = c2 - 1 + g2
    in1 = (x < W1) & (y >= W2); in2 = (y < W2) & (x >= W1)
    far1, y1 = cut(Q[in1], W1, (W2 + L) / 2, 0); far2, x2 = cut(Q[in2][:, [1, 0, 2]] * [1, 1, -1] + [0, 0, math.pi / 2], W2, (W1 + L) / 2, 0)
    a1f = r1 * (L - y1) - far1; a1n = r1 * (y1 - W2) - (in1.sum() - far1)
    a2f = r2 * (L - x2) - far2; a2n = r2 * (x2 - W1) - (in2.sum() - far2)
    E = (m - c2 + 1) * g1 + (m - c1 + 1) * g2 - k
    tot = corner + rest + a1n + a1f + a2n + a2f
    # the same corner in the frame of modules.k_flush, with the narrower arm first: what the three zones may cost there
    # is k_flush - k = corner + far zone 1 + far zone 2
    (cn, gn, fn), (cw, gw, fw) = sorted(((c1, g1, a1f), (c2, g2, a2f)))
    kfm = L * gn + (cn - 1) * f + (m - cn + 1) * gw
    cmod = kfm - k - fn - fw
    return dict(m=m, f=f, k=k, c1=c1, c2=c2, E=E, corner=corner, rest=rest, a1n=a1n, a1f=a1f, a2n=a2n, a2f=a2f, err=tot - E, note='',
                cn=cn, cw=cw, farn=fn, farw=fw, cmod=cmod, line=0.55 * (cn + cw) - 6.3)


def cut(T, W, mid, _):
    """T: the squares of an arm on the left wall (x across the strip, y along the wall). The cut is a line along the
    stacks, between two stacks, as near the middle of the wall as it can be. -> (squares beyond the cut, the y where the
    cut crosses the middle of the strip)"""
    s = ((np.degrees(T[:, 2]) + 45) % 90) - 45
    tl = np.abs(s) > 1.0
    if tl.sum() < 2: return int((T[:, 1] > mid).sum()), mid
    sm = math.radians(float(np.median(s[tl])))
    v = (-math.sin(sm), math.cos(sm))                       # across the stacks
    q = T[:, 0] * v[0] + T[:, 1] * v[1]
    qmid = W / 2 * v[0] + mid * v[1]
    qq = np.sort(q[tl & (np.abs(q - qmid) < 2.6)])
    if len(qq) < 2: return int((q > qmid).sum()), mid
    i = int(np.argmax(np.diff(qq))); qc = (qq[i] + qq[i + 1]) / 2
    return int((q > qc).sum()), (qc - W / 2 * v[0]) / v[1]


def solve(c, f):
    lo, hi = 0.0, 0.7
    for _ in range(80):
        t = (lo + hi) / 2
        if c * math.cos(t) + math.sin(t) > c - 1 + f: lo = t
        else: hi = t
    return (lo + hi) / 2


rows = []
for n in NS:
    L, lane, path = lowest(n)
    P, L2 = load(path or heldp, n)
    r = read(P, L2)
    if r is None: rows.append((n, lane, L2, None)); continue
    rows.append((n, lane, L2, r))
with open(out, 'w') as h:
    h.write('n\tfile_of\tside\tk\tf\tc1\tc2\tend_loss_E\tcorner\tarm1_near\tarm1_far\tarm2_near\tarm2_far\tplain_block\tnear_ends_and_corner\tfar_ends\tsum_less_E\tnarrow_arm\twide_arm\tfar_loss_narrow\tfar_loss_wide\tcorner_loss_modules_frame\tline_of_twoshort\tnote\n')
    for n, lane, L, r in rows:
        if r is None or r.get('note'):
            h.write('%d\t%s\t%.9f%s\t%s\n' % (n, lane, L, '\t' * 20, 'not two arms on two walls that meet' if r is None else r['note'])); continue
        h.write('%d\t%s\t%.9f\t%d\t%.4f\t%d\t%d\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.1e\t%d\t%d\t%.3f\t%.3f\t%.3f\t%.2f\t\n' % (
            n, lane, L, r['k'], r['f'], r['c1'], r['c2'], r['E'], r['corner'], r['a1n'], r['a1f'], r['a2n'], r['a2f'], r['rest'],
            r['corner'] + r['a1n'] + r['a2n'], r['a1f'] + r['a2f'], r['err'], r['cn'], r['cw'], r['farn'], r['farw'], r['cmod'], r['line']))
ok = [r for _, _, _, r in rows if r and not r.get('note')]
print('%d n, %d read as two arms, largest |sum less E| %.1e' % (len(rows), len(ok), max([abs(r['err']) for r in ok] or [0])))
