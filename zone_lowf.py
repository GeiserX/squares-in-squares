#!/usr/bin/env python3
"""Far zones at low side fractions: the steps around zone_search.py that the low-f sweep needs.

  zone_lowf.py pick   OUTDIR PICK.pkl [--above 0.8] [--cf C:F,C:F,...] [--known TABLE.tsv] [--every]
                      one zone for every (c, f, class) of OUTDIR/f*/zone-*.pkl, the lowest loss, as a module
                      (--above: drop a class that loses this much more than the best; --every: one per count)
  zone_lowf.py lens   PICK.pkl LENS.pkl [--part I/K] [--span 0.05]     lengths against f (modules.tabulate)
  zone_lowf.py join   LIBWORK NEWWORK PICK.pkl LENS.pkl [LENS.pkl ...] [--also WORK]
                      library.pkl and lens.pkl of modules.py with the picked zones added, and ids.txt
  zone_lowf.py three  LIBWORK PICK.pkl DETAILS.csv BOARD.json [--cf C:F,...]
                      loss by class, and the three-zone loss with the library's best corner
  zone_lowf.py slide  PICK.pkl [--cf C:F,...]                          what a grant of the grid is worth on a zone alone
  zone_lowf.py poke   C F LO HI STEP [--amax 3] [--gmax 0.30] [--out DIR]
                      the taper enumeration with one run that pokes into a slot of the grid's first column
  zone_lowf.py rows   PICK.pkl ZONESDIR TABLE.tsv                      module files into ZONESDIR, rows to append to TABLE.tsv

The zone problem, the evaluator and the searches are in zone_search.py and are used as they are. What is new here:

  pick   keeps the cheapest class of an f too. zone_search.py merge skips it, because at f of 0.86 and more the
         library holds that class. Below 0.86 the library has one or two classes for an arm of 8, 9 or 10 and
         none for an arm of 11, so the cheapest class is new as well. A picked zone carries ours = True, so
         modules.py queue and job use it.
  three  the loss a layout of two c-arms would have: corner + far zone + far zone, the lowest sum for every class
         (k - 2m - 1) mod c of n, with the corners the library holds for that pair of arms near f. It prints the
         sum twice: plain (a lower bound), and with the wall the looser arm leaves empty when the two far zones do
         not end their arms together.
  slide  the strip's grid side is rigid in the zone problem. In a layout the first column of the grid beside a far
         zone can stand off the end wall by g, when the corner grants it (modules.py: slide, g). This measures the
         length of a zone with that column lifted by g: the contact LP from the rigid zone, angles free.
  poke   a run beside one column of uprights on the wall side is one square short on the grid side, unless its last
         square pokes 1 - cos t into a slot between two cells of the grid's first column. poke enumerates the
         tapers with one such run and reports the slot each needs. Its zones carry `slot` and pick skips them.

Our own code. Reads the pickles of zone_search.py and modules.py as data.
"""
import csv, glob, json, math, os, pickle, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I drops the script dir
import numpy as np
import modules as M
import zone_search as Z


def _opt(a, key, default, cast=float):
    return cast(a[a.index(key) + 1]) if key in a else default


def _cf(a):
    v = _opt(a, '--cf', '', str)
    return [(int(x.split(':')[0]), round(float(x.split(':')[1]), 4)) for x in v.split(',') if x]


def name_of(c, n, f):
    return 'z%d-%df%03d' % (c, n, round(f * 1000))


def best_records(outdir):
    """{(c, f, count): the shortest record} over every zone file of OUTDIR"""
    recs = {}
    for p in sorted(glob.glob(outdir + '/f*/zone-*.pkl')):
        r = pickle.load(open(p, 'rb')); key = (r['c'], round(r['f'], 4), r['count'])
        if r.get('slot') is not None: continue           # a zone of `poke` needs its slot: it is not a rigid zone
        if key not in recs or r['lam'] < recs[key]['lam'] - 1e-9: recs[key] = r
    return recs


def cmd_pick(a):
    outdir, out = a[0], a[1]
    above = _opt(a, '--above', 0.8); cf = _cf(a); known = {}
    if '--known' in a:                               # zones another run already put in the table: (c, f, count) -> length
        for r in csv.DictReader(open(a[a.index('--known') + 1]), delimiter='\t'):
            known[(int(r['c']), round(float(r['f']), 4), int(r['count']))] = float(r['length'])
    recs = best_records(outdir); every = '--every' in a     # --every: every count (for the table), not one per class
    best = {}
    for (c, f, n), r in recs.items():
        if cf and (c, f) not in cf: continue
        loss = Z.loss_of(c, f, n, r['lam']); key = (c, f, n if every else n % c)
        if key not in best or loss < best[key][0] - 1e-6: best[key] = (loss, n, r)
    low = collections.defaultdict(lambda: 9e9)
    for key, v in best.items(): low[key[:2]] = min(low[key[:2]], v[0])
    mods = []
    for key in sorted(best):
        loss, n, r = best[key]; c, f = key[:2]
        if loss > low[(c, f)] + above and not every: continue
        name = name_of(c, n, f)
        if (c, f, n) in known: name += 'b' if r['lam'] < known[(c, f, n)] - 1e-6 else ''
        q = Z.as_module(r['P'], c, f, r['lam'], name + '.F1', r['how'], r['base'])
        q['ours'] = True; q['known'] = (c, f, n) in known and not name.endswith('b')
        mods.append(q)
        print('%s class %d length %.6f loss %.4f %s%s' % (q['id'], n % c, r['lam'], loss, r['how'], ' (in the table already)' if q['known'] else ''))
    pickle.dump(mods, open(out, 'wb'))
    print('picked', len(mods), 'zones at', len(low), 'pairs of c and f')
    return 0


def cmd_lens(a):
    mods = pickle.load(open(a[0], 'rb')); out = a[1]
    i, k = map(int, _opt(a, '--part', '0/1', str).split('/'))
    M.SPAN = _opt(a, '--span', 0.05)
    lens = {}
    for q in mods[i::k]:
        t = M.tabulate(q)
        if t.get('knots') is None: print(q['id'], 'no table', flush=True); continue
        lens[q['id']] = t
        print('%s lock %.4f, f up to %.4f, length at f0 %.6f' % (q['id'], t['lock'], t['knots'][0][-1], t['own']), flush=True)
    pickle.dump(lens, open(out + '.tmp', 'wb')); os.replace(out + '.tmp', out)
    return 0


def cmd_join(a):
    work, new, pick = a[0], a[1], a[2]
    also = _opt(a, '--also', None, str)
    lf = [x for x in (a[3:a.index('--also')] if '--also' in a else a[3:])]
    lib = pickle.load(open(work + '/library.pkl', 'rb')); lens = pickle.load(open(work + '/lens.pkl', 'rb'))
    have = set(q['id'] for q in lib['mods'])
    if also:                                         # the zones an earlier run merged into its own copy of the library
        lib2 = pickle.load(open(also + '/library.pkl', 'rb')); lens2 = pickle.load(open(also + '/lens.pkl', 'rb'))
        k = 0
        for q in lib2['mods']:
            if q['tag'] == 'z' and q['id'] not in have and q['id'] in lens2:
                q = dict(q); q['ours'] = True; lib['mods'].append(q); lens[q['id']] = lens2[q['id']]; have.add(q['id']); k += 1
        print('zones of %s: %d' % (also, k))
    mine = {}
    for p in lf: mine.update(pickle.load(open(p, 'rb')))
    ids = []
    for q in pickle.load(open(pick, 'rb')):
        if q['id'] in have or q['id'] not in mine: continue
        lib['mods'].append(q); lens[q['id']] = mine[q['id']]; ids.append(q['id']); have.add(q['id'])
    os.makedirs(new, exist_ok=True)
    pickle.dump(lib, open(new + '/library.pkl', 'wb')); pickle.dump(lens, open(new + '/lens.pkl', 'wb'))
    open(new + '/ids.txt', 'w').write('\n'.join(ids) + '\n')
    print('added', len(ids), 'zones; library', len(lib['mods']), 'modules')
    return 0


def corner_loss(q, f, y0, x0):
    t1, t2 = M.flush_tilt(q['c1'], f), M.flush_tilt(q['c2'], f)
    return q['c1'] * math.cos(t1) * y0 + q['c2'] * math.cos(t2) * (x0 - (q['c1'] - 1 + f)) - q['count']


def corners_at(lib, lens, c1, c2, f, reach=0.035):
    """[(loss at f, count, id, f0)] of the library's corners of this pair of arms: at f from its table when the
    table reaches f, else as found when it was found within `reach` of f"""
    out = []
    gi = int(np.argmin(np.abs(M.GRID - f)))
    for q in lib['mods']:
        if q['kind'] == 'far' or sorted((q['c1'], q['c2'])) != sorted((c1, c2)): continue
        t = lens.get(q['id']); val = None; yx = None
        if t is not None and abs(float(M.GRID[gi]) - f) < 3e-3:
            y0, x0 = t['tab'][len(M.COST) // 2][0][gi], t['tab'][len(M.COST) // 2][1][gi]
            if np.isfinite(y0) and np.isfinite(x0): val = corner_loss(q, float(M.GRID[gi]), float(y0), float(x0)); yx = (float(y0), float(x0))
        if val is None and abs(q['f0'] - f) <= reach: val = corner_loss(q, q['f0'], q['y0'], q['x0']); yx = (q['y0'], q['x0'])
        if val is not None: out.append((val, q['count'], q['id'], q['f0'], (yx[0] - yx[1]) * q['c1'] * math.cos(M.flush_tilt(q['c1'], f))))
    return sorted(out)


def far_library(lib, lens, c, f, reach=0.035):
    """{class: (loss at f, count, id)} of the library's own far zones of a c-arm (not the designed ones)"""
    best = {}
    for q in lib['mods']:
        if q['kind'] != 'far' or q['c'] != c or q['tag'] == 'z' or q['miss'] or q.get('poke'): continue
        t = lens.get(q['id']); val = None
        if t is not None and t.get('knots') is not None:
            fs, ls = t['knots']
            if fs[0] - 1e-9 <= f <= fs[-1] + 1e-9: val = Z.loss_of(c, f, q['count'], float(np.interp(f, fs, ls)))
        if val is None and abs(q['f0'] - f) <= reach: val = q['loss0']
        if val is None: continue
        cl = q['count'] % c
        if cl not in best or val < best[cl][0]: best[cl] = (val, q['count'], q['id'])
    return best


def three_zone(c, corners, far, slack=False):
    """{class of n: (sum, corner, far class a, far class b)}: the lowest corner + far + far for every class.
    slack: add what the looser arm leaves unused. Both arms end at the same wall, so the two far zones must end
    the two arms at lengths that differ by whole pitches. In squares: the corner's y0 - x0, plus (class + loss) of
    far zone 1, less (class + loss) of far zone 2, must be a multiple of c; what is left over is wall that holds
    nothing (the corner can take up a part of it by trading y0 for x0, which this sum does not count)."""
    out = {}
    for lc, cnt, cid, f0, dc in corners:
        for a in far:
            for b in far:
                r = (cnt + a + b) % c; s = lc + far[a][0] + far[b][0]
                if slack:
                    d = (dc + a + far[a][0] - b - far[b][0]) % c
                    s += min(d, c - d)
                if r not in out or s < out[r][0]: out[r] = (s, cid, a, b)
    return out


def cmd_three(a):
    work, pick, details, board = a[:4]
    lib = pickle.load(open(work + '/library.pkl', 'rb')); lens = pickle.load(open(work + '/lens.pkl', 'rb'))
    mods = pickle.load(open(pick, 'rb'))
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    brd = {int(r['n']): float(r['L']) for r in json.load(open(board))}
    cf = _cf(a) or sorted(set((q['c'], round(q['f0'], 4)) for q in mods))
    for c, f in cf:
        new = {}
        for q in mods:
            if q['c'] == c and abs(q['f0'] - f) < 1e-6: new[q['count'] % c] = (q['loss0'], q['count'], q['id'])
        old = far_library(lib, lens, c, f)
        both = dict(old)
        for cl, v in new.items():
            if cl not in both or v[0] < both[cl][0]: both[cl] = v
        cor = corners_at(lib, lens, c, c, f)
        print('\nc %d f %.2f' % (c, f))
        print('  far zone, loss by class, new:     ' + '  '.join('%d: %.2f (%d)' % (cl, new[cl][0], new[cl][1]) if cl in new else '%d: -' % cl for cl in range(c)))
        print('  far zone, loss by class, library: ' + '  '.join('%d: %.2f (%d)' % (cl, old[cl][0], old[cl][1]) if cl in old else '%d: -' % cl for cl in range(c)))
        if not cor: print('  no corner of two %d-arms within reach of f in the library' % c)
        else:
            byc = {}
            for v in cor: byc.setdefault(v[1] % c, v)
            print('  corners: ' + '  '.join('class %d: %.2f (%s, found at f %.3f)' % (k, byc[k][0], byc[k][2], byc[k][3]) for k in sorted(byc)))
            for sl, word in ((False, ''), (True, ' and the slack of the looser arm')):
                t_old = three_zone(c, cor, old, sl); t_new = three_zone(c, cor, both, sl)
                print('  three-zone loss%s by class of n, library: ' % word + '  '.join('%d: %.2f' % (r, t_old[r][0]) if r in t_old else '%d: -' % r for r in range(c)))
                print('  three-zone loss%s by class of n, with new: ' % word + '  '.join('%d: %.2f' % (r, t_new[r][0]) if r in t_new else '%d: -' % r for r in range(c)))
        # the board and the held file as two c-arms, for n whose board f is within 0.03 of f
        cell = collections.defaultdict(list)
        for n in range(300, 1001):
            m = math.isqrt(n - 1); k = n - m * m; fb = brd[n] - m; fo = held[n] - m
            if abs(fb - f) > 0.03 or m - c + 1 < 5: continue
            cell[(k - 2 * m - 1) % c].append((M.k_flush(m, fb, c, c) - k, M.k_flush(m, min(fo, 1.0), c, c) - k, n))
        if cell:
            print('  board as two %d-arms, loss by class of n (n, board, held): ' % c + '  '.join(
                '%d: %d, %.2f, %.2f' % (r, len(cell[r]), np.median([x[0] for x in cell[r]]), np.median([x[1] for x in cell[r]])) for r in sorted(cell)))
    return 0


def cmd_slide(a):
    mods = pickle.load(open(a[0], 'rb')); cf = _cf(a)
    M.SLIDE = True
    gs = (0.05, 0.10, 0.15, 0.25)
    print('zone\tclass\tlength\tloss\t' + '\t'.join('loss at g=%.2f (cells below the slot)' % g for g in gs))
    for q in mods:
        c, f = q['c'], round(q['f0'], 4)
        if cf and (c, f) not in cf: continue
        cells = ['%.4f' % q['loss0']]
        for g in gs:
            best = None
            for j0 in range(0, int(math.ceil(q['len0'])) + 3):   # the slot: cells j0 and up stand off by g
                mod = dict(c=c, lean=-1, miss=[], rig=[], slide=np.r_[np.zeros(j0), np.full(40 - j0, g)], g=g)
                r = M.far_len(mod, f, q['P'], q['len0'] + 1e-7)
                if r is not None and (best is None or r[0] < best[0] - 1e-9): best = (r[0], j0)
            cells.append('none' if best is None else '%.4f (%d)' % (Z.loss_of(c, f, q['count'], best[0]), best[1]))
        print('%s\t%d\t%.6f\t' % (q['id'], q['count'] % c, q['len0']) + '\t'.join(cells), flush=True)
    return 0


# ----------------------------------------------------------------------------------------------- tapers that poke

def poke_sites(c, f, lam, amax=3, dmax=0.0):
    """taper_sites of zone_search.py with two more freedoms. amax: a run may clear up to amax columns on the wall
    side (zone_search.py: 3). dmax > 0: a run that clears a wall-side columns may keep its last slot and poke its
    grid-side corner up to dmax past the strip, into a slot between two cells of the grid's first column.
    -> [slab][(a, b, squares, caps, poke)]; poke is None or (depth, height of the corner)."""
    t, p, W = Z.geom(c, f); ct, st, tt = math.cos(t), math.sin(t), math.tan(t)
    h = 0.5 * (ct + st); d = 0.5 * (ct - st)
    x0 = np.r_[np.arange(c - 1), W - 1 - np.arange(c - 1)]
    def cap(cx, cy):
        Lx, Ly, Bx, By, Rx = cx - h, cy - d, cx + d, cy - h, cx + h
        lo = np.maximum(x0[None, :], Lx[:, None]); hi = np.minimum(x0[None, :] + 1, Rx[:, None])
        over = hi - lo > 1e-9
        yl = np.where(hi <= Bx[:, None], Ly[:, None] - (hi - Lx[:, None]) * tt,
                      np.where(lo >= Bx[:, None], By[:, None] + (lo - Bx[:, None]) / tt, By[:, None]))
        return np.where(over, yl, np.inf)
    out = []; j = 0
    while True:
        cy0 = lam + p / 2 - j * p
        opts = []
        if j == 0:
            s = np.arange(c); cx = W / 2 + (s - (c - 1) / 2) * ct; cy = cy0 - (s - (c - 1) / 2) * st
            opts.append((0, c - 1, np.c_[cx, cy], cap(cx, cy).min(0), None))
        else:
            opts.append((0, -1, np.zeros((0, 2)), np.full(len(x0), np.inf), None))
            for a in range(0, amax + 1):
                sh = a * (1 - ct) / ct + (1e-6 if a else 0.0)
                for b in range(a, c):
                    s = np.arange(a, b + 1)
                    cx = W / 2 + (s - (c - 1) / 2) * ct + sh * ct; cy = cy0 - (s - (c - 1) / 2) * st - sh * st
                    if (cy - h).min() < 1e-9: continue
                    over = float((cx + h).max()) - W
                    if over > dmax + 1e-9: continue
                    opts.append((a, b, np.c_[cx, cy], cap(cx, cy).min(0), (over, float(cy[-1] + d)) if over > 1e-9 else None))
            if len(opts) == 1: break
        out.append(opts); j += 1
    return out


def poke_best(c, f, lam, amax=3, dmax=0.0, gmax=None):
    """The largest count of the lattice designs at lam with at most one run that pokes (and, with gmax, a slot no
    taller than gmax). -> (count, runs, squares, uprights, slot) with slot = None or (cells below, g, depth)."""
    t, p, W = Z.geom(c, f); tt = math.tan(t)
    def slot(pk):                                    # the slot a poke needs: whole cells below it, then g
        j0 = math.floor(pk[1] - pk[0] / tt - 1e-9)
        return j0, pk[1] + pk[0] * tt - j0 + 2e-6
    S = poke_sites(c, f, lam, amax, dmax)
    if gmax is not None:
        S = [[o for o in opts if o[4] is None or slot(o[4])[1] <= gmax] for opts in S]
    fl = lambda v: np.where(np.isinf(v), 9, np.clip(np.floor(np.minimum(v, 8.0) + 1e-9), 0, 8)).astype(np.int64)
    nc = 2 * (c - 1)
    caps = fl(S[0][0][3])[None, :]; cnt = np.zeros(1, int); pk = np.zeros(1, int); idx = [np.zeros(1, int)]
    pw = 10 ** np.arange(nc, dtype=np.int64)
    for opts in S[1:]:
        oc = fl(np.array([o[3] for o in opts])); on = np.array([o[1] - o[0] + 1 for o in opts]); op = np.array([o[4] is not None for o in opts], int)
        k = len(cnt)
        caps = np.minimum(caps[:, None, :], oc[None, :, :]).reshape(-1, nc)
        cnt = (cnt[:, None] + on[None, :]).ravel(); pk = (pk[:, None] + op[None, :]).ravel()
        idx = [np.repeat(q, len(opts)) for q in idx] + [np.tile(np.arange(len(opts)), k)]
        ok = pk <= 1
        caps, cnt, pk, idx = caps[ok], cnt[ok], pk[ok], [q[ok] for q in idx]
        key = caps @ pw
        o = np.lexsort((-cnt, key, pk))
        first = np.r_[True, (key[o][1:] != key[o][:-1]) | (pk[o][1:] != pk[o][:-1])]
        sel = o[first]
        caps, cnt, pk, idx = caps[sel], cnt[sel], pk[sel], [q[sel] for q in idx]
    hts = np.where(caps >= 9, 0, caps); m = c - 1
    best = None
    for kl in range(m + 1):
        tot = cnt + hts[:, :kl].sum(1) + hts[:, m:m + (m - kl)].sum(1)
        q = int(np.argmax(tot))
        if best is None or tot[q] > best[0]: best = (int(tot[q]), q, kl)
    N, q, kl = best
    runs = []; sq = []; sl = None
    for jj, opts in enumerate(S[1:]):
        o = opts[int(idx[jj + 1][q])]; runs.append((o[0], o[1]))
        sq += [(x, y, -math.degrees(t)) for x, y in o[2]]
        if o[4] is not None: sl = slot(o[4]) + (o[4][0],)
    for i in range(kl): sq += [(i + 0.5, 0.5 + r, 0.0) for r in range(hts[q, i])]
    for i in range(m - kl): sq += [(W - 0.5 - i, 0.5 + r, 0.0) for r in range(hts[q, m + i])]
    return N, runs, np.array(sq), (kl, [int(v) for v in hts[q, :kl]], [int(v) for v in hts[q, m:m + m - kl]]), sl


def cmd_poke(a):
    """zone_lowf.py poke C F LO HI STEP [--amax 3] [--gmax 0.30] [--out DIR]
    For every count: the lattice position of the best taper (zone_search.py's family), of the best taper with up to
    --amax wall-side columns beside a run, and of the best taper with one run that pokes into a slot of the grid's
    first column no taller than --gmax. The poking design of every class is then checked by the contact LP of
    modules.py with that slot open (cells above it stand off by g), and written to --out as a zone file."""
    c, f, lo, hi, step = int(a[0]), float(a[1]), float(a[2]), float(a[3]), float(a[4])
    amax = _opt(a, '--amax', 3, int); gmax = _opt(a, '--gmax', 0.30); outdir = _opt(a, '--out', None, str)
    t, p, W = Z.geom(c, f); dmax = (1 - math.cos(t)) + 2e-6          # one wall-side column beside the run
    first = [{}, {}, {}]; prev = [0, 0, 0]
    for lam in np.arange(lo, hi + 1e-9, step):
        for q, r in enumerate((Z.taper_best(c, f, float(lam)) + (None,), poke_best(c, f, float(lam), amax, 0.0), poke_best(c, f, float(lam), amax, dmax, gmax))):
            for n in range(prev[q] + 1, r[0] + 1): first[q].setdefault(n, (float(lam),) + r)
            prev[q] = max(prev[q], r[0])
    M.SLIDE = True
    print('c %d f %.3f tilt %.3f deg: a poke of one column is %.4f deep and needs a slot of %.4f or more' % (c, f, math.degrees(t), 1 - math.cos(t), (1 - math.cos(t)) / (math.sin(t) * math.cos(t))))
    best = [dict(), dict(), dict()]
    for q in range(3):
        for n, v in first[q].items():
            if v[1] != n or v[0] <= lo + 1e-9: continue
            loss = Z.loss_of(c, f, n, v[0])
            if n % c not in best[q] or loss < best[q][n % c][0]: best[q][n % c] = (loss, n, v)
    for cl in range(c):
        cells = ['%.3f (%d)' % best[q][cl][:2] if cl in best[q] else '-' for q in range(3)]
        line = 'class %d: lattice %s | wall-side columns up to %d: %s | one poke, slot up to %.2f: %s' % (cl, cells[0], amax, cells[1], gmax, cells[2])
        if cl in best[2] and best[2][cl][2][5] is not None:
            loss, n, (lam, N, runs, sq, up, sl) = best[2][cl]
            mod = dict(c=c, lean=-1, miss=[], rig=[], slide=np.r_[np.zeros(sl[0]), np.full(40 - sl[0], sl[1])], g=sl[1])
            r = M.far_len(mod, f, sq, lam + 0.004)
            line += ' | slot above %d cells, g %.3f, runs %s, wall %s, grid %s' % (sl[0], sl[1], '.'.join('%d-%d' % x if x[1] >= x[0] else '0' for x in runs), up[1], up[2])
            line += ' | LP with the slot open: ' + ('not legal' if r is None else 'length %.6f loss %.4f' % (r[0], Z.loss_of(c, f, n, r[0])))
            if r is not None and outdir:
                base = dict(id='lattice taper with one poke', src='zone_lowf.py poke (our own design)', licence='our own')
                Z._save(outdir, 'zone-%d-s950' % n, dict(lam=r[0], gap=0.0, P=r[1], how='taper with one poke, slot above %d cells, g %.3f' % (sl[0], sl[1]),
                                                       base=base, c=c, f=f, count=n, seed=950, cpu=0.0, slot=sl))
        print(line, flush=True)
    return 0


def cmd_rows(a):
    mods = pickle.load(open(a[0], 'rb')); zdir, tsv = a[1], a[2]
    lines = []
    for q in mods:
        if q.get('known'): continue
        name = q['id'][:-3]; c, f, n = q['c'], q['f0'], q['count']
        if os.path.exists('%s/%s.pkl' % (zdir, name)): print('kept as it is:', name); continue
        pickle.dump(q, open('%s/%s.pkl' % (zdir, name), 'wb'))
        Z.picture(q['P'], c, f, q['len0'], '%s/%s.svg' % (zdir, name), '%s  count %d  class %d  length %.5f  loss %.3f' % (name, n, n % c, q['len0'], q['loss0']))
        with open('%s/%s.txt' % (zdir, name), 'w') as h:
            h.write('%s count %d class %d f %.3f length %.6f loss %.4f %s\n%s\n' % (name, n, n % c, f, q['len0'], q['loss0'], q['sig'], '\n'.join(Z.rows_of(q['P']))))
        lines.append('far\t%d\t%.3f\t%d\t%d\t%.6f\t%.4f\t%s; low-f sweep\t%s\n' % (c, f, n, n % c, q['len0'], q['loss0'], q['how'], 'zones/%s.pkl' % name))
    with open(tsv, 'a') as h: h.writelines(lines)
    print('rows appended', len(lines))
    return 0


def two_tapers(c1, c2, f, lam1, lam2, hold=1):
    """A corner as two tapers that share the meeting square (round 19). Arm 1 runs up the left wall: its lattice taper
    of zone_search.py at lam1 stands on the floor (the zone frame is the corner frame, lean1 = -1). Arm 2 runs along the
    floor: its taper at lam2, mirrored in y = x (lean2 = +1), stands on the left wall. hold = 1: arm 1 keeps the
    meeting square [0, W1] x [0, W2] with the staircase of its upright columns, and arm 2 keeps only the squares that lie
    wholly at x >= W1; hold = 2 the other way round. -> (P, count of taper 1, count of taper 2)"""
    W1, W2 = c1 - 1 + f, c2 - 1 + f
    A = np.asarray(Z.taper_best(c1, f, lam1)[2], float).reshape(-1, 3)
    B = np.asarray(Z.taper_best(c2, f, lam2)[2], float).reshape(-1, 3)[:, [1, 0, 2]].copy(); B[:, 2] = -B[:, 2]
    ext = lambda S: 0.5 * (np.abs(np.cos(np.radians(S[:, 2]))) + np.abs(np.sin(np.radians(S[:, 2]))))
    if hold == 1: B = B[B[:, 0] - ext(B) >= W1 - 1e-9]
    else: A = A[A[:, 1] - ext(A) >= W2 - 1e-9]
    return np.vstack([A, B]), len(A), len(B)


def cmd_corner(a):
    """zone_lowf.py corner C1 C2 F OUT.pkl [--lo D] [--hi D] [--step S] [--keep K] [--seconds S]
    The corners of two tapers that share the meeting square (two_tapers), for every pair of taper positions lam1 in
    W2 + [lo, hi] and lam2 in W1 + [lo, hi] at which a taper gains a square, both holds. Each pair is settled (squeeze
    and the contact LP of zone_corner.py with both stacks sliding) and its loss measured. Prints the best per count
    class and the library's lowest corner loss of the same arms near F for comparison, and writes the K best of each
    class as start states for zone_corner.py search and control (the format of zone_corner.py base)."""
    import time, zone_corner as ZC
    c1, c2, f, out = int(a[0]), int(a[1]), float(a[2]), a[3]
    lo, hi, step = _opt(a, '--lo', 1.2), _opt(a, '--hi', 4.2), _opt(a, '--step', 0.01)
    keep = _opt(a, '--keep', 2, int); until = time.time() + _opt(a, '--seconds', 1200.0)
    W1, W2 = c1 - 1 + f, c2 - 1 + f
    def firsts(c, base):                             # the positions where the taper count steps up
        res = []; prev = -1
        for lam in np.arange(base + lo, base + hi + 1e-9, step):
            N = Z.taper_best(c, f, float(lam))[0]
            if N > prev: res.append(round(float(lam) + 1e-4, 5)); prev = N
        return res
    L1, L2 = firsts(c1, W2), firsts(c2, W1)
    print('%dx%d f %.4f: %d positions on arm 1 (%.3f..%.3f), %d on arm 2 (%.3f..%.3f)' % (c1, c2, f, len(L1), L1[0], L1[-1], len(L2), L2[0], L2[-1]), flush=True)
    mod = ZC.cmod(c1, c2, -1, 1)
    res = collections.defaultdict(list); tried = 0; built = 0
    for hold in ((1,) if c1 == c2 else (1, 2)):          # equal arms: hold 2 is the mirror of hold 1
        for l1 in L1:
            for l2 in L2:
                if time.time() > until: break
                P, n1, n2 = two_tapers(c1, c2, f, l1, l2, hold); tried += 1
                r = ZC.settle_zone(P, mod, f, l1 + 0.004, l2 + 0.004)
                if r is None: continue
                built += 1; N = len(r[2]); L = ZC.loss_of(mod, f, N, r[0], r[1])
                res[N % c1].append((L, N, r[0], r[1], r[2], hold, l1, l2))
    print('pairs tried %d, settled %d' % (tried, built), flush=True)
    recs = []
    for cl in sorted(res):
        rs = sorted(res[cl], key=lambda v: v[0])[:keep]
        for j, (L, N, y0, x0, P, hold, l1, l2) in enumerate(rs):
            cid = 'tt%dx%d-%df%04d%s' % (c1, c2, N, round(f * 10000), 'abcdefgh'[j])
            print('class %d: %s count %d loss %.4f y0 %.6f x0 %.6f (hold %d, lam %.3f %.3f)' % (cl, cid, N, L, y0, x0, hold, l1, l2), flush=True)
            recs.append(dict(id=cid, src='zone_lowf.py corner: two lattice tapers that share the meeting square (our own design)',
                             licence='our own', sig='tt%d.%d.%d' % (hold, round(l1 * 1000), round(l2 * 1000)), count=N, c1=c1, c2=c2,
                             lean1=-1, lean2=1, f=f, y0=y0, x0=x0, P=P))
    try:                                             # the library's corners of these arms near f, for comparison
        lib = pickle.load(open(_opt(a, '--lib', '', str) + '/library.pkl', 'rb'))
        near = [(q['loss0'], q['id'], q['count'], q['f0']) for q in lib['mods'] if q['kind'] == 'corner' and not q['miss']
                and {q['c1'], q['c2']} == {c1, c2} and abs(q['f0'] - f) < 0.03]
        for v in sorted(near)[:4]: print('library corner %s count %d f %.4f loss %.4f' % (v[1], v[2], v[3], v[0]), flush=True)
        if not near: print('library: no corner of these arms within 0.03 of f', flush=True)
    except Exception as e: print('library not read:', e, flush=True)
    pickle.dump(recs, open(out, 'wb'))
    return 0


if __name__ == '__main__':
    cmds = dict(pick=cmd_pick, lens=cmd_lens, join=cmd_join, three=cmd_three, slide=cmd_slide, poke=cmd_poke, rows=cmd_rows,
                corner=cmd_corner)
    sys.exit(cmds[sys.argv[1]](sys.argv[2:]) or 0)
