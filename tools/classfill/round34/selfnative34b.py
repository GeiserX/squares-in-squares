import sys, json, math, time
sys.path.insert(0, 'lane')
import numpy as np
import modules as M
import classfill_native34 as N
import classfill_finish as F
for n in [int(x) for x in sys.argv[1].split(',')]:
    sq = M.read_layouts('held-%d.csv' % n)[n]
    d, why = M.cut(sq, n)
    mods = M.modules_of(d, 'x', 'x', 'nat34'); tw, ids = M.slid(d, mods)
    by = {q['id']: dict(id=q['id'], q=q) for q in mods + tw}
    for idl in (ids, [ids[0].rstrip('~'), ids[1].rstrip('~'), ids[2].rstrip('~')]):
        M.SLIDE = True
        C = by[idl[2]]['q']
        r, msg = N.measure(C, d, d['s1'], d['s2']); N.RES.clear(); N.RES[C['id']] = r; N.install()
        res = dict(n=n, ids=idl, measure=msg)
        for up in (0., 1e-4, 3e-4, 1e-3, 3e-3):
            t = time.time()
            P, why = M.assemble(None, n, by[idl[2]], by[idl[0]], by[idl[1]], d['s1'], d['s2'], d['f'] + up)
            if P is None:
                res['up%g' % up] = why; continue
            raw = 'tmp/%d-selfnat.csv' % n; M.write_layout(raw, n, P)
            cert = F.certify(__import__('pathlib').Path(raw), n)
            res['up%g' % up] = dict(legal=bool(M.legal(P)), cert_side=None if cert is None else (1 + cert[0]) * n ** .5, model_side=d['m'] + d['f'] + up, sec=round(time.time() - t, 1))
            if cert and (1 + cert[0]) * n ** .5 < d['m'] + d['f'] + .0011:
                res['PASS_up'] = up; break
        print('SELFNATB ' + json.dumps(res), flush=True)
