#!/usr/bin/env python3
"""A band generator with the tilt free (avenues/band.md, round 16).

The jonathan1506 bands are one stack of chains of 3 squares at one tilt, between two upright staircases. The
frame: the band runs from (0, 0) to (L, L). The upper staircase is the lattice anchored at the left and top
walls, cut along the diagonal so that the lower right corner of each cell has y - x >= A. The lower one is
anchored at the bottom and right walls, and the upper left corner of each cell has y - x <= -B. A and B are
f plus a whole number (2 + f and 1 + f in the held 905 and 966).

A chain has its axis u = (cos t, sin t), t the tilt (-45 to 0 degrees), and the next chain sits face to
face along v = (-sin t, cos t). For a chain at height q along v, the slide p along u is free between two
bounds: the upper staircase pushes it to p >= lo(q) and the lower one to p <= hi(q), and the walls do the
same near the corners. Both bounds are exact (an interval per cell from the separating axes). The chains
are placed by a greedy along q: the next chain at the smallest q at least 1 above the last one where
lo(q) <= hi(q). Two chains face to face only need 1 apart in q, so the greedy holds the most chains for
its start. The slides that the greedy picks are the slides of the normal step and of the slip: they come
out of the teeth, they are not set.

Then the exact refill (Evan Daniel's fillfast, MIT, imported from his clone) puts the uprights, and the
count names the n the layout holds at side L. A target goes to the squeeze of family_step.py (sequential
LP, then fq) and to floatsafe.

  band_gen.py ctl     L TILT A B              one band, its chains and its count
  band_gen.py scan    M F0 F1 ... [--tilts] [--ab]   the largest count over tilts, starts and corridors
  band_gen.py build   DETAILS OUT N[:F] [...]  the scan at the target's m, then the squeeze and floatsafe

Our own code; it imports family_step (squeeze, finish, certify, fq) and methods_lp and does not change them.
"""
import argparse, csv, json, math, os, sys, time

import numpy as np

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
sys.path.insert(0, os.environ.get('EVAND_PACKER', '$SCRATCH/bounties-squares/ext/evand/search/packer'))
import family_step as fs  # noqa: E402
import methods_lp as mlp  # noqa: E402
import fillfast  # noqa: E402

EPS = 1e-9        # clearance the generator keeps from every cell and wall (the squeeze takes it back)


class Corridor:
    """The two staircases of side L: teeth cells only (the rest of each staircase is behind them)."""

    def __init__(self, L, A, B, size=3):
        self.L = L; self.size = size; m = int(math.floor(L)); f = L - m
        up = []
        for i in range(0, m):                   # upper: x in [i, i+1], y in [i+1+A, i+2+A], inside the box
            y0 = i + 1 + A
            if y0 >= -1e-12 and y0 + 1 <= L + 1e-9:
                up.append((i + 0.5, y0 + 0.5))
        lo = []
        for j in range(0, m):                   # lower: y in [j, j+1], x in [j+1+B, j+2+B]
            x0 = j + 1 + B
            if x0 >= -1e-12 and x0 + 1 <= L + 1e-9:
                lo.append((x0 + 0.5, j + 0.5))
        self.up = np.array(up).reshape(-1, 2); self.lo = np.array(lo).reshape(-1, 2)


def _intervals(cells, q, al, half_u=1.5, half_v=0.5):
    """For a chain at height q (along v) and every cell: the open interval of slides p where they overlap.
    -> (p1, p2, hit) arrays; hit is False where they never overlap."""
    ca, sa = math.cos(al), math.sin(al)
    u = np.array([ca, sa]); v = np.array([-sa, ca])
    c0 = q * v                                   # chain centre at p = 0
    d0 = c0[None, :] - cells                     # chain centre minus cell centre at p = 0
    p1 = np.full(len(cells), -np.inf); p2 = np.full(len(cells), np.inf)
    hit = np.ones(len(cells), bool)
    # axis v: u . v = 0, a condition on q only
    rv = half_v + 0.5 * (abs(v[0]) + abs(v[1]))
    hit &= np.abs(d0 @ v) < rv - EPS
    # axis u
    ru = half_u + 0.5 * (abs(u[0]) + abs(u[1]))
    a = d0 @ u
    p1 = np.maximum(p1, -ru - a + EPS); p2 = np.minimum(p2, ru - a - EPS)
    # axes x and y of the cell
    for ax in (0, 1):
        r = half_u * abs(u[ax]) + half_v * abs(v[ax]) + 0.5
        k = u[ax]
        if abs(k) < 1e-12:
            hit &= np.abs(d0[:, ax]) < r - EPS
            continue
        e1 = (-r - d0[:, ax]) / k; e2 = (r - d0[:, ax]) / k
        lo_, hi_ = np.minimum(e1, e2), np.maximum(e1, e2)
        p1 = np.maximum(p1, lo_ + EPS / abs(k)); p2 = np.minimum(p2, hi_ - EPS / abs(k))
    hit &= p1 < p2
    return p1, p2, hit


def bounds(C, q, al, half_u=None):
    """-> (lo, hi): the slides p of a chain at height q that touch neither staircase nor a wall."""
    half_u = C.size / 2 if half_u is None else half_u
    lo, hi = -np.inf, np.inf
    if len(C.up):
        p1, p2, h = _intervals(C.up, q, al, half_u)
        if h.any():
            lo = max(lo, p2[h].max())
    if len(C.lo):
        p1, p2, h = _intervals(C.lo, q, al, half_u)
        if h.any():
            hi = min(hi, p1[h].min())
    ca, sa = math.cos(al), math.sin(al)
    u = np.array([ca, sa]); v = np.array([-sa, ca])
    for ax in (0, 1):
        r = half_u * abs(u[ax]) + 0.5 * abs(v[ax])
        k = u[ax]; c = q * v[ax]
        # r + EPS <= c + p k <= L - r - EPS
        a1 = (r + EPS - c) / k; a2 = (C.L - r - EPS - c) / k
        lo = max(lo, min(a1, a2)); hi = min(hi, max(a1, a2))
    return lo, hi


def qrange(L, al):
    """Heights q where a chain centre can be inside the box at all."""
    ca, sa = math.cos(al), math.sin(al)
    v = np.array([-sa, ca])
    cs = np.array([[0, 0], [L, 0], [0, L], [L, L]]) @ v
    return cs.min(), cs.max()


def feasible(C, q, al):
    lo, hi = bounds(C, q, al)
    return lo <= hi, lo, hi


def greedy(C, al, q0, step=2e-3, pick='mid', q_end=None):
    """Chains from height q0 upwards. -> list of (q, p, lo, hi)."""
    qa, qb = qrange(C.L, al)
    q_end = qb if q_end is None else q_end
    out = []
    q = q0
    while q < q_end:
        ok, lo, hi = feasible(C, q, al)
        if not ok:
            # walk up to the next feasible height, then bisect back to its start
            q1 = q
            while q1 < q_end:
                q1 += step
                ok, lo, hi = feasible(C, q1, al)
                if ok:
                    break
            if not ok:
                break
            a, b = q1 - step, q1
            for _ in range(40):
                mid = (a + b) / 2
                if feasible(C, mid, al)[0]:
                    b = mid
                else:
                    a = mid
            q = b
            ok, lo, hi = feasible(C, q, al)
            if not ok:
                q = q1; ok, lo, hi = feasible(C, q, al)
        p = {'mid': (lo + hi) / 2, 'lo': lo, 'hi': hi}[pick]
        out.append((q, p, lo, hi))
        q = q + 1 + 2 * EPS
    return out


def squares(chains, al, size=3):
    ca, sa = math.cos(al), math.sin(al)
    u = np.array([ca, sa]); v = np.array([-sa, ca])
    T = []
    for q, p, lo, hi in chains:
        c = q * v + p * u
        for k in range(size):
            x, y = c + (k - (size - 1) / 2) * u
            T.append((x, y, al))
    return np.array(T).reshape(-1, 3)


def refill(L, T, tau=0.0):
    """The exact upright fill; with tau > 0 an upright may overlap the band by up to tau (the squeeze repairs
    it: the held corners turn their uprights by 0.02 to 0.08 degrees to make that room)."""
    X = T.copy(); X[:, 2] = np.degrees(X[:, 2])
    F = fillfast.fill(L, X, 'exact', tau=tau)
    F[:, 2] = np.radians(F[:, 2])
    return F


def ends(C, al, chains, L):
    """Partial chains at both ends: try a chain of 1 or 2 squares (either end of it) just before the first
    and just after the last full chain. -> extra squares list"""
    ca, sa = math.cos(al), math.sin(al)
    u = np.array([ca, sa]); v = np.array([-sa, ca])
    extra = []
    for q in (chains[0][0] - 1 - 2 * EPS, chains[-1][0] + 1 + 2 * EPS):
        best = []
        for size in range(C.size - 1, 0, -1):
            lo, hi = bounds(C, q, al, half_u=size / 2)
            if lo <= hi:
                c = q * v + (lo + hi) / 2 * u
                best = [tuple(c + (k - (size - 1) / 2) * u) + (al,) for k in range(size)]
                break
        extra += best
    return np.array(extra).reshape(-1, 3)


def layout(L, al, A, B, off, pick='mid', part=True, drop=(0, 0), size=3, tau=0.0):
    """One band layout. off: the start height above the first feasible one. -> (count, F, chains)"""
    C = Corridor(L, A, B, size)
    qa, qb = qrange(L, al)
    first = greedy(C, al, qa, pick=pick)
    if not first:
        return 0, None, []
    ch = greedy(C, al, first[0][0] + off, pick=pick)
    if drop[0] or drop[1]:
        ch = ch[drop[0]:len(ch) - drop[1]]
    if not ch:
        return 0, None, []
    T = squares(ch, al, size)
    if part:
        E = ends(C, al, ch, L)
        if len(E):
            T = np.vstack([T, E])
    F = refill(L, T, tau)
    return len(F), F, ch


def scan(L, tilts, abs_, offs, picks=('mid',), parts=(True, False), drops=((0, 0),), log=None):
    """Every (tilt, A, B, start, pick, partial ends, drop): -> list of (count, tilt deg, a, b, off, pick, part, drop)"""
    m = int(math.floor(L)); f = L - m
    res = []
    for a, b in abs_:
        A, B = a + f, b + f
        for td in tilts:
            al = math.radians(td)
            for off in offs:
                for pick in picks:
                    for part in parts:
                        for dr in drops:
                            try:
                                c, F, ch = layout(L, al, A, B, off, pick, part, dr)
                            except Exception as ex:
                                c = -1
                            res.append((c, td, a, b, off, pick, part, dr))
        if log:
            best = max(r for r in res if r[2] == a and r[3] == b)
            log('  a %d b %d best %s' % (a, b, best))
    return sorted(res, key=lambda r: -r[0])


def best_at(L, abs_, tilts, offs, keep=1, picks=('mid',), stop=None, taus=(0.0,), drops=((0, 0),), parts=(False,)):
    """The largest counts at side L. The chain count of the greedy picks the candidates (it costs a third of
    a fill); only those within one chain of the best per corridor get the fills over picks and ends.
    -> list of (count, tilt deg, a, b, off, pick, part, F), best first"""
    m = int(math.floor(L)); f = L - m
    out = []
    for ab in abs_:
        a, b = ab[0], ab[1]; size = ab[2] if len(ab) > 2 else 3
        C = Corridor(L, a + f, b + f, size)
        cand = []
        for td in tilts:
            if stop and stop():
                break
            al = math.radians(td)
            qa, qb = qrange(L, al)
            first = greedy(C, al, qa)
            if not first:
                continue
            for off in offs:
                ch = greedy(C, al, first[0][0] + off)
                cand.append((len(ch), td, off))
        if not cand:
            continue
        top = max(c[0] for c in cand)
        for nch, td, off in cand:
            if nch < top - (keep - 1) or (stop and stop()):
                continue
            al = math.radians(td)
            for pick in picks:
                for part in parts:
                    for tau in taus:
                        for dr in drops:
                            c, F, ch = layout(L, al, a + f, b + f, off, pick, part, dr, size=size, tau=tau)
                            out.append((c, td, a, b, off, pick, part, F, size, tau, dr))
    return sorted(out, key=lambda r: (-r[0], r[9]))


def drop_to(F, n):
    """Keep n squares: drop uprights farthest from the band first."""
    if len(F) <= n:
        return F
    up = np.nonzero(np.abs(fs.fold(F[:, 2])) < 1e-9)[0]
    d = np.abs(F[up, 1] - F[up, 0])
    gone = set(up[np.argsort(-d)][:len(F) - n].tolist())
    return F[[i for i in range(len(F)) if i not in gone]]


def cmd_build(a):
    import band_step as bs
    os.makedirs(a.out + '/raw', exist_ok=True)
    held, bar = bs.bars(a.details, a.bars)
    stop = (lambda: os.path.exists(a.deadline) and time.time() > float(open(a.deadline).read().split()[0])) if a.deadline else None
    log = open(a.out + '/rows.tsv', 'a')
    tilts = np.arange(a.t0, a.t1 + 1e-9, a.tstep)
    offs = np.arange(0, 1 - 1e-9, a.ostep)
    abs_ = [tuple(int(x) for x in s.split(',')) for s in a.ab.split()]
    taus = tuple(float(x) for x in a.taus.split(','))
    drops = [tuple(int(x) for x in s.split(',')) for s in a.drops.split()]
    for spec in a.targets:
        n = int(spec.split(':')[0]); m = math.isqrt(n)
        if stop and stop():
            print('deadline: stop before %d' % n, flush=True); break
        Ln = (bar[n] + 1) * math.sqrt(n); fbar = Ln - m
        if ':' in spec:
            fgrid = [float(v) for v in spec.split(':')[1].split(',')]
        else:
            fgrid = list(np.arange(min(fbar - 1e-6, a.fhi), a.flo - 1e-9, -a.fstep))
        print('%d (m %d, k %d): bar f %.6f, f from %.6f to %.6f' % (n, m, n - m * m, fbar, fgrid[0], fgrid[-1]), flush=True)
        hits = []; miss = 0

        def probe(f):
            t0 = time.time()
            res = best_at(m + f, abs_, tilts, offs, stop=stop, taus=taus, drops=drops, parts=tuple(bool(int(x)) for x in a.parts.split(',')))
            if not res:
                return 0
            c = res[0][0]
            print('  f %.6f: best %d (%s) %.0f s' % (f, c, ' '.join('%d@%.2f/%d%d/%.2f/%s/%d/t%g/d%d%d' % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[9], r[10][0], r[10][1]) for r in res[:3]), time.time() - t0), flush=True)
            log.write('scan\t%d\t%d\t%.6f\t%d\t%s\n' % (n, m, f, c, ' '.join('%d@%.3f/%d,%d/%.2f/%s/%d/t%g/d%d%d' % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[9], r[10][0], r[10][1]) for r in res[:5])))
            log.flush()
            ok = [r for r in res if r[0] >= n]
            if ok:
                hits.append((f, ok[:a.nbuild]))
            return c

        if a.bisect and ':' not in spec:
            # the smallest f that holds n: counts grow with f, so bisect between flo (assumed short) and the bar
            hi = fbar - 1e-6; lo = a.flo
            if probe(hi) >= n:
                for _ in range(a.bisect):
                    if stop and stop():
                        break
                    mid = (lo + hi) / 2
                    if probe(mid) >= n:
                        hi = mid
                    else:
                        lo = mid
        else:
            for f in fgrid:
                if stop and stop():
                    break
                if probe(f) >= n:
                    miss = 0
                    if ':' in spec and len(hits) >= a.nf:      # an explicit list runs upwards: the first hits are the smallest f
                        break
                else:
                    miss += 1
                    if hits and miss >= a.misses:
                        break
        if not hits:
            print('  %d: no f in the grid holds it' % n, flush=True)
            continue
        hits.sort(key=lambda h: h[0])
        for f, rs in hits[:a.nf]:
            for r in rs:
                if stop and stop():
                    break
                c, td, aa, bb, off, pick, part, F, size, tau, dr = r
                G = drop_to(F, n)
                t1 = time.time(); fs.set_limit(a.buildsec)
                try:
                    X, L, trace = fs.squeeze(G, iters=a.iters, fq=True, stop=stop, apart=max(3e-2, 2 * tau))
                    X, L = fs.finish(X, L, Ln, 'down', 1e-2, stop=stop)
                except fs.Unreadable as ex:
                    print('  %d: %s' % (n, ex), flush=True); continue
                try:
                    Lc, rows = fs.certify(n, X)
                    state = 'certified' if (Lc is not None and (Lc / math.sqrt(n) - 1) < bar[n] - 1e-10) else 'above'
                except ImportError:
                    Lc = None; state = 'below' if L < Ln - 1e-9 else 'above'
                tag = 'f%.4f-t%.2f-ab%d%dc%d-o%.2f-%s%d-tau%g-d%d%d' % (f, td, aa, bb, size, off, pick, part, tau, dr[0], dr[1])
                if state in ('certified', 'below'):
                    fs.write_rows('%s/raw/%d-gen-%s.csv' % (a.out, n, tag), n, X)
                print('  n %d at f %.6f (count %d, %s): built %.9f -> %.9f, bar %.9f, %s (%.0f s)' % (
                    n, f, c, tag, m + f, L, Ln, state, time.time() - t1), flush=True)
                log.write('build\t%d\t%d\t%.6f\t%d\t%s\t%.9f\t%.9f\t%.9f\t%s\n' % (n, m, f, c, tag, m + f, L, Ln, state))
                log.flush()


# ---------------------------------------------------------------- commands

def cmd_ctl(a):
    L = a.L; m = int(math.floor(L)); f = L - m
    al = math.radians(a.tilt)
    c, F, ch = layout(L, al, a.a + f, a.b + f, a.off, a.pick, not a.nopart)
    print('L %.9f tilt %.4f a %d b %d off %.3f: %d chains, count %d' % (L, a.tilt, a.a, a.b, a.off, len(ch), c))
    if a.verbose:
        ca, sa = math.cos(al), math.sin(al)
        u = np.array([ca, sa]); v = np.array([-sa, ca])
        prev = None
        for j, (q, p, lo, hi) in enumerate(ch):
            cen = q * v + p * u
            print('%2d q %.4f p %.4f [%.4f %.4f] w %.4f s %.4f r %.4f dq %.4f' % (
                j, q, p, lo, hi, hi - lo, (cen[0] + cen[1]) / 2 ** .5, (cen[1] - cen[0]) / 2 ** .5, q - prev if prev is not None else 0))
            prev = q
    if a.out and F is not None:
        fs.write_rows(a.out, len(F), F)


def cmd_scan(a):
    tilts = np.arange(a.t0, a.t1 + 1e-9, a.tstep)
    abs_ = [tuple(int(x) for x in s.split(',')) for s in a.ab.split()]
    offs = np.arange(0, 1, a.ostep)
    for F in a.f:
        L = a.m + F
        t0 = time.time()
        res = scan(L, tilts, abs_, offs, log=None)
        print('m %d f %.6f: best %s (%.0f s)' % (a.m, F, res[:3], time.time() - t0), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    q = sp.add_parser('ctl'); q.add_argument('L', type=float); q.add_argument('tilt', type=float)
    q.add_argument('a', type=int); q.add_argument('b', type=int); q.add_argument('--off', type=float, default=0.0)
    q.add_argument('--pick', default='mid'); q.add_argument('--nopart', action='store_true'); q.add_argument('-v', '--verbose', action='store_true')
    q.add_argument('--out'); q.set_defaults(fn=cmd_ctl)
    q = sp.add_parser('scan'); q.add_argument('m', type=int); q.add_argument('f', type=float, nargs='+')
    q.add_argument('--t0', type=float, default=-37.0); q.add_argument('--t1', type=float, default=-33.0); q.add_argument('--tstep', type=float, default=0.05)
    q.add_argument('--ab', default='2,1 1,2'); q.add_argument('--ostep', type=float, default=0.1); q.set_defaults(fn=cmd_scan)
    q = sp.add_parser('build'); q.add_argument('details'); q.add_argument('out'); q.add_argument('targets', nargs='+')
    q.add_argument('--bars', nargs='*', default=[]); q.add_argument('--deadline')
    q.add_argument('--t0', type=float, default=-37.0); q.add_argument('--t1', type=float, default=-33.0); q.add_argument('--tstep', type=float, default=0.1)
    q.add_argument('--ab', default='2,1 1,2'); q.add_argument('--ostep', type=float, default=0.2)
    q.add_argument('--fhi', type=float, default=0.62); q.add_argument('--flo', type=float, default=0.55); q.add_argument('--fstep', type=float, default=0.001)
    q.add_argument('--misses', type=int, default=3); q.add_argument('--bisect', type=int, default=0); q.add_argument('--taus', default='0,0.03'); q.add_argument('--drops', default='0,0'); q.add_argument('--parts', default='0');q.add_argument('--nf', type=int, default=2); q.add_argument('--nbuild', type=int, default=1)
    q.add_argument('--iters', type=int, default=40); q.add_argument('--buildsec', type=float, default=600); q.set_defaults(fn=cmd_build)
    a = ap.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
