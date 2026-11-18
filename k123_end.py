#!/usr/bin/env python3
"""The end of a band of chains, edited, then counted with the exact refill (avenues/k123.md, round 21).

A band of chains runs from corner to corner. Its count is the band plus the uprights that the exact refill
(Evan Daniel's fillfast, MIT, imported from his clone through EVAND_PACKER) puts on the four wall lattices.
With the tilted squares fixed, more room adds no upright until the side grows by a whole unit, so a square
more has to come from the tilted part. This tool edits the first or the last chain of the band, moves the
band, and counts:

  none        the band as it is
  dropc       the end chain removed (dropc2: at both ends)
  addc        one chain more at the end (the end chain moved by the pitch of the band)
  drop-lo/hi  the end chain loses its square at one end
  add-lo/hi   the end chain gains a square at one end, along its axis
  slide+-S    the end chain slides along its axis by S

Each edited band is moved along the diagonal (tau, about the centre of the box) and across it (delta), and
counted at every side of a grid. The tilted squares must stay apart and inside the box. For each count the
lowest side is kept, and the best starts of the counts near their bars are written for a quench.

  k123_end.py scan CUR.csv BARS.tsv OUTDIR N [N ...] [--lo -0.02] [--step 0.0025] [--over 0.012]
         [--taus -0.1,0,0.1] [--deltas -0.1,0,0.1] [--edits ...] [--targets 0,1]
  k123_end.py ctl  CUR.csv N OUTDIR        the controls (each can fail): the band of N with its end chain
         removed must come back to N with addc, and with one square of the end chain removed it must come
         back to N with add-lo or add-hi, at the side of N.
Lines: n edit end tau delta count side bar room. Finish a start with k123_turn.py (--turns=0, fq) and certify
with methods_take.py. Our own code; it imports methods_lp, family_step and k123_join and does not change them.
"""
import argparse, math, os, sys, time

import numpy as np

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
sys.path.insert(0, os.environ.get('EVAND_PACKER', '$SCRATCH/bounties-squares/ext/evand/search/packer'))
import methods_lp as mlp  # noqa: E402
import family_step as fs  # noqa: E402
import k123_join as kj  # noqa: E402

EDITS = ['none', 'dropc', 'addc', 'drop-lo', 'drop-hi', 'addj', 'slide+0.2', 'slide-0.2', 'slide+0.4', 'slide-0.4']


def refill(L, T):
    import fillfast
    X = T.copy(); X[:, 2] = np.degrees(X[:, 2])
    F = fillfast.fill(L, X, 'exact', tau=0.0)
    F[:, 2] = np.radians(F[:, 2])
    return F


def axis(Q, g):
    """Unit vector along chain g (from its first square to its last) and the spacing of its squares."""
    P = Q[g, :2]
    if len(g) < 2:
        a = float(Q[g[0], 2]); return np.array([math.cos(a), math.sin(a)]), 1.0, g
    d = P[-1] - P[0]; u = d / np.linalg.norm(d)
    if u[0] - u[1] < 0:                       # the same sense in every layout: across the band, to the bottom right
        u = -u
    o = np.argsort(P @ u); g = np.asarray(g)[o]
    sp = float(np.mean(np.diff(Q[g, :2] @ u)))
    return u, sp, g


def edit(Q, G, kind):
    """The tilted squares after one edit of chain 0. -> array (k, 3) or None"""
    T = [Q[g] for g in G]
    g0 = np.asarray(G[0]); u, sp, g0 = axis(Q, g0)
    if kind == 'none':
        pass
    elif kind == 'dropc':
        T = T[1:]
    elif kind == 'addc':
        c0 = Q[G[0], :2].mean(axis=0); c1 = Q[G[1], :2].mean(axis=0)
        B = Q[G[0]].copy(); B[:, :2] += c0 - c1; T = [B] + T
    elif kind in ('drop-lo', 'drop-hi'):
        if len(g0) < 2:
            return None
        T[0] = Q[g0[1:]] if kind == 'drop-lo' else Q[g0[:-1]]
    elif kind.startswith('add-lo') or kind.startswith('add-hi'):
        lo = kind.startswith('add-lo')
        da, db = (float(x) for x in kind.split(':')[1:3]) if ':' in kind else (0.0, 0.0)
        w = np.array([u[1], -u[0]])
        e = Q[g0[0]].copy() if lo else Q[g0[-1]].copy()
        e[:2] += (-u if lo else u) * (sp + da) + w * db
        T[0] = np.vstack([Q[g0], e[None, :]])
    elif kind.startswith('slide'):
        B = Q[g0].copy(); B[:, :2] += u * float(kind[5:]); T[0] = B
    return np.vstack(T)


def legal_tilted(T, L):
    h = (np.abs(np.cos(T[:, 2])) + np.abs(np.sin(T[:, 2]))) / 2
    if (T[:, 0] - h).min() < -1e-12 or (T[:, 1] - h).min() < -1e-12 or (T[:, 0] + h).max() > L + 1e-12 or (T[:, 1] + h).max() > L + 1e-12:
        return False
    return float(mlp.min_gap(T)) >= -1e-12


def edited_sets(Q, L, edits):
    """(edit name, end, tilted squares in the frame of Q) for single-end edits at the first and the last end."""
    out = []
    G, _ = kj.st.chains(Q)
    R = kj.rot(Q, L); GR, _ = kj.st.chains(R)
    ex = []
    for e in edits:
        if e in ('add-lo', 'add-hi', 'addj'):
            for k in (('add-lo', 'add-hi') if e == 'addj' else (e,)):
                ex += ['%s:%g:%g' % (k, da, db) for da in (0.0, 0.03, 0.06) for db in (-0.06, -0.03, 0.0, 0.03, 0.06)]
        else:
            ex.append(e)
    if 'dropc2' in ex:                         # a chain less at both ends
        ex.remove('dropc2')
        T = edit(Q, G, 'dropc'); G1, _ = kj.st.chains(T)
        out.append(('dropc2', 'both', edit(T, G1[::-1], 'dropc')))
    for e in ex:
        T = edit(Q, G, e)
        if T is not None:
            out.append((e, 'first', T))
        if e != 'none':
            T = edit(R, GR, e)
            if T is not None:
                out.append((e, 'last', kj.rot(T, L)))
    return out


def scan_one(n, P, bars, a, out):
    Q, L0 = kj.norm(P)
    targets = [n + int(t) for t in a.targets.split(',')]
    hi = max(bars.get(c, L0) for c in targets) + a.over
    Ls = np.arange(L0 + a.lo, hi + 1e-12, a.step)
    taus = [float(x) for x in a.taus.split(',')]; deltas = [float(x) for x in a.deltas.split(',')]
    best = {}
    t0 = time.time()
    for e, end, T in edited_sets(Q, L0, a.edits.split(',')):
        for tau in taus:
            for de in deltas:
                for L in Ls:
                    T2 = T.copy(); sh = (L - L0) / 2 + tau
                    T2[:, 0] += sh + de / 2; T2[:, 1] += sh - de / 2
                    if not legal_tilted(T2, L):
                        continue
                    F = refill(L, T2)
                    c = len(F)
                    if c < min(targets) or c > max(targets) + 1:
                        continue
                    k = (c, e, end)
                    if k not in best or L < best[k][0]:
                        best[k] = (L, tau, de, F)
                    if c >= max(targets):
                        break
        print('# %d %s %s done %.0fs' % (n, e, end, time.time() - t0), flush=True)
    rows = []
    for (c, e, end), (L, tau, de, F) in sorted(best.items()):
        bar = bars.get(c, 9e9); room = bar - L
        tag = '%d-%s-%s-t%+.2f-d%+.2f' % (n, e, end, tau, de)
        flag = ''
        if room > -a.over and c in targets:
            if float(mlp.min_gap(F)) >= -1e-12 and mlp.side(F) <= L + 1e-9:
                fs.write_rows('%s/%d-end-%s.csv' % (out, c, tag), c, F); flag = 'WRITTEN'
            else:
                flag = 'ILLEGAL'
        rows.append(room)
        print('%d\t%s\t%s\t%+.2f\t%+.2f\t%d\t%.6f\t%.6f\t%+.6f\t%s\t%s' % (n, e, end, tau, de, c, L, bar, room, tag, flag), flush=True)


def ctl(a):
    """Remove the end chain (or one square of it) and refill at the side of N. The edit back must give N again
    at a side not far above the side of N; the start is written for the quench, which must end on N."""
    ALL = mlp.load(a.cur, {a.n})
    Q, L0 = kj.norm(ALL[a.n])
    G, up = kj.st.chains(Q)
    os.makedirs(a.out, exist_ok=True)
    for kind, back in (('dropc', ('addc',)), ('drop-lo', ('add-lo',)), ('drop-hi', ('add-hi',))):
        T = edit(Q, G, kind)
        F = refill(L0, T)
        G2, _ = kj.st.chains(F)
        for b0 in back:
          for b in ([b0] if b0 == 'addc' else ['%s:%g:%g' % (b0, da, db) for da in (0.0, 0.03, 0.06) for db in (-0.06, -0.03, 0.0, 0.03, 0.06)]):
            T2 = edit(F, G2, b)
            hit = None
            for L in np.arange(L0, L0 + 0.08, 0.0025):
                for tau in (0.0, -0.05, 0.05):
                    T3 = T2.copy(); T3[:, :2] += (L - L0) / 2 + tau
                    if T2 is None or not legal_tilted(T3, L):
                        continue
                    F3 = refill(L, T3)
                    if len(F3) >= a.n:
                        hit = (L, tau, F3); break
                if hit:
                    break
            if hit:
                fs.write_rows('%s/%d-ctl-%s-%s.csv' % (a.out, a.n, kind, b), a.n, hit[2][:a.n] if len(hit[2]) > a.n else hit[2])
            if hit or b == b0 or b.endswith(':0.06:0.06'):
              print('ctl %d: %s gives %d at the side %.9f; %s gives %s' % (a.n, kind, len(F), L0, b,
                  'n at %.6f (+%.4f)' % (hit[0], hit[0] - L0) if hit else 'no n below +0.08'), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    q = sp.add_parser('scan'); q.add_argument('cur'); q.add_argument('bars'); q.add_argument('out'); q.add_argument('ns', type=int, nargs='+')
    q.add_argument('--lo', type=float, default=-0.02); q.add_argument('--step', type=float, default=0.0025)
    q.add_argument('--over', type=float, default=0.012)
    q.add_argument('--taus', default='-0.1,0,0.1'); q.add_argument('--deltas', default='-0.1,0,0.1')
    q.add_argument('--edits', default=','.join(EDITS)); q.add_argument('--targets', default='0,1')
    q = sp.add_parser('ctl'); q.add_argument('cur'); q.add_argument('n', type=int); q.add_argument('out')
    a = ap.parse_args()
    if a.cmd == 'ctl':
        return ctl(a)
    bars = {}
    for line in open(a.bars):
        w = line.split()
        if len(w) >= 2 and w[0].isdigit():
            bars[int(w[0])] = float(w[1])
    ALL = mlp.load(a.cur, set(a.ns))
    os.makedirs(a.out, exist_ok=True)
    for n in a.ns:
        scan_one(n, ALL[n], bars, a, a.out)


if __name__ == '__main__':
    main()
