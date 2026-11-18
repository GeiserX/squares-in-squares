"""Round 34 join screen with the native residual corner model: the 705 and 999 corners at their own native f
(the only f where the model rebuilds them, measured 01:58Z), joined with every far module of the round 33 library
that has the right stack width, and every stack count that fits. A layout counts as a candidate when its side
m + f is below the live side of its count; it is certified and written for the full fq loop."""
import sys, json, math, csv, pickle, time, hashlib
from pathlib import Path
sys.path.insert(0, 'lane')
import modules as M
import classfill_native34 as N
import classfill_finish as F
tag = sys.argv[1]
out = Path('out/joins-' + tag); out.mkdir(parents=True, exist_ok=True)
live = {int(r['n']): float(r['L']) for r in csv.DictReader(open('bar.csv'))}
lib = pickle.load(open('compose/library-r33.pkl', 'rb'))
fars = [q for q in lib['mods'] if q['kind'] == 'far']
M.SLIDE = True
rep = []
for n0 in (705, 999):
    d, why = M.cut(M.read_layouts('held-%d.csv' % n0)[n0], n0)
    mods = M.modules_of(d, 'held n=%d of gather/round33-2026-11-17a.csv' % n0, 'our own submitted packing', 'nat34'); tw, ids = M.slid(d, mods)
    by = {q['id']: q for q in mods + tw}
    C = by[ids[2]]; r, msg = N.measure(C, d, d['s1'], d['s2']); N.RES.clear(); N.RES[C['id']] = r; N.install()
    f = d['f']; m = d['m']; L = m + f
    t1, t2 = M.flush_tilt(C['c1'], f), M.flush_tilt(C['c2'], f); p1, p2 = 1 / math.cos(t1), 1 / math.cos(t2)
    own = [by[ids[0]], by[ids[1]]]
    for F1 in own[:1] + [q for q in fars if q['c'] == C['c1']]:
        a1 = M.far_at(F1, f)
        if a1 is None: continue
        for F2 in own[1:] + [q for q in fars if q['c'] == C['c2']]:
            if F1 is own[0] and F2 is own[1]: continue
            a2 = M.far_at(F2, f)
            if a2 is None: continue
            S1 = int((L - C['y0'] - a1[0]) / p1); S2 = int((L - C['x0'] - a2[0]) / p2)
            for s1 in (S1, S1 - 1):
                for s2 in (S2, S2 - 1):
                    if s1 < 1 or s2 < 1: continue
                    t = time.time()
                    P, why = M.assemble(None, m * m + 1, dict(id=C['id'], q=C), dict(id=F1['id'], q=F1), dict(id=F2['id'], q=F2), s1, s2, f)
                    if P is not None or not why.startswith('holds'):
                        rep.append(dict(corner=C['id'], F1=F1['id'], F2=F2['id'], s1=s1, s2=s2, why=why)); continue
                    n = int(why.split()[1])
                    if not (m * m < n <= (m + 1) ** 2) or n not in live:
                        rep.append(dict(corner=C['id'], F1=F1['id'], F2=F2['id'], s1=s1, s2=s2, n=n, why='count outside m')); continue
                    margin = live[n] - L
                    rec = dict(corner=C['id'], F1=F1['id'], F2=F2['id'], s1=s1, s2=s2, n=n, side=L, live=live[n], margin=margin)
                    if margin > -2e-3:
                        P, why = M.assemble(None, n, dict(id=C['id'], q=C), dict(id=F1['id'], q=F1), dict(id=F2['id'], q=F2), s1, s2, f)
                        if P is None:
                            rec['why'] = why
                        else:
                            raw = out / ('%d-%s-%s-%s-%d-%d.csv' % (n, C['id'], F1['id'], F2['id'], s1, s2)).replace('~', 't')
                            M.write_layout(str(raw), n, P); cert = F.certify(raw, n)
                            rec['legal'] = bool(M.legal(P))
                            if cert:
                                F.write(raw, cert[1]); rec['cert_side'] = (1 + cert[0]) * n ** .5; rec['cert_margin'] = live[n] - rec['cert_side']
                                rec['path'] = str(raw); rec['sha256'] = hashlib.sha256(raw.read_bytes()).hexdigest()
                                rec['sources'] = dict(corner=C['src'], far1=F1['src'], far2=F2['src'])
                                raw.with_suffix('.json').write_text(json.dumps(rec, indent=1) + '\n')
                    rec['sec'] = round(time.time() - t, 2)
                    rep.append(rec); print('JOIN ' + json.dumps({k: v for k, v in rec.items() if k != 'sources'}), flush=True)
(out / 'report.json').write_text(json.dumps(rep, indent=1) + '\n')
(out / 'DONE').write_text(time.strftime('%FT%TZ', time.gmtime()) + '\n')
print('JOINSCAN_DONE', len(rep), flush=True)
