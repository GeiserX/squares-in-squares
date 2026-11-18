#!/usr/bin/env python3
"""Corner swap: a loose corner of one layout takes a tighter packing with more squares.

Read a host layout of n squares at side s from one of its corners. The squares that lie whole in the corner window
of side w are a packing of c squares. When w is at least the best side of c + j, put that best packing (any of its
8 symmetries) into the window in their place. The host squares that cross the edge of the window stay. When none of
them meets a new square, the result is a packing of n + j squares at side s, and it is better than the table
when s is below the side to beat of n + j. When some of them meet a new square, up to j - 1 of them may leave, and
the result holds n + j less the squares that left. Only hosts with s below the side to beat of n + 1 are read.

forensics_pool.py build is the case where the host is a part and plain grid. Here the host is any layout: an end
of a band, a ragged corner. The k123 lane read the board's 910 as our 909 with one square more at an end (round 20).

Usage: forensics_swap.py DETAILS.csv BEST.csv OUT_DIR [--max-j 2] [--pad 2e-10] [--ctl] FILE.csv [FILE.csv ...]
  BEST.csv   the merged best file (submission layout); the new corner packings come from it
  FILE.csv   host layouts, submission layout or per-n layout
  --ctl      report every valid swap, not only the ones below the side to beat (for the control)
"""
import sys, os, csv, math, collections, time
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forensics_compose as fc
import forensics_pool as fp

TOL = 1e-9


def layouts(p):
    L = collections.defaultdict(list)
    with open(p) as h:
        for r in csv.DictReader(h):
            try:
                L[int(r['n'])].append((fp.fnum(r['x']), fp.fnum(r['y']), fp.fnum(r['angle'])))
            except (KeyError, ValueError):
                continue
    return {n: np.array(v, float) for n, v in L.items() if len(v) == n}


def flip(Q, s, fx, fy):
    """The layout seen from corner (fx, fy): that corner goes to the origin."""
    R = Q.copy()
    if fx:
        R[:, 0] = s - R[:, 0]; R[:, 2] = -R[:, 2]
    if fy:
        R[:, 1] = s - R[:, 1]; R[:, 2] = -R[:, 2]
    return R


def main():
    argv = sys.argv[1:]
    def opt(name, default, cast):
        if name in argv:
            i = argv.index(name); v = cast(argv[i + 1]); del argv[i:i + 2]; return v
        return default
    maxj = opt('--max-j', 2, int); pad = opt('--pad', 2e-10, float)
    ctl = '--ctl' in argv
    if ctl:
        argv.remove('--ctl')
    details, bestp, out, files = argv[0], argv[1], argv[2], argv[3:]
    D = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    B = layouts(bestp); P8 = {}
    def parts(c):
        if c not in P8:
            s, Q = fc.frame(B[c]); P8[c] = (s, [fc.sym(Q, s, g) for g in range(8)])
        return P8[c]
    os.makedirs(out, exist_ok=True); t0 = time.time(); nh = 0; ncand = 0; ntest = 0; hits = []; best = {}
    for p in files:
        for n, A in sorted(layouts(p).items()):
            if n + 1 > 1000:
                continue
            s, Q = fc.frame(A); nh += 1
            want = list(range(1, maxj + 1)) if (ctl or D[n + 1] - s > pad * math.sqrt(n + 1)) else []
            if not want:
                continue
            for fx in (0, 1):
                for fy in (0, 1):
                    R = flip(Q, s, fx, fy); K = fc.corners(R)
                    ext = np.maximum(K[:, :, 0].max(1), K[:, :, 1].max(1)); o = np.argsort(ext, kind='stable'); e = ext[o]
                    lo = np.minimum(K[:, :, 0].min(1), K[:, :, 1].min(1))
                    for c in range(2, n):
                        if e[c] <= e[c - 1] + TOL:
                            continue
                        w = e[c - 1]
                        for j in want:
                            if c + j > 1000 or c + j not in B or D[c + j] > w + TOL:
                                continue
                            ncand += 1
                            rest = o[c:]
                            # host squares outside the window that reach into it (or near its edge)
                            kx = K[rest, :, 0].min(1); ky = K[rest, :, 1].min(1)
                            near = rest[(kx < w + 1e-9) & (ky < w + 1e-9)]
                            sP, S8 = parts(c + j)
                            for g in range(8):
                                Pn = S8[g]; ntest += 1
                                bad = set()
                                if len(near):
                                    KP = fc.corners(Pn); KN = K[near]
                                    tr = cKDTree(Pn[:, :2]); cand = tr.query_ball_point(R[near, :2], 1.4143)
                                    for ii, lst in enumerate(cand):
                                        if any(fc.gap(KP[jj], KN[ii]) < -TOL for jj in lst):
                                            bad.add(int(near[ii]))
                                            if len(bad) > j - 1:
                                                break
                                net = j - len(bad)
                                if net < 1 or n + net > 1000 or (not ctl and D[n + net] - s <= pad * math.sqrt(n + net)):
                                    continue
                                keep = np.array([r for r in rest if int(r) not in bad], int)
                                X = np.r_[R[keep], Pn]
                                g2 = (D[n + net] - s) / math.sqrt(n + net)
                                hits.append((g2, n + net, n, c, j, fx, fy, g, w, s, p, len(bad)))
                                k = n + net
                                if not ctl and (k not in best or g2 > best[k][0]):
                                    best[k] = (g2, X)
                                    fc.write_csv('%s/%d.csv' % (out, k), k, X)
                                if ctl and len(hits) <= 20:
                                    fc.write_csv('%s/ctl-%d-%d.csv' % (out, k, len(hits)), k, X)
                                break
    hits.sort(key=lambda r: -r[0])
    print('%d hosts, %d corner windows looser than the best side of their count plus j, %d placements, %d valid swaps, %.0f s' % (
        nh, ncand, ntest, len(hits), time.time() - t0))
    for h in hits[:40]:
        print('   n %d from host n %d [%s]: corner %d%d, window of %d squares at %.9f takes the best %d (sym %d), %d host squares out; side %.10f against %.10f, gain %.3e' % (
            h[1], h[2], os.path.basename(h[10]), h[5], h[6], h[3], h[8], h[3] + h[4], h[7], h[11], h[9], D[h[1]], h[0]))


if __name__ == '__main__':
    main()
