#!/usr/bin/env python3
"""rigidsoft_topo: quench starts from a staircase topology and a doubly sheared block.

The fq quench never moves an upright square to another row, so the soft form it reaches from a block is fixed by
the rows of uprights around the block (rigidsoft.md sections 7 and 8). This tool writes the start directly from
the row counts: four staircases of uprights, one in each corner of the box, and the block of rigidsoft_pin.py
in the hole. The block's chains run along the diagonal from the bottom left corner to the top right corner.

  rigidsoft_topo.py one OUT.txt M F A B EPS BL BR TL TR [DX DY]
        M + F is the side of the start, A chains of B squares turned by EPS degrees, each staircase a list of row
        counts "7,6,5,3,2,1" from its wall corner outward (BL and BR rows from the bottom, TL and TR from the top)
  rigidsoft_topo.py held OUT.txt SUB.csv N EPS DF A B
        control A: the held uprights of N at a side DF larger and the uniform block at the held block's centre
  rigidsoft_topo.py deep OUT.txt M F A B EPS X0 Y0 BL BR TL TR
        control B: the stepped block of the held 261 (A * B + 1 squares, first square at X0 Y0) in four staircases
  rigidsoft_topo.py deep --fit SUB.csv N EPS
        X0 Y0 of the uniform lattice that fits the tilted squares of a held layout best

Output: fq text files (first line "n side", then x y degrees). Quench them with `fq quench --in F --out G`.
"""
import math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rigidsoft as RS  # noqa: E402
import rigidsoft_pin as PN  # noqa: E402

S2 = math.sqrt(2.0)


def uprights(s, BL, BR, TL, TR):
    """centres of the uprights of four staircases; None when two staircases overlap"""
    out = []
    for j, c in enumerate(BL):
        out += [(i + 0.5, j + 0.5) for i in range(c)]
    for j, c in enumerate(BR):
        out += [(s - i - 0.5, j + 0.5) for i in range(c)]
    for j, c in enumerate(TL):
        out += [(i + 0.5, s - j - 0.5) for i in range(c)]
    for j, c in enumerate(TR):
        out += [(s - i - 0.5, s - j - 0.5) for i in range(c)]
    P = np.array(out, float)
    d = np.abs(P[:, None, :] - P[None, :, :]).max(axis=2)
    np.fill_diagonal(d, 9.0)
    if (d < 1 - 1e-9).any():
        return None
    return P


def start(m, f, a, b, eps, BL, BR, TL, TR, dx=0.0, dy=0.0):
    s = m + f
    P = uprights(s, BL, BR, TL, TR)
    if P is None:
        return None
    T = np.array(PN.pblock(a, b, eps, s / 2 + dx, s / 2 + dy), float)
    return s, np.vstack([T, np.column_stack([P, np.zeros(len(P))])])


def cmd_one(a):
    L = lambda t: [int(v) for v in t.split(',') if v]
    dx, dy = (float(a[10]), float(a[11])) if len(a) > 11 else (0.0, 0.0)
    r = start(int(a[1]), float(a[2]), int(a[3]), int(a[4]), float(a[5]), L(a[6]), L(a[7]), L(a[8]), L(a[9]), dx, dy)
    if r is None:
        sys.exit('staircases overlap')
    RS.write_txt(a[0], r[0], r[1])
    print('squares', len(r[1]), 'side', r[0])


def cmd_held(a):
    out, sub, n, eps, df, x, y = a[0], a[1], int(a[2]), float(a[3]), float(a[4]), int(a[5]), int(a[6])
    s, X = RS.normalize(RS.load(sub, {n})[n])
    up = X[np.abs(X[:, 2]) < 3].copy(); ti = X[np.abs(X[:, 2]) >= 3]
    for q in range(len(up)):
        for c in (0, 1):
            fr = (up[q, c] - 0.5) % 1
            if min(fr, 1 - fr) > 0.03:        # anchored to the far wall: it moves with the wall
                up[q, c] += df
    cx, cy = ti[:, 0].mean() + df / 2, ti[:, 1].mean() + df / 2
    C = ti[:, :2] - ti[:, :2].mean(0); w, V = np.linalg.eigh(C.T @ C)
    along = abs(V[:, 1] @ np.array([1.0, 1.0])) > abs(V[:, 1] @ np.array([1.0, -1.0]))
    T = PN.pblock(x, y, eps, cx, cy) if along else PN.pblock(y, x, eps, cx, cy)
    RS.write_txt(out, s + df, np.vstack([np.array(T, float), up]))
    print('squares', len(T) + len(up), 'held side %.9f' % s)


def stepblock(a, b, eps, c0, nshift=2):
    """the block of the held 261: A chains on the 45-degree lattice with step sec(eps), squares at 45 - eps. The
    NSHIFT chains next to the bottom right staircase start one square later, the chain after them has B + 1
    squares and the others B. c0 is the centre of the first square of the first chain. A * B + 1 squares."""
    e = math.radians(eps); st = 1.0 / math.cos(e) / S2; out = []
    for j in range(a):
        ks = range(1, b + 1) if j < nshift else (range(0, b + 1) if j == nshift else range(0, b))
        for k in ks:
            out.append((c0[0] + (k - j) * st, c0[1] + (k + j) * st, 45.0 - eps))
    return out


def stepsblock(a, b, eps, c0, cuts):
    """stepblock with one step at every chain index of CUTS: the chain at a cut has B + 1 squares, and every
    chain before a cut starts one square later than the chains after it. A * B + len(CUTS) squares.
    stepsblock(a, b, eps, c0, (2,)) is stepblock(a, b, eps, c0, 2)."""
    e = math.radians(eps); st = 1.0 / math.cos(e) / S2; out = []
    for j in range(a):
        o = sum(1 for c in cuts if j < c)
        for k in range(o, o + b + (1 if j in cuts else 0)):
            out.append((c0[0] + (k - j) * st, c0[1] + (k + j) * st, 45.0 - eps))
    return out


def fit_c0(sub, n, eps, nshift=2):
    """c0 of the uniform lattice that fits the tilted squares of a held layout best (the control: n = 261)"""
    s, X = RS.normalize(RS.load(sub, {n})[n])
    T = X[np.abs(X[:, 2]) > 5]
    th = math.radians(float(np.median(T[:, 2])))
    eu = np.array([math.cos(th), math.sin(th)]); ev = np.array([-math.sin(th), math.cos(th)])
    u = T[:, :2] @ eu; v = T[:, :2] @ ev
    idx = {0: (0, 0)}; todo = [0]
    while todo:
        i = todo.pop()
        for j in range(len(T)):
            if j in idx:
                continue
            du = u[j] - u[i]; dv = v[j] - v[i]
            if abs(abs(du) - 1) < 0.12 and abs(dv) < 0.3:
                idx[j] = (idx[i][0] + int(round(du)), idx[i][1]); todo.append(j)
            elif abs(abs(dv) - 1) < 0.12 and abs(du) < 0.3:
                idx[j] = (idx[i][0], idx[i][1] + int(round(dv))); todo.append(j)
    I = np.array([idx[k] for k in range(len(T))]); I -= I.min(0)
    a = I[:, 0].max() + 1
    st = 1.0 / math.cos(math.radians(eps)) / S2
    jj = a - 1 - I[:, 0]; kk = I[:, 1]
    c = T[:, :2] - np.column_stack([(kk - jj) * st, (kk + jj) * st])
    return s, float(c[:, 0].mean()), float(c[:, 1].mean()), int(a), len(T)


def cmd_deep(a):
    """rigidsoft_topo.py deep OUT.txt M F A B EPS X0 Y0 BL BR TL TR   or   deep --fit SUB.csv N EPS"""
    if a[0] == '--fit':
        print('side %.9f c0 %.6f %.6f chains %d tilted %d' % fit_c0(a[1], int(a[2]), float(a[3])))
        return
    L = lambda t: [int(v) for v in t.split(',') if v]
    m, f, x, y, eps = int(a[1]), float(a[2]), int(a[3]), int(a[4]), float(a[5])
    P = uprights(m + f, L(a[8]), L(a[9]), L(a[10]), L(a[11]))
    if P is None:
        sys.exit('staircases overlap')
    T = np.array(stepblock(x, y, eps, (float(a[6]), float(a[7]))), float)
    RS.write_txt(a[0], m + f, np.vstack([T, np.column_stack([P, np.zeros(len(P))])]))
    print('squares', len(T) + len(P), 'tilted', len(T), 'side', m + f)


if __name__ == '__main__':
    cmds = {'one': cmd_one, 'held': cmd_held, 'deep': cmd_deep}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]](sys.argv[2:])
