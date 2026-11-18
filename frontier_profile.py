#!/usr/bin/env python3
"""Where a two-arm layout gains its squares over the plain grid, zone by zone.

  frontier_profile.py SUB.csv TARGETS.tsv OUT.tsv [N ...]

A layout at side L = m + f with n = m^2 + k squares is turned (by the symmetries of the square) so that its
two arms of flush stacks sit on the left wall (arm 1, stacks of c1, strip width W1 = c1 - 1 + f) and on
the bottom wall (arm 2, c2, W2), with the shared corner at the bottom left. The box is cut in three:

  A = [0, W1] x [0, L]       baseline (c1 - 1) m uprights
  B = [W1, L] x [0, W2]      baseline (c2 - 1)(m - c1 + 1) uprights
  R = the rest               baseline (m - c1 + 1)(m - c2 + 1) uprights, exactly full

k is the sum of the three excesses (squares are counted by their centres). Inside A and B the excess is
split along the wall: the flush run (first to last flush stack), the corner side of it and the far side.
A flush run of length l gains g l with g = f - sin t (t the flush tilt). The table sets each zone's gain
beside what the same length would gain at the flush rate. Our own code; reads data only. Run with python -I.
"""
import csv, math, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from frontier_read import load, normal
from frontier_stacks import stacks


def flush_arms(A, s, m):
    """-> [(wall, c, tilt_rad, [stack centres])] for stacks that are flush to 3e-3, at least 3 of a kind per wall"""
    f = s - m
    T = A[np.abs(A[:, 2]) > 0.5]
    if len(T) < 12: return []
    chains, _ = stacks(T)
    arms = collections.defaultdict(list)
    for ch in chains:
        c = len(ch)
        if c < 5: continue
        t = math.radians(abs(float(np.median(T[ch, 2]))))
        if abs(c * math.cos(t) + math.sin(t) - (c - 1 + f)) > 3e-3: continue
        ax = T[ch[-1], :2] - T[ch[0], :2]
        cen = T[ch, :2].mean(0); W = c - 1 + f
        if abs(ax[0]) > abs(ax[1]):
            wall = 'L' if cen[0] < W / 2 + 0.05 else 'R' if cen[0] > s - W / 2 - 0.05 else None
        else:
            wall = 'B' if cen[1] < W / 2 + 0.05 else 'T' if cen[1] > s - W / 2 - 0.05 else None
        if wall: arms[(wall, c)].append((cen, t))
    out = [(w, c, float(np.median([t for _, t in v])), [p for p, _ in v]) for (w, c), v in arms.items() if len(v) >= 3]
    return sorted(out, key=lambda a: -len(a[3]))


def turn(A, s, w1, w2):
    """symmetry that puts wall w1 on the left and wall w2 on the bottom; -> centres (angles are not needed)"""
    X = A[:, :2].copy()
    if w1 in 'BT':
        X = X[:, ::-1].copy(); sw = {'B': 'L', 'T': 'R', 'L': 'B', 'R': 'T'}; w1, w2 = sw[w1], sw[w2]
    if w1 == 'R': X[:, 0] = s - X[:, 0]
    if w2 == 'T': X[:, 1] = s - X[:, 1]
    return X


def profile(sq, n):
    m = math.isqrt(n - 1); k = n - m * m
    s, A = normal(sq); f = s - m
    arms = flush_arms(A, s, m)
    if len(arms) < 2: return None
    a1 = arms[0]
    a2 = next((a for a in arms[1:] if (a[0] in 'LR') != (a1[0] in 'LR')), None)
    if a2 is None: return None
    X = turn(A, s, a1[0], a2[0])
    def along(a, axis):
        P = turn(np.array([[p[0], p[1], 0] for p in a[3]]), s, a1[0], a2[0])
        return float(P[:, axis].min()), float(P[:, axis].max())
    c1, t1 = a1[1], a1[2]; c2, t2 = a2[1], a2[2]
    W1 = c1 - 1 + f; W2 = c2 - 1 + f
    p1 = 1 / math.cos(t1); p2 = 1 / math.cos(t2)
    y0, y1 = along(a1, 1); y0 -= p1 / 2; y1 += p1 / 2
    x0, x1 = along(a2, 0); x0 -= p2 / 2; x1 += p2 / 2
    inA = X[:, 0] < W1; inB = (~inA) & (X[:, 1] < W2)
    yA = X[inA, 1]; xB = X[inB, 0]
    g1 = f - math.sin(t1); g2 = f - math.sin(t2)
    z = {}
    z['A_flush'] = ((yA >= y0) & (yA < y1)).sum() - (c1 - 1) * (y1 - y0), g1 * (y1 - y0)
    z['A_corner'] = (yA < y0).sum() - (c1 - 1) * y0, g1 * y0
    z['A_far'] = (yA >= y1).sum() - (c1 - 1) * (s - y1 - f), g1 * (s - y1)
    z['B_flush'] = ((xB >= x0) & (xB < x1)).sum() - (c2 - 1) * (x1 - x0), g2 * (x1 - x0)
    z['B_corner'] = (xB < x0).sum() - (c2 - 1) * (x0 - W1), g2 * (x0 - W1)
    z['B_far'] = (xB >= x1).sum() - (c2 - 1) * (s - x1), g2 * (s - x1)
    rest = (~inA & ~inB).sum() - (m - c1 + 1) * (m - c2 + 1)
    tot = sum(v[0] for v in z.values()) + rest
    return dict(m=m, k=k, f=f, c1=c1, c2=c2, tilt1=math.degrees(t1), tilt2=math.degrees(t2), n1=len(a1[3]), n2=len(a2[3]),
                y0=y0, x0=x0 - W1, z=z, rest=int(rest), total=float(tot))


ZONES = ['A_flush', 'A_corner', 'A_far', 'B_flush', 'B_corner', 'B_far']


def main():
    sub, targets, out = sys.argv[1:4]
    want = set(map(int, sys.argv[4:]))
    P = load(sub)
    Tg = {int(r['n']): r for r in csv.DictReader(open(targets), delimiter='\t')}
    with open(out, 'w') as h:
        h.write('n\tm\tk\tf\tdeficit\tc1\tstacks1\ttilt1\tc2\tstacks2\ttilt2\tcorner_len1\tcorner_len2\t' +
                '\t'.join('%s\t%s_at_flush_rate' % (q, q) for q in ZONES) + '\trest\tsum\n')
        for n in sorted(P):
            if n < 300 or (want and n not in want): continue
            d = profile(P[n], n)
            if d is None: continue
            s = d['m'] + d['f']; b = float(Tg[n]['target_L'])
            cells = [n, d['m'], d['k'], '%.6f' % d['f'], '%.3f' % (s * s - b * b), d['c1'], d['n1'], '%.2f' % d['tilt1'],
                     d['c2'], d['n2'], '%.2f' % d['tilt2'], '%.2f' % d['y0'], '%.2f' % d['x0']]
            for q in ZONES: cells += ['%.2f' % d['z'][q][0], '%.2f' % d['z'][q][1]]
            cells += [d['rest'], '%.2f' % d['total']]
            h.write('\t'.join(map(str, cells)) + '\n')


if __name__ == '__main__':
    main()
