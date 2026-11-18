#!/usr/bin/env python3
"""rebuild_pool.py OUT.csv N:FILE [N:FILE ...]: a k123 join pool where each layout is turned to the symmetry
whose k123_join.norm reading finds the most chains. A corner-window layout can sit so that norm keeps the band
on the wrong diagonal and reads 3 chains (6, 84, 6) where 30 exist; the k123 scan then never finds its seams.
Our own code; imports methods_lp, k123_join and k123_step57 unchanged."""
import csv, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import methods_lp as m  # noqa: E402
import k123_join as kj  # noqa: E402
import k123_step57 as st  # noqa: E402


def sym(P, k):
    Q, L = st.boxed(P); R = Q.copy()
    if k & 1:
        R[:, 0] = L - R[:, 0]; R[:, 2] = -R[:, 2]
    if k & 2:
        R[:, 1] = L - R[:, 1]; R[:, 2] = -R[:, 2]
    if k & 4:
        R = R[:, [1, 0, 2]]; R[:, 2] = math.pi / 2 - R[:, 2]
    return R


def best(P, n):
    out = (-1, P, 0)
    for k in range(8):
        R = sym(P, k)
        try:
            Q, L = kj.norm(R); c = len(kj.Lay(n, Q, L, 'x').size)
        except Exception:
            continue
        if c > out[0]:
            out = (c, R, k)
    return out


if __name__ == '__main__':
    with open(sys.argv[1], 'w') as f:
        w = csv.writer(f); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for spec in sys.argv[2:]:
            n, p = spec.split(':', 1); n = int(n)
            c, R, k = best(m.load(p, {n})[n], n)
            print(n, p, 'chains', c, 'sym', k, 'gap %.2e' % m.min_gap(R))
            w.writerows((n, i, *r) for i, r in enumerate(R))
