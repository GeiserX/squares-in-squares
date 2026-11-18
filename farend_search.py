#!/usr/bin/env python3
"""Far ends of an arm that are not lattice tapers, measured against the lattice taper of the same count class.

  farend_search.py run C F OUTDIR [--lo 2.4] [--hi 7.0] [--step 0.004] [--seconds 60] [--designs less,share1]
                                  [--classes 2,3,5] [--seed 1] [--deadline FILE]
  farend_search.py table OUTDIR [OUTDIR ...]        the rows of every run as one table, best of each cell
  farend_search.py lib LIBWORK NEWWORK OUT.tsv OUTDIR [OUTDIR ...] [--gain 0.03] [--tapers]   the new far ends as modules
  farend_search.py results LIBWORK OUT.tsv OUTDIR [OUTDIR ...]    the best row of each cell, with the library's lowest
  farend_search.py turn OUTDIR FILE [--seconds 60]     the bar turns and hops on a far end that a run saved
  farend_search.py cut LIBWORK C OUTDIR [--classes 2,3] [--flo 0.66] [--fhi 0.76] [--per 3] [--seconds 30]
                                  one square less or more, from the far zones of the library

The zone problem, the loss and the count class are those of zone_search.py: a far zone of N squares in a strip of
width W = c - 1 + f has the length lam and the loss c cos t * lam - N, and it serves the class N mod c.

A run first enumerates the lattice tapers of (C, F) with zone_search.taper_best and builds the best of every count.
The lowest loss of each class is "the taper" of that class. Then, for each class, dear classes first:

  less     one square deleted from the best taper of the class above (the beam of zone_search.delete_beam), then the
           sweep of kinds and hops. This is the one-less step of the stair-c avenue, on a far end.
  more     one square put into the best taper of the class below (zone_search.insert), then the sweep and hops.
  shareR   the far end takes the R cells of the first grid column that stand on the end wall. Their squares become
           squares of the zone, so the zone is one square wider over its last R rows and the grid across the wall is
           no longer rigid there. The count is the squares less R. Start: the best taper of the class with those R
           uprights, then the sweep and hops. (modules.py knows such a zone: its `miss` list.)
  retilt   one bar of the taper at a time is turned about its centre by a few degrees, steeper first, and the change
           is kept when the zone gets shorter. Then hops. The far zones cut from built layouts that lose less than
           the taper of their class have bars at their own tilts.
  morex    more, from every distinct taper of the class below (up to 4) and the four largest pockets of each.
  less+, more+   less and more again, from the best zone of any design that rows.tsv holds for the class above or
           below (a turned zone, not a taper), with the bar turns before the hops.
  hop      the sweep and hops on the best taper of the class itself (the control of the three designs: it says how
           much of a gain is the hops alone).

Each result is one row of OUTDIR/rows.tsv and one pickle. --deadline FILE holds a unix time; the run stops there.

Our own code. Imports zone_search and modules of this lane and changes neither file.
"""
import csv, glob, math, os, pickle, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I drops the script dir
import numpy as np
from scipy.optimize import minimize
import modules as M
import zone_search as Z

_SOFT0, _MOD0 = Z.soft, Z.mod_of


class shared:
    """zone_search with a far zone that holds the cells `miss` of the rest: the exact test and the LP get the list
    through mod_of, and the soft search gets the other cells of the first grid column as fixed squares and its wall
    one unit out."""

    def __init__(self, miss):
        self.miss = [tuple(q) for q in miss]

    def __enter__(self):
        miss = self.miss; ms = set(miss)
        if not miss: return self

        def mod_of(c, lean=-1):
            return dict(c=c, lean=lean, miss=list(miss), rig=[])

        def soft(P, c, f, lam, lean=-1, delta=Z.DELTA, maxiter=200):
            t, p, W = Z.geom(c, f)
            S = M.stack_squares(c, lean * math.degrees(t), W / 2, lam + p / 2)
            J = int(math.ceil(lam + c * math.sin(t) + 2.5))
            cells = np.array([(W + .5, .5 + j, 0.0) for j in range(J) if (0, j) not in ms])
            S = np.vstack([S, cells]); S[:, 2] = np.radians(S[:, 2])
            X = np.array(P, float); X[:, 2] = np.radians(X[:, 2]); nz = len(X)
            E0, _ = Z.soft_energy(X.ravel(), nz, S, W + 1.0, delta)
            if E0 <= Z.EPS: return np.array(P, float), E0
            r = minimize(Z.soft_energy, X.ravel(), args=(nz, S, W + 1.0, delta), jac=True, method='L-BFGS-B',
                         options={'maxiter': maxiter, 'ftol': 1e-30, 'gtol': 1e-14})
            Q = r.x.reshape(nz, 3).copy(); Q[:, 2] = np.degrees(Q[:, 2])
            return Q, float(r.fun)

        Z.mod_of, Z.soft = mod_of, soft
        return self

    def __exit__(self, *a):
        Z.mod_of, Z.soft = _MOD0, _SOFT0


def bars_of(P):
    """the bars of a zone: rows of tilted squares set face to face (frontier_stacks.stacks), as lists of indices"""
    from frontier_stacks import stacks
    tilted = np.nonzero(np.abs(P[:, 2]) > 0.5)[0]
    if len(tilted) < 2: return [[int(i)] for i in tilted]
    return [[int(tilted[i]) for i in ch] for ch in stacks(P[tilted])[0]]


def retilt(P, c, f, lam, until, steps=(3.0, 6.0, -3.0, 10.0), lean=-1):
    """Turn one bar at a time about its centre by a few degrees (steeper first), squeeze and compact, and keep each
    change that shortens the zone. A lattice taper has every bar at the flush tilt. The far zones cut from built
    layouts that lose less than the taper of their class have bars at their own tilts, 23 to 30 degrees beside a
    flush tilt of 24. -> (length, P, changes kept)"""
    kept = 0; again = True
    while again:
        again = False
        for g in sorted(bars_of(P), key=lambda g: float(P[g, 1].mean())):      # the bars nearest the end wall first
            a0 = float(np.median(P[g, 2]))
            for d in steps:
                if time.time() > until: return lam, P, kept
                Q = M.retilt(P, [g], [a0 + lean * d])
                r = Z.settle_zone(Q, c, f, lam + 0.15, lean)
                if r is not None and r[0] < lam - 1e-7:
                    lam, P = r; kept += 1; again = True; break
            if again: break
    return lam, P, kept


def tapers(c, f, lo, hi, step, log):
    """-> {count: (length, P)}: the best lattice taper of every count, built and compacted"""
    first = {}; prev = 0; t0 = time.time()
    for lam in np.arange(lo, hi + 1e-9, step):
        N, runs, sq, up = Z.taper_best(c, f, float(lam))
        for n in range(prev + 1, N + 1): first.setdefault(n, (float(lam), sq, N))
        prev = max(prev, N)
    log('enumerated %.1f to %.1f in %.0f s, %d counts' % (lo, hi, time.time() - t0, len(first)))
    out = {}
    for n in sorted(first):
        lam, sq, N = first[n]
        if N != n or lam <= lo + 1e-9: continue
        r = Z.settle_zone(sq, c, f, lam + 0.004)
        if r is not None: out[n] = r
    log('built %d tapers in %.0f s' % (len(out), time.time() - t0))
    return out


def _opt(a, key, default, cast=float):
    return cast(a[a.index(key) + 1]) if key in a else default


def cmd_run(a):
    c, f, outdir = int(a[0]), float(a[1]), a[2]
    lo = _opt(a, '--lo', 2.4); hi = _opt(a, '--hi', 7.0); step = _opt(a, '--step', 0.004)
    seconds = _opt(a, '--seconds', 60.0); seed = _opt(a, '--seed', 1, int)
    designs = _opt(a, '--designs', 'less,share1', str).split(',')
    only = _opt(a, '--classes', None, str); only = None if only is None else [int(x) for x in only.split(',')]
    dl = _opt(a, '--deadline', None, str)
    os.makedirs(outdir, exist_ok=True)
    rng = np.random.default_rng(seed)
    t0 = time.time()
    tag = 'c%d-f%04d' % (c, round(f * 1e4))
    log = lambda s: print('[%s %.0fs] %s' % (tag, time.time() - t0, s), flush=True)
    left = lambda: (float(open(dl).read().strip()) - time.time()) if dl and os.path.exists(dl) else 1e9
    cache = '%s/tapers-%s.pkl' % (outdir, tag)
    if os.path.exists(cache): T = pickle.load(open(cache, 'rb'))
    else:
        T = tapers(c, f, lo, hi, step, log)
        pickle.dump(T, open(cache + '.tmp', 'wb')); os.replace(cache + '.tmp', cache)
    loss = lambda n, lam: Z.loss_of(c, f, n, lam)
    by = {}
    for n, (lam, P) in T.items(): by.setdefault(n % c, []).append((loss(n, lam), n))
    for r in by: by[r].sort()
    base = {r: by[r][0] for r in by}
    log('taper by class: ' + '  '.join('%d: %.3f (%d)' % (r, base[r][0], base[r][1]) for r in sorted(base)))
    rows = '%s/rows.tsv' % outdir
    if not os.path.exists(rows):
        open(rows, 'w').write('c\tf\tclass\tdesign\tcount\tmiss\tlength\tloss\ttaper_loss\ttaper_count\tless_taper\tstart\thops\tseconds\tfile\n')

    def row(r, design, n, miss, lam, P, start, k, sec):
        ls = loss(n, lam); name = 'z-%s-%s-cls%d-n%d.pkl' % (tag, design, r, n)
        pickle.dump(dict(c=c, f=f, count=n, miss=miss, lam=lam, P=P, design=design, start=start, loss=ls), open('%s/%s' % (outdir, name), 'wb'))
        open(rows, 'a').write('%d\t%.4f\t%d\t%s\t%d\t%d\t%.6f\t%.4f\t%.4f\t%d\t%+.4f\t%s\t%d\t%.0f\t%s\n' % (
            c, f, r, design, n, len(miss), lam, ls, base[r][0], base[r][1], ls - base[r][0], start, k, sec, name))
        log('class %d %-7s count %d loss %.4f (taper %.4f, %+.4f) from %s, %d hops' % (r, design, n, ls, base[r][0], ls - base[r][0], start, k))

    for n0 in sorted(T):                             # the taper rows, so that the table stands alone
        if (loss(n0, T[n0][0]), n0) == base[n0 % c]: row(n0 % c, 'taper', n0, [], T[n0][0], T[n0][1], 'enumeration', 0, 0)
    order = sorted(base, key=lambda r: -base[r][0])
    if only is not None: order = [r for r in order if r in only]
    for r in order:
        for design in designs:
            if left() < seconds + 20: log('deadline'); return 0
            t1 = time.time()
            try:
                if design == 'hop':
                    ls, n1 = base[r]; lam1, P1 = T[n1]
                    l, P, k, won = Z.hops(P1, c, f, lam1, seconds, rng)
                    row(r, design, n1, [], l, P, 'taper %d' % n1, k, time.time() - t1)
                elif design == 'retilt':
                    seen = set(); cands = []         # every distinct taper of the class, and each with one more
                    for ls, n1 in by[r]:             # flush stack taken into the zone, so that the top bar may turn too
                        if round(ls, 3) in seen: continue
                        seen.add(round(ls, 3)); lam1, P1 = T[n1]
                        cands.append((n1, lam1, P1))
                        P2, lam2 = Z.add_stacks(P1, c, f, lam1, 1)
                        cands.append((n1 + c, lam2, P2))
                        if len(cands) >= 6: break
                    best = None; part = seconds * 0.8 / len(cands)
                    for n1, lam1, P1 in cands:
                        l, P, kept = retilt(P1, c, f, lam1, time.time() + part)
                        if kept and (best is None or loss(n1, l) < best[0]): best = (loss(n1, l), n1, l, P, kept)
                    if best is None:
                        n1 = base[r][1]
                        row(r, design, n1, [], T[n1][0], T[n1][1], 'no bar turned on %d starts' % len(cands), 0, time.time() - t1)
                        continue
                    _, n1, l, P, kept = best
                    l, P, k, won = Z.hops(P, c, f, l, max(5.0, t1 + seconds - time.time()), rng)
                    row(r, design, n1, [], l, P, 'taper %d of %d starts, %d bars turned' % (n1, len(cands), kept), k, time.time() - t1)
                elif design in ('less+', 'more+'):  # the same two steps from the best zone of any design so far
                    src = (r + 1) % c if design == 'less+' else (r - 1) % c
                    got = None
                    for q in csv.DictReader(open(rows), delimiter='\t'):
                        if int(q['c']) == c and abs(float(q['f']) - f) < 1e-9 and int(q['class']) == src and not int(q['miss']):
                            if got is None or float(q['loss']) < float(got['loss']): got = q
                    if got is None or got['design'] == 'taper': continue      # less and more start from the taper
                    rec = pickle.load(open('%s/%s' % (outdir, got['file']), 'rb')); n1 = rec['count']
                    if design == 'less+': st = Z.delete_beam(rec['P'], c, f, rec['lam'], 1, beam=3)[:2]; n2 = n1 - 1
                    else: st = Z.insert(rec['P'], c, f, rec['lam'])[:2]; n2 = n1 + 1
                    best = None
                    for lam1, P1 in st:
                        l, P, kept = retilt(P1, c, f, lam1, time.time() + seconds * 0.25)
                        if best is None or l < best[0]: best = (l, P)
                    if best is None: continue
                    l, P, k, won = Z.hops(best[1], c, f, best[0], max(5.0, t1 + seconds - time.time()), rng)
                    row(r, design, n2, [], l, P, '%s %d of class %d %s 1' % (got['design'], n1, src, 'less' if design == 'less+' else 'plus'), k, time.time() - t1)
                elif design == 'morex':             # more, from every distinct taper of the class below
                    seen = set(); best = None; tried = 0
                    for ls, n1 in by.get((r - 1) % c, []):
                        if round(ls, 3) in seen or tried >= 4: continue
                        seen.add(round(ls, 3)); tried += 1; lam1, P1 = T[n1]
                        for lam2, P2 in Z.insert(P1, c, f, lam1, top=4)[:1]:
                            if best is None or loss(n1 + 1, lam2) < best[0]: best = (loss(n1 + 1, lam2), n1, lam2, P2)
                    if best is None: continue
                    _, n1, lam1, P1 = best
                    l, P, kept = retilt(P1, c, f, lam1, time.time() + seconds * 0.3)
                    l, P, k, won = Z.hops(P, c, f, l, max(5.0, t1 + seconds - time.time()), rng)
                    row(r, design, n1 + 1, [], l, P, 'taper %d plus 1, best of %d tapers' % (n1, tried), k, time.time() - t1)
                elif design == 'less':
                    up = by.get((r + 1) % c, [])[:2]; best = None
                    for ls, n1 in up:
                        lam1, P1 = T[n1]
                        st = Z.delete_beam(P1, c, f, lam1, 1, beam=3)
                        if st and (best is None or loss(n1 - 1, st[0][0]) < best[0]): best = (loss(n1 - 1, st[0][0]), n1, st[0])
                    if best is None: continue
                    _, n1, (lam1, P1) = best
                    l, P, k, won = Z.hops(P1, c, f, lam1, seconds, rng)
                    row(r, design, n1 - 1, [], l, P, 'taper %d less 1' % n1, k, time.time() - t1)
                elif design == 'more':
                    dn = by.get((r - 1) % c, [])[:2]; best = None
                    for ls, n1 in dn:
                        lam1, P1 = T[n1]
                        st = Z.insert(P1, c, f, lam1)
                        if st and (best is None or loss(n1 + 1, st[0][0]) < best[0]): best = (loss(n1 + 1, st[0][0]), n1, st[0])
                    if best is None: continue
                    _, n1, (lam1, P1) = best
                    l, P, k, won = Z.hops(P1, c, f, lam1, seconds, rng)
                    row(r, design, n1 + 1, [], l, P, 'taper %d plus 1' % n1, k, time.time() - t1)
                elif design.startswith('share'):
                    R = int(design[5:]); ls, n1 = base[r]; lam1, P1 = T[n1]
                    W = c - 1 + f; miss = [(0, j) for j in range(R)]
                    Q = np.vstack([P1, [(W + .5, .5 + j, 0.0) for j in range(R)]])
                    with shared(miss):
                        le = Z.length(Q, c, f, lam1 + 1e-6)
                        if le is None: log('class %d %s: start not legal' % (r, design)); continue
                        l, P, k, won = Z.hops(Q, c, f, le[0], seconds, rng)
                        le = Z.length(P, c, f, l + 1e-7)
                    if le is None: continue
                    row(r, design, n1, miss, le[0], P, 'taper %d with %d cells' % (n1, R), k, time.time() - t1)
            except Exception as e:                   # one cell must not end the run
                log('class %d %s failed: %r' % (r, design, e))
    log('DONE')
    return 0


def cmd_table(a):
    best = {}
    for d in a:
        for p in glob.glob(d + '/rows.tsv') + glob.glob(d + '/*/rows.tsv'):
            for r in csv.DictReader(open(p), delimiter='\t'):
                key = (int(r['c']), r['f'], int(r['class']), r['design'])
                if key not in best or float(r['loss']) < float(best[key]['loss']): best[key] = r
    cells = sorted(set(k[:2] for k in best))
    designs = sorted(set(k[3] for k in best) - {'taper'})
    print('c\tf\tclass\ttaper\t' + '\t'.join(designs) + '\tbest_new_less_taper')
    for c, f in cells:
        low = 9.0
        for r in range(c):
            t = best.get((c, f, r, 'taper'))
            if t is None: continue
            vals = [best.get((c, f, r, d)) for d in designs]
            new = [float(v['loss']) for v in vals if v]
            d = (min(new) - float(t['loss'])) if new else float('nan')
            if new: low = min(low, d)
            print('%d\t%s\t%d\t%.3f\t%s\t%+.3f' % (c, f, r, float(t['loss']), '\t'.join('%.3f' % float(v['loss']) if v else '-' for v in vals), d))
        print('# c %d f %s: the best new far end is %+.3f squares against the taper of its class' % (c, f, low))
    return 0


def cmd_lib(a):
    """farend_search.py lib LIBWORK NEWWORK OUT.tsv OUTDIR [OUTDIR ...] [--gain 0.03] [--span 0.05] [--tapers]
    The new far ends as modules of modules.py. A zone goes in when it is --gain or more below the lowest loss the
    library holds for its arm and class at its f (the tabulated lengths, as the generator sees them). Its lengths are
    tabulated by modules.tabulate within --span of its f. NEWWORK gets library.pkl, lens.pkl and farend-ids.txt."""
    import farend_rows as R
    work, new, out = a[:3]
    gain = _opt(a, '--gain', 0.03); M.SPAN = _opt(a, '--span', 0.05)
    tapers_too = '--tapers' in a                     # lattice tapers too: for an f where the library is thin
    dirs = [d for d in a[3:] if not d.startswith('--') and os.path.isdir(d)]
    lib = pickle.load(open(work + '/library.pkl', 'rb')); lens = pickle.load(open(work + '/lens.pkl', 'rb'))
    best = {}
    for d in dirs:
        for p in glob.glob(d + '/rows.tsv') + glob.glob(d + '/*/rows.tsv'):
            for r in csv.DictReader(open(p), delimiter='\t'):
                if (r['design'] == 'taper' and not tapers_too) or int(r['miss']): continue
                key = (int(r['c']), r['f'], int(r['class']))
                if key not in best or float(r['loss']) < float(best[key][0]['loss']): best[key] = (r, os.path.dirname(p))
    cs = sorted(set(k[0] for k in best))
    far = R.plain_far(lib, lens, cs)
    low = {}
    for c in cs:
        Zs, A, g = R.loss_table(far, c)
        cls = np.array([q['count'] % c for q, _, _ in Zs])
        for r in range(c):
            col = A[cls == r]
            low[(c, r)] = np.nanmin(np.where(np.isnan(col), np.inf, col), axis=0) if len(col) else np.full(len(R.FS), np.inf)
    ids = []; lines = []
    for key in sorted(best):
        r, d = best[key]; c, f, cl = key[0], float(r['f']), key[2]
        held = float(low[(c, cl)][int(np.argmin(np.abs(R.FS - f)))])
        ls = float(r['loss'])
        note = 'kept'
        if ls > held - gain: note = 'not below the library'
        else:
            rec = pickle.load(open('%s/%s' % (d, r['file']), 'rb'))
            name = 'fe%d-%df%03d%s' % (c, int(r['count']), round(f * 1000), r['design'][:2])
            q = Z.as_module(rec['P'], c, f, rec['lam'], name + '.F1', 'farend_search.py %s (%s)' % (r['design'], r['start']),
                            dict(id='lattice taper', src='zone_search.py taper enumeration (our own design)', licence='our own'))
            q['ours'] = True
            t = M.tabulate(q)
            if t.get('knots') is None: note = 'no table'
            else:
                lib['mods'].append(q); lens[q['id']] = t; ids.append(q['id'])
                note = 'kept as %s, f %.4f to %.4f' % (q['id'], t['lock'], t['knots'][0][-1])
        lines.append('%d\t%.4f\t%d\t%s\t%s\t%.4f\t%s\t%.3f\t%+.3f\t%s' % (c, f, cl, r['design'], r['count'], ls, r['taper_loss'], held, ls - held, note))
        print(lines[-1], flush=True)
    os.makedirs(new, exist_ok=True)
    pickle.dump(lib, open(new + '/library.pkl', 'wb')); pickle.dump(lens, open(new + '/lens.pkl', 'wb'))
    open(new + '/farend-ids.txt', 'w').write(''.join(i + '\n' for i in ids))
    with open(out, 'w') as h:
        h.write('c\tf\tclass\tdesign\tcount\tloss\ttaper_loss\tlibrary_lowest\tless_library\tnote\n' + '\n'.join(lines) + '\n')
    print('new far ends in the library: %d' % len(ids))
    return 0


def cmd_cut(a):
    """farend_search.py cut LIBWORK C OUTDIR [--classes 2,3] [--flo 0.66] [--fhi 0.76] [--per 3] [--seconds 30]
                            [--steps cut-,cut+] [--seed 1] [--deadline FILE]
    One square less and one square more, from the far zones of the library and not from a taper. For each class the
    starts are the --per lowest far zones of the class above (one square deleted) and of the class below (one put
    in) whose own f is in the range, one of each signature. Each runs at the f of its zone: the bar turns, then
    hops. The row has the lowest loss the library holds for the class at that f in the taper_loss column, so that
    `lib` and `results` read OUTDIR as they read a run."""
    import farend_rows as R
    work, c, outdir = a[0], int(a[1]), a[2]
    classes = [int(x) for x in _opt(a, '--classes', ','.join(str(r) for r in range(c)), str).split(',')]
    flo = _opt(a, '--flo', 0.66); fhi = _opt(a, '--fhi', 0.76); per = _opt(a, '--per', 3, int)
    seconds = _opt(a, '--seconds', 30.0); rng = np.random.default_rng(_opt(a, '--seed', 1, int))
    steps = _opt(a, '--steps', 'cut-,cut+', str).split(',')
    dl = _opt(a, '--deadline', None, str)
    left = lambda: (float(open(dl).read().strip()) - time.time()) if dl and os.path.exists(dl) else 1e9
    os.makedirs(outdir, exist_ok=True)
    t0 = time.time()
    log = lambda s: print('[cut c%d %.0fs] %s' % (c, time.time() - t0, s), flush=True)
    lib = pickle.load(open(work + '/library.pkl', 'rb')); lens = pickle.load(open(work + '/lens.pkl', 'rb'))
    Zs, A, _ = R.loss_table(R.plain_far(lib, lens, [c]), c)
    cls = np.array([q['count'] % c for q, _, _ in Zs])

    def lowest(r, f):
        col = A[cls == r, int(np.argmin(np.abs(R.FS - f)))]
        col = col[np.isfinite(col)]
        return float(col.min()) if len(col) else float('nan')

    rows = '%s/rows.tsv' % outdir
    if not os.path.exists(rows):
        open(rows, 'w').write('c\tf\tclass\tdesign\tcount\tmiss\tlength\tloss\ttaper_loss\ttaper_count\tless_taper\tstart\thops\tseconds\tfile\n')
    for r in classes:
        for design, src, d in (('cut-', (r + 1) % c, -1), ('cut+', (r - 1) % c, 1)):
            if design not in steps: continue
            cand = sorted(((Z.loss_of(c, float(q['f0']), q['count'], q['len0']), q['id'], q) for q, _, _ in Zs
                           if q['count'] % c == src and q['lean'] == -1 and flo - 1e-9 <= q['f0'] <= fhi + 1e-9), key=lambda t: t[:2])
            seen = set(); pick = []
            for ls0, _, q in cand:
                if q['sig'] in seen: continue
                seen.add(q['sig']); pick.append((ls0, q))
                if len(pick) >= per: break
            for ls0, q in pick:
                if left() < seconds + 30: log('deadline'); return 0
                f = float(q['f0']); P0 = np.asarray(q['P'], float); t1 = time.time()
                try:
                    le = Z.length(P0, c, f, q['len0'] + 1e-6)
                    if le is None:                   # a zone cut from a squeezed build touches: open it a little
                        r0 = Z.settle_zone(P0, c, f, q['len0'] + 0.01)
                        if r0 is None: log('class %d %s: %s is not legal in the zone frame' % (r, design, q['id'])); continue
                        le = (r0[0],); P0 = r0[1]
                    st = (Z.delete_beam(P0, c, f, le[0], 1, beam=3) if d < 0 else Z.insert(P0, c, f, le[0]))[:2]
                    best = None
                    for lam1, P1 in st:
                        l, P, kept = retilt(P1, c, f, lam1, time.time() + seconds * 0.15)
                        if best is None or l < best[0]: best = (l, P)
                    if best is None: log('class %d %s: no start from %s' % (r, design, q['id'])); continue
                    l, P, k, won = Z.hops(best[1], c, f, best[0], max(5.0, t1 + seconds - time.time()), rng)
                except Exception as e:
                    log('class %d %s from %s failed: %r' % (r, design, q['id'], e)); continue
                n2 = q['count'] + d; ls = Z.loss_of(c, f, n2, l); low = lowest(r, f)
                name = 'z-c%d-f%04d-%s-cls%d-n%d-%s.pkl' % (c, round(f * 1e4), design, r, n2, q['id'].replace('.', '_'))
                start = 'library zone %s (%.4f) %s 1' % (q['id'], ls0, 'less' if d < 0 else 'plus')
                pickle.dump(dict(c=c, f=f, count=n2, miss=[], lam=l, P=P, design=design, start=start, loss=ls), open('%s/%s' % (outdir, name), 'wb'))
                open(rows, 'a').write('%d\t%.4f\t%d\t%s\t%d\t0\t%.6f\t%.4f\t%.4f\t0\t%+.4f\t%s\t%d\t%.0f\t%s\n' % (
                    c, f, r, design, n2, l, ls, low, ls - low, start, k, time.time() - t1, name))
                log('class %d %s count %d f %.4f loss %.4f (library %.4f, %+.4f) from %s, %d hops' % (r, design, n2, f, ls, low, ls - low, start, k))
    log('DONE')
    return 0


def cmd_turn(a):
    """farend_search.py turn OUTDIR FILE [--seconds 60] [--seed 1]
    The bar turns and then hops on a far end that a run saved (FILE is a pickle of OUTDIR). The result is one more
    row of OUTDIR/rows.tsv with the design 'turn'. It answers: does a far end with one square more also gain from a
    turned bar, as the taper of its class does."""
    outdir, name = a[:2]
    seconds = _opt(a, '--seconds', 60.0); rng = np.random.default_rng(_opt(a, '--seed', 1, int))
    rec = pickle.load(open('%s/%s' % (outdir, name), 'rb'))
    c, f, n = rec['c'], rec['f'], rec['count']; t1 = time.time()
    src = [r for r in csv.DictReader(open(outdir + '/rows.tsv'), delimiter='\t') if r['file'] == name][-1]
    l, P, kept = retilt(rec['P'], c, f, rec['lam'], time.time() + seconds * 0.6, steps=(2.0, 4.0, 7.0, 10.0, -2.0, -4.0))
    l, P, k, won = Z.hops(P, c, f, l, max(5.0, t1 + seconds - time.time()), rng)
    ls = Z.loss_of(c, f, n, l); out = name[:-4].replace('-' + rec['design'] + '-', '-turn-') + '.pkl'
    start = '%s %d (%.4f), %d bars turned' % (rec['design'], n, rec['loss'], kept)
    pickle.dump(dict(c=c, f=f, count=n, miss=[], lam=l, P=P, design='turn', start=start, loss=ls), open('%s/%s' % (outdir, out), 'wb'))
    open(outdir + '/rows.tsv', 'a').write('%d\t%.4f\t%s\tturn\t%d\t0\t%.6f\t%.4f\t%s\t%s\t%+.4f\t%s\t%d\t%.0f\t%s\n' % (
        c, f, src['class'], n, l, ls, src['taper_loss'], src['taper_count'], ls - float(src['taper_loss']), start, k, time.time() - t1, out))
    print('class %s turn count %d loss %.4f (before %.4f, taper %s) %d bars turned, %d hops' % (src['class'], n, ls, rec['loss'], src['taper_loss'], kept, k), flush=True)
    return 0


def cmd_results(a):
    """the best row of every (c, f, class, design), with the taper of the class and the lowest loss the library holds"""
    import farend_rows as R
    work, out = a[:2]
    lib = pickle.load(open(work + '/library.pkl', 'rb')); lens = pickle.load(open(work + '/lens.pkl', 'rb'))
    best = {}
    for d in a[2:]:
        for p in glob.glob(d + '/rows.tsv') + glob.glob(d + '/*/rows.tsv'):
            for r in csv.DictReader(open(p), delimiter='\t'):
                key = (int(r['c']), r['f'], int(r['class']), r['design'])
                if key not in best or float(r['loss']) < float(best[key]['loss']): best[key] = r
    low = {}
    for c in sorted(set(k[0] for k in best)):
        Zs, A, _ = R.loss_table(R.plain_far(lib, lens, [c]), c)
        cls = np.array([q['count'] % c for q, _, _ in Zs])
        for f in sorted(set(k[1] for k in best if k[0] == c)):
            j = int(np.argmin(np.abs(R.FS - float(f))))
            col = np.where(np.isnan(A[:, j]), np.inf, A[:, j])
            for r in range(c):
                rows = np.nonzero(cls == r)[0]
                if len(rows) and np.isfinite(col[rows]).any():
                    i = rows[int(np.argmin(col[rows]))]; low[(c, f, r)] = (float(col[i]), Zs[i][0]['id'])
    with open(out + '.tmp', 'w') as h:
        h.write('c\tf\tclass\tdesign\tcount\tcells_taken\tloss\ttaper_loss\tless_taper\tlibrary_lowest\tlibrary_zone\tless_library\tstart\thops\tseconds\n')
        for key in sorted(best, key=lambda k: (k[0], k[1], k[2], k[3] != 'taper', k[3])):
            r = best[key]; c, f, cl, d = key
            t = best.get((c, f, cl, 'taper')); lw = low.get((c, f, cl))
            ls = float(r['loss'])
            h.write('%d\t%s\t%d\t%s\t%s\t%s\t%.4f\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
                c, f, cl, d, r['count'], r['miss'], ls, '%.4f' % float(t['loss']) if t else '', '%+.4f' % (ls - float(t['loss'])) if t else '',
                '%.4f' % lw[0] if lw else '', lw[1] if lw else '', '%+.4f' % (ls - lw[0]) if lw else '', r['start'], r['hops'], r['seconds']))
    os.replace(out + '.tmp', out)
    print('rows: %d -> %s' % (len(best), out))
    return 0


if __name__ == '__main__':
    cmd = {'run': cmd_run, 'table': cmd_table, 'lib': cmd_lib, 'results': cmd_results, 'cut': cmd_cut, 'turn': cmd_turn}.get(sys.argv[1] if len(sys.argv) > 1 else '')
    if cmd is None: print(__doc__); sys.exit(2)
    sys.exit(cmd(sys.argv[2:]))
