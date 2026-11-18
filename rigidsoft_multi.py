#!/usr/bin/env python3
"""rigidsoft_multi: two fault moves at once on a soft block (rigidsoft.md, Round 20).

The fault move (rigidsoft_band.py fault) moves one band of rows one diagonal track, and every pinch in that band
changes its sense. A layout that keeps a change of sense needs a second band. When that band crosses the rows of
the first one, its start overlaps. This tool takes two bands A and B on the same layout, B after A along the block:
  - with at least one row between them (rows K2A and K1B - 1 differ), on any sides;
  - or sharing one row (K1B - 1 = K2A), on opposite sides. That row then takes one more tilted square at each end,
    its two teeth become those squares, and its pinch goes away. Its two shifts of SHIFT7 cancel.
A is applied first, then B on the result (rigidsoft_band.fault with extra=True for the shared row). The pinches
after both come from the reader of round 20, which reads the teeth that face a moved band.

  rigidsoft_multi.py list SUB.csv N [--maxch 0] [--fit 0.5] [--maxov 3]
        every pair that leaves at most MAXCH changes of sense, with the fit of its four leftover teeth (the largest
        distance from the middle of a row), the summed overlap of the start and the pinches. No quench.
  rigidsoft_multi.py run JOBDIR WORKER NWORKERS FQ HELD_DETAILS.csv SUB.csv N [--maxch 0] [--fit 0.5] [--maxov 3]
                     [--top 60] [--df 0,0.003] [--sets alm0] [--only TL6:12+BR13:16,..]
        the TOP pairs of that list, lowest overlap first, each quenched with fq (then one polish when it ends within
        5e-3 of the held side). appends JOBDIR/multi-N-WORKER.tsv; results below the held side (RIGIDSOFT_KEEP=X:
        up to X above it) go to JOBDIR/raw/N-<tag>.csv. The run stops at the unix time in JOBDIR/deadline.
"""
import csv, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rigidsoft as RS  # noqa: E402
import rigidsoft_band as BD  # noqa: E402

# the notches to fill may stand this far past the bound of rigidsoft_band.fault (RIGIDSOFT_SLACK, default 0.1)
SLACK = float(os.environ.get('RIGIDSOFT_SLACK', '0.1'))


def corners(x, y, d):
    t = math.radians(d); c, s = math.cos(t), math.sin(t)
    return np.array([[x + (a * c - b * s) * 0.5, y + (a * s + b * c) * 0.5] for a, b in ((1, 1), (-1, 1), (-1, -1), (1, -1))])


def sep(A, B):
    best = -9.0
    for P, Q in ((A, B), (B, A)):
        for i in range(4):
            e = P[(i + 1) % 4] - P[i]; nr = np.array([e[1], -e[0]]); nr /= np.linalg.norm(nr)
            best = max(best, float((Q @ nr).min() - (P @ nr).max()))
    return best


def overlap(s, Y, changed):
    """summed depth of the overlaps that touch a changed square (walls too)"""
    K = [corners(*r) for r in Y]; tot = 0.0
    for i in changed:
        k = K[i]
        w = min(k[:, 0].min(), k[:, 1].min(), s - k[:, 0].max(), s - k[:, 1].max())
        if w < -1e-4:
            tot -= w
        near = np.where((np.abs(Y[:, 0] - Y[i, 0]) < 1.5) & (np.abs(Y[:, 1] - Y[i, 1]) < 1.5))[0]
        for j in near:
            if j == i or (j in changed and j < i):
                continue
            g = sep(K[i], K[j])
            if g < -1e-4:
                tot -= g
    return tot


def fit_of(info):
    w = info.split()
    return max(abs(float(w[0][2:]) - 0.5), abs(float(w[1][2:]) - 0.5))


def pairs(s, X, maxch, fitmax, maxov):
    tt, idx, row, dev, a0, full = BD.teeth(s, X)
    nrow = int(row.max()) + 1
    singles = []
    for side in ('TL', 'BR'):
        for k1 in range(1, nrow):
            for k2 in range(k1 + 1, nrow):
                got = BD.fault(s, X, k1, k2, side, slack=SLACK)
                if got is not None and fit_of(got[1]) <= fitmax:
                    singles.append((side, k1, k2, got[0], got[1]))
    out = []
    for sa, a1, a2, Y1, ia in singles:
        for sb, b1, b2, _, _ in singles:
            if b1 - 1 < a2 or (b1 - 1 == a2 and sb == sa):
                continue
            got = BD.fault(s, Y1, b1, b2, sb, extra=(b1 - 1 == a2), slack=SLACK)
            if got is None:
                continue
            Y2, ib = got
            ch = int(ib.split()[-1])
            if ch > maxch or fit_of(ib) > fitmax:
                continue
            changed = np.where((np.abs(Y2 - X) > 1e-9).any(axis=1))[0]
            ov = overlap(s, Y2, set(int(c) for c in changed))
            if ov > maxov:
                continue
            tag = '%s%d:%d+%s%d:%d' % (sa, a1, a2, sb, b1, b2)
            out.append((ov, max(fit_of(ia), fit_of(ib)), ch, tag, Y2, ia, ib))
    out.sort(key=lambda o: (o[2], o[0]))
    return out


def opts(a, i, d):
    while i < len(a):
        d[a[i]] = a[i + 1]; i += 2
    return d


def cmd_list(a):
    sub, n = a[0], int(a[1])
    o = opts(a, 2, {'--maxch': '0', '--fit': '0.5', '--maxov': '3'})
    s, X = RS.normalize(RS.load(sub, {n})[n])
    for ov, ft, ch, tag, Y, ia, ib in pairs(s, X, int(o['--maxch']), float(o['--fit']), float(o['--maxov'])):
        print('%d\t%s\tchanges %d\tfit %.2f\toverlap %.3f\t%s | %s' % (n, tag, ch, ft, ov, ia, ib), flush=True)


def cmd_run(a):
    jd, w, nw, fqbin, held_csv, sub, n = a[0], int(a[1]), int(a[2]), a[3], a[4], a[5], int(a[6])
    o = opts(a, 7, {'--maxch': '0', '--fit': '0.5', '--maxov': '3', '--top': '60', '--df': '0,0.003', '--sets': 'alm0',
                    '--only': ''})
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(held_csv))}
    os.makedirs(jd + '/raw', exist_ok=True); os.makedirs(jd + '/tmp', exist_ok=True)
    s, X = RS.normalize(RS.load(sub, {n})[n])
    lst = pairs(s, X, int(o['--maxch']), float(o['--fit']), float(o['--maxov']))
    if o['--only']:
        keep = o['--only'].split(',')
        lst = [p for p in lst if p[3] in keep]
    lst = lst[:int(o['--top'])]
    print('n=%d side %.9f pairs %d' % (n, s, len(lst)), flush=True)
    res = '%s/multi-%d-%d.tsv' % (jd, n, w); best = None; nq = 0
    for q, (ov, ft, ch, tag, Y, ia, ib) in enumerate(lst):
        if q % nw != w:
            continue
        if time.time() > float(open(jd + '/deadline').read()):
            break
        got = None; log = []
        for fs in o['--sets'].split(','):
            for df in [float(v) for v in o['--df'].split(',')]:
                s1, X1, dt = RS.fq(fqbin, jd + '/tmp', s + df, Y, RS.FLAGSETS[fs], timeout=180)
                log.append('%s+%g:%s:%.0fs' % (fs, df, 'None' if s1 is None else '%.9f' % s1, dt))
                if s1 is not None and (got is None or s1 < got[0]):
                    got = (s1, X1)
        if got is not None and got[0] < held[n] + 5e-3:
            s2, X2, dt = RS.fq(fqbin, jd + '/tmp', got[0], got[1], RS.FLAGSETS['pol'])
            if s2 is not None and s2 < got[0]:
                got = (s2, X2)
        nq += 1
        sb = got[0] if got else float('nan')
        with open(res, 'a') as h:
            h.write('%d\t%s\t%.9f\t%.9f\t%.3e\t%s\tch%d fit%.2f ov%.3f\t%s | %s\n' % (
                n, tag, held[n], sb, held[n] - sb, ' '.join(log), ch, ft, ov, ia, ib))
        if got is not None and (best is None or sb < best):
            best = sb
            print('BEST n=%d %s side %.9f held %.9f below %.3e' % (n, tag, sb, held[n], held[n] - sb), flush=True)
        if got is not None and sb < held[n] + float(os.environ.get('RIGIDSOFT_KEEP', '-1e-9')):
            ft2 = tag.replace(':', '-').replace('+', '_')
            tmpf = '%s/raw/.%d-%s.tmp' % (jd, n, ft2)
            with open(tmpf, 'w', newline='') as h:
                wr = csv.writer(h); wr.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for qq, (xx, yy, dd) in enumerate(got[1]):
                    wr.writerow([n, qq, repr(float(xx)), repr(float(yy)), repr(math.radians(float(dd)))])
            os.rename(tmpf, '%s/raw/%d-%s.csv' % (jd, n, ft2))
    print('MULTIEND n=%d quenches %d best %s held %.9f' % (n, nq, 'None' if best is None else '%.9f' % best, held[n]), flush=True)


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in ('list', 'run'):
        sys.exit(__doc__)
    {'list': cmd_list, 'run': cmd_run}[sys.argv[1]](sys.argv[2:])
