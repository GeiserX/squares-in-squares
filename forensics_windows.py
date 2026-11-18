"""Windows of a layout: the squares that lie whole inside a square window are a packing of that count.

A window that is smaller than the side to beat of its count is a better packing of that count.

  python forensics_windows.py corners MERGED.csv DETAILS.csv
  python forensics_windows.py walls   MERGED.csv DETAILS.csv
  python forensics_windows.py any     MERGED.csv DETAILS.csv [--deadline EPOCH] [--only N,N,...]
  python forensics_windows.py pool    FILES.txt  DETAILS.csv [--deadline EPOCH] [--bar 2e-10]
  python forensics_windows.py near    MERGED.csv DETAILS.csv OUT_DIR [--within 1e-4] [--top 60]
  python forensics_windows.py closures DETAILS.csv [--bar 2e-10]

corners: the four corner windows of every layout, every window side.
walls:   windows along a wall, starting at the edge of every square, in all 8 symmetries.
any:     windows with the lower left corner at the left edge of one square and the bottom edge of
         another. Layouts go in a seeded random order until the deadline.
pool:    the corner windows of every distinct layout in a list of packing files. A count is kept
         only when its squares do not overlap: a public file may hold layouts that are not packings.
near:    corner windows that end a little above the side to beat, written to OUT_DIR as starts for
         a quench (list.tsv and one csv per count).
closures: the rules that need no layout: one square less, one row and one column more, the 10 in
         the corner and the 26 in the corner. Prints every n that one of them would lower.

MERGED.csv holds one layout per n (the submission format). DETAILS.csv gives the side to beat per n.
Control: run it with the details of an older round. The n that a later take lowered by the corner rule
must come out of the window of their larger n (497 out of 639 against the round 16 details).
"""
import math
import random
import sys
import time

import numpy as np

import forensics_compose as fc
import forensics_pool as fp

EPS = 1e-9


def sides(details):
    """The side to beat for every n: m for a grid, m + f where the table has it, else m + 1."""
    _, fh = fc.held_f(details)
    side = np.full(1002, np.inf)
    for n in range(1, 1001):
        m, k = fc.mk(n)
        side[n] = m if k == 0 else (m + fh[(m, k)] if (m, k) in fh else m + 1.0)
    return side


def boxes(P):
    """Frame of a layout and the axis box of every square."""
    s, Q = fc.frame(P)
    h = (np.abs(np.cos(Q[:, 2])) + np.abs(np.sin(Q[:, 2]))) / 2
    return s, Q[:, 0], Q[:, 1], h


def note(best, side, n, e, where):
    """Record every count whose window side e (sorted) is below the side to beat."""
    c = np.arange(1, len(e) + 1)
    g = side[c] - e
    for i in np.nonzero((g > EPS) & (c < n))[0]:
        cc = int(c[i])
        gg = g[i] / math.sqrt(cc)
        if cc not in best or gg > best[cc][0]:
            best[cc] = (gg, n, where, float(e[i]), float(side[cc]))


def wall_windows(M, side, walls):
    best = {}
    nwin = 0
    for n in sorted(M):
        s, x0, y0, h = boxes(M[n])
        for sym in range(8):
            if not walls and sym & 4:
                continue
            x, y = x0.copy(), y0.copy()
            if sym & 1:
                x = s - x
            if sym & 2:
                y = s - y
            if sym & 4:
                x, y = y, x
            xhi, ylo, yhi = x + h, y - h, y + h
            starts = np.unique(np.round(ylo, 7)) if walls else [0.0]
            for a in starts:
                sel = ylo >= a - EPS
                e = np.sort(np.maximum(xhi[sel], yhi[sel] - a))
                nwin += 1
                note(best, side, n, e, 'sym %d start %.6f' % (sym, a))
    return best, nwin, sorted(M)


def any_windows(M, side, dead, only):
    best = {}
    nwin = 0
    done = []
    order = sorted(M)
    random.Random(1).shuffle(order)
    if only:
        order = only
    for n in order:
        if dead and time.time() > dead:
            break
        s, x, y, h = boxes(M[n])
        xlo, xhi, ylo, yhi = x - h, x + h, y - h, y + h
        for a in np.unique(np.round(xlo, 7)):
            sx = xlo >= a - EPS
            ex, yl, yh = xhi[sx] - a, ylo[sx], yhi[sx]
            for b in np.unique(np.round(yl, 7)):
                sel = yl >= b - EPS
                e = np.sort(np.maximum(ex[sel], yh[sel] - b))
                nwin += 1
                note(best, side, n, e, 'start %.6f, %.6f' % (a, b))
        done.append(n)
    return best, nwin, done


def corner_extents(x, y, h):
    """For each of the four corners: how far each square reaches from that corner."""
    xlo, xhi, ylo, yhi = x - h, x + h, y - h, y + h
    X0, X1, Y0, Y1 = xlo.min(), xhi.max(), ylo.min(), yhi.max()
    return [np.maximum(ex, ey) for ex, ey in ((xhi - X0, yhi - Y0), (X1 - xlo, yhi - Y0), (xhi - X0, Y1 - ylo), (X1 - xlo, Y1 - ylo))]


def pool_windows(files, side, dead, bar):
    """Corner windows of every distinct layout of every file. Returns best, layouts, files read, files skipped, windows refused."""
    import pandas as pd
    best = {}
    seen = set()
    nlay = nfile = nbad = refused = 0
    for fi, f in enumerate(files):
        if dead and time.time() > dead:
            break
        try:
            o = 1 if open(f).readline().strip().split(',')[0] == 'id' else 0
            df = pd.read_csv(f, header=0, usecols=[o, o + 2, o + 3, o + 4], dtype=str)
            A = np.column_stack([df.iloc[:, j].str.lstrip('s').astype(float).to_numpy() for j in range(4)])
        except Exception as ex:
            print('skip %s: %s' % (f, str(ex)[:80]), flush=True)
            nbad += 1
            continue
        nfile += 1
        A = A[np.argsort(A[:, 0], kind='stable')]
        ns, st, cn = np.unique(A[:, 0].astype(int), return_index=True, return_counts=True)
        for n, i0, c0 in zip(ns, st, cn):
            if n != c0 or n < 5 or n > 1000:
                continue
            x, y, a = A[i0:i0 + c0, 1], A[i0:i0 + c0, 2], A[i0:i0 + c0, 3]
            h = (np.abs(np.cos(a)) + np.abs(np.sin(a))) / 2
            s = max((x + h).max() - (x - h).min(), (y + h).max() - (y - h).min())
            m = math.isqrt(int(n))
            if not np.isfinite(s) or s < m - EPS or s > m + 1.0 + 1e-6:
                continue
            key = (int(n), round(float(s), 9), round(float(x.sum() - n * (x - h).min() + 3 * (y.sum() - n * (y - h).min())), 5))
            if key in seen:
                continue
            seen.add(key)
            nlay += 1
            for ci, ee in enumerate(corner_extents(x, y, h)):
                od = np.argsort(ee)
                e = ee[od]
                c = np.arange(1, n + 1)
                g = (side[c] - e) / np.sqrt(c)
                for i in np.nonzero((g > bar) & (c < n))[0]:
                    cc = int(c[i])
                    if cc in best and g[i] <= best[cc][0]:
                        continue
                    P = np.column_stack([x, y, a])[od[:cc]]
                    if cc > 1 and fc.worst_overlap(P) < -1e-7:
                        refused += 1
                        continue
                    best[cc] = (float(g[i]), int(n), 'file %d corner %d, %s' % (fi, ci, f), float(e[i]), float(side[cc]))
    return best, nlay, nfile, nbad, refused


def near_windows(M, side, within, top, out):
    """Corner windows that end at most `within` (score) above the side to beat. Grid counts are left out."""
    import os
    os.makedirs(out, exist_ok=True)
    best = {}
    for n, sq in M.items():
        if n < 30 or len(sq) != n:
            continue
        A = np.array(sq, float)
        h = (np.abs(np.cos(A[:, 2])) + np.abs(np.sin(A[:, 2]))) / 2
        for ci, ee in enumerate(corner_extents(A[:, 0], A[:, 1], h)):
            od = np.argsort(ee)
            e = ee[od]
            c = np.arange(1, n + 1)
            g = (e - side[c]) / np.sqrt(c)
            for i in np.nonzero((g > 2e-9) & (g < within) & (c < n - 1) & (c >= 20))[0]:
                cc = int(c[i])
                m, k = fc.mk(cc)
                if k == 0 or abs(side[cc] - m - 1.0) < 1e-6:
                    continue
                if cc not in best or g[i] < best[cc][0]:
                    best[cc] = (float(g[i]), n, ci, float(e[i]), float(side[cc]), A[od[:cc]].copy())
    rows = sorted(best.items(), key=lambda kv: kv[1][0])
    with open(out + '/list.tsv', 'w') as fh:
        fh.write('count\tfrom_n\tcorner\twindow\tto_beat\tscore_above\n')
        for cc, v in rows[:top]:
            fh.write('%d\t%d\t%d\t%.10f\t%.10f\t%.3e\n' % (cc, v[1], v[2], v[3], v[4], v[0]))
            fc.write_csv('%s/%d.csv' % (out, cc), cc, fc.frame([tuple(r) for r in v[5]])[1])
    return rows


def closures(details, bar):
    """Every n that a rule with no layout would lower: (rule, n, from n, side now, side by the rule, score gain)."""
    import csv
    L = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    out = []
    for n in range(1, 1001):
        m, k = fc.mk(n)
        if n + 1 in L and (L[n] - L[n + 1]) / math.sqrt(n) > bar:
            out.append(('one square less', n, n + 1, L[n], L[n + 1], (L[n] - L[n + 1]) / math.sqrt(n)))
        n2 = (m + 1) ** 2 + k
        if n2 in L and (L[n2] - L[n] - 1) / math.sqrt(n2) > bar:
            out.append(('one row and one column more', n2, n, L[n2], L[n] + 1, (L[n2] - L[n] - 1) / math.sqrt(n2)))
        for a, fpart, name in ((3, math.sqrt(0.5), 'the 10 in the corner'), (5, 1.5 * math.sqrt(2) - 1.5, 'the 26 in the corner')):
            n3 = (m + a) ** 2 + k + 1
            if k > 0 and n3 in L and k + 1 <= 2 * (m + a):
                s = m + a + max(L[n] - m, fpart)
                if (L[n3] - s) / math.sqrt(n3) > bar:
                    out.append((name, n3, n, L[n3], s, (L[n3] - s) / math.sqrt(n3)))
    return sorted(out, key=lambda r: -r[5])


def opt(argv, name, default):
    return float(argv[argv.index(name) + 1]) if name in argv else default


def main(argv):
    if len(argv) < 3 or argv[1] not in ('corners', 'walls', 'any', 'pool', 'near', 'closures') or (len(argv) < 4 and argv[1] != 'closures'):
        print(__doc__)
        return 2
    if argv[1] == 'closures':
        bar = opt(argv, '--bar', 2e-10)
        rows = closures(argv[2], bar)
        print('closures: %d n that a rule would lower by more than %.1e' % (len(rows), bar))
        for r in rows:
            print('   %s: n %d from n %d: side %.10f against %.10f, gain %.3e' % r)
        return 0
    mode, merged, details = argv[1], argv[2], argv[3]
    side = sides(details)
    t0 = time.time()
    if mode == 'pool':
        files = [l.strip() for l in open(merged) if l.strip()]
        best, nlay, nfile, nbad, refused = pool_windows(files, side, opt(argv, '--deadline', 0.0), opt(argv, '--bar', 2e-10))
        print('pool: %d files read (%d skipped), %d distinct layouts, %d corner windows, %.0f s; windows refused because their squares overlap: %d; counts with a window below the side to beat: %d, sum %.3e'
              % (nfile, nbad, nlay, 4 * nlay, time.time() - t0, refused, len(best), sum(v[0] for v in best.values())))
        for cc, v in sorted(best.items(), key=lambda kv: -kv[1][0]):
            print('   n %d from n %d (%s): window %.9f against %.9f, gain %.3e' % (cc, v[1], v[2], v[3], v[4], v[0]))
        return 0
    if mode == 'near':
        if len(argv) < 5:
            print(__doc__)
            return 2
        within, top = opt(argv, '--within', 1e-4), int(opt(argv, '--top', 60))
        rows = near_windows(fp.load_merged(merged), side, within, top, argv[4])
        print('near: %d counts have a corner window within %.1e (score) above the side to beat; the first %d are in %s' % (len(rows), within, min(top, len(rows)), argv[4]))
        for cc, v in rows[:top]:
            print('   count %d from n %d corner %d: window %.9f, to beat %.9f, above by %.3e' % (cc, v[1], v[2], v[3], v[4], v[0]))
        return 0
    dead = float(argv[argv.index('--deadline') + 1]) if '--deadline' in argv else 0.0
    only = [int(v) for v in argv[argv.index('--only') + 1].split(',')] if '--only' in argv else None
    M = fp.load_merged(merged)
    t0 = time.time()
    if mode == 'any':
        best, nwin, done = any_windows(M, side, dead, only)
    else:
        best, nwin, done = wall_windows(M, side, mode == 'walls')
    total = sum(v[0] for v in best.values())
    print('%s: %d layouts, %d windows, %.0f s; counts with a window below the side to beat: %d, sum %.3e'
          % (mode, len(done), nwin, time.time() - t0, len(best), total))
    if mode == 'any':
        print('layouts done:', ' '.join(str(n) for n in sorted(done)))
    for cc, v in sorted(best.items(), key=lambda kv: -kv[1][0]):
        print('   n %d from n %d (%s): window %.9f against %.9f, gain %.3e' % (cc, v[1], v[2], v[3], v[4], v[0]))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
