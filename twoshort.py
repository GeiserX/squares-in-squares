#!/usr/bin/env python3
"""The two-short slice (m 28 to 31, k 5 to 16): what loss a side allows for every pair of arm sizes, and which pairs pay.

  twoshort.py table  GAP.tsv [--m 28-31] [--k 5-16] [--c 6-16]        the loss a side allows by (c1, c2), board and held
  twoshort.py held   HELD.csv GAP.tsv [--m 28-31] [--k 5-16]           what each held layout of the slice is
  twoshort.py far    C F [--lo 1.5] [--hi 9] [--step 0.01] [--refine 4] [--build N] [--save DIR]
                                                                       the lattice far zones of an arm of C by count class
  twoshort.py pay    GAP.tsv ZONES.tsv FAR.tsv [--c 6-15] [--corner 8x9=2.72,..] [--out TSV]
                                                                       the margin of every pair at every n of the slice

The model is the one of modules.py: a stack of c squares is flush in a strip of width c - 1 + f, an arm of
flush stacks holds g = f - sin t squares more per unit of wall than c - 1 grid columns, and two arms that are
flush from end to end hold m^2 + k_flush squares. The implied loss of a side is k_flush - k: what the three end
zones (one corner, two far ends) may cost at that side.

Our own code. Reads tables as data only. Imports modules.py of this lane.
"""
import argparse, collections, csv, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from modules import flush_tilt, k_flush


def span(s):
    a, b = s.split('-'); return int(a), int(b)


def slice_rows(path, ms, ks):
    out = []
    for r in csv.DictReader(open(path), delimiter='\t'):
        m, k = int(r['m']), int(r['k'])
        if ms[0] <= m <= ms[1] and ks[0] <= k <= ks[1]:
            out.append(dict(n=int(r['n']), m=m, k=k, ours=float(r['ours_L']), board=float(r['board_L']), gap=float(r['score_gap'])))
    return out


def gain(c, f):
    return f - math.sin(flush_tilt(c, f))


def cmd_table(a):
    rows = slice_rows(a.gap, span(a.m), span(a.k)); c0, c1 = span(a.c)
    cs = list(range(c0, c1 + 1))
    print('g = f - sin t by c at f = 0.62: ' + ' '.join('%d:%.3f' % (c, gain(c, 0.62)) for c in cs))
    for r in rows:
        fb, fh = r['board'] - r['m'], r['ours'] - r['m']
        print('n %d  m %d k %d  board f %.4f  held f %.4f  score gap %.2e' % (r['n'], r['m'], r['k'], fb, fh, r['gap']))
        print('   c1\\c2 ' + ' '.join('%11d' % c for c in cs))
        for ca in cs:
            print('   %5d ' % ca + ' '.join('%5.2f/%5.2f' % (k_flush(r['m'], fb, ca, cb) - r['k'], k_flush(r['m'], fh, ca, cb) - r['k']) for cb in cs))


def zone_table(path):
    """results/zones-*.tsv -> far[c] = [(f, class, count, loss)], corner[(c1, c2)] = [(f, count, loss)]"""
    far = collections.defaultdict(list); cor = collections.defaultdict(list)
    for r in csv.DictReader(open(path), delimiter='\t'):
        try:
            f = float(r['f']); loss = float(r['loss']); cnt = int(r['count'])
        except (ValueError, KeyError):
            continue
        if r['kind'] == 'far':
            far[int(r['c'])].append((f, cnt % int(r['c']), cnt, loss))
        elif r['kind'] == 'corner':
            c = r['c'].replace('x', ' ').replace(',', ' ').split()
            if len(c) == 2: cor[(int(c[0]), int(c[1]))].append((f, cnt, loss))
    return far, cor


def cmd_held(a):
    import modules
    from frontier_read import normal
    from frontier_stacks import stacks
    rows = slice_rows(a.gap, span(a.m), span(a.k))
    P = modules.read_layouts(a.held)
    for r in rows:
        n = r['n']; sq = P[n]
        s, A = normal(sq); m = r['m']; f = s - m
        T = A[np.abs(A[:, 2]) > 0.5]
        hist = collections.Counter()
        if len(T) >= 2:
            chains, _ = stacks(T)
            for ch in chains: hist[len(ch)] += 1
        d, why = modules.cut(sq, n)
        arms = modules.arms_at(A, s, m, 0.05)
        ang = collections.Counter(int(round(abs(x))) for x in T[:, 2])
        print('n %d m %d k %d f %.4f tilted %d cut %s arms(tol .05) %s chains %s angles %s' % (
            n, m, r['k'], f, len(T), ('%dx%d s %d,%d' % (d['c1'], d['c2'], d['s1'], d['s2'])) if d else why,
            [(w, c, len(p)) for w, c, t, p in arms], dict(sorted(hist.items())), dict(ang.most_common(4))))

BEAM = int(os.environ.get("TWOSHORT_BEAM", "200000"))   # states kept after each slab (the result is then an upper bound of the lowest loss)


def taper_count(c, f, lam, want=False):
    """The largest count of the lattice tapers of zone_search.taper_sites at stack position lam. It is the dynamic
    programme of zone_search.taper_best, run once for every split kl of the c - 1 upright columns (kl against the
    wall, the others against the grid). A split needs only the heights of its own c - 1 columns as the state, where
    taper_best keeps all 2 (c - 1) in one 64-bit key, which an arm of 11 or more overflows. So the state is half as
    long and the programme is exact for wide arms too; BEAM is a guard that the log reports when it cuts.
    -> (count, states at most, cut), and with want also the squares (x, y, degrees) of the best taper."""
    import zone_search as Z
    S = Z.taper_sites(c, f, lam)
    fl = lambda v: np.where(np.isinf(v), 9, np.clip(np.floor(np.minimum(v, 8.0) + 1e-9), 0, 8)).astype(np.int64)
    m = c - 1
    c0 = fl(S[0][0][3]); OC = [fl(np.array([o[3] for o in opts])) for opts in S[1:]]
    ON = [np.array([o[1] - o[0] + 1 for o in opts]) for opts in S[1:]]
    best = (-1, None); big = 0; cut = False
    for kl in range(m + 1):
        cols = np.r_[np.arange(kl), m + np.arange(m - kl)].astype(int)
        caps = c0[cols][None, :]; cnt = np.zeros(1, int); idx = [np.zeros(1, int)]
        pw = 10 ** np.arange(m, dtype=np.int64)
        for oc_all, on in zip(OC, ON):
            oc = oc_all[:, cols]; k = len(cnt)
            caps = np.minimum(caps[:, None, :], oc[None, :, :]).reshape(-1, m)
            cnt = (cnt[:, None] + on[None, :]).ravel()
            key = caps @ pw
            o = np.lexsort((-cnt, key))
            first = np.r_[True, key[o][1:] != key[o][:-1]]
            sel = o[first]
            if len(sel) > BEAM:
                sel = sel[np.argsort(-(cnt[sel] + np.where(caps[sel] >= 9, 0, caps[sel]).sum(1)))[:BEAM]]; cut = True
            if want: idx = [np.repeat(q, len(on))[sel] for q in idx] + [np.tile(np.arange(len(on)), k)[sel]]
            caps, cnt = caps[sel], cnt[sel]; big = max(big, len(cnt))
        hts = np.where(caps >= 9, 0, caps)
        tot = cnt + hts.sum(1); q = int(np.argmax(tot))
        if tot[q] > best[0]: best = (int(tot[q]), (kl, hts[q].copy(), [int(i[q]) for i in idx]) if want else None)
    if not want: return best[0], big, cut
    kl, hts, path = best[1]
    t = flush_tilt(c, f); W = c - 1 + f
    sq = []
    for jj, opts in enumerate(S[1:]):
        sq += [(x, y, -math.degrees(t)) for x, y in opts[path[jj + 1]][2]]
    for i in range(kl): sq += [(i + 0.5, 0.5 + r, 0.0) for r in range(hts[i])]
    for i in range(m - kl): sq += [(W - 0.5 - i, 0.5 + r, 0.0) for r in range(hts[kl + i])]
    return best[0], big, cut, np.array(sq)


def cmd_far(a):
    """The lattice far zones of an arm of C at F: for every count class the lowest loss c cos t lam - count."""
    import time
    c, f = a.c_arm, a.f
    t = flush_tilt(c, f); cc = c * math.cos(t)
    first = {}; prev = 0; t0 = time.time(); big = 0; cuts = 0
    a.lo = max(a.lo, c / 2 * math.sin(t) + math.cos(t) / 2 - 0.5 / math.cos(t) + a.step)    # below this the flush stack crosses the end wall
    for lam in np.arange(a.lo, a.hi + 1e-9, a.step):
        N, ns, cu = taper_count(c, f, float(lam)); big = max(big, ns); cuts += cu
        for n in range(prev + 1, N + 1):
            if N == n and lam > a.lo + 1e-9: first[n] = float(lam)
        prev = max(prev, N)
    best = {}
    for n, lam in first.items():
        loss = cc * lam - n
        if n % c not in best or loss < best[n % c][0]: best[n % c] = (loss, n, lam)
    for cl in sorted(best, key=lambda q: best[q][0])[:a.refine]:      # the position of the best classes, by bisection
        _, n, hi = best[cl]; lo = hi - a.step
        for _ in range(8):
            mid = (lo + hi) / 2
            if taper_count(c, f, mid)[0] >= n: hi = mid
            else: lo = mid
        best[cl] = (cc * hi - n, n, hi)
    built = {}
    if a.build:                                                       # the best classes as squares, squeezed and compacted
        import zone_search as Z, pickle
        for cl in sorted(best, key=lambda q: best[q][0])[:a.build]:
            _, n, lam = best[cl]
            N, _, _, sq = taper_count(c, f, lam + 1e-9, want=True)
            if N < n or len(sq) < n: continue
            sq = sq[:n] if len(sq) == n else sq
            try: r = Z.settle_zone(sq, c, f, lam + 0.004)
            except Exception as ex: r = None; print('# build of %d failed: %s' % (n, ex), flush=True)
            if r is None or len(sq) != n: continue
            built[cl] = (cc * r[0] - n, r[0])
            if a.save:
                os.makedirs(a.save, exist_ok=True)
                pickle.dump(dict(c=c, f=f, count=n, lam=r[0], P=r[1], how='twoshort.py far: lattice taper, squeezed and compacted'),
                            open('%s/zt%d-%df%03d.pkl' % (a.save, c, n, round(f * 1000)), 'wb'))
    for cl in sorted(best):
        bl = built.get(cl)
        print('far\t%d\t%.3f\t%d\t%d\t%.4f\t%.4f\t%s\t%s' % (c, f, cl, best[cl][1], best[cl][2], best[cl][0],
              '' if bl is None else '%.4f' % bl[1], '' if bl is None else '%.4f' % bl[0]), flush=True)
    print('# c %d f %.3f: %.0f s, %d states at most, the beam cut at %d positions, lowest lattice loss %.3f' % (c, f, time.time() - t0, big, cuts, min(v[0] for v in best.values())), flush=True)


CORNER_LINE = (0.55, -6.3)        # the lower line through the library's corners below f = 0.82: loss = 0.55 (c1 + c2) - 6.3


def flip_cost(ca, cb, f):
    """k_flush(m, f, cb, ca) - k_flush(m, f, ca, cb): the same layout seen from the other wall (it does not depend on m).
    A corner of loss x in the labelling (cb, ca) has the loss x - flip_cost(ca, cb, f) in the labelling (ca, cb)."""
    return gain(cb, f) * (ca - 1 + f) - gain(ca, f) * (cb - 1 + f) + (cb - ca) * f


def far_table(path, built=True):
    """rows of `far` -> far[c][f] = {class: (loss, count)}; the built loss where the row has one"""
    far = collections.defaultdict(lambda: collections.defaultdict(dict))
    for ln in open(path):
        w = ln.rstrip('\n').split('\t')
        if w[0] != 'far': continue
        c, f, cl, n = int(w[1]), float(w[2]), int(w[3]), int(w[4])
        loss = float(w[8]) if built and len(w) > 8 and w[8] else float(w[6])
        if cl not in far[c][f] or loss < far[c][f][cl][0]: far[c][f][cl] = (loss, n)
    return far


def cmd_pay(a):
    """The margin of every pair at every n of the slice: the loss the held (and the board's) side allows, less the best
    far zone of each arm at that f (FAR.tsv, rows of `far`), less a corner. Pairs are taken with the narrower arm as
    arm 1 (the other labelling is the same layout). The corner is the library's lowest loss below f = 0.82 for a pair
    it holds in either labelling (ZONES.tsv), else the lower line. --corner gives the loss of corners we built: such a
    corner takes the place of the line, and of a library corner that loses more."""
    rows = slice_rows(a.gap, span(a.m), span(a.k)); c0, c1 = span(a.c); cs = list(range(c0, c1 + 1))
    ft = far_table(a.far)
    far = {c: {f: min(v[0] for v in ft[c][f].values()) for f in ft[c]} for c in ft}
    zfar, cor = zone_table(a.zones)
    zf = collections.defaultdict(dict)                       # the zone table's far zones (built and measured), lowest loss by f
    for c, v in zfar.items():
        for f, cl, n, l in v: zf[c][f] = min(zf[c].get(f, 9e9), l)
    def far_at(c, f):
        out = []
        for tab in (far, zf):
            if c in tab and tab[c]:
                fs = sorted(tab[c]); out.append(float(np.interp(f, fs, [tab[c][x] for x in fs])))
        return min(out)
    lib = {}
    for (ca, cb), v in cor.items():
        for f, n, l in v:
            if f >= 0.82: continue
            key, val = ((ca, cb), l) if ca <= cb else ((cb, ca), l - flip_cost(cb, ca, f))
            if key not in lib or val < lib[key][0]: lib[key] = (val, f, '%dx%d' % (ca, cb))
    meas = {}                                                # --corner 8x9=2.72,...: corners we built, narrower arm first
    for s in (a.corner or '').split(','):
        if s: meas[tuple(int(x) for x in s.split('=')[0].split('x'))] = float(s.split('=')[1])
    def corner(ca, cb):
        if (ca, cb) in lib and lib[(ca, cb)][0] <= meas.get((ca, cb), 9e9): return lib[(ca, cb)][0], 'lib'
        if (ca, cb) in meas: return meas[(ca, cb)], 'built'
        return CORNER_LINE[0] * (ca + cb) + CORNER_LINE[1], 'line'
    print('library corners below f = 0.82, narrower arm first (loss, f, labelled in the library): ' +
          ' '.join('%dx%d:%.2f@%.3f(%s)' % (p[0], p[1], v[0], v[1], v[2]) for p, v in sorted(lib.items())))
    print('the line at these pairs: ' + ' '.join('%dx%d:%.2f' % (p[0], p[1], CORNER_LINE[0] * sum(p) + CORNER_LINE[1]) for p in sorted(lib)))
    print('far zones, lowest loss by c at f = 0.62, 0.66, 0.70, 0.74: ' + ' | '.join('%d: %s' % (c, ' '.join('%.2f' % far_at(c, f) for f in (0.62, 0.66, 0.70, 0.74))) for c in cs))
    out = []
    for r in rows:
        fb, fh = r['board'] - r['m'], r['ours'] - r['m']
        for ca in cs:
            for cb in cs:
                if cb < ca: continue
                co, how = corner(ca, cb)
                mh = k_flush(r['m'], fh, ca, cb) - r['k'] - far_at(ca, fh) - far_at(cb, fh) - co
                mb = k_flush(r['m'], fb, ca, cb) - r['k'] - far_at(ca, fb) - far_at(cb, fb) - co
                out.append((mh, mb, r['n'], r['m'], r['k'], fh, fb, ca, cb, how))
    for lo in (9, 10, 11, 12):
        wide = [o for o in out if o[8] >= lo]
        if not wide: continue
        b = max(wide)
        print('pairs with an arm of %d or more: %d rows; margin on held above 0.3: %d rows on %d n, above 0: %d rows on %d n; best %+.2f (n %d, %dx%d, corner %s); best on the board %+.2f' % (
            lo, len(wide), sum(o[0] > 0.3 for o in wide), len({o[2] for o in wide if o[0] > 0.3}), sum(o[0] > 0 for o in wide),
            len({o[2] for o in wide if o[0] > 0}), b[0], b[2], b[7], b[8], b[9], max(o[1] for o in wide)))
    print('n\tm\tk\theld f\tboard f\tbest pair (margin on held, on the board, corner)\tbest pair with an arm of 10 or more\ttwo 8-arms')
    for r in rows:
        mine = [o for o in out if o[2] == r['n']]
        b = max(mine); w = max(o for o in mine if o[8] >= 10); e = next(o for o in mine if o[7] == 8 and o[8] == 8)
        fm = lambda o: '%dx%d %+.2f %+.2f %s' % (o[7], o[8], o[0], o[1], o[9])
        print('%d\t%d\t%d\t%.4f\t%.4f\t%s\t%s\t%s' % (r['n'], r['m'], r['k'], b[5], b[6], fm(b), fm(w), fm(e)))
    # by pair: the median and the best margin over the slice
    print('pair\tcorner\tmedian margin on held\tbest\tmedian on the board\tbest')
    for ca in cs:
        for cb in cs:
            mine = [o for o in out if o[7] == ca and o[8] == cb]
            if not mine: continue
            print('%dx%d\t%s\t%+.2f\t%+.2f\t%+.2f\t%+.2f' % (ca, cb, mine[0][9], float(np.median([o[0] for o in mine])), max(o[0] for o in mine),
                                                         float(np.median([o[1] for o in mine])), max(o[1] for o in mine)))
    if a.out:
        with open(a.out, 'w') as h:
            h.write('n\tm\tk\theld_f\tboard_f\tc1\tc2\tmargin_held\tmargin_board\tcorner\n')
            for o in sorted(out, key=lambda o: (o[2], o[7], o[8])):
                h.write('%d\t%d\t%d\t%.4f\t%.4f\t%d\t%d\t%.3f\t%.3f\t%s\n' % (o[2], o[3], o[4], o[5], o[6], o[7], o[8], o[0], o[1], o[9]))


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('table'); p.add_argument('gap'); p.add_argument('--m', default='28-31'); p.add_argument('--k', default='5-16'); p.add_argument('--c', default='6-16'); p.set_defaults(fn=cmd_table)
    p = sub.add_parser('held'); p.add_argument('held'); p.add_argument('gap'); p.add_argument('--m', default='28-31'); p.add_argument('--k', default='5-16'); p.set_defaults(fn=cmd_held)
    p = sub.add_parser('far'); p.add_argument('c_arm', type=int); p.add_argument('f', type=float); p.add_argument('--lo', type=float, default=1.5)
    p.add_argument('--hi', type=float, default=9.0); p.add_argument('--step', type=float, default=0.01); p.add_argument('--refine', type=int, default=4); p.add_argument('--build', type=int, default=0); p.add_argument('--save'); p.set_defaults(fn=cmd_far)
    p = sub.add_parser('pay'); p.add_argument('gap'); p.add_argument('zones'); p.add_argument('far'); p.add_argument('--m', default='28-31'); p.add_argument('--k', default='5-16')
    p.add_argument('--c', default='6-15'); p.add_argument('--out'); p.add_argument('--corner'); p.set_defaults(fn=cmd_pay)
    a = ap.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
