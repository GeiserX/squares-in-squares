#!/usr/bin/env python3
"""Tilted blocks with slips for n = m*m + k, k = 1, 2, 3 (avenues/k123.md, round 17).

The design. A block is N chains of w squares. The chain axis u stands at 45 degrees minus phi to the
x axis, so the chain crosses a diagonal corridor between two upright staircases (the lattice of the left
and top walls, cut where y - x >= a + f, and the lattice of the bottom and right walls, cut where
y - x <= -(b + f)). The next chain sits face to face and slides along u. The teeth of the staircases go
into the pockets that the slides open, and the jam line of the corridor is

    a + b + 2 f = (sqrt(2) w + j sin(phi)) / cos(phi),      j = -1 when a + b is odd, 0 or -2 when even

(fjam below). phi = 0 and j = 0 is the rigid 45 degree block. The two flat faces of the block stand
against the other two lattices, which the exact refill finds.

The corridor, the exact slide bounds and the greedy are the same construction as band_gen.py (round 16,
chains of 3 from corner to corner); they are written out here for any w so this file does not depend on
it. The refill is Evan Daniel's fillfast (MIT), imported from his clone (EVAND_PACKER).

  k123_block.py fjam   W S J PHI_DEG                       the jam line
  k123_block.py ctl    L W A B PHI_DEG N [--off --pick]    one block, its count, optional --out csv
  k123_block.py scan   OUT.tsv DEADLINE JOB [JOB ...]      JOB = m:k:w:a:b:n0-n1:phi0:phi1:dphi:f0:f1:df
  k123_block.py build  DETAILS OUTDIR DEADLINE ROW.json    squeeze (sequential LP, fq) and certify

Our own code; it imports family_step (squeeze, certify, fq) and does not change it.
"""
import argparse, json, math, os, sys, time

import numpy as np

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
sys.path.insert(0, os.environ.get('EVAND_PACKER', '$SCRATCH/bounties-squares/ext/evand/search/packer'))

EPS = 1e-9
R2 = math.sqrt(2.0)


def fjam(w, s, j, phi):
    """The side fraction at which chains of w jam in a corridor of a + b = s, at phi radians off 45."""
    return ((R2 * w + j * math.sin(phi)) / math.cos(phi) - s) / 2


def rate(w, s, phi):
    """Squares gained per unit of m by a band of such chains from corner to corner."""
    return R2 * w * math.cos(phi) - (s + 1)


# ---------------------------------------------------------------- corridor and chains

class Corridor:
    def __init__(self, L, A, B, size):
        self.L = L; self.size = size; m = int(math.floor(L))
        up = [(i + 0.5, i + 1 + A + 0.5) for i in range(-1, m + 1) if i + 1 + A >= -1e-12 and i + 2 + A <= L + 1e-9 and i >= 0]
        lo = [(j + 1 + B + 0.5, j + 0.5) for j in range(-1, m + 1) if j + 1 + B >= -1e-12 and j + 2 + B <= L + 1e-9 and j >= 0]
        self.up = np.array(up).reshape(-1, 2); self.lo = np.array(lo).reshape(-1, 2)


def _intervals(cells, q, al, half_u, half_v=0.5):
    ca, sa = math.cos(al), math.sin(al)
    u = np.array([ca, sa]); v = np.array([-sa, ca])
    d0 = (q * v)[None, :] - cells
    p1 = np.full(len(cells), -np.inf); p2 = np.full(len(cells), np.inf)
    hit = np.abs(d0 @ v) < half_v + 0.5 * (abs(v[0]) + abs(v[1])) - EPS
    ru = half_u + 0.5 * (abs(u[0]) + abs(u[1]))
    a = d0 @ u
    p1 = np.maximum(p1, -ru - a + EPS); p2 = np.minimum(p2, ru - a - EPS)
    for ax in (0, 1):
        r = half_u * abs(u[ax]) + half_v * abs(v[ax]) + 0.5
        k = u[ax]
        e1 = (-r - d0[:, ax]) / k; e2 = (r - d0[:, ax]) / k
        p1 = np.maximum(p1, np.minimum(e1, e2) + EPS / abs(k)); p2 = np.minimum(p2, np.maximum(e1, e2) - EPS / abs(k))
    hit &= p1 < p2
    return p1, p2, hit


def bounds(C, q, al, half_u=None):
    """The slides p of a chain at height q that touch neither staircase nor a wall. -> (lo, hi)"""
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
        a1 = (r + EPS - c) / k; a2 = (C.L - r - EPS - c) / k
        lo = max(lo, min(a1, a2)); hi = min(hi, max(a1, a2))
    return lo, hi


def greedy(C, al, q0, q_end, step=5e-3):
    """Chains from height q0 upwards, each at the smallest feasible height at least 1 above the last."""
    out = []; q = q0
    while q < q_end:
        lo, hi = bounds(C, q, al)
        if lo > hi:
            q1 = q; ok = False
            while q1 < q_end:
                q1 += step
                lo, hi = bounds(C, q1, al)
                if lo <= hi:
                    ok = True; break
            if not ok:
                break
            a, b = q1 - step, q1
            for _ in range(30):
                mid = (a + b) / 2
                l2, h2 = bounds(C, mid, al)
                if l2 <= h2:
                    b = mid
                else:
                    a = mid
            q = b; lo, hi = bounds(C, q, al)
        out.append((q, lo, hi))
        q = q + 1 + 2 * EPS
    return out


def qrange(L, al):
    v = np.array([-math.sin(al), math.cos(al)])
    cs = np.array([[0, 0], [L, 0], [0, L], [L, L]]) @ v
    return cs.min(), cs.max()


def runs(ch, n):
    """Every window of n chains in a row that are exactly 1 apart. -> list of start indices"""
    out = []
    for i in range(0, len(ch) - n + 1):
        if all(ch[k + 1][0] - ch[k][0] < 1 + 1e-6 for k in range(i, i + n - 1)):
            out.append(i)
    return out


def squares(sel, al, size, pick):
    ca, sa = math.cos(al), math.sin(al)
    u = np.array([ca, sa]); v = np.array([-sa, ca])
    T = []
    for q, lo, hi in sel:
        p = {'mid': (lo + hi) / 2, 'lo': lo, 'hi': hi}[pick] if isinstance(pick, str) else lo + pick * (hi - lo)
        c = q * v + p * u
        for k in range(size):
            x, y = c + (k - (size - 1) / 2) * u
            T.append((x, y, al))
    return np.array(T).reshape(-1, 3)


def refill(L, T, tau=0.0):
    import fillfast
    X = T.copy(); X[:, 2] = np.degrees(X[:, 2])
    F = fillfast.fill(L, X, 'exact', tau=tau)
    F[:, 2] = np.radians(F[:, 2])
    return F


def block(L, w, a, b, phi_deg, n, off=0.0, picks=('mid',), tau=0.0, every=1):
    """The best count over the windows of n chains. -> (count, F, info) or (0, None, None)"""
    m = int(math.floor(L)); f = L - m
    al = math.radians(-45.0 + phi_deg)
    C = Corridor(L, a + f, b + f, w)
    qa, qb = qrange(L, al)
    ch = greedy(C, al, qa + off, qb)
    best = (0, None, None)
    for i in runs(ch, n)[::every]:
        for pick in picks:
            T = squares(ch[i:i + n], al, w, pick)
            F = refill(L, T, tau)
            if len(F) > best[0]:
                best = (len(F), F, dict(i=i, pick=pick, chains=len(ch), runs=len(runs(ch, n))))
    return best


# ---------------------------------------------------------------- commands

def cmd_fjam(a):
    phi = math.radians(a.phi)
    print('w %d s %d j %d phi %.4f: f %.7f, band rate %.5f per m' % (a.w, a.s, a.j, a.phi, fjam(a.w, a.s, a.j, phi), rate(a.w, a.s, phi)))


def cmd_ctl(a):
    t0 = time.time()
    c, F, info = block(a.L, a.w, a.a, a.b, a.phi, a.n, a.off, tuple(a.pick.split(',')), a.tau)
    m = int(a.L)
    print('L %.9f w %d a %d b %d phi %.4f n %d off %.2f: count %d = m*m %+d  %s  %.1f s' % (
        a.L, a.w, a.a, a.b, a.phi, a.n, a.off, c, c - m * m, info, time.time() - t0))
    if a.out and F is not None:
        import family_step as fs
        fs.write_rows(a.out, len(F), F)


def cmd_scan(a):
    stop = lambda: time.time() > float(open(a.deadline).read().split()[0])
    out = open(a.out, 'a')
    for job in a.jobs:
        p = job.split(':')
        m, k, w, aa, bb = (int(x) for x in p[:5])
        n0, n1 = (int(x) for x in p[5].split('-'))
        phi0, phi1, dphi, f0, f1, df = (float(x) for x in p[6:12])
        s = aa + bb
        best = {}
        for phi in np.arange(phi0, phi1 + 1e-9, dphi):
            for f in np.arange(f0, f1 + 1e-9, df):
                if stop():
                    break
                L = m + f
                al = math.radians(-45.0 + phi)
                C = Corridor(L, aa + f, bb + f, w)
                qa, qb = qrange(L, al)
                for off in a.offs:
                    ch = greedy(C, al, qa + off, qb)
                    for n in range(n0, n1 + 1):
                        rs = runs(ch, n)
                        for i in rs[::a.every]:
                            for pick in a.picks:
                                T = squares(ch[i:i + n], al, w, pick)
                                F = refill(L, T, a.tau)
                                g = len(F) - m * m
                                row = dict(m=m, k=k, w=w, a=aa, b=bb, n=n, phi=round(float(phi), 4), f=round(float(f), 6), off=off, i=i, pick=pick, gain=g, tilted=len(T))
                                if g >= k:
                                    out.write(json.dumps(row) + '\n'); out.flush()
                                key = (n, round(float(f), 6))
                                if key not in best or g > best[key][0]:
                                    best[key] = (g, round(float(phi), 3), off, i)
        for key in sorted(best):
            print('m %d w %d ab %d,%d n %d f %.4f: best gain %d at phi %.3f off %.2f i %d' % (m, w, aa, bb, key[0], key[1], *best[key]), flush=True)
        hit = [f for (n, f), v in best.items() if v[0] >= k]
        print('JOB %s: smallest f with gain >= %d: %s' % (job, k, min(hit) if hit else 'none'), flush=True)


def cmd_build(a):
    import csv
    import family_step as fs
    stop = lambda: time.time() > float(open(a.deadline).read().split()[0])
    held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(a.details))}
    os.makedirs(a.out, exist_ok=True)
    for line in a.rows:
        r = json.loads(line)
        m, w = r['m'], r['w']; n = m * m + r['k']; L = m + r['f']
        al = math.radians(-45.0 + r['phi'])
        C = Corridor(L, r['a'] + r['f'], r['b'] + r['f'], w)
        qa, qb = qrange(L, al)
        ch = greedy(C, al, qa + r['off'], qb)
        T = squares(ch[r['i']:r['i'] + r['n']], al, w, r['pick'])
        F = refill(L, T, 0.0)
        if len(F) < n:
            print('row holds %d, not %d' % (len(F), n), flush=True); continue
        if len(F) > n:                                   # drop the uprights nearest a far corner
            up = np.nonzero(np.abs(fs.fold(F[:, 2])) < 1e-9)[0]
            d = np.abs(F[up, 1] - F[up, 0])
            gone = set(up[np.argsort(-d)][:len(F) - n].tolist())
            F = F[[i for i in range(len(F)) if i not in gone]]
        Ln = (held[n] + 1) * math.sqrt(n)
        t0 = time.time(); fs.set_limit(a.sec)
        try:
            X, Lx, trace = fs.squeeze(F, iters=a.iters, fq=True, stop=stop)
        except fs.Unreadable as ex:
            print('n %d: %s' % (n, ex), flush=True); continue
        tag = 'w%d-ab%d%d-n%d-phi%.3f-f%.4f' % (w, r['a'], r['b'], r['n'], r['phi'], r['f'])
        fs.write_rows('%s/%d-%s.csv' % (a.out, n, tag), n, X)
        print('n %d %s: built %.9f -> %.9f (held %.9f) %s  %.0f s  trace %s' % (
            n, tag, L, Lx, Ln, 'BELOW' if Lx < Ln - 1e-9 else 'above', time.time() - t0, [(t[0], round(t[1], 9)) for t in trace]), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    q = sp.add_parser('fjam'); q.add_argument('w', type=int); q.add_argument('s', type=int); q.add_argument('j', type=int); q.add_argument('phi', type=float); q.set_defaults(fn=cmd_fjam)
    q = sp.add_parser('ctl'); q.add_argument('L', type=float); q.add_argument('w', type=int); q.add_argument('a', type=int); q.add_argument('b', type=int)
    q.add_argument('phi', type=float); q.add_argument('n', type=int); q.add_argument('--off', type=float, default=0.0); q.add_argument('--pick', default='mid')
    q.add_argument('--tau', type=float, default=0.0); q.add_argument('--out'); q.set_defaults(fn=cmd_ctl)
    q = sp.add_parser('scan'); q.add_argument('out'); q.add_argument('deadline'); q.add_argument('jobs', nargs='+')
    q.add_argument('--offs', type=lambda s: [float(x) for x in s.split(',')], default=[0.0, 0.35, 0.7, 1.05])
    q.add_argument('--picks', type=lambda s: s.split(','), default=['mid']); q.add_argument('--tau', type=float, default=0.0)
    q.add_argument('--every', type=int, default=1); q.set_defaults(fn=cmd_scan)
    q = sp.add_parser('build'); q.add_argument('details'); q.add_argument('out'); q.add_argument('deadline'); q.add_argument('rows', nargs='+')
    q.add_argument('--iters', type=int, default=60); q.add_argument('--sec', type=float, default=900); q.set_defaults(fn=cmd_build)
    a = ap.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
