#!/usr/bin/env python3
"""rigidsoft_band: moves on a soft block, a block of tilted squares whose rows are turned both ways in bands
(rigidsoft.md section 11 and Round 19).

  rigidsoft_band.py fault JOBDIR WORKER NWORKERS FQ HELD_DETAILS.csv SUB.csv N [--side TL,BR] [--k all|6:12,..]
                    [--shift7 0.15] [--eps asis,0.26] [--df 0,0.003] [--sets alm0,def] [--dry 0]
                    [--fit 0.5] [--fit1 0.5] [--maxch 99]
        The fault move on the layout of N in SUB.csv. The block runs along the main diagonal (mirror the
        layout first when it does not). A band of rows K1..K2-1 moves one diagonal track (0.7071 across the
        block) toward one side staircase. Every tooth of that staircase that faces the band goes back one
        square, one square fills each notch between two teeth of the other staircase that face the band, and
        the two squares left over become one more tilted square of row K1-1 and of row K2. The count stays N.
        --shift7: how far those two rows move away. --eps: turn of every row in degrees, or as it is.
        --dry 1 lists the bands and the pinched rows they leave, with no quench.
        appends JOBDIR/fault-N-WORKER.tsv.
  rigidsoft_band.py end JOBDIR WORKER NWORKERS FQ HELD_DETAILS.csv SUB.csv N [--only asis,..] [--shift7 0.15]
                    [--tols 0.1,0.15,0.2,0.25,0.3] [--df 0,0.003] [--sets alm0] [--dry 0]
        A band that runs from row K to one end of the block moves one track, with or without a new tilted
        square beside it. The staircases are built again (rigidsoft_step.staircases) and a start with exactly
        N squares is quenched. appends JOBDIR/end-N-WORKER.tsv.
  rigidsoft_band.py scan JOBDIR WORKER NWORKERS FQ HELD_DETAILS.csv N A B [--drop 2] [--eps 0] [--f F]
                    [--df 0.001] [--tols 0.05,0.1,0.15] [--grid 0.05] [--xr -0.4,0.4] [--yr -0.4,0.4]
                    [--maxq 400] [--sets alm0,def] [--ends 1] [--loose 1]
        A fresh block: A chains of B squares along the diagonal from the bottom left corner, every square at
        45 - EPS degrees, at every place of a grid.
        --drop K: every set of up to K end sites is left out. An end site is a corner of the block; with
        --ends 2 also the square next to a corner in the end row, when that corner is out.
        --loose 1: after the staircases, every wall row gets one more upright where a unit cell slides in
        between its squares and clears the block.
        --f: side fraction of the start (default: the rigid threshold of the short extent A); start side M + F + DF.
        Only a start with exactly N squares is quenched, once per set of row counts, left-out sites and loose squares.
        appends JOBDIR/band-N-AxB-WORKER.tsv.
  rigidsoft_band.py room SUB.csv N
        the room of every chain of the block between the two end staircases, and what the chain takes
  A run stops at the unix time in JOBDIR/deadline. RIGIDSOFT_KEEP=X writes results up to X above the held side
  to JOBDIR/raw/ (default: only results below it).

Controls (rigidsoft.md, Round 19):
  fault: green. `fault ... 297 --side TL --k 6:12` on the held 297 ends at 17.739455512, the side the board holds.
  end:   green. `end ... 297 --only asis --sets alm0,def` ends at the held 17.740417288.
  scan:  red. `scan ... 297 6 18` ends at 17.741250448 on the row counts of the held 297 (17.740417288): the
         quench of a fresh block stops at a worse jam, so a scan that finds nothing is a weak negative.
"""
import csv, itertools, math, os, sys, time, zlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rigidsoft as RS  # noqa: E402
import rigidsoft_pin as PN  # noqa: E402
import rigidsoft_step as ST  # noqa: E402
import rigidsoft_hop as HP  # noqa: E402

S2 = math.sqrt(2.0)


def end_sites(a, b, ends):
    """[(site, needs)]: the corners of the block, and with ENDS = 2 the next square of the end row (needs its corner)"""
    out = []
    for k in (0, b - 1):
        for j, jn in ((0, 1), (a - 1, a - 2)):
            out.append((k * a + j, None))
            if ends >= 2 and a > 2:
                out.append((k * a + jn, k * a + j))
    return out


def drop_sets(a, b, kmax, ends):
    S = end_sites(a, b, ends)
    for r in range(0, kmax + 1):
        for c in itertools.combinations(S, r):
            ids = {s for s, _ in c}
            if all(need is None or need in ids for _, need in c):
                yield tuple(sorted(ids))


def loose(s, T, th, P, tol):
    """one more upright in each wall row that has room: a unit cell that slides in between the squares of the row
    and clears the block. [(x, y)]"""
    out = []
    for name, k, w in (('B', 1, 0.5), ('T', 1, s - 0.5), ('L', 0, 0.5), ('R', 0, s - 0.5)):
        Q = np.vstack([P] + ([np.array(out)] if out else []))
        row = sorted(float(p[1 - k]) for p in Q if abs(p[k] - w) < 0.5)
        edge = [-0.5] + row + [s + 0.5]
        for lo, hi in zip(edge[:-1], edge[1:]):
            if hi - lo < 2.0 - 1e-9:
                continue
            for pos in np.arange(lo + 1.0, hi - 1.0 + 1e-9, 0.02):
                c = (w, pos) if k == 0 else (pos, w)
                if ST.clear(c[0], c[1], T, th, tol):
                    out.append(c); break
            else:
                continue
            break
    return out


def cmd_scan(a):
    jd, w, nw, fqbin, held_csv, n, x, y = a[0], int(a[1]), int(a[2]), a[3], a[4], int(a[5]), int(a[6]), int(a[7])
    opt = {'--drop': '2', '--eps': '0', '--f': '', '--df': '0.001', '--tols': '0.05,0.1,0.15', '--grid': '0.05',
           '--xr': '-0.4,0.4', '--yr': '-0.4,0.4', '--maxq': '400', '--sets': 'alm0,def', '--ends': '1', '--loose': '1'}
    i = 8
    while i < len(a):
        opt[a[i]] = a[i + 1]; i += 2
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(held_csv))}
    os.makedirs(jd + '/raw', exist_ok=True); os.makedirs(jd + '/tmp', exist_ok=True)
    m = math.isqrt(n)
    A = math.floor(x * S2) - 1                               # the rigid rule of the short extent
    fr = (x * S2 - A) / 2
    while fr >= 1:
        fr -= 0.5
    f0 = float(opt['--f']) if opt['--f'] else fr
    s = m + f0 + float(opt['--df'])
    g = float(opt['--grid'])
    x0, x1 = [float(v) for v in opt['--xr'].split(',')]; y0, y1 = [float(v) for v in opt['--yr'].split(',')]
    res = '%s/band-%d-%dx%d-%d.tsv' % (jd, n, x, y, w)
    seen = set(); nq = 0; q = 0; best = None; near = {}
    drops = list(drop_sets(x, y, int(opt['--drop']), int(opt['--ends'])))
    stop = False
    for eps in [float(v) for v in opt['--eps'].split(',')]:
        th = math.radians(45.0 - eps)
        hwt = (abs(math.cos(th)) + abs(math.sin(th))) / 2
        for dx in np.arange(x0, x1 + 1e-9, g):
            for dy in np.arange(y0, y1 + 1e-9, g):
                T0 = np.array(PN.pblock(x, y, eps, s / 2 + dx, s / 2 + dy), float)
                for dr in drops:
                    q += 1
                    if stop:
                        continue
                    if time.time() > float(open(jd + '/deadline').read()) or nq >= int(opt['--maxq']):
                        stop = True; continue
                    T = np.delete(T0, list(dr), axis=0)
                    if (T[:, :2] - hwt).min() < -1e-9 or (T[:, :2] + hwt).max() > s + 1e-9:
                        continue
                    for tol in [float(v) for v in opt['--tols'].split(',')]:
                        rows, P = ST.staircases(s, T, tol)
                        if len(P) == 0:
                            continue
                        d = np.abs(P[:, None, :] - P[None, :, :]).max(axis=2); np.fill_diagonal(d, 9.0)
                        if (d < 1 - 1e-9).any():
                            continue
                        Lo = loose(s, T, th, P, tol) if opt['--loose'] == '1' else []
                        for use in ([Lo, []] if Lo else [[]]):
                            c = len(T) + len(P) + len(use)
                            near[c - n] = near.get(c - n, 0) + 1
                            sig = (eps, dr, tuple(tuple(rows[k]) for k in ('BL', 'BR', 'TL', 'TR')),
                                   tuple((round(u[0], 1), round(u[1], 1)) for u in use))
                            if c != n or sig in seen:
                                continue
                            seen.add(sig)
                            if zlib.crc32(repr(sig).encode()) % nw != w:      # one worker per set
                                continue
                            U = np.vstack([P] + ([np.array(use)] if use else []))
                            X = np.vstack([T, np.column_stack([U, np.zeros(len(U))])])
                            got = None; log = []
                            for fs in opt['--sets'].split(','):
                                s1, X1, dt = RS.fq(fqbin, jd + '/tmp', s, X, RS.FLAGSETS[fs], timeout=180)
                                log.append('%s:%s:%.0fs' % (fs, 'None' if s1 is None else '%.9f' % s1, dt))
                                if s1 is not None and (got is None or s1 < got[0]):
                                    got = (s1, X1)
                            if got is not None and got[0] < held[n] + 3e-3:
                                s2, X2, dt = RS.fq(fqbin, jd + '/tmp', got[0], got[1], RS.FLAGSETS['pol'])
                                if s2 is not None and s2 < got[0]:
                                    got = (s2, X2)
                            nq += 1
                            sb = got[0] if got else float('nan')
                            tag = '%dx%d_e%g_%.2f_%.2f_t%g_d%s_l%d' % (x, y, eps, dx, dy, tol, '.'.join(str(v) for v in dr) or 'x', len(use))
                            with open(res, 'a') as h:
                                h.write('%d\t%s\t%.9f\t%.9f\t%.3e\t%s\t%s\n' % (
                                    n, tag, held[n], sb, held[n] - sb, ' '.join(log),
                                    ' '.join('%s=%s' % (k, ','.join(str(v) for v in rows[k])) for k in ('BL', 'BR', 'TL', 'TR'))))
                            if got is not None and (best is None or sb < best):
                                best = sb
                                print('BEST n=%d %s side %.9f held %.9f below %.3e' % (n, tag, sb, held[n], held[n] - sb), flush=True)
                            if got is not None and sb < held[n] + float(os.environ.get('RIGIDSOFT_KEEP', '-1e-9')):
                                tmpf = '%s/raw/.%d-%s.tmp' % (jd, n, tag)
                                with open(tmpf, 'w', newline='') as h:
                                    wr = csv.writer(h); wr.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                                    for qq, (xx, yy, dd) in enumerate(got[1]):
                                        wr.writerow([n, qq, repr(float(xx)), repr(float(yy)), repr(math.radians(float(dd)))])
                                os.rename(tmpf, '%s/raw/%d-%s.csv' % (jd, n, tag))
    print('BANDEND n=%d %dx%d start side %.9f placements %d quenches %d best %s held %.9f count minus n %s' % (
        n, x, y, s, q, nq, 'None' if best is None else '%.9f' % best, held[n],
        ' '.join('%+d:%d' % (k, v) for k, v in sorted(near.items()) if abs(k) <= 3)), flush=True)


def main_block(X):
    """rigidsoft_hop.block_rows on the largest group of tilted squares that touch (centres under 1.25 apart).
    A tilted square that stands alone elsewhere (the held 263 has one) is left out of the block."""
    til = np.where(np.abs(X[:, 2]) >= 3)[0]
    P = X[til, :2]; lab = -np.ones(len(til), int); g = 0
    for i in range(len(til)):
        if lab[i] >= 0:
            continue
        lab[i] = g; todo = [i]
        while todo:
            j = todo.pop()
            for k in np.where((lab < 0) & (np.hypot(P[:, 0] - P[j, 0], P[:, 1] - P[j, 1]) < 1.25))[0]:
                lab[k] = g; todo.append(k)
        g += 1
    big = int(np.argmax(np.bincount(lab)))
    if (lab == big).all():
        return HP.block_rows(X)
    Y = X.copy(); Y[til[lab != big], 2] = 0.0          # the squares outside the block count as not tilted here
    return HP.block_rows(Y)


_TEETH = {}


def teeth(s, X):
    """`read_teeth`, kept for the last layout: `fault` asks for the same layout once per band"""
    key = (float(s), X.tobytes())
    if key not in _TEETH:
        _TEETH.clear(); _TEETH[key] = read_teeth(s, X)
    return _TEETH[key]


def read_teeth(s, X):
    """the teeth of the two side staircases of a block that runs along the main diagonal: an upright with a free
    corner on the line of the row ends. {'TL': [(t, q)], 'BR': [(t, q)]}, t = row of the block plus the place
    of the tip along that row (0..1), q = index of the square. Also the rows and the two lines."""
    idx, row, dev = main_block(X); T = X[idx]
    al = (T[:, 0] + T[:, 1]) / S2; ac = (T[:, 0] - T[:, 1]) / S2
    nrow = int(row.max()) + 1
    a0 = np.array([al[row == r].mean() for r in range(nrow)])
    cnt = [int((row == r).sum()) for r in range(nrow)]
    full = int(np.median(cnt))
    # round 20: each row has its own end line, so the teeth that face a band moved by a fault are read too
    # (before, one line for the whole block left them out)
    ltl = {r: float(ac[row == r].min()) - 0.5 for r in range(nrow) if cnt[r] >= full}
    lbr = {r: float(ac[row == r].max()) + 0.5 for r in range(nrow) if cnt[r] >= full}
    ups = [q for q in range(len(X)) if abs(X[q, 2]) < 3]
    P = X[ups, :2]

    def has(x, y):
        return bool((np.abs(P - np.array([x, y])).max(axis=1) < 0.25).any())

    def pos(cx, cy):
        a = (cx + cy) / S2; r = int(np.argmin(np.abs(a0 - a)))
        return r + (a - a0[r] + 0.5), r

    def near(lines, r, v):
        d = [abs(v - lines[k]) for k in (r - 1, r, r + 1) if k in lines]
        return bool(d) and min(d) < 0.25

    out = {'TL': [], 'BR': []}
    for q in ups:
        x, y = float(X[q, 0]), float(X[q, 1])
        if not has(x + 1, y) and not has(x, y - 1):
            t, r = pos(x + 0.5, y - 0.5)
            if near(ltl, r, (x + 0.5 - (y - 0.5)) / S2):
                out['TL'].append((t, q))
        if not has(x - 1, y) and not has(x, y + 1):
            t, r = pos(x - 0.5, y + 0.5)
            if near(lbr, r, (x - 0.5 - (y + 0.5)) / S2):
                out['BR'].append((t, q))
    out['TL'].sort(); out['BR'].sort()
    return out, idx, row, dev, a0, full


def pinches(tt, nrow, band=None):
    """the pinched rows and their sense: a row with a tip of each side staircase; + when the top left tip comes
    first along the block. BAND (k1, k2, tl, br): the tips that the rows k1..k2-1 see after a fault."""
    tl = [t for t, _ in tt['TL']]; br = [t for t, _ in tt['BR']]
    if band:
        k1, k2, btl, bbr = band
        tl = [t for t in tl if not (k1 - 0.7071 < t < k2 + 0.7071)] + list(btl)
        br = [t for t in br if not (k1 - 0.7071 < t < k2 + 0.7071)] + list(bbr)
    out = {}
    for r in range(nrow):
        a = sorted(t for t in tl if r <= t < r + 1); b = sorted(t for t in br if r <= t < r + 1)
        if a and b:
            out[r] = 1 if a[0] < b[0] else -1
    return out


def fault(s, X, k1, k2, side, shift7=0.15, eps=None, extra=False, slack=0.0):
    """a band of rows k1..k2-1 of the block moves one diagonal track toward SIDE ('TL' or 'BR'). Every tooth of
    that side whose tip is within half a track of the band goes back one square. On the other side, a square
    fills every notch between two teeth that both face the band. Two squares are left over. They become a
    seventh tilted square of the row under the band and of the row over it, each in the notch of the tooth that
    faced that row, and each of those two rows moves SHIFT7 away from SIDE to make room. The count of squares
    stays. None when the teeth do not give exactly that. EPS: set every row to the sense that the new teeth give
    it, at EPS degrees (a row between two senses is set to 45 degrees)."""
    tt, idx, row, dev, a0, full = teeth(s, X)
    nrow = int(row.max()) + 1
    if not (1 <= k1 < k2 <= nrow - 1):
        return None
    other = 'BR' if side == 'TL' else 'TL'
    sg = -1.0 if side == 'TL' else 1.0                                  # across step toward SIDE, in (x - y)
    mine = [(t, q) for t, q in tt[side] if k1 - 0.7071 < t < k2 + 0.7071]
    lo = [(t, q) for t, q in mine if t < k1]; hi = [(t, q) for t, q in mine if t > k2]
    mid = [(t, q) for t, q in mine if k1 <= t <= k2]
    if side == 'TL':        # a new bottom right square stands left of a tooth: the notch under that tooth
        adv = [(t, q) for t, q in tt[other] if k1 + 1.4142 - slack <= t <= k2 + slack]
    else:                   # a new top left square stands right of a tooth: the notch over that tooth
        adv = [(t, q) for t, q in tt[other] if k1 - slack <= t <= k2 - 1.4142 + slack]
    if len(lo) != 1 or len(hi) != 1 or len(mid) != len(adv):
        return None
    # EXTRA (round 20): the row under or over the band may already hold one more square at its other end, from a
    # fault on the other side that shares that row (rigidsoft_multi.py). SLACK widens the range of the notches to
    # fill: a tip 0.01 past the bound (the held 494 has one at 19.60) left a band out.
    if not extra and (int((row == k1 - 1).sum()) != full or int((row == k2).sum()) != full):
        return None
    if extra and (int((row == k1 - 1).sum()) < full or int((row == k2).sum()) < full):
        return None
    Y = X.copy()
    band = idx[(row >= k1) & (row < k2)]
    Y[band, 0] += sg * 0.5; Y[band, 1] -= sg * 0.5
    for (tb, qb), (tm, qm) in zip(adv, mid):
        Y[qm] = (X[qb, 0] + sg * 1.0, X[qb, 1], 0.0)
    ac = (X[:, 0] - X[:, 1]) / S2
    for (t, q), r in ((lo[0], k1 - 1), (hi[0], k2)):
        m = idx[row == r]
        Y[m, 0] -= sg * shift7 / S2; Y[m, 1] += sg * shift7 / S2        # the row makes room, away from SIDE
        e = m[np.argmin(ac[m])] if side == 'TL' else m[np.argmax(ac[m])]
        Y[q] = (Y[e, 0] + sg / S2, Y[e, 1] - sg / S2, X[e, 2])
    rec = sorted(t for t, _ in mine)
    mids = [(u + v) / 2 for u, v in zip(rec[:-1], rec[1:])]
    fill = [t - 0.7071 if side == 'TL' else t + 0.7071 for t, _ in adv]
    pin = pinches(tt, nrow, (k1, k2, mids, fill) if side == 'TL' else (k1, k2, fill, mids))
    keys = sorted(pin)
    info = 'lo%.2f hi%.2f mid%d pin %s' % (lo[0][0] - (k1 - 1), hi[0][0] - k2, len(mid),
                                           ''.join('%d%s' % (k, '+' if pin[k] > 0 else '-') for k in keys))
    info += ' changes %d' % sum(1 for u, v in zip(keys[:-1], keys[1:]) if pin[u] != pin[v])
    if eps and keys:
        idx2, row2, dev2 = HP.block_rows(Y)
        for r in range(int(row2.max()) + 1):
            d = [abs(r - k) for k in keys]; j = int(np.argmin(d))
            near = [pin[k] for k, v in zip(keys, d) if v == min(d)]
            sense = float(near[0]) if len(set(near)) == 1 else 0.0
            dd = sense * eps
            Y[idx2[row2 == r], 2] = 45.0 + dd if dd <= 0 else dd - 45.0
    return Y, info


def cmd_fault(a):
    """rigidsoft_band.py fault JOBDIR WORKER NWORKERS FQ HELD_DETAILS.csv SUB.csv N [--side TL,BR] [--k all|6:12,..]
    [--shift7 0.15] [--eps asis,0.26] [--df 0,0.003] [--sets alm0,def] [--dry 0]
    [--fit 0.5] [--fit1 0.5] [--maxch 99] [--clean 0]
    --fit F keeps the bands whose two leftover teeth both stand within F of the middle of the row they face,
    --fit1 F those with at least one within F, --maxch C those that leave at most C changes of sense.
    --clean 1 (round 20) leaves out a band with a row of more squares than the others inside it: the fourth or
    seventh square of an earlier fault there collides with the staircase when the band moves.
    --reduce R (round 20) keeps the bands that leave at least R fewer changes of sense than the layout has: the two
    new tilted squares of a band cost room, and only a band that takes changes out pays for them."""
    jd, w, nw, fqbin, held_csv, sub, n = a[0], int(a[1]), int(a[2]), a[3], a[4], a[5], int(a[6])
    opt = {'--side': 'TL,BR', '--k': 'all', '--shift7': '0.15', '--eps': 'asis', '--df': '0,0.003', '--sets': 'alm0,def', '--dry': '0',
           '--fit': '0.5', '--fit1': '0.5', '--maxch': '99', '--clean': '0', '--reduce': '0'}
    i = 7
    while i < len(a):
        opt[a[i]] = a[i + 1]; i += 2
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(held_csv))}
    os.makedirs(jd + '/raw', exist_ok=True); os.makedirs(jd + '/tmp', exist_ok=True)
    s, X = RS.normalize(RS.load(sub, {n})[n])
    tt, idx, row, dev, a0, full = teeth(s, X)
    nrow = int(row.max()) + 1
    pin = pinches(tt, nrow)
    print('n=%d side %.9f rows %d of %d; TL tips %s; BR tips %s; pinched %s' % (
        n, s, nrow, full, ' '.join('%.2f' % t for t, _ in tt['TL']), ' '.join('%.2f' % t for t, _ in tt['BR']),
        ''.join('%d%s ' % (k, '+' if pin[k] > 0 else '-') for k in sorted(pin))), flush=True)
    kp = sorted(pin); ch0 = sum(1 for u, v in zip(kp[:-1], kp[1:]) if pin[u] != pin[v])
    ks = [(k1, k2) for k1 in range(1, nrow) for k2 in range(k1 + 1, nrow)] if opt['--k'] == 'all' else \
         [tuple(int(v) for v in t.split(':')) for t in opt['--k'].split(',')]
    res = '%s/fault-%d-%d.tsv' % (jd, n, w)
    nq = 0; best = None; q = 0
    for side in opt['--side'].split(','):
        for k1, k2 in ks:
            for sh in [float(v) for v in opt['--shift7'].split(',')]:
                for ep in opt['--eps'].split(','):
                    got0 = fault(s, X, k1, k2, side, sh, None if ep == 'asis' else float(ep))
                    if got0 is None:
                        continue
                    Y, info = got0
                    wd = info.split()
                    fl, fh = abs(float(wd[0][2:]) - 0.5), abs(float(wd[1][2:]) - 0.5)
                    if max(fl, fh) > float(opt['--fit']) or min(fl, fh) > float(opt['--fit1']) or int(wd[-1]) > int(opt['--maxch']):
                        continue
                    if opt['--clean'] == '1' and any(int((row == r).sum()) > full for r in range(k1, k2)):
                        continue
                    if int(wd[-1]) > ch0 - int(opt['--reduce']):
                        continue
                    q += 1
                    tag = '%s%d:%d_s%g_e%s' % (side, k1, k2, sh, ep)
                    if opt['--dry'] == '1':
                        print('DRY', tag, info); continue
                    if q % nw != w:
                        continue
                    if time.time() > float(open(jd + '/deadline').read()):
                        break
                    got = None; log = []
                    for fs in opt['--sets'].split(','):
                        for df in [float(v) for v in opt['--df'].split(',')]:
                            s1, X1, dt = RS.fq(fqbin, jd + '/tmp', s + df, Y, RS.FLAGSETS[fs], timeout=120)
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
                        h.write('%d\t%s\t%.9f\t%.9f\t%.3e\t%s\t%s\n' % (n, tag, held[n], sb, held[n] - sb, ' '.join(log), info))
                    if got is not None and (best is None or sb < best):
                        best = sb
                        print('BEST n=%d %s side %.9f held %.9f below %.3e' % (n, tag, sb, held[n], held[n] - sb), flush=True)
                    if got is not None and sb < held[n] + float(os.environ.get('RIGIDSOFT_KEEP', '-1e-9')):
                        tmpf = '%s/raw/.%d-%s.tmp' % (jd, n, tag.replace(':', '-'))
                        with open(tmpf, 'w', newline='') as h:
                            wr = csv.writer(h); wr.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                            for qq, (xx, yy, dd) in enumerate(got[1]):
                                wr.writerow([n, qq, repr(float(xx)), repr(float(yy)), repr(math.radians(float(dd)))])
                        os.rename(tmpf, '%s/raw/%d-%s.csv' % (jd, n, tag.replace(':', '-')))
    print('FAULTEND n=%d moves %d quenches %d best %s held %.9f' % (n, q, nq, 'None' if best is None else '%.9f' % best, held[n]), flush=True)


def end_starts(s, X, shift7=0.15):
    """the tilted squares of every start of the `end` move: a band that runs from row k to one end of the block moves
    one diagonal track to one side, with or without a new tilted square at the open end of the row next to it.
    Also ('asis', the tilted squares as they are), the control. [(tag, T)]"""
    tt, idx, row, dev, a0, full = teeth(s, X)
    nrow = int(row.max()) + 1; T0 = X[idx]
    ac = (T0[:, 0] - T0[:, 1]) / S2
    out = [('asis', T0.copy())]
    for side in ('TL', 'BR'):
        sg = -1.0 if side == 'TL' else 1.0
        for k in range(1, nrow):
            for end in ('hi', 'lo'):
                band = (row >= k) if end == 'hi' else (row < k)
                r7 = k - 1 if end == 'hi' else k
                for seven in (1, 0):
                    T = T0.copy()
                    T[band, 0] += sg * 0.5; T[band, 1] -= sg * 0.5
                    if seven:
                        m = np.where(row == r7)[0]
                        if len(m) != full:
                            continue
                        T[m, 0] -= sg * shift7 / S2; T[m, 1] += sg * shift7 / S2
                        e = m[np.argmin(ac[m])] if side == 'TL' else m[np.argmax(ac[m])]
                        T = np.vstack([T, [T[e, 0] + sg / S2, T[e, 1] - sg / S2, T[e, 2]]])
                    out.append(('%s%d%s_7%d' % (side, k, end, seven), T))
    return out


def cmd_end(a):
    """rigidsoft_band.py end JOBDIR WORKER NWORKERS FQ HELD_DETAILS.csv SUB.csv N [--only asis,TL6hi_71] [--shift7 0.15]
    [--tols 0.1,0.15,0.2,0.25,0.3] [--df 0,0.003] [--sets alm0] [--dry 0]
    A band that runs to one end of the block moves one diagonal track. The four staircases are built again on their
    wall lattices around the new tilted squares (rigidsoft_step.staircases), once per tolerance, and a start with
    exactly N squares is quenched. Control: the start `asis` must give N squares and end at the side of SUB.csv."""
    jd, w, nw, fqbin, held_csv, sub, n = a[0], int(a[1]), int(a[2]), a[3], a[4], a[5], int(a[6])
    opt = {'--only': '', '--shift7': '0.15', '--tols': '0.1,0.15,0.2,0.25,0.3', '--df': '0,0.003', '--sets': 'alm0', '--dry': '0'}
    i = 7
    while i < len(a):
        opt[a[i]] = a[i + 1]; i += 2
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(held_csv))}
    os.makedirs(jd + '/raw', exist_ok=True); os.makedirs(jd + '/tmp', exist_ok=True)
    s, X = RS.normalize(RS.load(sub, {n})[n])
    only = set(v for v in opt['--only'].split(',') if v)
    res = '%s/end-%d-%d.tsv' % (jd, n, w)
    q = 0; nq = 0; best = None; seen = set()
    for tag0, T in end_starts(s, X, float(opt['--shift7'])):
        if only and tag0 not in only:
            continue
        hw = RS.hw(T[:, 2])
        if (T[:, 0] - hw).min() < -1e-9 or (T[:, 1] - hw).min() < -1e-9 or (T[:, 0] + hw).max() > s + 1e-9 or (T[:, 1] + hw).max() > s + 1e-9:
            continue
        cnt = []
        for tol in [float(v) for v in opt['--tols'].split(',')]:
            rows, P = ST.staircases(s, T, tol)
            c = len(T) + len(P); cnt.append('%g:%+d' % (tol, c - n))
            sig = (tag0, tuple(tuple(rows[k]) for k in ('BL', 'BR', 'TL', 'TR')))
            if c != n or sig in seen:
                continue
            seen.add(sig); q += 1
            tag = '%s_t%g' % (tag0, tol)
            if opt['--dry'] == '1' or q % nw != w:
                continue
            if time.time() > float(open(jd + '/deadline').read()):
                break
            Y = np.vstack([T, np.column_stack([P, np.zeros(len(P))])])
            got = None; log = []
            for fs in opt['--sets'].split(','):
                for df in [float(v) for v in opt['--df'].split(',')]:
                    s1, X1, dt = RS.fq(fqbin, jd + '/tmp', s + df, Y, RS.FLAGSETS[fs], timeout=120)
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
                h.write('%d\t%s\t%.9f\t%.9f\t%.3e\t%s\t%s\n' % (n, tag, held[n], sb, held[n] - sb, ' '.join(log),
                        ' '.join('%s=%s' % (k, ','.join(str(v) for v in rows[k])) for k in ('BL', 'BR', 'TL', 'TR'))))
            if got is not None and (best is None or sb < best):
                best = sb
                print('BEST n=%d %s side %.9f held %.9f below %.3e' % (n, tag, sb, held[n], held[n] - sb), flush=True)
            if got is not None and sb < held[n] + float(os.environ.get('RIGIDSOFT_KEEP', '-1e-9')):
                tmpf = '%s/raw/.%d-%s.tmp' % (jd, n, tag)
                with open(tmpf, 'w', newline='') as h:
                    wr = csv.writer(h); wr.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                    for qq, (xx, yy, dd) in enumerate(got[1]):
                        wr.writerow([n, qq, repr(float(xx)), repr(float(yy)), repr(math.radians(float(dd)))])
                os.rename(tmpf, '%s/raw/%d-%s.csv' % (jd, n, tag))
        if opt['--dry'] == '1':
            print('DRY', tag0, 'tilted', len(T), 'count minus n by tolerance', ' '.join(cnt))
    print('ENDEND n=%d starts with n squares %d quenches %d best %s held %.9f start side %.9f' % (
        n, q, nq, 'None' if best is None else '%.9f' % best, held[n], s), flush=True)


def cmd_room(a):
    """per chain of the block: squares, span of the centres along the block, sum of the steps over 1"""
    s, X = RS.normalize(RS.load(a[0], {int(a[1])})[int(a[1])])
    idx, row, dev = HP.block_rows(X); T = X[idx]
    P = T[:, :2] - T[:, :2].mean(axis=0)
    w, V = np.linalg.eigh(P.T @ P)
    u = np.array([1.0, 1.0 if V[0, -1] * V[1, -1] > 0 else -1.0]) / S2; v = np.array([u[1], -u[0]])
    al = T[:, :2] @ u; ac = T[:, :2] @ v
    col = np.round(ac - ac.min()).astype(int)
    print('side %.9f tilted %d rows %d chains %d' % (s, len(T), row.max() + 1, col.max() + 1))
    for c in range(col.max() + 1):
        mk = np.where(col == c)[0]; mk = mk[np.argsort(al[mk])]
        st = np.diff(al[mk])
        print('chain %d squares %d span %.6f over %.6f changes %d' % (
            c, len(mk), al[mk][-1] - al[mk][0], float((st - 1).sum()),
            int((np.abs(np.diff(np.sign(np.round(dev[mk], 2)))) > 0).sum())))


if __name__ == '__main__':
    cmds = {'scan': cmd_scan, 'room': cmd_room, 'fault': cmd_fault, 'end': cmd_end}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]](sys.argv[2:])
