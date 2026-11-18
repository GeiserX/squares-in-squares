#!/usr/bin/env python3
"""midm: one sqpack job on one n (Couzo's sqpack, MIT, used by path), with the starts of drive.py.

  local  the layout of n (sqpack --local)
  drop   the layout of n+1 (sqpack drops a square by the init's size)
  grow   the layout of n-1 (sqpack adds one)
The side of the result is measured here with methods_lp.side. A result below the held side is written to
OUT/raw/<n>-sq<mode>-<seed>.csv (raw rows; methods_take.py certifies). One line per job in OUT/sqpack.tsv.

Usage: midm_sqpack.py --n N --sub HELD.csv --out DIR --sqpack PATH --mode local|drop|grow [--seconds 150] [--seed 1] [--ref SIDE]
"""
import argparse, csv, math, os, subprocess, sys, tempfile, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import methods_lp as mlp  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, required=True); ap.add_argument('--sub', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--sqpack', required=True); ap.add_argument('--mode', default='local')
    ap.add_argument('--seconds', type=float, default=150); ap.add_argument('--seed', type=int, default=1); ap.add_argument('--ref', type=float, default=0.0)
    a = ap.parse_args()
    n = a.n; os.makedirs(a.out + '/raw', exist_ok=True)
    src_n = {'local': n, 'drop': n + 1, 'grow': n - 1}[a.mode]
    L = mlp.load(a.sub, {n, src_n}); Lheld = mlp.side(L[n]); src = mlp.normal(L[src_n])
    work = tempfile.mkdtemp(prefix='sq%d-' % n, dir=a.out)
    with open(work + '/init.txt', 'w') as h:
        h.write('# n = %d\n' % n)
        for x, y, t in src:
            h.write('%r %r %r\n' % (float(x), float(y), float(t)))
    open(work + '/records.txt', 'w').write('%d %r\n' % (n, Lheld))
    cmd = [os.path.abspath(a.sqpack), 'search', str(n), '--time', str(a.seconds), '--threads', '1', '--seed', str(a.seed), '--init', 'init.txt']
    if a.mode == 'local':
        cmd.append('--local')
    t0 = time.time()
    with open(work + '/sqpack.log', 'w') as lf:
        try:
            subprocess.run(cmd, cwd=work, stdout=lf, stderr=subprocess.STDOUT, timeout=a.seconds * 3 + 120)
        except subprocess.TimeoutExpired:
            pass
    res = '%s/results/n%d.txt' % (work, n); side = math.nan
    if os.path.exists(res):
        z = [tuple(float(v) for v in l.split()[:3]) for l in open(res) if l.strip() and not l.startswith('#')]
        if len(z) == n:
            P = mlp.normal(np.array(z)); side = mlp.side(P)
            if side < Lheld - 1e-9:
                with open('%s/raw/%d-sq%s-%d.csv' % (a.out, n, a.mode, a.seed), 'w', newline='') as g:
                    w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                    for i, (x, y, t) in enumerate(P):
                        w.writerow([n, i, repr(float(x)), repr(float(y)), repr(float(t))])
    with open(a.out + '/sqpack.tsv', 'a') as h:
        h.write('%d\t%s\t%d\t%.0f\t%.12f\t%.12f\t%s\t%s\n' % (n, a.mode, a.seed, time.time() - t0, Lheld, side,
                                                           'below' if side < Lheld - 1e-9 else 'no', 'ref' if (a.ref and side <= a.ref + 1e-7) else '-'))
    print('n=%d sqpack %s seed %d: held %.12f result %.12f' % (n, a.mode, a.seed, Lheld, side), flush=True)


if __name__ == '__main__':
    main()
