"""Self rebuild repair test: corner LP from the native state with (a) native angles at f0 (no retilt),
(b) the heal step of relax when the fixed-angle LP has no start. Modules.py is imported, never edited."""
import sys, pickle, math, json, time
sys.path.insert(0, 'lane')
import numpy as np
import modules as M
b = pickle.load(open('compose/library-r33.pkl', 'rb'))
orig_corner_len = M.corner_len
def corner_len_fix(mod, f, Pm, y0, x0, cost=(1.0, 1.0), caps=(None, None), native=NATIVE if False else None):
    keep = abs(f - mod['f0']) < 1e-12 and MODE['native_angles']
    if keep:
        Pq = Pm
    else:
        new = [mod['lean1'] * math.degrees(M.flush_tilt(mod['c1'], f)) if mod['grp'][g[0]] == 1 else
               mod['lean2'] * math.degrees(M.flush_tilt(mod['c2'], f)) for g in mod['rig']]
        Pq = M.retilt(Pm, mod['rig'], new)
    P, mode = M.corner_state(mod, f, Pq, y0, x0)
    out = M.relax(P, mode, cost, caps) if (mod.get('turn') or MODE['heal']) else M.settle(P, mode, cost, caps)
    if out is None or not M.legal(out[0], mode): return None
    Q = out[0][:len(Pq)].copy(); Q[:, 2] = np.degrees(Q[:, 2])
    return y0 + out[1][0], x0 + out[1][1], Q
NATIVE = None
MODE = dict(native_angles=False, heal=False)
M.corner_len = corner_len_fix
for n in (705, 999, 934):
    lay = next(x for x in b['layouts'] if x['n'] == n)
    by = {q['id']: dict(id=q['id'], q=q) for q in b['mods']}
    ids = lay['ids_slide']
    for na, heal in ((False, True), (True, False), (True, True)):
        MODE.update(native_angles=na, heal=heal); M.SLIDE = True
        t = time.time(); got = None; why = None
        C = by[ids[2]]['q']
        for up in (0., 1e-4, 3e-4, 1e-3, 3e-3):
            P, why = M.assemble(None, n, by[ids[2]], by[ids[0]], by[ids[1]], lay['s1'], lay['s2'], lay['f'] + up)
            if P is not None:
                ok = M.legal(P, None)
                L = lay['m'] + lay['f'] + up
                got = dict(up=up, legal=bool(ok), side_model=L); break
        print('DIAGC ' + json.dumps(dict(n=n, native_angles=na, heal=heal, got=got, why=why, sec=round(time.time() - t, 1))), flush=True)
