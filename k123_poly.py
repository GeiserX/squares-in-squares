#!/usr/bin/env python3
"""The best rigid 45 degree shape at one side fraction, as one exact 0/1 program (avenues/k123.md, section 8).

Every square is either upright on one of the four corner lattices, or tilted by 45 degrees on one tilted
lattice. The program picks any set of sites of the tilted lattice and any set of upright cells, with no
two squares overlapping, and counts the squares. So it covers every rigid 45 degree shape at once (a
rectangle, a shape with steps, several blocks on the same tilted lattice), not only a x b blocks.

The tilted lattice is pinned: one face of its squares lies on the line x + y = K through the lattice
points of the bottom left corner, and one face lies on a tooth line of the bottom right corner (BR, with
x - y = L - K2) or of the top left corner (TL, with y - x = L - K2), or a vertex of a tilted square lies on
a wall (WL, WB, WR, WT: left, bottom, right, top). WW0 and WW1 are the two lattices with a vertex on
the left wall and a vertex on the bottom wall, and no tooth line. At the rigid side fraction of a chain of w squares the
chain then stands tooth to tooth. A shape that fits at a smaller side fraction with the same contacts
still fits at F, so one scan just below a held side fraction covers every such shape below it.

  k123_poly.py solve M F K PIN K2 [--sec 60] [--out FILE.csv]     one program
  k123_poly.py scan  M F K0 K1 K20 K21 OUT.jsonl [--sec 60] [--write DIR] [--min GAIN]   every pin in the ranges
  k123_poly.py build N DETAILS OUTDIR FILE.csv [...]             squeeze a written shape (family_step: LP, fq)

Control: solve 25 0.52082 13 BR 13 must give 626 (the held 17 x 17 block). At F = 0.5200 the same pin must
give 625 or less from a 17 chain (the chain no longer fits).
Our own code. It needs numpy and scipy (HiGHS through scipy.optimize.milp).
"""
import argparse, json, math, os, sys, time

import numpy as np
from scipy import sparse
from scipy.optimize import milp, LinearConstraint, Bounds

R2 = math.sqrt(2.0)
TOL = 1e-7
U = np.array([1.0, 1.0]) / R2
V = np.array([-1.0, 1.0]) / R2
HT = 0.5 + R2 / 2          # half extent of the pair (tilted, upright) on each of the four axes


def candidates(m, f, K, pin, K2):
    L = m + f
    up = []
    for ax in (0, 1):
        for ay in (0, 1):
            for i in range(m):
                for j in range(m):
                    up.append((i + 0.5 if ax == 0 else L - i - 0.5, j + 0.5 if ay == 0 else L - j - 0.5))
    up = np.array(up)
    ou = K / R2 + 0.5
    if pin in ('WW0', 'WW1'):   # no tooth line: a vertex on the left wall and a vertex on the bottom wall (K is not used)
        ou = 0.0 if pin == 'WW0' else 0.5
        ov = ou
    elif pin == 'BR':
        ov = (K2 - L) / R2 + 0.5
    elif pin == 'TL':
        ov = (L - K2) / R2 - 0.5
    else:                       # a vertex of a tilted square on a wall: left, bottom, right, top
        ov = {'WL': ou, 'WB': -ou, 'WR': ou - R2 * L, 'WT': R2 * L - ou}[pin]
    o = ou * U + ov * V
    r = int(2 * L) + 3
    ti = []
    h = R2 / 2
    for i in range(-r, r + 1):
        for j in range(-r, r + 1):
            c = o + i * U + j * V
            if c[0] - h >= -TOL and c[0] + h <= L + TOL and c[1] - h >= -TOL and c[1] + h <= L + TOL:
                ti.append((c[0], c[1]))
    return L, up, np.array(ti).reshape(-1, 2)


def program(L, up, ti):
    """-> (A, n) with A x <= 1 for every clique of squares that overlap pairwise."""
    nu, nt = len(up), len(ti)
    n = nu + nt
    allc = np.vstack([up, ti]) if nt else up
    tilted = np.arange(n) >= nu
    # cliques from sample points: every square that holds the point inside overlaps every other one
    step = 0.2
    g = np.arange(0.037, L, step)
    px, py = np.meshgrid(g, g + 0.011)
    P = np.c_[px.ravel(), py.ravel()]
    cell = {}
    for q in range(n):
        cell.setdefault((int(allc[q, 0]), int(allc[q, 1])), []).append(q)
    cliques = set()
    for p in P:
        ix, iy = int(p[0]), int(p[1])
        mem = []
        for a in (ix - 1, ix, ix + 1):
            for b in (iy - 1, iy, iy + 1):
                for q in cell.get((a, b), ()):
                    d = p - allc[q]
                    if tilted[q]:
                        if abs(d @ U) < 0.5 - 1e-6 and abs(d @ V) < 0.5 - 1e-6:
                            mem.append(q)
                    elif abs(d[0]) < 0.5 - 1e-6 and abs(d[1]) < 0.5 - 1e-6:
                        mem.append(q)
        if len(mem) > 1:
            cliques.add(tuple(sorted(mem)))
    covered = set()
    for c in cliques:
        for a in range(len(c)):
            for b in range(a + 1, len(c)):
                covered.add((c[a], c[b]))
    # every exact pair that no clique holds
    pairs = []
    for q in range(n):
        ix, iy = int(allc[q, 0]), int(allc[q, 1])
        for a in (ix - 2, ix - 1, ix, ix + 1, ix + 2):
            for b in (iy - 2, iy - 1, iy, iy + 1, iy + 2):
                for r in cell.get((a, b), ()):
                    if r <= q or (q, r) in covered:
                        continue
                    d = allc[r] - allc[q]
                    if tilted[q] and tilted[r]:
                        continue
                    if not tilted[q] and not tilted[r]:
                        hit = abs(d[0]) < 1 - TOL and abs(d[1]) < 1 - TOL
                    else:
                        hit = abs(d[0]) < HT - TOL and abs(d[1]) < HT - TOL and abs(d @ U) < HT - TOL and abs(d @ V) < HT - TOL
                    if hit:
                        pairs.append((q, r))
    rows = [list(c) for c in cliques] + [list(p) for p in pairs]
    ri = np.concatenate([np.full(len(r), k) for k, r in enumerate(rows)])
    ci = np.concatenate([np.array(r) for r in rows])
    A = sparse.csr_matrix((np.ones(len(ri)), (ri, ci)), shape=(len(rows), n))
    return A, n


def solve(m, f, K, pin, K2, sec=60.0):
    t0 = time.time()
    L, up, ti = candidates(m, f, K, pin, K2)
    A, n = program(L, up, ti)
    nu = len(up)
    w = np.ones(n)
    w[:nu] += 1e-6 * (3 - np.arange(nu) // (m * m))          # break the tie between the four lattices
    res = milp(-w, constraints=LinearConstraint(A, ub=np.ones(A.shape[0])), integrality=np.ones(n), bounds=Bounds(0, 1),
               options=dict(time_limit=sec, mip_rel_gap=0.0))
    if res.x is None:
        return dict(m=m, f=f, K=K, pin=pin, K2=K2, count=0, status=int(res.status), sec=round(time.time() - t0, 1)), None
    x = res.x > 0.5
    cnt = int(x.sum()); nt = int(x[nu:].sum())
    bound = -float(res.mip_dual_bound) if getattr(res, 'mip_dual_bound', None) is not None else float('nan')
    rows = [(up[q, 0], up[q, 1], 0.0) for q in range(nu) if x[q]] + [(ti[q, 0], ti[q, 1], 45.0) for q in range(len(ti)) if x[nu + q]]
    info = dict(m=m, f=f, K=K, pin=pin, K2=K2, count=cnt, gain=cnt - m * m, tilted=nt, bound=round(bound, 3), status=int(res.status),
                rows=A.shape[0], cols=n, sec=round(time.time() - t0, 1))
    return info, (L, np.array(rows))


def write(path, L, P):
    """x, y, degrees: one row per square, centre and turn (the reader of family_step takes it through its own writer)."""
    with open(path + '.tmp', 'w') as o:
        o.write('# side %.12f\n' % L)
        for x, y, d in P:
            o.write('%.12f,%.12f,%.6f\n' % (x, y, d))
    os.replace(path + '.tmp', path)


def build(a):
    import csv
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import family_step as fs
    held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(a.details))}
    Ln = (held[a.n] + 1) * math.sqrt(a.n)
    os.makedirs(a.outdir, exist_ok=True)
    for p in a.files:
        P = np.loadtxt(p, delimiter=',', comments='#').reshape(-1, 3)
        P[:, 2] = np.radians(P[:, 2])
        if len(P) < a.n:
            print('%s holds %d, not %d' % (p, len(P), a.n), flush=True); continue
        if len(P) > a.n:                                 # drop the uprights nearest a far corner
            up = np.nonzero(np.abs(P[:, 2]) < 1e-9)[0]
            d = np.abs(P[up, 1] - P[up, 0])
            gone = set(up[np.argsort(-d)][:len(P) - a.n].tolist())
            P = P[[i for i in range(len(P)) if i not in gone]]
        t0 = time.time(); fs.set_limit(a.sec)
        try:
            X, Lx, trace = fs.squeeze(P, iters=a.iters, fq=True)
        except fs.Unreadable as ex:
            print('n %d: %s' % (a.n, ex), flush=True); continue
        tag = os.path.basename(p)[:-4]
        fs.write_rows('%s/%d-%s.csv' % (a.outdir, a.n, tag), a.n, X)
        print('n %d %s: -> %.9f (held %.9f) %s  %.0f s  trace %s' % (
            a.n, tag, Lx, Ln, 'BELOW' if Lx < Ln - 1e-9 else 'above', time.time() - t0, [(t[0], round(t[1], 9)) for t in trace]), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    q = sp.add_parser('solve'); q.add_argument('m', type=int); q.add_argument('f', type=float); q.add_argument('K', type=int)
    q.add_argument('pin'); q.add_argument('K2', type=int); q.add_argument('--sec', type=float, default=60); q.add_argument('--out')
    q = sp.add_parser('scan'); q.add_argument('m', type=int); q.add_argument('f', type=float)
    for name in ('K0', 'K1', 'K20', 'K21'):
        q.add_argument(name, type=int)
    q.add_argument('out'); q.add_argument('--sec', type=float, default=60); q.add_argument('--write'); q.add_argument('--pins', default='BR,TL,WL,WB,WR,WT')
    q.add_argument('--deadline'); q.add_argument('--min', type=int, default=1)
    q = sp.add_parser('build'); q.add_argument('n', type=int); q.add_argument('details'); q.add_argument('outdir'); q.add_argument('files', nargs='+')
    q.add_argument('--iters', type=int, default=60); q.add_argument('--sec', type=float, default=600)
    a = ap.parse_args()
    if a.cmd == 'build':
        return build(a)
    if a.cmd == 'solve':
        info, sol = solve(a.m, a.f, a.K, a.pin, a.K2, a.sec)
        print(json.dumps(info))
        if a.out and sol:
            write(a.out, *sol)
        return
    out = open(a.out, 'a')
    if a.write:
        os.makedirs(a.write, exist_ok=True)
    for K in range(a.K0, a.K1 + 1):
        for pin in a.pins.split(','):
            for K2 in (range(a.K20, a.K21 + 1) if pin in ('BR', 'TL') else [0]):
                if a.deadline and time.time() > float(open(a.deadline).read().split()[0]):
                    return
                info, sol = solve(a.m, a.f, K, pin, K2, a.sec)
                out.write(json.dumps(info) + '\n'); out.flush()
                print(json.dumps(info), flush=True)
                if a.write and sol and info['count'] >= a.m * a.m + a.min:
                    write('%s/m%d-f%.5f-K%d-%s%d-n%d.csv' % (a.write, a.m, a.f, K, pin, K2, info['count']), *sol)


if __name__ == '__main__':
    main()
