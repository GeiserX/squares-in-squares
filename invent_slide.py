#!/usr/bin/env python3
"""Slide starts: a packing of N + 1 squares with one arm-end square removed, as plain starts for the soft chain.

The drop scan of invent_drop.py quenches each start with fq, and fq ends above a sheared start. This tool writes
the starts and leaves them alone. The soft search opens the jam on the right one, and fq follows after that.

The tilted squares are grouped into arms (squares whose centres are within 1.6). Each arm has a long axis. The
candidates are the PER tilted squares at each end of each arm along that axis. The ends nearest another arm come
first: on 979 -> 978 the square that opened the slide was the last one of the arm of 9, on the side of the other
arm.

Usage: invent_slide.py SRC.csv NSRC OUTDIR [--per 1] [--tag s] [--odd]
  --odd     the candidates are the odd-tilt squares (more than 2.5 degrees from the two main tilts of their arm)
            and the tilted squares outside every arm, in place of the arm ends
  SRC.csv   raw rows (n, square_id, x, y, angle in radians) holding the packing of NSRC squares
Output: OUTDIR/N-TAGk.csv for N = NSRC - 1 and k = 0, 1, ..., and one line per start on stdout.
Our own code. Reads packings as data only. Nothing is certified here.
"""
import argparse, collections, csv, math, os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import methods_lp as mlp  # noqa: E402


def arms(X, Y, T):
    """connected groups of tilted squares (centres within 1.6), the large ones only"""
    idx = list(np.where(T)[0]); seen = set(); out = []
    P = np.stack([X, Y], 1)
    for i in idx:
        if i in seen: continue
        comp = [i]; seen.add(i); q = [i]
        while q:
            j = q.pop()
            d = np.hypot(P[idx, 0] - P[j, 0], P[idx, 1] - P[j, 1])
            for k in np.where(d < 1.6)[0]:
                k = idx[k]
                if k not in seen: seen.add(k); comp.append(k); q.append(k)
        if len(comp) >= 12: out.append(comp)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('nsrc', type=int); ap.add_argument('out')
    ap.add_argument('--per', type=int, default=1); ap.add_argument('--tag', default='s')
    ap.add_argument('--odd', action='store_true', help='the odd-tilt squares in place of the arm ends')
    ap.add_argument('--max', type=int, default=0, help='with --odd: keep this many, the ones farthest from the arm centre (0 = all)')
    a = ap.parse_args()
    n1 = a.nsrc; n = n1 - 1; os.makedirs(a.out, exist_ok=True)
    H = mlp.load(a.src, {n1})[n1]
    R = [tuple(r) for r in H]
    assert len(R) == n1, 'the file holds %d squares of n = %d' % (len(R), n1)
    A = np.array(R); s = mlp.side(H)
    X = A[:, 0] - A[:, 0].min(); Y = A[:, 1] - A[:, 1].min()
    d = np.degrees(A[:, 2]) % 90.0; d = np.where(d > 45, d - 90, d); T = np.abs(d) > 0.5
    G = arms(X, Y, T)
    cen = [np.array([X[g].mean(), Y[g].mean()]) for g in G]
    cand = []
    for gi, g in enumerate(G):
        P = np.stack([X[g], Y[g]], 1); c = P.mean(0)
        w, v = np.linalg.eigh(np.cov((P - c).T)); ax = v[:, int(np.argmax(w))]
        t = (P - c) @ ax; order = np.argsort(t)
        for end, sel in (('low', order[:a.per]), ('high', order[::-1][:a.per])):
            tip = P[sel[0]]
            other = min((float(np.hypot(*(tip - cen[j]))) for j in range(len(G)) if j != gi), default=1e9)
            for rank, j in enumerate(sel):
                cand.append((rank, other, gi, end, int(g[j])))
    cand.sort()
    if a.odd:
        # the squares whose tilt is more than 2.5 degrees from the two main tilts of their arm, and the tilted
        # squares outside every arm: the fillers of the end zones
        cand = []; inarm = set()
        for gi, g in enumerate(G):
            inarm.update(int(i) for i in g)
            cnt = collections.Counter(np.round(np.abs(d[g])).astype(int).tolist()); main = [k for k, _ in cnt.most_common(2)]
            for i in g:
                if min(abs(abs(d[i]) - m) for m in main) > 2.5: cand.append((0, 0.0, gi, 'odd tilt', int(i)))
        cand += [(0, 0.0, -1, 'outside', int(i)) for i in np.where(T)[0] if int(i) not in inarm]
        # the ones farthest from the centre of their arm first: those are at the arm ends
        far = lambda q: -float(np.hypot(X[q[4]] - cen[q[2]][0], Y[q[4]] - cen[q[2]][1])) if q[2] >= 0 else 0.0
        cand.sort(key=far)
        if a.max: cand = cand[:a.max]
    print('source n = %d, side %.9f, %d tilted squares in %d arm(s) of %s' % (n1, s, int(T.sum()), len(G), [len(g) for g in G]))
    for k, (rank, other, gi, end, i) in enumerate(cand):
        path = '%s/%d-%s%d.csv' % (a.out, n, a.tag, k)
        with open(path + '.tmp', 'w', newline='') as h:
            w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
            for j, (x, y, g) in enumerate(r for q, r in enumerate(R) if q != i):
                w.writerow([n, j, repr(float(x)), repr(float(y)), repr(float(g))])
        os.rename(path + '.tmp', path)
        print('%s: arm %d, %s, square %d at (%.2f, %.2f) %+.1f deg, %.1f from the next arm' % (
            os.path.basename(path), gi, end, i, X[i] + 0.5, Y[i] + 0.5, d[i], other))
    return 0


if __name__ == '__main__':
    sys.exit(main())
