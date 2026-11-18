#!/usr/bin/env python3
"""Windows anywhere in a layout as part versions for forensics_pool.py build.

forensics_pool.py build puts two parts into opposite corners of one square, and the rest is plain grid. It fails
when two upright squares collide in the inner corners of the parts. A part with a free inner corner fits. The 202
of round 19 is a corner window of a 263, and its free corner gave 450 in round 20 (forensics_winparts.py).

A window anywhere in a layout has four cut sides, not two, so each of its four corners can be free. This tool
scans every window of every layout (the scan of forensics_windows.py any) but keeps only the counts that the
build can use: a count a*a + ka whose best side fraction is below the fraction of some target, with a partner
part below it too (the test of forensics_pool.py build). For each such count it keeps the KEEP lowest windows
whose side fraction is below the largest target fraction that can use the count, and adds them to the versions
of a pool pickle.

Usage: forensics_anyparts.py BASE.pkl OUT.pkl DETAILS.csv KEEP [--deadline EPOCH] FILE.csv [FILE.csv ...]
  FILE.csv in the submission layout (id,n,square_id,x,y,angle) or the per-n layout (n,square_id,x,y,angle)
"""
import sys, os, csv, math, pickle, collections, time, heapq
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forensics_compose as fc
import forensics_pool as fp

EPS = 1e-9
CNT = [0]


def usable(details, extra=2):
    """count -> the largest target side fraction (less the padding) that can use it as a part."""
    D, fh = fc.held_f(details); use = {}
    for n in range(2, 1001):
        m, k = fc.mk(n)
        if k < 2:
            continue
        ft = fh[(m, k)] - 2e-10 * math.sqrt(n)
        for a in range(1, m):
            b = m - a
            for ka in range(1, 2 * a + 1):
                na = a * a + ka
                if D[na] - a >= ft:
                    continue
                for kb in range(max(1, k - ka), min(2 * b, k - ka + extra) + 1):
                    nb = b * b + kb
                    if D[nb] - b < ft:
                        use[na] = max(use.get(na, -1.0), ft); use[nb] = max(use.get(nb, -1.0), ft)
    return use


def layouts(p):
    L = collections.defaultdict(list)
    with open(p) as h:
        for r in csv.DictReader(h):
            try:
                L[int(r['n'])].append((fp.fnum(r['x']), fp.fnum(r['y']), fp.fnum(r['angle'])))
            except (KeyError, ValueError):
                continue
    return {n: v for n, v in L.items() if len(v) == n}


def scan(A, U, cs, best, keep, tag):
    """Every window of layout A anchored at a left edge and a bottom edge; for each usable count keep the lowest."""
    s, Q = fc.frame(A)
    h = (np.abs(np.cos(Q[:, 2])) + np.abs(np.sin(Q[:, 2]))) / 2
    x, y = Q[:, 0], Q[:, 1]
    xlo, xhi, ylo, yhi = x - h, x + h, y - h, y + h
    N = len(A); nwin = 0
    cs = [c for c in cs if c < N]
    if not cs:
        return 0
    ci = np.array(cs); lim = np.array([math.isqrt(c) + U[c] for c in cs])
    for a in np.unique(np.round(xlo, 7)):
        sx = xlo >= a - EPS
        if sx.sum() <= cs[0]:
            continue
        ex, yl, yh, ix = xhi[sx] - a, ylo[sx], yhi[sx], np.nonzero(sx)[0]
        for b in np.unique(np.round(yl, 7)):
            sel = yl >= b - EPS
            if sel.sum() <= cs[0]:
                continue
            ext = np.maximum(ex[sel], yh[sel] - b); o = np.argsort(ext, kind='stable'); e = ext[o]; nwin += 1
            ok = ci < len(e)
            if not ok.any():
                continue
            c2 = ci[ok]; w = e[c2 - 1]; nxt = e[c2]
            hit = (w < lim[ok]) & (nxt > w + EPS) & (w >= np.sqrt(c2.astype(float)).astype(int))
            for j in np.nonzero(hit)[0]:
                c = int(c2[j]); wv = float(w[j]); H = best[c]
                if len(H) >= keep * 6 and -H[0][0] <= wv:
                    continue
                idx = ix[np.nonzero(sel)[0][o[:c]]]
                CNT[0] += 1; item = (-wv, CNT[0], tag + ' start %.4f,%.4f' % (a, b), Q[idx].copy())
                if len(H) < keep * 6:
                    heapq.heappush(H, item)
                else:
                    heapq.heapreplace(H, item)
    return nwin


def main():
    argv = sys.argv[1:]; dead = None
    if '--deadline' in argv:
        i = argv.index('--deadline'); dead = float(argv[i + 1]); del argv[i:i + 2]
    base, outp, details, keep, files = argv[0], argv[1], argv[2], int(argv[3]), argv[4:]
    U = usable(details); cs = sorted(U); t0 = time.time()
    print('usable part counts: %d %s' % (len(cs), cs), flush=True)
    V = pickle.load(open(base, 'rb'))
    vers = collections.defaultdict(dict)
    for n, L in V.items():
        for s, Q, name in L:
            key = (round(s, 7), round(float(np.sort(Q[:, 0] + 3 * Q[:, 1])[:5].sum()), 4)); vers[n][key] = (s, Q, name)
    best = collections.defaultdict(list); nlay = 0; nwin = 0; stop = False; CNT[0] = 0
    for p in files:
        for n, A in sorted(layouts(p).items()):
            if dead and time.time() > dead:
                stop = True; break
            nwin += scan(A, U, cs, best, keep, 'window of n = %d [%s]' % (n, os.path.basename(p))); nlay += 1
        if stop:
            break
    add = 0; per = {}
    for c, H in best.items():
        got = 0
        for negw, _, name, Q in sorted(H, key=lambda r: (-r[0], r[1])):
            if got >= keep:
                break
            if fp.add_version(vers, c, [tuple(q) for q in Q], name):
                got += 1; add += 1
        per[c] = got
    W2 = {n: sorted(v.values(), key=lambda x: x[0]) for n, v in vers.items()}
    pickle.dump(W2, open(outp + '.tmp', 'wb')); os.replace(outp + '.tmp', outp)
    print('%d layouts%s, %d windows, %d window versions added %s, %d n in the pickle, %.0f s' % (
        nlay, ' (stopped at the deadline)' if stop else '', nwin, add, sorted(per.items()), len(W2), time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
