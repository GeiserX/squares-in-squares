#!/usr/bin/env python3
"""rigidsoft_scan: build rigid 45-degree block layouts just above a held side and let the fq quench soften them.

The quench alone takes the rigid 8 x 13 block of n = 261 from side 16.6925 to 16.6844 (rigidsoft.md): the block
turns by 1.1 degrees, because only its long extent is tight. So a rigid block whose threshold is a little above
the side we hold may end below it. This tool lists those blocks by the exact rule of structure.md section 2,
places each at every position of the box, fills the uprights exactly (Evan Daniel's fillfast, MIT, imported
from EVAND_PACKER) and quenches.

  rigidsoft_scan.py plan HELD_DETAILS.csv JOBDIR [--ns 329,366 | --mmin 12 --mmax 31] [--above 0.03] [--amax 40]
                    [--taus 0:1e-4,0.006:-0.004] [--maxpos 40] [--two]
        JOBDIR/jobs.tsv: one line per (n, block or pair of blocks, side, position)
  rigidsoft_scan.py run JOBDIR WORKER NWORKERS FQ HELD_DETAILS.csv
        fill, quench, append JOBDIR/results-WORKER.tsv, write JOBDIR/raw/<n>-<tag>.csv below the held side

  rigidsoft_scan.py shear JOBDIR WORKER NWORKERS FQ HELD_DETAILS.csv N A B [--eps ..] [--df ..] [--taus ..] [--shrink ..] [--freeze ..]
        a tight sheared block (structure_shear.block) with a tolerant fill, then the quench
  rigidsoft_scan.py deep JOBDIR WORKER NWORKERS FQ HELD_DETAILS.csv N A B [--df ..] [--tau ..] [--sigs ..]
        the sheared block with one slide per chain, by a coordinate search on the exact-fill count
  Every run stops at the unix time in JOBDIR/deadline. RIGIDSOFT_KEEP=X also writes results up to X above the held side.

--taus TAU:DF pairs: the fill tolerance and the offset of the side from the block's threshold. TAU = 0 with
DF = 1e-4 is the rigid layout. TAU > 0 with DF < 0 is a start below the threshold with overlaps up to TAU, which
the quench has to remove.

Measured on the control n = 261 (rigidsoft.md section 3): `run` ends 0.0056 above the held side, and `shear` and
`deep` do no better. `run` rebuilds the held 451 from its rigid 6 x 23 block to 1e-9.
"""
import csv, math, os, sys, time, random
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('EVAND_PACKER', '$SCRATCH/bounties-squares/ext/evand/search/packer'))
import rigidsoft as RS  # noqa: E402

S2 = math.sqrt(2.0)


def AB(a, f):
    return math.ceil(a * S2 - 2 * f - 1e-12)


def gain(a, b, f):
    A, B = AB(a, f), AB(b, f)
    return a * b - math.ceil((A * B + A + B) / 2), A, B


def thresholds(a):
    r = a * S2 - math.floor(a * S2)
    return [t for t in (r / 2, (r + 1) / 2) if 0.5 <= t < 1.0]


def block(a, b, cx, cy):
    """a chains of b squares at exactly 45 degrees, centre (cx, cy)"""
    d = np.array([1.0, 1.0]) / S2; v = np.array([-1.0, 1.0]) / S2
    out = []
    for k in range(b):
        for j in range(a):
            c = np.array([cx, cy]) + (k - (b - 1) / 2) * d + (j - (a - 1) / 2) * v
            out.append((float(c[0]), float(c[1]), 45.0))
    return out


def centre(a, b, f, i, j):
    """lower-left edge on the integer line x + y = i, upper-left edge on the line y - x = f + j"""
    s = i + b / S2; t = f + j - a / S2
    return (s - t) / 2, (s + t) / 2


def inside(T, L):
    h = S2 / 2
    return all(x - h > -1e-9 and y - h > -1e-9 and x + h < L + 1e-9 and y + h < L + 1e-9 for x, y, _ in T)


def positions(a, b, m, f):
    L = m + f
    out = []
    for i in range(0, 2 * m + 2):
        for j in range(-m - 1, m + 2):
            cx, cy = centre(a, b, f, i, j)
            if inside(block(a, b, cx, cy), L):
                out.append((i, j))
    return out


def cmd_plan(a):
    held_csv, jd = a[0], a[1]
    opt = {'--ns': '', '--mmin': '12', '--mmax': '31', '--above': '0.03', '--amax': '40', '--taus': '0:1e-4', '--maxpos': '40',
           '--below': '0.0'}
    two = '--two' in a
    a = [x for x in a if x != '--two']
    i = 2
    while i < len(a):
        opt[a[i]] = a[i + 1]; i += 2
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(held_csv))}
    ns = [int(v) for v in opt['--ns'].split(',') if v] or [n for n in held if int(opt['--mmin']) <= math.isqrt(n) <= int(opt['--mmax'])]
    amax = int(opt['--amax']); above = float(opt['--above']); below = float(opt['--below'])
    taus = [(float(p.split(':')[0]), float(p.split(':')[1])) for p in opt['--taus'].split(',')]
    rng = random.Random(1)
    os.makedirs(jd, exist_ok=True)
    rows = []
    for n in ns:
        m = math.isqrt(n); k = n - m * m
        if k <= 0:
            continue
        fh = held[n] - m
        cands = []
        for x in range(1, amax + 1):
            for y in range(x, amax + 1):
                ts = sorted(set(thresholds(x) + thresholds(y)))
                for t in ts:
                    if not (fh - below - 1e-9 <= t <= fh + above):
                        continue
                    g, A, B = gain(x, y, t + 1e-9)
                    if g < k or m < (A + B) / 2 + 1:
                        continue
                    cands.append((x, y, t, g))
        for (x, y, t, g) in cands:
            for tau, df in taus:
                f = t + df
                pos = positions(x, y, m, f)
                if len(pos) > int(opt['--maxpos']):
                    pos = rng.sample(pos, int(opt['--maxpos']))
                for (pi, pj) in pos:
                    rows.append((n, m, k, '%dx%d' % (x, y), '%.9f' % t, '%.9f' % f, '%g' % tau, '%d:%d' % (pi, pj), g))
        if two:
            # two blocks, each with its own gain, placed in opposite corners of the box
            singles = []
            for x in range(1, amax + 1):
                for y in range(x, amax + 1):
                    for t in sorted(set(thresholds(x) + thresholds(y))):
                        if t <= fh + above:
                            g, A, B = gain(x, y, max(t, fh - below) + 1e-9)
                            if 0 < g < k and (A + B) / 2 + 1 <= m:
                                singles.append((x, y, max(t, fh - below), g, (A + B) / 2))
            seen = set()
            for p in singles:
                for q in singles:
                    if p[3] + q[3] < k or p[3] + q[3] > k + 1 or (p[:2], q[:2]) in seen or (q[:2], p[:2]) in seen:
                        continue
                    t = max(p[2], q[2])
                    if not (fh - below - 1e-9 <= t <= fh + above) or p[4] + q[4] + 2 > m * 1.42:
                        continue
                    seen.add((p[:2], q[:2]))
                    for tau, df in taus:
                        f = t + df
                        P1 = positions(p[0], p[1], m, f); P2 = positions(q[0], q[1], m, f)
                        if not P1 or not P2:
                            continue
                        for _ in range(int(opt['--maxpos'])):
                            u = rng.choice(P1); v = rng.choice(P2)
                            rows.append((n, m, k, '%dx%d+%dx%d' % (p[0], p[1], q[0], q[1]), '%.9f' % t, '%.9f' % f, '%g' % tau,
                                         '%d:%d+%d:%d' % (u[0], u[1], v[0], v[1]), p[3] + q[3]))
    # nearest threshold above the held side first, in steps of 0.002, shuffled inside a step
    rows.sort(key=lambda r: (round((float(r[4]) - (held[r[0]] - r[1])) / 0.002), rng.random()))
    with open(jd + '/jobs.tsv', 'w') as h:
        h.write('n\tm\tk\tblock\tthreshold\tf\ttau\tpos\trule_gain\n')
        for r in rows:
            h.write('\t'.join(str(v) for v in r) + '\n')
    print('jobs', len(rows), 'n', len(set(r[0] for r in rows)))


def overlap(T1, T2):
    """True when two sets of 45-degree squares come closer than a square"""
    A = np.array(T1)[:, :2]; B = np.array(T2)[:, :2]
    d = A[:, None, :] - B[None, :, :]
    u = np.abs(d[:, :, 0] + d[:, :, 1]) / S2; v = np.abs(d[:, :, 1] - d[:, :, 0]) / S2
    return bool((np.maximum(u, v) < 1 - 1e-9).any())


def cmd_run(a):
    import fillfast
    jd, w, nw, fqbin, held_csv = a[0], int(a[1]), int(a[2]), a[3], a[4]
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(held_csv))}
    os.makedirs(jd + '/raw', exist_ok=True); os.makedirs(jd + '/tmp', exist_ok=True)
    res = '%s/results-%d.tsv' % (jd, w)
    ndone = sum(1 for _ in open(res)) if os.path.exists(res) else 0
    jobs = [l.rstrip('\n').split('\t') for l in open(jd + '/jobs.tsv')][1:]
    mine = [j for i, j in enumerate(jobs) if i % nw == w][ndone:]
    for q, j in enumerate(mine):
        if time.time() > float(open(jd + '/deadline').read()):
            print('deadline', flush=True); break
        n, m, k = int(j[0]), int(j[1]), int(j[2]); f = float(j[5]); tau = float(j[6]); L = m + f
        T = []
        bad = False
        for bl, ps in zip(j[3].split('+'), j[7].split('+')):
            x, y = (int(v) for v in bl.split('x')); pi, pj = (int(v) for v in ps.split(':'))
            cx, cy = centre(x, y, f, pi, pj)
            Tb = block(x, y, cx, cy)
            if T and overlap(T, Tb):
                bad = True
            T += Tb
        tag = '%s_%s_%s_%s' % (j[3].replace('+', 'p'), j[5], j[6], j[7].replace(':', '.').replace('+', 'p'))
        line = None
        if bad:
            line = (n, tag, held[n], 'overlap', 0, float('nan'), '')
        else:
            t0 = time.time()
            U = fillfast.fill(L, np.array(T, float).reshape(-1, 3), mode='exact', tau=tau)
            c = len(U); tf = time.time() - t0
            if c < n:
                line = (n, tag, held[n], 'short', c - n, float('nan'), 'fill %.1fs' % tf)
            else:
                X = np.array(U, float)[:, :3]
                if c > n:        # more than n: take the last uprights out
                    X = X[:n]
                best = None; log = ['fill %.1fs' % tf]
                for fs in ('alm0', 'def'):
                    s1, X1, dt = RS.fq(fqbin, jd + '/tmp', L, X, RS.FLAGSETS[fs])
                    log.append('%s:%s:%.0fs' % (fs, 'None' if s1 is None else '%.9f' % s1, dt))
                    if s1 is not None and (best is None or s1 < best[0]):
                        best = (s1, X1)
                if best is not None and best[0] < held[n] + 3e-3:
                    for rnd in range(3):
                        s2, X2, dt = RS.fq(fqbin, jd + '/tmp', best[0], best[1], RS.FLAGSETS['pol'])
                        log.append('pol:%s:%.0fs' % ('None' if s2 is None else '%.9f' % s2, dt))
                        if s2 is None or not (s2 < best[0] - 3e-9):
                            break
                        best = (s2, X2)
                sb = best[0] if best else float('nan')
                line = (n, tag, held[n], 'ok', c - n, sb, ' '.join(log))
                if best is not None and best[0] < held[n] + float(os.environ.get('RIGIDSOFT_KEEP', '-1e-9')):
                    tmpf = '%s/raw/.%d-%s.tmp' % (jd, n, tag)
                    with open(tmpf, 'w', newline='') as h:
                        wr = csv.writer(h); wr.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                        for qq, (x, y, d) in enumerate(best[1]):
                            wr.writerow([n, qq, repr(float(x)), repr(float(y)), repr(math.radians(float(d)))])
                    os.rename(tmpf, '%s/raw/%d-%s.csv' % (jd, n, tag))
        with open(res, 'a') as h:
            h.write('%d\t%s\t%.9f\t%s\t%d\t%.9f\t%.3e\t%s\n' % (line[0], line[1], line[2], line[3], line[4], line[5], line[2] - line[5], line[6]))
        print(*line, flush=True)


def sblock(a, b, eps_deg, cx, cy):
    """a chains of b squares; each chain runs along the exact diagonal with step sec(eps), the squares stand at
    45 - eps degrees and the chains are stacked along the squares' own axis (structure_shear.block)"""
    eps = math.radians(eps_deg); phi = math.pi / 4 - eps
    v = np.array([-math.sin(phi), math.cos(phi)])
    step = np.array([1.0, 1.0]) / S2 / math.cos(eps)
    out = []
    for k in range(b):
        for j in range(a):
            c = np.array([cx, cy]) + (k - (b - 1) / 2) * step + (j - (a - 1) / 2) * v
            out.append((float(c[0]), float(c[1]), math.degrees(phi)))
    return out


def sinside(T, L):
    for x, y, d in T:
        h = (abs(math.cos(math.radians(d))) + abs(math.sin(math.radians(d)))) / 2
        if x - h < -1e-9 or y - h < -1e-9 or x + h > L + 1e-9 or y + h > L + 1e-9:
            return False
    return True


def cmd_shear(a):
    """rigidsoft_scan.py shear JOBDIR WORKER NWORKERS FQ HELD.csv N A B --eps 1,2,3 --df 0.001,0.004 --taus 0.03,0.08
                              [--offs -0.2,-0.1,0,0.1,0.2] [--maxq 400]
    a sheared block at a side DF above the held side, uprights by the tolerant fill, then the quench"""
    import fillfast
    jd, w, nw, fqbin, held_csv, n, x, y = a[0], int(a[1]), int(a[2]), a[3], a[4], int(a[5]), int(a[6]), int(a[7])
    opt = {'--eps': '1,2,3', '--df': '0.001,0.004', '--taus': '0.03,0.08', '--offs': '-0.2,-0.1,0,0.1,0.2', '--maxq': '400',
           '--shrink': '0', '--span': '3', '--freeze': '0', '--sets': 'alm0,alm3'}
    i = 8
    while i < len(a):
        opt[a[i]] = a[i + 1]; i += 2
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(held_csv))}
    os.makedirs(jd + '/raw', exist_ok=True); os.makedirs(jd + '/tmp', exist_ok=True)
    m = math.isqrt(n); fh = held[n] - m
    offs = [float(v) for v in opt['--offs'].split(',')]; taus = [float(v) for v in opt['--taus'].split(',')]
    jobs = []
    shr = [float(v) for v in opt['--shrink'].split(',')]; span = int(opt['--span'])
    for eps in [float(v) for v in opt['--eps'].split(',')]:
        e = math.radians(abs(eps))
        En = x * math.cos(e) + math.sin(e); Ed = (y - 1) / math.cos(e) + math.cos(e) + math.sin(e)
        for df in [float(v) for v in opt['--df'].split(',')]:
            f = fh + df; L = m + f
            i0 = int(round((L - Ed / S2))); j0 = int(round(En / S2 - f))
            for di in range(-span, span + 1):
                for dj in range(-span, span + 1):
                    for o1 in offs:
                        for o2 in offs:
                            for sh in shr:
                                jobs.append((eps, df, i0 + di, j0 + dj, o1, o2, sh))
    random.Random(3).shuffle(jobs)
    res = '%s/shear-%d-%dx%d-%d.tsv' % (jd, n, x, y, w)
    nq = 0
    for q, (eps, df, bi, bj, o1, o2, sh) in enumerate(jobs):
        if q % nw != w:
            continue
        if time.time() > float(open(jd + '/deadline').read()) or nq >= int(opt['--maxq']):
            break
        e = math.radians(abs(eps)); f = fh + df; L = m + f
        En = x * math.cos(e) + math.sin(e); Ed = (y - 1) / math.cos(e) + math.cos(e) + math.sin(e)
        s = bi + o1 + Ed / S2; t = f + o2 + bj - En / S2
        cx, cy = (s - t) / 2, (s + t) / 2
        T = sblock(x, y, abs(eps), cx, cy)
        if eps < 0:          # the mirror shear: reflect the block in the diagonal through its centre
            T = [(cx + (yy - cy), cy + (xx - cx), 90.0 - d) for xx, yy, d in T]
        if not sinside(T, L):
            continue
        Tf = T
        if sh > 0:           # the fill sees the block pulled toward its centre by the factor 1 - sh
            Tf = [(cx + (xx - cx) * (1 - sh), cy + (yy - cy) * (1 - sh), d) for xx, yy, d in T]
        for tau in taus:
            U = fillfast.fill(L, np.array(Tf, float).reshape(-1, 3), mode='exact', tau=tau)
            if len(U) >= n:
                break
        c = len(U)
        if sh > 0:           # fillfast returns the tilted squares first: put the true block back
            U = np.array(U, float); U[:len(T), :3] = np.array(T, float)
        tag = '%dx%d_e%g_df%g_t%g_s%g_%d.%d_%g.%g' % (x, y, eps, df, tau, sh, bi, bj, o1, o2)
        if c < n:
            with open(res, 'a') as h:
                h.write('%d\t%s\t%.9f\tshort\t%d\tnan\tnan\t\n' % (n, tag, held[n], c - n))
            continue
        X = np.array(U, float)[:n, :3]
        nq += 1
        best = None; log = []
        if opt['--freeze'] != '0':
            # stage 1: the uprights are frozen and only the block moves, so the block has to seat itself in the
            # staircase the fill made. stage 2: every square free, the exact polish first, then the ALM.
            spec = '%d-%d' % (len(T), n - 1)
            for mu in opt['--freeze'].split(','):
                s1, X1, dt = RS.fq(fqbin, jd + '/tmp', L, X, ['--loosen', '1.0', '--freeze', spec, '--mu0', mu, '--mu-max', '1e4', '--no-polish'])
                log.append('frz%s:%s:%.0fs' % (mu, 'None' if s1 is None else '%.9f' % s1, dt))
                if s1 is None:
                    continue
                for fs in ('pol', 'alm0'):
                    s2, X2, dt = RS.fq(fqbin, jd + '/tmp', s1, X1, RS.FLAGSETS[fs])
                    log.append('%s:%s:%.0fs' % (fs, 'None' if s2 is None else '%.9f' % s2, dt))
                    if s2 is not None and (best is None or s2 < best[0]):
                        best = (s2, X2)
        for fs in (() if opt['--freeze'] != '0' else opt['--sets'].split(',')):
            s1, X1, dt = RS.fq(fqbin, jd + '/tmp', L, X, RS.FLAGSETS[fs])
            log.append('%s:%s:%.0fs' % (fs, 'None' if s1 is None else '%.9f' % s1, dt))
            if s1 is not None and (best is None or s1 < best[0]):
                best = (s1, X1)
        if best is not None and best[0] < held[n] + 3e-3:
            for rnd in range(3):
                s2, X2, dt = RS.fq(fqbin, jd + '/tmp', best[0], best[1], RS.FLAGSETS['pol'])
                log.append('pol:%s:%.0fs' % ('None' if s2 is None else '%.9f' % s2, dt))
                if s2 is None or not (s2 < best[0] - 3e-9):
                    break
                best = (s2, X2)
        sb = best[0] if best else float('nan')
        with open(res, 'a') as h:
            h.write('%d\t%s\t%.9f\tok\t%d\t%.9f\t%.3e\t%s\n' % (n, tag, held[n], c - n, sb, held[n] - sb, ' '.join(log)))
        print(n, tag, 'held %.9f' % held[n], 'count', c - n, 'got %.9f' % sb, 'below %.3e' % (held[n] - sb), flush=True)
        if best is not None and best[0] < held[n] - 1e-9:
            tmpf = '%s/raw/.%d-%s.tmp' % (jd, n, tag)
            with open(tmpf, 'w', newline='') as h:
                wr = csv.writer(h); wr.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for qq, (xx, yy, d) in enumerate(best[1]):
                    wr.writerow([n, qq, repr(float(xx)), repr(float(yy)), repr(math.radians(float(d)))])
            os.rename(tmpf, '%s/raw/%d-%s.csv' % (jd, n, tag))


def dblock(a, b, eps_deg, cx, cy, sig, ext, mirror=False):
    """the soft block with one slide per chain: chain j starts where chain j-1 starts, plus one square along the
    squares' own axis, plus sig[j] >= 0 along their other axis in the direction that opens the teeth (the form of
    the held 261: slides 0.08 to 0.24). ext[j] = (extra squares at the start, at the end) of chain j"""
    eps = math.radians(eps_deg); phi = math.pi / 4 - eps
    u = np.array([math.cos(phi), math.sin(phi)]); v = np.array([-math.sin(phi), math.cos(phi)])
    step = np.array([1.0, 1.0]) / S2 / math.cos(eps)
    pa = np.array([-1.0, 1.0]) / S2
    ut = u if float(u @ pa) > 0 else -u
    o = [np.zeros(2)]
    for j in range(1, a):
        o.append(o[-1] + v + sig[j] * ut)
    mid = (a - 1) / 2 * v
    out = []
    for j in range(a):
        for k in range(-ext[j][0], b + ext[j][1]):
            c = np.array([cx, cy]) + (k - (b - 1) / 2) * step + o[j] - mid
            out.append((float(c[0]), float(c[1]), math.degrees(phi)))
    if mirror:
        out = [(cx + (yy - cy), cy + (xx - cx), 90.0 - d) for xx, yy, d in out]
    return out


def cmd_deep(a):
    """rigidsoft_scan.py deep JOBDIR WORKER NWORKERS FQ HELD.csv N A B [--df -0.001] [--p 1] [--tau 0.02]
                             [--sigs 0,0.04,0.08,0.12,0.16,0.2,0.24,0.3] [--offs -0.1,0,0.1] [--span 1]
    the soft block at the angle that meets the staircase again after B squares, tan = P*(sqrt(2)/2)/B, at a side DF
    from the held side. For each position a coordinate search over the slide of every chain and one more square at
    each chain end keeps the largest exact-fill count; a count of N or more goes to the quench."""
    import fillfast
    jd, w, nw, fqbin, held_csv, n, x, y = a[0], int(a[1]), int(a[2]), a[3], a[4], int(a[5]), int(a[6]), int(a[7])
    opt = {'--df': '-0.001', '--p': '1', '--tau': '0.02', '--sigs': '0,0.04,0.08,0.12,0.16,0.2,0.24,0.3', '--offs': '-0.1,0,0.1',
           '--span': '1', '--eps': ''}
    i = 8
    while i < len(a):
        opt[a[i]] = a[i + 1]; i += 2
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(held_csv))}
    os.makedirs(jd + '/raw', exist_ok=True); os.makedirs(jd + '/tmp', exist_ok=True)
    m = math.isqrt(n); fh = held[n] - m
    tau = float(opt['--tau']); sigs = [float(v) for v in opt['--sigs'].split(',')]
    offs = [float(v) for v in opt['--offs'].split(',')]; span = int(opt['--span'])
    epss = [float(v) for v in opt['--eps'].split(',')] if opt['--eps'] else [math.degrees(math.atan(float(opt['--p']) * (S2 / 2) / y))]
    jobs = []
    for eps in epss:
        for df in [float(v) for v in opt['--df'].split(',')]:
            for mirror in (False, True):
                for di in range(-span, span + 1):
                    for dj in range(-span, span + 1):
                        for o1 in offs:
                            for o2 in offs:
                                jobs.append((eps, df, mirror, di, dj, o1, o2))
    random.Random(5).shuffle(jobs)
    res = '%s/deep-%d-%dx%d-%d.tsv' % (jd, n, x, y, w)
    for q, (eps, df, mirror, di, dj, o1, o2) in enumerate(jobs):
        if q % nw != w:
            continue
        if time.time() > float(open(jd + '/deadline').read()):
            break
        e = math.radians(eps); f = fh + df; L = m + f
        En = x * math.cos(e) + math.sin(e); Ed = (y - 1) / math.cos(e) + math.cos(e) + math.sin(e)
        bi = int(round(L - Ed / S2)) + di; bj = int(round(En / S2 - f)) + dj
        st = bi + o1 + Ed / S2; tt = f + o2 + bj - En / S2
        cx, cy = (st - tt) / 2, (st + tt) / 2
        sig = [0.0] * x; ext = [(0, 0)] * x
        nf = [0]

        def cnt(sig, ext):
            T = dblock(x, y, eps, cx, cy, sig, ext, mirror)
            if not sinside(T, L):
                return -1, None
            nf[0] += 1
            U = fillfast.fill(L, np.array(T, float).reshape(-1, 3), mode='exact', tau=tau)
            return len(U), U
        best, U = cnt(sig, ext)
        if best < 0:
            continue
        t0 = time.time()
        for sweep in range(2):
            moved = False
            for j in range(1, x):
                for val in sigs:
                    if val == sig[j]:
                        continue
                    s2 = list(sig); s2[j] = val
                    c, U2 = cnt(s2, ext)
                    if c > best:
                        best, U, sig, moved = c, U2, s2, True
            for j in range(x):
                for ee in ((1, 0), (0, 1)):
                    e2 = list(ext); e2[j] = (ext[j][0] + ee[0], ext[j][1] + ee[1])
                    c, U2 = cnt(sig, e2)
                    if c > best:
                        best, U, ext, moved = c, U2, e2, True
            if not moved or best >= n:
                break
        tag = '%dx%d_e%.3f%s_df%g_%d.%d_%g.%g' % (x, y, eps, 'm' if mirror else 'p', df, bi, bj, o1, o2)
        desc = 'sig=%s ext=%s fills=%d %.0fs' % (','.join('%g' % v for v in sig), ''.join('%d%d' % t for t in ext), nf[0], time.time() - t0)
        if best < n:
            with open(res, 'a') as h:
                h.write('%d\t%s\t%.9f\tshort\t%d\tnan\tnan\t%s\n' % (n, tag, held[n], best - n, desc))
            print(n, tag, 'short', best - n, desc, flush=True)
            continue
        X = np.array(U, float)[:n, :3]
        bq = None; log = []
        for fs in ('alm0', 'alm3'):
            s1, X1, dt = RS.fq(fqbin, jd + '/tmp', L, X, RS.FLAGSETS[fs])
            log.append('%s:%s:%.0fs' % (fs, 'None' if s1 is None else '%.9f' % s1, dt))
            if s1 is not None and (bq is None or s1 < bq[0]):
                bq = (s1, X1)
        if bq is not None and bq[0] < held[n] + 3e-3:
            for rnd in range(3):
                s2, X2, dt = RS.fq(fqbin, jd + '/tmp', bq[0], bq[1], RS.FLAGSETS['pol'])
                log.append('pol:%s:%.0fs' % ('None' if s2 is None else '%.9f' % s2, dt))
                if s2 is None or not (s2 < bq[0] - 3e-9):
                    break
                bq = (s2, X2)
        sb = bq[0] if bq else float('nan')
        with open(res, 'a') as h:
            h.write('%d\t%s\t%.9f\tok\t%d\t%.9f\t%.3e\t%s %s\n' % (n, tag, held[n], best - n, sb, held[n] - sb, desc, ' '.join(log)))
        print(n, tag, 'count', best - n, 'held %.9f' % held[n], 'got %.9f' % sb, 'below %.3e' % (held[n] - sb), desc, flush=True)
        if bq is not None and bq[0] < held[n] + float(os.environ.get('RIGIDSOFT_KEEP', '-1e-9')):
            tmpf = '%s/raw/.%d-%s.tmp' % (jd, n, tag)
            with open(tmpf, 'w', newline='') as h:
                wr = csv.writer(h); wr.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for qq, (xx, yy, d) in enumerate(bq[1]):
                    wr.writerow([n, qq, repr(float(xx)), repr(float(yy)), repr(math.radians(float(d)))])
            os.rename(tmpf, '%s/raw/%d-%s.csv' % (jd, n, tag))


if __name__ == '__main__':
    {'plan': cmd_plan, 'run': cmd_run, 'shear': cmd_shear, 'deep': cmd_deep}[sys.argv[1]](sys.argv[2:])
