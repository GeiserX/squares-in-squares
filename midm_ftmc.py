#!/usr/bin/env python3
"""midm: one FTMC job on one n (Evan Daniel's ftmc.py, MIT, run from a dir that holds only ftmc.py, gen.py,
layout.py and target/release/packer of his repo; nothing of it is copied into this repo).

The start is the layout of n in SUB. The full-line test is off (--k 999), as in ftmc_queue.py. A result below
the held side is written to OUT/raw/<n>-ftmc-<seed>.csv (raw rows; methods_take.py certifies). One line per
job in OUT/ftmc.tsv.

Usage: midm_ftmc.py --n N --sub HELD.csv --out DIR --ftmc DIR [--seconds 150] [--seed 1] [--ref SIDE]
"""
import argparse, csv, math, os, subprocess, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import methods_lp as mlp  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, required=True); ap.add_argument('--sub', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--ftmc', required=True); ap.add_argument('--seconds', type=float, default=150)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--ref', type=float, default=0.0)
    a = ap.parse_args()
    n = a.n; out = os.path.abspath(a.out); os.makedirs(out + '/raw', exist_ok=True)
    P = mlp.normal(mlp.load(a.sub, {n})[n]); Lheld = mlp.side(P)
    d = np.degrees(P[:, 2]) % 90.0; d = np.where(d > 45, d - 90, d)
    init = '%s/ftmc-%d-%d.txt' % (out, n, a.seed); pre = '%s/ftmc-%d-%d' % (out, n, a.seed)
    with open(init, 'w') as h:
        h.write('%d %r\n' % (n, float(Lheld)))
        for (x, y, _), g in zip(P, d):
            h.write('%r %r %r\n' % (float(x), float(y), float(g)))
    t0 = time.time()
    with open(pre + '.log', 'w') as lf:
        subprocess.run([sys.executable, 'ftmc.py', '--n', str(n), '--k', '999', '--init', init, '--seed', str(a.seed),
                        '--time', str(a.seconds), '--out', pre], cwd=a.ftmc, stdout=lf, stderr=subprocess.STDOUT)
    side = math.nan; best = pre + '.best.txt'
    if os.path.exists(best):
        L = [l.split() for l in open(best) if l.strip() and not l.startswith('#')]
        if int(L[0][0]) == n and len(L) >= n + 1:
            Q = np.array([[float(q[0]), float(q[1]), math.radians(float(q[2]))] for q in L[1:n + 1]])
            Q = mlp.normal(Q); side = mlp.side(Q)
            if side < Lheld - 1e-9:
                with open('%s/raw/%d-ftmc-%d.csv' % (out, n, a.seed), 'w', newline='') as g:
                    w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                    for i, (x, y, t) in enumerate(Q):
                        w.writerow([n, i, repr(float(x)), repr(float(y)), repr(float(t))])
    last = open(pre + '.log').read().strip().splitlines()[-1:] or ['']
    with open(out + '/ftmc.tsv', 'a') as h:
        h.write('%d\t%d\t%.0f\t%.12f\t%.12f\t%s\t%s\t%s\n' % (n, a.seed, time.time() - t0, Lheld, side, 'below' if side < Lheld - 1e-9 else 'no',
                                                             'ref' if (a.ref and side <= a.ref + 1e-7) else '-', last[0][:160]))
    print('n=%d ftmc seed %d: held %.12f result %.12f | %s' % (n, a.seed, Lheld, side, last[0][:160]), flush=True)


if __name__ == '__main__':
    main()
