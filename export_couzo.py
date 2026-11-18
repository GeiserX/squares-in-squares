#!/usr/bin/env python3
"""Export franciscouzo/square-packing (MIT) best packings to Kaggle rows, per n.

Usage: export_couzo.py <couzo checkout> <out.csv>

Wraps the repo's own prepare_kaggle.Packings. Its algebraic-certificate
branch needs an experiments/ tree that the public repo does not ship; for
those n we fall back to the finite certificate the repo also keeps (a
slightly weaker packing), and if that fails too the n is skipped (the merge
step fills it from another source).
"""
import csv, sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
import mpmath as mp  # noqa: E402
import prepare_kaggle as pk  # noqa: E402

out = Path(sys.argv[2])
with mp.workdps(pk.DPS):
    P = pk.Packings(root, ())
    with out.open('w', newline='') as h:
        w = csv.writer(h, lineterminator='\n')
        w.writerow(pk.COLUMNS)
        idx = 0
        for n in range(1, 1001):
            try:
                rows, src = P.rows(n)
            except Exception as e:  # algebraic certificate missing
                saved = P.upper[str(n)]['verified']
                try:
                    P.upper[str(n)]['verified'] = P.finite[str(n)]
                    rows, src = P.rows(n)
                    print(f'n={n}: fell back to finite certificate ({e})', file=sys.stderr)
                except Exception as e2:
                    print(f'n={n}: skipped ({e2})', file=sys.stderr)
                    continue
                finally:
                    P.upper[str(n)]['verified'] = saved
            factor = 1 if src['kind'] == 'grid' else 1 + mp.mpf(pk.CENTRE_DILATION)
            for sid, (x, y, t) in enumerate(rows[:n]):
                if src['kind'] == 'grid':
                    vals = [str(float(x)), str(float(y)), '0']
                else:
                    vals = [pk.number(x * factor), pk.number(y * factor), pk.number(t)]
                w.writerow([idx, n, sid, *vals])
                idx += 1
print('rows', idx)
