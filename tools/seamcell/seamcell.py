#!/usr/bin/env python3
"""seamcell: periodic seam-cell solver for the two-grid band regime (T4 of TOOLS-PLAN-2026-11-09).

  seamcell.py mine  --in 498.csv [--p 1..6]                   > mined.jsonl
  seamcell.py fold  --in 498.csv --p 3 [--k K] [--f F]        local relax of the folded seam (controls)
  seamcell.py cell  --f 0.7941 --p 1..6 --D 1..4 [--gain 0.80] [--starts 200] [--workers 12] > cells.jsonl
  seamcell.py minf  --cells cells.jsonl                        push f down on found cells (continuation)

Net gain per diagonal step of a cell with k tilted squares per p steps and D removed diagonals is
  g = k/p - (D - 1)
because a box of side m + f holds m^2 + (1 - D) m + O(1) uprights and the seam adds k/p per step.
The leader's m + 0.794 family fits n - m^2 = 0.82 m - 3.9.
"""
import argparse, csv, json, math, os, sys, time
import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kernel import energy_grad  # noqa: E402
from cert import certify  # noqa: E402

SQ2 = math.sqrt(2.0)
HALF = math.pi / 2


def rng_list(s):
    if ':' in s and '..' not in s:
        a, b = s.split(':'); return float(a), float(b)
    if '..' in s:
        a, b = s.split('..'); return list(range(int(a), int(b) + 1))
    return [int(x) for x in s.split(',')]


# ----------------------------------------------------------------------------------------- mine
def load_csv(path):
    rows = [r for r in csv.DictReader(open(path))]
    P = np.array([(float(r['x']), float(r['y']), float(r['angle'])) for r in rows])
    return P


def side_of(P):
    """Bounding-box side, as the metric measures it."""
    e = 0.5 * (np.abs(np.cos(P[:, 2])) + np.abs(np.sin(P[:, 2])))
    return float(max((P[:, 0] + e).max() - (P[:, 0] - e).min(), (P[:, 1] + e).max() - (P[:, 1] - e).min()))


def circ_median(v):
    """median of values mod 1, robust to wrap."""
    a = np.angle(np.mean(np.exp(2j * np.pi * v))) / (2 * np.pi) % 1.0
    d = (v - a + 0.5) % 1.0 - 0.5
    return (a + np.median(d)) % 1.0


def mine(P, ptol=1e-6):
    L = side_of(P)
    f = L - math.floor(L)
    tm = np.mod(P[:, 2], HALF)
    up = (tm < ptol) | (HALF - tm < ptol)
    U = P[up]; T = P[~up]
    fx = (U[:, 0] - 0.5) % 1.0; fy = (U[:, 1] - 0.5) % 1.0
    # G1 (bottom-right): x off-lattice, y on; G2 (top-left): y off-lattice, x on.
    g1 = U[:, 0] - U[:, 1] > 0
    a1 = circ_median(fx[g1]); b1 = circ_median(fy[g1])
    a2 = circ_median(fx[~g1]); b2 = circ_median(fy[~g1])
    # translate by (-a2, -b1): G1 offset (a1 - a2, 0), G2 offset (0, b2 - b1)
    ox = (a1 - a2) % 1.0 or 1.0; oy = (b2 - b1) % 1.0 or 1.0
    sh = np.array([a2, b1])
    G1 = U[g1, :2] - sh; G2 = U[~g1, :2] - sh
    T2 = T.copy(); T2[:, :2] -= sh
    I1 = np.round(G1[:, 0] - 0.5 - ox).astype(int); J1 = np.round(G1[:, 1] - 0.5).astype(int)
    A2 = np.round(G2[:, 0] - 0.5).astype(int); B2 = np.round(G2[:, 1] - 0.5 - oy).astype(int)
    res1 = np.abs(G1[:, 0] - 0.5 - ox - I1).max(); res2 = np.abs(G2[:, 1] - 0.5 - oy - B2).max()
    # boundary diagonals, from the middle of the seam (ignore the caps)
    mid1 = (J1 > 3) & (J1 < math.floor(L) - 4); mid2 = (A2 > 3) & (A2 < math.floor(L) - 4)
    d1 = int(np.min((I1 - J1)[mid1])); d2 = int(np.min((B2 - A2)[mid2]))
    D = d1 + d2
    # bring to the canonical frame where G2 keeps b - a >= 0: translate by (d2, 0)
    # (G2 cell (a, b) -> (a + d2, b): b - (a + d2) >= 0 ; G1 (i, j) -> (i + d2, j): i - j >= d1 + d2)
    T2[:, 0] += d2
    return dict(L=L, f=f, ox=ox, oy=oy, d1=d1, d2=d2, D=D, n_up=int(up.sum()), n_g1=int(g1.sum()),
                n_g2=int((~g1).sum()), n_tilt=int(len(T)), lattice_res=(float(res1), float(res2)),
                tilted=T2)


def fold_window(T, p, k=None, u0=None):
    """Tilted squares in a window of p steps along u = (x + y)/sqrt2, taken from the seam middle."""
    u = (T[:, 0] + T[:, 1]) / SQ2
    order = np.argsort(u); T = T[order]; u = u[order]
    if u0 is None:
        u0 = 0.5 * (u.min() + u.max()) - 0.5 * p * SQ2
    sel = (u >= u0) & (u < u0 + p * SQ2)
    W = T[sel]
    if k is not None and len(W) != k:
        # take the k squares nearest the window centre
        c = u0 + 0.5 * p * SQ2
        idx = np.argsort(np.abs(u - c))[:k]
        W = T[np.sort(idx)]
    return W, u0


def fold_average(T, W, p, reach=3, tol=0.2):
    """Average each window square over its copies at t*(p, p), |t| <= reach (the folded seam)."""
    out = []
    for x, y, th in W:
        acc = []
        for t in range(-reach, reach + 1):
            q = np.array([x + t * p, y + t * p])
            d = np.hypot(T[:, 0] - q[0], T[:, 1] - q[1])
            j = int(np.argmin(d))
            if d[j] < tol:
                da = ((T[j, 2] - th) + math.pi / 4) % HALF - math.pi / 4
                acc.append((T[j, 0] - t * p, T[j, 1] - t * p, th + da))
        out.append(np.mean(acc, axis=0) if acc else np.array([x, y, th]))
    return np.array(out)


def period_residual(T, p):
    """For each tilted square in the seam middle, distance to the nearest tilted square shifted by
    (p, p), with angle mod 90 deg compared too.  Small median = period p."""
    u = (T[:, 0] + T[:, 1]) / SQ2
    lo, hi = np.quantile(u, 0.25), np.quantile(u, 0.75) - p * SQ2
    out = []
    for i in np.where((u >= lo) & (u <= hi))[0]:
        q = T[i, :2] + p
        d = np.hypot(T[:, 0] - q[0], T[:, 1] - q[1])
        j = int(np.argmin(d))
        da = abs(((T[j, 2] - T[i, 2]) + math.pi / 4) % HALF - math.pi / 4)
        out.append(d[j] + da)
    return float(np.median(out)) if out else float('nan'), len(out)


# ------------------------------------------------------------------------------------- solver
def _fun(z, k, p, D, s, im, f, lo):
    g = np.empty_like(z)
    E = energy_grad(z, k, p, D, s, im, g)
    # grids must not collide: ox + oy + D >= 2 (sufficient, see cert.py)
    c = 2.0 - D - z[3 * k] - z[3 * k + 1]
    if c > 0:
        E += 100 * c * c; g[3 * k] -= 200 * c; g[3 * k + 1] -= 200 * c
    return E, g


def relax(z, k, p, D, f, s=1.0, im=1, lo=None, iters=3000, free_o=True):
    lo = f - 0.35 if lo is None else lo
    b = [(None, None)] * (3 * k) + ([(lo, f), (lo, f)] if free_o else [(z[3 * k],) * 2, (z[3 * k + 1],) * 2])
    r = minimize(_fun, z, args=(k, p, D, s, im, f, lo), jac=True, method='L-BFGS-B', bounds=b,
                 options=dict(maxiter=iters, maxfun=iters * 2, ftol=1e-30, gtol=1e-16, maxcor=30))
    return r.x, float(r.fun)


def random_start(k, p, D, f, rs):
    """Tilted centres spread along the seam between the two staircases."""
    z = np.empty(3 * k + 2)
    # seam centre line in canonical frame: midway between G1 tips (x - y = ox + D - 1)
    # and G2 tips (x - y = 1 - oy)
    vmid = 0.5 * ((f + D - 1) + (1 - f))
    vhalf = 0.5 * max(0.05, (f + D - 1) - (1 - f)) + 0.35
    for i in range(k):
        u = rs.uniform(0, p * SQ2)
        w = vmid + rs.uniform(-vhalf, vhalf)          # w = x - y
        uu = u * SQ2                                   # x + y
        z[3 * i] = 0.5 * (uu + w); z[3 * i + 1] = 0.5 * (uu - w)
        z[3 * i + 2] = rs.uniform(0, HALF)
    z[3 * k] = f; z[3 * k + 1] = f
    return z


SCHED = (0.70, 0.80, 0.88, 0.94, 0.98, 1.0)


def feasible_at(z, k, p, D, f, delta=1e-7, sched=SCHED, im=1, iters=3000):
    """Grow the squares from small to side 1 + delta, relaxing at each step.  Returns (z, E)."""
    E = None
    for s in sched:
        z, E = relax(z, k, p, D, f, s=s, im=im, iters=iters)
    z, E = relax(z, k, p, D, f, s=1.0 + delta, im=im, iters=iters * 2)
    return z, E


def split(z, k):
    return z[:3 * k].reshape(k, 3), float(z[3 * k]), float(z[3 * k + 1])


def cert_z(z, k, p, D, f):
    sq, ox, oy = split(z, k)
    return certify(sq, p, ox, oy, D, f)


def minimise_f(z, k, p, D, f, step=0.004, tol=2e-5, delta=1e-7, iters=3000):
    """Continuation: lower f while the cell stays feasible (penalty zero at side 1 + delta and the
    independent certificate positive).  Returns (f_star, z_star)."""
    best = (f, z.copy())
    while step >= tol:
        f2 = best[0] - step
        z2 = best[1].copy()
        z2[3 * k] = min(z2[3 * k], f2); z2[3 * k + 1] = min(z2[3 * k + 1], f2)
        z2, E = relax(z2, k, p, D, f2, s=1.0 + delta, iters=iters)
        ok = E < 1e-26 and cert_z(z2, k, p, D, f2)[0] > 0
        if ok:
            best = (f2, z2)
        else:
            step *= 0.5
    return best


def minf_full(z, k, p, D, f):
    """Penalty continuation, then the fixed-line NLP to the local jam.  Returns (f_star, z)."""
    from nlp import polish
    fs, zs = minimise_f(z, k, p, D, f)
    zs = zs.copy(); zs[3 * k] = min(zs[3 * k], fs); zs[3 * k + 1] = min(zs[3 * k + 1], fs)
    f2, z2 = polish(zs, k, p, D)
    if f2 < fs and cert_z(z2, k, p, D, f2)[0] > 0:
        return f2, z2
    return fs, zs


def job(args):
    """One multistart: (k, p, D, f, seed) -> record or None."""
    k, p, D, f, seed, delta, extra = args
    rs = np.random.default_rng(seed)
    z = random_start(k, p, D, f, rs) if extra is None else np.array(extra, float)
    z, E = feasible_at(z, k, p, D, f, delta=delta)
    c = cert_z(z, k, p, D, f)
    ok = E < 1e-26 and c[0] > 0
    f_nlp = None
    if not ok and E < NLP_E:
        # near-feasible: the penalty stalls within ~1e-3 of a jam, so let the fixed-line NLP restore
        # feasibility and minimise f; accept if its certified jam is at or below the target f
        from nlp import polish
        fs, z2 = polish(z, k, p, D)
        if fs <= f + 1e-12:
            c2 = cert_z(z2, k, p, D, f)
            if c2[0] > 0:
                z, c, ok, f_nlp = z2, c2, True, fs
    return dict(k=k, p=p, D=D, f=f, seed=seed, E=E, cert=c[0], worst=c[1], ok=bool(ok), f_nlp=f_nlp,
                z=z.tolist() if ok else None)


NLP_E = 1e-4


def rec_out(r, f_star=None):
    k, p, D = r['k'], r['p'], r['D']
    o = dict(p=p, k=k, D=D, gain_per_step=k / p - (D - 1), f=r['f'], f_star=f_star, ok=r['ok'],
             cert=r['cert'], seed=r['seed'])
    if r.get('z') is not None:
        sq, ox, oy = split(np.array(r['z']), k)
        o.update(ox=ox, oy=oy, coords=sq.tolist())
    return o


# ---------------------------------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('mine'); a.add_argument('--in', dest='inp', required=True); a.add_argument('--p', default='1..6')
    a = sub.add_parser('fold')
    a.add_argument('--in', dest='inp', required=True); a.add_argument('--p', type=int, required=True)
    a.add_argument('--k', type=int); a.add_argument('--f', type=float); a.add_argument('--no-images', action='store_true')
    a.add_argument('--minf', action='store_true'); a.add_argument('--raw', action='store_true', help='no fold averaging')
    a.add_argument('--grow', action='store_true'); a.add_argument('--grow-from', type=float, default=0.94)
    a = sub.add_parser('cell')
    a.add_argument('--f', type=float, required=True); a.add_argument('--p', default='1..6'); a.add_argument('--D', default='1..4')
    a.add_argument('--gain', type=float, default=0.80); a.add_argument('--gmax', type=float, default=1.2)
    a.add_argument('--starts', type=int, default=200); a.add_argument('--workers', type=int, default=12)
    a.add_argument('--delta', type=float, default=1e-7); a.add_argument('--seed', type=int, default=1)
    a.add_argument('--minf', action='store_true'); a.add_argument('--stop-first', action='store_true')
    a.add_argument('--warm', help='jsonl of z vectors to add as starts')
    a = sub.add_parser('perturb')
    a.add_argument('--cell', required=True, help='json record with coords, ox, oy, p, k, D')
    a.add_argument('--f', type=float, required=True); a.add_argument('--starts', type=int, default=50)
    a.add_argument('--dang', type=float, default=5.0); a.add_argument('--dpos', type=float, default=0.1)
    a.add_argument('--workers', type=int, default=12); a.add_argument('--seed', type=int, default=7)
    A = ap.parse_args()

    if A.cmd == 'mine':
        P = load_csv(A.inp); M = mine(P)
        T = M.pop('tilted')
        print(json.dumps({k: v for k, v in M.items()}), file=sys.stderr)
        ang = np.degrees(np.mod(T[:, 2], HALF))
        print(f'tilted angles deg: median {np.median(ang):.3f}, range {ang.min():.2f}..{ang.max():.2f}', file=sys.stderr)
        for p in rng_list(A.p):
            res, cnt = period_residual(T, p)
            W, u0 = fold_window(T, p)
            print(json.dumps(dict(src=A.inp, p=p, k=len(W), D=M['D'], f=M['f'], ox=M['ox'], oy=M['oy'],
                                  period_residual=res, n_checked=cnt,
                                  gain_per_step=len(W) / p - (M['D'] - 1), u0=u0, coords=W.tolist())))
        return

    if A.cmd == 'fold':
        P = load_csv(A.inp); M = mine(P); T = M['tilted']
        W, u0 = fold_window(T, A.p, A.k)
        if not A.raw:
            W = fold_average(T, W, A.p)
        k = len(W); f = A.f if A.f is not None else M['f']
        z = np.concatenate([W.ravel(), [min(M['ox'], f), min(M['oy'], f)]])
        c0 = certify(W, A.p, M['ox'], M['oy'], M['D'], f)
        im = 0 if A.no_images else 1
        if A.grow:
            # shrink the squares and grow them back to side 1 + 1e-7, starting from the fold
            sched = tuple(s for s in SCHED if s >= A.grow_from)
            z2, E = feasible_at(z.copy(), k, A.p, M['D'], f, sched=sched, im=im, iters=20000)
        else:
            # local relax only: the fold is the start
            z2, E = relax(z.copy(), k, A.p, M['D'], f, s=1.0 + 1e-7, im=im, iters=20000)
        c = cert_z(z2, k, A.p, M['D'], f)
        ok = E < 1e-26 and c[0] > 0
        out = dict(src=A.inp, p=A.p, k=k, D=M['D'], f=f, images=bool(im), fold_cert=c0[0], fold_worst=c0[1],
                   E=E, cert=c[0], worst=c[1], ok=bool(ok), gain_per_step=k / A.p - (M['D'] - 1))
        if ok and A.minf:
            fs, zs = minf_full(z2, k, A.p, M['D'], f)
            out['f_star'] = fs; out['cert_star'] = cert_z(zs, k, A.p, M['D'], fs)[0]
            sq, ox, oy = split(zs, k); out.update(ox=ox, oy=oy, coords=sq.tolist())
        print(json.dumps(out))
        return

    if A.cmd in ('cell', 'perturb'):
        from multiprocessing import Pool
        jobs = []
        if A.cmd == 'cell':
            rs = np.random.default_rng(A.seed)
            for D in rng_list(A.D):
                if 2 * A.f + D < 2:
                    continue
                for p in rng_list(A.p):
                    for k in range(1, 6 * p + 1):
                        g = k / p - (D - 1)
                        if g < A.gain - 1e-12 or g > A.gmax + 1e-12:
                            continue
                        # area bound: tilted area per step <= free area per step 2f + D - 1
                        if k / p > 2 * A.f + D - 1:
                            continue
                        for s in range(A.starts):
                            jobs.append((k, p, D, A.f, int(rs.integers(1 << 62)), A.delta, None))
            if A.warm:
                for l in open(A.warm):
                    r = json.loads(l)
                    z = np.concatenate([np.array(r['coords']).ravel(), [min(r['ox'], A.f), min(r['oy'], A.f)]])
                    jobs.append((r['k'], r['p'], r['D'], A.f, 10**9 + len(jobs), A.delta, z.tolist()))
        else:
            r = json.loads(open(A.cell).read().splitlines()[0])
            rs = np.random.default_rng(A.seed)
            C = np.array(r['coords'])
            for s in range(A.starts):
                C2 = C.copy()
                C2[:, :2] += rs.uniform(-A.dpos, A.dpos, C2[:, :2].shape)
                C2[:, 2] += np.radians(rs.uniform(-A.dang, A.dang, len(C2)))
                z = np.concatenate([C2.ravel(), [A.f, A.f]])
                jobs.append((r['k'], r['p'], r['D'], A.f, s, 1e-7, z.tolist()))
        # cheapest configurations first so early answers arrive early
        jobs.sort(key=lambda j: (j[0] * 1.0, j[2]))
        print(f'# {len(jobs)} jobs', file=sys.stderr)
        t0 = time.time(); nok = {}
        with Pool(A.workers) as pool:
            for r in pool.imap_unordered(job, jobs, chunksize=1):
                key = (r['p'], r['k'], r['D'])
                nok.setdefault(key, [0, 0]); nok[key][1] += 1
                print(f"# job p={r['p']} k={r['k']} D={r['D']} seed={r['seed']} ok={int(r['ok'])} E={r['E']:.2e} cert={r['cert']:.2e} f_nlp={r['f_nlp']} t={time.time() - t0:.0f}", file=sys.stderr, flush=True)
                if r['ok']:
                    nok[key][0] += 1
                    fs = None
                    if getattr(A, 'minf', False):
                        fs, zs = minf_full(np.array(r['z']), r['k'], r['p'], r['D'], r['f'])
                        r['z'] = zs.tolist()
                    print(json.dumps(rec_out(r, fs)), flush=True)
                    if getattr(A, 'stop_first', False):
                        pool.terminate(); break
        for key in sorted(nok):
            p, k, D = key
            print(f'# p={p} k={k} D={D} gain={k / p - (D - 1):.3f} ok {nok[key][0]}/{nok[key][1]}', file=sys.stderr)
        print(f'# wall {time.time() - t0:.0f}s', file=sys.stderr)
        return


if __name__ == '__main__':
    main()
