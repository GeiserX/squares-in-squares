import sys, pickle, math, time, json
sys.path.insert(0, 'lane')
import numpy as np
import modules as M
b = pickle.load(open('compose/library-r33.pkl', 'rb'))
ns = [int(x) for x in sys.argv[1].split(',')]
for n in ns:
    lay = next(x for x in b['layouts'] if x['n'] == n)
    for idsname in ('ids_slide', 'ids'):
        for slide in (True, False):
            M.SLIDE = slide
            by = {q['id']: q for q in b['mods']}
            ids = lay[idsname]
            C, F1, F2 = by[ids[2]], by[ids[0]], by[ids[1]]
            f = lay['f']; m = lay['m']; L = m + f
            t1, t2 = M.flush_tilt(C['c1'], f), M.flush_tilt(C['c2'], f)
            p1, p2 = 1 / math.cos(t1), 1 / math.cos(t2)
            t = time.time()
            a = M.far_at(F1, f); c = M.far_at(F2, f)
            capy = L - a[0] - lay['s1'] * p1 if a else None
            capx = L - c[0] - lay['s2'] * p2 if c else None
            res = dict(n=n, ids=idsname, slide=slide, f=f, f0C=C['f0'], y0C=C['y0'] if 'y0' in C else None, x0C=C.get('x0'),
                       far1=a[0] if a else None, far1_len0=F1['len0'], far2=c[0] if c else None, far2_len0=F2['len0'], capy=capy, capx=capx)
            # corner minima by cost order, as corner_at does
            for first in (0, 1, None):
                cost = (1.0, 1.0) if first is None else ((1.0, 0.02) if first == 0 else (0.02, 1.0))
                at = M.corner_len(C, C['f0'], C['P'], C['y0'] + 1e-6, C['x0'] + 1e-6, cost)
                for g in M.path(C['f0'], f):
                    if at is None: break
                    at = M.corner_len(C, float(g), at[2], at[0] + 0.02, at[1] + 0.02, cost)
                res['corner_first%s' % first] = None if at is None else (at[0], at[1])
            co = M.corner_at(C, f, capy, capx) if capy is not None and capx is not None else None
            res['corner_at'] = None if co is None else (co[0], co[1])
            res['sec'] = round(time.time() - t, 1)
            print('DIAG ' + json.dumps(res), flush=True)
