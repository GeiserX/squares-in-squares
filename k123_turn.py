#!/usr/bin/env python3
"""A collective turn of the tilted squares of a layout, then one fq quench (avenues/k123.md, section 9).

A band of chains sits on its jam line: the side falls when every chain turns a little further, and a random
kick never makes that move, because it has to turn every chain by the same angle at once. This tool makes
the move by hand. It turns every tilted square of a layout by the same angle and lets fq squeeze the box.

  self   each tilted square turns about its own centre (the band keeps its axis, the chains turn)
  band   all tilted squares turn as one rigid body about their centroid

usage: k123_turn.py LAYOUT.csv N OUTDIR FQ [--turns=-0.3,-0.1,0.1,0.3] [--modes self,band]
                    [--loosen 1.003,1.01] [--bar SIDE] [--keep]
  LAYOUT.csv  a file with the Kaggle rows of n (a held file, or a raw file that midm_scan.py wrote)
  --bar       the side to beat (default: the side of the layout itself)
  --keep      write every result to OUTDIR/turn/<n>-<mode>-<turn>-<loosen>.csv, not only the ones below the bar
One line per try goes to OUTDIR/turn-<n>.tsv. A result below the bar by
max(1e-9, sqrt(n)*1e-10) gets the deep polish of
midm_scan.py and is written to OUTDIR/raw/<n>-turn-<mode>-<turn>-<loosen>.csv (raw rows; certify with
methods_take.py on boxA).

Control (it can fail): turn a held band by -0.3 degrees with --keep, then give the result back to the tool
with the turns +0.1 to +0.5 and --bar unset. The tool must come back to the held side.
Our own code. It imports midm_scan (quench, polish flags) and methods_lp and does not change them. fq is
Evan Daniel's MIT quench binary, used by path.
"""
import argparse, math, os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import methods_lp as mlp  # noqa: E402
import midm_scan as ms  # noqa: E402


def turned(P, mode, deg):
    """The layout with its tilted squares turned by deg."""
    Q = mlp.normal(P).copy(); t = ms.tilted(Q); a = math.radians(deg)
    if not t.any():
        return Q
    if mode == 'band':
        c = Q[t, :2].mean(axis=0); d = Q[t, :2] - c
        ca, sa = math.cos(a), math.sin(a)
        Q[t, 0] = c[0] + ca * d[:, 0] - sa * d[:, 1]
        Q[t, 1] = c[1] + sa * d[:, 0] + ca * d[:, 1]
    Q[t, 2] += a
    return Q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('layout'); ap.add_argument('n', type=int); ap.add_argument('out'); ap.add_argument('fq')
    ap.add_argument('--turns', default='-0.3,-0.2,-0.1,-0.05,0.05,0.1,0.2,0.3')
    ap.add_argument('--modes', default='self,band'); ap.add_argument('--loosen', default='1.003,1.01')
    ap.add_argument('--bar', type=float, default=0.0); ap.add_argument('--keep', action='store_true')
    a = ap.parse_args()
    n = a.n; os.makedirs(a.out, exist_ok=True); tmp = a.out + '/tmp'; os.makedirs(tmp, exist_ok=True)
    P = mlp.load(a.layout, {n})[n]
    L0 = mlp.side(P); bar = a.bar or L0; best = bar
    lg = open('%s/turn-%d.tsv' % (a.out, n), 'a')
    lg.write('# n=%d layout=%s side=%.12f bar=%.12f tilted=%d %s\n' % (
        n, os.path.basename(a.layout), L0, bar, int(ms.tilted(P).sum()), time.strftime('%H:%M:%S', time.gmtime())))
    low = math.inf
    for mode in a.modes.split(','):
        for deg in (float(x) for x in a.turns.split(',')):
            for lo in a.loosen.split(','):
                s, X = ms.to_fq(turned(P, mode, deg)); tq = time.time()
                s2, X2 = ms.quench(a.fq, tmp, s, X, ['--loosen', lo])
                if s2 is None or not math.isfinite(s2):
                    lg.write('%s\t%+.3f\t%s\tnan\t\t%.1f\n' % (mode, deg, lo, time.time() - tq)); continue
                tag = '%s-%+.3f-%s' % (mode, deg, lo)
                if s2 < best - max(1e-9, math.sqrt(n) * 1e-10):
                    # Keep the first win if the following deep quench times out.
                    ms.write_raw(a.out, n, ms.from_fq(X2), 'turn-' + tag)
                    s3, X3 = ms.quench(a.fq, tmp, s2, X2, ms.POLISH)
                    if s3 is not None and s3 < s2:
                        s2, X2 = s3, X3
                    best = s2; ms.write_raw(a.out, n, ms.from_fq(X2), 'turn-' + tag)
                if a.keep:
                    os.makedirs(a.out + '/turn', exist_ok=True)
                    ms.write_raw(a.out + '/turn', n, ms.from_fq(X2), tag)
                    os.rename('%s/turn/raw/%d-%s.csv' % (a.out, n, tag), '%s/turn/%d-%s.csv' % (a.out, n, tag))
                low = min(low, s2)
                lg.write('%s\t%+.3f\t%s\t%.12f\t%+.3e\t%.1f\n' % (mode, deg, lo, s2, s2 - bar, time.time() - tq)); lg.flush()
    lg.write('# END n=%d lowest %.12f bar %.12f lowest-bar %+.3e\n' % (n, low, bar, low - bar)); lg.close()
    print('n=%d lowest %.12f bar %.12f lowest-bar %+.3e' % (n, low, bar, low - bar), flush=True)


if __name__ == '__main__':
    main()
