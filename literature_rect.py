#!/usr/bin/env python3
"""Rectangle window plus upright strips: the border step and the sub-window, joined and widened.

Take a w x h rectangle window of a held packing that holds c whole squares. Put p unit columns to its right
and q unit rows above it. In a square of side S = max(w + p, h + q) that is
    c + p*floor(S) + q*floor(w)   squares (columns run the full height, rows sit over the window), or
    c + q*floor(S) + p*floor(h)   squares (rows run the full width, columns sit beside the window).
p = q = 0 is the plain sub-window; a whole packing with p = q = 1 is the border step; a window one unit
narrower than it is tall with p = 1 is the cut-out Ostashev used for n = 129. A hit is a total t with
S below the held L(t) by more than --tol.

The window's lower-left corner sits on a square's left and bottom extents. Only anchors within --reach of
the donor's corner are tried (at most --cap per axis), in each of the donor's four orientations, and only
windows that cut at most --depth off the far sides (the plain sub-window at any place and size is
literature_window.py's job).

  literature_rect.py scan HELD.csv HELD_DETAILS.csv OUT.tsv [--min-n 30] [--mod K,R] [--reach 2.05] [--cap 6] [--pq 2] [--depth 3.05]
  literature_rect.py take HELD.csv HELD_DETAILS.csv OUT_DIR HITS.tsv [HITS.tsv ...]

Run it with python -I.
"""
import argparse, csv, math, os, sys
from pathlib import Path

LANE = str(Path(__file__).resolve().parent)
sys.path.insert(0, LANE)
import numpy as np  # noqa: E402

GAP = 3e-11
SLACK = 1e-7   # windows are counted this much larger than the extents they are named by


def flip(rows, fx, fy):
    """Mirror the packing in x and/or y (a mirrored unit square at angle t is one at angle -t)."""
    out = []
    for r in rows:
        x, y, a = float(r['x']), float(r['y']), float(r['angle'])
        if fx:
            x, a = -x, -a
        if fy:
            y, a = -y, -a
        out.append((x, y, a))
    return np.array(out)


def extents(P):
    h = (np.abs(np.cos(P[:, 2])) + np.abs(np.sin(P[:, 2]))) / 2
    return P[:, 0] - h, P[:, 0] + h, P[:, 1] - h, P[:, 1] + h


def clusters(v):
    s = np.sort(v)
    return s[np.concatenate(([True], np.diff(s) > SLACK))]


def near(v, reach, cap):
    c = clusters(v)
    c = c[c <= c[0] + reach]
    if len(c) > cap:
        c = c[np.unique(np.linspace(0, len(c) - 1, cap).round().astype(int))]
    return c


def scan_one(rows, Lc, tol, reach, cap, pq, depth):
    best = {}
    N = len(rows)
    for fx in (0, 1):
        for fy in (0, 1):
            x0, x1, y0, y1 = extents(flip(rows, fx, fy))
            for a in near(x0, reach, cap):
                for b in near(y0, reach, cap):
                    m = (x0 >= a - 1e-12) & (y0 >= b - 1e-12)
                    if m.sum() < 4:
                        continue
                    wv, hv = x1[m] - a, y1[m] - b
                    W, H = np.unique(np.round(wv, 7)) + SLACK, np.unique(np.round(hv, 7)) + SLACK
                    C = np.zeros((len(W), len(H)))
                    np.add.at(C, (np.searchsorted(W, wv), np.searchsorted(H, hv)), 1)
                    C = C.cumsum(0).cumsum(1)
                    i0, j0 = np.searchsorted(W, W[-1] - depth), np.searchsorted(H, H[-1] - depth)
                    C, W, H = C[i0:, j0:], W[i0:], H[j0:]   # only windows that cut at most `depth` off each side
                    for p in range(pq + 1):
                        for q in range(pq + 1):
                            S = np.maximum(W[:, None] + p, H[None, :] + q)
                            fS = np.floor(S)
                            for mode, tot in ((1, C + p * fS + q * np.floor(W)[:, None]),
                                              (2, C + q * fS + p * np.floor(H)[None, :])):
                                if mode == 2 and (p == 0 or q == 0):
                                    continue   # same count as mode 1
                                t = tot.astype(int)
                                ok = (t <= 1000) & (t >= 5) & ((t != N) | (p + q > 0))
                                hit = ok & (S < Lc[np.minimum(t, 1000)] - tol)
                                for i, j in zip(*np.nonzero(hit)):
                                    c, s = int(t[i, j]), float(S[i, j])
                                    if c not in best or s < best[c][0]:
                                        best[c] = (s, fx, fy, float(a), float(b), float(W[i]), float(H[j]), p, q, mode)
    return best


def load(held_csv):
    P = {}
    for r in csv.DictReader(open(held_csv)):
        P.setdefault(int(r['n']), []).append(r)
    return P


def cmd_scan(a):
    L = {int(r['n']): float(r['L']) for r in csv.DictReader(open(a.details))}
    Lc = np.array([0.0] + [L[n] for n in range(1, 1001)])
    P = load(a.held)
    K, R = (int(v) for v in a.mod.split(','))
    with open(a.out, 'w') as h:
        h.write('c\tdonor\ts\theld_L\tfx\tfy\ta\tb\tw\th\tp\tq\tmode\n'); h.flush()
        for i, N in enumerate(sorted(P, reverse=True)):   # large n first: the gap to the board is there
            if i % 25 == 0:
                print('at donor', N, flush=True)
            if N < a.min_n or N % K != R:
                continue
            for c, v in sorted(scan_one(P[N], Lc, a.tol, a.reach, a.cap, a.pq, a.depth).items()):
                h.write('%d\t%d\t%r\t%r\t%s\n' % (c, N, v[0], L[c], '\t'.join(repr(x) for x in v[1:]))); h.flush()
                print('hit', c, 'from', N, 's %.9f' % v[0], 'held %.9f' % L[c], 'p,q,mode', v[7:], flush=True)
    print('scan done', a.out)


def build(rows, fx, fy, a, b, w, h, p, q, mode):
    """-> list of (x, y, angle) texts, or None."""
    P = flip(rows, fx, fy)
    x0, x1, y0, y1 = extents(P)
    m = (x0 >= a - 1e-12) & (y0 >= b - 1e-12) & (x1 <= a + w + 1e-12) & (y1 <= b + h + 1e-12)
    Q = P[m]
    if not len(Q):
        return None
    ax, by = x0[m].min(), y0[m].min()
    w, h = x1[m].max() - ax, y1[m].max() - by          # the true extents of the chosen squares
    S = max(w + (p + GAP if p else 0), h + (q + GAP if q else 0))
    out = [(repr(x - ax), repr(y - by), repr(t)) for x, y, t in Q]

    def line(k, lo, hi):   # k unit squares spread over [lo, hi]
        return [lo + 0.5 + i * ((hi - lo - 1) / (k - 1) if k > 1 else 0.0) for i in range(k)]

    cols = [w + GAP + 0.5 + i * ((S - w - GAP - 1) / (p - 1) if p > 1 else 0.0) for i in range(p)]
    rws = [h + GAP + 0.5 + i * ((S - h - GAP - 1) / (q - 1) if q > 1 else 0.0) for i in range(q)]
    if mode == 1:      # columns the full height; rows over the window only
        for cx in cols:
            out += [(repr(cx), repr(y), '0.0') for y in line(math.floor(S), 0.0, S)]
        for ry in rws:
            out += [(repr(x), repr(ry), '0.0') for x in line(math.floor(w), 0.0, w)]
    else:              # rows the full width; columns beside the window only
        for ry in rws:
            out += [(repr(x), repr(ry), '0.0') for x in line(math.floor(S), 0.0, S)]
        for cx in cols:
            out += [(repr(cx), repr(y), '0.0') for y in line(math.floor(h), 0.0, h)]
    return out


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
    prior = {}
    if not fresh:
        prior = {int(r['n']): float(r['new']) for r in csv.DictReader(open(tsv), delimiter='\t')}
    kept, tot = 0, 0.0
    with open(tsv, 'a') as h:
        if fresh:
            h.write('n\theld\tnew\tgain\tsource\tlicence\n')
        for c, r in sorted(best.items()):
            N = int(r['donor'])
            sq = build(P[N], int(r['fx']), int(r['fy']), float(r['a']), float(r['b']), float(r['w']), float(r['h']),
                       int(r['p']), int(r['q']), int(r['mode']))
            if sq is None or len(sq) < c:
                print('drop', c, 'from', N, 'built', None if sq is None else len(sq)); continue
            sq = sq[:c]   # a square too many can always be deleted
            rows = [{'n': str(c), 'square_id': str(i), 'x': x, 'y': y, 'angle': t} for i, (x, y, t) in enumerate(sq)]
            _, fr, sc, e = floatsafe.work((c, rows))
            if fr is None or not (sc < score[c] - 1e-10) or not (sc < prior.get(c, 9)):
                print('drop', c, 'from', N, sc, score[c], e); continue
            with open(os.path.join(a.out, '%d.csv' % c), 'w', newline='') as g:
                w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for z in fr:
                    w.writerow([z['n'], z['square_id'], z['x'], z['y'], z['angle']])
            print('keep', c, 'from', N, 'gain %.3e' % (score[c] - sc), 'dilation', e, flush=True)
            h.write('%d\t%r\t%r\t%.3e\t%s\t%s\n' % (c, score[c], sc, score[c] - sc,
                    'window %sx%s of held n=%d plus %s columns and %s rows (literature_rect.py)'
                    % (r['w'][:7], r['h'][:7], N, r['p'], r['q']), 'ours, on the held n=%d' % N))
            kept += 1; tot += score[c] - sc
    print('kept', kept, 'gain', repr(tot))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('scan'); s.add_argument('held'); s.add_argument('details'); s.add_argument('out')
    s.add_argument('--min-n', type=int, default=30); s.add_argument('--mod', default='1,0')
    s.add_argument('--tol', type=float, default=1e-6); s.add_argument('--reach', type=float, default=2.05)
    s.add_argument('--cap', type=int, default=6); s.add_argument('--pq', type=int, default=2)
    s.add_argument('--depth', type=float, default=3.05); s.set_defaults(f=cmd_scan)
    t = sub.add_parser('take'); t.add_argument('held'); t.add_argument('details'); t.add_argument('out')
    t.add_argument('hits', nargs='+'); t.set_defaults(f=cmd_take)
    a = ap.parse_args(); a.f(a)


if __name__ == '__main__':
    main()
