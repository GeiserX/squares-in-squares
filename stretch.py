#!/usr/bin/env python3
"""Stretch a held packing to a larger side: same fractional part, side + d.

A large-n best is two upright corner grids with a tilted channel along a
diagonal. Cut the template across that channel (on x + y = c), shift the far
side by (d, d), copy the band c - 2d < x + y <= c into the gap (it lands
exactly where the shifted part left room, so only the seam at c can clash),
then fill what is left with upright squares on the four corner lattices of the
new box. The result is rigid moves plus a greedy fill, so it is feasible at
side L0 + d as built; any subset of it is too. It beats our best for target n
when it holds at least n squares and L0 + d is below our current side for n.

Integer d keeps both corner grids on their corner lattices, which is why the
fractional part (the "family" of the side) carries over.

  stretch.py --best DIR [DIR ...] --cur per-n.tsv --out OUTDIR [--procs P]
             [--n0 a,b,c] [--dmax 30] [--cuts 13]

DIR holds <n>.csv (Kaggle rows) and <n>.score; per n the lowest score wins.
--cur is the per-n table (n, score, L) the gain is measured against. Each
candidate is checked with the official metric; winners land in OUTDIR/best/
and OUTDIR/found.tsv (n, score, L, n0, d, c, orient).
"""
import argparse, csv, math, os, sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kaggle_metric as km  # noqa: E402

TOL = 1e-9
EPS = (1e-12, 1e-11, 1e-10, 1e-9, 1e-8, 1e-7)


def hw(t):
    return (abs(math.cos(t)) + abs(math.sin(t))) / 2


def sep(a, b):
    """True if unit squares a=(x,y,t), b do not overlap (SAT, touching ok)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    if dx * dx + dy * dy >= 2.0:
        return True
    for tt in (a[2], b[2]):
        for k in (0.0, math.pi / 2):
            phi = tt + k
            c, s = math.cos(phi), math.sin(phi)
            p = abs(dx * c + dy * s)
            h = (abs(math.cos(a[2] - phi)) + abs(math.sin(a[2] - phi))) / 2 \
                + (abs(math.cos(b[2] - phi)) + abs(math.sin(b[2] - phi))) / 2
            if p >= h - TOL:
                return True
    return False


class Grid:
    def __init__(self):
        self.cells = {}
        self.sq = []

    def key(self, x, y):
        return (int(math.floor(x / 1.5)), int(math.floor(y / 1.5)))

    def fits(self, s):
        kx, ky = self.key(s[0], s[1])
        for i in (kx - 1, kx, kx + 1):
            for j in (ky - 1, ky, ky + 1):
                for q in self.cells.get((i, j), ()):
                    if not sep(s, self.sq[q]):
                        return False
        return True

    def add(self, s):
        self.cells.setdefault(self.key(s[0], s[1]), []).append(len(self.sq))
        self.sq.append(s)


def load(path):
    z = [(float(r['x']), float(r['y']), float(r['angle'])) for r in csv.DictReader(open(path))]
    lo_x = min(x - hw(t) for x, y, t in z)
    lo_y = min(y - hw(t) for x, y, t in z)
    z = [(x - lo_x, y - lo_y, t) for x, y, t in z]
    L = max(max(x + hw(t), y + hw(t)) for x, y, t in z)
    return z, L


def stretch(z, L0, d, c, orient):
    """Layout in [0, L0+d]^2. orient 1 mirrors x first (the other diagonal)."""
    if orient:
        z = [(L0 - x, y, -t) for x, y, t in z]
    L1 = L0 + d
    g = Grid()
    inside = lambda s: (s[0] - hw(s[2]) >= -TOL and s[1] - hw(s[2]) >= -TOL
                        and s[0] + hw(s[2]) <= L1 + TOL and s[1] + hw(s[2]) <= L1 + TOL)
    for x, y, t in z:                      # rigid part: stay + shifted
        s = (x, y, t) if x + y <= c else (x + d, y + d, t)
        if g.fits(s):
            g.add(s)
    for x, y, t in z:                      # band copy into the gap
        if c - 2 * d < x + y <= c:
            s = (x + d, y + d, t)
            if inside(s) and g.fits(s):
                g.add(s)
    m = int(math.floor(L1 + 1e-12))
    for i in range(m):                     # four corner lattices
        for j in range(m):
            for s in ((L1 - 0.5 - i, 0.5 + j, 0.0), (0.5 + i, L1 - 0.5 - j, 0.0),
                      (0.5 + i, 0.5 + j, 0.0), (L1 - 0.5 - i, L1 - 0.5 - j, 0.0)):
                if g.fits(s):
                    g.add(s)
    z1 = g.sq
    if orient:
        z1 = [(L1 - x, y, -t) for x, y, t in z1]
    return z1, L1


def to_rows(n, z, eps):
    xs = [p[0] for p in z]; ys = [p[1] for p in z]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    f = 1.0 + eps
    return [dict(n=str(n), square_id=str(i), x=repr(cx + (x - cx) * f), y=repr(cy + (y - cy) * f),
                 angle=repr(t)) for i, (x, y, t) in enumerate(z)]


def verify(n, z):
    for e in EPS:
        rows = to_rows(n, z[:n], e)
        _, s, Ls, why = km.evaluate_single_puzzle(n, rows)
        if why == 'ok':
            return s, Ls, rows
    return None


def job(a):
    n0, path, L0, d, cuts, Lcur = a
    z, L0m = load(path)
    out = []
    L1 = L0m + d
    # targets: n with our side above L1 (minus a hair for the eps dilation)
    tg = [n for n, L in Lcur.items() if L > L1 + 1e-6]
    if not tg:
        return out
    need = min(tg)
    for orient in (0, 1):
        for k in range(1, cuts + 1):
            c = 2 * L0m * k / (cuts + 1)
            z1, _ = stretch(z, L0m, d, c, orient)
            N = len(z1)
            if N < need:
                continue
            for n in sorted(t for t in tg if t <= N):
                r = verify(n, z1)
                if r and r[0] < Lcur_score[n] - 1e-13:
                    out.append((n, r[0], r[1], n0, d, c, orient, r[2]))
    return out


def worker_init(cs):
    global Lcur_score
    Lcur_score = cs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--best', nargs='+', required=True)
    ap.add_argument('--cur', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--procs', type=int, default=2)
    ap.add_argument('--n0', default='')
    ap.add_argument('--dmax', type=int, default=30)
    ap.add_argument('--cuts', type=int, default=13)
    ap.add_argument('--slack', type=float, default=0.97)
    a = ap.parse_args()
    cur = {int(r['n']): (float(r['score']), float(r['L']))
           for r in csv.DictReader(open(a.cur), delimiter='\t')}
    Lcur = {n: v[1] for n, v in cur.items()}
    Scur = {n: v[0] for n, v in cur.items()}
    best = {}
    for dname in a.best:
        for p in Path(dname).glob('*.score'):
            n = int(p.stem)
            s = float(p.read_text())
            if n not in best or s < best[n][0]:
                best[n] = (s, p.with_suffix('.csv'))
    only = {int(x) for x in a.n0.split(',') if x}
    jobs = []
    for n0, (s, path) in sorted(best.items()):
        if only and n0 not in only:
            continue
        L0 = (s + 1) * math.sqrt(n0)
        if abs(L0 - round(L0)) < 1e-9:
            continue
        for d in range(1, a.dmax + 1):
            L1 = L0 + d
            if L1 > Lcur[1000]:
                break
            k = max([n for n in Lcur if Lcur[n] <= L1 + 1e-12], default=0)
            if n0 + a.slack * (L1 * L1 - L0 * L0) > k:   # area bound prune
                jobs.append((n0, str(path), L0, d, a.cuts, Lcur))
    print(f'{len(jobs)} template/d jobs', flush=True)
    out = Path(a.out); (out / 'best').mkdir(parents=True, exist_ok=True)
    win = {}
    with Pool(a.procs, initializer=worker_init, initargs=(Scur,)) as pool:
        for i, res in enumerate(pool.imap_unordered(job, jobs, chunksize=1)):
            for n, s, Ls, n0, d, c, o, rows in res:
                if n not in win or s < win[n][0]:
                    win[n] = (s, Ls, n0, d, c, o)
                    t = out / 'best' / f'{n}.csv.tmp'
                    with open(t, 'w', newline='') as h:
                        w = csv.writer(h, lineterminator='\n')
                        w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                        for r in rows:
                            w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
                    t.replace(out / 'best' / f'{n}.csv')
                    (out / 'best' / f'{n}.score').write_text(repr(s))
            if (i + 1) % 25 == 0:
                gain = sum(Scur[n] - v[0] for n, v in win.items())
                print(f'{i + 1}/{len(jobs)} wins={len(win)} gain={gain:.7f}', flush=True)
    with open(out / 'found.tsv', 'w') as h:
        h.write('n\tscore\tL\tn0\td\tc\torient\tgain\n')
        for n in sorted(win):
            s, Ls, n0, d, c, o = win[n]
            h.write(f'{n}\t{s!r}\t{Ls}\t{n0}\t{d}\t{c:.4f}\t{o}\t{Scur[n] - s:.10f}\n')
    gain = sum(Scur[n] - v[0] for n, v in win.items())
    print(f'done: {len(win)} puzzles improved, total gain {gain:.7f}', flush=True)


if __name__ == '__main__':
    main()
