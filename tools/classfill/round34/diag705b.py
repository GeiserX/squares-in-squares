import sys, pickle, math, json
sys.path.insert(0, 'lane')
import numpy as np
import modules as M
b = pickle.load(open('compose/library-r33.pkl', 'rb'))
by = {q['id']: q for q in b['mods']}
for cid, slide in (('705cj33.C~', True), ('705cj33.C', False), ('705cj33.C', True), ('999cj33.C~', True), ('999cj33.C', False), ('934cj33.C', True)):
    M.SLIDE = slide
    C = by[cid]; f = C['f0']
    new = [C['lean1'] * math.degrees(M.flush_tilt(C['c1'], f)) if C['grp'][g[0]] == 1 else C['lean2'] * math.degrees(M.flush_tilt(C['c2'], f)) for g in C['rig']]
    Pm = M.retilt(C['P'], C['rig'], new)
    dP = float(np.max(np.abs(Pm - C['P'])))
    out = {}
    for eps in (1e-6, 1e-4, 1e-3, 1e-2):
        P, mode = M.corner_state(C, f, Pm, C['y0'] + eps, C['x0'] + eps)
        pairs = M.pair_list(P, math.sqrt(2) + 1e-3)
        ma, mb = mode[pairs[:, 0]], mode[pairs[:, 1]]
        pairs = pairs[~(((ma != 0) & (mb != 0)) & ~((ma > 0) & (mb > 0) & (ma != mb)))]
        g = M.best_axes(P, pairs)[0]
        i = int(np.argmin(g))
        s = M.settle(P, mode, (1.0, 1.0))
        out[eps] = dict(min_gap=float(g.min()), worst=(int(pairs[i, 0]), int(pairs[i, 1]), int(mode[pairs[i, 0]]), int(mode[pairs[i, 1]])),
                        n_neg=int((g < -2e-9).sum()), settle=None if s is None else [round(C['y0'] + eps + s[1][0], 9), round(C['x0'] + eps + s[1][1], 9), bool(M.legal(s[0], mode))])
    print('DIAGB ' + json.dumps(dict(id=cid, slide=slide, turn=bool(C.get('turn')), retilt_change=dP, nPm=len(Pm), miss=len(C['miss']), y0=C['y0'], x0=C['x0'], states=out)), flush=True)
