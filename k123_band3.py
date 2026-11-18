#!/usr/bin/env python3
"""A band of chains from corner to corner at its own m (avenues/k123.md, section 7).

The held k = 3 layouts at m = 21, 22 and 24 are the band of m = 20 or 23 with whole rows added. A band
built at its own m is longer, holds more squares, and can turn further before it loses the count. This
tool walks the turn along the jam line of k123_block.fjam and keeps every turn that still holds m*m + k.

  k123_band3.py scan  M K W A B PHI0 PHI1 DPHI OUT.jsonl [--df 1e-4] [--offs 0,0.1,..] [--taus 0,0.03]
  k123_band3.py build DETAILS OUTDIR DEADLINE ROW.json [ROW.json ...]   squeeze (sequential LP, fq), write csv

A row is one json line: m, k, w, a, b, phi (degrees off 45), f, off, n (chains), i, pick, tau, gain.
Control: scan 20 3 3 A B 10.30 10.50 0.02 must hold 403 at the held turn of 10.42 degrees and lose it above.
Our own code. It imports k123_block (corridor, greedy, exact refill) and family_step (squeeze, fq).
"""
import argparse, json, math, os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import k123_block as kb


def layout(r, tau=None):
    """The tilted squares and the refill of one row. -> (L, T, F)"""
    m, w = r['m'], r['w']; L = m + r['f']
    al = math.radians(-45.0 + r['phi'])
    C = kb.Corridor(L, r['a'] + r['f'], r['b'] + r['f'], w)
    qa, qb = kb.qrange(L, al)
    ch = kb.greedy(C, al, qa + r['off'], qb)
    T = kb.squares(ch[r['i']:r['i'] + r['n']], al, w, r['pick'])
    F = kb.refill(L, T, r['tau'] if tau is None else tau)
    return L, T, F


def cmd_scan(a):
    out = open(a.out, 'a')
    m, k, w = a.m, a.k, a.w
    s = a.a + a.b
    for phi in np.arange(a.phi0, a.phi1 + 1e-9, a.dphi):
        f = kb.fjam(w, s, -1, math.radians(phi)) + a.df
        L = m + f
        al = math.radians(-45.0 + phi)
        C = kb.Corridor(L, a.a + f, a.b + f, w)
        qa, qb = kb.qrange(L, al)
        best = None; seen = set()
        for off in a.offs:
            ch = kb.greedy(C, al, qa + off, qb)
            key = tuple(round(c[0], 4) for c in ch)
            if not ch or key in seen:
                continue
            seen.add(key)
            for n in range(len(ch), max(0, len(ch) - a.drop - 1), -1):
                for i in kb.runs(ch, n):
                    T = kb.squares(ch[i:i + n], al, w, 'mid')
                    for tau in a.taus:
                        F = kb.refill(L, T, tau)
                        row = dict(m=m, k=k, w=w, a=a.a, b=a.b, phi=round(float(phi), 4), f=round(float(f), 7), off=off, n=n, i=i,
                                   pick='mid', tau=tau, gain=len(F) - m * m, tilted=len(T), chains=len(ch))
                        out.write(json.dumps(row) + '\n'); out.flush()
                        if best is None or row['gain'] > best['gain']:
                            best = row
        if best:
            print('m %d w %d ab %d,%d phi %.3f f %.6f: best gain %+d (%d chains of %d, off %.2f, tau %.2f)' % (
                m, w, a.a, a.b, phi, f, best['gain'], best['n'], best['chains'], best['off'], best['tau']), flush=True)
        else:
            print('m %d w %d ab %d,%d phi %.3f f %.6f: no chain' % (m, w, a.a, a.b, phi, f), flush=True)


def cmd_build(a):
    import csv
    import family_step as fs
    stop = lambda: time.time() > float(open(a.deadline).read().split()[0])
    held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(a.details))}
    os.makedirs(a.out, exist_ok=True)
    for line in a.rows:
        r = json.loads(open(line).read() if os.path.exists(line) else line)
        n = r['m'] * r['m'] + r['k']
        L, T, F = layout(r)
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
        tag = 'w%d-ab%d%d-n%d-phi%.3f-tau%.2f' % (r['w'], r['a'], r['b'], r['n'], r['phi'], r['tau'])
        fs.write_rows('%s/%d-%s.csv' % (a.out, n, tag), n, X)
        print('n %d %s: built %.9f -> %.9f (held %.9f) %s  %.0f s  trace %s' % (
            n, tag, L, Lx, Ln, 'BELOW' if Lx < Ln - 1e-9 else 'above', time.time() - t0, [(t[0], round(t[1], 9)) for t in trace]), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    fl = lambda s: [float(x) for x in s.split(',')]
    q = sp.add_parser('scan')
    for name in ('m', 'k', 'w', 'a', 'b'):
        q.add_argument(name, type=int)
    for name in ('phi0', 'phi1', 'dphi'):
        q.add_argument(name, type=float)
    q.add_argument('out'); q.add_argument('--df', type=float, default=1e-4); q.add_argument('--offs', type=fl, default=[0.0, 0.1, 0.35, 0.7, 1.05])
    q.add_argument('--taus', type=fl, default=[0.0, 0.03]); q.add_argument('--drop', type=int, default=0); q.set_defaults(fn=cmd_scan)
    q = sp.add_parser('build'); q.add_argument('details'); q.add_argument('out'); q.add_argument('deadline'); q.add_argument('rows', nargs='+')
    q.add_argument('--iters', type=int, default=60); q.add_argument('--sec', type=float, default=900); q.set_defaults(fn=cmd_build)
    a = ap.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
