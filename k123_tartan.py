#!/usr/bin/env python3
"""A tilted block with slips in both directions, fitted by LP (avenues/k123.md, round 17).

The design. A rigid block of a x b squares at 45 degrees sits in a hole between four upright lattices,
one per corner of the box. Turn every square of the block by phi. Rows stay rigid along u and columns stay
rigid along v, so square (i, j) has its centre at

    O + (i + S_j) u + (j + R_i) v,       u = (cos t, sin t), v = (-sin t, cos t), t = 45 degrees + phi

with one slide S_j per row and one slip R_i per column. S grows and R falls (for phi > 0), which keeps the
squares apart. The slides open pockets at the four faces of the block, and the teeth of the staircases go
into them. The held 261 (8 x 13 at 41.88 degrees) is this structure.

For a fixed phi every centre is linear in (O, S, R) and every upright is linear in the side L (it keeps
its walls). With one separating axis per pair of a tilted square and an upright, "no overlap" is a linear
constraint, so the smallest L is an LP. The axes are chosen again after each step (sequential LP). The
uprights come from a held layout: the hole stays, only the block changes.

  k123_tartan.py fit    HELD.csv N [--phis a,b,step] [--out DIR]     the LP over phi; writes the best layout
  k123_tartan.py build  HELD.csv DETAILS OUTDIR N [N ...]            fit, squeeze (LP on every square, fq), certify

Our own code; it imports family_step (squeeze, certify, fq) and methods_lp and does not change them.
"""
import argparse, csv, math, os, sys, time

import numpy as np
from scipy.optimize import linprog

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)

R2 = math.sqrt(2.0)


def fold(th):
    t = np.mod(th, math.pi / 2)
    return np.where(t > math.pi / 4, t - math.pi / 2, t)


def load(path, n):
    P = []
    with open(path) as fh:
        r = csv.reader(fh); head = next(r)
        ix = {h: k for k, h in enumerate(head)}
        for rec in r:
            if int(rec[ix['n']]) == n:
                P.append((float(rec[ix['x']]), float(rec[ix['y']]), float(rec[ix['angle']])))
    return np.array(P)


class Hole:
    """A held layout read as uprights that keep their walls, and one block of tilted squares on a grid."""

    def __init__(self, P):
        ang = fold(P[:, 2])
        up = np.abs(ang) < 1e-7
        self.n = len(P)
        h = 0.5 * (np.abs(np.cos(P[:, 2])) + np.abs(np.sin(P[:, 2])))
        x0 = (P[:, 0] - h).min(); y0 = (P[:, 1] - h).min()
        P = P.copy(); P[:, 0] -= x0; P[:, 1] -= y0
        self.L = max((P[:, 0] + h).max(), (P[:, 1] + h).max())
        U = P[up][:, :2]; T = P[~up]
        self.base = np.zeros_like(U); self.e = np.zeros_like(U)
        for ax in (0, 1):
            lo = U[:, ax] - 0.5; hi = self.L - U[:, ax] - 0.5
            left = np.abs(lo - np.round(lo)) <= np.abs(hi - np.round(hi))
            self.base[:, ax] = np.where(left, np.round(lo) + 0.5, -np.round(hi) - 0.5)
            self.e[:, ax] = np.where(left, 0.0, 1.0)
        self.off = np.abs(self.base + self.e * self.L - U).max()        # how far the uprights are from their lattices
        # the block: index the tilted squares on their own grid
        t0 = float(np.median(np.mod(T[:, 2], math.pi / 2)))
        self.t0 = t0
        u = np.array([math.cos(t0), math.sin(t0)]); v = np.array([-u[1], u[0]])
        Uc = T[:, :2] @ u; Vc = T[:, :2] @ v
        N = len(T); idx = {0: (0, 0)}; todo = [0]
        while todo:
            k = todo.pop()
            for l in range(N):
                if l in idx:
                    continue
                du = Uc[l] - Uc[k]; dv = Vc[l] - Vc[k]
                if abs(abs(du) - 1) < 0.03 and abs(dv) < 0.3:
                    idx[l] = (idx[k][0] + int(round(du)), idx[k][1]); todo.append(l)
                elif abs(abs(dv) - 1) < 0.03 and abs(du) < 0.3:
                    idx[l] = (idx[k][0], idx[k][1] + int(round(dv))); todo.append(l)
        if len(idx) != N:
            raise ValueError('the tilted squares are not one block (%d of %d on a grid)' % (len(idx), N))
        I = np.array([idx[k] for k in range(N)]); I -= I.min(0)
        self.sites = I; self.a = int(I[:, 0].max()) + 1; self.b = int(I[:, 1].max()) + 1
        self.T = T
        # O: the centre of the grid frame, from a least squares fit of the held centres
        ic, jc = (self.a - 1) / 2, (self.b - 1) / 2
        self.c0 = (T[:, :2] - np.outer(I[:, 0] - ic, u) - np.outer(I[:, 1] - jc, v)).mean(0)

    @classmethod
    def parts(cls, L, U, sites, t0, c0, n):
        """A hole from uprights (centres at side L), a set of grid sites and the grid frame."""
        H = cls.__new__(cls)
        H.n = n; H.L = L
        U = np.asarray(U, float).reshape(-1, 2)
        H.base = np.zeros_like(U); H.e = np.zeros_like(U)
        for ax in (0, 1):
            lo = U[:, ax] - 0.5; hi = L - U[:, ax] - 0.5
            left = np.abs(lo - np.round(lo)) <= np.abs(hi - np.round(hi))
            free = np.minimum(np.abs(lo - np.round(lo)), np.abs(hi - np.round(hi))) > 1e-6     # on no wall lattice: it stays where it is
            H.base[:, ax] = np.where(free, U[:, ax], np.where(left, np.round(lo) + 0.5, -np.round(hi) - 0.5))
            H.e[:, ax] = np.where(free | left, 0.0, 1.0)
            H.nfree = int(free.sum()) + getattr(H, 'nfree', 0)
        H.off = float(np.abs(H.base + H.e * L - U).max()) if len(U) else 0.0
        I = np.asarray(sites, int).reshape(-1, 2).copy(); I -= I.min(0)
        H.sites = I; H.a = int(I[:, 0].max()) + 1; H.b = int(I[:, 1].max()) + 1
        H.t0 = t0; H.c0 = np.asarray(c0, float); H.T = None
        return H

    def uprights(self, L):
        return self.base + self.e * L

    def upright_rows(self, nv, iL, L):
        """Two uprights on different lattices keep apart: linear in L."""
        Up = self.uprights(L); rows = []; rhs = []
        mixed = np.nonzero((self.e[:, None, :] != self.e[None, :, :]).any(2) & (np.abs(Up[:, None, :] - Up[None, :, :]).max(2) < 1.6))
        for k, l in zip(*mixed):
            if k >= l:
                continue
            d = Up[k] - Up[l]; ax = int(np.argmax(np.abs(d))); s = 1.0 if d[ax] >= 0 else -1.0
            row = np.zeros(nv); row[iL] = -s * (self.e[k, ax] - self.e[l, ax])
            rows.append(row); rhs.append(-1.0 + s * (self.base[k, ax] - self.base[l, ax]))
        return rows, rhs

    def start(self, phi, mode='uniform', cr=0.0, cs=0.0):
        """S (per row), R (per column) for a turn phi: 'uniform' is the turned lattice, 'teeth' slips once a tooth."""
        a, b = self.a, self.b
        tp = math.tan(phi)
        if mode == 'uniform':
            S = (np.arange(b) - (b - 1) / 2) * tp; R = -(np.arange(a) - (a - 1) / 2) * tp
        else:
            kap = R2 / math.cos(phi); tau = kap * tp
            S = tau * np.floor((np.arange(b) + cs) / kap); R = -tau * np.floor((np.arange(a) + cr) / kap)
            S -= S.mean(); R -= R.mean()
        return S, R

    def centres(self, t, O, S, R):
        u = np.array([math.cos(t), math.sin(t)]); v = np.array([-u[1], u[0]])
        ic, jc = (self.a - 1) / 2, (self.b - 1) / 2
        i = self.sites[:, 0]; j = self.sites[:, 1]
        return O[None, :] + np.outer(i - ic + S[j], u) + np.outer(j - jc + R[i], v)

    def layout(self, t, O, S, R, L):
        C = self.centres(t, O, S, R)
        Up = self.uprights(L)
        return np.vstack([np.c_[C, np.full(len(C), t)], np.c_[Up, np.zeros(len(Up))]])

    def fit(self, phi, S, R, iters=60, tr=0.15, log=None):
        """Sequential LP at one turn. -> (L, O, S, R, min sep)"""
        a, b = self.a, self.b
        t = math.pi / 4 + phi if abs(fold(np.array([self.t0]))[0]) > 0 else phi
        t = self.t0 + phi                                   # the held block angle plus the turn
        u = np.array([math.cos(t), math.sin(t)]); v = np.array([-u[1], u[0]])
        ic, jc = (a - 1) / 2, (b - 1) / 2
        i = self.sites[:, 0]; j = self.sites[:, 1]
        nv = 2 + b + a + 1; iL = nv - 1
        O = self.c0.copy(); L = self.L + 0.05
        sg = 1.0 if phi >= 0 else -1.0
        ht = 0.5 * (abs(u[0]) + abs(u[1]))                  # half extent of a tilted square on x or y
        hu = 0.5 * (abs(u[0]) + abs(u[1]))                  # half extent of an upright on u or v
        axes = [(np.array([1.0, 0.0]), 0.5 + ht), (np.array([0.0, 1.0]), 0.5 + ht), (u, 0.5 + hu), (v, 0.5 + hu)]
        last = None
        for it in range(iters):
            C = self.centres(t, O, S, R); Up = self.uprights(L)
            D = C[:, None, :] - Up[None, :, :]
            near = np.argwhere((np.abs(D[:, :, 0]) < 2.2) & (np.abs(D[:, :, 1]) < 2.2))
            rows = []; rhs = []
            d = D[near[:, 0], near[:, 1]]
            seps = np.stack([np.abs(d @ n) - r for n, r in axes], 1)
            pick = seps.argmax(1)
            for (kt, ku), ax, dd in zip(near, pick, d):
                n, r = axes[ax]
                s = 1.0 if dd @ n >= 0 else -1.0
                row = np.zeros(nv)
                row[0] = -s * n[0]; row[1] = -s * n[1]
                row[2 + j[kt]] = -s * (n @ u); row[2 + b + i[kt]] = -s * (n @ v)
                row[iL] = s * (n @ self.e[ku])
                const = s * (n @ ((i[kt] - ic) * u + (j[kt] - jc) * v)) - s * (n @ self.base[ku])
                rows.append(row); rhs.append(-r + const)
            # walls
            for kt in range(len(C)):
                for ax in (0, 1):
                    if C[kt, ax] < 2.5:
                        row = np.zeros(nv); row[ax] = -1; row[2 + j[kt]] = -u[ax]; row[2 + b + i[kt]] = -v[ax]
                        rows.append(row); rhs.append(-ht + (i[kt] - ic) * u[ax] + (j[kt] - jc) * v[ax])
                    if C[kt, ax] > L - 2.5:
                        row = np.zeros(nv); row[ax] = 1; row[2 + j[kt]] = u[ax]; row[2 + b + i[kt]] = v[ax]; row[iL] = -1
                        rows.append(row); rhs.append(-ht - (i[kt] - ic) * u[ax] - (j[kt] - jc) * v[ax])
            r2, h2 = self.upright_rows(nv, iL, L); rows += r2; rhs += h2
            # the slides keep their order
            for jj in range(b - 1):
                row = np.zeros(nv); row[2 + jj] = sg; row[2 + jj + 1] = -sg; rows.append(row); rhs.append(0.0)
            for ii in range(a - 1):
                row = np.zeros(nv); row[2 + b + ii] = -sg; row[2 + b + ii + 1] = sg; rows.append(row); rhs.append(0.0)
            z0 = np.r_[O, S, R, L]
            bnd = [(z0[k] - tr, z0[k] + tr) for k in range(nv - 1)] + [(L - 0.3, L + 0.3)]
            cost = np.zeros(nv); cost[iL] = 1.0
            res = linprog(cost, A_ub=np.array(rows), b_ub=np.array(rhs), bounds=bnd, method='highs')
            if res.status != 0:
                if log:
                    log('    it %d: LP status %d' % (it, res.status))
                if it < 6:                                  # an overlapping start: open the box and try again
                    L += 0.15; tr = min(tr * 1.5, 0.5)
                    continue
                L = float('inf')
                break
            z = res.x
            O = z[:2]; S = z[2:2 + b]; R = z[2 + b:2 + b + a]; Ln = z[iL]
            if log:
                log('    it %d: L %.9f' % (it, Ln))
            if last is not None and abs(Ln - last) < 1e-10 and it > 3:
                L = Ln; break
            last = Ln; L = Ln
        return L, O, S, R, t


def best_fit(H, phis, log=None, starts=None):
    out = []
    starts = starts or [('uniform', 0, 0)] + [('teeth', cr, cs) for cr in (0.0, 0.5, 1.0) for cs in (0.0, 0.5, 1.0)]
    for phi in phis:
        best = None
        for mode, cr, cs in starts:
            S, R = H.start(phi, mode, cr, cs)
            L, O, S, R, t = H.fit(phi, S, R)
            if best is None or L < best[0]:
                best = (L, O, S, R, t, mode, cr, cs)
        out.append((phi,) + best)
        if log:
            log('  phi %+.3f deg: L %.9f (start %s %.1f %.1f)' % (math.degrees(phi), best[0], best[5], best[6], best[7]))
    return out


def cmd_fit(a):
    import methods_lp as mlp
    P = load(a.held, a.n)
    H = Hole(P)
    print('n %d: side %.9f, block %d x %d (%d squares) at %.4f deg, %d uprights, %.1e off their lattices' % (
        a.n, H.L, H.a, H.b, len(H.sites), math.degrees(H.t0), len(H.base), H.off), flush=True)
    p0, p1, dp = (float(x) for x in a.phis.split(','))
    phis = [math.radians(x) for x in np.arange(p0, p1 + 1e-9, dp)]
    res = best_fit(H, phis, log=lambda s: print(s, flush=True))
    phi, L, O, S, R, t, mode, cr, cs = min(res, key=lambda r: r[1])
    X = H.layout(t, O, S, R, L)
    print('best: phi %+.4f deg, L %.9f (held %.9f, %+.6f), min gap %.2e' % (math.degrees(phi), L, H.L, L - H.L, mlp.min_gap(X)), flush=True)
    print('  S', np.round(S, 4).tolist()); print('  R', np.round(R, 4).tolist())
    if a.out:
        import family_step as fs
        os.makedirs(a.out, exist_ok=True)
        fs.write_rows('%s/%d-fit.csv' % (a.out, a.n), a.n, X)


def cmd_build(a):
    import family_step as fs
    import methods_lp as mlp
    held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(a.details))}
    os.makedirs(a.out + '/raw', exist_ok=True)
    p0, p1, dp = (float(x) for x in a.phis.split(','))
    phis = [math.radians(x) for x in np.arange(p0, p1 + 1e-9, dp)]
    for n in a.ns:
        t0 = time.time()
        try:
            H = Hole(load(a.held, n))
        except ValueError as ex:
            print('n %d: %s' % (n, ex), flush=True); continue
        Ln = (held[n] + 1) * math.sqrt(n)
        res = best_fit(H, phis)
        phi, L, O, S, R, t, mode, cr, cs = min(res, key=lambda r: r[1])
        X = H.layout(t, O, S, R, L + 1e-9)
        gap = mlp.min_gap(X)
        print('n %d: block %d x %d, fit phi %+.3f L %.9f (held %.9f), min gap %.2e, %.0f s' % (n, H.a, H.b, math.degrees(phi), L, Ln, gap, time.time() - t0), flush=True)
        if not (L < Ln - 1e-7):
            continue
        fs.set_limit(a.sec)
        try:
            Y, Ly, trace = fs.squeeze(X, iters=a.iters, fq=True)
        except fs.Unreadable as ex:
            print('  n %d: %s' % (n, ex), flush=True); continue
        Lc, rows = fs.certify(n, Y)
        ok = Lc is not None and (Lc / math.sqrt(n) - 1) < held[n] - 1e-10
        if ok:
            fs.write_rows('%s/raw/%d-tartan.csv' % (a.out, n), n, Y)
        print('  n %d: squeeze %.9f -> %.9f, certified %s, score %s (held %r) %s  %.0f s' % (
            n, L, Ly, 'None' if Lc is None else '%.9f' % Lc, 'None' if Lc is None else repr(Lc / math.sqrt(n) - 1), held[n], 'KEEP' if ok else 'drop', time.time() - t0), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    q = sp.add_parser('fit'); q.add_argument('held'); q.add_argument('n', type=int); q.add_argument('--phis', default='0,4,0.25'); q.add_argument('--out'); q.set_defaults(fn=cmd_fit)
    q = sp.add_parser('build'); q.add_argument('held'); q.add_argument('details'); q.add_argument('out'); q.add_argument('ns', type=int, nargs='+')
    q.add_argument('--phis', default='0,4,0.25'); q.add_argument('--iters', type=int, default=60); q.add_argument('--sec', type=float, default=1200); q.set_defaults(fn=cmd_build)
    a = ap.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
