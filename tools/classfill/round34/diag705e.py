import sys, pickle, math, json
sys.path.insert(0, 'lane')
import numpy as np
import modules as M
from scipy.spatial import cKDTree
for n in (705, 999):
    sq = M.read_layouts('held-%d.csv' % n)[n]
    d, why = M.cut(sq, n)
    mods = M.modules_of(d, 'x', 'x', 'dg'); tw, ids = M.slid(d, mods)
    by = {q['id']: q for q in mods + tw}
    C = by[ids[2]]; M.SLIDE = True
    print('KEYS', sorted(k for k in C.keys() if k not in ('P',)), 'y0', C['y0'], 'x0', C['x0'], 'f0', C['f0'], 'lean', C['lean1'], C['lean2'], 'c', C['c1'], C['c2'])
    P, mode = M.corner_state(C, C['f0'], C['P'], C['y0'], C['x0'])
    X = d['X']; L = d['m'] + d['f']
    best = None
    for sx in (1, -1):
        for sy in (1, -1):
            for sw in (False, True):
                def tf(A, sx=sx, sy=sy, sw=sw):
                    Q = A[:, :2].copy()
                    if sw: Q = Q[:, ::-1]
                    return np.c_[Q[:, 0] if sx == 1 else L - Q[:, 0], Q[:, 1] if sy == 1 else L - Q[:, 1]]
                dd = cKDTree(X[:, :2]).query(tf(C['P']))[0].max()
                if best is None or dd < best[0]: best = (dd, tf, sx, sy, sw)
    tf = best[1]; T = cKDTree(X[:, :2])
    for mv in (1, 2):
        A = P[mode == mv]; Q = tf(A); dist, idx = T.query(Q)
        nat = X[idx]
        print('MODE', mv, 'sym', best[2:], 'model angle deg', np.degrees(A[:, 2]).round(5).tolist()[:2], 'native angle', np.asarray(nat[:, 2]).round(5).tolist()[:2])
        print('   dxy', np.round(nat[:, :2] - Q, 5).tolist())
    zs = np.asarray(d['zone'])
    for z in ('S1', 'S2'):
        Z = X[zs == z]
        print('ZONE', z, 'count', len(Z), 'angles', np.unique(np.round(Z[:, 2], 6))[:6].tolist())
