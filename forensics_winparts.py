#!/usr/bin/env python3
"""Corner windows of every layout as part versions for forensics_pool.py build.

forensics_pool.py build puts two parts into opposite corners of one square. A part only needs a side fraction below
the target's fraction; it need not be the best layout of its count. The squares that lie whole in a corner window of
any layout are such a part, and their far corner is the ragged edge of the window, which often leaves room for the
other part. The 450 of round 20 is the 202 squares in a corner window of the round 19 263 and a public 52.

Control (round 20): on a merge without the forensics takes, build --only 450 from the round 19 versions alone gives no
layout (376 pairs, each one square short); with the corner windows of that merge it gives 450 at 21.7243727098.

This tool reads every corner window of every layout in the packing files, keeps for each count the KEEP lowest
windows whose side fraction is below FMAX, adds them to the versions of a pool pickle and writes a new pickle.

Usage: forensics_winparts.py BASE.pkl OUT.pkl FMAX KEEP FILE.csv [FILE.csv ...]
  FILE.csv in the submission layout (id,n,square_id,x,y,angle) or the per-n layout (n,square_id,x,y,angle)
"""
import sys, os, csv, math, pickle, collections, time
import numpy as np
LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
import forensics_compose as fc
import forensics_pool as fp


def layouts(p):
    L = collections.defaultdict(list)
    with open(p) as h:
        for r in csv.DictReader(h):
            try:
                L[int(r['n'])].append((fp.fnum(r['x']), fp.fnum(r['y']), fp.fnum(r['angle'])))
            except (KeyError, ValueError):
                continue
    return {n: v for n, v in L.items() if len(v) == n}


def windows(A, fmax):
    """(count, window side, flip x, flip y, index order) of every corner window with a side fraction below fmax."""
    s, Q = fc.frame(A); K = fc.corners(Q); out = []
    for fx in (0, 1):
        for fy in (0, 1):
            X = K[:, :, 0] if not fx else s - K[:, :, 0]; Y = K[:, :, 1] if not fy else s - K[:, :, 1]
            ext = np.maximum(X.max(1), Y.max(1)); o = np.argsort(ext); e = ext[o]
            for c in range(2, len(A)):
                if e[c] <= e[c - 1] + 1e-9:
                    continue          # a tie: the window of side e[c-1] holds more than c squares
                m = math.isqrt(c)
                if c == m * m or e[c - 1] - m >= fmax or e[c - 1] < m:
                    continue
                out.append((c, float(e[c - 1]), fx, fy, o[:c]))
    return Q, out


def main():
    base, outp, fmax, keep, files = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4]), sys.argv[5:]
    V = pickle.load(open(base, 'rb')); t0 = time.time()
    vers = collections.defaultdict(dict)
    for n, L in V.items():
        for s, Q, name in L:
            key = (round(s, 7), round(float(np.sort(Q[:, 0] + 3 * Q[:, 1])[:5].sum()), 4)); vers[n][key] = (s, Q, name)
    cand = collections.defaultdict(list); nlay = 0
    for p in files:
        for n, A in sorted(layouts(p).items()):
            Q, W = windows(A, fmax); nlay += 1
            for c, w, fx, fy, idx in W:
                cand[c].append((w, p, n, fx, fy, Q, idx))
    add = 0
    for c, L in cand.items():
        L.sort(key=lambda r: r[0]); got = 0
        for w, p, n, fx, fy, Q, idx in L:
            if got >= keep:
                break
            if fp.add_version(vers, c, [tuple(q) for q in Q[idx]], 'window %d of n = %d corner %d%d [%s]' % (c, n, fx, fy, os.path.basename(p))):
                got += 1; add += 1
    W2 = {n: sorted(v.values(), key=lambda x: x[0]) for n, v in vers.items()}
    pickle.dump(W2, open(outp + '.tmp', 'wb')); os.replace(outp + '.tmp', outp)
    print('%d layouts, %d counts with a window below fraction %.3f, %d window versions added, %d n in the pickle, %.0f s' % (nlay, len(cand), fmax, add, len(W2), time.time() - t0))


if __name__ == '__main__':
    main()
