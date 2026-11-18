"""Share of squares a public layout has in common with each excluded layout of rules a-d (data, read only).

  python -I share_ac.py REFDIR N[,N...]
For each n: the reference REFDIR/<n>.csv against every excluded layout audit_ac.excluded(n) finds.
Both are centred on their bounding box; over the 8 symmetries the one with the most squares
matched is kept. Prints max centre distance, and the share of reference squares whose nearest
excluded centre is within 1e-6, 1e-3 and 1e-2 (a copy reads 1.0 at 1e-6; a polished copy about
1.0 at 1e-3; an independent design of the same count reads low at 1e-3).
"""
import csv, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import audit_ac as A  # noqa: E402


def share(a, b):
    best = None
    for sw in (False, True):
        for sx in (1, -1):
            for sy in (1, -1):
                c = a[:, ::-1] if sw else a
                c = c * np.array([sx, sy])
                d = np.sqrt(((c[:, None, :] - b[None, :, :]) ** 2).sum(-1)).min(1)
                r = (float((d < 1e-6).mean()), float((d < 1e-3).mean()), float((d < 1e-2).mean()), float(d.max()))
                if best is None or r[1:3] > best[1:3]:
                    best = r
    return best


def main():
    refdir = Path(sys.argv[1])
    for n in [int(x) for x in sys.argv[2].split(',')]:
        rows = list(csv.DictReader(open(refdir / f'{n}.csv')))
        c = A.centres(rows)
        out = []
        for label, ex in A.excluded(n):
            s = share(c, A.centres(ex))
            out.append(f'{label[:28]}: 1e-6 {s[0]:.3f} 1e-3 {s[1]:.3f} 1e-2 {s[2]:.3f} max {s[3]:.3g}')
        print(n, ' | '.join(out) or 'no excluded layout of this n', flush=True)


if __name__ == '__main__':
    main()
