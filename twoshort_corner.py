#!/usr/bin/env python3
"""A corner for any pair of arm sizes, made from nothing: the staircase design of the library's best low-f corner.

  twoshort_corner.py stair C1 C2 F OUT.pkl [--top 6] [--step 0.05] [--h H,H] [--tag a] [--per 1] [--walls] [--keep 0] [--seconds S]

The library's best corner of two 8-arms below f = 0.8 (zc8x8-98f7134, loss 2.47) is a staircase of uprights in the
corner (columns of 7, 6, .. 1), the rows of arm 1 on the lattice of its flush stacks, each row one square shorter at
the wall end than the row above it, and the columns of arm 2 the same way, cut where they meet arm 1. This tool
builds that design for any (c1, c2, f): for a staircase of H columns and the two stack positions (y0, x0) it places
the staircase, then the rows of arm 1 from the first flush stack down (the longest run of each lattice row that is
clear, over a few shifts along the row), then the columns of arm 2 the same way. It scans H, y0 and x0, keeps for
every count the layout with the lowest loss, and settles the best with zone_corner.settle_zone (soft squeeze, then
the contact LP). OUT.pkl is a base file for `zone_corner.py search` (hops, insert, delete) and `adopt`.

--per K keeps the K lowest scan layouts of every count that differ in (H, squares of arm 1), not one: the settle moves a
loss by up to 1.2 squares, so the lowest scan layout of a count is often not its lowest corner. --top 0 settles all of
them. --walls puts the first flush stack of each arm into the scan, so that no row or column is placed across it.
--keep K writes only the K lowest settled corners and the 4 lowest of every class. --seconds S stops the settles
after S seconds of run time and writes what it has.

Our own code and our own design. Imports zone_corner, zone_search and modules of this lane.
"""
import argparse, math, os, pickle, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import zone_corner as ZC

SHIFTS = (0.0, -0.2, -0.4, -0.6, -0.8, 0.2, 0.4, 0.6, 0.8)      # along a row, in squares; the lattice place first


def gaps(C, P):
    """separating-axis gap of every unit square of C (k, 3: x, y, radians) to every one of P -> (k, len(P))"""
    d = P[None, :, :2] - C[:, None, :2]
    a, b = C[:, None, 2], P[None, :, 2]
    ext = 0.5 + 0.5 * (np.abs(np.cos(b - a)) + np.abs(np.sin(b - a)))
    g = np.full(ext.shape, -np.inf)
    for ang in (a + 0 * b, a + math.pi / 2 + 0 * b, b + 0 * a, b + math.pi / 2 + 0 * a):
        g = np.maximum(g, np.abs(d[..., 0] * np.cos(ang) + d[..., 1] * np.sin(ang)) - ext)
    return g


def best_run(cands, placed, lo_wall=1e-9, tol=-1e-9):
    """cands: list of (k, 3) candidate rows (one per shift). The longest clear contiguous run over the shifts (the
    first shift wins a tie). -> (k', 3) array, possibly empty"""
    best = np.zeros((0, 3))
    for C in cands:
        h = 0.5 * (np.abs(np.cos(C[:, 2])) + np.abs(np.sin(C[:, 2])))
        ok = (C[:, 0] - h >= -lo_wall) & (C[:, 1] - h >= -lo_wall)
        if len(placed): ok &= gaps(C, placed).min(1) >= tol
        run = (0, 0); i = 0
        while i < len(C):
            if not ok[i]: i += 1; continue
            j = i
            while j < len(C) and ok[j]: j += 1
            if j - i > run[1] - run[0]: run = (i, j)
            i = j
        if run[1] - run[0] > len(best): best = C[run[0]:run[1]]
    return best


def stair(c1, c2, f, H, y0, x0, shifts=SHIFTS, order=(1, 2), minrun=1, walls=False):
    """the staircase corner at (H, y0, x0) -> (k, 3) array x, y, degrees"""
    mod = ZC.cmod(c1, c2)
    t1, t2, p1, p2, W1, W2 = ZC.geom(mod, f)
    P = [(i + 0.5, r + 0.5, 0.0) for i in range(H) for r in range(H - i)]
    P = np.array(P, float).reshape(-1, 3)
    s1 = np.arange(c1) - (c1 - 1) / 2; s2 = np.arange(c2) - (c2 - 1) / 2
    def row(j, sh_list):                             # arm 1: a row rising to the right, j pitches under the first flush stack
        cy = y0 + p1 / 2 - j * p1
        cands = [np.c_[W1 / 2 + (s1 + sh) * math.cos(t1), cy + (s1 + sh) * math.sin(t1), np.full(c1, t1)] for sh in sh_list]
        return [C[C[:, 0] + 0.5 * (math.cos(t1) + math.sin(t1)) <= W1 + 1e-9] for C in cands]
    def col(j, sh_list):                             # arm 2: a column leaning right, j pitches before the first flush stack
        cx = x0 + p2 / 2 - j * p2
        cands = [np.c_[cx + (s2 + sh) * math.sin(t2), W2 / 2 + (s2 + sh) * math.cos(t2), np.full(c2, -t2)] for sh in sh_list]
        return [C[C[:, 1] + 0.5 * (math.cos(t2) + math.sin(t2)) <= W2 + 1e-9] for C in cands]
    Wl = np.zeros((0, 3))
    if walls:                                        # the first flush stack of each arm, as placed squares that are not counted
        Wl = np.vstack([np.c_[W1 / 2 + s1 * math.cos(t1), y0 + p1 / 2 + s1 * math.sin(t1), np.full(c1, t1)],
                        np.c_[x0 + p2 / 2 + s2 * math.sin(t2), W2 / 2 + s2 * math.cos(t2), np.full(c2, -t2)]])
    e1 = e2 = 0; j = 1
    while (e1 < 2 or e2 < 2) and j < 40:             # a row of arm 1 and a column of arm 2 in turn, so that they meet on the diagonal
        for which in order:
            if which == 1 and e1 < 2:
                R = best_run(row(j, shifts), np.vstack([P, Wl]))
                if len(R) < minrun: e1 += 1
                else: P = np.vstack([P, R]); e1 = 0
            if which == 2 and e2 < 2:
                R = best_run(col(j, shifts), np.vstack([P, Wl]))
                if len(R) < minrun: e2 += 1
                else: P = np.vstack([P, R]); e2 = 0
        j += 1
    P[:, 2] = np.degrees(P[:, 2])
    return P


def cmd_stair(a):
    c1, c2, f = a.c1, a.c2, a.f
    mod = ZC.cmod(c1, c2); t0 = time.time()
    t1, t2, p1, p2, W1, W2 = ZC.geom(mod, f)
    hs = [int(v) for v in a.h.split(',')] if a.h else [min(c1, c2) - 2, min(c1, c2) - 1, min(c1, c2), max(c1, c2) - 1]
    best = {}                                        # (count,) or (count, H, squares of arm 1) -> (loss, H, y0, x0)
    for H in sorted(set(hs)):
        for y0 in np.arange(H + 1.5, H + 1.5 + 3 * p1 + 1e-9, a.step):
            for x0 in np.arange(max(H + 1.5, W1 + 0.2), H + 1.5 + 3 * p2 + 1e-9, a.step):
                P = stair(c1, c2, f, H, float(y0), float(x0), walls=a.walls)
                N = len(P); loss = ZC.loss_of(mod, f, N, y0, x0)
                key = (N, H, int((P[:, 2] > 1e-9).sum())) if a.per > 1 else (N,)
                if key not in best or loss < best[key][0]: best[key] = (loss, H, float(y0), float(x0))
    bycount = {}
    for key, v in best.items(): bycount.setdefault(key[0], []).append(v)
    cands = []                                       # (scan loss, count, rank in its count, H, y0, x0)
    for N, vs in bycount.items():
        vs.sort()
        cands += [(v[0], N, i, v[1], v[2], v[3]) for i, v in enumerate(vs[:a.per])]
    cands.sort()
    print('scan %.0f s: %d counts, %d layouts' % (time.time() - t0, len(bycount), len(cands)), flush=True)
    # the best count of every class of arm 1, then the next best layouts
    seen = set(); pick = []
    for cnd in cands:
        if cnd[1] % c1 not in seen: seen.add(cnd[1] % c1); pick.append(cnd)
    pick = pick + [cnd for cnd in cands if cnd not in pick]
    if a.top > 0: pick = pick[:a.top]
    base = []

    def write():
        out = base
        if a.keep > 0:
            srt = sorted(base, key=lambda b: b['loss']); out = srt[:a.keep]; cnt = {}
            for b in srt:
                cl = b['count'] % c1; cnt[cl] = cnt.get(cl, 0) + 1
                if cnt[cl] <= 4 and not any(b is v for v in out): out.append(b)
        if out:
            pickle.dump([{k: v for k, v in b.items() if k != 'loss'} for b in out], open(a.out + '.tmp', 'wb')); os.replace(a.out + '.tmp', a.out)
        return out

    for it, (loss, N, rank, H, y0, x0) in enumerate(pick):
        if a.seconds and time.time() - t0 > a.seconds: print('stopped at %d of %d layouts' % (it, len(pick)), flush=True); break
        P = stair(c1, c2, f, H, y0, x0, walls=a.walls)
        g = ZC.exact(P, mod, f, y0 + 0.02, x0 + 0.02)
        try: r = ZC.settle_zone(P, mod, f, y0 + 0.02, x0 + 0.02)
        except Exception as ex: r = None; print('count %d: settle failed: %s' % (N, ex), flush=True)
        if r is None:
            print('count %d class %d H %d: scan loss %.3f at (%.3f, %.3f), gaps %.1e %.1e %.1e: not settled' % (N, N % c1, H, loss, y0, x0, g[0], g[1], g[2]), flush=True)
            continue
        ys, xs, Q = r
        ls = ZC.loss_of(mod, f, N, ys, xs)
        print('count %d class %d H %d: scan loss %.3f at (%.3f, %.3f) | settled y0 %.6f x0 %.6f loss %.4f (%.0f s)' % (
            N, N % c1, H, loss, y0, x0, ys, xs, ls, time.time() - t0), flush=True)
        base.append(dict(id='st%dx%d-%df%04d%s%s' % (c1, c2, N, round(f * 1e4), a.tag, str(rank) if rank else ''), src='twoshort_corner.py: staircase corner (our own design)',
                         licence='our own', c1=c1, c2=c2, lean1=1, lean2=-1, f=f, count=N, y0=ys, x0=xs, P=Q, H=H, loss=ls))
        if len(base) % 25 == 0: write()
    out = write()
    print('kept %d corners of %d settled, lowest loss %s' % (len(out), len(base), '%.4f' % min(b['loss'] for b in base) if base else '-'))


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('stair'); p.add_argument('c1', type=int); p.add_argument('c2', type=int); p.add_argument('f', type=float); p.add_argument('out')
    p.add_argument('--top', type=int, default=6); p.add_argument('--step', type=float, default=0.05); p.add_argument('--h'); p.add_argument('--tag', default='a')
    p.add_argument('--per', type=int, default=1); p.add_argument('--walls', action='store_true'); p.add_argument('--keep', type=int, default=0); p.add_argument('--seconds', type=float, default=0.0)
    p.set_defaults(fn=cmd_stair)
    a = ap.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
