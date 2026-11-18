#!/usr/bin/env python3
"""Sub-window scan: does a square window of a held packing hold more squares than we hold at that side?

For a held packing of N squares, every axis-aligned square window [a, a+s] x [b, b+s] that contains c whole
squares is a packing of c squares in side s. The best window has its left edge on some square's left extent
and its bottom edge on some square's bottom extent, so those are the only anchors tried. For each anchor the
squares to its upper right are sorted by the side they need; the k-th one gives the smallest side that holds
k squares from that anchor. A hit is a count c with side below the held L(c) by more than --tol.
(Joost de Winter's above324 packings were found this way from Couzo's; the border step is its inverse.)

  literature_window.py scan HELD.csv HELD_DETAILS.csv OUT.tsv [--min-n 30] [--mod K,R] [--tol 1e-7] [--min-drop 1]
A negative --tol lists near misses (windows up to -tol above the held side), the starts for a re-quench;
--min-drop D keeps only windows at least D squares smaller than their donor.
  literature_window.py take HELD.csv HELD_DETAILS.csv OUT_DIR HITS.tsv [HITS.tsv ...]

scan writes one row per (c, donor N, a, b, s) hit, best side per (c, donor). take builds the best hit per c,
passes it through floatsafe and keeps it when it scores below the held score by more than 1e-10; it writes
OUT_DIR/<c>.csv and appends to OUT_DIR/take.tsv. Run it with python -I.
"""
import argparse, csv, math, os, sys
from pathlib import Path

LANE = str(Path(__file__).resolve().parent)
sys.path.insert(0, LANE)
import numpy as np  # noqa: E402


def extents(rows):
    P = np.array([(float(r['x']), float(r['y']), float(r['angle'])) for r in rows])
    h = (np.abs(np.cos(P[:, 2])) + np.abs(np.sin(P[:, 2]))) / 2
    return P[:, 0] - h, P[:, 0] + h, P[:, 1] - h, P[:, 1] + h


def anchors(v):
    """Distinct values of v, one per 1e-7 cluster (its smallest member)."""
    s = np.sort(v)
    keep = np.concatenate(([True], np.diff(s) > 1e-7))
    return s[keep]


def scan_one(rows, L, tol, drop=1):
    """-> {c: (s, a, b)} for the counts c this packing's windows win."""
    x0, x1, y0, y1 = extents(rows)
    N = len(rows)
    Lc = np.array([L.get(c, 0.0) for c in range(0, N + 1)])
    B = anchors(y0)
    best = {}
    for a in anchors(x0):
        m = x0 >= a - 1e-12
        if m.sum() < 2:
            continue
        w = x1[m] - a
        yy0, yy1 = y0[m], y1[m]
        S = np.maximum(w[None, :], yy1[None, :] - B[:, None])          # side each square needs, per b
        S[yy0[None, :] < B[:, None] - 1e-12] = np.inf                   # squares below the bottom edge
        S.sort(axis=1)
        k = S.shape[1]
        bi = S.argmin(axis=0)                                           # best bottom edge per count
        sm = S[bi, np.arange(k)]
        for j in np.nonzero(sm < Lc[1:k + 1] - tol)[0]:                 # column j holds j + 1 squares
            c, s = int(j) + 1, float(sm[j])
            if c <= N - drop and (c not in best or s < best[c][0]):
                best[c] = (s, float(a), float(B[bi[j]]))
    return best


def load(held_csv):
    P = {}
    for r in csv.DictReader(open(held_csv)):
        P.setdefault(int(r['n']), []).append(r)
    return P


def cmd_scan(a):
    L = {int(r['n']): float(r['L']) for r in csv.DictReader(open(a.details))}
    P = load(a.held)
    K, R = (int(v) for v in a.mod.split(','))
    with open(a.out, 'w') as h:
        h.write('c\tdonor\ts\theld_L\ta\tb\n')
        for N in sorted(P):
            if N < a.min_n or N % K != R:
                continue
            for c, (s, xa, yb) in sorted(scan_one(P[N], L, a.tol, a.min_drop).items()):
                h.write('%d\t%d\t%r\t%r\t%r\t%r\n' % (c, N, s, L[c], xa, yb)); h.flush()
                if a.tol > 0:
                    print('hit', c, 'from', N, 's %.9f' % s, 'held %.9f' % L[c], flush=True)
    print('scan done', a.out)


def cmd_take(a):
    import floatsafe
    score = {int(r['n']): float(r['score']) for r in csv.DictReader(open(a.details))}
    P = load(a.held)
    best = {}
    for f in a.hits:
        for r in csv.DictReader(open(f), delimiter='\t'):
            c = int(r['c'])
            if c not in best or float(r['s']) < float(best[c]['s']):
                best[c] = r
    os.makedirs(a.out, exist_ok=True)
    tsv = os.path.join(a.out, 'take.tsv')
    fresh = not os.path.exists(tsv)
    kept, tot = 0, 0.0
    with open(tsv, 'a') as h:
        if fresh:
            h.write('n\theld\tnew\tgain\tsource\tlicence\n')
        for c, r in sorted(best.items()):
            N, s, xa, yb = int(r['donor']), float(r['s']), float(r['a']), float(r['b'])
            x0, x1, y0, y1 = extents(P[N])
            inside = (x0 >= xa - 1e-12) & (y0 >= yb - 1e-12) & (x1 <= xa + s + 1e-12) & (y1 <= yb + s + 1e-12)
            pick = [q for q, ok in zip(P[N], inside) if ok][:c]
            if len(pick) != c:
                print('drop', c, 'window of', N, 'holds', len(pick)); continue
            rows = [{'n': str(c), 'square_id': str(i), 'x': repr(float(q['x']) - xa), 'y': repr(float(q['y']) - yb),
                     'angle': q['angle']} for i, q in enumerate(pick)]
            _, fr, sc, e = floatsafe.work((c, rows))
            if fr is None or not (sc < score[c] - 1e-10):
                print('drop', c, 'from', N, sc, score[c], e); continue
            with open(os.path.join(a.out, '%d.csv' % c), 'w', newline='') as g:
                w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for q in fr:
                    w.writerow([q['n'], q['square_id'], q['x'], q['y'], q['angle']])
            print('keep', c, 'from', N, 'gain %.3e' % (score[c] - sc), 'dilation', e, flush=True)
            h.write('%d\t%r\t%r\t%.3e\t%s\t%s\n' % (c, score[c], sc, score[c] - sc,
                    'sub-window of held n=%d (literature_window.py)' % N, 'ours, on the held n=%d' % N))
            kept += 1; tot += score[c] - sc
    print('kept', kept, 'gain', repr(tot))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('scan'); s.add_argument('held'); s.add_argument('details'); s.add_argument('out')
    s.add_argument('--min-n', type=int, default=30); s.add_argument('--mod', default='1,0')
    s.add_argument('--tol', type=float, default=1e-7)
    s.add_argument('--min-drop', type=int, default=1); s.set_defaults(f=cmd_scan)
    t = sub.add_parser('take'); t.add_argument('held'); t.add_argument('details'); t.add_argument('out')
    t.add_argument('hits', nargs='+'); t.set_defaults(f=cmd_take)
    a = ap.parse_args(); a.f(a)


if __name__ == '__main__':
    main()
