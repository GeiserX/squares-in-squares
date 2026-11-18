#!/usr/bin/env python3
"""rebuild_seams.py POOL.csv BARS.tsv OUTDIR TARGETS NX,NY [NX,NY ...] [--dmax 0.3] [--room -0.03]

Brute force over every seam (j1, j2, shift s, every symmetry of each layout that reads the most chains, turned or not) of k123_join.join for the target counts
only, with the d ladder of the k123 lane, and no chain-size match test. k123_join.py scan skips a seam when a
chain is mis-read (a lone tilted square read as a chain of size 1 shifts every later index), which the clean
735 and 790 of round 24 have at chain 15. Prints one line per legal start (min gap >= -1e-9) with its room
(bar side minus start side) and writes the starts above --room as OUTDIR/<n>-rb-<tag>.csv. Our own code; it
imports k123_join, methods_lp and family_step and does not change them."""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import methods_lp as m  # noqa: E402
import k123_join as kj  # noqa: E402
import family_step as fs  # noqa: E402
import rebuild_pool as rp  # noqa: E402

D = (0, .01, .02, .04, .07, .1, .13, .16, .2, .25, .3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pool'); ap.add_argument('bars'); ap.add_argument('out'); ap.add_argument('targets')
    ap.add_argument('pairs', nargs='+'); ap.add_argument('--room', type=float, default=-0.03)
    ap.add_argument('--top', type=int, default=3)
    ap.add_argument('--syms', type=int, default=1, help='symmetries kept per layout (each also turned)')
    ap.add_argument('--smax', type=int, default=10, help='shifts -smax..smax')
    a = ap.parse_args()
    T = {int(t) for t in a.targets.split(',')}
    bars = {int(w[0]): float(w[1]) for w in (l.split('\t') for l in open(a.bars).read().splitlines()) if len(w) > 1}
    ns = sorted({int(v) for p in a.pairs for v in p.split(',')})
    A = m.load(a.pool, set(ns))
    lay = {}
    for n in ns:
        # every symmetry whose own chain reading holds most chains, without kj.norm (rebuild_pool.py says why)
        cand = []
        for k in range(8):
            Q = rp.sym(A[n], k); L = m.side(Q)
            try:
                c = len(kj.Lay(n, Q, L, 'x').size)
            except Exception:
                continue
            cand.append((c, k, Q, L))
        top = max(c[0] for c in cand)
        lay[n] = []
        for c, k, Q, L in cand:
            if c == top and len(lay[n]) < 2 * a.syms:
                lay[n] += [kj.Lay(n, Q, L, '%d-s%d' % (n, k)), kj.Lay(n, kj.rot(Q, L), L, '%dr-s%d' % (n, k))]
    os.makedirs(a.out, exist_ok=True)
    found = {}
    for p in a.pairs:
        nx, ny = map(int, p.split(','))
        for x in lay[nx]:
            for y in lay[ny]:
                base = max(0.0, y.f - x.f)
                for j1 in range(len(x.size)):
                    for j2 in range(len(y.size)):
                        for s in range(-a.smax, a.smax + 1):
                            for d in D:
                                try:
                                    F, Lf = kj.join(x, y, j1, j2, s, base + d)
                                except Exception:
                                    break
                                if len(F) not in T:
                                    break
                                if m.min_gap(F) >= -1e-9:
                                    n = len(F); tag = '%s-%s-j%d-%d-s%d' % (x.tag, y.tag, j1, j2, s)
                                    found.setdefault(n, []).append((Lf, tag, d, F))
                                    break
    for n in sorted(found):
        rows = sorted(found[n], key=lambda r: r[0])
        for Lf, tag, d, F in rows[:a.top]:
            room = bars[n] - Lf
            w = room > a.room
            print('n %d start %.9f d %.2f bar %.9f room %+.6f %s%s' % (n, Lf, d, bars[n], room, tag, ' WRITTEN' if w else ''), flush=True)
            if w:
                fs.write_rows(os.path.join(a.out, '%d-rb-%s.csv' % (n, tag)), n, F)


if __name__ == '__main__':
    main()
