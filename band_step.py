#!/usr/bin/env python3
"""The shell step for the diagonal band of the jonathan1506 layouts (avenues/band.md, round 15).

A band layout is one band of tilted squares from corner to corner with an upright grid on each side. The
band is one sheared stack: chains of c squares (c = 3 in all 12 held bands) at one tilt, each chain face
to face with the next. Between two chains the slide along the chain is dp. A normal step has dp of about
+0.23 and moves the band off the diagonal by sin(phi) - dp cos(phi), with phi = 45 degrees less the tilt.
A slip has dp of about -0.04 and moves it back. So a chain advances the band by 1 / cos(phi) along the
diagonal on average, about 1.013, and a shell (sqrt 2 of diagonal) is about 1.4 chains.

The shell rule. The grids are lattices anchored at the walls, so the exact fill (Evan Daniel's fillfast,
MIT, imported from his clone) rebuilds them for any band: one grid row and one grid column on each side
come and go with the box. The step is therefore an edit of the band only:

  delete j    remove chain j and pull every later chain back by the step into j (the stack stays face to
              face, the slip pattern after j is kept)
  insert j    repeat chain j with its own step after it and push every later chain on by that step
  trim0/1     drop the first or last square of the band (a partial end chain)

then place the band in the box of side m + f at one of four corner anchorings, drop every square that is
not inside, and fill the uprights exactly. The count of the fill names the n the layout holds at the
donor's f. A beam over edits (widths and depth below) finds the largest count for each target m.

  band_step.py measure SUB.csv N [N ...]               angle, chains, period, slips, grid rows and columns
  band_step.py search  SUB.csv DONOR M [--depth D]     the largest count at side M + f of the donor
  band_step.py build   SUB.csv DETAILS.csv OUTDIR DONOR:M [...] [--bars DIR ...] [--depth D] [--deadline FILE]
                                                       search, then every n the count reaches whose bar is
                                                       above the donor's f: squeeze, fq, certify, raw csv
  band_step.py take    DETAILS.csv TAKEDIR RAWDIR [--bars DIR ...] [--sources S.tsv]

Our own code; it imports family_step (squeeze, finish, certify, fq), family_readers (band_frame) and
methods_lp, and does not change them. Reads data only: run with python -I.
"""
import argparse, collections, csv, glob, math, os, sys, time

import numpy as np

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
sys.path.insert(0, os.environ.get('EVAND_PACKER', '$SCRATCH/bounties-squares/ext/evand/search/packer'))
import family_step as fs  # noqa: E402
import family_readers as fr  # noqa: E402
import methods_lp as mlp  # noqa: E402
import fillfast  # noqa: E402

SLIP = 0.10        # a step whose slide dp is under this is a slip
OPS = ('delete', 'insert', 'insn', 'inss', 'flip')


# ---------------------------------------------------------------- the band

def band(P):
    """-> dict(s, Q, tilt mask, th, u, v, chains [index arrays along the band, each sorted along u],
    cen [chain centres], dp [slide of each step], U [upright indices])."""
    s, Q, t = fr.band_frame(P)
    T = np.nonzero(t)[0]
    th0 = float(np.median(fs.fold(Q[T, 2])))
    best = None
    for th in (th0, th0 + math.pi / 2):          # the chains run along one of the two axes of the squares
        u = np.array([math.cos(th), math.sin(th)]); v = np.array([-math.sin(th), math.cos(th)])
        p = Q[:, :2] @ u; q = Q[:, :2] @ v
        order = T[np.argsort(q[T])]; ch = [[order[0]]]
        for i in order[1:]:
            if q[i] - q[ch[-1][-1]] < 0.35: ch[-1].append(i)
            else: ch.append([i])
        if best is None or len(ch) > len(best[0]):
            best = (ch, th, u, v, p)
    chains, th, u, v, p = best
    chains.sort(key=lambda c: Q[c, 0].mean() + Q[c, 1].mean())     # along the band, from (0, 0)
    pc = np.array([p[c].mean() for c in chains])
    if len(pc) > 2 and np.median(np.diff(pc)) < 0:                  # u points the way the normal steps slide
        u = -u; p = -p; pc = -pc
    chains = [np.array(sorted(c, key=lambda i: p[i])) for c in chains]
    cen = np.array([Q[c, :2].mean(0) for c in chains])
    return dict(s=s, Q=Q, t=t, th=th0, u=u, v=v, chains=chains, cen=cen, dp=np.diff(pc), U=np.nonzero(~t)[0])


def grid_lines(Q, idx):
    """Rows and columns of the uprights idx: distinct centre heights and abscissae (to 0.05)."""
    if len(idx) == 0:
        return 0, 0
    return len(np.unique(np.round(Q[idx, 1] * 20))), len(np.unique(np.round(Q[idx, 0] * 20)))


def measure(n, P):
    B = band(P)
    s, Q = B['s'], B['Q']
    m = math.isqrt(n); k = n - m * m
    steps = np.diff(B['cen'], axis=0)
    norm = steps[B['dp'] >= SLIP]; slips = np.nonzero(B['dp'] < SLIP)[0] + 1
    per = np.median(norm, axis=0) if len(norm) else np.array([np.nan, np.nan])
    a = (B['cen'][:, 0] + B['cen'][:, 1]) / math.sqrt(2)
    U = B['U']; above = U[(Q[U, 1] - Q[U, 0]) > 0]; below = U[(Q[U, 1] - Q[U, 0]) <= 0]
    phi = math.pi / 4 - abs(B['th'])
    return dict(n=n, m=m, k=k, f=s - m, tilt=math.degrees(abs(B['th'])), tilted=int(B['t'].sum()),
                chains=len(B['chains']), sizes=''.join(str(len(c)) for c in B['chains']),
                period='(%.3f, %.3f) at %.1f deg' % (per[0], per[1], math.degrees(math.atan2(per[1], per[0]))),
                pitch=1 / math.cos(phi), slips=len(slips), slip_at=' '.join(str(j) for j in slips),
                slip_gaps=' '.join(str(int(g)) for g in np.diff(slips)), a0=a[0], a1=a[-1], diag=s * math.sqrt(2),
                above=len(above), above_rc='%d x %d' % grid_lines(Q, above), below=len(below),
                below_rc='%d x %d' % grid_lines(Q, below))


# ---------------------------------------------------------------- the edit and the fill

def rel_chains(B):
    """The band as chain shapes (squares relative to their chain centre) and steps. -> (c0, shapes, steps)"""
    Q = B['Q']
    shapes = [Q[c] - np.array([B['cen'][j][0], B['cen'][j][1], 0.0]) for j, c in enumerate(B['chains'])]
    return B['cen'][0].copy(), shapes, [None] + list(np.diff(B['cen'], axis=0))


def assemble(c0, shapes, steps, trim=(0, 0)):
    out = []; c = c0.copy()
    for j, S in enumerate(shapes):
        if j:
            c = c + steps[j]
        out.append(S + np.array([c[0], c[1], 0.0]))
    T = np.vstack(out)
    a = T[:, 0] + T[:, 1]; o = np.argsort(a)
    T = T[o[trim[0]:len(o) - trim[1]]]
    return T


def base_steps(steps):
    """The median normal step and the median slip of a band: the two kinds split at the larger gap of their
    directions. -> (normal, slip), either None when the band has one kind only."""
    S = np.array([st for st in steps[1:] if st is not None])
    if len(S) < 3:
        return None, None
    ang = np.arctan2(S[:, 1], S[:, 0]); o = np.sort(ang); g = np.diff(o)
    if g.max() < math.radians(4):
        return np.median(S, 0), None
    cut = o[np.argmax(g)] + g.max() / 2
    lo, hi = S[ang < cut], S[ang >= cut]
    nrm, slp = (lo, hi) if len(lo) >= len(hi) else (hi, lo)
    return np.median(nrm, 0), np.median(slp, 0)


def kind_of(st, nrm, slp):
    return 0 if np.linalg.norm(st - nrm) <= np.linalg.norm(st - slp) else 1


def apply(base, ops):
    c0, shapes, steps = base
    shapes = list(shapes); steps = list(steps)
    trim = [0, 0]
    for op, j in ops:
        if op == 'delete':
            if j == 0:
                c0 = c0 + steps[1]; shapes.pop(0); steps.pop(1); steps[0] = None
            else:
                shapes.pop(j); nxt = steps[j + 1] if j + 1 < len(steps) else None
                steps.pop(j)
                if nxt is not None:
                    steps[j] = nxt
        elif op == 'insert':
            st = steps[j] if j > 0 else steps[1]
            shapes.insert(j + 1, shapes[j]); steps.insert(j + 1, st)
        elif op in ('insn', 'inss'):
            st = base_steps(steps)[0 if op == 'insn' else 1]
            if st is None:
                continue
            shapes.insert(j + 1, shapes[max(j, 1)]); steps.insert(j + 1, st)
        elif op == 'flip' and 0 < j < len(steps):
            nrm, slp = base_steps(steps)
            if nrm is None or slp is None:
                continue
            steps[j] = slp if kind_of(steps[j], nrm, slp) == 0 else nrm
        elif op == 'trim0':
            trim[0] += 1
        elif op == 'trim1':
            trim[1] += 1
    return assemble(c0, shapes, steps, tuple(trim))


def inside(T, L):
    h = (np.abs(np.cos(T[:, 2])) + np.abs(np.sin(T[:, 2]))) / 2
    return (T[:, 0] - h > -1e-9) & (T[:, 1] - h > -1e-9) & (T[:, 0] + h < L + 1e-9) & (T[:, 1] + h < L + 1e-9)


TAU = [0.0]       # the tolerant fill: uprights may overlap the band by up to this (the squeeze must repair it)


def fill(T, L):
    """Tilted squares (radians) inside the box, plus the exact upright fill. -> array (radians)"""
    T = T[inside(T, L)]
    X = T.copy(); X[:, 2] = np.degrees(X[:, 2])
    F = fillfast.fill(L, X, 'exact', tau=TAU[0])
    F[:, 2] = np.radians(F[:, 2])
    return F


def anchors(dL):
    A = [(0.0, 0.0), (dL, dL), (0.0, dL), (dL, 0.0)]
    return A + [(dL / 2, dL / 2)] if abs(dL) > 1.5 else A


def evaluate(base, ops, L, dL):
    """-> best (count, smallest gap of the tilted set, anchor, layout) over the anchors."""
    T0 = apply(base, ops)
    best = None
    for dx, dy in anchors(dL):
        T = T0 + np.array([dx, dy, 0.0])
        F = fill(T, L)
        key = (len(F), dx, dy)
        if best is None or key[0] > best[0]:
            best = (len(F), (dx, dy), F)
    return best


def positions(B, ends=3, per_type=4):
    """Chains worth an edit: both ends of the band and a spread of normal steps and of slips."""
    J = len(B['chains']); dp = B['dp']
    pos = set(range(min(ends, J))) | set(range(max(0, J - ends), J))
    for kind in (dp >= SLIP, dp < SLIP):
        idx = np.nonzero(kind)[0] + 1
        if len(idx):
            pos |= set(int(idx[i]) for i in np.linspace(0, len(idx) - 1, min(per_type, len(idx))).astype(int))
    return sorted(pos)


def search(B, m, depth=3, beam=4, log=print, stop=None):
    """Beam over band edits for the box of side m + f (f of the donor). -> list of (count, ops, anchor, layout),
    best first, one per count."""
    f = B['s'] - math.floor(B['s']); L = m + f; dL = L - B['s']
    base = rel_chains(B)
    pos = positions(B)
    seen = {}
    c, anc, F = evaluate(base, [], L, dL)
    seen[()] = (c, [], anc, F)
    front = [()]
    shells = int(round(B['s'] - L))
    if shells and shells % 3 == 0:
        # three shells are one period of the band: 4 chains (12 squares) with one slip. Delete 4 chains in a row
        # for every 3 shells down, at every place along the band, then the beam polishes the ends.
        P = 4 * shells // 3; J = len(B['chains'])
        for j in range(0, J - P + 1):
            if stop and stop():
                break
            o2 = tuple([('delete', j)] * P)
            c, anc, F = evaluate(base, list(o2), L, dL)
            seen[o2] = (c, list(o2), anc, F)
        front = sorted((o for o in seen if o), key=lambda o: -seen[o][0])[:beam]
        if log:
            log('  period: %d places, best counts %s' % (J - P + 1, [seen[o][0] for o in front]))
    for d in range(depth):
        cand = []
        for ops in front:
            for j in pos:
                for op in OPS:
                    if op == 'delete' and j >= len(B['chains']) - sum(1 for o in ops if o[0] == 'delete'):
                        continue
                    o2 = tuple(sorted(ops + ((op, j),)))
                    if o2 in seen:
                        continue
                    if stop and stop():
                        break
                    try:
                        c, anc, F = evaluate(base, list(o2), L, dL)
                    except Exception:
                        continue
                    seen[o2] = (c, list(o2), anc, F); cand.append(o2)
            for op in ('trim0', 'trim1'):
                o2 = tuple(sorted(ops + ((op, 0),)))
                if o2 not in seen:
                    c, anc, F = evaluate(base, list(o2), L, dL)
                    seen[o2] = (c, list(o2), anc, F); cand.append(o2)
        cand.sort(key=lambda o: -seen[o][0])
        front = cand[:beam]
        if log:
            log('  depth %d: %d edits, best counts %s' % (d + 1, len(cand), [seen[o][0] for o in cand[:6]]))
    by = {}
    for c, ops, anc, F in seen.values():
        if c not in by or len(ops) < len(by[c][1]):
            by[c] = (c, ops, anc, F)
    return sorted(by.values(), key=lambda r: -r[0])


# ---------------------------------------------------------------- the re-tilt

def retilt(B, dth, keep):
    """The band of B turned by dth (radians): every chain turns about its centre, and each step keeps its
    distance across the faces (dq) and, by `keep`, its slide dp ('dp') or its x or y component ('x', 'y'; the
    normal steps of the held bands share the y component 0.678). dth = 0 gives the donor band exactly.
    -> tilted squares (x, y, radians)"""
    Q = B['Q']; u0 = B['u']; v0 = np.array([-u0[1], u0[0]])
    c_, s_ = math.cos(dth), math.sin(dth)
    R = np.array([[c_, -s_], [s_, c_]])
    u = R @ u0; v = R @ v0
    out = []; c = B['cen'][0].copy()
    for j, ch in enumerate(B['chains']):
        if j:
            st = B['cen'][j] - B['cen'][j - 1]
            dq = float(st @ v0); dp = float(st @ u0)
            if keep in ('x', 'y'):
                ax = 0 if keep == 'x' else 1
                if abs(u[ax]) > 1e-6:
                    dp = (st[ax] - dq * v[ax]) / u[ax]
            c = c + dq * v + dp * u
        O = (Q[ch, :2] - B['cen'][j]) @ R.T
        for (ox, oy), a in zip(O, Q[ch, 2]):
            out.append((c[0] + ox, c[1] + oy, a + dth))
    return np.array(out)


def snap(T, L, corner, s0):
    """Move the band so its extent touches two walls: corner 0 left and bottom, 1 right and top, 2 left and top,
    3 right and bottom. Corner 4 keeps the donor's place, 5 moves it by the change of side on both axes."""
    if corner >= 4:
        d = 0.0 if corner == 4 else L - s0
        return T + np.array([d, d, 0.0])
    h = (np.abs(np.cos(T[:, 2])) + np.abs(np.sin(T[:, 2]))) / 2
    lo_x, hi_x = (T[:, 0] - h).min(), (T[:, 0] + h).max(); lo_y, hi_y = (T[:, 1] - h).min(), (T[:, 1] + h).max()
    dx = -lo_x if corner in (0, 2) else L - hi_x
    dy = -lo_y if corner in (0, 3) else L - hi_y
    return T + np.array([dx, dy, 0.0])


def tilt_scan(B, m, fs_, dths, keeps=('dp', 'y', 'x'), trims=(0, 1, 2, 3), stop=None):
    """Count of every re-tilt, side and corner, after cutting `trims` chains off the far end. -> list of
    (count, f, dth deg, keep, corner, trim, layout), best first."""
    out = []
    for keep in keeps:
        for dth in dths:
            T0 = retilt(B, math.radians(dth), keep)
            a = T0[:, 0] + T0[:, 1]; o = np.argsort(a)
            for tr in trims:
                T1 = T0[o[:len(o) - tr]] if tr else T0
                for f in fs_:
                    if stop and stop():
                        return sorted(out, key=lambda r: -r[0])
                    L = m + f
                    for corner in (0, 1, 2, 3, 4, 5):
                        F = fill(snap(T1, L, corner, B['s']), L)
                        out.append((len(F), f, dth, keep, corner, tr, F))
    return sorted(out, key=lambda r: (-r[0], r[1]))


def cmd_tilt(a):
    P = fs.load(a.sub, {a.donor})
    B = band(P[a.donor])
    os.makedirs(a.out, exist_ok=True)
    f0 = B['s'] - math.floor(B['s'])
    fs_ = sorted(set([f0] + [round(v, 6) for v in np.arange(a.flo, a.fhi + 1e-9, a.fstep) if v > f0 + 1e-7]))   # the donor's own f exactly
    dths = np.arange(-a.dth, a.dth + 1e-9, a.dstep)
    stop = (lambda: time.time() > float(open(a.deadline).read().split()[0])) if a.deadline else None
    t0 = time.time()
    res = tilt_scan(B, a.m, fs_, dths, keeps=tuple(a.keeps.split(',')), trims=tuple(int(v) for v in a.trims.split(',')), stop=stop)
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(a.details))}
    best = {}
    for c, f, dth, keep, corner, tr, F in res:
        # the smallest f at which each count is reached
        if c not in best or f < best[c][1]:
            best[c] = (c, f, dth, keep, corner, tr, F)
    with open(a.out + '/tilt.tsv', 'a') as h:
        for c in sorted(best, reverse=True)[:8]:
            _, f, dth, keep, corner, tr, F = best[c]
            Lh = held.get(c, float('nan'))
            line = '%d\t%d\t%d\t%.6f\t%+.2f\t%s\t%d\t%d\t%.6f\t%s' % (a.donor, a.m, c, f, dth, keep, corner, tr, Lh - a.m,
                   'below held' if a.m + f < Lh - 1e-9 else 'not below')
            h.write(line + '\n'); print(line, flush=True)
            if a.m + f < Lh - 1e-9 and c <= 1000:
                fs.write_rows('%s/%d-tilt-from%d.csv' % (a.out, c, a.donor), c, F)
    print('%d fills in %.0f s' % (len(res), time.time() - t0))


# ---------------------------------------------------------------- bars and certify

def bars(details, dirs):
    """The bar of each n: the lowest of the held score and every take dir's take.tsv score."""
    bar = {int(r['n']): float(r['score']) for r in csv.DictReader(open(details))}
    held = dict(bar)
    for d in dirs:
        p = os.path.join(d, 'take.tsv')
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p), delimiter='\t'):
            try:
                n = int(r['n']); sc = float(r['new'])
            except (KeyError, ValueError):
                continue
            if sc < bar.get(n, 9e9):
                bar[n] = sc
    return held, bar


def drop_to(F, n):
    """Keep n squares: drop uprights farthest from the band first (they never matter for the side)."""
    if len(F) <= n:
        return F
    up = np.nonzero(np.abs(fs.fold(F[:, 2])) < 1e-9)[0]
    d = np.abs(F[up, 1] - F[up, 0])
    gone = set(up[np.argsort(-d)][:len(F) - n].tolist())
    return F[[i for i in range(len(F)) if i not in gone]]


def cmd_measure(a):
    P = fs.load(a.sub, set(a.n))
    keys = None
    for n in a.n:
        try:
            r = measure(n, P[n])
        except Exception as ex:
            print('%d: %s' % (n, ex)); continue
        if keys is None:
            keys = list(r); print('\t'.join(keys))
        print('\t'.join(('%.6f' % v) if isinstance(v, float) else str(v) for v in r.values()))


def cmd_search(a):
    P = fs.load(a.sub, {a.donor})
    B = band(P[a.donor])
    for c, ops, anc, F in search(B, a.m, depth=a.depth)[:5]:
        print('m %d f %.6f count %d (k %d) ops %s anchor %s gap %.2e' % (a.m, B['s'] - math.floor(B['s']), c, c - a.m * a.m, ops, anc, mlp.min_gap(F)))


def cmd_build(a):
    os.makedirs(a.out + '/raw', exist_ok=True)
    held, bar = bars(a.details, a.bars)
    TAU[0] = a.tau
    stop = (lambda: os.path.exists(a.deadline) and time.time() > float(open(a.deadline).read().split()[0])) if a.deadline else None
    log = open(a.out + '/rows.tsv', 'a')
    for spec in a.pairs:
        donor, m = (int(v) for v in spec.split(':'))
        if stop and stop():
            print('deadline: stop before %s' % spec, flush=True); break
        P = fs.load(a.sub, {donor})
        B = band(P[donor]); f = B['s'] - math.floor(B['s'])
        t0 = time.time()
        res = search(B, m, depth=a.depth, beam=a.beam, stop=stop)
        print('%d -> m %d: counts %s (%.0f s)' % (donor, m, [r[0] for r in res[:6]], time.time() - t0), flush=True)
        c0, ops0, anc0, F0 = res[0]
        log.write('search\t%d\t%d\t%d\t%s\t%s\t%.6f\t%s\t%.0f\n' % (donor, m, c0, ' '.join('%s%d' % o for o in ops0) or '-',
                  '%.3f,%.3f' % anc0, f, ' '.join(str(r[0]) for r in res[:6]), time.time() - t0))
        log.flush()
        done = set()
        for c, ops, anc, F in res:
            for n in range(c, m * m, -1):
                if n in done or n > 1000:
                    continue
                Ln = (bar[n] + 1) * math.sqrt(n)
                if not (m + f < Ln - 1e-9):
                    continue
                done.add(n)
                G = drop_to(F, n)
                g = mlp.min_gap(G)
                t1 = time.time(); fs.set_limit(a.buildsec)
                try:
                    X, L, trace = fs.squeeze(G, iters=a.iters, fq=True, stop=stop, apart=max(3e-2, 2 * a.tau))
                    X, L = fs.finish(X, L, Ln, 'down', 1e-2, stop=stop)
                except fs.Unreadable as ex:
                    print('  %d: %s' % (n, ex), flush=True); continue
                try:
                    Lc, rows = fs.certify(n, X)
                    state = 'certified' if (Lc is not None and (Lc / math.sqrt(n) - 1) < bar[n] - 1e-10) else 'above'
                except ImportError:                    # no pandas on this box: the take certifies on boxA
                    state = 'below' if L < Ln - 1e-9 else 'above'
                if state in ('certified', 'below'):
                    fs.write_rows('%s/raw/%d-from%d.csv' % (a.out, n, donor), n, X)
                print('  n %d from %d (count %d at m %d, ops %s, anchor %s, gap %.2e): built %.9f -> %.9f, bar %.9f, %s (%.0f s)' % (
                    n, donor, c, m, ops, anc, g, m + f, L, Ln, state, time.time() - t1), flush=True)
                log.write('%d\t%d\t%d\t%d\t%s\t%s\t%.3e\t%.9f\t%.9f\t%.9f\t%s\n' % (
                    n, donor, m, c, ' '.join('%s%d' % o for o in ops), '%.3f,%.3f' % anc, g, m + f, L, Ln, state))
                log.flush()


def cmd_take(a):
    import floatsafe
    held, bar = bars(a.details, a.bars)
    src = {}
    if a.sources:
        for r in csv.DictReader(open(a.sources), delimiter='\t'):
            src[int(r['donor'])] = (r['source'], r['licence'])
    best = {}
    for p in sorted(glob.glob(a.raw + '/*.csv')):
        b = os.path.basename(p)[:-4]; n = int(b.split('-')[0]); donor = int(b.split('from')[1])
        rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(p))]
        if len(rows) != n:
            continue
        _, frows, score, e = floatsafe.work((n, rows))
        if frows is None or not (score < bar[n] - 1e-10):
            print('drop', n, score, bar[n], p); continue
        if n not in best or score < best[n][0]:
            best[n] = (score, frows, donor)
    os.makedirs(a.take, exist_ok=True)
    for n, (score, frows, donor) in best.items():
        tmp = '%s/%d.csv.tmp' % (a.take, n)
        with open(tmp, 'w', newline='') as g:
            w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
            for r in frows:
                w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
        os.replace(tmp, '%s/%d.csv' % (a.take, n))
    tmp = a.take + '/take.tsv.tmp'
    with open(tmp, 'w') as h:
        h.write('n\told\tnew\tgain\tsource\tlicence\n')
        for n in sorted(best):
            score, frows, donor = best[n]
            s, lic = src.get(donor, ('band_step.py from the held packing of n = %d' % donor, 'see the round tables'))
            h.write('%d\t%r\t%r\t%.3e\t%s\t%s\n' % (n, held[n], score, held[n] - score, s, lic))
            print('keep', n, held[n], score, '%.3e' % (held[n] - score))
    os.replace(tmp, a.take + '/take.tsv')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    q = sp.add_parser('measure'); q.add_argument('sub'); q.add_argument('n', type=int, nargs='+'); q.set_defaults(fn=cmd_measure)
    q = sp.add_parser('search'); q.add_argument('sub'); q.add_argument('donor', type=int); q.add_argument('m', type=int)
    q.add_argument('--depth', type=int, default=3); q.set_defaults(fn=cmd_search)
    q = sp.add_parser('build'); q.add_argument('sub'); q.add_argument('details'); q.add_argument('out'); q.add_argument('pairs', nargs='+')
    q.add_argument('--bars', nargs='*', default=[]); q.add_argument('--depth', type=int, default=3); q.add_argument('--beam', type=int, default=4)
    q.add_argument('--iters', type=int, default=40); q.add_argument('--tau', type=float, default=0.0); q.add_argument('--buildsec', type=float, default=600); q.add_argument('--deadline'); q.set_defaults(fn=cmd_build)
    q = sp.add_parser('tilt'); q.add_argument('sub'); q.add_argument('details'); q.add_argument('out'); q.add_argument('donor', type=int); q.add_argument('m', type=int)
    q.add_argument('--flo', type=float, default=0.562); q.add_argument('--fhi', type=float, default=0.583); q.add_argument('--fstep', type=float, default=0.003)
    q.add_argument('--dth', type=float, default=2.0); q.add_argument('--dstep', type=float, default=0.25); q.add_argument('--deadline')
    q.add_argument('--keeps', default='dp,y,x'); q.add_argument('--trims', default='0,1,2,3')
    q.set_defaults(fn=cmd_tilt)
    q = sp.add_parser('take'); q.add_argument('details'); q.add_argument('take'); q.add_argument('raw')
    q.add_argument('--bars', nargs='*', default=[]); q.add_argument('--sources'); q.set_defaults(fn=cmd_take)
    a = ap.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
