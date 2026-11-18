#!/usr/bin/env python3
"""Two held bands of chains joined at a seam: the first end of one layout with the second end of another
(avenues/k123.md, section "Round 19").

k123_step57.py up joins two copies of one layout, so it keeps both ends of that layout. This tool joins the
part of layout X before a seam with the part of layout Y after a seam. The result has the first end zone of
X and the second end zone of Y, at a new m. Each layout is also used turned by 180 degrees, which swaps its
two ends. So the ends of every held band become ends for every other band.

The second part is moved by (sh, sh), sh = s + (fX - fY) + d with s whole: the two upright lattices of Y then
continue the lattices of X, and the new side is mY + s + fX + d. The chain j2 of Y lands where the chain j1
of X stood. d >= 0 keeps the two parts apart, and the fq quench takes it back.

  k123_join.py list CUR.csv N [N ...]                          the chains of each layout
  k123_join.py scan CUR.csv BARS.tsv OUTDIR NX,NY [NX,NY ...] [--room -0.003] [--top 2] [--mmin 15]
       every seam of every pair (both layouts also turned by 180 degrees). It prints one line for each
       (count, m) reached with a legal start, with the room: the side to beat minus the side of the start.
       It writes the starts with room above --room as OUTDIR/<n>-join-<tag>.csv (Kaggle rows).
       --rmax and --pmax widen the seam (a start with an overlap r at the seam gets a larger d), and
       --only N,N keeps those counts and prints every seam chain j1 of them.
  k123_join.py write CUR.csv OUTDIR TAG:D [TAG:D ...]          the start of one line of scan (TAG as printed, D its d)
  BARS.tsv: n <tab> side to beat.

The chains can have any size: a seam needs the same chain sizes on both sides in the two layouts.
Finish a start with k123_turn.py (--turns=0, fq) and certify with methods_take.py. A result is a seed for the next scan.
Controls (each can fail, all green on 2026-11-12): the held 680 with itself gives the step down of k123_step57.py
(444 at s = -5) and its step up (966 at s = 5), and both quenches end on the round 17 sides to 1e-9. The held 788,
turned, with the held 965 ends on the held 403, and the held 680 with itself at s = 2 on the held 789, to 1e-9.
Our own code. It imports methods_lp, family_step (write_rows) and k123_step57 and does not change them.
"""
import argparse, math, os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import family_step as fs  # noqa: E402
import methods_lp as mlp  # noqa: E402
import k123_step57 as st  # noqa: E402


def norm(P):
    """The layout in its box, with the band on the main diagonal and the chains at 35 degrees. -> (Q, L)"""
    Q, L = st.boxed(P)
    G, up = st.chains(Q)
    if abs(float(np.mean([Q[g, 0].mean() - Q[g, 1].mean() for g in G]))) > 2.0:      # the other diagonal: mirror
        Q[:, 0] = L - Q[:, 0]; Q[:, 2] = -Q[:, 2]
    th = np.degrees(Q[:, 2]) % 90.0
    t = (th > 1.0) & (th < 89.0)
    if float(np.median(th[t])) > 45.0:                                                 # transpose: 55 -> 35 degrees
        Q = np.c_[Q[:, 1], Q[:, 0], math.pi / 2 - Q[:, 2]]
    if len(st.chains(Q)[0]) < 10:
        # Near 45 degrees the median test can transpose a readable band away.
        raw, L = st.boxed(P)
        best = (len(st.chains(Q)[0]), False)
        for bits in range(8):
            candidate = raw.copy()
            if bits & 1:
                candidate[:, 0] = L - candidate[:, 0]
                candidate[:, 2] = -candidate[:, 2]
            if bits & 2:
                candidate[:, 1] = L - candidate[:, 1]
                candidate[:, 2] = -candidate[:, 2]
            if bits & 4:
                candidate = candidate[:, [1, 0, 2]]
                candidate[:, 2] = math.pi / 2 - candidate[:, 2]
            groups, _ = st.chains(candidate)
            angles = np.degrees(candidate[:, 2]) % 90.0
            tilted = (angles > 1.0) & (angles < 89.0)
            rank = (len(groups), float(np.median(angles[tilted])) <= 45.0)
            if rank > best:
                best, Q = rank, candidate
    return Q, L


def rot(Q, L):
    R = Q.copy(); R[:, 0] = L - R[:, 0]; R[:, 1] = L - R[:, 1]
    return R


class Lay:
    def __init__(self, n, Q, L, tag):
        self.n, self.Q, self.L, self.tag = n, Q, L, tag
        self.m = int(L); self.f = L - self.m
        self.G, self.up = st.chains(Q)
        self.c = np.array([Q[g, :2].mean(axis=0) for g in self.G])
        self.size = np.array([len(g) for g in self.G])


def join(X, Y, j1, j2, s, d):
    """Chains 0..j1-1 of X, chains j2.. of Y moved by sh. -> (array, new side)"""
    sh = s + (X.f - Y.f) + d
    Ln = Y.L + sh
    S = (X.c[j1 - 1].sum() + Y.c[j2].sum() + 2 * sh) / 2
    parts = [X.Q[g] for g in X.G[:j1]]
    for g in Y.G[j2:]:
        B = Y.Q[g].copy(); B[:, :2] += sh; parts.append(B)
    U = X.Q[X.up]
    parts.append(U[(U[:, 0] + U[:, 1] < S) & (U[:, 0] < Ln - 0.49) & (U[:, 1] < Ln - 0.49)])
    V = Y.Q[Y.up].copy(); V[:, :2] += sh
    parts.append(V[(V[:, 0] + V[:, 1] >= S) & (V[:, 0] > 0.49) & (V[:, 1] > 0.49)])
    new = []
    r = int(Ln) + 2
    for i in range(r):
        for j in range(r):
            x, y = Ln - i - 0.5, j + 0.5                       # the bottom right lattice
            if x < 0.49 or y > Ln - 0.49:
                continue
            if (x > X.L + 0.25 and x + y < S) or (y < sh - 0.25 and x + y >= S):
                new.append((x, y, 0.0)); new.append((y, x, 0.0))   # and its mirror on the top left lattice
    if new:
        parts.append(np.array(new))
    return np.vstack(parts), Ln


def seams(X, Y, mmin, rmax=0.12, pmax=0.12):
    """Every (j1, j2, s) where the chain j2 of Y, moved by s + fX - fY, lands on the chain j1 of X."""
    out = []
    d0 = X.f - Y.f
    for j1 in range(5, len(X.G) - 4):
        for j2 in range(4, len(Y.G) - 5):
            if X.size[j1] != Y.size[j2] or X.size[j1 - 1] != Y.size[j2 - 1]:      # the same chains on both sides of the seam
                continue
            D = X.c[j1] - Y.c[j2]
            par = (D[0] + D[1]) / 2 - d0; perp = (D[0] - D[1]) / 2
            s = round(par); r = par - s
            if abs(perp) > pmax or abs(r) > rmax or Y.m + s < mmin:
                continue
            out.append((j1, j2, s, r, perp))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    q = sp.add_parser('list'); q.add_argument('cur'); q.add_argument('ns', type=int, nargs='+')
    q = sp.add_parser('scan'); q.add_argument('cur'); q.add_argument('bars'); q.add_argument('out'); q.add_argument('pairs', nargs='+')
    q.add_argument('--room', type=float, default=-0.003); q.add_argument('--top', type=int, default=2)
    q.add_argument('--mmin', type=int, default=15); q.add_argument('--gap', type=float, default=-1e-6)
    q.add_argument('--rmax', type=float, default=0.12); q.add_argument('--pmax', type=float, default=0.12)
    q.add_argument('--only', default='', help='print and write only these counts (comma list)')
    q = sp.add_parser('write'); q.add_argument('cur'); q.add_argument('out'); q.add_argument('tags', nargs='+')
    a = ap.parse_args()
    if a.cmd == 'write':
        import re
        os.makedirs(a.out, exist_ok=True)
        jobs = [re.match(r'(\d+)(r?)-(\d+)(r?)-j(\d+)-(\d+)-s(-?\d+):([\d.]+)$', t).groups() for t in a.tags]
        ALL = mlp.load(a.cur, {int(j[0]) for j in jobs} | {int(j[2]) for j in jobs})
        lay = {}
        for n, P in ALL.items():
            Q, L = norm(P)
            lay[(n, '')] = Lay(n, Q, L, '%d' % n); lay[(n, 'r')] = Lay(n, rot(Q, L), L, '%dr' % n)
        for t, (nx, rx, ny, ry, j1, j2, s, d) in zip(a.tags, jobs):
            F, Ln = join(lay[(int(nx), rx)], lay[(int(ny), ry)], int(j1), int(j2), int(s), float(d))
            path = '%s/%d-join-%s.csv' % (a.out, len(F), t.split(':')[0])
            fs.write_rows(path, len(F), F)
            print('%s side %.6f gap %+.6f' % (path, Ln, float(mlp.min_gap(F))), flush=True)
        return
    if a.cmd == 'list':
        ALL = mlp.load(a.cur, set(a.ns))
        for n in a.ns:
            Q, L = norm(ALL[n]); X = Lay(n, Q, L, str(n))
            th = np.degrees(Q[:, 2]) % 90.0
            mid = [float(np.mean(th[g])) for g in X.G[5:-5]]
            perp = X.c[:, 0] - X.c[:, 1]
            if len(X.G) < 12:
                print('%d: %d groups of tilted squares, no band' % (n, len(X.G)), flush=True); continue
            print('%d m %d k %d f %.6f chains %d sizes %s turn of the middle %.3f, x - y of the chains %.3f to %.3f' % (
                n, X.m, n - X.m ** 2, X.f, len(X.G), ''.join(str(min(v, 9)) for v in X.size), 45 - float(np.median(mid)),
                float(perp[5:-5].min()), float(perp[5:-5].max())), flush=True)
            for e, R in (('first', X), ('last', Lay(n, rot(Q, L), L, 'r'))):
                print('   %s end: turns of chains 0-5 %s' % (e, ' '.join('%.1f' % float(np.mean(np.degrees(R.Q[g, 2]) % 90.0)) for g in R.G[:6])), flush=True)
        return
    bars = {}
    for line in open(a.bars):
        w = line.split()
        if len(w) >= 2 and w[0].isdigit():
            bars[int(w[0])] = float(w[1])
    want = set()
    for p in a.pairs:
        want.update(int(x) for x in p.split(','))
    ALL = mlp.load(a.cur, want)
    lay = {}
    for n in want:
        Q, L = norm(ALL[n])
        lay[(n, 0)] = Lay(n, Q, L, '%d' % n); lay[(n, 1)] = Lay(n, rot(Q, L), L, '%dr' % n)
    os.makedirs(a.out, exist_ok=True)
    only = {int(x) for x in a.only.split(',') if x}
    for p in a.pairs:
        nx, ny = (int(x) for x in p.split(','))
        for rx in (0, 1):
            for ry in (0, 1):
                X, Y = lay[(nx, rx)], lay[(ny, ry)]
                best = {}
                for j1, j2, s, r, perp in seams(X, Y, a.mmin, a.rmax, a.pmax):
                    for d in (0.0, 0.01, 0.02, 0.04, 0.07, 0.1, 0.13, 0.16, 0.2, 0.25, 0.3):
                        d += max(0.0, Y.f - X.f)
                        F, Ln = join(X, Y, j1, j2, s, d)
                        n2 = len(F)
                        if n2 > 1000 or mlp.side(F) > Ln + 1e-6:
                            continue
                        gap = float(mlp.min_gap(F))
                        if gap < a.gap:
                            continue
                        if only and n2 not in only:
                            break
                        key = (n2, int(Ln), j1 if only else 0)
                        if key not in best or Ln < best[key][0]:
                            best[key] = (Ln, j1, j2, s, d, r, perp, gap, F)
                        break
                for (n2, m2, _), (Ln, j1, j2, s, d, r, perp, gap, F) in sorted(best.items()):
                    bar = bars.get(n2, 9e9); room = bar - Ln
                    tag = '%s-%s-j%d-%d-s%d' % (X.tag, Y.tag, j1, j2, s)
                    flag = ''
                    if room > a.room:
                        fs.write_rows('%s/%d-join-%s.csv' % (a.out, n2, tag), n2, F); flag = 'WRITTEN'
                    print('%s + %s: n %d m %d k %d  start %.6f (d %.3f, gap %+.5f, r %+.3f, perp %+.3f)  bar %.6f  room %+.6f  %s %s' % (
                        X.tag, Y.tag, n2, m2, n2 - m2 * m2, Ln, d, gap, r, perp, bar, room, tag, flag), flush=True)


if __name__ == '__main__':
    main()
