"""Self rebuild control with the native residual corner model: corner LP from the native state, then the corner
squares placed into the native layout (the arms and the rest kept native). Passes when the corner state the model
finds at the native f fits under both native arms within +1e-3 of side, and the native layout certifies with it.
Then measures the same corner at f0 + 1e-4, 1e-3, 3e-3 (does the model state exist, and its lengths)."""
import sys, json, math, pickle, time
sys.path.insert(0, 'lane')
import numpy as np
import modules as M
import classfill_native34 as N
import classfill_finish as F
for n in [int(x) for x in sys.argv[1].split(',')]:
    sq = M.read_layouts('held-%d.csv' % n)[n]
    d, why = M.cut(sq, n)
    mods = M.modules_of(d, 'x', 'x', 'nat34'); tw, ids = M.slid(d, mods)
    by = {q['id']: q for q in mods + tw}
    out = dict(n=n)
    for cid in (ids[2], ids[2].rstrip('~')):
        M.SLIDE = cid.endswith('~') or True
        C = by[cid]
        r, msg = N.measure(C, d, d['s1'], d['s2'])
        rec = dict(measure=msg)
        if r is None:
            out[cid] = rec; continue
        N.RES[C['id']] = r; N.install()
        P, mode = M.corner_state(C, C['f0'], C['P'], C['y0'], C['x0'])
        rec['native_state_legal'] = bool(M.legal(P, mode))
        pairs = M.pair_list(P, math.sqrt(2) + 1e-3); ma, mb = mode[pairs[:, 0]], mode[pairs[:, 1]]
        pairs = pairs[~(((ma != 0) & (mb != 0)) & ~((ma > 0) & (mb > 0) & (ma != mb)))]
        rec['native_min_gap'] = float(M.best_axes(P, pairs)[0].min())
        t = time.time()
        at = M.corner_len(C, C['f0'], C['P'], C['y0'] + 1e-6, C['x0'] + 1e-6, (1.0, 1.0))
        rec['lp_at_f0'] = None if at is None else [at[0] - C['y0'], at[1] - C['x0']]
        for df in (1e-4, 1e-3, 3e-3):
            a2 = at
            for g in M.path(C['f0'], C['f0'] + df):
                if a2 is None: break
                a2 = M.corner_len(C, float(g), a2[2], a2[0] + 0.02, a2[1] + 0.02, (1.0, 1.0))
            rec['lp_at_f0+%g' % df] = None if a2 is None else [a2[0] - C['y0'], a2[1] - C['x0']]
        rec['sec'] = round(time.time() - t, 1)
        out[cid] = rec
    print('SELFNAT ' + json.dumps(out), flush=True)
