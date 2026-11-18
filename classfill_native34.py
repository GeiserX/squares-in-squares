"""Round 34: native residual corner model (classfill own file; modules.py is imported, never edited).

The round 33 self rebuild of 705 and 999 failed because the quenched native stacks are not the rigid, centred flush
stacks the module model draws (705: first arm-2 stack square 0.0133 off, later arm-2 stacks shifted (+0.0022, -0.0050);
999: arm-1 stack angles 16.297-16.449 deg against the model's 16.515 deg). Here every modelled stack square and every
modelled cell of the rest carries its native residual (position and angle offset from the model at the native f),
measured from the cut, and keeps it at every f. At the native f the corner state is then the native layout itself.
"""
import math
import numpy as np
from scipy.spatial import cKDTree
import modules as M

STACK0_ONLY = False   # True: only the first stack of each arm keeps its native residual (joins at another f)
EXTRA = 0.0   # share of the last stack's along-arm residual taken off the caps (0: the legality test decides)
RES = {}          # corner id -> dict(s1={(j,k):d}, s2={(j,k):d}, cell={(i,j):d})
_cs, _as = M.corner_state, M.assemble


def frame(C, d):
    X = d['X']; L = d['m'] + d['f']; T = cKDTree(X[:, :2]); best = None
    for sx in (1, -1):
        for sy in (1, -1):
            for sw in (False, True):
                def tf(A, sx=sx, sy=sy, sw=sw):
                    Q = A[:, :2].copy()
                    if sw: Q = Q[:, ::-1]
                    return np.c_[Q[:, 0] if sx == 1 else L - Q[:, 0], Q[:, 1] if sy == 1 else L - Q[:, 1]]
                dd = T.query(tf(C['P']))[0].max()
                if best is None or dd < best[0]: best = (dd, tf, sx, sy, sw)
    return best


def measure(C, d, s1, s2):
    """Residuals of every stack square (all s1, s2 stacks) and every cell of the rest, at the native f."""
    dd, tf, sx, sy, sw = frame(C, d)
    if dd > 1e-9 or sw or sx != 1 or sy != 1:
        return None, 'corner frame is not the identity (%.2e %s %s %s)' % (dd, sx, sy, sw)
    X = d['X']; T = cKDTree(X[:, :2]); f = C['f0']; c1, c2 = C['c1'], C['c2']
    W1, W2 = c1 - 1 + f, c2 - 1 + f; t1, t2 = M.flush_tilt(c1, f), M.flush_tilt(c2, f); p1, p2 = 1 / math.cos(t1), 1 / math.cos(t2)
    res = dict(s1={}, s2={}, cell={})
    worst = 0.0
    for j in range(s1):
        st = M.stack_squares(c1, C['lean1'] * math.degrees(t1), W1 / 2, C['y0'] + (j + .5) * p1)
        dist, idx = T.query(st[:, :2])
        for k in range(c1):
            res['s1'][(j, k)] = (X[idx[k], 0] - st[k, 0], X[idx[k], 1] - st[k, 1], X[idx[k], 2] - st[k, 2]); worst = max(worst, dist[k])
    for j in range(s2):
        st = M.stack_squares(c2, C['lean2'] * math.degrees(t2), C['x0'] + (j + .5) * p2, W2 / 2, along_x=False)
        dist, idx = T.query(st[:, :2])
        for k in range(c2):
            res['s2'][(j, k)] = (X[idx[k], 0] - st[k, 0], X[idx[k], 1] - st[k, 1], X[idx[k], 2] - st[k, 2]); worst = max(worst, dist[k])
    cs = M.corner_slide(C); gone = set(map(tuple, C['miss']))
    for i in range(d['m'] + 2):
        for j in range(d['m'] + 2):
            if (i, j) in gone: continue
            q = np.array([W1 + .5 + i + cs(i, j)[0], W2 + .5 + j + cs(i, j)[1]])
            dist, k = T.query(q)
            if dist < 0.2 and abs(((X[k, 2] + 45) % 90) - 45) < 1.0:
                res['cell'][(i, j)] = (X[k, 0] - q[0], X[k, 1] - q[1], X[k, 2])
    return res, 'worst stack residual %.3e' % worst


def corner_state(mod, f, Pm, y0, x0):
    P, mode = _cs(mod, f, Pm, y0, x0)
    r = RES.get(mod['id'])
    if not r: return P, mode
    c1, c2 = mod['c1'], mod['c2']; n0 = len(Pm)
    for k in range(c1):
        dx, dy, da = r['s1'].get((0, k), (0, 0, 0)); P[n0 + k, 0] += dx; P[n0 + k, 1] += dy; P[n0 + k, 2] += math.radians(da)
    for k in range(c2):
        dx, dy, da = r['s2'].get((0, k), (0, 0, 0)); P[n0 + c1 + k, 0] += dx; P[n0 + c1 + k, 1] += dy; P[n0 + c1 + k, 2] += math.radians(da)
    W1, W2 = c1 - 1 + f, c2 - 1 + f
    for b in range(n0 + c1 + c2, len(P)):
        i = int(round(P[b, 0] - W1 - .5)); j = int(round(P[b, 1] - W2 - .5))
        if (i, j) in r['cell']:
            dx, dy, a = r['cell'][(i, j)]
            # the model cell already holds the corner slide; the residual is to the native square
            q0 = (W1 + .5 + i + M.corner_slide(mod)(i, j)[0], W2 + .5 + j + M.corner_slide(mod)(i, j)[1])
            P[b, 0] = q0[0] + dx; P[b, 1] = q0[1] + dy; P[b, 2] = math.radians(a)
    return P, mode


def install():
    M.corner_state = corner_state


def assemble(lib, n, C, F1, F2, s1, s2, f):
    """modules.assemble with the native residuals of the corner's stacks and rest cells (copied; one change marked)."""
    qc = C['q']; r = RES.get(qc['id'])
    if not r: return _as(lib, n, C, F1, F2, s1, s2, f)
    m = math.isqrt(n - 1); L = m + f
    q1, q2 = F1['q'], F2['q']
    c1, c2 = qc['c1'], qc['c2']
    W1, W2 = c1 - 1 + f, c2 - 1 + f
    t1, t2 = M.flush_tilt(c1, f), M.flush_tilt(c2, f); p1, p2 = 1 / math.cos(t1), 1 / math.cos(t2)
    f1 = M.far_at(q1, f); f2 = M.far_at(q2, f)
    if f1 is None or f2 is None: return None, 'a far zone does not exist at f'
    # change: the native stacks stand further out than the model's chain by their along-arm residual
    j1 = max([jj for jj, kk in r['s1']] or [0]); j2 = max([jj for jj, kk in r['s2']] or [0])
    e1 = max([r['s1'][(min(s1 - 1, j1), k)][1] for k in range(c1) if (min(s1 - 1, j1), k) in r['s1']] or [0.0])
    e2 = max([r['s2'][(min(s2 - 1, j2), k)][0] for k in range(c2) if (min(s2 - 1, j2), k) in r['s2']] or [0.0])
    co = M.corner_at(qc, f, L - f1[0] - s1 * p1 - EXTRA * max(e1, 0.0), L - f2[0] - s2 * p2 - EXTRA * max(e2, 0.0))
    if co is None: return None, 'the corner does not fit under both arms'
    y0, x0, Pc = co
    parts = [Pc]
    def resid(st, arm, j):   # change: native residual of stack j (the last measured stack for later ones)
        st = st.copy(); key = 's%d' % arm
        js = max([jj for jj, kk in r[key]] or [0])
        if STACK0_ONLY and j > 0: return st
        for k in range(len(st)):
            dx, dy, da = r[key].get((min(j, js), k), (0, 0, 0)); st[k, 0] += dx; st[k, 1] += dy; st[k, 2] += da
        return st
    parts += [resid(M.stack_squares(c1, qc['lean1'] * math.degrees(t1), W1 / 2, y0 + (j + .5) * p1), 1, j) for j in range(s1)]
    parts += [resid(M.stack_squares(c2, qc['lean2'] * math.degrees(t2), x0 + (j + .5) * p2, W2 / 2, along_x=False), 2, j) for j in range(s2)]
    ni, nj = m - c1 + 1, m - c2 + 1
    gone = set(map(tuple, qc['miss']))
    a = f1[1].copy()
    if q1['lean'] != -qc['lean1']: a[:, 0] = W1 - a[:, 0]; a[:, 2] = -a[:, 2]
    parts.append(np.c_[a[:, 0], L - a[:, 1], -a[:, 2]]); gone |= {(i, nj - 1 - j) for i, j in q1['miss']}
    a = f2[1].copy()
    if q2['lean'] != qc['lean2']: a[:, 0] = W2 - a[:, 0]; a[:, 2] = -a[:, 2]
    parts.append(np.c_[L - a[:, 1], a[:, 0], a[:, 2]]); gone |= {(ni - 1 - i, j) for j, i in q2['miss']}
    cs = M.corner_slide(qc)
    off = {(i, 0): cs(i, 0) for i in range(ni)}; off.update({(0, j): cs(0, j) for j in range(1, nj)})
    if M.SLIDE:
        for far, arm, fl, nn, grant in ((q2, 2, f2[0], ni, qc.get('g2', 0.0)), (q1, 1, f1[0], nj, qc.get('g1', 0.0))):
            if far.get('slide') is None: continue
            sl = far['slide']
            reach = int(math.ceil(fl + far['c'] * math.sin(M.flush_tilt(far['c'], f)) + 2.5))
            for j in range(min(len(sl), nn - 1, reach)):
                if arm == 2: off[(ni - 1 - j, 0)] = (-float(sl[j]), 0.0)
                else: off[(0, nj - 1 - j)] = (0.0, -float(sl[j]))
    cells = []
    for i in range(ni):
        for j in range(nj):
            if (i, j) in gone: continue
            base = (W1 + .5 + i + off.get((i, j), (0.0, 0.0))[0], W2 + .5 + j + off.get((i, j), (0.0, 0.0))[1], 0.0)
            if (i, j) in r['cell'] and (i, j) not in {(ni - 1 - jj, 0) for jj in range(ni)} | {(0, nj - 1 - jj) for jj in range(nj)} or (i, j) in r['cell'] and (i < 3 or j < 3):
                q0 = (W1 + .5 + i + cs(i, j)[0], W2 + .5 + j + cs(i, j)[1])
                dx, dy, a3 = r['cell'][(i, j)]; base = (q0[0] + dx, q0[1] + dy, a3)   # change: native residual cell
            cells.append(base)
    parts.append(np.array(cells))
    P = np.vstack(parts); P[:, 2] = np.radians(P[:, 2])
    if len(P) != n: return None, 'holds %d squares' % len(P)
    return P, None


def install():
    M.corner_state = corner_state
    M.assemble = assemble


_ca = M.corner_at


def corner_at(mod, f, cap_y, cap_x):
    """Round 34: for a corner with native residuals, first walk from its own native state (legal under the residual
    model, and u = 0 is a feasible LP step) to f with both caps in every LP; then the round 33 orders."""
    if mod['id'] in RES:
        at = (mod['y0'], mod['x0'], mod['P'])
        if abs(f - mod['f0']) < 1e-12:
            if at[0] <= cap_y + 1e-9 and at[1] <= cap_x + 1e-9:
                r = M.corner_len(mod, f, at[2], at[0], at[1], cost=(1.0, 1.0), caps=(cap_y - at[0], cap_x - at[1]))
                return r if r is not None and r[0] <= cap_y + 1e-9 and r[1] <= cap_x + 1e-9 else at
        else:
            for g in M.path(mod['f0'], f):
                at = M.corner_len(mod, float(g), at[2], at[0], at[1], cost=(1.0, 1.0), caps=(cap_y - at[0], cap_x - at[1]))
                if at is None: break
            if at is not None and at[0] <= cap_y + 1e-9 and at[1] <= cap_x + 1e-9:
                return at
    return _ca(mod, f, cap_y, cap_x)


def install():
    M.corner_state = corner_state
    M.assemble = assemble
    M.corner_at = corner_at
