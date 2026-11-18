#!/usr/bin/env python3
"""rigidsoft_chain: one chain of the block moves one square along its length, then a quench.

A chain is a line of tilted squares that touch face to face. The square at one end of the line goes to the free
place one step past the other end. The upright nearest to that place goes to the place the square left, on the
wall lattice of the nearest corner. So the block keeps its count of tilted squares and the chain sits one square
further along. Every line of the block is tried, along the chains and across them, in both directions.

  rigidsoft_chain.py run JOBDIR FQ HELD_DETAILS.csv SUB.csv N [--steps 1] [--top 6] [--df 0.002] [--sets alm0]
                     [--keep 0.01] [--tols 0.1,0.15,0.2,0.25,0.3]
        --tols adds, for each move, the starts with the four staircases built again around the new block by
        rigidsoft_step.staircases at each tolerance, when the count is N (tag ..._tTOL).
        step 1 runs every move on the layout of N in SUB.csv. With --steps 2, step 2 runs every move on the --top
        lowest results of step 1 in which the block changed (a tilted square stands more than 0.5 from every
        tilted square of the start). A result under the held side + KEEP is written to JOBDIR/raw/.
        appends JOBDIR/chain-N.tsv: n, step, tag, start side, side, held side, held minus side, block changed,
        count of tilted squares, quench log.
  The run stops at the unix time in JOBDIR/deadline.

Control (rigidsoft.md section 13), red: the held 261 (16.678779876) from the kinked 261 with one more tilted square
(16.682926829), in two steps. No start ends under the kinked side. A weaker control is green: on the held 261 the step
cu1l ends at 16.680751090 with a changed block, and from there the reverse step cu1h ends at the held side.
"""
import csv, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rigidsoft as RS  # noqa: E402
import rigidsoft_step as ST  # noqa: E402


def home(s, X, ups, hole):
    """the free cell of the wall lattice nearest to HOLE: each coordinate counts from its nearest wall"""
    def lat(c):
        if c < s / 2:
            return [math.floor(c - 0.5) + 0.5, math.ceil(c - 0.5) + 0.5]
        return [s - (math.floor(s - c - 0.5) + 0.5), s - (math.ceil(s - c - 0.5) + 0.5)]
    best = None
    for x in lat(hole[0]):
        for y in lat(hole[1]):
            if min(x, y) < 0.5 - 1e-6 or max(x, y) > s - 0.5 + 1e-6:
                continue
            if len(ups) and (np.maximum(np.abs(X[ups, 0] - x), np.abs(X[ups, 1] - y)) < 0.98).any():
                continue
            d = (x - hole[0]) ** 2 + (y - hole[1]) ** 2
            if best is None or d < best[0]:
                best = (d, x, y)
    return (best[1], best[2]) if best else (float(hole[0]), float(hole[1]))


def chains(s, X):
    """every move of one line of tilted squares by one square: (tag, layout)"""
    til = np.abs(X[:, 2]) >= 3
    ti = np.where(til)[0]; T = X[ti]
    deg = float(np.median(T[:, 2] % 90)); th = math.radians(deg)
    u = np.array([math.cos(th), math.sin(th)]); v = np.array([-u[1], u[0]])
    hw = (abs(u[0]) + abs(u[1])) / 2
    ups = np.where(~til)[0]
    for ax, (a, b) in enumerate(((u, v), (v, u))):
        ca = T[:, :2] @ a; cb = T[:, :2] @ b
        order = list(np.argsort(cb)); groups = [[order[0]]]
        for i in order[1:]:
            if cb[i] - cb[groups[-1][-1]] < 0.3:
                groups[-1].append(i)
            else:
                groups.append([i])
        li = 0
        for g in groups:
            g = sorted(g, key=lambda i: ca[i])
            runs = [[g[0]]]
            for i in g[1:]:
                if ca[i] - ca[runs[-1][-1]] < 1.15:
                    runs[-1].append(i)
                else:
                    runs.append([i])
            for line in runs:
                li += 1
                if len(line) < 3:
                    continue
                for end in (0, 1):
                    tail, head, nxt = (line[0], line[-1], line[-2]) if end else (line[-1], line[0], line[1])
                    p = 2 * T[head, :2] - T[nxt, :2]
                    if min(p[0], p[1]) - hw < -0.02 or max(p[0], p[1]) + hw > s + 0.02:
                        continue
                    D = T[:, :2] - p
                    if (np.maximum(np.abs(D @ u), np.abs(D @ v)) < 0.9).any():
                        continue
                    q = ups[np.argmin(((X[ups, :2] - p) ** 2).sum(axis=1))]
                    hole = X[ti[tail], :2].copy()
                    Y = X.copy()
                    Y[ti[tail]] = (p[0], p[1], T[head, 2])
                    hx, hy = home(s, X, ups[ups != q], hole)
                    Y[q] = (hx, hy, 0.0)
                    yield 'c%s%d%s' % ('uv'[ax], li, 'hl'[end]), Y


def changed(X0, X1):
    """True when a tilted square of X1 stands more than 0.5 from every tilted square of X0"""
    A = X0[np.abs(X0[:, 2]) >= 3, :2]; B = X1[np.abs(X1[:, 2]) >= 3, :2]
    if not len(A) or not len(B):
        return True
    d = np.sqrt(((B[:, None, :] - A[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
    return bool(d.max() > 0.5)


def cmd_run(a):
    jd, fqbin, held_csv, sub, n = a[0], a[1], a[2], a[3], int(a[4])
    opt = {'--steps': '1', '--top': '6', '--df': '0.002', '--sets': 'alm0', '--keep': '0.01', '--tols': ''}
    i = 5
    while i < len(a):
        opt[a[i]] = a[i + 1]; i += 2
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(held_csv))}[n]
    os.makedirs(jd + '/raw', exist_ok=True); os.makedirs(jd + '/tmp', exist_ok=True)
    s0, X0 = RS.normalize(RS.load(sub, {n})[n])
    res = '%s/chain-%d.tsv' % (jd, n)
    starts = [('', s0, X0)]; best = None; nq = 0
    for step in range(1, int(opt['--steps']) + 1):
        out = []
        for pre, s, X in starts:
            var = []; near = {}
            for tag0, Y in chains(s, X):
                var.append((tag0, Y))
                # the same move with the four staircases built again around the new block (rigidsoft_step.staircases)
                Tn = Y[np.abs(Y[:, 2]) >= 3]; seen = set()
                for tol in [float(v) for v in opt['--tols'].split(',') if v]:
                    rows, P = ST.staircases(s, Tn, tol)
                    c = len(Tn) + len(P) - n; near[c] = near.get(c, 0) + 1
                    sig = tuple(tuple(rows[k]) for k in ('BL', 'BR', 'TL', 'TR'))
                    if c or sig in seen:
                        continue
                    seen.add(sig)
                    var.append(('%s_t%g' % (tag0, tol), np.vstack([Tn, np.column_stack([P, np.zeros(len(P))])])))
            if opt['--tols']:
                print('BUILT n=%d step %d start %s%.9f moves %d count minus n %s' % (n, step, pre, s, len(var), ' '.join(
                    '%+d:%d' % kv for kv in sorted(near.items()) if abs(kv[0]) <= 3)), flush=True)
            for tag, Y in var:
                if time.time() > float(open(jd + '/deadline').read()):
                    break
                got = None; log = []
                for fs in opt['--sets'].split(','):
                    for df in [float(v) for v in opt['--df'].split(',')]:
                        s1, X1, dt = RS.fq(fqbin, jd + '/tmp', s + df, Y, RS.FLAGSETS[fs], timeout=120)
                        log.append('%s:%s:%.0fs' % (fs, 'None' if s1 is None else '%.9f' % s1, dt))
                        if s1 is not None and (got is None or s1 < got[0]):
                            got = (s1, X1)
                nq += 1
                tag = pre + tag
                if got is None:
                    with open(res, 'a') as h:
                        h.write('%d\t%d\t%s\t%.9f\tnan\t%.9f\tnan\t0\t0\t%s\n' % (n, step, tag, s, held, ' '.join(log)))
                    continue
                sb, Xb = got
                # fq gives an upright at any multiple of 90 degrees: bring every angle into (-45, 45], box at the origin
                Xb = RS.normalize(np.column_stack([Xb[:, :2], np.radians(Xb[:, 2])]))[1]
                ch = changed(X, Xb); nt = int((np.abs(Xb[:, 2]) >= 3).sum())
                with open(res, 'a') as h:
                    h.write('%d\t%d\t%s\t%.9f\t%.9f\t%.9f\t%.3e\t%d\t%d\t%s\n' % (n, step, tag, s, sb, held, held - sb, ch, nt, ' '.join(log)))
                if ch:
                    out.append((sb, tag + '.', Xb))
                if best is None or sb < best:
                    best = sb
                    print('BEST n=%d step %d %s side %.9f held %.9f below %.3e changed %d' % (n, step, tag, sb, held, held - sb, ch), flush=True)
                if sb < held + float(opt['--keep']):
                    tmpf = '%s/raw/.%d-%s.tmp' % (jd, n, tag)
                    with open(tmpf, 'w', newline='') as h:
                        wr = csv.writer(h); wr.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                        for qq, (xx, yy, d) in enumerate(Xb):
                            wr.writerow([n, qq, repr(float(xx)), repr(float(yy)), repr(math.radians(float(d)))])
                    os.rename(tmpf, '%s/raw/%d-%s.csv' % (jd, n, tag))
        out.sort(key=lambda r: r[0])
        starts = [(t, sb, Xb) for sb, t, Xb in out[:int(opt['--top'])]]
        print('STEP n=%d step %d quenches %d changed %d best %s held %.9f' % (
            n, step, nq, len(out), 'None' if best is None else '%.9f' % best, held), flush=True)
    print('CHAINEND n=%d quenches %d best %s held %.9f' % (n, nq, 'None' if best is None else '%.9f' % best, held), flush=True)


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] != 'run':
        sys.exit(__doc__)
    cmd_run(sys.argv[2:])
