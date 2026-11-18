"""Predict the count frontier of fresh joins at the measured quartic fraction."""
import json
import math
from pathlib import Path
import numpy as np
import forensics_rect as rect
import forensics_compose as fc

FRACTION = 0.6008017348087404


def predict(src, tf, start, sides, output, force=False):
    """List side-qualified counts before assembly. Collisions remain untested."""
    limit = FRACTION + 5e-8
    excess = np.arange(tf.shape[2])[None, None, :]
    partner = np.max(np.where(tf[..., 0] <= limit, excess, 0), axis=2)
    predictions = []
    for key, side, q in src[start:]:
        path, n0 = key
        original = Path(str(path) + '.origin.json')
        origin = json.loads(original.read_text()).get('path', path) if original.exists() else path
        if not force and not any(tag in str(origin) for tag in ('take-k123-r24/', 'take-k123-r25/', 'take-k123-r26/')):
            continue
        mm = min(32, int(math.ceil(side - 1e-9)))
        widths = np.arange(1, mm + 1)
        for sym, r in rect.sym8(q, side):
            corners = fc.corners(r)
            ex = corners[:, :, 0].max(1)
            ey = corners[:, :, 1].max(1)
            counts = np.sum((ex[None, None, :] <= widths[:, None, None] + limit) &
                            (ey[None, None, :] <= widths[None, :, None] + limit), axis=2)
            ea = counts - widths[:, None] * widths[None, :]
            for m in range(2, 32):
                cap = min(m - 1, mm)
                wb = m - widths[:cap]
                hb = m - widths[:cap]
                eb = partner[wb[:, None], hb[None, :]]
                ks = ea[:cap, :cap] + eb
                good = (ea[:cap, :cap] > 0) & (eb > 0)
                if not good.any():
                    continue
                k = int(np.max(np.where(good, ks, 0)))
                n = m*m + k
                if n > 1000 or (not force and m + FRACTION >= sides[n] - 1e-7):
                    continue
                wi, hi = np.argwhere(good & (ks == k))[0]
                predictions.append(dict(source=origin, snapshot=path, source_n=n0,
                                        sym=sym, m=m, n=n, predicted_side=m + FRACTION,
                                        A=[int(wi + 1), int(hi + 1), int(ea[wi, hi])],
                                        B=[int(m-wi-1), int(m-hi-1), int(eb[wi, hi])],
                                        status='side-qualified; pair collision untested'))
    Path(output).write_text(json.dumps(predictions, indent=2))
    return predictions
