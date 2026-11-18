#!/usr/bin/env python3
"""The 0.6841 block ("the pod") with one arm beside it: count the layout with the exact fill.

The held 491, 685 and 739 hold one rigid block of 82 squares at 23.9886 degrees with about 30 loose
squares round it. Alone it puts 5 squares more than the grid into a slab 17 wide and 10 + f high, at
f = 0.684143606. The held 685 adds an arm in the rows the slab leaves free: rows of 8 squares at
24.74 degrees in a slot of width 7 + f along a wall. This tool builds that layout for any m and any
arm width c: the pod of the held 491 in the bottom-right corner, flush rows of c + 1 squares along the
left wall, and the uprights from the exact fill (Evan Daniel's fillfast, MIT, imported from his clone
through EVAND_PACKER). It prints the count for every phase of the row stack.

  ctl     the tilted squares of 491 must refill to 491, the pod alone must give m*m + 5 at m = 22 and
          m = 17, and the pod moved to m = 16 must leave the square.
  scan    M C: both tilts of an arm of rows of C + 1 with the pod, for every height of the lowest row
          from 8.5 to 12 (the slab of the pod ends at 10.684). --low starts the arm at the floor.
          Writes the best layout as a quench start (n, side, then x y degrees per line).

  stuff   add the squares a scan layout lacks, in its emptiest places left of --xmax, and quench with fq
          with the side free. A result is written when its side ends below HELD_SIDE.

Usage:
  forensics_pod.py ctl HELD.csv
  forensics_pod.py scan HELD.csv M C OUT_DIR [--step 0.02] [--low] [--want N]
  forensics_pod.py stuff START.txt N HELD_SIDE OUT_DIR [--fq PATH] [--seeds 3] [--xmax X] [--jit 0.05]
"""
import sys, os, math, argparse
import numpy as np

import forensics_turn as ft

sys.path.insert(0, os.environ.get('EVAND_PACKER', '$SCRATCH/bounties-squares/ext/evand/search/packer'))
import fillfast

F = 0.6841436063588683           # the side fraction the two chains of the block fix
EPS = 2e-9


def pod_of(held):
    s, A = ft.normalize(ft.load(held, 491))
    T = A[np.abs(A[:, 2]) > 0.5]
    inpod = (T[:, 0] > 5.0) & (T[:, 1] < 11.2)
    return s, T, T[inpod], T[~inpod]


def corners(Q):
    th = np.radians(Q[:, 2]); c, s = np.cos(th), np.sin(th)
    off = np.array([[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]])
    return Q[:, None, :2] + np.stack([off[:, 0] * c[:, None] - off[:, 1] * s[:, None], off[:, 0] * s[:, None] + off[:, 1] * c[:, None]], -1)


def overlap(A, B, tol=1e-9):
    """True for each square of A that overlaps some square of B by more than tol (separating axes)."""
    if not len(A) or not len(B):
        return np.zeros(len(A), bool)
    PA, PB = corners(A), corners(B)
    hit = np.zeros(len(A), bool)
    for i in range(len(A)):
        near = np.nonzero(np.hypot(B[:, 0] - A[i, 0], B[:, 1] - A[i, 1]) < 1.4143)[0]
        for j in near:
            sep = False
            for ang in (A[i, 2], A[i, 2] + 90, B[j, 2], B[j, 2] + 90):
                u = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
                a = PA[i] @ u; b = PB[j] @ u
                if a.max() <= b.min() + tol or b.max() <= a.min() + tol:
                    sep = True; break
            if not sep:
                hit[i] = True; break
    return hit


def arm_tilt(c, f=F):
    """(c + 1) cos t + sin t = c + f, the smaller root."""
    R = math.hypot(c + 1, 1); return math.atan2(1, c + 1) + math.acos((c + f) / R)


def arm_rows(c, sign, y0, side, f=F):
    """Flush rows of c + 1 squares in the slot 0 <= x <= c + f, stacked upward from the row centred at y0."""
    t = arm_tilt(c, f); C, S = math.cos(t), math.sin(t)
    rows = []
    half_h = ((c + 1) * S + C) / 2
    j = 0
    while True:
        yc = y0 + j / C
        if yc + half_h > side + 1e-9:
            break
        if yc - half_h >= -1e-9:
            rows.append([((c + f) / 2 + (i - c / 2) * C, yc + sign * (i - c / 2) * S, sign * math.degrees(t)) for i in range(c + 1)])
        j += 1
    return rows


def cmd_ctl(held):
    s, T, pod, rest = pod_of(held)
    ok = True
    n = len(fillfast.fill(s, T, mode='exact')); print('all %d tilted squares of 491 at its side: %d (want 491)' % (len(T), n)); ok &= n == 491
    n = len(fillfast.fill(s, pod, mode='exact')); print('the pod alone, %d squares, m = 22: %d (want 489)' % (len(pod), n)); ok &= n == 489
    P = pod.copy(); P[:, 0] -= 5.0
    n = len(fillfast.fill(s - 5.0, P, mode='exact')); print('the pod alone, m = 17: %d (want 294)' % n); ok &= n == 294
    P = pod.copy(); P[:, 0] -= 6.0
    bad = bool((corners(P)[:, :, 0].min() < -1e-9))
    print('the pod at m = 16 leaves the square: %s (want True, the control can fail)' % bad); ok &= bad
    print('CONTROL GREEN' if ok else 'CONTROL RED'); return 0 if ok else 1


def cmd_scan(held, m, c, out, step, low, want):
    s491, T, pod, rest = pod_of(held)
    side = m + F + EPS
    P = pod.copy(); P[:, 0] += side - s491
    t = arm_tilt(c); C = math.cos(t)
    base = len(fillfast.fill(side, P, mode='exact'))
    print('m %d c %d: tilt %.4f deg, gain per unit %.4f, pod alone %d (k = %d)' % (m, c, math.degrees(t), F - math.sin(t), base, base - m * m), flush=True)
    best = (0, None); os.makedirs(out, exist_ok=True)
    half_h = ((c + 1) * math.sin(t) + C) / 2
    b_lo, b_hi = (0.0, 1 / C) if low else (8.5, 12.0)            # the lowest corner of the first row
    for sign in (1, -1):
        ph = b_lo
        while ph < b_hi:
            rows = arm_rows(c, sign, ph + half_h, side)
            A = np.array([q for r in rows for q in r], float).reshape(-1, 3)
            keep = np.ones(len(A), bool)
            if len(A):
                hit = overlap(A, P)
                for r in range(len(rows)):                       # a row that touches the pod goes out whole
                    if hit[r * (c + 1):(r + 1) * (c + 1)].any():
                        keep[r * (c + 1):(r + 1) * (c + 1)] = False
            A = A[keep]
            Rr = fillfast.fill(side, np.r_[P, A], mode='exact', time_limit=5)
            n = len(Rr)
            if n > best[0]:
                best = (n, Rr, sign, ph, len(A) // (c + 1))
                print('   tilt %+d phase %.3f rows %d: %d (k = %d)' % (sign, ph, len(A) // (c + 1), n, n - m * m), flush=True)
                path = '%s/pod-m%d-c%d-n%d.txt' % (out, m, c, n)
                with open(path, 'w') as h:
                    h.write('%d %r\n' % (n, side))
                    for x, y, g in Rr:
                        h.write('%r %r %r\n' % (float(x), float(y), float(g)))
            ph += step
    n = best[0]
    print('m %d c %d best %d (k = %d) at tilt %+d phase %.3f rows %d%s' % (m, c, n, n - m * m, best[2], best[3], best[4], ('  want %d: %s' % (want, 'REACHED' if n >= want else '%d short' % (want - n))) if want else ''), flush=True)


def emptiest(X, side, k, xmax, step=0.05):
    """k centres for extra uprights with x below xmax, each as far as possible from the squares already there."""
    P = [tuple(r[:2]) for r in X]
    gx, gy = np.meshgrid(np.arange(0.5, min(xmax, side - 0.5) + 1e-9, step), np.arange(0.5, side - 0.5 + 1e-9, step))
    G = np.c_[gx.ravel(), gy.ravel()]
    out = []
    for _ in range(k):
        A = np.array(P); d = np.full(len(G), np.inf)
        for a in range(0, len(A), 64):
            d = np.minimum(d, np.hypot(G[:, None, 0] - A[None, a:a + 64, 0], G[:, None, 1] - A[None, a:a + 64, 1]).min(axis=1))
        b = int(np.argmax(d)); out.append((float(G[b, 0]), float(G[b, 1]), float(d[b]))); P.append((float(G[b, 0]), float(G[b, 1])))
    return out


def cmd_stuff(start, n, held_side, out, fq, seeds, xmax, jit):
    """Add the missing squares to a scan layout in its emptiest places and quench with the side free."""
    L = [l.split() for l in open(start) if l.strip()]
    side = float(L[0][1]); X = np.array([[float(v) for v in q[:3]] for q in L[1:]])
    if len(X) >= n:
        X = X[:n]; add = []
    else:
        add = emptiest(X, side, n - len(X), xmax)
    print('%s: %d squares at side %.10f, need %d, added at %s' % (os.path.basename(start), len(X), side, n, [(round(x, 2), round(y, 2), 'room %.2f' % d) for x, y, d in add]), flush=True)
    Y = np.array([tuple(r) for r in X] + [(x, y, 0.0) for x, y, _ in add], float)
    os.makedirs(out, exist_ok=True); best = None
    for seed in range(seeds):
        for polish in (False, True):
            Z = Y.copy()
            if seed:
                rng = np.random.default_rng(seed); Z[len(X):, :2] += rng.normal(0, jit, (len(Z) - len(X), 2)); Z[len(X):, 2] = rng.uniform(-45, 45, len(Z) - len(X))
            s2, Q = ft.quench(fq, side, Z, ft.POLISH if polish else [], timeout=900)
            if s2 is None:
                print('   seed %d polish %d: quench failed' % (seed, polish), flush=True); continue
            print('   seed %d polish %d: side %.10f  (%+.3e to held)' % (seed, polish, s2, s2 - held_side), flush=True)
            if s2 < held_side - 1e-9 and (best is None or s2 < best):
                best = s2; path = '%s/%d-pod-s%d%s.csv' % (out, n, seed, 'p' if polish else '')
                ft.write_rows(path, n, Q); print('   wrote', path, flush=True)


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == 'ctl':
        sys.exit(cmd_ctl(sys.argv[2]))
    if len(sys.argv) > 2 and sys.argv[1] == 'stuff':
        ap = argparse.ArgumentParser()
        ap.add_argument('cmd'); ap.add_argument('start'); ap.add_argument('n', type=int); ap.add_argument('held_side', type=float); ap.add_argument('out')
        ap.add_argument('--fq', default=os.path.expanduser('$SCRATCH/squares-base/fq')); ap.add_argument('--seeds', type=int, default=3)
        ap.add_argument('--xmax', type=float, default=1e9); ap.add_argument('--jit', type=float, default=0.05)
        a = ap.parse_args()
        cmd_stuff(a.start, a.n, a.held_side, a.out, a.fq, a.seeds, a.xmax, a.jit); sys.exit(0)
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['scan']); ap.add_argument('held'); ap.add_argument('m', type=int); ap.add_argument('c', type=int); ap.add_argument('out')
    ap.add_argument('--step', type=float, default=0.02); ap.add_argument('--low', action='store_true'); ap.add_argument('--want', type=int, default=0)
    a = ap.parse_args()
    cmd_scan(a.held, a.m, a.c, a.out, a.step, a.low, a.want)
