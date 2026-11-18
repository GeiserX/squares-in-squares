#!/usr/bin/env python3
"""A block corner for any pair of arm sizes: a plain block in the corner, and each arm ends on an edge of the block.

  invent_block.py count C1 C2 F [--v V1,V2]                 the fixed term of every block size, and the count of the corner
  invent_block.py block LIBWORK C1 C2 F OUT.pkl [--blocks A:B,A:B] [--far 3] [--leans +-] [--tag a] [--seconds S] [--any]

The design is that of the held 979 (two arms that never meet). Frame of a corner module of modules.py: arm 1 (stacks of
c1) runs up the left wall in the strip 0 <= x <= W1 = c1 - 1 + f, arm 2 (c2) along the bottom wall in 0 <= y <= W2, and
the upright grid starts at (W1, W2) and is kept. A block of A by B upright squares stands in the corner, less the cells
that would meet the grid (i >= c1 - 1 and j >= c2 - 1). The near end of arm 1 stands on the top edge of the block, at
y = B, and the near end of arm 2 on its right edge, at x = A. An arm end on a flat edge is what a far zone is, so the
near ends are far zones of the library at this f (only zones with no missing rest cell and no poke, which may be
mirrored), moved to the block. With the lengths lam1 and lam2 of the two far zones the first flush stacks stand at
y0 = B + lam1 and x0 = A + lam2, and in the frame of zone_corner.loss_of the corner loses

  loss = v1 + v2 + T(A, B),   T = r1 B + r2 (A - W1) - cells of the block,   r = c cos t = c - 1 + g

where v is the loss of a far zone. One more row of the block costs g1 squares, and one more column g2. The smallest
blocks whose two near ends do not meet are (c1 - 1) by c2 and c1 by (c2 - 1): the first has T = c2 g1 - r2 f.

`block` builds each corner, settles it with zone_corner.settle_zone (soft squeeze, then the contact LP, then the exact
test) and writes a base file for `zone_corner.py adopt` and `search`, as twoshort_corner.py does for the staircase.
It prints the count next to the settled loss of every corner: the two must agree, or the placement is wrong.

Our own code and our own design. Imports zone_corner and modules of this lane. Reads the library pickles as data.
"""
import argparse, math, os, pickle, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I drops the script dir
import numpy as np
import modules as M
import zone_corner as ZC


def cells(c1, c2, A, B):
    """the cells (i, j) of a block of A by B in the corner that do not meet the upright grid at (W1, W2)"""
    return [(i, j) for i in range(A) for j in range(B) if not (i >= c1 - 1 and j >= c2 - 1)]


def fixed(c1, c2, f, A, B):
    """T(A, B): what the block adds to the loss of the corner, before the two near ends"""
    mod = ZC.cmod(c1, c2); t1, t2, p1, p2, W1, W2 = ZC.geom(mod, f)
    return c1 * math.cos(t1) * B + c2 * math.cos(t2) * (A - W1) - len(cells(c1, c2, A, B))


def sizes(c1, c2):
    """block sizes whose two near ends do not meet: not both edges inside the strip of the other arm"""
    out = [(c1 - 1, c2), (c1, c2 - 1), (c1, c2), (c1 - 1, c2 + 1), (c1 + 1, c2 - 1), (c1 + 1, c2), (c1, c2 + 1), (c1 + 1, c2 + 1)]
    return [s for s in out if s[0] >= 1 and s[1] >= 1]


def far_options(lib, c, f, top, own=True):
    """the lowest far zones of an arm of c at f that may be mirrored: [(loss, length, squares in degrees, entry)], one for
    each count class and length modulo the pitch"""
    i = int(np.argmin(np.abs(M.FF - f))); t = M.flush_tilt(c, f); rows = []
    for e in lib.far.get(c, []):
        L = e['L'][i]
        if not np.isfinite(L) or not e['sym'] or not M.usable(e['q']): continue
        if e['q'].get('slide') is not None: continue
        if own and e['q']['licence'] != 'our own': continue
        rows.append((c * math.cos(t) * float(L) - e['count'], e['count'], round(float(L), 3), e['id'], e))
    rows.sort(key=lambda r: r[:4]); seen = set(); out = []; p = 1 / math.cos(t)
    for loss, cnt, L, _, e in rows:
        key = (cnt % c, round((L % p) / p * 50))         # a zone with more flush stacks is the same zone: one for each class and length modulo the pitch
        if key in seen: continue
        seen.add(key)
        at = M.far_at(e['q'], f)
        if at is None: continue
        out.append((c * math.cos(t) * at[0] - e['count'], float(at[0]), np.array(at[1], float), e))
        if len(out) >= top: break
    return out


def near1(Pf, lean_far, lean1, B, W1):
    """a far zone (frame: wall y = 0, strip 0 <= x <= W) as the near end of arm 1 on the edge y = B"""
    a = Pf.copy()
    if lean_far != lean1: a[:, 0] = W1 - a[:, 0]; a[:, 2] = -a[:, 2]
    return np.c_[a[:, 0], B + a[:, 1], a[:, 2]]


def near2(Pf, lean_far, lean2, A, W2):
    """a far zone as the near end of arm 2 on the edge x = A (a transpose, so the tilt changes sign)"""
    a = Pf.copy()
    if lean_far != -lean2: a[:, 0] = W2 - a[:, 0]; a[:, 2] = -a[:, 2]
    return np.c_[A + a[:, 1], a[:, 0], -a[:, 2]]


def corner(c1, c2, f, A, B, F1, F2, lean1=1, lean2=-1):
    """the block corner -> (squares x, y, degrees; y0; x0) before any settle"""
    mod = ZC.cmod(c1, c2, lean1, lean2); t1, t2, p1, p2, W1, W2 = ZC.geom(mod, f)
    blk = np.array([(i + 0.5, j + 0.5, 0.0) for i, j in cells(c1, c2, A, B)], float).reshape(-1, 3)
    P = np.vstack([blk, near1(F1[2], F1[3]['lean'], lean1, B, W1), near2(F2[2], F2[3]['lean'], lean2, A, W2)])
    return P, B + F1[1], A + F2[1]


def cmd_count(a):
    c1, c2, f = a.c1, a.c2, a.f
    mod = ZC.cmod(c1, c2); t1, t2, p1, p2, W1, W2 = ZC.geom(mod, f)
    g1, g2 = f - math.sin(t1), f - math.sin(t2)
    v = [float(x) for x in a.v.split(',')] if a.v else None
    print('arms %d and %d at f %.4f: tilts %.3f and %.3f degrees, g %.4f and %.4f, r %.4f and %.4f' % (
        c1, c2, f, math.degrees(t1), math.degrees(t2), g1, g2, c1 * math.cos(t1), c2 * math.cos(t2)))
    print('block\tcells\tlost\tT' + ('\tcorner' if v else ''))
    for A, B in sizes(c1, c2) + ([(int(s.split(':')[0]), int(s.split(':')[1])) for s in a.blocks.split(',')] if a.blocks else []):
        n = len(cells(c1, c2, A, B)); T = fixed(c1, c2, f, A, B)
        print('%dx%d\t%d\t%d\t%.4f' % (A, B, n, A * B - n, T) + ('\t%.4f' % (v[0] + v[1] + T) if v else ''))


def cmd_block(a):
    c1, c2, f = a.c1, a.c2, a.f; t0 = time.time()
    lean1, lean2 = (1 if a.leans[0] == '+' else -1), (1 if a.leans[1] == '+' else -1)
    mod = ZC.cmod(c1, c2, lean1, lean2); t1, t2, p1, p2, W1, W2 = ZC.geom(mod, f)
    lib = M.Library(a.lib, only=lambda q: q['kind'] == 'far' and q['c'] in (c1, c2))
    O1 = far_options(lib, c1, f, a.far, own=not a.any); O2 = far_options(lib, c2, f, a.far, own=not a.any)
    for c, O in ((c1, O1), (c2, O2)):
        for o in O: print('far zone of %d: %s count %d length %.4f loss %.4f lean %d (%s)' % (c, o[3]['id'], o[3]['count'], o[1], o[0], o[3]['lean'], o[3]['q']['licence']), flush=True)
    if not O1 or not O2: print('no far zone for one arm'); return 1
    bl = [(int(s.split(':')[0]), int(s.split(':')[1])) for s in a.blocks.split(',')] if a.blocks else sizes(c1, c2)
    base = []; k = 0
    for A, B in bl:
        T = fixed(c1, c2, f, A, B)
        for F1 in O1:
            for F2 in O2:
                if a.seconds and time.time() - t0 > a.seconds: break
                P, y0, x0 = corner(c1, c2, f, A, B, F1, F2, lean1, lean2); N = len(P)
                cnt = F1[0] + F2[0] + T
                g = ZC.exact(P, mod, f, y0 + 0.02, x0 + 0.02)
                try: r = ZC.settle_zone(P, mod, f, y0 + 0.02, x0 + 0.02)
                except Exception as ex: r = None; print('settle failed: %s' % ex, flush=True)
                tag = 'block %dx%d near %s + %s: %d squares class %d, count %.4f, placed gaps %.1e %.1e %.1e beyond %d' % (
                    A, B, F1[3]['id'], F2[3]['id'], N, N % c1, cnt, g[0], g[1], g[2], g[3])
                if r is None: print(tag + ' | not settled', flush=True); continue
                ys, xs, Q = r; ls = ZC.loss_of(mod, f, N, ys, xs)
                print(tag + ' | settled y0 %.6f (placed %.6f) x0 %.6f (placed %.6f) loss %.4f, settled less count %+.4f (%.0f s)' % (
                    ys, y0, xs, x0, ls, ls - cnt, time.time() - t0), flush=True)
                lic = sorted({F1[3]['q']['licence'], F2[3]['q']['licence'], 'our own'})
                base.append(dict(id='bk%dx%d-%df%04d%s%d' % (c1, c2, N, round(f * 1e4), a.tag, k),
                                 src='invent_block.py: block corner of %d by %d with the far zones %s and %s as near ends (our own design)' % (A, B, F1[3]['id'], F2[3]['id']),
                                 licence='our own' if lic == ['our own'] else '; '.join(lic), c1=c1, c2=c2, lean1=lean1, lean2=lean2, f=f, count=N,
                                 y0=ys, x0=xs, P=Q, A=A, B=B, loss=ls, count_loss=cnt))
                k += 1
    if base:
        pickle.dump([{k_: v for k_, v in b.items() if k_ not in ('loss', 'count_loss', 'A', 'B')} for b in base], open(a.out + '.tmp', 'wb'))
        os.replace(a.out + '.tmp', a.out)
        srt = sorted(base, key=lambda b: b['loss'])
        print('kept %d corners, lowest loss %.4f (%s, block %dx%d, %d squares, class %d); largest settled less count %+.4f' % (
            len(base), srt[0]['loss'], srt[0]['id'], srt[0]['A'], srt[0]['B'], srt[0]['count'], srt[0]['count'] % c1,
            max(abs(b['loss'] - b['count_loss']) for b in base)))
        seen = set()
        for b in srt:
            if b['count'] % c1 in seen: continue
            seen.add(b['count'] % c1); print('  class %d: %.4f (%s, block %dx%d, %d squares)' % (b['count'] % c1, b['loss'], b['id'], b['A'], b['B'], b['count']))
    else: print('kept 0 corners')
    return 0


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('count'); p.add_argument('c1', type=int); p.add_argument('c2', type=int); p.add_argument('f', type=float)
    p.add_argument('--v'); p.add_argument('--blocks'); p.set_defaults(fn=cmd_count)
    p = sub.add_parser('block'); p.add_argument('lib'); p.add_argument('c1', type=int); p.add_argument('c2', type=int); p.add_argument('f', type=float); p.add_argument('out')
    p.add_argument('--blocks'); p.add_argument('--far', type=int, default=3); p.add_argument('--leans', default='+-'); p.add_argument('--tag', default='a')
    p.add_argument('--seconds', type=float, default=0.0); p.add_argument('--any', action='store_true'); p.set_defaults(fn=cmd_block)
    a = ap.parse_args(); sys.exit(a.fn(a) or 0)


if __name__ == '__main__':
    main()
