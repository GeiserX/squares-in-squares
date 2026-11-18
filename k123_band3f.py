#!/usr/bin/env python3
"""A band of chains with its start offset scanned, for turns where the greedy start fails (avenues/k123.md, section 10).

k123_block.greedy puts each chain at the smallest feasible height. Below a turn of atan(1/7) = 8.13 degrees that
start sits on the edge of a forbidden window, and every seventh chain drifts into it, so the greedy never
gives a full band there. This tool places the chains on a comb q0 + x0 + k (k whole) and scans x0. It keeps
the longest runs of feasible chains, refills them and counts.

  k123_band3f.py scan  M K W A B PHI0 PHI1 DPHI OUT.jsonl [--df 1e-4] [--dx 0.01] [--taus 0,0.03,0.06]
                       [--save DIR] [--top 6]
  k123_band3f.py build DETAILS OUTDIR DEADLINE LAYOUT.npy [...] [--iters 60] [--sec 600]

scan writes one json line per run it refilled (m, k, w, a, b, phi, f, x0, chains, tau, gain). With --save it
writes the layout of each row that holds m*m + k or more to DIR/<n>-<tag>.npy (x, y, radians).
build squeezes a saved layout (family_step: sequential LP, then fq) and writes OUTDIR/<n>-<tag>.csv.
Control: scan 20 3 3 1 2 10.40 10.44 0.02 must hold 403 (the held band of 25 chains), as k123_band3.py does.
Our own code. It imports k123_block (corridor, slide bounds, exact refill) and family_step.
"""
import argparse, json, math, os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import k123_block as kb


def comb_runs(C, al, qa, qb, x0):
    """The maximal runs of feasible chains on the comb qa + x0 + k. -> list of lists of (q, lo, hi)"""
    out = []; cur = []
    q = qa + x0
    while q < qb:
        lo, hi = kb.bounds(C, q, al)
        if lo <= hi:
            cur.append((q, lo, hi))
        else:
            if cur:
                out.append(cur)
            cur = []
        q += 1 + 2e-9
    if cur:
        out.append(cur)
    return out


def cmd_scan(a):
    out = open(a.out, 'a')
    m, k, w = a.m, a.k, a.w; s = a.a + a.b
    if a.save:
        os.makedirs(a.save, exist_ok=True)
    for phi in np.arange(a.phi0, a.phi1 + 1e-9, a.dphi):
        f = kb.fjam(w, s, -1, math.radians(phi)) + a.df
        L = m + f; al = math.radians(-45.0 + phi)
        C = kb.Corridor(L, a.a + f, a.b + f, w)
        qa, qb = kb.qrange(L, al)
        cand = []
        for x0 in np.arange(0.0, 1.0, a.dx):
            for run in comb_runs(C, al, qa, qb, float(x0)):
                cand.append((len(run), float(x0), run))
        if not cand:
            print('m %d phi %.3f f %.6f: no chain' % (m, phi, f), flush=True); continue
        top = max(c[0] for c in cand)
        # one candidate per distinct run (same first height to 1e-6), longest first
        seen = set(); pick = []
        for n, x0, run in sorted(cand, key=lambda c: -c[0]):
            key = (n, round(run[0][0] % 1.0, 3))
            if n < top - 1 or key in seen:
                continue
            seen.add(key); pick.append((n, x0, run))
        best = None
        for n, x0, run in pick[:a.top]:
            T = kb.squares(run, al, w, 'mid')
            for tau in a.taus:
                F = kb.refill(L, T, tau)
                row = dict(m=m, k=k, w=w, a=a.a, b=a.b, phi=round(float(phi), 4), f=round(float(f), 7), x0=round(x0, 4),
                           chains=n, tau=tau, gain=len(F) - m * m, tilted=len(T))
                out.write(json.dumps(row) + '\n'); out.flush()
                if best is None or row['gain'] > best['gain']:
                    best = row
                if a.save and row['gain'] >= k:
                    tag = 'w%d-ab%d%d-n%d-phi%.3f-x%.3f-tau%.2f' % (w, a.a, a.b, n, phi, x0, tau)
                    np.save('%s/%d-%s.npy' % (a.save, m * m + k, tag), np.asarray(F, float))
                    break
        print('m %d w %d ab %d,%d phi %.3f f %.6f: longest run %d chains, best gain %+d (x0 %.2f, tau %.2f), %d runs refilled' % (
            m, w, a.a, a.b, phi, f, top, best['gain'], best['x0'], best['tau'], min(len(pick), a.top)), flush=True)


def cmd_build(a):
    import csv
    import family_step as fs
    stop = lambda: time.time() > float(open(a.deadline).read().split()[0])
    held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(a.details))}
    os.makedirs(a.out, exist_ok=True)
    for path in a.layouts:
        base = os.path.basename(path)[:-4]; n = int(base.split('-')[0])
        F = np.load(path)
        if len(F) < n:
            print('%s holds %d, not %d' % (base, len(F), n), flush=True); continue
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
        fs.write_rows('%s/%s.csv' % (a.out, base), n, X)
        print('n %d %s: -> %.9f (held %.9f) %s  %.0f s  trace %s' % (
            n, base, Lx, Ln, 'BELOW' if Lx < Ln - 1e-9 else 'above', time.time() - t0, [(t[0], round(t[1], 9)) for t in trace]), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    fl = lambda s: [float(x) for x in s.split(',')]
    q = sp.add_parser('scan')
    for name in ('m', 'k', 'w', 'a', 'b'):
        q.add_argument(name, type=int)
    for name in ('phi0', 'phi1', 'dphi'):
        q.add_argument(name, type=float)
    q.add_argument('out'); q.add_argument('--df', type=float, default=1e-4); q.add_argument('--dx', type=float, default=0.01)
    q.add_argument('--taus', type=fl, default=[0.0, 0.03, 0.06]); q.add_argument('--save', default=''); q.add_argument('--top', type=int, default=6)
    q.set_defaults(fn=cmd_scan)
    q = sp.add_parser('build'); q.add_argument('details'); q.add_argument('out'); q.add_argument('deadline'); q.add_argument('layouts', nargs='+')
    q.add_argument('--iters', type=int, default=60); q.add_argument('--sec', type=float, default=600); q.set_defaults(fn=cmd_build)
    a = ap.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
