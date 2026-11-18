import sys, math
sys.path.insert(0, 'lane')
import numpy as np
import modules as M
import classfill_native34 as N
n = int(sys.argv[1])
d, why = M.cut(M.read_layouts('held-%d.csv' % n)[n], n)
mods = M.modules_of(d, 'x', 'x', 'nat34'); tw, ids = M.slid(d, mods)
by = {q['id']: q for q in mods + tw}; M.SLIDE = True
C = by[ids[2]]; r, msg = N.measure(C, d, d['s1'], d['s2']); N.RES[C['id']] = r; N.install()
s1, s2 = d['s1'], d['s2']
print('last stack residuals s1', [tuple(round(v, 5) for v in r['s1'][(s1 - 1, k)]) for k in range(C['c1'])])
print('last stack residuals s2', [tuple(round(v, 5) for v in r['s2'][(s2 - 1, k)]) for k in range(C['c2'])])
print('first stack residuals s2', [tuple(round(v, 5) for v in r['s2'][(0, k)]) for k in range(C['c2'])])
f = d['f']; L = d['m'] + f
f1 = M.far_at(by[ids[0]], f); f2 = M.far_at(by[ids[1]], f)
t1, t2 = M.flush_tilt(C['c1'], f), M.flush_tilt(C['c2'], f); p1, p2 = 1 / math.cos(t1), 1 / math.cos(t2)
cy, cx = L - f1[0] - s1 * p1, L - f2[0] - s2 * p2
for ey, ex in ((0, 0), (0.001, 0.001), (0.0022, 0.0022)):
    co = M.corner_at(C, f, cy - ey, cx - ex)
    print('caps -', ey, ex, '->', None if co is None else (co[0], co[1]))
