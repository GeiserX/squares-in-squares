import sys, json, math
from pathlib import Path
sys.path.insert(0, 'lane')
import modules as M
import classfill_native34 as N
import classfill_finish as F
n = int(sys.argv[1]); N.STACK0_ONLY = sys.argv[2] == '1'
d, why = M.cut(M.read_layouts('held-%d.csv' % n)[n], n)
mods = M.modules_of(d, 'x', 'x', 'nat34'); tw, ids = M.slid(d, mods)
by = {q['id']: dict(id=q['id'], q=q) for q in mods + tw}; M.SLIDE = True
C = by[ids[2]]['q']; r, msg = N.measure(C, d, d['s1'], d['s2']); N.RES[C['id']] = r; N.install()
for up in (0., 1e-5, 1e-4, 3e-4, 1e-3, 3e-3, -1e-4):
    P, why = M.assemble(None, n, by[ids[2]], by[ids[0]], by[ids[1]], d['s1'], d['s2'], d['f'] + up)
    if P is None: print('up', up, why); continue
    raw = Path('tmp/%d-fscan.csv' % n); M.write_layout(str(raw), n, P); cert = F.certify(raw, n)
    print('up', up, 'legal', M.legal(P), 'cert_side-native', None if cert is None else (1 + cert[0]) * n ** .5 - (d['m'] + d['f']))
