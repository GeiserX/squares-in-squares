#!/usr/bin/env python3
"""rigidsoft_step: place a stepped, doubly sheared block (the deep form of the held 261), build the four
staircases of uprights around it on their wall lattices, and quench.

The block is `rigidsoft_topo.stepblock`: A chains of B squares turned by eps, with sin(eps) = (sqrt(2)/2)/B, the
NSHIFT chains next to one long side one square further along, and one chain of B + 1 squares. The uprights are
not filled by a general filler. Each of the four staircases stands on the lattice of its own wall corner, and a
row runs from its wall to the block. A bottom left row exists only below the left tip of the block and a top
left row only above it, and the same holds on the right with the right tip. In one row, the staircase from the
right wall stops where the one from the left wall ends. A cell is taken when it clears every tilted square
shrunk by TOL on each side. The uniform block overlaps the cells of the held 261 by up to 0.2, so TOL has to be
that large, and the quench removes the overlap. Only a start with exactly N squares is quenched, and only once
per set of row counts.

  rigidsoft_step.py scan JOBDIR WORKER NWORKERS FQ HELD_DETAILS.csv N A B [--nshift 2] [--sign -1] [--df 0.001]
                    [--tols 0.1,0.15,0.2,0.25] [--grid 0.05] [--xr -0.5,0.5] [--yr -0.5,1.5] [--f F] [--maxq 60]
                    [--cuts 2:5,3:6] [--plain 0.5,1.0,1.4]
        the first square of the block is scanned over the grid around the place that centres the block in the box.
        --cuts gives blocks with J steps (rigidsoft_topo.stepsblock), all sets with the same J: the turn is then
        sin(eps) = J * (sqrt(2)/2)/B and the rule is f = (sqrt(2 B^2 - J^2) - B')/2.
        --f sets the fraction of the start side (default: the deep rule); the start side is M + F + DF.
        --plain E1,E2,.. scans the block with no step, turned by each angle in degrees (`turn_f` gives the side
        of each turn when B is odd; with --f every turn starts at that side).
        appends JOBDIR/step-N-AxB-WORKER.tsv; a side below the held one is written to JOBDIR/raw/.
  The run stops at the unix time in JOBDIR/deadline. RIGIDSOFT_KEEP=X also writes results up to X above the held side.

Control (rigidsoft.md section 7): `scan ... 261 8 13 --tols 0.2,0.25,0.3` ends at the held 16.678779876.
"""
import csv, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rigidsoft as RS  # noqa: E402
import rigidsoft_topo as TP  # noqa: E402

S2 = math.sqrt(2.0)


def clear(cx, cy, T, th, tol):
    """True when the unit upright at (cx, cy) clears every tilted square of T shrunk by tol on each side"""
    c, s = abs(math.cos(th)), abs(math.sin(th)); h = 0.5 - tol
    dx = T[:, 0] - cx; dy = T[:, 1] - cy
    near = (np.abs(dx) < 0.5 + h * (c + s)) & (np.abs(dy) < 0.5 + h * (c + s))
    if not near.any():
        return True
    dx = dx[near]; dy = dy[near]
    du = dx * math.cos(th) + dy * math.sin(th); dv = -dx * math.sin(th) + dy * math.cos(th)
    hit = (np.abs(du) < h + 0.5 * (c + s)) & (np.abs(dv) < h + 0.5 * (c + s))
    return not hit.any()


def staircases(s, T, tol):
    """row counts (BL, BR, TL, TR) and the centres of the uprights around the block T"""
    m = int(s); th = math.radians(T[0, 2])
    yl = T[np.argmin(T[:, 0]), 1]; yr = T[np.argmax(T[:, 0]), 1]
    rows = {'BL': [], 'BR': [], 'TL': [], 'TR': []}; P = []
    for reg in rows:
        for j in range(m):
            y = j + 0.5 if reg[0] == 'B' else s - j - 0.5
            ylim = yl if reg[1] == 'L' else yr
            if (reg[0] == 'B' and y + 0.5 > ylim + 1e-9) or (reg[0] == 'T' and y - 0.5 < ylim - 1e-9):
                break
            # a row runs from its wall to the block; the right staircase stops at the left one of the same row
            other = rows[reg[0] + 'L'][j] if reg[1] == 'R' and j < len(rows[reg[0] + 'L']) else 0
            c = 0
            for i in range(m):
                x = i + 0.5 if reg[1] == 'L' else s - i - 0.5
                if reg[1] == 'R' and x - 0.5 < other - 1e-9:
                    break
                if not clear(x, y, T, th, tol):
                    break
                P.append((x, y)); c += 1
            rows[reg].append(c)
    return rows, np.array(P, float)


def turn_f(b, B, eps):
    """side fraction of a chain of b squares turned by eps degrees, from a tooth of one end staircase to a tooth
    of the other end one diagonal track over. The two teeth are B + 2f along the diagonal and one half diagonal
    apart, and the chain touches them W apart across its width: 2b^2 + 2W^2 = (B + 2f)^2 + 1. W = sqrt(1/2) is
    the rigid block and W = 0 the deep form. None when B is even (the teeth then face each other) or when the
    turn is larger than the deep one."""
    if B % 2 == 0:
        return None
    lo, hi = 0.0, math.sqrt(0.5)
    def turn(w):
        f = (math.sqrt(2 * b * b + 2 * w * w - 1) - B) / 2
        return math.degrees(math.atan(1 / (B + 2 * f)) - math.atan(w / b)), f
    if abs(eps) > turn(0.0)[0] + 1e-9:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if turn(mid)[0] > abs(eps):
            lo = mid
        else:
            hi = mid
    return turn((lo + hi) / 2)[1]


def cmd_scan(a):
    jd, w, nw, fqbin, held_csv, n, x, y = a[0], int(a[1]), int(a[2]), a[3], a[4], int(a[5]), int(a[6]), int(a[7])
    opt = {'--nshift': '2', '--sign': '-1', '--df': '0.001', '--tols': '0.1,0.15,0.2,0.25', '--grid': '0.05', '--xr': '-0.5,0.5',
           '--yr': '-0.5,1.5', '--f': '', '--maxq': '60', '--cuts': '', '--plain': ''}
    i = 8
    while i < len(a):
        opt[a[i]] = a[i + 1]; i += 2
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(held_csv))}
    os.makedirs(jd + '/raw', exist_ok=True); os.makedirs(jd + '/tmp', exist_ok=True)
    m = math.isqrt(n)
    B = math.floor(y * S2) - 1
    cutsets = [tuple(int(v) for v in c.split(':')) for c in opt['--cuts'].split(',') if c] or \
              [(int(v),) for v in opt['--nshift'].split(',')]
    J = len(cutsets[0])
    fd = float(opt['--f']) if opt['--f'] else (math.sqrt(2 * y * y - J * J) - B) / 2
    while not opt['--f'] and fd >= 1:
        fd -= 0.5
    eps = float(opt['--sign']) * math.degrees(math.asin(J * math.sqrt(0.5) / y))
    variants = [(ns, eps, m + fd + float(opt['--df'])) for ns in cutsets]
    if opt['--plain']:
        # the block with no step, turned by each angle; the side comes from --f or from turn_f
        variants = []
        for e in [float(v) for v in opt['--plain'].split(',')]:
            fe = float(opt['--f']) if opt['--f'] else turn_f(y, B, e)
            if fe is not None:
                variants.append(((), float(opt['--sign']) * e, m + fe + float(opt['--df'])))
    kc = (y - 1) / 2.0 if opt['--plain'] else y / 2.0; jc = (x - 1) / 2.0
    g = float(opt['--grid'])
    x0, x1 = [float(v) for v in opt['--xr'].split(',')]; y0, y1 = [float(v) for v in opt['--yr'].split(',')]
    res = '%s/step-%d-%dx%d-%d.tsv' % (jd, n, x, y, w)
    seen = set(); nq = 0; q = 0; best = None; near = {}
    for ns, eps, s in variants:
        st = 1.0 / math.cos(math.radians(eps)) / S2
        base = (s / 2 - (kc - jc) * st, s / 2 - (kc + jc) * st)
        for dx in np.arange(x0, x1 + 1e-9, g):
            for dy in np.arange(y0, y1 + 1e-9, g):
                q += 1
                if q % nw != w:
                    continue
                if time.time() > float(open(jd + '/deadline').read()) or nq >= int(opt['--maxq']):
                    break
                T = np.array(TP.stepsblock(x, y, eps, (base[0] + dx, base[1] + dy), ns), float)
                hw = (abs(math.cos(math.radians(T[0, 2]))) + abs(math.sin(math.radians(T[0, 2])))) / 2
                if (T[:, :2] - hw).min() < 0 or (T[:, :2] + hw).max() > s:
                    continue
                for tol in [float(v) for v in opt['--tols'].split(',')]:
                    rows, P = staircases(s, T, tol)
                    c = len(T) + len(P)
                    near[c - n] = near.get(c - n, 0) + 1
                    sig = (ns, eps, tuple(tuple(rows[k]) for k in ('BL', 'BR', 'TL', 'TR')))
                    if c != n or sig in seen:
                        continue
                    seen.add(sig)
                    X = np.vstack([T, np.column_stack([P, np.zeros(len(P))])])
                    got = None; log = []
                    for fs in ('alm0', 'def'):
                        s1, X1, dt = RS.fq(fqbin, jd + '/tmp', s, X, RS.FLAGSETS[fs], timeout=180)
                        log.append('%s:%s:%.0fs' % (fs, 'None' if s1 is None else '%.9f' % s1, dt))
                        if s1 is not None and (got is None or s1 < got[0]):
                            got = (s1, X1)
                    nq += 1
                    sb = got[0] if got else float('nan')
                    tag = '%dx%d_s%s_%.2f_%.2f_t%g' % (x, y, '.'.join(str(v) for v in ns) if ns else 'e%g' % eps, dx, dy, tol)
                    with open(res, 'a') as h:
                        h.write('%d\t%s\t%.9f\t%.9f\t%.3e\t%s\t%s\n' % (n, tag, held[n], sb, held[n] - sb, ' '.join(log),
                                                                    ' '.join('%s=%s' % (k, ','.join(str(v) for v in rows[k])) for k in ('BL', 'BR', 'TL', 'TR'))))
                    if got is not None and (best is None or sb < best):
                        best = sb
                        print('BEST n=%d %s side %.9f held %.9f below %.3e' % (n, tag, sb, held[n], held[n] - sb), flush=True)
                    if got is not None and sb < held[n] + float(os.environ.get('RIGIDSOFT_KEEP', '-1e-9')):
                        tmpf = '%s/raw/.%d-%s.tmp' % (jd, n, tag)
                        with open(tmpf, 'w', newline='') as h:
                            wr = csv.writer(h); wr.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                            for qq, (xx, yy, d) in enumerate(got[1]):
                                wr.writerow([n, qq, repr(float(xx)), repr(float(yy)), repr(math.radians(float(d)))])
                        os.rename(tmpf, '%s/raw/%d-%s.csv' % (jd, n, tag))
    eps, s = variants[-1][1], variants[-1][2]
    print('STEPEND n=%d %dx%d eps %.4f start side %.9f placements %d quenches %d best %s held %.9f count minus n %s' % (
        n, x, y, eps, s, q, nq, 'None' if best is None else '%.9f' % best, held[n],
        ' '.join('%+d:%d' % (k, v) for k, v in sorted(near.items()) if abs(k) <= 3)), flush=True)


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] != 'scan':
        sys.exit(__doc__)
    cmd_scan(sys.argv[2:])
