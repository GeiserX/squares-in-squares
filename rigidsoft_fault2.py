#!/usr/bin/env python3
"""rigidsoft_fault2: the fault move of rigidsoft_band.py for a band that holds a row with an extra square
(round 21, rigidsoft.md section 15).

  rigidsoft_fault2.py dry SUB.csv N [options]
  rigidsoft_fault2.py run JOBDIR WORKER NWORKERS FQ BAR.csv SUB.csv N [options] [--df 0,0.003] [--sets alm0,def]
options: [--side TL,BR] [--k all|13:26,..] [--shift7 0.15] [--rm 0.1] [--add 0.02] [--fix 0.35] [--need 1]
         [--reduce 0] [--minch 0] [--maxch 99] [--fit 9] [--flipx none|side|all] [--spare-rank 0] [--resume 0]

The move is built from the overlaps, not from the list of teeth, so a row with a fourth or seventh square inside the
band moves with the band:
  1. every tilted square of rows K1..K2-1 moves one diagonal track toward SIDE, extra squares too;
  2. rows K1-1 and K2 move SHIFT7 away from SIDE and each takes one more tilted square at its SIDE end;
  3. every upright on the SIDE half that now overlaps a tilted square by more than RM goes (the teeth that face the
     band, and at a row with an extra square the cells behind the tooth that went before);
  4. on the other side an upright goes into every notch next to a tooth that faces the band, where it clears every
     square to ADD;
  5. when the count is short, the spare squares go to the notches of step 4 that overlap least, up to FIX, and when
     it is over, the uprights of step 4 that came last go again.
--flipx side: a row inside the band whose extra square stands at the SIDE end first sends that square to its other
end and moves 2 * SHIFT7 toward SIDE (the SIDE staircase has one tooth fewer there, so the count can stay N with no
spare square); --flipx all does it for every row with an extra square inside the band.
--spare-rank R rotates the order of the spare notches by R places before filling the shortfall. A comma list
runs each distinct resulting start once per band and shift. Rank 0 keeps the round 21 order.
--resume 1 skips tags already recorded in this worker's result table. A missing expected raw file is run again.
Use resume only with the same input, options and keep threshold.
--minch C leaves out starts with fewer than C changes, for a continuation after a lower-change scan.
--need 1 keeps only the bands with a row of more squares than the others inside them (the new case); --need 0 also
runs the plain bands (the control against rigidsoft_band.py fault). The changes of sense are read from the new start
with rigidsoft_band.read_teeth. --reduce R keeps the bands that take R changes out; --fit F keeps the bands whose two
new end squares overlap the uprights left in place by at most F in sum.
A run stops at the unix time in JOBDIR/deadline and appends JOBDIR/fault2-N-WORKER.tsv.
RIGIDSOFT_KEEP=X writes results up to X above the bar side to JOBDIR/raw/.
"""
import csv, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rigidsoft as RS  # noqa: E402
import rigidsoft_band as RB  # noqa: E402

S2 = math.sqrt(2.0)


def corners(r):
    t = math.radians(float(r[2])); c, s = math.cos(t), math.sin(t)
    return np.array([[r[0] + (a * c - b * s) * 0.5, r[1] + (a * s + b * c) * 0.5] for a, b in ((1, 1), (-1, 1), (-1, -1), (1, -1))])


def gap(A, B):
    """the separating gap of two squares given by their corners (negative: the depth of the overlap)"""
    best = -9.0
    for P, Q in ((A, B), (B, A)):
        for i in range(4):
            e = P[(i + 1) % 4] - P[i]; nrm = np.array([e[1], -e[0]]); nrm /= np.linalg.norm(nrm)
            best = max(best, float((Q @ nrm).min() - (P @ nrm).max()))
    return best


def worst(Y, K, q, others):
    """the deepest overlap of square q with the squares OTHERS that stand within 1.5 of it (0 when none)"""
    g = 0.0
    for j in others:
        if j == q or abs(Y[j, 0] - Y[q, 0]) > 1.5 or abs(Y[j, 1] - Y[q, 1]) > 1.5:
            continue
        g = min(g, gap(K[q], K[j]))
    return g


def changes(s, Y):
    tt, idx, row, dev, a0, full = RB.read_teeth(s, Y)
    pin = RB.pinches(tt, int(row.max()) + 1); k = sorted(pin)
    return sum(1 for u, v in zip(k[:-1], k[1:]) if pin[u] != pin[v]), ''.join('%d%s' % (r, '+' if pin[r] > 0 else '-') for r in k)


def flip_extra(X, idx, row, r, shift7=0.15):
    """row R holds one more square than the others at one end: that square goes to the other end of the row, and the
    row moves 2 * SHIFT7 toward the end that loses it (round 21). Returns the end that held it ('TL' or 'BR')."""
    ac = (X[:, 0] - X[:, 1]) / S2
    m = idx[row == r]
    nb = [idx[row == k] for k in (r - 1, r + 1) if (row == k).any()]
    lo = np.median([ac[q].min() for q in nb]); hi = np.median([ac[q].max() for q in nb])
    tl = (lo - ac[m].min()) > (ac[m].max() - hi)
    if tl:
        e = m[np.argmin(ac[m])]; f = m[np.argmax(ac[m])]
        X[e, 0], X[e, 1] = X[f, 0] + 1 / S2, X[f, 1] - 1 / S2
        X[m, 0] -= 2 * shift7 / S2; X[m, 1] += 2 * shift7 / S2
    else:
        e = m[np.argmax(ac[m])]; f = m[np.argmin(ac[m])]
        X[e, 0], X[e, 1] = X[f, 0] - 1 / S2, X[f, 1] + 1 / S2
        X[m, 0] += 2 * shift7 / S2; X[m, 1] -= 2 * shift7 / S2
    X[e, 2] = X[f, 2]
    return 'TL' if tl else 'BR'


def fault2(s, X, n, k1, k2, side, shift7=0.15, rm=0.1, add=0.02, fix=0.35, flipx='none', spare_rank=0):
    """(Y, info) or None. See the module doc for the steps. FLIPX 'side': every row inside the band whose extra square
    stands at the SIDE end sends it to the other end first (flip_extra); 'all': every row with an extra square."""
    tt, idx, row, dev, a0, full = RB.teeth(s, X)
    nrow = int(row.max()) + 1
    if not (1 <= k1 < k2 <= nrow - 1):
        return None
    other = 'BR' if side == 'TL' else 'TL'
    sg = -1.0 if side == 'TL' else 1.0
    ac = (X[:, 0] - X[:, 1]) / S2
    acm = float(ac[idx].mean())
    extra_in = [r for r in range(k1, k2) if int((row == r).sum()) > full]
    Y = X.copy()
    flipped = []
    if flipx != 'none':
        for r in extra_in:
            Z = Y.copy(); e = flip_extra(Z, idx, row, r, shift7)
            if flipx == 'all' or e == side:
                Y = Z; flipped.append('%d%s' % (r, e))
    band = idx[(row >= k1) & (row < k2)]
    Y[band, 0] += sg * 0.5; Y[band, 1] -= sg * 0.5
    new = []
    moved = list(band)
    for r in (k1 - 1, k2):
        m = idx[row == r]
        if len(m) < full:
            return None
        Y[m, 0] -= sg * shift7 / S2; Y[m, 1] += sg * shift7 / S2
        e = m[np.argmin(ac[m])] if side == 'TL' else m[np.argmax(ac[m])]
        new.append((Y[e, 0] + sg / S2, Y[e, 1] - sg / S2, X[e, 2]))
        moved += list(m)
    Y = np.vstack([Y, np.array(new)])
    N0 = len(X); moved += [N0, N0 + 1]
    K = [corners(r) for r in Y]
    ups = [q for q in range(N0) if abs(X[q, 2]) < 3]
    near_band = [q for q in ups if (ac[q] - acm) * sg > 0 and
                 min(np.hypot(Y[moved, 0] - Y[q, 0], Y[moved, 1] - Y[q, 1])) < 1.5]
    gone = [q for q in near_band if worst(Y, K, q, moved) < -rm]
    live = [q for q in range(len(Y)) if q not in set(gone)]
    # the new end squares: how much they overlap what stays (the fit of section 13, as an overlap)
    fitov = -sum(worst(Y, K, q, [j for j in live if j != q]) for q in (N0, N0 + 1))
    # notches on the other side, next to every tooth that faces the band
    cand = []
    for t, qb in tt[other]:
        if k1 - 1.0 <= t <= k2 + 1.0:
            x, y = float(X[qb, 0]), float(X[qb, 1])
            for c in ((x + sg, y), (x, y - sg)):
                if 0.5 - 1e-9 <= c[0] <= s - 0.5 + 1e-9 and 0.5 - 1e-9 <= c[1] <= s - 0.5 + 1e-9:
                    cand.append((t, c))
    Yl = Y[live]; added = []; spare = []
    for t, c in cand:
        r = np.array([c[0], c[1], 0.0]); kc = corners(r)
        close = np.where((np.abs(Yl[:, 0] - c[0]) < 1.5) & (np.abs(Yl[:, 1] - c[1]) < 1.5))[0]
        g = min([gap(kc, corners(Yl[j])) for j in close] + [0.0])
        if g >= -add:
            Yl = np.vstack([Yl, r]); added.append(c)
        elif g >= -fix:
            spare.append((-g, c))
    cnt = len(Yl)
    fixed = 0
    if cnt < n:
        ordered = sorted(spare)
        if ordered:
            off = spare_rank % len(ordered)
            ordered = ordered[off:] + ordered[:off]
        for g, c in ordered:
            if cnt >= n:
                break
            r = np.array([c[0], c[1], 0.0]); kc = corners(r)
            close = np.where((np.abs(Yl[:, 0] - c[0]) < 1.5) & (np.abs(Yl[:, 1] - c[1]) < 1.5))[0]
            g2 = min([gap(kc, corners(Yl[j])) for j in close] + [0.0])
            if g2 >= -fix:
                Yl = np.vstack([Yl, r]); cnt += 1; fixed += 1
    elif cnt > n and cnt - n <= len(added):
        Yl = Yl[:n]; fixed = -(cnt - n); cnt = n
    info = 'extra_in %s flipped %s gone %d added %d fixed %+d count %+d fitov %.3f spares %d spare_rank %d' % (
        ','.join(str(r) for r in extra_in) or '-', ','.join(flipped) or '-', len(gone), len(added), fixed, len(Yl) - n, fitov, len(spare), spare_rank)
    if len(Yl) != n:
        return None, info
    ch, pin = changes(s, Yl)
    return Yl, info + ' pin %s changes %d' % (pin, ch)


def parse(a, i, opt):
    while i < len(a):
        opt[a[i]] = a[i + 1]; i += 2
    return opt


OPT = {'--side': 'TL,BR', '--k': 'all', '--shift7': '0.15', '--rm': '0.1', '--add': '0.02', '--fix': '0.35', '--need': '1',
       '--resume': '0', '--reduce': '0', '--minch': '0', '--spare-rank': '0', '--maxch': '99', '--fit': '9', '--flipx': 'none', '--df': '0,0.003', '--sets': 'alm0,def'}


def bands(s, X, n, opt):
    tt, idx, row, dev, a0, full = RB.teeth(s, X)
    nrow = int(row.max()) + 1
    pin = RB.pinches(tt, nrow); kp = sorted(pin)
    ch0 = sum(1 for u, v in zip(kp[:-1], kp[1:]) if pin[u] != pin[v])
    ks = [(k1, k2) for k1 in range(1, nrow) for k2 in range(k1 + 1, nrow)] if opt['--k'] == 'all' else \
         [tuple(int(v) for v in t.split(':')) for t in opt['--k'].split(',')]
    for side in opt['--side'].split(','):
        for k1, k2 in ks:
            if opt['--need'] == '1' and not any(int((row == r).sum()) > full for r in range(k1, k2)):
                continue
            for sh in [float(v) for v in opt['--shift7'].split(',')]:
                ranks = [int(v) for v in opt['--spare-rank'].split(',')]
                seen = set()
                if 0 not in ranks:
                    base = fault2(s, X, n, k1, k2, side, sh, float(opt['--rm']), float(opt['--add']),
                                  float(opt['--fix']), opt['--flipx'], 0)
                    if base is not None and base[0] is not None:
                        seen.add(tuple(sorted(map(tuple, np.round(base[0], 12)))))
                for rank in ranks:
                    got = fault2(s, X, n, k1, k2, side, sh, float(opt['--rm']), float(opt['--add']),
                                 float(opt['--fix']), opt['--flipx'], rank)
                    if got is None:
                        continue
                    Y, info = got
                    tag = '%s%d:%d_s%g' % (side, k1, k2, sh)
                    if rank:
                        tag += '_v%d' % rank
                    if Y is None:
                        yield tag, None, info, ch0
                        continue
                    sig = tuple(sorted(map(tuple, np.round(Y, 12))))
                    if sig in seen:
                        continue
                    seen.add(sig)
                    ch = int(info.split()[-1]); fo = float(info.split('fitov ')[1].split()[0])
                    if ch < int(opt['--minch']) or ch > int(opt['--maxch']) or ch > ch0 - int(opt['--reduce']) or fo > float(opt['--fit']):
                        continue
                    yield tag, Y, info, ch0


def cmd_dry(a):
    sub, n = a[0], int(a[1]); opt = parse(a, 2, dict(OPT))
    s, X = RS.normalize(RS.load(sub, {n})[n])
    for tag, Y, info, ch0 in bands(s, X, n, opt):
        print('DRY', tag, 'ok' if Y is not None else 'count', 'from %d changes' % ch0, info, flush=True)


def completed_tags(res, jd, n, bar, keep):
    """Recorded measurements can be skipped once their expected layout file exists."""
    done = set()
    if not os.path.exists(res):
        return done
    with open(res) as h:
        for line in h:
            row = line.rstrip('\n').split('\t')
            if len(row) < 5:
                continue
            try:
                sb = float(row[3])
            except ValueError:
                continue
            path = '%s/raw/%d-%s.csv' % (jd, n, row[1].replace(':', '-'))
            if not (sb < bar + keep) or os.path.exists(path):
                done.add(row[1])
    return done


def cmd_run(a):
    jd, w, nw, fqbin, bar_csv, sub, n = a[0], int(a[1]), int(a[2]), a[3], a[4], a[5], int(a[6])
    opt = parse(a, 7, dict(OPT))
    bar = {int(r['n']): float(r['L']) for r in csv.DictReader(open(bar_csv))}
    os.makedirs(jd + '/raw', exist_ok=True); os.makedirs(jd + '/tmp', exist_ok=True)
    s, X = RS.normalize(RS.load(sub, {n})[n])
    res = '%s/fault2-%d-%d.tsv' % (jd, n, w)
    done = set()
    if opt['--resume'] == '1':
        done = completed_tags(res, jd, n, bar[n], float(os.environ.get('RIGIDSOFT_KEEP', '-1e-9')))
    q = 0; nq = 0; best = None
    print('n=%d start side %.9f bar %.9f' % (n, s, bar[n]), flush=True)
    for tag, Y, info, ch0 in bands(s, X, n, opt):
        if Y is None:
            continue
        q += 1
        if q % nw != w or tag in done:
            continue
        if time.time() > float(open(jd + '/deadline').read()):
            break
        got = None; log = []
        for fs in opt['--sets'].split(','):
            for df in [float(v) for v in opt['--df'].split(',')]:
                s1, X1, dt = RS.fq(fqbin, jd + '/tmp', s + df, Y, RS.FLAGSETS[fs], timeout=150)
                log.append('%s+%g:%s:%.0fs' % (fs, df, 'None' if s1 is None else '%.9f' % s1, dt))
                if s1 is not None and (got is None or s1 < got[0]):
                    got = (s1, X1)
        if got is not None and got[0] < bar[n] + 5e-3:
            s2, X2, dt = RS.fq(fqbin, jd + '/tmp', got[0], got[1], RS.FLAGSETS['pol'])
            if s2 is not None and s2 < got[0]:
                got = (s2, X2)
        nq += 1
        sb = got[0] if got else float('nan')
        with open(res, 'a') as h:
            h.write('%d\t%s\t%.9f\t%.9f\t%.3e\t%s\t%s\n' % (n, tag, bar[n], sb, bar[n] - sb, ' '.join(log), info))
        if got is not None and (best is None or sb < best):
            best = sb
            print('BEST n=%d %s side %.9f bar %.9f below %.3e %s' % (n, tag, sb, bar[n], bar[n] - sb, info), flush=True)
        if got is not None and sb < bar[n] + float(os.environ.get('RIGIDSOFT_KEEP', '-1e-9')):
            t2 = tag.replace(':', '-')
            tmpf = '%s/raw/.%d-%s.tmp' % (jd, n, t2)
            with open(tmpf, 'w', newline='') as h:
                wr = csv.writer(h); wr.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for qq, (xx, yy, dd) in enumerate(got[1]):
                    wr.writerow([n, qq, repr(float(xx)), repr(float(yy)), repr(math.radians(float(dd)))])
            os.rename(tmpf, '%s/raw/%d-%s.csv' % (jd, n, t2))
    print('FAULT2END n=%d moves %d quenches %d best %s bar %.9f' % (n, q, nq, 'None' if best is None else '%.9f' % best, bar[n]), flush=True)


if __name__ == '__main__':
    cmds = {'dry': cmd_dry, 'run': cmd_run}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]](sys.argv[2:])
