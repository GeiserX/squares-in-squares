"""Penalty kernel for one periodic seam cell (numba).

Frame (only the relative geometry of the two grids matters in an infinite seam):
  G1 = upright unit cells [ox+i, ox+i+1] x [j, j+1] kept when i - j >= D   (bottom-right grid)
  G2 = upright unit cells [a, a+1] x [oy+b, oy+b+1] kept when b - a >= 0   (top-left grid)
  The k tilted squares repeat under T = (p, p).  Translating the whole picture by (1, 0) maps
  (d1, d2) to (d1 - 1, d2 + 1), so only D = d1 + d2 matters for the cell.
  With the box side L = m + f, the grids fit when ox <= f and oy <= f.

State vector z = [x0, y0, t0, ..., x_{k-1}, y_{k-1}, t_{k-1}, ox, oy].
Energy = sum over overlapping pairs of (SAT penetration depth)^2, every square drawn at side s
(s = 1 + delta when we want a certified clearance at side 1).
"""
import math
import numpy as np
from numba import njit

SQ2 = math.sqrt(2.0)


@njit(cache=True, inline='always')
def _h(a):
    return 0.5 * (abs(math.cos(a)) + abs(math.sin(a)))


@njit(cache=True, inline='always')
def _hp(a):
    c = math.cos(a); s = math.sin(a)
    sc = 1.0 if c >= 0 else -1.0
    ss = 1.0 if s >= 0 else -1.0
    return 0.5 * (-sc * s + ss * c)


@njit(cache=True)
def pair_pen(ax, ay, ta, bx, by, tb, s, out):
    """SAT penetration of two squares of side s.  Returns pen (>0 overlap, else 0) and writes
    d pen / d (ax, ay, ta, bx, by, tb) into out[0:6]."""
    dx = bx - ax; dy = by - ay
    best = 1e30; bphi = 0.0; bown = 0
    for own in range(2):
        th = ta if own == 0 else tb
        for q in range(2):
            phi = th + q * (math.pi / 2)
            nx = math.cos(phi); ny = math.sin(phi)
            pr = nx * dx + ny * dy
            ov = s * _h(ta - phi) + s * _h(tb - phi) - abs(pr)
            if ov < best:
                best = ov; bphi = phi; bown = own
    for r in range(6):
        out[r] = 0.0
    if best <= 0.0:
        return 0.0
    phi = bphi
    nx = math.cos(phi); ny = math.sin(phi)
    pr = nx * dx + ny * dy
    sg = 1.0 if pr >= 0 else -1.0
    perp = -math.sin(phi) * dx + math.cos(phi) * dy
    dphi = -s * _hp(ta - phi) - s * _hp(tb - phi) - sg * perp
    dta = s * _hp(ta - phi)
    dtb = s * _hp(tb - phi)
    if bown == 0:
        dta += dphi
    else:
        dtb += dphi
    out[0] = sg * nx; out[1] = sg * ny; out[2] = dta
    out[3] = -sg * nx; out[4] = -sg * ny; out[5] = dtb
    return best


@njit(cache=True)
def energy_grad(z, k, p, D, s, use_images, grad):
    """Total energy and gradient.  use_images=0 drops the periodic images (negative control only)."""
    for r in range(grad.shape[0]):
        grad[r] = 0.0
    ox = z[3 * k]; oy = z[3 * k + 1]
    E = 0.0
    g = np.zeros(6)
    cut2 = (s * SQ2) ** 2
    for i in range(k):
        xi = z[3 * i]; yi = z[3 * i + 1]; ti = z[3 * i + 2]
        # tilted - tilted, with images under (p, p)
        for j in range(i, k):
            xj = z[3 * j]; yj = z[3 * j + 1]; tj = z[3 * j + 2]
            # images centred on the actual offset: squares may drift many periods apart along u
            t0 = int(round(((xi + yi) - (xj + yj)) / (2.0 * p)))
            for t in range(t0 - 2, t0 + 3):
                if j == i and t <= 0:
                    continue
                if use_images == 0 and t != 0:
                    continue
                bx = xj + t * p; by = yj + t * p
                if (bx - xi) ** 2 + (by - yi) ** 2 >= cut2:
                    continue
                pen = pair_pen(xi, yi, ti, bx, by, tj, s, g)
                if pen > 0.0:
                    E += pen * pen
                    w = 2.0 * pen
                    grad[3 * i] += w * g[0]; grad[3 * i + 1] += w * g[1]; grad[3 * i + 2] += w * g[2]
                    grad[3 * j] += w * g[3]; grad[3 * j + 1] += w * g[4]; grad[3 * j + 2] += w * g[5]
        # G1 obstacles: centres (ox + I + .5, J + .5), kept when I - J >= D
        i0 = int(math.floor(xi - ox)); j0 = int(math.floor(yi))
        for I in range(i0 - 2, i0 + 3):
            for J in range(j0 - 2, j0 + 3):
                if I - J < D:
                    continue
                cx = ox + I + 0.5; cy = J + 0.5
                if (cx - xi) ** 2 + (cy - yi) ** 2 >= cut2:
                    continue
                pen = pair_pen(xi, yi, ti, cx, cy, 0.0, s, g)
                if pen > 0.0:
                    E += pen * pen
                    w = 2.0 * pen
                    grad[3 * i] += w * g[0]; grad[3 * i + 1] += w * g[1]; grad[3 * i + 2] += w * g[2]
                    grad[3 * k] += w * g[3]
        # G2 obstacles: centres (A + .5, oy + B + .5), kept when B - A >= 0
        a0 = int(math.floor(xi)); b0 = int(math.floor(yi - oy))
        for A in range(a0 - 2, a0 + 3):
            for B in range(b0 - 2, b0 + 3):
                if B - A < 0:
                    continue
                cx = A + 0.5; cy = oy + B + 0.5
                if (cx - xi) ** 2 + (cy - yi) ** 2 >= cut2:
                    continue
                pen = pair_pen(xi, yi, ti, cx, cy, 0.0, s, g)
                if pen > 0.0:
                    E += pen * pen
                    w = 2.0 * pen
                    grad[3 * i] += w * g[0]; grad[3 * i + 1] += w * g[1]; grad[3 * i + 2] += w * g[2]
                    grad[3 * k + 1] += w * g[4]
    return E
