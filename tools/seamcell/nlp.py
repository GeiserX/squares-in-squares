"""Fixed-line NLP polish of a periodic seam cell: minimise f = max(ox, oy).

Same formulation as Evan Daniel's nlpdesc.py (MIT): for each near pair, the best SAT edge line of one
square must keep all 4 corners of the other outside it (smooth, sufficient for disjointness).  Lines
are re-picked at each outer round.  SLSQP replaces IPOPT (no cyipopt on the boxF).  Periodic images
(t * (p, p)) and the two grids' upright cells (moving with ox / oy) are the extra elements.
"""
import math
import numpy as np
from scipy.optimize import minimize

H = 0.5
U = np.array([(H, H), (-H, H), (-H, -H), (H, -H)])
E4 = np.array([(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)])

# element = (kind, a, b): kind 0 tilted (a = index, b = image t), 1 G1 cell (I, J), 2 G2 cell (A, B)


def elem_state(v, k, p, el):
    kind, a, b = el
    if kind == 0:
        return v[3 * a] + b * p, v[3 * a + 1] + b * p, v[3 * a + 2]
    if kind == 1:
        return v[3 * k] + a + 0.5, b + 0.5, 0.0
    return a + 0.5, v[3 * k + 1] + b + 0.5, 0.0


def near_elements(v, k, p, D, cut=1.5):
    pairs = []
    for i in range(k):
        xi, yi, _ = elem_state(v, k, p, (0, i, 0))
        for j in range(i, k):
            xj, yj, _ = elem_state(v, k, p, (0, j, 0))
            t0 = int(round(((xi + yi) - (xj + yj)) / (2.0 * p)))
            for t in range(t0 - 2, t0 + 3):
                if j == i and t <= 0:
                    continue
                x, y, _ = elem_state(v, k, p, (0, j, t))
                if math.hypot(x - xi, y - yi) < cut:
                    pairs.append(((0, i, 0), (0, j, t)))
        ox, oy = v[3 * k], v[3 * k + 1]
        for I in range(int(math.floor(xi - ox)) - 2, int(math.floor(xi - ox)) + 3):
            for J in range(int(math.floor(yi)) - 2, int(math.floor(yi)) + 3):
                if I - J >= D and math.hypot(ox + I + 0.5 - xi, J + 0.5 - yi) < cut:
                    pairs.append(((0, i, 0), (1, I, J)))
        for A in range(int(math.floor(xi)) - 2, int(math.floor(xi)) + 3):
            for B in range(int(math.floor(yi - oy)) - 2, int(math.floor(yi - oy)) + 3):
                if B - A >= 0 and math.hypot(A + 0.5 - xi, oy + B + 0.5 - yi) < cut:
                    pairs.append(((0, i, 0), (2, A, B)))
    return pairs


def best_line(sa, sb):
    best = None
    for (own, oth, w) in ((sa, sb, 0), (sb, sa, 1)):
        c, s = math.cos(own[2]), math.sin(own[2])
        R = np.array([[c, -s], [s, c]])
        co, so = math.cos(oth[2]), math.sin(oth[2])
        P = np.array(oth[:2]) + U @ np.array([[co, -so], [so, co]]).T
        for kk in range(4):
            g = float(((P - np.array(own[:2])) @ (R @ E4[kk])).min() - H)
            if best is None or g > best[0]:
                best = (g, w, kk)
    return best


def build(v, k, p, D):
    cons = []
    for (ea, eb) in near_elements(v, k, p, D):
        sa = elem_state(v, k, p, ea); sb = elem_state(v, k, p, eb)
        g, w, kk = best_line(sa, sb)
        if g > 0.3:
            continue
        own, oth = (ea, eb) if w == 0 else (eb, ea)
        cons.append((own, oth, kk))
    return cons


def con_values(v, k, p, cons, margin):
    out = np.empty(4 * len(cons))
    for r, (own, oth, kk) in enumerate(cons):
        xs, ys, ts = elem_state(v, k, p, own)
        xo, yo, to = elem_state(v, k, p, oth)
        n = np.array([math.cos(ts) * E4[kk][0] - math.sin(ts) * E4[kk][1],
                      math.sin(ts) * E4[kk][0] + math.cos(ts) * E4[kk][1]])
        co, so = math.cos(to), math.sin(to)
        P = np.array([xo, yo]) + U @ np.array([[co, -so], [so, co]]).T
        out[4 * r:4 * r + 4] = (P - [xs, ys]) @ n - H - margin
    return out


def polish(v, k, p, D, rounds=30, R=0.02, margin=1e-9, log=None):
    """v = [x, y, t]*k + [ox, oy].  Returns (f_star, v)."""
    v = np.array(v, float)
    f_cur = max(v[3 * k], v[3 * k + 1])
    feas = exact_min_gap(v, k, p, D) > 0
    if not feas:
        f_cur = float('inf')     # restoration: the first feasible round is accepted whatever its f
    for rd in range(rounds):
        cons = build(v, k, p, D)
        x0 = np.concatenate([v, [max(v[3 * k], v[3 * k + 1])]])
        nv = len(x0)
        bounds = [(x0[i] - R, x0[i] + R) for i in range(nv)]
        C = [dict(type='ineq', fun=lambda x: con_values(x[:-1], k, p, cons, margin)),
             dict(type='ineq', fun=lambda x: np.array([x[-1] - x[3 * k], x[-1] - x[3 * k + 1],
                                                       x[3 * k] + x[3 * k + 1] + D - 2.0]))]
        r = minimize(lambda x: x[-1], x0, jac=lambda x: np.eye(nv)[-1], method='SLSQP', bounds=bounds,
                     constraints=C, options=dict(maxiter=300, ftol=1e-15))
        v2 = r.x[:-1]
        f2 = max(v2[3 * k], v2[3 * k + 1])
        cg = exact_min_gap(v2, k, p, D)
        if log:
            log(f'nlp round {rd}: f {f_cur:.10f} -> {f2:.10f} min gap {cg:.2e} ({r.message[:30]})')
        if cg <= 0:
            if f_cur == float('inf') and rd < 3:
                v = v2          # still restoring: try again from the new point
                continue
            break
        if f2 >= f_cur - 1e-12:
            break
        v, f_cur = v2, f2
    return f_cur, v


def exact_min_gap(v, k, p, D):
    from cert import certify
    sq = np.asarray(v[:3 * k]).reshape(k, 3)
    return certify(sq, p, v[3 * k], v[3 * k + 1], D)[0]
