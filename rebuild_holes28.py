"""holes28.py H FILE [FILE ...]: the largest empty axis-parallel square in each layout, on a grid of step H.
A cell is free when no square (grown by half the cell diagonal) touches it; the largest square of free cells
(dynamic programming) then bounds the largest empty upright square from below. Prints n, side, hole edge."""
import csv, math, sys
import numpy as np
h = float(sys.argv[1])
for p in sys.argv[2:]:
    R = list(csv.DictReader(open(p)))
    sq = [(float(r['x']), float(r['y']), float(r['angle'])) for r in R]
    xs, ys = [], []
    for x, y, a in sq:
        c, s = math.cos(a), math.sin(a)
        for dx, dy in ((.5, .5), (.5, -.5), (-.5, .5), (-.5, -.5)):
            xs.append(x + c * dx - s * dy); ys.append(y + s * dx + c * dy)
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    L = max(x1 - x0, y1 - y0)
    N = int(math.ceil(L / h))
    occ = np.zeros((N, N), bool)
    g = h * math.sqrt(2) / 2
    cx = x0 + (np.arange(N) + 0.5) * h
    cy = y0 + (np.arange(N) + 0.5) * h
    for x, y, a in sq:
        c, s = math.cos(a), math.sin(a)
        r = 0.5 * (abs(c) + abs(s)) + g
        i0 = max(0, int((x - r - x0) / h)); i1 = min(N, int((x + r - x0) / h) + 2)
        j0 = max(0, int((y - r - y0) / h)); j1 = min(N, int((y + r - y0) / h) + 2)
        X, Y = np.meshgrid(cx[i0:i1] - x, cy[j0:j1] - y, indexing='ij')
        u = np.abs(X * c + Y * s); v = np.abs(-X * s + Y * c)
        # grown square: cell centre within 0.5 + g of the square (Chebyshev in its frame, conservative)
        occ[i0:i1, j0:j1] |= (u <= 0.5 + g) & (v <= 0.5 + g)
    free = ~occ
    D = np.zeros((N + 1, N + 1), np.int32)
    best = 0; arg = None
    for i in range(N):
        row = free[i]
        prev = D[i]; cur = D[i + 1]
        for j in np.nonzero(row)[0]:
            v = min(prev[j], cur[j], prev[j + 1]) + 1
            cur[j + 1] = v
            if v > best:
                best = v; arg = (i, j)
    print(len(sq), '%.9f' % L, 'hole %.4f' % (best * h), 'at', None if arg is None else ('%.3f' % (x0 + (arg[0] - best + 1) * h), '%.3f' % (y0 + (arg[1] - best + 1) * h)), p, flush=True)
