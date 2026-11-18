#!/usr/bin/env python3
"""rigidsoft_return: turn every row of a soft block one way by one angle, build the four staircases again, quench
(rigidsoft.md, Round 20).

The flip (rigidsoft_hop.py --moves flip) keeps the uprights, so the teeth that pinch a row put its sense back. The
plain scan (rigidsoft_step.py scan --plain) builds the staircases fresh, but only around a pure A x B block, and the
held soft blocks hold rows with one more square (the 4-rows of 328 and 365, the 7-rows of 263 and 494). This tool
keeps the sites of the block as they are, extra squares included, puts them on the lattice of a block turned by EPS
in one sense, places it at the old centre plus a shift, builds the four staircases on their wall lattices
(rigidsoft_step.staircases, cells clear of the block shrunk by TOL), and quenches every new set of row counts that
has exactly N squares. Tilted squares outside the block stay where they are.

  rigidsoft_return.py run JOBDIR FQ BAR.csv FILE.csv N [--eps 2.78] [--sign 1,-1] [--s0 SIDE] [--df 0.001,0.004]
                      [--tols 0.1,0.15,0.2,0.25] [--grid 0.1] [--range 0.3] [--mode int,real] [--maxq 400] [--over 0]
        --eps: the turns to try (degrees); --s0: the start side less DF (default M + turn_f of the rows)
        --mode int puts every square on the integer site nearest to it; real keeps the offsets of the old layout
        --over K also takes starts with up to K squares too many, less the uprights nearest to a tilted square
  rigidsoft_return.py dry FILE.csv N [same options]: counts only, no quench

Out JOBDIR/ret-N-0.tsv (one line per quench) and JOBDIR/raw/ (results under the bar side, or up to RIGIDSOFT_KEEP
above it). The run stops at the unix time in JOBDIR/deadline.
Control: the midm 263 (every row at 2.59 deg) with --eps 2.59 must end at its own side, 16.724372710.
"""
import csv, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rigidsoft as RS  # noqa: E402
import rigidsoft_band as BD  # noqa: E402
import rigidsoft_step as ST  # noqa: E402

S2 = math.sqrt(2.0)


def sites(s, X):
    """the layout turned so that the block runs along (1, 1), the block's squares as lattice sites (k along the
    block, j across it, real numbers) and the other tilted squares (rows x, y, degrees in that frame)"""
    idx, row, dev = BD.main_block(X)
    T = X[idx]
    P = T[:, :2] - T[:, :2].mean(axis=0)
    w, V = np.linalg.eigh(P.T @ P)
    mirror = not (V[0, -1] * V[1, -1] > 0)
    Y = X.copy()
    if mirror:                       # the block runs along (1, -1): mirror y so that it runs along (1, 1)
        Y[:, 1] = s - Y[:, 1]; Y[:, 2] = -Y[:, 2]
    T = Y[idx]
    al = (T[:, 0] + T[:, 1]) / S2; p = (T[:, 1] - T[:, 0]) / S2
    k = al - al.min(); j = p - p.min()
    # the integer grid that fits the sites best (circular mean of the fractional parts)
    ok = math.atan2(np.sin(2 * np.pi * k).mean(), np.cos(2 * np.pi * k).mean()) / (2 * np.pi)
    oj = math.atan2(np.sin(2 * np.pi * j).mean(), np.cos(2 * np.pi * j).mean()) / (2 * np.pi)
    k = k - ok; j = j - oj
    til = np.where(np.abs(Y[:, 2]) >= 3)[0]
    loose = np.array([i for i in til if i not in set(idx.tolist())], int)
    return Y, idx, k, j, loose, mirror, int(np.median(np.bincount(row)))


def build(k, j, eps, c):
    """centres on the lattice of a block turned by eps (step sec(eps) along both diagonals), every square at 45 - eps;
    c is the centre of the block"""
    st = 1.0 / math.cos(math.radians(eps)) / S2
    x = (k - j) * st; y = (k + j) * st
    x = x - x.mean() + c[0]; y = y - y.mean() + c[1]
    return np.column_stack([x, y, np.full(len(k), 45.0 - eps)])


def opts(a, i):
    o = {'--eps': '2.78', '--sign': '1,-1', '--s0': '', '--df': '0.001,0.004', '--tols': '0.1,0.15,0.2,0.25',
         '--grid': '0.1', '--range': '0.3', '--mode': 'int,real', '--maxq': '400', '--over': '0'}
    while i < len(a):
        o[a[i]] = a[i + 1]; i += 2
    return o


def starts(s, X, n, o):
    """every start with exactly n squares, once per (mode, eps, side, row counts)"""
    Y, idx, k, j, loose, mirror, b = sites(s, X)
    m = math.isqrt(n); B = math.floor(b * S2) - 1
    c0 = Y[idx, :2].mean(axis=0)
    g = float(o['--grid']); R = float(o['--range'])
    shifts = [(dx, dy) for dx in np.arange(-R, R + 1e-9, g) for dy in np.arange(-R, R + 1e-9, g)]
    shifts.sort(key=lambda t: t[0] ** 2 + t[1] ** 2)
    seen = set(); count = {}
    for mode in o['--mode'].split(','):
        kk, jj = (np.round(k), np.round(j)) if mode == 'int' else (k, j)
        if mode == 'int' and len(set(zip(kk.tolist(), jj.tolist()))) < len(kk):
            print('SKIP int: two squares on one site', flush=True)
            continue
        for e in [float(v) for v in o['--eps'].split(',')]:
            for sg in [float(v) for v in o['--sign'].split(',')]:
                eps = sg * e
                if o['--s0']:
                    sides = [float(o['--s0']) + float(d) for d in o['--df'].split(',')]
                else:
                    fe = ST.turn_f(b, B, e)
                    if fe is None:
                        continue
                    sides = [m + fe + float(d) for d in o['--df'].split(',')]
                for s1 in sides:
                    for dx, dy in shifts:
                        T = build(kk, jj, eps, (c0[0] + dx, c0[1] + dy))
                        hw = (abs(math.cos(math.radians(T[0, 2]))) + abs(math.sin(math.radians(T[0, 2])))) / 2
                        if (T[:, :2] - hw).min() < 0 or (T[:, :2] + hw).max() > s1:
                            count['out'] = count.get('out', 0) + 1
                            continue
                        Tall = np.vstack([T, Y[loose]]) if len(loose) else T
                        for tol in [float(v) for v in o['--tols'].split(',')]:
                            rows, P = ST.staircases(s1, Tall, tol)
                            cn = len(Tall) + len(P)
                            count[cn - n] = count.get(cn - n, 0) + 1
                            sig = (mode, eps, round(s1, 6), tuple(tuple(rows[q]) for q in ('BL', 'BR', 'TL', 'TR')))
                            if not (n <= cn <= n + int(o['--over'])) or sig in seen:
                                continue
                            seen.add(sig)
                            if cn > n:      # one or two uprights too many: take out the ones nearest to a tilted square
                                d = np.min(np.hypot(P[:, None, 0] - Tall[None, :, 0], P[:, None, 1] - Tall[None, :, 1]), axis=1)
                                P = np.delete(P, np.argsort(d)[:cn - n], axis=0)
                            Xs = np.vstack([Tall, np.column_stack([P, np.zeros(len(P))])])
                            tag = '%s_e%g_s%.4f_%.2f_%.2f_t%g_o%d' % (mode, eps, s1, dx, dy, tol, cn - n)
                            yield tag, s1, Xs, rows
    print('COUNT', ' '.join('%s:%d' % (q, v) for q, v in sorted(count.items(), key=str)), flush=True)


def cmd_dry(a):
    f, n = a[0], int(a[1]); o = opts(a, 2)
    s, X = RS.normalize(RS.load(f, {n})[n])
    Y, idx, k, j, loose, mirror, b = sites(s, X)
    print('n=%d side %.9f block %d loose %d mirror %s rows-width %d k-err %.3f j-err %.3f' % (
        n, s, len(idx), len(loose), mirror, b, np.abs(k - np.round(k)).max(), np.abs(j - np.round(j)).max()))
    q = 0
    for tag, s1, Xs, rows in starts(s, X, n, o):
        q += 1
        if q <= 12:
            print('START', tag, ' '.join('%s=%s' % (r, ','.join(map(str, rows[r]))) for r in ('BL', 'BR', 'TL', 'TR')))
    print('STARTS', q)


def cmd_run(a):
    jd, fqbin, bar_csv, f, n = a[0], a[1], a[2], a[3], int(a[4]); o = opts(a, 5)
    bar = {int(r['n']): float(r['L']) for r in csv.DictReader(open(bar_csv))}
    os.makedirs(jd + '/raw', exist_ok=True); os.makedirs(jd + '/tmp', exist_ok=True)
    s, X = RS.normalize(RS.load(f, {n})[n])
    res = '%s/ret-%d-0.tsv' % (jd, n); best = None; nq = 0
    keep = float(os.environ.get('RIGIDSOFT_KEEP', '-1e-9'))
    print('n=%d side %.9f bar %.9f' % (n, s, bar[n]), flush=True)
    for tag, s1, Xs, rows in starts(s, X, n, o):
        if time.time() > float(open(jd + '/deadline').read()) or nq >= int(o['--maxq']):
            break
        got = None; log = []
        for fs in ('alm0', 'def'):
            s2, X2, dt = RS.fq(fqbin, jd + '/tmp', s1, Xs, RS.FLAGSETS[fs], timeout=300)
            log.append('%s:%s:%.0fs' % (fs, 'None' if s2 is None else '%.9f' % s2, dt))
            if s2 is not None and (got is None or s2 < got[0]):
                got = (s2, X2)
        if got is not None and got[0] < bar[n] + 3e-3:
            for rnd in range(3):
                s3, X3, dt = RS.fq(fqbin, jd + '/tmp', got[0], got[1], RS.FLAGSETS['pol'], timeout=300)
                log.append('pol:%s:%.0fs' % ('None' if s3 is None else '%.9f' % s3, dt))
                if s3 is None or not (s3 < got[0] - 3e-9):
                    break
                got = (s3, X3)
        nq += 1
        sb = got[0] if got else float('nan')
        with open(res, 'a') as h:
            h.write('%d\t%s\t%.9f\t%.9f\t%.3e\t%s\t%s\n' % (n, tag, bar[n], sb, bar[n] - sb, ' '.join(log),
                    ' '.join('%s=%s' % (r, ','.join(map(str, rows[r]))) for r in ('BL', 'BR', 'TL', 'TR'))))
        if got is not None and (best is None or sb < best):
            best = sb
            print('BEST n=%d %s side %.9f bar %.9f below %.3e' % (n, tag, sb, bar[n], bar[n] - sb), flush=True)
        if got is not None and sb < bar[n] + keep:
            tmpf = '%s/raw/.%d-%s.tmp' % (jd, n, tag)
            with open(tmpf, 'w', newline='') as h:
                wr = csv.writer(h); wr.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for qq, (xx, yy, d) in enumerate(got[1]):
                    wr.writerow([n, qq, repr(float(xx)), repr(float(yy)), repr(math.radians(float(d)))])
            os.rename(tmpf, '%s/raw/%d-%s.csv' % (jd, n, tag))
    print('RETEND n=%d quenches %d best %s bar %.9f' % (n, nq, 'None' if best is None else '%.9f' % best, bar[n]), flush=True)


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in ('run', 'dry'):
        sys.exit(__doc__)
    {'run': cmd_run, 'dry': cmd_dry}[sys.argv[1]](sys.argv[2:])
