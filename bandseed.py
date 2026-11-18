#!/usr/bin/env python3
"""Tilted-band seed generator for Squares in Squares.

The per-n bests above n = 300 are not jammed grids: a band of tilted squares
runs corner to corner, with upright staircases filling the two triangles on
either side of it. This builds that layout for a container side L and a few
parameters, and searches the parameters for the smallest L that still holds
at least n squares:

  band   rows k of squares tilted by alpha, rows 1 apart, centred on the
         container's diagonal plus a perpendicular offset; each row is filled
         from one end (or centred) as far as the walls allow;
  stairs rows of upright squares pushed against the right wall (lower-right
         triangle) and against the left wall (upper-left triangle), each row
         stopping at its first collision.

The layout is a seed, not an answer: drive.py hands it to sqpack, which
removes the extra squares and relaxes the rest (perturb and shrink), and only
a result the official metric accepts with a lower score is kept.

  bandseed.py N [--seconds 60] [--Lmax L] [--out seed.txt]
"""
import argparse, math, random, sys, time

import numpy as np

TOL = 1e-9


def _half(t, phi):
    """Half-width of a unit square at angle t projected on the axis at angle phi."""
    d = t - phi
    return 0.5 * (np.abs(np.cos(d)) + np.abs(np.sin(d)))


def collides(x, y, t, X, Y, T):
    """True if the unit square (x, y, t) overlaps any square in the arrays (SAT)."""
    if len(X) == 0:
        return False
    dx, dy = X - x, Y - y
    near = dx * dx + dy * dy < 2.0
    if not near.any():
        return False
    dx, dy, T = dx[near], dy[near], T[near]
    sep = np.zeros(len(T), dtype=bool)
    for phi in (t, t + math.pi / 2):
        proj = np.abs(dx * math.cos(phi) + dy * math.sin(phi))
        sep |= proj >= 0.5 + _half(T, phi) - TOL
    for k in (0, 1):
        phi = T + k * math.pi / 2
        proj = np.abs(dx * np.cos(phi) + dy * np.sin(phi))
        sep |= proj >= _half(t, phi) + 0.5 - TOL
    return not sep.all()


def overlap(x1, y1, t1, x2, y2, t2):
    """Elementwise (broadcast) SAT test: True where two unit squares overlap."""
    dx, dy = x2 - x1, y2 - y1
    sep = np.zeros(np.broadcast(dx, t1, t2).shape, dtype=bool)
    for tt in (t1, t2):
        for k in (0.0, math.pi / 2):
            phi = tt + k
            proj = np.abs(dx * np.cos(phi) + dy * np.sin(phi))
            sep |= proj >= _half(t1, phi) + _half(t2, phi) - TOL
    return ~sep & (dx * dx + dy * dy < 2.0)


def layout(L, theta, off, w1, w2, step=0.04):
    """Squares (x, y, t) of one band layout in the square [0, L]^2.

    Stairs: an upright grid anchored at the bottom-right corner keeps the cells
    whose centre lies below the diagonal y = x + off by more than w1, and one
    anchored at the top-left corner keeps those above it by more than w2.
    Band: the channel left between them is filled greedily with squares at
    angle theta, candidates on a fine grid taken from the bottom-left corner
    along the diagonal, each placed if it fits. (A fan of angles per candidate
    was tried: no more squares, 7x slower.)
    """
    m = int(math.floor(L + 1e-12))
    g = np.arange(m) + 0.5
    GX, GY = np.meshgrid(g, g)
    GX, GY = GX.ravel(), GY.ravel()
    d_lr = ((L - GX) - GY + off) / math.sqrt(2)      # lower-right grid: x = L - gx, y = gy
    d_ul = ((L - GY) - GX - off) / math.sqrt(2)      # upper-left grid:  x = gx, y = L - gy
    lr = d_lr > w1
    ul = d_ul > w2
    UX = np.concatenate([L - GX[lr], GX[ul]])
    UY = np.concatenate([GY[lr], L - GY[ul]])
    # the two grids must not overlap each other
    if len(UX) and lr.any() and ul.any():
        a_x, a_y = (L - GX[lr])[:, None], GY[lr][:, None]
        b_x, b_y = GX[ul][None, :], (L - GY[ul])[None, :]
        if overlap(a_x, a_y, 0.0, b_x, b_y, 0.0).any():
            return []
    h = 0.5 * (abs(math.cos(theta)) + abs(math.sin(theta)))
    span = max(w1, w2) + 1.5
    u = np.arange(h, L - h + 1e-12, step)
    CX, CY = np.meshgrid(u, u)
    CX, CY = CX.ravel(), CY.ravel()
    dd = (CX - CY + off) / math.sqrt(2)              # signed distance to the channel axis
    c = np.abs(dd) <= span
    CX, CY = CX[c], CY[c]
    # drop candidates that hit a stair square (only stairs near the channel matter)
    nearU = np.abs((UX - UY + off) / math.sqrt(2)) <= span + 1.5
    SX, SY = UX[nearU], UY[nearU]
    ok = np.ones(len(CX), dtype=bool)
    for i in range(0, len(CX), 4000):
        sl = slice(i, i + 4000)
        ok[sl] = ~overlap(CX[sl, None], CY[sl, None], theta, SX[None, :], SY[None, :], 0.0).any(axis=1)
    CX, CY = CX[ok], CY[ok]
    order = np.lexsort((CX - CY, CX + CY))           # along the diagonal, then across
    BX, BY = [], []
    for i in order:
        x, y = CX[i], CY[i]
        if BX and overlap(x, y, theta, np.array(BX), np.array(BY), theta).any():
            continue
        BX.append(x); BY.append(y)
    return [(x, y, theta) for x, y in zip(BX, BY)] + [(x, y, 0.0) for x, y in zip(UX, UY)]


def sample(rng, L):
    return (math.radians(rng.uniform(5, 40)) * rng.choice((1, -1)), rng.uniform(-1.0, 1.0),
            rng.uniform(-0.5, 2.5), rng.uniform(-0.5, 2.5))


def jiggle(rng, p, L):
    q = list(p)
    i = rng.randrange(4)
    q[i] += rng.gauss(0, (math.radians(2), 0.15, 0.2, 0.2)[i])
    return tuple(q)


def min_side(n, p, lo, hi, iters=22):
    """Smallest L in [lo, hi] whose layout holds >= n squares (None if hi fails)."""
    if len(layout(hi, *p)) < n:
        return None
    for _ in range(iters):
        mid = (lo + hi) / 2
        if len(layout(mid, *p)) >= n:
            hi = mid
        else:
            lo = mid
    return hi


def best_count(L, seconds, rng=None):
    """Most squares a band layout fits in side L: random starts, then hill-climb."""
    rng = rng or random.Random()
    best = (0, None)
    t_end = time.time() + seconds
    while time.time() < t_end:
        p = sample(rng, L)
        c = len(layout(L, *p))
        for _ in range(15):                           # short hill-climb from each start
            q = jiggle(rng, p, L)
            cq = len(layout(L, *q))
            if cq >= c:
                p, c = q, cq
        if c > best[0]:
            best = (c, p)
    return best


def search(n, seconds, L, rng=None):
    """Band seed for n at side L: the best layout found, with at least n squares
    if possible, then the smallest side that layout still holds n at."""
    c, p = best_count(L, seconds, rng)
    if p is None:
        return None
    Lmin = min_side(n, p, math.sqrt(n), L) if c >= n else None
    return c, p, Lmin, layout(Lmin or L, *p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n', type=int)
    ap.add_argument('L', type=float, help='container side to build at (e.g. our current best)')
    ap.add_argument('--seconds', type=float, default=60)
    ap.add_argument('--seed', type=int)
    ap.add_argument('--out')
    a = ap.parse_args()
    r = search(a.n, a.seconds, a.L, random.Random(a.seed))
    if r is None:
        sys.exit(1)
    c, p, Lmin, sq = r
    msg = f'smallest side {Lmin:.9f} (score {Lmin / math.sqrt(a.n) - 1:.9f})' if Lmin else 'short of n'
    print(f'n={a.n} L={a.L} best count={c} (grid {int(a.L) ** 2}) {msg} '
          f'theta={math.degrees(p[0]):.3f} off={p[1]:.4f} w1={p[2]:.4f} w2={p[3]:.4f}')
    if a.out:
        with open(a.out, 'w') as h:
            h.write(f'# n = {len(sq)}\n')
            for x, y, t in sq:
                h.write(f'{x!r} {y!r} {t!r}\n')


if __name__ == '__main__':
    main()
