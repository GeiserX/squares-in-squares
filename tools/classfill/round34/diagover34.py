import sys, json, math
sys.path.insert(0, 'lane')
import numpy as np
import modules as M
import classfill_native34 as N
n = int(sys.argv[1]); up = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
sq = M.read_layouts('held-%d.csv' % n)[n]
d, why = M.cut(sq, n)
mods = M.modules_of(d, 'x', 'x', 'nat34'); tw, ids = M.slid(d, mods)
by = {q['id']: dict(id=q['id'], q=q) for q in mods + tw}
M.SLIDE = True
C = by[ids[2]]['q']; F1 = by[ids[0]]['q']; F2 = by[ids[1]]['q']
r, msg = N.measure(C, d, d['s1'], d['s2']); N.RES[C['id']] = r; N.install()
f = d['f'] + up; L = d['m'] + f
f1 = M.far_at(F1, f); f2 = M.far_at(F2, f)
t1, t2 = M.flush_tilt(C['c1'], f), M.flush_tilt(C['c2'], f); p1, p2 = 1 / math.cos(t1), 1 / math.cos(t2)
co = M.corner_at(C, f, L - f1[0] - d['s1'] * p1, L - f2[0] - d['s2'] * p2)
print('caps', L - f1[0] - d['s1'] * p1, L - f2[0] - d['s2'] * p2, 'corner', None if co is None else co[:2], 'native', C['y0'], C['x0'], 'far', f1[0], f2[0], 'len0', F1['len0'], F2['len0'])
P, why = M.assemble(None, n, by[ids[2]], by[ids[0]], by[ids[1]], d['s1'], d['s2'], f)
if P is None: print('none', why); sys.exit()
sizes = [len(co[2]), C['c1'] * d['s1'], C['c2'] * d['s2'], len(f1[1]), len(f2[1])]
lab = []
for name, k in zip(['corner', 'stacks1', 'stacks2', 'far1', 'far2'], sizes): lab += [name] * k
lab += ['cells'] * (len(P) - len(lab))
pairs = M.pair_list(P, math.sqrt(2) + 1e-3)
g = M.best_axes(P, pairs)[0]
bad = np.argsort(g)[:12]
from collections import Counter
print('neg pairs', int((g < -2e-9).sum()), Counter((lab[pairs[b, 0]], lab[pairs[b, 1]]) for b in np.nonzero(g < -2e-9)[0]))
for b in bad:
    i, j = pairs[b]
    print(round(float(g[b]), 6), lab[i], i, P[i].round(4).tolist(), lab[j], j, P[j].round(4).tolist())
# compare assembled bodies to native
from scipy.spatial import cKDTree
T = cKDTree(d['X'][:, :2]); dist, idx = T.query(P[:, :2])
for name in ['corner', 'stacks1', 'stacks2', 'far1', 'far2', 'cells']:
    sel = np.array([l == name for l in lab])
    print('vs native', name, 'max', float(dist[sel].max()), 'n>1e-6', int((dist[sel] > 1e-6).sum()))
