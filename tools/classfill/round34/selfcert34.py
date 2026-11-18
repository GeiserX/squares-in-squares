import sys, json, math
from pathlib import Path
sys.path.insert(0, 'lane')
import modules as M
import classfill_native34 as N
import classfill_finish as F
n = int(sys.argv[1])
d, why = M.cut(M.read_layouts('held-%d.csv' % n)[n], n)
mods = M.modules_of(d, 'x', 'x', 'nat34'); tw, ids = M.slid(d, mods)
by = {q['id']: dict(id=q['id'], q=q) for q in mods + tw}; M.SLIDE = True
C = by[ids[2]]['q']; r, msg = N.measure(C, d, d['s1'], d['s2']); N.RES[C['id']] = r; N.install()
for up in (0., 1e-4, 3e-4, 1e-3):
    P, why = M.assemble(None, n, by[ids[2]], by[ids[0]], by[ids[1]], d['s1'], d['s2'], d['f'] + up)
    if P is None: print('up', up, why); continue
    raw = Path('tmp/%d-selfcert.csv' % n); M.write_layout(str(raw), n, P); cert = F.certify(raw, n)
    print('up', up, 'legal', M.legal(P), 'cert_side', None if cert is None else repr((1 + cert[0]) * n ** .5), 'native side', repr(d['m'] + d['f']))
    if cert and (1 + cert[0]) * n ** .5 < d['m'] + d['f'] + .0011:
        wrong, reason = M.assemble(None, n + 1, by[ids[2]], by[ids[0]], by[ids[1]], d['s1'], d['s2'], d['f'] + up)
        print('SELF_PASS', json.dumps(dict(n=n, up=up, certified_side=(1 + cert[0]) * n ** .5, wrong_count=reason))); break
