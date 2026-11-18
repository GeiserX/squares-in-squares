"""Independent certifier for a periodic seam cell (plain numpy, shares no code with kernel.py).

The separation gap of two unit squares is the largest, over the 8 edge lines of the pair, of the
smallest signed distance of the other square's corners outside that line.  gap > 0 proves the two
interiors are disjoint, with at least that clearance (the same test as Evan's nlpdesc.line_gap and
the official metric's SAT check).
"""
import math
import numpy as np

H = 0.5
U = np.array([(H, H), (-H, H), (-H, -H), (H, -H)])
E4 = np.array([(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)])


def corners(x, y, t):
    c, s = math.cos(t), math.sin(t)
    R = np.array([[c, -s], [s, c]])
    return np.array([x, y]) + U @ R.T


def gap(a, b):
    """a, b = (x, y, t).  Exact SAT clearance of two unit squares."""
    best = -1e30
    for (s_, o) in ((a, b), (b, a)):
        P = corners(*o)
        c, s = math.cos(s_[2]), math.sin(s_[2])
        R = np.array([[c, -s], [s, c]])
        for e in E4:
            n = R @ e
            best = max(best, float(((P - s_[:2]) @ n).min() - H))
    return best


def cell_squares(sq, p, ox, oy, D, reach=3):
    """The k tilted squares, their images at t*(p,p) for |t| <= 2, and every kept upright within
    `reach` of any tilted centre."""
    sq = np.asarray(sq, float)
    # every square's images over the whole span the cell's squares occupy, plus 2 periods each side
    u = sq[:, 0] + sq[:, 1]
    tlo = int(math.floor((u.min() - u.max()) / (2 * p))) - 2
    thi = -tlo
    tilted = []
    for t in range(tlo, thi + 1):
        for i, (x, y, th) in enumerate(sq):
            tilted.append((i, t, np.array([x + t * p, y + t * p, th])))
    up = {}
    for (x, y, th) in sq:
        for I in range(int(math.floor(x - ox)) - reach, int(math.floor(x - ox)) + reach + 1):
            for J in range(int(math.floor(y)) - reach, int(math.floor(y)) + reach + 1):
                if I - J >= D:
                    up[('G1', I, J)] = np.array([ox + I + 0.5, J + 0.5, 0.0])
        for A in range(int(math.floor(x)) - reach, int(math.floor(x)) + reach + 1):
            for B in range(int(math.floor(y - oy)) - reach, int(math.floor(y - oy)) + reach + 1):
                if B - A >= 0:
                    up[('G2', A, B)] = np.array([A + 0.5, oy + B + 0.5, 0.0])
    return tilted, up


def certify(sq, p, ox, oy, D, f=None):
    """Smallest clearance in the cell: tilted vs tilted (with images), tilted vs uprights, and the
    two grids against each other.  Returns (min_gap, worst_pair_description)."""
    k = len(sq)
    tilted, up = cell_squares(sq, p, ox, oy, D)
    worst = (1e30, None)
    base = [(i, t, s) for (i, t, s) in tilted if t == 0]
    for (i, _, a) in base:
        for (j, t, b) in tilted:
            if (j, t) == (i, 0):
                continue
            if t == 0 and j < i:
                continue
            if np.hypot(*(a[:2] - b[:2])) > 1.42:
                continue
            g = gap(a, b)
            if g < worst[0]:
                worst = (g, f'T{i} - T{j}@{t}')
        for key, b in up.items():
            if np.hypot(*(a[:2] - b[:2])) > 1.42:
                continue
            g = gap(a, b)
            if g < worst[0]:
                worst = (g, f'T{i} - {key}')
    # the grids against each other: the strip condition ox + oy + D >= 2 is sufficient
    gg = ox + oy + D - 2.0
    if gg < worst[0]:
        worst = (gg, 'G1 - G2 strip')
    if f is not None:
        for (v, name) in ((f - ox, 'ox > f'), (f - oy, 'oy > f')):
            if v < 0 and v < worst[0]:
                worst = (v, name)
    return worst
