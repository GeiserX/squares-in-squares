#!/usr/bin/env python3
"""Rectangle corner windows of every layout as parts: alone with plain grid, or two in opposite corners.

The corner rules of this lane use square windows and square parts. The board's 685 is two rectangle parts
that meet in plain columns: a zone 17 + f wide and 10 + f high with 5 squares more than the grid, and a zone
9 + f wide and 16 + f high with 4 more (section 13.1). A rectangle window can hold more squares above the grid
than the square window around it, when the strip between them is below the grid.

A corner window of a layout is the set of squares that lie whole in [0, w + F] x [0, h + F] after one of the
8 symmetries; w and h are integers and 0 <= F < 1. Its excess is e = count - w*h.

  single: the window in the corner of an m x m grid (m >= w, h) is a layout of m*m + e squares at side m + F.
  pair:   window A (wA, hA, eA) at the top left and window B (m - wA, m - hA, eB) at the bottom right, with
          plain grid in the other two blocks, is a layout of m*m + eA + eB at side m + max(FA, FB) when the
          squares of A and B do not collide where the two boxes overlap.

Usage: forensics_rect.py DETAILS.csv OUT_DIR [--keep 6] [--bar 2e-10] [--only N,..] [--raise N:DS,..]
                          [--slack DS] [--per-n K] FILE.csv [...]
  FILE.csv in the submission layout (id,n,square_id,x,y,angle) or the per-n layout (n,square_id,x,y,angle).
  --raise N:DS adds DS to the side to beat of n (positive controls only).
  --slack DS   keeps every composition up to DS above the side to beat of its n (a start for an fq polish:
               in round 21 the polish took the 749 pair 1.19e-3 lower in side, 30 times its margin).
  --per-n K    writes up to K compositions of distinct side per n (default 1, the lowest).
  --max-mesh M tries at most M pairs per n, lowest side first (default 400).
  --strict-single keeps single windows only below the true bar, even when pairs use slack.
  --no-single  skips the single rule (with --slack it keeps every layout's own corner, a requench of the merge).
  --collide D  also writes pairs whose parts collide by less than D (worst overlap depth), as starts for the
               default fq quench (loosen, ALM, polish), tagged c; up to --per-n of them per n.
  --skip-ties  skips pairs whose side is the side to beat within 2e-8 (a part is the best layout itself; in round 21
               118 of 216 kept pairs were such ties and none moved under the polish).
  --cache FILE stores the window table and skips layouts already read (trusted local pickle only).
  --fresh-only tries only pairs containing a window read in this run.
  --fresh-start N resumes a cached fresh-source range at index N, with --fresh-only.
  --archive DIR keeps an immutable per-layout snapshot of every new donor.
  --gap FILE orders targets by their current score gap to board_L in a TSV.
  --f-sep D keeps at most --per-cluster (default 2) windows per rounded F/D bin.
  --rescan-cache rebuilds the table from cached source arrays, without reading their files.
Writes OUT_DIR/<n>-<tag>.csv for every layout kept and prints one line each.
"""
import sys, os, csv, math, collections, time, pickle, hashlib, json
import numpy as np
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1, '.')
import forensics_compose as fc
import forensics_pool as fp

TOL = 1e-9
WMAX = 32



def write_cache(path, value):
    """Replace a whole cache through a temporary file unique to this writer."""
    import tempfile
    path = Path(path)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            pickle.dump(value, handle)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def opt(argv, name, default):
    if name in argv:
        i = argv.index(name); v = argv[i + 1]; del argv[i:i + 2]; return v
    return default


def layouts(p):
    L = collections.defaultdict(list)
    with open(p) as h:
        for r in csv.DictReader(h):
            try:
                L[int(r['n'])].append((fp.fnum(r['x']), fp.fnum(r['y']), fp.fnum(r['angle'])))
            except (KeyError, ValueError, TypeError, AttributeError):
                continue
    return {n: v for n, v in L.items() if len(v) == n}


def sym8(Q, s):
    """(tag, squares in the frame of the symmetry) for the 8 symmetries; the window corner is the origin."""
    for g in range(8):
        R = Q.copy()
        if g & 1:
            R[:, 0] = s - R[:, 0]; R[:, 2] = -R[:, 2]
        if g & 2:
            R[:, 1] = s - R[:, 1]; R[:, 2] = -R[:, 2]
        if g & 4:
            R[:, [0, 1]] = R[:, [1, 0]]; R[:, 2] = math.pi / 2 - R[:, 2]
        yield g, R


def select_windows(values, indices, keep, fsep=0.0, per_cluster=2):
    """Lowest windows, optionally reserving slots for distinct side fractions."""
    order = np.argsort(values, axis=1, kind='stable')
    fs = np.take_along_axis(values, order, 1)
    ids = np.take_along_axis(indices, order, 1)
    if not fsep:
        return fs[:, :keep], ids[:, :keep]
    bins = np.round(np.where(np.isfinite(fs), fs, 0.) / fsep)
    width = fs.shape[1]
    prior = np.tril(np.ones((width, width), bool))
    counts = np.sum((bins[:, :, None] == bins[:, None, :]) & prior, axis=2)
    eligible = np.isfinite(fs) & (counts <= per_cluster)
    rank = np.where(eligible, np.arange(width)[None, :], width)
    chosen = np.argsort(rank, axis=1, kind='stable')[:, :keep]
    valid = np.take_along_axis(eligible, chosen, 1)
    return (np.where(valid, np.take_along_axis(fs, chosen, 1), np.inf),
            np.where(valid, np.take_along_axis(ids, chosen, 1), -1))


def main(argv):
    excluded_source_n = {int(x) for x in opt(argv, '--exclude-source-n', '').split(',') if x}
    keep = int(opt(argv, '--keep', '6')); bar = float(opt(argv, '--bar', '2e-10'))
    only = opt(argv, '--only', ''); only = set(int(x) for x in only.split(',')) if only else None
    rz = opt(argv, '--raise', '')
    slack = float(opt(argv, '--slack', '0')); per_n = int(opt(argv, '--per-n', '1'))
    max_mesh = int(opt(argv, '--max-mesh', '400'))
    strict_single = '--strict-single' in argv
    if strict_single:
        argv.remove('--strict-single')
    no_single = '--no-single' in argv
    if no_single:
        argv.remove('--no-single')
    collide = float(opt(argv, '--collide', '0'))
    skip_ties = '--skip-ties' in argv
    if skip_ties:
        argv.remove('--skip-ties')
    cache = opt(argv, '--cache', '')
    archive = opt(argv, '--archive', '')
    gap_csv = opt(argv, '--gap', '')
    fsep = float(opt(argv, '--f-sep', '0'))
    per_cluster = int(opt(argv, '--per-cluster', '2'))
    rescan = '--rescan-cache' in argv
    if rescan:
        argv.remove('--rescan-cache')
    fresh_only = '--fresh-only' in argv
    if fresh_only:
        argv.remove('--fresh-only')
    fresh_since = opt(argv, '--fresh-start', '')
    details, out, files = argv[1], argv[2], argv[3:]
    os.makedirs(out, exist_ok=True)
    D = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    for t in (rz.split(',') if rz else []):
        a, b = t.split(':'); D[int(a)] += float(b)
    # side to beat as a fraction over m, less the padding; grids are never targets
    ft = {}
    for n in range(2, 1001):
        m, k = fc.mk(n)
        if k and (only is None or n in only):
            ft[n] = D[n] - m - bar * math.sqrt(n)
    beat = {n: m_f + math.isqrt(n) for n, m_f in ft.items()}   # the true side to beat, for the log
    ft = {n: v + slack for n, v in ft.items()}
    # G[e][m0]: the most lenient target m*m + e with m >= m0 (single rule)
    G = np.full((70, WMAX + 2), -1.0); GN = np.zeros((70, WMAX + 2), int)
    for e in range(1, 70):
        best, bn = -1.0, 0
        for m0 in range(WMAX + 1, 0, -1):
            n = m0 * m0 + e
            if e <= 2 * m0 and n in ft and ft[n] > best:
                best, bn = ft[n], n
            G[e, m0] = best; GN[e, m0] = bn
    t0 = time.time()
    # table of the lowest windows per (w, h, e): TF holds F, TI the layout index * 8 + symmetry, best first
    E = 69
    TF = np.full((WMAX + 2, WMAX + 2, E + 1, keep), np.inf); TI = np.full(TF.shape, -1, int)
    Gwh = np.full((WMAX + 2, WMAX + 2, E + 1), -1.0)
    for w in range(1, WMAX + 1):
        for h in range(1, WMAX + 1):
            Gwh[w, h, 1:] = G[1:, max(w, h)]
    src = []; single = []; seen = set()
    if cache and os.path.exists(cache):
        saved = pickle.load(open(cache, 'rb'))
        if saved['keep'] != keep:
            raise ValueError('cache --keep differs')
        TF, TI, src, seen = saved['TF'], saved['TI'], saved['src'], saved['seen']
    prior_sources = []
    if rescan:
        prior_sources = src
        TF = np.full(TF.shape, np.inf); TI = np.full(TI.shape, -1, int)
        src = []; seen = set()
    initial_sources = len(src)
    fresh_start = int(fresh_since) if fresh_since else initial_sources
    if not 0 <= fresh_start <= max(initial_sources, len(prior_sources)):
        raise ValueError('--fresh-start outside cached source range')

    def input_layouts():
        for (key, side, q) in prior_sources:
            yield key[0], {key[1]: q}
        for path in files:
            try:
                yield path, layouts(path)
            except OSError as error:
                print('skip vanished donor', path, error, flush=True)

    for p, loaded in input_layouts():
        for n0, sq in loaded.items():
            if n0 in excluded_source_n:
                continue
            s, Q = fc.frame(sq)
            digest = (n0, hashlib.sha256(np.round(Q, 12).tobytes()).hexdigest())
            if digest in seen:
                continue
            seen.add(digest)
            source = p
            if archive:
                os.makedirs(archive, exist_ok=True)
                source = os.path.join(archive, '%d-%s.csv' % (n0, digest[1][:20]))
                if (not os.path.exists(source) or not os.path.exists(source + '.origin.json') or
                        os.path.getsize(source + '.origin.json') == 0):
                    receipt = dict(path=p, n=n0, digest=digest[1])
                    if 'take-forensics-r24' in archive:
                        import forensics_sources
                        scratch = Path(archive).parents[2]
                        ok, ancestry = forensics_sources.trace(p, n0, scratch)
                        if not ok:
                            print('skip donor whose ancestry changed', p, flush=True)
                            seen.discard(digest)
                            continue
                        receipt.update(verified_ancestry=True, ancestry=ancestry)
                    fc.write_csv(source + '.tmp', n0, np.array(sq))
                    if receipt.get('verified_ancestry'):
                        receipt['snapshot_sha256'] = hashlib.sha256(Path(source + '.tmp').read_bytes()).hexdigest()
                    with open(source + '.origin.json.tmp', 'w') as origin:
                        json.dump(receipt, origin)
                    os.replace(source + '.tmp', source)
                    os.replace(source + '.origin.json.tmp', source + '.origin.json')
            li = len(src); src.append(((source, n0), s, Q))
            mm = min(WMAX, int(math.ceil(s - 1e-9)))
            W = np.arange(1, mm + 1)
            c0 = (W[:, None] * W[None, :]).reshape(-1)
            ranks = c0[:, None] + np.arange(E)[None, :]              # count w*h + e for e = 1..E
            valid = ranks < n0
            ranks = np.minimum(ranks, n0 - 1)
            for g, R in sym8(Q, s):
                K = fc.corners(R)
                ex = K[:, :, 0].max(1); ey = K[:, :, 1].max(1)
                d = np.maximum(ex[None, None, :] - W[:, None, None], ey[None, None, :] - W[None, :, None]).reshape(mm * mm, -1)
                d.sort(axis=1)
                F = np.maximum(np.take_along_axis(d, ranks, axis=1), 0.0)
                F[~valid] = np.inf; F[F >= 1.0 - 1e-9] = np.inf
                F = F.reshape(mm, mm, E)
                # single rule
                hit = F < Gwh[1:mm + 1, 1:mm + 1, 1:]
                for wi, hi, ei in zip(*np.nonzero(hit)):
                    w, h, e = wi + 1, hi + 1, ei + 1
                    single.append((int(GN[e, max(w, h)]), float(F[wi, hi, ei]), w, h, e, li, g))
                # table update where the new window is below the K-th
                cur = TF[1:mm + 1, 1:mm + 1, 1:]
                imp = F < cur[..., -1]
                if imp.any():
                    ii = np.nonzero(imp)
                    catF = np.concatenate([cur[ii], F[ii][:, None]], 1)
                    catI = np.concatenate([TI[1:mm + 1, 1:mm + 1, 1:][ii], np.full((len(ii[0]), 1), li * 8 + g)], 1)
                    fs, ids = select_windows(catF, catI, keep, fsep, per_cluster)
                    sub = (ii[0] + 1, ii[1] + 1, ii[2] + 1)
                    TF[sub] = fs; TI[sub] = ids
    if cache:
        write_cache(cache, dict(keep=keep, TF=TF, TI=TI, src=src, seen=seen))
    import forensics_predict
    predictions = forensics_predict.predict(src, TF, initial_sources, D, os.path.join(out, 'quartic-predictions.json'))
    print('quartic side-qualified predictions %d, before pair assembly' % len(predictions), flush=True)
    print('layouts %d, new %d, %.0f s' % (len(src), len(src) - initial_sources, time.time() - t0), flush=True)
    found = {}; sides = collections.defaultdict(set); csides = collections.defaultdict(set)

    def part(li, g, w, h, e, f):
        key, s0, Q0 = src[li]; R = dict(sym8(Q0, s0))[g]; K = fc.corners(R)
        sel = np.nonzero(np.maximum(K[:, :, 0].max(1) - w, K[:, :, 1].max(1) - h) <= f + 1e-15)[0][:w * h + e]
        return key, R[sel].copy()

    pair_meta = None

    def record(path):
        with open(path + '.json.tmp', 'w') as handle:
            json.dump(pair_meta, handle, default=lambda value: value.item())
        os.replace(path + '.json.tmp', path + '.json')

    def keep_valid(n, side, X, tag, _beat):
        key = round(side, 9)
        if key in sides[n] or len(sides[n]) >= per_n:
            return
        Kx = fc.corners(X)
        if len(X) != n or Kx.min() < -TOL or Kx.max() > side + TOL:
            print('  invalid: count %d box %.3g %.3g' % (len(X), Kx.min(), Kx.max() - side)); return
        wo = fc.worst_overlap(X)
        if wo < -TOL:
            print('  invalid: overlap %.3g' % wo); return
        sides[n].add(key); found[n] = min(found.get(n, 99.0), side)
        path = '%s/%d-%s-%.9f.csv' % (out, n, tag, side) if per_n > 1 else '%s/%d-%s.csv' % (out, n, tag)
        fc.write_csv(path + '.tmp', n, X); os.replace(path + '.tmp', path); record(path)
        print('  VALID n=%d side %.10f (beat %.10f, %+.3e)' % (n, side, beat[n], side - beat[n]), flush=True)

    # single rule: the window in the corner of an m x m grid
    for n, f, w, h, e, li, g in ([] if no_single else sorted(single, key=lambda x: x[1] - ft[x[0]])):
        if fresh_only and li < fresh_start:
            continue
        m = math.isqrt(n); side = m + f
        if strict_single and side >= beat[n]:
            continue
        if len(sides[n]) >= per_n:
            continue
        key, P = part(li, g, w, h, e, f)
        pair_meta = dict(kind='single rectangle window', n=n, side=side,
                         A=dict(source=key, sym=int(g), w=w, h=h, excess=e))
        print('single n=%d m=%d e=%d window %dx%d F=%.10f target f=%.10f from %s sym %d' % (n, m, e, w, h, f, ft[n], key, g), flush=True)
        grid = [(i + 0.5 + f, j + 0.5, 0.0) for i in range(w, m) for j in range(m)] + [(i + 0.5, j + 0.5 + f, 0.0) for i in range(w) for j in range(h, m)]
        keep_valid(n, side, np.r_[P, np.array(grid).reshape(-1, 3)], 's%dx%d' % (w, h), m + ft[n])
    # pair rule: A at the top left, B at the bottom right
    Fb = TF[..., 0]
    npair = 0; nmesh = 0
    order = sorted(ft)
    if gap_csv:
        board = {int(r['n']): float(r['board_L']) for r in csv.DictReader(open(gap_csv), delimiter='\t')}
        order.sort(key=lambda n: (-(D[n] - board.get(n, D[n])) / math.sqrt(n), n))
    for n in order:
        m, k = fc.mk(n)
        if m < 2 or m > WMAX or k < 2:
            continue
        f_t = ft[n]
        A = Fb[1:m, 1:m, 1:k]                       # wA, hA, eA
        B = Fb[m - 1:0:-1, m - 1:0:-1, k - 1:0:-1]  # m-wA, m-hA, k-eA
        ok = (A < f_t) & (B < f_t)
        cand = []
        for wa, ha, ea in zip(*np.nonzero(ok)):
            wA, hA, eA = wa + 1, ha + 1, ea + 1; wB, hB, eB = m - wA, m - hA, k - eA
            npair += 1
            for ia in range(keep):
                fA = TF[wA, hA, eA, ia]
                if not fA < f_t:
                    break
                for ib in range(keep):
                    fB = TF[wB, hB, eB, ib]
                    if not fB < f_t:
                        break
                    if fresh_only and TI[wA, hA, eA, ia] // 8 < fresh_start and TI[wB, hB, eB, ib] // 8 < fresh_start:
                        continue
                    if skip_ties and abs(max(fA, fB) - (D[n] - m)) < 2e-8:
                        continue
                    cand.append((max(fA, fB), wA, hA, eA, ia, ib))
        cand.sort()                                 # lowest side first, at most --max-mesh tries per n
        for f, wA, hA, eA, ia, ib in cand[:max_mesh]:
            if len(sides[n]) >= per_n:
                break
            wB, hB, eB = m - wA, m - hA, k - eA
            fA, ga = TF[wA, hA, eA, ia], TI[wA, hA, eA, ia]; fB, gb = TF[wB, hB, eB, ib], TI[wB, hB, eB, ib]
            side = m + f; nmesh += 1
            kA, PA = part(ga // 8, ga % 8, wA, hA, eA, fA); PA[:, 1] = side - PA[:, 1]; PA[:, 2] = -PA[:, 2]
            kB, PB = part(gb // 8, gb % 8, wB, hB, eB, fB); PB[:, 0] = side - PB[:, 0]; PB[:, 2] = -PB[:, 2]
            pair_meta = dict(n=n, side=side, A=dict(source=kA, sym=int(ga % 8), w=wA, h=hA, excess=eA),
                             B=dict(source=kB, sym=int(gb % 8), w=wB, h=hB, excess=eB))
            wo = fc.worst_overlap(PA, PB)
            print('pair n=%d m=%d A %dx%d+%d F=%.8f %s/%d  B %dx%d+%d F=%.8f %s/%d  target f=%.8f  overlap %.3g' % (
                n, m, wA, hA, eA, fA, kA, ga % 8, wB, hB, eB, fB, kB, gb % 8, f_t, wo), flush=True)
            grid = [(i + 0.5, j + 0.5, 0.0) for i in range(wA) for j in range(hB)] + \
                   [(side - 0.5 - i, side - 0.5 - j, 0.0) for i in range(wB) for j in range(hA)]
            if wo < -TOL:
                if collide and wo > -collide and len(csides[n]) < per_n and round(side, 9) not in csides[n]:
                    X = np.r_[PA, PB, np.array(grid).reshape(-1, 3)]
                    if len(X) == n:
                        csides[n].add(round(side, 9))
                        path = '%s/%d-c%dx%d-%.9f.csv' % (out, n, wA, hA, side)
                        fc.write_csv(path + '.tmp', n, X); os.replace(path + '.tmp', path); record(path)
                        print('  START n=%d side %.10f overlap %.3g (beat %.10f)' % (n, side, wo, beat[n]), flush=True)
                continue
            keep_valid(n, side, np.r_[PA, PB, np.array(grid).reshape(-1, 3)], 'p%dx%d' % (wA, hA), m + f_t)
    print('single candidates %d, pair candidates %d, meshes tried %d, valid n %d: %s, colliding starts %d  (%.0f s)' % (
        len(single), npair, nmesh, len(found), sorted(found), sum(len(v) for v in csides.values()), time.time() - t0))


if __name__ == '__main__':
    main(sys.argv[:])
