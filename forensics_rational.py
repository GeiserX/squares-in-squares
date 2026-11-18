#!/usr/bin/env python3
"""Read the six-extra-square rectangle of the 5-12-13 family.

forensics_rational.py census OUTPUT.json SOURCE.csv [...]
forensics_rational.py pairs OUT_DIR SOURCE.csv [...]
forensics_rational.py control SOURCE.csv [...]

The measured part fits 9 by 18 at fraction 12/17. Pairs at m = 27
collide. At m >= 28, extra plain rows separate their ends. Outputs are
starts for a default fq quench, followed by floatsafe certification.
"""
import itertools
import json
import math
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_compose as fc
import forensics_rect as fr


F = 12 / 17


def sources(paths):
    for path in paths:
        for n, sq in fr.layouts(path).items():
            side, q = fc.frame(sq)
            yield str(path), n, side, q


def census(paths):
    reports = []
    for path, n, side, q in sources(paths):
        m = math.isqrt(n); f = side - m; raw = []
        for g, r in fr.sym8(q, side):
            k = fc.corners(r)
            ex, ey = k[:, :, 0].max(1), k[:, :, 1].max(1)
            for a in range(1, m + 1):
                for b in range(1, m + 1):
                    count = int(((ex <= a + f + 1e-9) & (ey <= b + f + 1e-9)).sum())
                    if count > a * b:
                        raw.append((count - a * b, a, b, g))
        windows = {}
        for e in sorted({x[0] for x in raw}):
            rows = [r for r in raw if r[0] >= e]
            dims = sorted({(a, b) for _, a, b, _ in rows})
            minimal = [(a, b) for a, b in dims if not any(
                c <= a and d <= b and (c < a or d < b) for c, d in dims)]
            windows[e] = [dict(w=a, h=b, sym=next(g for _, aa, bb, g in rows
                                                if (aa, bb) == (a, b)))
                          for a, b in minimal]
        reports.append(dict(n=n, path=path, f=f, windows=windows))
    return reports


def pairs(paths, outdir=None, only=None):
    src = list(sources(paths)); summary = []
    if outdir is not None:
        outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    for m in ((27, 28, 29, 30, 31) if only is None else only):
        n = m * m + 12; variants = []
        for a, b in ((9, m - 9), (m - 9, 9)):
            vs = []
            for path, dn, side, q in src:
                for g, r in fr.sym8(q, side):
                    k = fc.corners(r); need = a * b + 6
                    rank = np.maximum(k[:, :, 0].max(1) - a, k[:, :, 1].max(1) - b)
                    ids = np.argsort(rank, kind='stable')[:need]
                    if len(ids) < need:
                        continue
                    f = max(0., float(rank[ids].max()))
                    if f <= F + 2e-8:
                        vs.append((path, dn, g, f, r[ids].copy()))
            variants.append(vs)
        least_collision = math.inf; kept = []; seen = set()
        for aa, bb in itertools.product(*variants):
            pa, na, ga, fa, a = aa; pb, nb, gb, fb, b = bb
            side = m + max(fa, fb); a = a.copy(); b = b.copy()
            a[:, 1] = side - a[:, 1]; a[:, 2] *= -1
            b[:, 0] = side - b[:, 0]; b[:, 2] *= -1
            wo = fc.worst_overlap(a, b)
            least_collision = min(least_collision, abs(min(wo, 0)))
            key = np.round(np.r_[a[:, :2].ravel(), b[:, :2].ravel()], 7).tobytes()
            if key in seen or wo < -.06:
                continue
            seen.add(key)
            grid = [(i + .5, j + .5, 0) for i in range(9) for j in range(9)]
            grid += [(side - .5 - i, side - .5 - j, 0)
                     for i in range(m - 9) for j in range(m - 9)]
            x = np.r_[a, b, np.array(grid).reshape(-1, 3)]
            assert len(x) == n
            meta = dict(n=n, side=side, kind='forced rational-angle rectangle pair',
                        A=dict(source=[pa, na], sym=ga, w=9, h=m-9, excess=6),
                        B=dict(source=[pb, nb], sym=gb, w=m-9, h=9, excess=6), overlap=wo)
            if outdir is not None:
                dest = outdir / ('%d-crational-%d.csv' % (n, len(kept)))
                fc.write_csv(dest, n, x)
                Path(str(dest) + '.json').write_text(json.dumps(meta))
            kept.append((x, meta))
        summary.append(dict(m=m, n=n, variants=[len(v) for v in variants],
                            least_collision=least_collision, written=len(kept)))
        if outdir is None and m == 29:
            assert kept, 'known 853 pair absent'
            assert max(fc.worst_overlap(x) for x, _ in kept) > -1e-6
    return summary


def main(argv):
    if argv[1] == 'census':
        result = census(argv[3:])
        Path(argv[2]).write_text(json.dumps(result, indent=2))
    elif argv[1] == 'control':
        result = pairs(argv[2:], only=(27, 29))
        assert result[0]['written'] == 0 and result[0]['least_collision'] > .7
        assert result[1]['written'] > 0
        print('CONTROL 741 refused; 853 rebuilt within 1e-6 overlap', flush=True)
    else:
        result = pairs(argv[3:], argv[2])
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main(sys.argv)
