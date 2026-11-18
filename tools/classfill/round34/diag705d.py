import sys, pickle, math, json
sys.path.insert(0, 'lane')
import numpy as np
import modules as M
from scipy.spatial import cKDTree
b = pickle.load(open('compose/library-r33.pkl', 'rb'))
for n in (705, 999):
    sq = M.read_layouts('held-%d.csv' % n)[n]
    d, why = M.cut(sq, n)
    print('CUT', n, why if d is None else dict(f=d['f'], m=d['m'], c1=d['c1'], c2=d['c2'], s1=d['s1'], s2=d['s2'], zones=sorted(set(map(str, d['zone'])))), flush=True)
    if d is None: continue
    lib = next(x for x in b['layouts'] if x['n'] == n)
    print('LIB f', lib['f'], 'held f', d['f'], 'same' if abs(lib['f'] - d['f']) < 1e-12 else 'DIFFERENT', flush=True)
    mods = M.modules_of(d, 'x', 'x', 'dg'); tw, ids = M.slid(d, mods)
    by = {q['id']: q for q in mods + tw}
    for cid in (ids[2], ids[2].rstrip('~')):
        C = by[cid]; M.SLIDE = True
        P, mode = M.corner_state(C, C['f0'], C['P'], C['y0'], C['x0'])
        # the native corner region in the same frame: zone 'C' squares and its stacks are in d['X']? report the frame of C['P']
        X = d['X']; Z = np.asarray(d['zone'])
        # corner frame: C['P'] are corner free squares; locate them in X to get the transform (pure translation/reflection assumed)
        tree = None
        out = {}
        for zname in sorted(set(map(str, Z))):
            out[zname] = int((Z == zname).sum())
        # compare modeled bodies to native squares after matching the corner free squares
        Pm = C['P'].copy()
        # brute: try the 8 symmetries of the square side L about the board, pick one that maps Pm onto X squares
        L = d['m'] + d['f']; best = None
        cand = []
        for sx in (1, -1):
            for sy in (1, -1):
                for sw in (False, True):
                    Q = Pm[:, :2].copy()
                    if sw: Q = Q[:, ::-1]
                    Q = np.c_[Q[:, 0] if sx == 1 else L - Q[:, 0], Q[:, 1] if sy == 1 else L - Q[:, 1]]
                    dd = cKDTree(X[:, :2]).query(Q)[0].max()
                    cand.append((dd, sx, sy, sw))
        dd, sx, sy, sw = min(cand)
        def tf(A):
            Q = A[:, :2].copy()
            if sw: Q = Q[:, ::-1]
            return np.c_[Q[:, 0] if sx == 1 else L - Q[:, 0], Q[:, 1] if sy == 1 else L - Q[:, 1]]
        T = cKDTree(X[:, :2])
        rep = dict(id=cid, match_free=float(dd))
        Pd = P.copy()
        for mv in (0, 1, 2, -1):
            sel = mode == mv
            dist, idx = T.query(tf(Pd[sel]))
            rep['mode%d' % mv] = dict(count=int(sel.sum()), max=float(dist.max()), n_over_1e6=int((dist > 1e-6).sum()), worst=int(np.argmax(dist)))
        print('DIAGD ' + json.dumps(rep), flush=True)
