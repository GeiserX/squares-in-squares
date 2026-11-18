#!/usr/bin/env python3
"""rigidsoft: make the rigid 45-degree blocks of a packing soft, then let the fq quench close the side.

A rigid block is a set of touching squares at exactly 45 degrees on one square lattice. A soft block is the
same squares turned by d off 45 degrees with one slide per column (shear A) or per row (shear B), so the chains
of the block still run along the exact diagonal. That is the form of the held 261 and 971 (structure.md
section 2). The tool writes one start per operator and runs `fq quench` on each. Nothing is certified here:
methods_take.py does that on boxA.

  rigidsoft.py blocks SUB.csv N [N ...]
        the blocks of each n: squares, lattice size, angle
  rigidsoft.py gen SUB.csv JOBDIR --ns 536,578 [--ops LIST] [--from-next K] [--txt FILE:N]
        one fq start per (n, operator) under JOBDIR/start, and JOBDIR/jobs.tsv
  rigidsoft.py run JOBDIR WORKER NWORKERS FQ HELD_DETAILS.csv
        worker WORKER of NWORKERS: quench its jobs until JOBDIR/deadline (a unix time), append
        JOBDIR/results-WORKER.tsv, and write JOBDIR/raw/<n>-<tag>.csv when the side ends below the held side

Operators (--ops, comma separated; each is applied to every block of the packing unless it names one):
  id            the packing as it is (the baseline: the quench alone)
  rot:D         every block turned rigidly by D degrees about its centre
  shA:D shB:D   shear by D degrees, columns (A) or rows (B) stay stacked
  regA:P regB:P shear by the angle with tan = P*(sqrt(2)/2)/len, len = squares along the chain: the block's teeth
                meet the grid staircase again after len squares (P = 1) as in the held 261 (13 squares, 3.11 deg)
  A sign list after '@' picks the sign per block, e.g. regA:1@+- ; without it both signs of all blocks are tried
  when the packing has up to 3 blocks, else the two uniform sign choices.
--from-next K: the start is the held n+K with the K uprights nearest to a block taken out (several choices).
"""
import csv, itertools, math, os, subprocess, sys, time
import numpy as np

S2 = math.sqrt(2.0)


def load(path, want):
    pz = {}
    with open(path, newline='') as h:
        for r in csv.DictReader(h):
            n = int(r['n'])
            if n in want:
                pz.setdefault(n, []).append((int(r['square_id']), float(r['x']), float(r['y']), float(r['angle'])))
    return {n: np.array([v[1:] for v in sorted(rows)]) for n, rows in pz.items()}


def hw(deg):
    t = np.radians(deg)
    return (np.abs(np.cos(t)) + np.abs(np.sin(t))) / 2


def normalize(P):
    """rows (x, y, radians) -> side, rows (x, y, degrees in (-45, 45]) with the box at the origin"""
    d = np.degrees(P[:, 2]) % 90.0
    d = np.where(d > 45.0 + 1e-9, d - 90.0, d)
    h = hw(d)
    x0 = (P[:, 0] - h).min(); y0 = (P[:, 1] - h).min()
    X = np.column_stack([P[:, 0] - x0, P[:, 1] - y0, d])
    s = max((X[:, 0] + h).max(), (X[:, 1] + h).max())
    return float(s), X


def side(X):
    h = hw(X[:, 2])
    return float(max((X[:, 0] + h).max() - (X[:, 0] - h).min(), (X[:, 1] + h).max() - (X[:, 1] - h).min()))


def blocks(X, tol=1e-6, link=1.05, tilt=None):
    """connected sets of squares at 45 degrees (tilt=None) or within tol of tilt; each with lattice coordinates.
    returns a list of dicts: idx (indices), ij (integer lattice coordinates), phi (degrees), na, nb"""
    a = np.abs(X[:, 2])
    sel = np.where(np.abs(a - (45.0 if tilt is None else tilt)) < tol)[0]
    if len(sel) == 0:
        return []
    from scipy.spatial import cKDTree
    C = X[sel, :2]
    tr = cKDTree(C)
    par = list(range(len(sel)))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for i, j in tr.query_pairs(link):
        par[find(i)] = find(j)
    groups = {}
    for i in range(len(sel)):
        groups.setdefault(find(i), []).append(i)
    out = []
    for g in groups.values():
        idx = sel[g]
        phi = float(np.median(X[idx, 2]))
        t = math.radians(phi)
        u1 = np.array([math.cos(t), math.sin(t)]); u2 = np.array([-math.sin(t), math.cos(t)])
        c = X[idx, :2]
        p = c @ u1; q = c @ u2
        i = np.rint(p - p[0]).astype(int); j = np.rint(q - q[0]).astype(int)
        i -= i.min(); j -= j.min()
        res = max(np.abs(p - p[0] - np.rint(p - p[0])).max(), np.abs(q - q[0] - np.rint(q - q[0])).max())
        out.append({'idx': idx, 'ij': np.column_stack([i, j]), 'phi': phi, 'na': int(i.max() + 1), 'nb': int(j.max() + 1),
                    'res': float(res)})
    out.sort(key=lambda b: -len(b['idx']))
    return out


def apply_op(X, B, kind, val, sign):
    """one operator on one block; returns new rows"""
    Y = X.copy()
    idx = B['idx']; ij = B['ij'].astype(float)
    cen = X[idx, :2].mean(axis=0)
    if kind == 'rot':
        d = math.radians(val * sign)
        R = np.array([[math.cos(d), -math.sin(d)], [math.sin(d), math.cos(d)]])
        Y[idx, :2] = (X[idx, :2] - cen) @ R.T + cen
        Y[idx, 2] = X[idx, 2] + val * sign
        return Y
    if kind in ('regA', 'regB'):
        ln = B['na'] if kind == 'regA' else B['nb']
        dl = math.atan(val * (S2 / 2) / ln) * sign
        kind = 'shA' if kind == 'regA' else 'shB'
    else:
        dl = math.radians(val) * sign
    phi = math.radians(B['phi']) - dl
    u1 = np.array([math.cos(phi), math.sin(phi)]); u2 = np.array([-math.sin(phi), math.cos(phi)])
    if kind == 'shA':      # columns of fixed i stay stacked along u2; the chains of fixed j keep the old u1 direction
        c = np.outer(ij[:, 0], u1 + math.tan(dl) * u2) + np.outer(ij[:, 1], u2)
    else:                  # rows of fixed j stay stacked along u1; the chains of fixed i keep the old u2 direction
        c = np.outer(ij[:, 0], u1) + np.outer(ij[:, 1], u2 - math.tan(dl) * u1)
    Y[idx, :2] = c - c.mean(axis=0) + cen
    Y[idx, 2] = math.degrees(phi)
    return Y


def parse_ops(spec, nblocks):
    """-> list of (tag, [(kind, val, sign) per block])"""
    out = []
    for item in spec.split(','):
        item = item.strip()
        if item == 'id':
            out.append(('id', None)); continue
        signs = None
        if '@' in item:
            item, s = item.split('@'); signs = [[1 if ch == '+' else -1 for ch in s]]
        kind, val = item.split(':'); val = float(val)
        if signs is None:
            if nblocks <= 3:
                signs = [list(t) for t in itertools.product((1, -1), repeat=nblocks)]
            else:
                signs = [[1] * nblocks, [-1] * nblocks]
        for sg in signs:
            sg = (sg + [sg[-1]] * nblocks)[:nblocks]
            tag = '%s%g%s' % (kind, val, ''.join('p' if v > 0 else 'm' for v in sg))
            out.append((tag, [(kind, val, v) for v in sg]))
    return out


def write_txt(path, s, X):
    with open(path, 'w') as h:
        h.write('%d %r\n' % (len(X), float(s)))
        for x, y, d in X:
            h.write('%r %r %r\n' % (float(x), float(y), float(d)))


def read_txt(path):
    L = [l.split() for l in open(path) if l.strip() and not l.startswith('#')]
    n = int(L[0][0])
    return float(L[0][1]), np.array([[float(v) for v in q[:3]] for q in L[1:n + 1]])


def shift_in(X):
    """move the rows so that the box starts at the origin; returns side, rows"""
    h = hw(X[:, 2])
    Y = X.copy(); Y[:, 0] -= (X[:, 0] - h).min(); Y[:, 1] -= (X[:, 1] - h).min()
    return side(Y), Y


def near_uprights(X, B, k):
    """indices of the uprights that touch the block, nearest first"""
    up = np.where(np.abs(X[:, 2]) < 3.0)[0]
    c = X[B['idx'], :2]
    d = np.array([np.abs(c - X[u, :2]).max(axis=1).min() for u in up])
    o = np.argsort(d)
    return [int(up[t]) for t in o[:k]]


def cmd_blocks(a):
    P = load(a[0], set(int(v) for v in a[1:]))
    for n in sorted(P):
        s, X = normalize(P[n])
        B = blocks(X)
        print(n, 'side %.9f' % s, 'blocks', [(len(b['idx']), b['na'], b['nb'], round(b['phi'], 3), '%.1e' % b['res']) for b in B])


def cmd_gen(a):
    sub, jd = a[0], a[1]
    opt = {'--ops': 'id', '--ns': '', '--from-next': '0', '--txt': '', '--tilt': '', '--tol': '1e-6', '--pick': '6'}
    i = 2
    while i < len(a):
        opt[a[i]] = a[i + 1]; i += 2
    os.makedirs(jd + '/start', exist_ok=True)
    K = int(opt['--from-next'])
    tilt = float(opt['--tilt']) if opt['--tilt'] else None
    starts = []          # (n, label, side, rows)
    if opt['--txt']:
        f, n = opt['--txt'].rsplit(':', 1)
        s, X = read_txt(f); starts.append((int(n), 'txt', s, X))
    ns = [int(v) for v in opt['--ns'].split(',') if v]
    P = load(sub, set(ns) | set(n + K for n in ns))
    for n in ns:
        if K == 0:
            s, X = normalize(P[n]); starts.append((n, 'h', s, X))
        else:
            if n + K not in P:
                continue
            s, X = normalize(P[n + K])
            B = blocks(X, tol=float(opt['--tol']), tilt=tilt)
            seen = set()
            for bi, b in enumerate(B[:3]):
                cand = near_uprights(X, b, int(opt['--pick']))
                for comb in itertools.combinations(cand, K):
                    if comb in seen:
                        continue
                    seen.add(comb)
                    keep = np.ones(len(X), bool); keep[list(comb)] = False
                    starts.append((n, 'x%d_%s' % (K, '_'.join(str(c) for c in comb)), s, X[keep]))
    rows = []
    for n, lab, s, X in starts:
        B = blocks(X, tol=float(opt['--tol']), tilt=tilt)
        for tag, per in parse_ops(opt['--ops'], len(B)):
            Y = X
            if per is not None:
                if not B:
                    continue
                for b, (kind, val, sg) in zip(B, per):
                    Y = apply_op(Y, b, kind, val, sg)
            name = '%d-%s-%s' % (n, lab, tag)
            write_txt('%s/start/%s.txt' % (jd, name), s, Y)
            rows.append((name, n, s, len(B)))
    new = not os.path.exists(jd + '/jobs.tsv')
    with open(jd + '/jobs.tsv', 'a') as h:
        if new:
            h.write('name\tn\tside0\tblocks\n')
        for r in rows:
            h.write('%s\t%d\t%r\t%d\n' % r)
    print('starts', len(rows))


FLAGSETS = {
    'alm0': ['--loosen', '1.0'],
    'alm3': ['--loosen', '1.003'],
    'def': [],
    'pol': ['--no-alm', '--loosen', '1.0', '--flip-top', '64', '--pit', '600'],
    # stiffer starts for a block that the default ALM turns back (rigidsoft.md section 3)
    'stiff3': ['--loosen', '1.0', '--mu0', '1e3', '--mu-max', '1e5'],
    'stiff5': ['--loosen', '1.0', '--mu0', '1e5', '--mu-max', '1e7'],
    'shrink': ['--loosen', '1.0', '--shrink'],
    'shrink1': ['--loosen', '1.01', '--shrink'],
    'round': ['--loosen', '1.0', '--round-r0', '0.1', '--round-compress'],
    # round 21: the round set at other corner radii, for fault2 starts with spare squares in tight notches
    'round05': ['--loosen', '1.0', '--round-r0', '0.05', '--round-compress'],
    'round15': ['--loosen', '1.0', '--round-r0', '0.15', '--round-compress'],
    'round2': ['--loosen', '1.0', '--round-r0', '0.2', '--round-compress'],
    'round25': ['--loosen', '1.0', '--round-r0', '0.25', '--round-compress'],
    'round3': ['--loosen', '1.0', '--round-r0', '0.3', '--round-compress'],
    'round32': ['--loosen', '1.0', '--round-r0', '0.32', '--round-compress'],
    'round31': ['--loosen', '1.0', '--round-r0', '0.31', '--round-compress'],
    'round315': ['--loosen', '1.0', '--round-r0', '0.315', '--round-compress'],
    'round305': ['--loosen', '1.0', '--round-r0', '0.305', '--round-compress'],
    'round309': ['--loosen', '1.0', '--round-r0', '0.309', '--round-compress'],
    'round319': ['--loosen', '1.0', '--round-r0', '0.319', '--round-compress'],
    'round321': ['--loosen', '1.0', '--round-r0', '0.321', '--round-compress'],
    'round325': ['--loosen', '1.0', '--round-r0', '0.325', '--round-compress'],
    'round33': ['--loosen', '1.0', '--round-r0', '0.33', '--round-compress'],
    'round34': ['--loosen', '1.0', '--round-r0', '0.34', '--round-compress'],
    'round36': ['--loosen', '1.0', '--round-r0', '0.36', '--round-compress'],
    'round4': ['--loosen', '1.0', '--round-r0', '0.4', '--round-compress'],
    'round5': ['--loosen', '1.0', '--round-r0', '0.5', '--round-compress'],
    'soft': ['--loosen', '1.0', '--soft-a0', '0.1', '--soft-compress'],
}


def fq(fqbin, tmp, s, X, flags, timeout=900):
    a = '%s/a-%d.txt' % (tmp, os.getpid()); b = '%s/b-%d.txt' % (tmp, os.getpid())
    write_txt(a, s, X)
    if os.path.exists(b):
        os.remove(b)
    t = time.time(); out = (None, None)
    try:
        r = subprocess.run([fqbin, 'quench', '--in', a, '--out', b] + list(flags), capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0 and os.path.exists(b):
            out = read_txt(b)
    except subprocess.TimeoutExpired:
        pass
    return out[0], out[1], time.time() - t


def cmd_run(a):
    jd, w, nw, fqbin, held_csv = a[0], int(a[1]), int(a[2]), a[3], a[4]
    sets = a[5].split(',') if len(a) > 5 else ['alm0', 'def']
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(held_csv))}
    os.makedirs(jd + '/raw', exist_ok=True); os.makedirs(jd + '/tmp', exist_ok=True)
    done = set()
    res = '%s/results-%d.tsv' % (jd, w)
    if os.path.exists(res):
        done = set(l.split('\t')[0] for l in open(res))
    k = -1
    while True:
        jobs = [l.rstrip('\n').split('\t') for l in open(jd + '/jobs.tsv')][1:]
        todo = [(i, j) for i, j in enumerate(jobs) if i % nw == w and j[0] not in done]
        if not todo:
            break
        i, j = todo[0]
        name, n = j[0], int(j[1])
        if time.time() > float(open(jd + '/deadline').read()):
            print('deadline', flush=True); break
        s0, X0 = read_txt('%s/start/%s.txt' % (jd, name))
        best = None; log = []
        for fs in sets:
            s1, X1, dt = fq(fqbin, jd + '/tmp', s0, X0, FLAGSETS[fs])
            log.append('%s:%s:%.0fs' % (fs, 'None' if s1 is None else '%.9f' % s1, dt))
            if s1 is not None and (best is None or s1 < best[0]):
                best = (s1, X1)
        if best is not None and best[0] < held[n] + 3e-3:      # near or below the held side: the deep flags
            for rnd in range(3):
                s2, X2, dt = fq(fqbin, jd + '/tmp', best[0], best[1], FLAGSETS['pol'])
                log.append('pol:%s:%.0fs' % ('None' if s2 is None else '%.9f' % s2, dt))
                if s2 is None or not (s2 < best[0] - 3e-9):
                    break
                best = (s2, X2)
        sb = best[0] if best else float('nan')
        with open(res, 'a') as h:
            h.write('%s\t%d\t%.9f\t%.9f\t%.3e\t%s\n' % (name, n, held[n], sb, held[n] - sb, ' '.join(log)))
        done.add(name)
        print(name, 'held %.9f' % held[n], 'got %.9f' % sb, 'below %.3e' % (held[n] - sb), ' '.join(log), flush=True)
        if best is not None and best[0] < held[n] - 1e-9:
            tmpf = '%s/raw/.%s.tmp' % (jd, name)
            with open(tmpf, 'w', newline='') as h:
                wr = csv.writer(h); wr.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for q, (x, y, d) in enumerate(best[1]):
                    wr.writerow([n, q, repr(float(x)), repr(float(y)), repr(math.radians(float(d)))])
            os.rename(tmpf, '%s/raw/%d-%s.csv' % (jd, n, name.split('-', 1)[1]))


def cmd_kick(a):
    """rigidsoft.py kick JOBDIR WORKER NWORKERS FQ HELD.csv SUB.csv NS [--txt FILE:N] [--sig 0.01,0.02,0.04]
                         [--seeds 30] [--ops LIST]
    basin hopping with the quench: every start is the best packing so far of that n (first the held one, or the
    file of --txt), with an operator of --ops or none, kicked by SIG (fq --kick: SIG on x and y, 20*SIG degrees on
    the angle) and quenched. A lower side becomes the next start. Worker WORKER takes the n with index % NWORKERS."""
    jd, w, nw, fqbin, held_csv, sub = a[0], int(a[1]), int(a[2]), a[3], a[4], a[5]
    ns = [int(v) for v in a[6].split(',') if v]
    opt = {'--txt': '', '--sig': '0.01,0.02,0.04', '--seeds': '30', '--ops': '', '--target': ''}
    i = 7
    while i < len(a):
        opt[a[i]] = a[i + 1]; i += 2
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(held_csv))}
    os.makedirs(jd + '/raw', exist_ok=True); os.makedirs(jd + '/tmp', exist_ok=True)
    P = load(sub, set(ns))
    sigs = [float(v) for v in opt['--sig'].split(',')]
    res = '%s/kick-%d.tsv' % (jd, w)
    for q, n in enumerate(ns):
        if q % nw != w:
            continue
        if opt['--txt'] and int(opt['--txt'].rsplit(':', 1)[1]) == n:
            s0, X0 = read_txt(opt['--txt'].rsplit(':', 1)[0])
        else:
            s0, X0 = normalize(P[n])
        cur = (s0, X0); first = s0; nq = 0; nlow = 0
        ops = [None]
        if opt['--ops']:
            ops += parse_ops(opt['--ops'], len(blocks(X0)))
        for seed in range(1, int(opt['--seeds']) + 1):
            for sig in sigs:
                for op in ops:
                    if time.time() > float(open(jd + '/deadline').read()):
                        break
                    X = cur[1]
                    if op is not None and op[1] is not None:
                        B = blocks(X, tol=0.5)
                        for b, (kind, val, sg) in zip(B, op[1]):
                            X = apply_op(X, b, kind, val, sg)
                    s1, X1, dt = fq(fqbin, jd + '/tmp', cur[0], X, ['--loosen', '1.0', '--kick', repr(sig), '--seed', str(seed * 1000 + q)])
                    nq += 1
                    if s1 is None:
                        continue
                    if s1 < cur[0] + 2e-3:
                        s2, X2, dt2 = fq(fqbin, jd + '/tmp', s1, X1, FLAGSETS['pol'])
                        if s2 is not None and s2 < s1:
                            s1, X1 = s2, X2
                    with open(res, 'a') as h:
                        h.write('%d\t%g\t%d\t%s\t%.9f\t%.9f\t%.3e\n' % (n, sig, seed, op[0] if op else '-', cur[0], s1, cur[0] - s1))
                    if s1 < cur[0] - 3e-9:
                        cur = (s1, X1); nlow += 1
                        print('LOWER n=%d sig=%g seed=%d op=%s side %.9f (held %.9f, start %.9f)' % (n, sig, seed, op[0] if op else '-', s1, held[n], first), flush=True)
                        if s1 < held[n] + float(os.environ.get('RIGIDSOFT_KEEP', '-1e-9')):
                            tmpf = '%s/raw/.%d-kick.tmp' % (jd, n)
                            with open(tmpf, 'w', newline='') as h:
                                wr = csv.writer(h); wr.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                                for qq, (x, y, d) in enumerate(X1):
                                    wr.writerow([n, qq, repr(float(x)), repr(float(y)), repr(math.radians(float(d)))])
                            os.rename(tmpf, '%s/raw/%d-kick.csv' % (jd, n))
        print('KICKEND n=%d quenches %d lower %d start %.9f end %.9f held %.9f below held %.3e' % (n, nq, nlow, first, cur[0], held[n], held[n] - cur[0]), flush=True)


if __name__ == '__main__':
    c = sys.argv[1]
    {'blocks': cmd_blocks, 'gen': cmd_gen, 'run': cmd_run, 'kick': cmd_kick}[c](sys.argv[2:])
