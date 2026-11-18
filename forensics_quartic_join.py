"""Test the rectangle count frontier predicted at the quartic fraction."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_compose as fc
import forensics_predict as predict
import forensics_rect as rect


def build(cache, source, n, output, max_starts=32):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    source = Path(source)
    n0, sq = next(iter(rect.layouts(source).items()))
    s, q = fc.frame(sq)
    tf, ti, src = cache['TF'], cache['TI'], cache['src']
    m, k = fc.mk(n)
    limit = predict.FRACTION + 5e-8
    signatures = set()
    counts = dict(tested=0, valid=0, colliding=0, refused=0)
    best_collision = -float('inf')
    for ga, r in rect.sym8(q, s):
        corners = fc.corners(r)
        ex, ey = corners[:, :, 0].max(1), corners[:, :, 1].max(1)
        for wa in range(1, m):
            wb = m-wa
            for ha in range(1, m):
                hb = m-ha
                da = np.maximum(ex-wa, ey-ha)
                for ea in range(1, k):
                    eb = k-ea
                    ca = wa*ha+ea
                    if ca > n0:
                        continue
                    fa = max(0., float(np.partition(da, ca-1)[ca-1]))
                    if fa > limit:
                        continue
                    pa0 = r[np.flatnonzero(da <= fa + 1e-15)[:ca]].copy()
                    for slot in range(cache['keep']):
                        fb = tf[wb,hb,eb,slot]
                        if fb > limit:
                            break
                        li, gb = divmod(int(ti[wb,hb,eb,slot]), 8)
                        key, sb, qb = src[li]
                        rb = dict(rect.sym8(qb,sb))[gb]
                        kb = fc.corners(rb)
                        db = np.maximum(kb[:,:,0].max(1)-wb,kb[:,:,1].max(1)-hb)
                        pb = rb[np.flatnonzero(db <= fb + 1e-15)[:wb*hb+eb]].copy()
                        side = m+max(fa,fb)
                        pa = pa0.copy()
                        pa[:,1] = side-pa[:,1]
                        pa[:,2] *= -1
                        pb[:,0] = side-pb[:,0]
                        pb[:,2] *= -1
                        wo = fc.worst_overlap(pa,pb)
                        counts['tested'] += 1
                        best_collision = max(best_collision,wo)
                        if wo < -.06:
                            counts['refused'] += 1
                            continue
                        grid = [(i+.5,j+.5,0.) for i in range(wa) for j in range(hb)]
                        grid += [(side-.5-i,side-.5-j,0.) for i in range(wb) for j in range(ha)]
                        x = np.r_[pa,pb,np.array(grid).reshape(-1,3)]
                        assert len(x)==n
                        digest = hashlib.sha256(np.round(x,7).tobytes()).hexdigest()
                        if digest in signatures or len(signatures)>=max_starts:
                            continue
                        signatures.add(digest)
                        colliding = wo < -1e-9
                        if not colliding:
                            assert fc.worst_overlap(x) >= -1e-9
                        counts['colliding' if colliding else 'valid'] += 1
                        path = output / ('%d-%squartic-%s.csv' % (n,'c' if colliding else 'p',digest[:12]))
                        fc.write_csv(path,n,x)
                        parts = dict(kind='quartic predicted rectangle frontier',n=n,side=side,
                                     A=dict(source=[str(source),n0],sym=ga,w=wa,h=ha,excess=ea),
                                     B=dict(source=list(key),sym=gb,w=wb,h=hb,excess=eb))
                        Path(str(path)+'.json').write_text(json.dumps(parts))
    result = dict(n=n,source=str(source),fraction=predict.FRACTION,
                  best_pair_clearance=best_collision,starts=len(signatures),**counts)
    (output.parent/'measurement.json').write_text(json.dumps(result,indent=2))
    return result
